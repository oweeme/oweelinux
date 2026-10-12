#!/usr/bin/env python3
"""Prototipo de riesgos del escritorio Lite (4c). Se ejecuta en el HOST.
Arranca la imagen y, por variante, entra a la sesión (autologin de SDDM) y mide:
  plasma        sesión de Plasma (referencia)
  lite-python   labwc + panel en Python/GTK4 (layer-shell) + mako + swaybg
  lite-waybar   labwc + Waybar + mako + swaybg
Mide la memoria usada (free), el Pss de los procesos de la sesión, qué ventanas ve pywayland, y toma capturas.
Uso: lite-spike.py DISCO.img DIR_SALIDA [--variants plasma,lite-python,lite-waybar]"""
import argparse, importlib.util, os, shutil, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py"))
gui = importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)
U = "runuser -u oweeuser -- env HOME=/home/oweeuser XDG_RUNTIME_DIR=/run/user/1000 "
SESSION = {"plasma": "plasmax11.desktop", "lite-python": "owee-lite.desktop", "lite-waybar": "owee-lite.desktop"}
PROCS = {"plasma": "plasmashell|kwin_x11|Xorg|kded6|ksmserver|krunner|baloo|polkit-kde|org_kde_powerdev|kscreen|xdg-desktop-por",
         "lite-python": "labwc|owee_panel|mako|swaybg|Xwayland|xdg-desktop-por",
         "lite-waybar": "labwc|waybar|mako|swaybg|Xwayland|xdg-desktop-por"}

def variant(name, disk, out, work):
    os.chdir(work)
    for f in ("ser.sock", "mon.sock"):
        if os.path.exists(f): os.unlink(f)
    shutil.copyfile(gui.VARS_SRC, "vars.fd"); log = os.path.join(work, f"{name}.log"); open(log, "wb").close()
    os.environ["QEMU_MEM"] = "3072"; vm = gui.Vm(disk, work + "/vars.fd", log); r = {"name": name}
    try:
        assert vm.wait(gui.PROMPT, 240); time.sleep(8)
        if name != "plasma":
            # elegir la sesión y reiniciar SDDM para que entre sola (autologin). Se enmascaran los servicios de usuario
            # que Debian arranca solos y se descarga el panel del repositorio (así se prueba el código actual sin reconstruir).
            # AISLAR: detener SDDM y el gestor de usuario de la sesión de Plasma; si no, sus servicios (plasmashell, waybar.service...)
            # siguen vivos en la sesión nueva y contaminan la medición.
            vm.run("systemctl stop sddm; loginctl terminate-user oweeuser; systemctl stop user@1000.service; sleep 3; pkill -9 -u oweeuser; sleep 1; echo MARK_ST=ok", "ST", 90)
            vm.run("mkdir -p /etc/owee /etc/systemd/user; ln -sfn /dev/null /etc/systemd/user/waybar.service; ln -sfn /dev/null /etc/systemd/user/mako.service; "
                   "curl -s http://10.0.2.2:8002/owee_panel.py -o /tmp/owee_panel.py; "
                   "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/owee/lite.env; "
                   "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' >> /etc/environment; "
                   f"printf 'PANEL={'waybar' if name == 'lite-waybar' else 'python'}\\nOWEE_PANEL_PATH=/tmp/owee_panel.py\\n' > /etc/owee/panel.conf; "
                   f"printf '[Autologin]\\nUser=oweeuser\\nSession={SESSION[name]}\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 60)
        t0 = time.time(); started = None
        probe = "plasmashell" if name == "plasma" else ("owee_panel.py" if name == "lite-python" else "waybar")
        for _ in range(60):
            if vm.run(f"echo MARK_P=$(pgrep -f {probe} | head -1)", "P", 15): started = time.time() - t0; break
            time.sleep(3)
        r["arranque_s"] = started; time.sleep(45)
        vm.screenshot(os.path.join(out, f"lite-{name}.png"))
        r["usada_mb"] = vm.run("echo MARK_M=$(free -m | awk '/Mem:/{print $3}')", "M", 30)
        r["pss"] = vm.run("echo MARK_S=$(for p in $(pgrep -f '" + PROCS[name] + "'); do n=$(cat /proc/$p/comm); a=$(awk '/^Pss:/{print $2}' /proc/$p/smaps_rollup 2>/dev/null); echo \"$n:$((a/1024))\"; done | sort | awk -F: '{s[$1]+=$2} END{for(k in s) printf \"%s=%dMB \", k, s[k]}')", "S", 60)
        if name != "plasma":
            r["panel_log"] = vm.run("echo MARK_L=$(grep -h -E 'mem|NM|UPower|Error|Traceback|rror' /tmp/owee-panel.log /tmp/owee-waybar.log 2>/dev/null | tail -4 | tr '\\n' '|' | cut -c1-260)", "L", 30)
            r["procesos"] = vm.run("echo MARK_PS=$(ps -eo rss,args | grep -E 'waybar|owee_panel|labwc|mako|swaybg' | grep -v grep | awk '{printf \"%s:%dMB \", $2, $1/1024}' | cut -c1-300)", "PS", 30)
            vm.run(f"({U}WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland konsole > /tmp/foot.log 2>&1 &); echo MARK_F=ok", "F", 30); time.sleep(14)
            r["foot"] = vm.run("echo MARK_FO=$(pgrep -c konsole) $(head -c 160 /tmp/foot.log | tr '\\n' '|')", "FO", 30)
            r["ventanas_pywayland"] = vm.run(f"echo MARK_W=$({U}WAYLAND_DISPLAY=wayland-0 python3 /usr/libexec/owee/wl_toplevels.py 2>&1 | tail -2 | tr '\\n' ' ' | cut -c1-300)", "W", 60)
            time.sleep(3); vm.screenshot(os.path.join(out, f"lite-{name}-ventana.png"))
    finally:
        vm.kill()
    return r

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("disk"); ap.add_argument("out"); ap.add_argument("--variants", default="plasma,lite-python,lite-waybar")
    a = ap.parse_args(); out = os.path.abspath(a.out); os.makedirs(out, exist_ok=True)
    work = "/home/oweeme/.cache/oweelinux/vm/lite"; os.makedirs(work, exist_ok=True)
    http = subprocess.Popen(["python3", "-m", "http.server", "8002", "--bind", "127.0.0.1", "--directory", os.path.join(here, "..", "..", "desktop", "shell")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for n in a.variants.split(","):
        print(f"== {n}", flush=True); print(variant(n, os.path.abspath(a.disk), out, work), flush=True)
    http.kill()

if __name__ == "__main__": main()
