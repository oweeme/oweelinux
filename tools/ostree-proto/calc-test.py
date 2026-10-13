#!/usr/bin/env python3
"""Calculadora de OweeLinux (teclado y ratón virtuales). Se ejecuta en el HOST. Despliega panel y app de ajustes, comprueba que el panel cambia al instante
al modificar ~/.config/owee/settings.json y que la app de ajustes escribe ese archivo y cambia el fondo (swaybg).
Uso: calc-test.py DISCO.img DIR_SALIDA"""
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
shutil.copy(os.path.join(here, "mock-wpctl"), srv); shutil.rmtree(srv + "/apps", ignore_errors=True); shutil.copytree(os.path.join(repo, "desktop/apps"), srv + "/apps", ignore=shutil.ignore_patterns("__pycache__")); subprocess.run(["tar", "czf", srv + "/apps.tgz", "-C", srv, "apps"], check=True)
shutil.copy(os.path.join(repo, "desktop/session/owee-wallpaper"), srv + "/session")
for nm, col in (("Owee", "#EFF0F1"), ("Owee-Light", "#17231e")): subprocess.run(["python3", os.path.join(repo, "desktop/theme/icons/gen_icons.py"), srv + "/icons", col, nm], check=True, stdout=subprocess.DEVNULL)
subprocess.run(["tar", "czf", srv + "/owee-icons.tgz", "-C", srv + "/icons", "Owee", "Owee-Light"], check=True)
for f in os.listdir(os.path.join(repo, "desktop/widgets/sistema")): shutil.copy(os.path.join(repo, "desktop/widgets/sistema", f), srv)
shutil.copy(os.path.join(here, "mock-wpctl"), srv); shutil.rmtree(srv + "/apps", ignore_errors=True); shutil.copytree(os.path.join(repo, "desktop/apps"), srv + "/apps", ignore=shutil.ignore_patterns("__pycache__")); subprocess.run(["tar", "czf", srv + "/apps.tgz", "-C", srv, "apps"], check=True)
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
           "mkdir -p /tmp/session /tmp/mockbin; curl -s http://10.0.2.2:8006/shell.tgz | tar xz -C /tmp; curl -s http://10.0.2.2:8006/apps.tgz | tar xz -C /tmp; chmod +x /tmp/apps/calculadora/*.py; chmod +x /tmp/shell/*.py; for f in owee-apply-display owee-idle; do curl -s http://10.0.2.2:8006/session/$f -o /tmp/session/$f; chmod +x /tmp/session/$f; done; curl -s http://10.0.2.2:8006/mock-wpctl -o /tmp/mockbin/wpctl; chmod 755 /tmp/mockbin/wpctl; curl -s http://10.0.2.2:8006/session/owee-wallpaper -o /tmp/session/owee-wallpaper; chmod +x /tmp/session/owee-wallpaper; mkdir -p /var/home/oweeuser/.local/share/icons; curl -s http://10.0.2.2:8006/owee-icons.tgz | tar xz -C /var/home/oweeuser/.local/share/icons; chown -R oweeuser:oweeuser /var/home/oweeuser/.local; D=/var/home/oweeuser/.config/owee/widgets; install -d -o oweeuser -g oweeuser /var/home/oweeuser/.config /var/home/oweeuser/.config/owee $D; "
           "for f in 10-red.py 20-volumen.py 30-bateria.py; do curl -s http://10.0.2.2:8006/$f -o $D/$f; done; chown -R oweeuser:oweeuser $D; chmod +x $D/*; "
           "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/environment; "
           "printf 'PANEL=python\\nOWEE_PANEL_PATH=/tmp/shell/owee_panel.py\\nexport OWEE_DEBUG_LAYOUT=1 OWEE_POWER_SUPPLY_DIR=/tmp/ps PATH=/tmp/mockbin:$PATH\\n' > /etc/owee/panel.conf; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 120)
    time.sleep(40)
    time.sleep(40)
    q = Qmp(); time.sleep(3)
    sh(U + "WAYLAND_DISPLAY=wayland-0 OWEE_CALC_DEBUG=/tmp/calc-last sh -c 'nohup python3 /tmp/apps/calculadora/owee_calc.py > /tmp/calc.log 2>&1 &'", "A", 30); time.sleep(8)
    print("log:", sh("grep -v dconf /tmp/calc.log | grep -v a11y | head -8 | cut -c1-200", "LG", 30))
    vm.screenshot(os.path.join(out, "calc-0.png"))
    F = lambda cmd, k, t=30: sh(U + cmd, k, t) or ""
    for k in ["1", "2", "shift-equal", "7", "shift-8", "3"]: key(k)                       # 12+7*3 con el teclado
    time.sleep(1); vm.screenshot(os.path.join(out, "calc-1.png")); key("ret"); time.sleep(1.5)
    r = F("cat /tmp/calc-last", "R"); check("Calculadora: 12+7×3 = 33 con el teclado", r.strip("|") == "33", r); vm.screenshot(os.path.join(out, "calc-2.png"))
    q.click(511, 453); time.sleep(1)                                                         # AC con el ratón
    q.click(682, 517); time.sleep(0.5); q.click(767, 517); time.sleep(0.5); q.click(682, 517); time.sleep(0.5); q.click(767, 709); time.sleep(1.5)       # 9 × 9 =
    r = F("cat /tmp/calc-last", "R2"); check("Calculadora: 9×9 = 81 con el ratón", r.strip("|") == "81", r); vm.screenshot(os.path.join(out, "calc-3.png"))
    q.click(493, 143); time.sleep(1.5); vm.screenshot(os.path.join(out, "calc-cientifica.png"))                  # f(x): modo científico
finally:
    vm.kill(); http.kill()
print("PASA todo" if res and all(res) else "HAY FALLOS"); sys.exit(0 if res and all(res) else 1)
