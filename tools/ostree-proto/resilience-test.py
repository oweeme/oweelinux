#!/usr/bin/env python3
"""Resiliencia de la sesión (F-R): ¿qué le pasa al escritorio cuando un proceso se desboca? Se ejecuta en el HOST.

Arranca la imagen con Plasma en QEMU (una VM nueva por escenario, disco con -snapshot), espera al escritorio,
lanza un proceso que consume toda la memoria (`tail /dev/zero`) durante unos segundos y mide, cada ~2 s:
  - latencia de una consola (el comando más simple) y de una consulta al servidor gráfico (`xset q`);
y al final: si el proceso desbocado sigue vivo, cuántos OOM-kills hubo y si sobreviven plasmashell, kwin,
Xorg y sddm. Escenarios: S0 control · S1 sin swap · S2 con swap de 3 GB en disco · S3 con MemoryMax ·
S4 escritorio protegido (oom_score_adj=-900).
Uso: resilience-test.py DISCO.img [--only S0,S1] [--secs 90] [--workdir DIR]
Memoria/CPU de la VM: QEMU_MEM (por defecto 3072) / QEMU_SMP (2)."""
import argparse, importlib.util, os, re, shutil, sys, tempfile, time

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py"))
gui = importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)

XCMD = ("timeout 25 runuser -u oweeuser -- env DISPLAY=:0 XAUTHORITY=/home/oweeuser/.Xauthority "
        "xset q >/dev/null 2>&1; echo MARK_{k}=$?")
PROTECT = ("for n in plasmashell kwin_x11 Xorg sddm sddm-helper systemd-logind dbus-daemon; do "
           "for p in $(pgrep -x $n); do echo -900 > /proc/$p/oom_score_adj; done; done; echo MARK_PR=ok")


def timed(vm, cmd, key, limit):
    """Ejecuta cmd y devuelve (valor, segundos hasta ver MARK_key); valor None si no respondió en `limit`."""
    t0 = time.time(); v = vm.run(cmd, key, limit)
    return v, time.time() - t0


# Parámetros de cada escenario. hog: "tail" (consumo abrupto) o "perl" (gradual, ~60 MB/s).
SCEN = {
    "S0": dict(hog=None), "S1": dict(hog="tail"), "S2": dict(hog="tail", swap="3G"),
    "S3": dict(hog="tail", limit=True), "S4": dict(hog="tail", protect=True),
    # Serie T: presión GRADUAL con swap en un disco LENTO (usar QEMU_DRIVE_OPTS con throttling) y 2 GB de RAM
    "T0": dict(hog=None, swap="1500M"),
    "T1": dict(hog="perl", swap="1500M"),                       # sin protección
    "T2": dict(hog="perl", swap="1500M", limit=True),           # el proceso corre con MemoryMax/MemoryHigh
    "T3": dict(hog="perl", swap="1500M", earlyoom=True),        # earlyoom vigilando
}
HOGS = {"tail": "tail /dev/zero",
        "perl": "perl -e 'my @a; while(1){ push @a, q(x) x (30*1024*1024); select(undef,undef,undef,0.5) }'"}


def scenario(name, disk, secs, work, earlyoom_url):
    cfg = SCEN[name]
    os.chdir(work)
    for f in ("ser.sock", "mon.sock"):
        if os.path.exists(f): os.unlink(f)
    shutil.copyfile(gui.VARS_SRC, "vars.fd"); log = os.path.join(work, f"{name}.log"); open(log, "wb").close()
    vm = gui.Vm(disk, os.path.join(work, "vars.fd"), log); res = {"name": name}
    try:
        if not vm.wait(gui.PROMPT, 300): res["error"] = "no arrancó"; return res
        for _ in range(100):                     # esperar al escritorio
            if vm.run("echo MARK_P=$(pgrep -x plasmashell | head -1)", "P", 10): break
            time.sleep(3)
        time.sleep(25)
        res["x_base"] = timed(vm, XCMD.format(k="X0"), "X0", 60)[1]
        res["ping_base"] = timed(vm, "echo MARK_PG=1", "PG", 60)[1]
        if cfg.get("swap"):
            sw = vm.run(f"fallocate -l {cfg['swap']} /var/swapfile && chmod 600 /var/swapfile && mkswap /var/swapfile >/dev/null && swapon /var/swapfile; echo MARK_SW=$(swapon --show=SIZE --noheadings | tr -d ' \\n')", "SW", 120)
            print("  swap:", sw, flush=True)
        print("  memoria libre al empezar:", vm.run("echo MARK_MEM=$(free -m | awk '/Mem:/{print $7\"MB disp\"}')", "MEM", 30), flush=True)
        if cfg.get("protect"): print("  protección:", vm.run(PROTECT, "PR", 30), flush=True)
        if cfg.get("earlyoom"):
            print("  earlyoom:", vm.run(f"curl -s -o /tmp/earlyoom {earlyoom_url} && chmod +x /tmp/earlyoom && systemd-run --unit=earlyoom /tmp/earlyoom -m 10 -s 50 -r 0 --avoid '(^|/)(plasmashell|kwin_x11|Xorg|sddm|systemd|dbus-daemon|agetty|bash)$' >/dev/null 2>&1; sleep 1; echo MARK_EO=$(systemctl is-active earlyoom)", "EO", 60), flush=True)
        if cfg["hog"]:
            lim = "-p MemoryMax=900M -p MemoryHigh=700M " if cfg.get("limit") else ""
            hog = HOGS[cfg["hog"]].replace("'", "'\\''")
            vm.run(f"systemd-run -p User=oweeuser {lim}--collect --unit=hog sh -c '{hog}' >/dev/null 2>&1; echo MARK_H=$?", "H", 30)
        t0 = time.time(); pings = []; xs = []; kill_t = None
        while time.time() - t0 < secs:
            v, dt = timed(vm, "echo MARK_PG=1", "PG", 120); pings.append(dt if v else 120)
            v, dx = timed(vm, XCMD.format(k="X1"), "X1", 120); xs.append(dx if v == "0" else (None if v is None else -1))
            if cfg["hog"] and kill_t is None and not vm.run("echo MARK_HA=$(systemctl is-active hog)", "HA", 120) == "active": kill_t = time.time() - t0
            time.sleep(1)
        res["ping_max"] = max(pings) if pings else None
        okx = [x for x in xs if x is not None and x >= 0]
        res["x_max"] = max(okx) if okx else None
        res["x_fallos"] = sum(1 for x in xs if x is None or x < 0)
        res["muestras"] = len(pings); res["hog_terminado_a_los"] = kill_t
        res["hog_vivo"] = vm.run("echo MARK_HV=$(systemctl is-active hog)", "HV", 120) == "active"
        res["oom_kills"] = vm.run("echo MARK_OK=$(dmesg | grep -c 'Killed process')", "OK", 120)
        res["muertos_por_oom"] = vm.run("echo MARK_KP=$(dmesg | grep 'Killed process' | sed -E 's/.*\\(([^)]*)\\).*/\\1/' | sort | uniq -c | tr '\\n' ' ')", "KP", 120)
        res["sobreviven"] = {n: bool(vm.run(f"echo MARK_S=$(pgrep -x {n} | head -1)", "S", 120)) for n in ("plasmashell", "kwin_x11", "Xorg", "sddm")}
        res["escritorio_ok"] = vm.run(XCMD.format(k="X2"), "X2", 120) == "0"
    finally:
        vm.kill()
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("disk"); ap.add_argument("--only", default="S0,S1,S2,S3,S4")
    ap.add_argument("--secs", type=int, default=90); ap.add_argument("--workdir"); ap.add_argument("--earlyoom", help="ruta del binario earlyoom (se sirve a la VM por HTTP)")
    a = ap.parse_args()
    work = os.path.abspath(a.workdir or tempfile.mkdtemp(prefix="res-")); os.makedirs(work, exist_ok=True)
    os.environ.setdefault("QEMU_MEM", "3072")
    rows = []; http = None; url = ""
    if a.earlyoom:                                  # servir el binario a la VM (la VM no tiene apt)
        import subprocess
        d = os.path.dirname(os.path.abspath(a.earlyoom)); url = "http://10.0.2.2:8001/" + os.path.basename(a.earlyoom)
        http = subprocess.Popen(["python3", "-m", "http.server", "8001", "--bind", "127.0.0.1", "--directory", d], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for n in a.only.split(","):
            print(f"== {n} ...", flush=True); r = scenario(n, os.path.abspath(a.disk), a.secs, work, url); rows.append(r); print(r, flush=True)
    finally:
        if http: http.kill()
    print("\n%-3s %9s %9s %9s %10s %9s %5s  %s" % ("esc", "ping_max", "x_max", "x_fallos", "hog_acabó", "oom_kills", "ok?", "sobreviven plasma/kwin/Xorg/sddm"))
    for r in rows:
        if "error" in r: print(r["name"], r["error"]); continue
        s = r["sobreviven"]
        kt = r.get("hog_terminado_a_los"); kts = ("%.0fs" % kt) if kt is not None else ("no" if r.get("hog_vivo") else "-")
        print("%-3s %8.1fs %8.1fs %9s %10s %9s %5s  %s %s" % (r["name"], r["ping_max"] or -1, r["x_max"] or -1, r["x_fallos"], kts, r["oom_kills"],
              r["escritorio_ok"], "/".join("sí" if s[k] else "NO" for k in ("plasmashell", "kwin_x11", "Xorg", "sddm")), r["muertos_por_oom"] or ""))


if __name__ == "__main__":
    main()
