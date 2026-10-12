#!/usr/bin/env python3
"""Capturas del branding: escritorio, menú de aplicaciones y pantalla de login, más datos de configuración.
Uso: brand-shots.py DISCO.img DIR_SALIDA PREFIJO"""
import importlib.util, os, shutil, sys, time
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py"))
gui = importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)
disk, out, pre = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3]; os.makedirs(out, exist_ok=True)
work = "/home/oweeme/.cache/oweelinux/vm/brand"; os.makedirs(work, exist_ok=True); os.chdir(work)
for f in ("ser.sock", "mon.sock"):
    if os.path.exists(f): os.unlink(f)
shutil.copyfile(gui.VARS_SRC, "vars.fd"); open("c.log", "wb").close(); os.environ.setdefault("QEMU_MEM", "3072")
vm = gui.Vm(disk, work + "/vars.fd", work + "/c.log")
U = "runuser -u oweeuser -- env DISPLAY=:0 XAUTHORITY=/home/oweeuser/.Xauthority "
def shot(n): vm.screenshot(os.path.join(out, f"{pre}-{n}.png")); print("captura", f"{pre}-{n}.png", flush=True)
try:
    assert vm.wait(gui.PROMPT, 240)
    for _ in range(100):
        if vm.run("echo MARK_P=$(pgrep -x plasmashell | head -1)", "P", 10): break
        time.sleep(3)
    time.sleep(35); shot("escritorio")
    print("os-release:", vm.run("echo MARK_O=$(. /etc/os-release; echo $PRETTY_NAME)", "O", 20))
    print("esquema:", vm.run(f"echo MARK_C=$({U}kreadconfig6 --file kdeglobals --group General --key ColorScheme)", "C", 30))
    print("aspecto:", vm.run(f"echo MARK_L=$({U}kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage)", "L", 30))
    print("iconos:", vm.run(f"echo MARK_I=$({U}kreadconfig6 --file kdeglobals --group Icons --key Theme)", "I", 30))
    vm.mon.sendall(b"sendkey meta_l\n"); time.sleep(6); shot("menu"); vm.mon.sendall(b"sendkey esc\n"); time.sleep(2)
    vm.run("rm -f /etc/sddm.conf.d/10-owee-test.conf; systemctl restart sddm; echo MARK_T=ok", "T", 60)   # sin autologin: SDDM muestra el login
    for _ in range(40):                       # esperar a que SDDM muestre el login (greeter en marcha)
        if vm.run("echo MARK_G=$(pgrep -f sddm-greeter | head -1)", "G", 15): break
        time.sleep(3)
    time.sleep(12); shot("login")
    print("sddm:", vm.run("echo MARK_S=$(systemctl is-active sddm)/$(pgrep -fc sddm-greeter)greeter", "S", 20))
finally:
    vm.kill()
