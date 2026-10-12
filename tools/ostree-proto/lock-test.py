#!/usr/bin/env python3
"""Bloqueo de pantalla bajo fallos de servicios (F-R). Se ejecuta en el HOST.

Con la sesión de Plasma en QEMU: bloquea la pantalla, (opcionalmente) mata los servicios de red, energía y
audio MIENTRAS está bloqueada, e intenta desbloquear de dos formas, midiendo el tiempo:
  A) escribir la contraseña (el usuario de prueba no tiene: basta Enter) con el teclado virtual de QEMU;
  B) la receta de recuperación desde una consola: `loginctl unlock-sessions`.
Guarda capturas de pantalla (bloqueada / después). Disco con -snapshot.
Uso: lock-test.py DISCO.img [--kill] [--workdir DIR]"""
import argparse, importlib.util, os, shutil, sys, time

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py"))
gui = importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)
KILL = ("systemctl stop NetworkManager upower power-profiles-daemon 2>/dev/null; "
        "pkill -9 -u oweeuser -x -e 'pipewire|wireplumber|powerdevil|pipewire-pulse' >/dev/null 2>&1; echo MARK_K=ok")


def locker(vm):  # ¿hay un bloqueador activo?
    return bool(vm.run("echo MARK_L=$(pgrep -f kscreenlocker_greet | head -1)", "L", 30))


def wait_gone(vm, limit):
    t0 = time.time()
    while time.time() - t0 < limit:
        if not locker(vm): return time.time() - t0
        time.sleep(0.5)
    return None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("disk"); ap.add_argument("--kill", action="store_true"); ap.add_argument("--workdir")
    a = ap.parse_args(); work = os.path.abspath(a.workdir or "lock-work"); os.makedirs(work, exist_ok=True); os.chdir(work)
    for f in ("ser.sock", "mon.sock"):
        if os.path.exists(f): os.unlink(f)
    shutil.copyfile(gui.VARS_SRC, "vars.fd"); log = os.path.join(work, "console.log"); open(log, "wb").close()
    os.environ.setdefault("QEMU_MEM", "3072"); tag = "con_fallos" if a.kill else "sin_fallos"
    vm = gui.Vm(os.path.abspath(a.disk), os.path.join(work, "vars.fd"), log); out = {}
    try:
        assert vm.wait(gui.PROMPT, 240)
        for _ in range(100):
            if vm.run("echo MARK_P=$(pgrep -x plasmashell | head -1)", "P", 10): break
            time.sleep(3)
        time.sleep(25)
        vm.run("loginctl lock-sessions; echo MARK_LK=$?", "LK", 30)
        t0 = time.time()
        while time.time() - t0 < 40 and not locker(vm): time.sleep(1)
        out["bloqueo_activo"] = locker(vm); time.sleep(5)
        if a.kill: out["fallos_inyectados"] = vm.run(KILL, "K", 60)
        time.sleep(3); vm.screenshot(f"bloqueada_{tag}.png")
        # A) desbloquear escribiendo (Enter con contraseña vacía)
        vm.mon.sendall(b"sendkey ret\n"); out["A_enter_desbloquea_en"] = wait_gone(vm, 30)
        if out["A_enter_desbloquea_en"] is None:
            # B) receta de recuperación desde la consola
            vm.run("loginctl unlock-sessions; echo MARK_UL=$?", "UL", 30)
            out["B_unlock_sessions_en"] = wait_gone(vm, 30)
        time.sleep(3); vm.screenshot(f"despues_{tag}.png")
        out["escritorio_responde"] = vm.run("timeout 25 runuser -u oweeuser -- env DISPLAY=:0 XAUTHORITY=/home/oweeuser/.Xauthority xset q >/dev/null 2>&1; echo MARK_X=$?", "X", 60) == "0"
    finally:
        vm.kill()
    print(tag, out)


if __name__ == "__main__":
    main()
