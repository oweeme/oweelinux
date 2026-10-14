import importlib.util, os, shutil, subprocess, sys, time
spec = importlib.util.spec_from_file_location("gui", "/home/oweeme/Dev/oweelinux/tools/ostree-proto/gui-boot-test.py")
gui = importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)
S = "/tmp/owee-srv"
http = subprocess.Popen(["python3", "-m", "http.server", "8003", "--bind", "127.0.0.1", "--directory", S], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
W = "/home/oweeme/.cache/oweelinux/vm/litediag"; os.makedirs(W, exist_ok=True); os.chdir(W)
for f in ("ser.sock", "mon.sock"):
    if os.path.exists(f): os.unlink(f)
shutil.copyfile(gui.VARS_SRC, "vars.fd"); open("c.log", "wb").close(); os.environ["QEMU_MEM"] = "3072"
vm = gui.Vm("/home/oweeme/.cache/oweelinux/vm/lite-disk.img", W + "/vars.fd", W + "/c.log")
ENV = "HOME=/home/oweeuser XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 GSK_RENDERER=cairo "
GJS = "LD_LIBRARY_PATH=/tmp/gjs/usr/lib/x86_64-linux-gnu GI_TYPELIB_PATH=/tmp/gjs/usr/lib/x86_64-linux-gnu/gjs/girepository-1.0 "
U = f"runuser -u oweeuser -- env {ENV}"
def res(cmd, t=90):
    return vm.run(f"echo MARK_R=$({cmd} 2>&1 | grep -E 'RESULT|rror|Traceback|not found' | head -3 | tr '\\n' '|' | cut -c1-220)", "R", t)
def startup(cmd):   # tiempo de arranque del intérprete/programa sin interfaz (ms)
    return vm.run(f"s=$(date +%s%N); {cmd} >/dev/null 2>&1; e=$(date +%s%N); echo MARK_T=$(( (e-s)/1000000 ))ms", "T", 60)
try:
    assert vm.wait(gui.PROMPT, 240); time.sleep(8)
    vm.run("systemctl stop sddm; loginctl terminate-user oweeuser; systemctl stop user@1000.service; sleep 3; pkill -9 -u oweeuser; sleep 1; echo MARK_ST=ok", "ST", 90)
    vm.run("mkdir -p /etc/owee /etc/systemd/user /tmp/m /tmp/gjs; ln -sfn /dev/null /etc/systemd/user/waybar.service; ln -sfn /dev/null /etc/systemd/user/mako.service; "
           "for f in mem.py tg.py t.js hello_c hello_rs; do curl -s http://10.0.2.2:8003/$f -o /tmp/m/$f; done; chmod +x /tmp/m/hello_c /tmp/m/hello_rs; curl -s http://10.0.2.2:8003/gjs.tgz | tar xz -C /tmp/gjs; chmod -R a+rX /tmp/m /tmp/gjs; "
           "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\n' > /etc/environment; printf 'PANEL=none\\n' > /etc/owee/panel.conf; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 180)
    time.sleep(45)
    print("C     ", res(f"{U} /tmp/m/hello_c"), flush=True)
    print("Rust  ", res(f"{U} /tmp/m/hello_rs"), flush=True)
    print("Python", res(f"{U} TAG=python-pygobject python3 /tmp/m/tg.py"), flush=True)
    print("GJS   ", res(f"{U} {GJS} /tmp/gjs/usr/bin/gjs /tmp/m/t.js"), flush=True)
    print("arranque en vacío (ms): C", startup("/bin/true"), "| python3 -c pass", startup("python3 -c pass"),
          "| python+gtk import", startup("python3 -c 'import gi; gi.require_version(\"Gtk\",\"4.0\"); from gi.repository import Gtk'"),
          "| gjs -c 1", startup(f"env {GJS} /tmp/gjs/usr/bin/gjs -c 1"), flush=True)
finally:
    vm.kill(); http.kill()
