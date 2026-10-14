#!/usr/bin/env python3
"""Bandeja de apps (StatusNotifierItem). Se ejecuta en el HOST. Despliega el panel y una app FALSA con icono de bandeja (mock-sni.py), comprueba que el icono
aparece, que el clic izquierdo llama a Activate y el derecho a ContextMenu, y que al morir la app el icono desaparece.
Uso: tray-test.py DISCO.img DIR_SALIDA"""
import importlib.util, json, os, shutil, socket, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.abspath(os.path.join(here, "..", ".."))
spec = importlib.util.spec_from_file_location("it", os.path.join(here, "interaction-test.py"))
src = open(os.path.join(here, "interaction-test.py")).read()
gspec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py")); gui = importlib.util.module_from_spec(gspec); gspec.loader.exec_module(gui)
disk, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
srv = "/home/oweeme/.cache/oweelinux/vm/ssrv"; os.makedirs(srv, exist_ok=True)
shutil.copy(os.path.join(repo, "desktop/shell/owee_panel.py"), srv); shutil.copy(os.path.join(repo, "desktop/shell/owee_tray.py"), srv); shutil.copy(os.path.join(here, "mock-sni.py"), srv)
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
           "curl -s http://10.0.2.2:8006/owee_panel.py -o /tmp/owee_panel.py; curl -s http://10.0.2.2:8006/owee_tray.py -o /tmp/owee_tray.py; curl -s http://10.0.2.2:8006/mock-sni.py -o /tmp/mock-sni.py; D=/var/home/oweeuser/.config/owee/widgets; install -d -o oweeuser -g oweeuser /var/home/oweeuser/.config /var/home/oweeuser/.config/owee $D; "
           "for f in 10-red.py 20-volumen.py 30-bateria.py; do curl -s http://10.0.2.2:8006/$f -o $D/$f; done; chown -R oweeuser:oweeuser $D; chmod +x $D/*; "
           "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/environment; "
           "printf 'PANEL=python\\nOWEE_PANEL_PATH=/tmp/owee_panel.py\\nexport OWEE_DEBUG_LAYOUT=1 OWEE_POWER_SUPPLY_DIR=/tmp/ps PATH=/tmp/mockbin:$PATH\\n' > /etc/owee/panel.conf; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 120)
    time.sleep(40)
    time.sleep(40)
    q = Qmp(); time.sleep(2)
    sh(U + "sh -c 'rm -f /tmp/sni.log; nohup python3 /tmp/mock-sni.py >/tmp/sni.out 2>&1 &' ; sleep 1", "S", 30)
    time.sleep(10)
    check("el panel registró la app (registrado)", "registrado" in (sh("cat /tmp/sni.log", "R", 30) or ""), sh("cat /tmp/sni.log /tmp/sni.out | head -3", "R2", 30))
    lay = json.loads((sh("grep -h '\\[layout\\]' /run/user/1000/owee-panel.log | tail -1 | cut -c10-400", "L") or "{}").rstrip("|") or "{}"); print("posiciones:", lay, flush=True)
    check("aparece el icono en la bandeja", "tray" in lay); vm.screenshot(os.path.join(out, "bandeja.png"))
    if "tray" in lay:
        q.click(*lay["tray"]); time.sleep(2)
        for b in (1, 3):
            if b == 3:
                q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": True, "button": "right"}}]); time.sleep(0.15); q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": False, "button": "right"}}]); time.sleep(2)
        log = sh("cat /tmp/sni.log", "G", 30) or ""
        check("clic izquierdo llama a Activate", "Activate" in log, log); check("clic derecho llama a ContextMenu", "ContextMenu" in log, log)
    sh("pkill -f mock-sni.py", "K", 30); time.sleep(6)
    lay2 = json.loads((sh("grep -h '\\[layout\\]' /run/user/1000/owee-panel.log | tail -1 | cut -c10-400", "L2") or "{}").rstrip("|") or "{}")
    check("al morir la app el icono desaparece", "tray" not in lay2); vm.screenshot(os.path.join(out, "bandeja-sin.png"))
    print("memoria del panel:", sh("pid=$(pgrep -f owee_panel.py | tail -1); awk '/^(Pss|Rss):/{printf \"%s=%dMB \", $1, $2/1024}' /proc/$pid/smaps_rollup", "M"))
finally:
    vm.kill(); http.kill()
print("PASA todo" if res and all(res) else "HAY FALLOS"); sys.exit(0 if res and all(res) else 1)
