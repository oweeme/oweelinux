#!/usr/bin/env python3
"""Imagen Lite COMPLETA sin ayudas: el panel, el lanzador y los widgets vienen en la imagen (nada se despliega por HTTP). Se ejecuta en el HOST.
Abre el lanzador con el ratón, escribe "konsole" con el teclado, pulsa Intro y comprueba que la app arrancó.
Uso: image-lite-test.py DISCO.img DIR_SALIDA"""
import importlib.util, json, os, shutil, socket, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.abspath(os.path.join(here, "..", ".."))
spec = importlib.util.spec_from_file_location("it", os.path.join(here, "interaction-test.py"))
src = open(os.path.join(here, "interaction-test.py")).read()
gspec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py")); gui = importlib.util.module_from_spec(gspec); gspec.loader.exec_module(gui)
disk, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
srv = "/home/oweeme/.cache/oweelinux/vm/ssrv"; os.makedirs(srv, exist_ok=True)
shutil.copy(os.path.join(repo, "desktop/shell/owee_panel.py"), srv)
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
    pr = sh("pgrep -a -u oweeuser -f owee_panel | cut -c1-90; pgrep -c -u oweeuser waybar", "PR", 30) or ""
    check("el panel de la imagen (/usr/libexec/owee) corre y waybar no", "/usr/libexec/owee/owee_panel.py" in pr and pr.rstrip("|").endswith("0"), pr)
    wl = sh("ls /usr/share/owee/widgets; python3 -c \"import gi; gi.require_version('Gtk','4.0')\" && echo gtk-ok; which gjs", "WL", 30) or ""; print("imagen:", wl)
    q = Qmp(); time.sleep(4); vm.screenshot(os.path.join(out, "imagen-0.png"))
    q.click(60, 24); time.sleep(3); vm.screenshot(os.path.join(out, "imagen-abierto.png"))
    for k in "konsole": key(k)
    time.sleep(1); vm.screenshot(os.path.join(out, "imagen-busqueda.png"))
    key("ret"); time.sleep(10)
    n = sh("pgrep -c -u oweeuser konsole", "K", 30) or ""
    check("Intro lanza la primera coincidencia (konsole)", n.strip("|").strip().isdigit() and int(n.strip("|").strip()) > 0, n.strip("|"))
    vm.screenshot(os.path.join(out, "imagen-app.png"))
    print("memoria del panel:", sh("pid=$(pgrep -f owee_panel.py | tail -1); awk '/^(Pss|Rss):/{printf \"%s=%dMB \", $1, $2/1024}' /proc/$pid/smaps_rollup", "M"))
finally:
    vm.kill(); http.kill()
print("PASA todo" if res and all(res) else "HAY FALLOS"); sys.exit(0 if res and all(res) else 1)
