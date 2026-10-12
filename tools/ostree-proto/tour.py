#!/usr/bin/env python3
"""Recorrido visual: arranca la imagen, abre algunas apps como el usuario de prueba y guarda capturas (PNG).
Uso: tour.py DISCO.img DIR_SALIDA"""
import importlib.util, os, shutil, sys, time
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py"))
gui = importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)
disk, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
work = os.path.join(os.environ.get("TMPWORK", "/home/oweeme/.cache/oweelinux/vm"), "tour"); os.makedirs(work, exist_ok=True); os.chdir(work)
for f in ("ser.sock", "mon.sock"):
    if os.path.exists(f): os.unlink(f)
shutil.copyfile(gui.VARS_SRC, "vars.fd"); open("c.log", "wb").close(); os.environ.setdefault("QEMU_MEM", "3072")
vm = gui.Vm(disk, work + "/vars.fd", work + "/c.log")
RUN = "runuser -u oweeuser -- env DISPLAY=:0 XAUTHORITY=/home/oweeuser/.Xauthority "
def shot(name): vm.screenshot(os.path.join(out, name)); print("captura", name, flush=True)
try:
    assert vm.wait(gui.PROMPT, 240)
    for _ in range(100):
        if vm.run("echo MARK_P=$(pgrep -x plasmashell | head -1)", "P", 10): break
        time.sleep(3)
    time.sleep(25); shot("1-escritorio.png")
    vm.mon.sendall(b"sendkey meta_l\n"); time.sleep(6); shot("2-menu-aplicaciones.png")
    vm.mon.sendall(b"sendkey esc\n"); time.sleep(2)
    vm.run(f"({RUN}dolphin >/dev/null 2>&1 &); echo MARK_A=ok", "A", 30); time.sleep(10)
    vm.run(f"({RUN}konsole >/dev/null 2>&1 &); echo MARK_B=ok", "B", 30); time.sleep(10); shot("3-dolphin-y-konsole.png")
    vm.run(f"({RUN}systemsettings >/dev/null 2>&1 &); echo MARK_C=ok", "C", 30); time.sleep(12); shot("4-ajustes.png")
    print("memoria:", vm.run("echo MARK_M=$(free -m | awk '/Mem:/{print $3\"MB usados de \"$2\"MB\"}')", "M", 30))
finally:
    vm.kill()
