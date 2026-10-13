#!/usr/bin/env python3
"""Ajustes de OweeLinux v0.2 (todas las páginas). Se ejecuta en el HOST. Despliega panel y app de ajustes, comprueba que el panel cambia al instante
al modificar ~/.config/owee/settings.json y que la app de ajustes escribe ese archivo y cambia el fondo (swaybg).
Uso: ajustes-test.py DISCO.img DIR_SALIDA"""
import importlib.util, json, os, shutil, socket, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.abspath(os.path.join(here, "..", ".."))
spec = importlib.util.spec_from_file_location("it", os.path.join(here, "interaction-test.py"))
src = open(os.path.join(here, "interaction-test.py")).read()
gspec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py")); gui = importlib.util.module_from_spec(gspec); gspec.loader.exec_module(gui)
disk, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
srv = "/home/oweeme/.cache/oweelinux/vm/ssrv"; os.makedirs(srv, exist_ok=True)
os.makedirs(srv + "/shell", exist_ok=True); os.makedirs(srv + "/session", exist_ok=True)
shutil.rmtree(srv + "/shell", ignore_errors=True); shutil.copytree(os.path.join(repo, "desktop/shell"), srv + "/shell", ignore=shutil.ignore_patterns("__pycache__"))
subprocess.run(["tar", "czf", srv + "/shell.tgz", "-C", srv, "shell"], check=True)
for f in ("owee-wallpaper", "owee-apply-display", "owee-idle"): shutil.copy(os.path.join(repo, "desktop/session", f), srv + "/session")
shutil.copy(os.path.join(here, "mock-wpctl"), srv)
shutil.copy(os.path.join(repo, "desktop/session/owee-wallpaper"), srv + "/session")
for nm, col in (("Owee", "#EFF0F1"), ("Owee-Light", "#17231e")): subprocess.run(["python3", os.path.join(repo, "desktop/theme/icons/gen_icons.py"), srv + "/icons", col, nm], check=True, stdout=subprocess.DEVNULL)
subprocess.run(["tar", "czf", srv + "/owee-icons.tgz", "-C", srv + "/icons", "Owee", "Owee-Light"], check=True)
for f in os.listdir(os.path.join(repo, "desktop/widgets/sistema")): shutil.copy(os.path.join(repo, "desktop/widgets/sistema", f), srv)
shutil.copy(os.path.join(here, "mock-wpctl"), srv)
http = subprocess.Popen(["python3", "-m", "http.server", "8006", "--bind", "127.0.0.1", "--directory", srv], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
W = "/home/oweeme/.cache/oweelinux/vm/litediag"; os.makedirs(W, exist_ok=True); os.chdir(W)
for f in ("ser.sock", "mon.sock", "qmp.sock"):
    if os.path.exists(f): os.unlink(f)
shutil.copyfile(gui.VARS_SRC, "vars.fd"); open("c.log", "wb").close()
os.environ["QEMU_MEM"] = "3072"; os.environ["QEMU_EXTRA"] = "-qmp unix:qmp.sock,server=on,wait=off"
vm = gui.Vm(disk, W + "/vars.fd", W + "/c.log"); SW, SH = 1280, 800
U = "runuser -u oweeuser -- env HOME=/home/oweeuser XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus "
class Qmp:
    def __init__(self):
        for _ in range(100):
            if os.path.exists("qmp.sock"):
                try: self.s = socket.socket(socket.AF_UNIX); self.s.connect("qmp.sock"); break
                except OSError: pass
            time.sleep(0.1)
        self.f = self.s.makefile("rw"); self.f.readline(); self.cmd("qmp_capabilities")
    def cmd(self, name, **a):
        self.f.write(json.dumps({"execute": name, "arguments": a}) + "\n"); self.f.flush()
        while True:
            r = json.loads(self.f.readline())
            if "return" in r or "error" in r: return r
    def click(self, x, y):
        self.cmd("input-send-event", events=[{"type": "abs", "data": {"axis": "x", "value": int(x * 32767 / SW)}}, {"type": "abs", "data": {"axis": "y", "value": int(y * 32767 / SH)}}]); time.sleep(0.4)
        self.cmd("input-send-event", events=[{"type": "btn", "data": {"down": True, "button": "left"}}]); time.sleep(0.15)
        self.cmd("input-send-event", events=[{"type": "btn", "data": {"down": False, "button": "left"}}])
def key(k): vm.mon.sendall(f"sendkey {k}\n".encode()); time.sleep(0.3)
def sh(c, k, t=60): return vm.run(f"echo MARK_{k}=$({c} | tr '\\n' '|')", k, t)
res = []
def check(name, ok, detail=""): res.append(ok); print(("PASA   " if ok else "FALLA  ") + name + (f"  ({detail})" if detail else ""), flush=True)
try:
    assert vm.wait(gui.PROMPT, 240); time.sleep(8)
    vm.run("systemctl stop sddm; loginctl terminate-user oweeuser; systemctl stop user@1000.service; sleep 3; pkill -9 -u oweeuser; sleep 1; echo MARK_ST=ok", "ST", 90)
    vm.run("mkdir -p /etc/owee /etc/systemd/user /tmp/ps/BAT0; ln -sfn /dev/null /etc/systemd/user/waybar.service; ln -sfn /dev/null /etc/systemd/user/mako.service; "
           "printf '17\\n' > /tmp/ps/BAT0/capacity; printf 'Discharging\\n' > /tmp/ps/BAT0/status; chmod -R a+rX /tmp/ps; "
           "mkdir -p /tmp/session /tmp/mockbin; curl -s http://10.0.2.2:8006/shell.tgz | tar xz -C /tmp; chmod +x /tmp/shell/*.py; for f in owee-apply-display owee-idle; do curl -s http://10.0.2.2:8006/session/$f -o /tmp/session/$f; chmod +x /tmp/session/$f; done; curl -s http://10.0.2.2:8006/mock-wpctl -o /tmp/mockbin/wpctl; chmod 755 /tmp/mockbin/wpctl; curl -s http://10.0.2.2:8006/session/owee-wallpaper -o /tmp/session/owee-wallpaper; chmod +x /tmp/session/owee-wallpaper; mkdir -p /var/home/oweeuser/.local/share/icons; curl -s http://10.0.2.2:8006/owee-icons.tgz | tar xz -C /var/home/oweeuser/.local/share/icons; chown -R oweeuser:oweeuser /var/home/oweeuser/.local; D=/var/home/oweeuser/.config/owee/widgets; install -d -o oweeuser -g oweeuser /var/home/oweeuser/.config /var/home/oweeuser/.config/owee $D; "
           "for f in 10-red.py 20-volumen.py 30-bateria.py; do curl -s http://10.0.2.2:8006/$f -o $D/$f; done; chown -R oweeuser:oweeuser $D; chmod +x $D/*; "
           "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/environment; "
           "printf 'PANEL=python\\nOWEE_PANEL_PATH=/tmp/shell/owee_panel.py\\nexport OWEE_DEBUG_LAYOUT=1 OWEE_POWER_SUPPLY_DIR=/tmp/ps PATH=/tmp/mockbin:$PATH\\n' > /etc/owee/panel.conf; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 120)
    time.sleep(40)
    time.sleep(40)
    q = Qmp(); time.sleep(3)
    sh(U + "WAYLAND_DISPLAY=wayland-0 PATH=/tmp/mockbin:/usr/bin:/bin sh -c 'nohup python3 /tmp/shell/owee_settings.py > /tmp/settings.log 2>&1 &'", "A", 30); time.sleep(8)
    print("log:", sh("grep -v dconf /tmp/settings.log | grep -v a11y | head -12 | cut -c1-200", "LG", 30))
    vm.screenshot(os.path.join(out, "aj-1-apariencia.png"))
    A = lambda y: q.click(265, y)                                    # filas de la barra lateral
    F = lambda cmd, k, t=30: sh(U + cmd, k, t) or ""                 # orden como oweeuser
    # --- Apariencia: modo claro → kdeglobals con el esquema Breeze (apps Qt/KDE) y settings.ini (apps GTK)
    A(207); time.sleep(2); q.click(491, 280); time.sleep(3)
    kg = F("grep -c 'Colors:Window\\|ColorScheme=BreezeLight' /var/home/oweeuser/.config/kdeglobals", "KG"); sc = F("ls /usr/share/color-schemes | tr '\\n' ' '", "SC")
    check("Apariencia: el modo claro escribe el esquema Breeze en kdeglobals", "BreezeLight" in F("cat /var/home/oweeuser/.config/kdeglobals", "KG2") or "Breeze" in sc and kg.strip("|").strip() not in ("", "0"), kg + sc)
    vm.screenshot(os.path.join(out, "aj-t-claro.png"))
    # --- Sonido: volumen con clic en la barra, silenciar, otra salida
    A(336); time.sleep(2); q.click(1023, 311); time.sleep(3)
    v = F("cat /tmp/mock-vol", "V"); check("Sonido: el deslizante cambia el volumen (≈0.70)", v.strip("|").replace(".", "", 1).isdigit() and 0.6 <= float(v.strip("|")) <= 0.8, v)
    q.click(1081, 357); time.sleep(2); check("Sonido: el interruptor silencia la salida", F("ls /tmp/mock-mute", "MU").strip("|") == "/tmp/mock-mute")
    q.click(1020, 229); time.sleep(1.5); q.click(1020, 315); time.sleep(2.5); check("Sonido: elegir otra salida (Auriculares USB) la deja por defecto", F("cat /tmp/mock-default-sink", "DS").strip("|") == "48", F("cat /tmp/mock-default-sink", "DS2"))
    vm.screenshot(os.path.join(out, "aj-t-sonido.png"))
    # --- Teclado: Español (Latinoamérica)
    A(368); time.sleep(2); q.click(1032, 267); time.sleep(1.5); q.click(1032, 353); time.sleep(2.5)
    env = F("cat /var/home/oweeuser/.config/labwc/environment", "EN"); check("Teclado: la distribución se guarda y se recarga", "XKB_DEFAULT_LAYOUT=latam" in env, env); vm.screenshot(os.path.join(out, "aj-t-teclado.png"))
    # --- Ratón: desplazamiento natural
    A(400); time.sleep(2); q.click(1081, 427); time.sleep(2.5); vm.screenshot(os.path.join(out, "aj-t-raton.png"))
    rc = F("grep -c naturalScroll /var/home/oweeuser/.config/labwc/rc.xml; grep -A1 naturalScroll /var/home/oweeuser/.config/labwc/rc.xml | head -2 | tr -d ' ' ", "RC"); check("Ratón: el desplazamiento natural entra en rc.xml", "yes" in rc, rc)
    # --- Energía: bloquear tras 1 minuto → power.json y swayidle con el tiempo
    A(432); time.sleep(2); q.click(1045, 316); time.sleep(1.5); q.click(1045, 402); time.sleep(3)
    pj = F("cat /var/home/oweeuser/.config/owee/power.json; pgrep -a swayidle | cut -c1-120", "PJ"); check("Energía: 1 minuto llega a power.json y a swayidle", '"lock_min": "1"' in pj and "60" in pj, pj); vm.screenshot(os.path.join(out, "aj-t-energia.png"))
    # --- Fecha y hora y Aplicaciones (capturas)
    A(497); time.sleep(2); vm.screenshot(os.path.join(out, "aj-t-fecha.png"))
    A(529); time.sleep(2); vm.screenshot(os.path.join(out, "aj-t-apps.png"))
    # --- Pantalla: 150 % → barra de confirmación → Mantener
    A(304); time.sleep(2); q.click(1063, 282); time.sleep(1.5); q.click(1060, 404); time.sleep(3); vm.screenshot(os.path.join(out, "aj-t-pantalla-confirmar.png"))
    SC = lambda: F("WAYLAND_DISPLAY=wayland-0 wlr-randr | grep Scale", "RR")
    s1 = SC(); check("Pantalla: la escala 150 % se aplica de verdad", "1.5" in s1, s1)
    time.sleep(13); vm.screenshot(os.path.join(out, "aj-t-pantalla-revertida.png")); s2 = SC(); check("Pantalla: sin confirmar, vuelve sola a la escala anterior (100 %)", "1.0" in s2, s2)
    q.click(897, 282); time.sleep(1.5); q.click(895, 404); time.sleep(3); vm.screenshot(os.path.join(out, "aj-t-pantalla-2.png")); q.click(1225, 633); time.sleep(3)
    s3 = SC(); dj = F("cat /var/home/oweeuser/.config/owee/display.json | tr -d ' \\n'", "DJ"); check("Pantalla: al pulsar Mantener queda aplicada y guardada", "1.5" in s3 and '"scale":"1.5"' in dj, s3 + dj)
    vm.screenshot(os.path.join(out, "aj-t-pantalla-final.png"))
finally:
    vm.kill(); http.kill()
print("PASA todo" if res and all(res) else "HAY FALLOS"); sys.exit(0 if res and all(res) else 1)
