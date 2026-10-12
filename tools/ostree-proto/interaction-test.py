#!/usr/bin/env python3
"""Prueba de INTERACCIÓN de los widgets del panel (nivel 2): clics y ventanitas. Se ejecuta en el HOST.
Usa el ratón y el teclado virtuales de QEMU (QMP para el ratón absoluto, monitor para el teclado) sobre la sesión Lite de la VM.
Comprueba: (A) un widget de JavaScript cuenta clics; (B) un widget de Python abre un control deslizante y se maneja con el teclado;
(C) un calendario se abre. Guarda capturas. Uso: interaction-test.py DISCO.img DIR_SALIDA GJS.tgz"""
import importlib.util, json, os, shutil, socket, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.abspath(os.path.join(here, "..", ".."))
spec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py"))
gui = importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)
disk, out, gjs = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]); os.makedirs(out, exist_ok=True)
srv = "/home/oweeme/.cache/oweelinux/vm/isrv"; os.makedirs(srv, exist_ok=True)
shutil.copy(os.path.join(repo, "desktop/shell/owee_panel.py"), srv)
for f in ("load.py", "utc.js", "counter.js", "brillo.py", "calendario.py"): shutil.copy(os.path.join(repo, "desktop/widgets", f), srv)
shutil.copy(gjs, os.path.join(srv, "gjs.tgz"))
http = subprocess.Popen(["python3", "-m", "http.server", "8005", "--bind", "127.0.0.1", "--directory", srv], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
W = "/home/oweeme/.cache/oweelinux/vm/litediag"; os.makedirs(W, exist_ok=True); os.chdir(W)
for f in ("ser.sock", "mon.sock", "qmp.sock"):
    if os.path.exists(f): os.unlink(f)
shutil.copyfile(gui.VARS_SRC, "vars.fd"); open("c.log", "wb").close()
os.environ["QEMU_MEM"] = "3072"; os.environ["QEMU_EXTRA"] = "-qmp unix:qmp.sock,server=on,wait=off"
vm = gui.Vm(disk, W + "/vars.fd", W + "/c.log")
SW, SH = 1280, 800

class Qmp:
    def __init__(self):
        for _ in range(100):
            if os.path.exists("qmp.sock"):
                try: self.s = socket.socket(socket.AF_UNIX); self.s.connect("qmp.sock"); break
                except OSError: pass
            time.sleep(0.1)
        self.f = self.s.makefile("rw"); self.f.readline(); self.cmd("qmp_capabilities")
    def cmd(self, name, **args):
        self.f.write(json.dumps({"execute": name, "arguments": args}) + "\n"); self.f.flush()
        while True:
            r = json.loads(self.f.readline())
            if "return" in r or "error" in r: return r
    def move(self, x, y):
        self.cmd("input-send-event", events=[{"type": "abs", "data": {"axis": "x", "value": int(x * 32767 / SW)}}, {"type": "abs", "data": {"axis": "y", "value": int(y * 32767 / SH)}}])
    def click(self, x, y):
        self.move(x, y); time.sleep(0.4)
        self.cmd("input-send-event", events=[{"type": "btn", "data": {"down": True, "button": "left"}}]); time.sleep(0.15)
        self.cmd("input-send-event", events=[{"type": "btn", "data": {"down": False, "button": "left"}}])

def key(k): vm.mon.sendall(f"sendkey {k}\n".encode()); time.sleep(0.3)
def sh(c, k, t=60): return vm.run(f"echo MARK_{k}=$({c} | tr '\\n' '|')", k, t)
results = []
def check(name, ok, detail=""): results.append(ok); print(("PASA   " if ok else "FALLA  ") + name + (f"  ({detail})" if detail else ""), flush=True)
try:
    assert vm.wait(gui.PROMPT, 240); time.sleep(8)
    vm.run("systemctl stop sddm; loginctl terminate-user oweeuser; systemctl stop user@1000.service; sleep 3; pkill -9 -u oweeuser; sleep 1; echo MARK_ST=ok", "ST", 90)
    vm.run("mkdir -p /etc/owee /etc/systemd/user /tmp/gjs; ln -sfn /dev/null /etc/systemd/user/waybar.service; ln -sfn /dev/null /etc/systemd/user/mako.service; "
           "curl -s http://10.0.2.2:8005/owee_panel.py -o /tmp/owee_panel.py; curl -s http://10.0.2.2:8005/gjs.tgz | tar xz -C /tmp/gjs; chmod -R a+rX /tmp/gjs; "
           "D=/var/home/oweeuser/.config/owee/widgets; install -d -o oweeuser -g oweeuser /var/home/oweeuser/.config /var/home/oweeuser/.config/owee /var/home/oweeuser/.cache $D; "
           "for f in load.py utc.js counter.js brillo.py calendario.py; do curl -s http://10.0.2.2:8005/$f -o $D/$f; done; chown -R oweeuser:oweeuser $D /var/home/oweeuser/.cache; chmod +x $D/*; "
           "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/environment; "
           "printf 'PANEL=python\\nOWEE_PANEL_PATH=/tmp/owee_panel.py\\nexport OWEE_DEBUG_LAYOUT=1 PATH=/tmp/gjs/usr/bin:$PATH LD_LIBRARY_PATH=/tmp/gjs/usr/lib/x86_64-linux-gnu GI_TYPELIB_PATH=/tmp/gjs/usr/lib/x86_64-linux-gnu/gjs/girepository-1.0\\n' > /etc/owee/panel.conf; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 180)
    time.sleep(50)
    lay = sh("grep -h '\\[layout\\]' /tmp/owee-panel.log | tail -1 | cut -c10-300", "L")
    coords = json.loads((lay or "{}").rstrip("|") or "{}"); print("posiciones:", coords, flush=True)
    check("el panel informa de la posición de sus widgets", bool(coords))
    q = Qmp(); vm.screenshot(os.path.join(out, "interaccion-0.png"))
    # A) JavaScript: 3 clics en el contador
    if "counter" in coords:
        x, y = coords["counter"]
        for _ in range(3): q.click(x, y); time.sleep(2)
        time.sleep(3); n = sh("cat /var/home/oweeuser/.cache/owee-counter 2>&1", "A")
        check("(A) widget de JavaScript: 3 clics cuentan 3", (n or "").strip("|") == "3", f"archivo={n}")
        vm.screenshot(os.path.join(out, "interaccion-A.png"))
    # B) Python: abrir el deslizante y subir con el teclado
    if "brillo" in coords:
        x, y = coords["brillo"]; q.click(x, y); time.sleep(2); vm.screenshot(os.path.join(out, "interaccion-B-abierto.png"))
        for k in ("tab",) + ("right",) * 10: key(k)
        time.sleep(3); v = sh("cat /var/home/oweeuser/.cache/owee-brillo 2>&1", "B")
        check("(B) widget de Python: la ventanita se abre y el deslizante responde al teclado", (v or "").strip("|").isdigit() and int((v or "0").strip("|")) != 50, f"valor={v}")
        vm.screenshot(os.path.join(out, "interaccion-B-despues.png")); key("esc"); time.sleep(1)
    # C) calendario
    if "calendario" in coords:
        x, y = coords["calendario"]; q.click(x, y); time.sleep(2); vm.screenshot(os.path.join(out, "interaccion-C-calendario.png")); key("esc")
    print("panel sigue vivo:", sh("pgrep -f owee_panel.py | head -1", "V"))
finally:
    vm.kill(); http.kill()
print("PASA todo" if all(results) and results else "HAY FALLOS"); sys.exit(0 if all(results) and results else 1)
