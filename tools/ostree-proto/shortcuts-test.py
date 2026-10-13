#!/usr/bin/env python3
"""Calendario del reloj y atajos de teclado de la sesión Lite. Se ejecuta en el HOST. Clic en el reloj abre el calendario; Super+Espacio abre el lanzador,
Super+C el calendario, Super+E abre Archivos, Impr. Pant. guarda una captura. Despliega panel y rc.xml sin reconstruir la imagen.
Uso: shortcuts-test.py DISCO.img DIR_SALIDA"""
import importlib.util, json, os, shutil, socket, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.abspath(os.path.join(here, "..", ".."))
spec = importlib.util.spec_from_file_location("it", os.path.join(here, "interaction-test.py"))
src = open(os.path.join(here, "interaction-test.py")).read()
gspec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py")); gui = importlib.util.module_from_spec(gspec); gspec.loader.exec_module(gui)
disk, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
srv = "/home/oweeme/.cache/oweelinux/vm/ssrv"; os.makedirs(srv, exist_ok=True)
os.makedirs(srv + "/shell", exist_ok=True); os.makedirs(srv + "/session", exist_ok=True)
for f in os.listdir(os.path.join(repo, "desktop/shell")):
    if f.endswith(".py"): shutil.copy(os.path.join(repo, "desktop/shell", f), srv + "/shell")
shutil.copy(os.path.join(repo, "desktop/session/owee-wallpaper"), srv + "/session"); shutil.copy(os.path.join(repo, "desktop/session/labwc/rc.xml"), srv)
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
           "mkdir -p /tmp/shell /tmp/session; for f in owee_panel owee_tray owee_config owee_settings; do curl -s http://10.0.2.2:8006/shell/$f.py -o /tmp/shell/$f.py; done; chmod +x /tmp/shell/*.py; curl -s http://10.0.2.2:8006/session/owee-wallpaper -o /tmp/session/owee-wallpaper; chmod +x /tmp/session/owee-wallpaper; install -d -o oweeuser -g oweeuser /var/home/oweeuser/.config/labwc; curl -s http://10.0.2.2:8006/rc.xml -o /var/home/oweeuser/.config/labwc/rc.xml; chown oweeuser:oweeuser /var/home/oweeuser/.config/labwc/rc.xml; mkdir -p /var/home/oweeuser/.local/share/icons; curl -s http://10.0.2.2:8006/owee-icons.tgz | tar xz -C /var/home/oweeuser/.local/share/icons; chown -R oweeuser:oweeuser /var/home/oweeuser/.local; D=/var/home/oweeuser/.config/owee/widgets; install -d -o oweeuser -g oweeuser /var/home/oweeuser/.config /var/home/oweeuser/.config/owee $D; "
           "for f in 10-red.py 20-volumen.py 30-bateria.py; do curl -s http://10.0.2.2:8006/$f -o $D/$f; done; chown -R oweeuser:oweeuser $D; chmod +x $D/*; "
           "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/environment; "
           "printf 'PANEL=python\\nOWEE_PANEL_PATH=/tmp/shell/owee_panel.py\\nexport OWEE_DEBUG_LAYOUT=1 OWEE_POWER_SUPPLY_DIR=/tmp/ps PATH=/tmp/mockbin:$PATH\\n' > /etc/owee/panel.conf; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 120)
    time.sleep(40)
    time.sleep(40)
    q = Qmp(); time.sleep(3)
    q.click(640, 22); time.sleep(2.5); vm.screenshot(os.path.join(out, "calendario.png"))
    key("esc"); time.sleep(1)
    key("meta_l-spc"); time.sleep(2.5); vm.screenshot(os.path.join(out, "atajo-lanzador.png")); key("esc"); time.sleep(1)
    key("meta_l-c"); time.sleep(2.5); vm.screenshot(os.path.join(out, "atajo-calendario.png")); key("esc"); time.sleep(1)
    key("meta_l-e"); time.sleep(12)
    n = sh("pgrep -c -u oweeuser dolphin", "D", 30) or ""; check("Super+E abre Archivos", n.strip("|").strip().isdigit() and int(n.strip("|").strip()) > 0, n)
    key("print"); time.sleep(5)
    f = sh("ls /var/home/oweeuser/Imágenes/Capturas/ 2>&1 | head -3", "P", 30) or ""; check("Impr. Pant. guarda una captura", "captura-" in f, f)
    vm.screenshot(os.path.join(out, "atajos-final.png"))
finally:
    vm.kill(); http.kill()
print("PASA todo" if res and all(res) else "HAY FALLOS"); sys.exit(0 if res and all(res) else 1)
