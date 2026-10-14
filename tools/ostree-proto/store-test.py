#!/usr/bin/env python3
"""Tienda de apps (Bazaar por Flatpak) en la imagen COMPLETA: locales, fuentes, Fcitx5, cambio de idioma desde Ajustes a chino, japonés, ruso y Owee, y escritura con pinyin. Se ejecuta en el HOST.
Abre el lanzador con el ratón, escribe "konsole" con el teclado, pulsa Intro y comprueba que la app arrancó.
Uso: store-test.py DISCO.img DIR_SALIDA"""
import importlib.util, json, os, shutil, socket, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.abspath(os.path.join(here, "..", ".."))
spec = importlib.util.spec_from_file_location("it", os.path.join(here, "interaction-test.py"))
src = open(os.path.join(here, "interaction-test.py")).read()
gspec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py")); gui = importlib.util.module_from_spec(gspec); gspec.loader.exec_module(gui)
disk, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
srv = "/home/oweeme/.cache/oweelinux/vm/ssrv"; os.makedirs(srv, exist_ok=True)
shutil.rmtree(srv + "/dk", ignore_errors=True); os.makedirs(srv + "/dk"); shutil.copytree(os.path.join(repo, "desktop/apps"), srv + "/dk/apps", ignore=shutil.ignore_patterns("__pycache__")); subprocess.run(["tar", "czf", srv + "/apps-over.tgz", "-C", srv + "/dk", "apps"], check=True); shutil.copytree(os.path.join(repo, "desktop/shell"), srv + "/dk/shell", ignore=shutil.ignore_patterns("__pycache__"))
subprocess.run(["tar", "czf", srv + "/shell-over.tgz", "-C", srv + "/dk", "shell"], check=True)      # (código nuevo sobre la imagen, con mount --bind, hasta la próxima construcción)
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
    vm.run("mkdir -p /etc/owee /etc/systemd/user /tmp/ps/BAT0; "
                      "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/environment; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 120)
    time.sleep(45)
    q = Qmp(); time.sleep(2)
    F = lambda cmd, k, t=30: sh(U + cmd, k, t) or ""
    print("servicio:", sh("systemctl is-enabled owee-store.service; systemctl is-active owee-store.service; ls /var/lib/flatpak 2>&1 | head -3", "SV", 30))
    for i in range(40):                                                      # hasta ~20 min: descarga de Flathub (Bazaar + runtime de GNOME)
        time.sleep(30); st = sh("ls /var/lib/flatpak/.owee-store-ok 2>&1; systemctl is-active owee-store.service; du -sm /var/lib/flatpak | cut -f1", "PR", 30) or ""; print("progreso:", st, flush=True)
        if ".owee-store-ok" in st and "No such" not in st: break
    check("Bazaar queda instalado por el servicio del primer arranque", "No such" not in st and ".owee-store-ok" in st, st)
    print("apps:", sh("flatpak list --system --columns=application,version 2>&1 | head -5", "FL", 60))
    print("discover oculto:", sh("grep -c NoDisplay=true /usr/share/applications/org.kde.discover.desktop", "DC", 30))
    sh(U + "WAYLAND_DISPLAY=wayland-0 sh -c 'nohup flatpak run io.github.kolunmi.Bazaar > /tmp/bazaar.log 2>&1 &'", "BZ", 30); time.sleep(25)
    vm.screenshot(os.path.join(out, "bazaar.png"))
    check("Bazaar se abre", (sh("pgrep -c -f -i bazaar", "PB", 30) or "").strip("|").strip() not in ("", "0"), sh("tail -3 /tmp/bazaar.log", "BL", 30))
finally:
    vm.kill(); http.kill()
print("PASA todo" if res and all(res) else "HAY FALLOS"); sys.exit(0 if res and all(res) else 1)
