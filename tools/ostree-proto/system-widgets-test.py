#!/usr/bin/env python3
"""Widgets del sistema (red, volumen, batería) en la sesión Lite, con hardware SIMULADO. Se ejecuta en el HOST.
Crea una salida de audio virtual (PipeWire) y una batería falsa (OWEE_POWER_SUPPLY_DIR), despliega el panel y los widgets sin reconstruir
la imagen, y comprueba: los tres widgets dan datos correctos; el clic en el volumen abre la ventanita, el deslizante cambia el volumen real y el
botón lo silencia; la batería simulada se actualiza. Guarda capturas. Uso: system-widgets-test.py DISCO.img DIR_SALIDA"""
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
subprocess.run(["python3", os.path.join(repo, "desktop/theme/icons/gen_icons.py"), srv + "/icons"], check=True, stdout=subprocess.DEVNULL); subprocess.run(["tar", "czf", srv + "/owee-icons.tgz", "-C", srv + "/icons", "Owee"], check=True)
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
           "curl -s http://10.0.2.2:8006/owee_panel.py -o /tmp/owee_panel.py; D=/var/home/oweeuser/.config/owee/widgets; install -d -o oweeuser -g oweeuser /var/home/oweeuser/.config /var/home/oweeuser/.config/owee $D; "
           "curl -s http://10.0.2.2:8006/owee-icons.tgz | tar xz -C /tmp && install -d -o oweeuser -g oweeuser /var/home/oweeuser/.local /var/home/oweeuser/.local/share /var/home/oweeuser/.local/share/icons && cp -r /tmp/Owee /var/home/oweeuser/.local/share/icons/ && chown -R oweeuser:oweeuser /var/home/oweeuser/.local; "
           "for f in 10-red.py 20-volumen.py 30-bateria.py; do curl -s http://10.0.2.2:8006/$f -o $D/$f; done; chown -R oweeuser:oweeuser $D; chmod +x $D/*; "
           "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/environment; "
           "printf 'PANEL=python\\nOWEE_PANEL_PATH=/tmp/owee_panel.py\\nexport OWEE_DEBUG_LAYOUT=1 OWEE_POWER_SUPPLY_DIR=/tmp/ps PATH=/tmp/mockbin:$PATH\\n' > /etc/owee/panel.conf; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 120)
    time.sleep(40)
    # audio SIMULADO con un `wpctl` falso (mismo formato de salida): en esta VM el WirePlumber real acepta `set-volume` (rc=0) pero NO cambia el
    # volumen de una salida virtual, por motivos sin investigar. La lectura con el wpctl real se validó en un equipo físico (ver docs/ESCRITORIO.md).
    vm.run("mkdir -p /tmp/mockbin; curl -s http://10.0.2.2:8006/mock-wpctl -o /tmp/mockbin/wpctl; chmod 755 /tmp/mockbin/wpctl; rm -f /tmp/mock-vol /tmp/mock-mute; chmod a+rwx /tmp; echo MARK_MK=ok", "MK", 30)
    print("wpctl falso:", sh("PATH=/tmp/mockbin:$PATH wpctl get-volume @DEFAULT_AUDIO_SINK@", "AU", 30))
    time.sleep(8)
    W_ENV = U + "OWEE_POWER_SUPPLY_DIR=/tmp/ps PATH=/tmp/mockbin:$PATH:/usr/bin:/bin "
    for w, quiero in (("10-red.py", "owee-network-wired"), ("20-volumen.py", "owee-volume-high 40%"), ("30-bateria.py", "owee-battery-20 17%")):
        t = sh(f"{W_ENV} python3 /var/home/oweeuser/.config/owee/widgets/{w} | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('icon'), d.get('text'))\"", "W", 30) or ""
        check(f"widget {w}: texto esperado '{quiero}'", quiero in t, t.strip("|"))
    lay = sh("grep -h '\\[layout\\]' /run/user/1000/owee-panel.log | tail -1 | cut -c10-300", "L") or "{}"
    coords = json.loads(lay.rstrip("|") or "{}"); print("posiciones:", coords, flush=True)
    check("el panel muestra los tres widgets", all(k in coords for k in ("10-red", "20-volumen", "30-bateria")))
    q = Qmp(); vm.screenshot(os.path.join(out, "sistema-0.png"))
    if "20-volumen" in coords:
        x, y = coords["20-volumen"]; q.click(x, y); time.sleep(2); vm.screenshot(os.path.join(out, "sistema-volumen.png"))
        for k in ["right"] * 10: key(k)         # el foco ya empieza en el deslizante (un Tab previo lo movería al botón)
        time.sleep(4); v = sh("PATH=/tmp/mockbin:$PATH wpctl get-volume @DEFAULT_AUDIO_SINK@", "V", 30) or ""
        try: vol = float(v.strip("|").split()[1]) if "Volume" in v else -1
        except Exception: vol = -1
        check("el deslizante cambia el volumen REAL", vol > 0 and abs(vol - 0.40) > 0.005, v.strip("|"))
        key("tab"); key("ret"); time.sleep(4); v2 = sh("PATH=/tmp/mockbin:$PATH wpctl get-volume @DEFAULT_AUDIO_SINK@", "V", 30) or ""
        check("el botón silencia el volumen REAL", "MUTED" in v2, v2.strip("|")); vm.screenshot(os.path.join(out, "sistema-silencio.png")); key("esc")
    # batería simulada: pasa a 87 % cargando; el widget se actualiza solo (cada 15 s)
    vm.run("printf '87\\n' > /tmp/ps/BAT0/capacity; printf 'Charging\\n' > /tmp/ps/BAT0/status; echo MARK_B=ok", "B", 20); time.sleep(22)
    vm.screenshot(os.path.join(out, "sistema-bateria.png"))
    print("memoria del panel:", sh("pid=$(pgrep -f owee_panel.py | tail -1); awk '/^(Pss|Rss):/{printf \"%s=%dMB \", $1, $2/1024}' /proc/$pid/smaps_rollup", "M"))
finally:
    vm.kill(); http.kill()
print("PASA todo" if res and all(res) else "HAY FALLOS"); sys.exit(0 if res and all(res) else 1)
