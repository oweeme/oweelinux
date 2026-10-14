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
ENV = "HOME=/home/oweeuser XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 GSK_RENDERER=cairo QT_QPA_PLATFORM=wayland "
QT = "PYTHONPATH=/tmp/pys/usr/lib/python3/dist-packages LD_LIBRARY_PATH=/tmp/pys/usr/lib/x86_64-linux-gnu "
U = f"runuser -u oweeuser -- env {ENV}"
def res(cmd, t=90):
    out = vm.run(f"echo MARK_R=$({cmd} 2>&1 | grep -E 'RESULT|rror|Traceback' | tr '\\n' '|' | cut -c1-200)", "R", t); return out
try:
    assert vm.wait(gui.PROMPT, 240); time.sleep(8)
    vm.run("systemctl stop sddm; loginctl terminate-user oweeuser; systemctl stop user@1000.service; sleep 3; pkill -9 -u oweeuser; sleep 1; echo MARK_ST=ok", "ST", 90)
    vm.run("mkdir -p /etc/owee /etc/systemd/user /tmp/m /tmp/pys; ln -sfn /dev/null /etc/systemd/user/waybar.service; ln -sfn /dev/null /etc/systemd/user/mako.service; "
           "for f in mem.py tg.py tq.py; do curl -s http://10.0.2.2:8003/$f -o /tmp/m/$f; done; curl -s http://10.0.2.2:8003/pys.tgz | tar xz -C /tmp/pys; chmod -R a+rX /tmp/m /tmp/pys; "
           "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\n' > /etc/environment; printf 'PANEL=none\\n' > /etc/owee/panel.conf; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 120)
    time.sleep(45)
    print("base libre:", vm.run("echo MARK_F=$(free -m | awk '/Mem:/{print $3}')MB", "F", 30))
    print("1. GTK4 solo           ", res(f"{U} TAG=gtk4-solo python3 /tmp/m/tg.py"), flush=True)
    print("2. Qt6/PySide6 solo    ", res(f"{U} {QT} TAG=qt6-solo python3 /tmp/m/tq.py"), flush=True)
    vm.run(f"({U} QT_QPA_PLATFORM=wayland konsole > /dev/null 2>&1 &); echo MARK_K=ok", "K", 30); time.sleep(15)
    print("3. GTK4 con Konsole(Qt)", res(f"{U} TAG=gtk4+konsole python3 /tmp/m/tg.py"), flush=True)
    print("4. Qt6 con Konsole(Qt) ", res(f"{U} {QT} TAG=qt6+konsole python3 /tmp/m/tq.py"), flush=True)
    vm.run(f"({U} HOLD=60 TAG=primer-gtk python3 /tmp/m/tg.py > /dev/null 2>&1 &); echo MARK_A=ok", "A", 30); time.sleep(10)
    print("5. 2.º GTK4 con otro GTK4 ya cargado", res(f"{U} TAG=gtk4+otro-gtk4 python3 /tmp/m/tg.py"), flush=True)
finally:
    vm.kill(); http.kill()
