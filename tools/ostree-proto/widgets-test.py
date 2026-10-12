#!/usr/bin/env python3
"""Prueba de widgets de script (Python y JavaScript/GJS) en el panel. Se ejecuta en el HOST.
Despliega en la VM (sin reconstruir la imagen): el panel actual, los widgets de ejemplo, un widget que FALLA y otro que se CUELGA,
y GJS (extraído de un .tgz). Comprueba que los widgets aparecen, que los defectuosos no tumban el panel y mide la memoria del panel.
Uso: widgets-test.py DISCO.img DIR_SALIDA GJS.tgz"""
import importlib.util, os, shutil, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.abspath(os.path.join(here, "..", ".."))
spec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py"))
gui = importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)
disk, out, gjs = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]); os.makedirs(out, exist_ok=True)
srv = os.path.join("/home/oweeme/.cache/oweelinux/vm", "wsrv"); os.makedirs(srv, exist_ok=True)
shutil.copy(os.path.join(repo, "desktop/shell/owee_panel.py"), srv)
for f in ("load.py", "utc.js"): shutil.copy(os.path.join(repo, "desktop/widgets/ejemplos", f), srv)
shutil.copy(gjs, os.path.join(srv, "gjs.tgz"))
open(os.path.join(srv, "bad.sh"), "w").write("#!/bin/sh\necho esto no es json\n")
open(os.path.join(srv, "slow.sh"), "w").write("#!/bin/sh\n# owee-interval: 30\nsleep 20\necho '{\"text\":\"nunca\"}'\n")
http = subprocess.Popen(["python3", "-m", "http.server", "8004", "--bind", "127.0.0.1", "--directory", srv], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
W = "/home/oweeme/.cache/oweelinux/vm/litediag"; os.makedirs(W, exist_ok=True); os.chdir(W)
for f in ("ser.sock", "mon.sock"):
    if os.path.exists(f): os.unlink(f)
shutil.copyfile(gui.VARS_SRC, "vars.fd"); open("c.log", "wb").close(); os.environ["QEMU_MEM"] = "3072"
vm = gui.Vm(disk, W + "/vars.fd", W + "/c.log")
def sh(c, k, t=60): return vm.run(f"echo MARK_{k}=$({c} | tr '\\n' '|')", k, t)
try:
    assert vm.wait(gui.PROMPT, 240); time.sleep(8)
    vm.run("systemctl stop sddm; loginctl terminate-user oweeuser; systemctl stop user@1000.service; sleep 3; pkill -9 -u oweeuser; sleep 1; echo MARK_ST=ok", "ST", 90)
    vm.run("mkdir -p /etc/owee /etc/systemd/user /tmp/gjs; ln -sfn /dev/null /etc/systemd/user/waybar.service; ln -sfn /dev/null /etc/systemd/user/mako.service; "
           "curl -s http://10.0.2.2:8004/owee_panel.py -o /tmp/owee_panel.py; curl -s http://10.0.2.2:8004/gjs.tgz | tar xz -C /tmp/gjs; chmod -R a+rX /tmp/gjs; "
           "D=/var/home/oweeuser/.config/owee/widgets; install -d -o oweeuser -g oweeuser /var/home/oweeuser/.config /var/home/oweeuser/.config/owee $D; "
           "for f in load.py utc.js bad.sh slow.sh; do curl -s http://10.0.2.2:8004/$f -o $D/$f; done; chown -R oweeuser:oweeuser $D; chmod +x $D/*; "
           "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/environment; "
           "printf 'PANEL=python\\nOWEE_PANEL_PATH=/tmp/owee_panel.py\\nexport PATH=/tmp/gjs/usr/bin:$PATH LD_LIBRARY_PATH=/tmp/gjs/usr/lib/x86_64-linux-gnu GI_TYPELIB_PATH=/tmp/gjs/usr/lib/x86_64-linux-gnu/gjs/girepository-1.0\\n' > /etc/owee/panel.conf; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 180)
    time.sleep(40); vm.screenshot(os.path.join(out, "widgets-1.png"))
    print("salida de widgets a mano:", sh("D=/var/home/oweeuser/.config/owee/widgets; PATH=/tmp/gjs/usr/bin:$PATH LD_LIBRARY_PATH=/tmp/gjs/usr/lib/x86_64-linux-gnu GI_TYPELIB_PATH=/tmp/gjs/usr/lib/x86_64-linux-gnu/gjs/girepository-1.0 sh -c \"$D/load.py; $D/utc.js\" 2>&1 | cut -c1-110", "A"))
    time.sleep(25); vm.screenshot(os.path.join(out, "widgets-2.png"))
    print("panel vivo y su memoria:", sh("pid=$(pgrep -f owee_panel.py | tail -1); echo pid=$pid; awk '/^(Pss|Rss):/{printf \"%s=%dMB \", $1, $2/1024}' /proc/$pid/smaps_rollup", "B"))
    print("procesos widget sueltos (no deben quedar):", sh("ps -eo comm | grep -c -E 'slow.sh|sleep'", "C"))
finally:
    vm.kill(); http.kill()
