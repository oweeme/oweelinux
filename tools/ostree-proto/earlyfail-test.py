#!/usr/bin/env python3
"""Fallos tempranos de arranque (F3c-bis). Se ejecuta en el HOST.

Desde la release 1 (confirmada) se actualiza a tres versiones defectuosas, una por escenario, y se
comprueba que el sistema vuelve SOLO a la release 1 sin quedarse en bucle:
  initrd      initramfs corrupto: el kernel no puede montar la raíz -> panic -> reinicio (panic=5)
  neverready  un servicio bloquea el arranque: owee-health espera 90 s, la rechaza y reinicia
  hang        el sistema se cuelga del todo: lo reinicia el watchdog (hardware simulado i6300esb)
Todas parten de `owee-update` con OWEE_REF=owee:broken/<escenario>; el intento a prueba lo gasta GRUB.

Uso: earlyfail-test.py DISCO.img DIR_PUB_EARLY [--workdir DIR] [--only esc1,esc2]
Disco con -snapshot. Memoria/CPU: QEMU_MEM / QEMU_SMP."""
import argparse, importlib.util, os, re, shutil, sys, tempfile, time

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("powerloss", os.path.join(here, "powerloss-test.py"))
pl = importlib.util.module_from_spec(spec); spec.loader.exec_module(pl)   # reutiliza la clase Vm

SCEN = {"initrd": 401, "neverready": 402, "hang": 403}   # marcador de release de cada versión rota


def kv(txt, key):
    m = re.search(key + r"=(\S+)", txt or ""); return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("disk"); ap.add_argument("pub")
    ap.add_argument("--workdir"); ap.add_argument("--only", default=",".join(SCEN))
    a = ap.parse_args()
    work = os.path.abspath(a.workdir or tempfile.mkdtemp(prefix="early-")); os.makedirs(work, exist_ok=True); os.chdir(work)
    os.environ["QEMU_EXTRA"] = "-snapshot -device i6300esb -watchdog-action reset"
    for f in ("ser.sock",):
        if os.path.exists(f): os.unlink(f)
    shutil.copyfile(pl.OVMF_VARS, "vars.fd")
    stage = tempfile.mkdtemp(); os.symlink(os.path.realpath(a.pub), os.path.join(stage, "pub"))
    import subprocess
    http = subprocess.Popen(["python3", "-m", "http.server", "8000", "--bind", "127.0.0.1", "--directory", stage],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log = os.path.join(work, "console.log"); open(log, "wb").close()
    vm = pl.Vm(os.path.abspath(a.disk), os.path.join(work, "vars.fd"), "ser.sock", log)
    results = []; fails = []
    try:
        if not vm.wait_for(pl.PROMPT, 180): sys.exit("no arrancó la release 1")
        st = vm.run(r"echo MARK_S0=$(owee-status | tr '\n' ' ')", "S0", 20) or ""
        print("inicio:", st, flush=True)
        if kv(st, "release") != "1": sys.exit("se esperaba empezar en la release 1")
        vm.run("echo hola-usuario > /home/dato.txt; sync; echo MARK_D=ok", "D", 10)
        for name in a.only.split(","):
            marker = str(SCEN[name]); t0 = time.time(); problems = []
            up = vm.run(f"OWEE_REF=owee:broken/{name} owee-update 2>&1 | tail -1; echo MARK_UP=${{PIPESTATUS[0]}}", "UP", 180)
            if up != "0": problems.append(f"owee-update rc={up}")
            pos = len(vm.text()); vm.send("systemctl reboot")
            # El shell reimprime su prompt ANTES de que la máquina se reinicie: hay que esperar a ver el
            # menú de GRUB (el reinicio de verdad) y solo entonces un prompt nuevo.
            g = vm.wait_for(re.compile(rb"GNU GRUB  version"), 180, pos)
            if not g: problems.append("la máquina no llegó a reiniciarse tras `systemctl reboot`")
            else: pos = g.end()
            fell_back = False; saw_broken = False; grub_menus = 0; deadline = time.time() + int(os.environ.get("EARLYFAIL_TIMEOUT", "600"))
            while time.time() < deadline and not problems:
                m = vm.wait_for(pl.PROMPT, 120, pos)
                grub_menus = 1 + len(re.findall(rb"GNU GRUB  version", vm.text()[pos:]))
                if not m:
                    if vm.p.poll() is not None: problems.append("QEMU terminó"); break
                    continue                      # sin prompt todavía (cuelgue o reinicio en curso)
                pos = m.end()
                s1 = vm.run(r"echo MARK_S1=$(owee-status | tr '\n' ' ')", "S1", 10)
                pos = len(vm.text())               # lo siguiente que esperamos es un prompt NUEVO (tras un reinicio)
                if s1 is None: continue            # se reinició mientras preguntábamos
                rel = kv(s1, "release")
                if rel == "1": fell_back = True; final = s1; break
                if rel == marker: saw_broken = True   # llegó a arrancar la versión rota; esperar su caída
            elapsed = time.time() - t0
            if not fell_back and not problems: problems.append("no volvió a la release 1 en 10 minutos (¿bucle?)")
            evidence = ""
            if fell_back:
                text = vm.text().decode(errors="replace")
                if name == "initrd":
                    evidence = "kernel panic" if re.search(r"Kernel panic|not syncing|Initramfs unpacking failed", text) else ""
                else:
                    log_ = vm.run("echo MARK_E=$(tr '\\n' ',' < /var/lib/owee/earlyfail.log 2>/dev/null)", "E", 10) or ""
                    evidence = log_ if f"{name}-started" in log_ else ""
                if not evidence: problems.append("no hay evidencia de que la versión rota llegara a intentar arrancar")
                if kv(final, "booted") != kv(final, "confirmed"): problems.append("la versión en uso no es la confirmada")
                if vm.run("echo MARK_DATO=$(cat /home/dato.txt)", "DATO", 10) != "hola-usuario": problems.append("/home perdió el archivo")
                if grub_menus > 4: problems.append(f"demasiados reinicios ({grub_menus} menús de GRUB)")
            results.append((name, not problems, elapsed, evidence, grub_menus, problems))
            print(f"{'PASA ' if not problems else 'FALLA'}  {name:10s} volvió solo a la release 1 en {elapsed:5.0f}s  "
                  f"menús GRUB={grub_menus}  evidencia={evidence!r}" + (f"  PROBLEMAS: {problems}" if problems else ""), flush=True)
            if problems: fails.append(name); break
    finally:
        vm.kill(); http.kill(); shutil.rmtree(stage, ignore_errors=True)
    print("registro de consola:", log)
    print("PASA todos los escenarios" if not fails else f"FALLA: {fails}"); sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
