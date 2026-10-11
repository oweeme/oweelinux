#!/usr/bin/env python3
"""Arranque gráfico (F3h, hito M1). Se ejecuta en el HOST.

Arranca el disco en QEMU con pantalla virtual, entra por la consola serie y comprueba que
SDDM y Plasma están corriendo; espera a que aparezca el escritorio y guarda una captura (PNG).
Uso: gui-boot-test.py DISCO.img [--shot captura.png] [--workdir DIR] [--timeout S]
Disco con -snapshot: la prueba nunca lo modifica. Gráficos por software (sin GPU en la VM)."""
import argparse, os, re, shutil, socket, subprocess, sys, tempfile, threading, time

CODE, VARS_SRC = "/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_VARS_4M.fd"
PROMPT = re.compile(rb"root@[^\r\n]*# ")


class Vm:
    def __init__(self, disk, vars_fd, log):
        self.log = open(log, "ab"); self.buf = b""; self.lock = threading.Lock()
        cmd = ["qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-smp", "2", "-m", "3072", "-machine", "q35",
               "-display", "none", "-device", "virtio-vga", "-nic", "user", "-snapshot",
               "-chardev", "socket,id=ser0,path=ser.sock,server=on,wait=off", "-serial", "chardev:ser0",
               "-monitor", "unix:mon.sock,server,nowait",
               "-drive", f"if=pflash,format=raw,readonly=on,file={CODE}", "-drive", f"if=pflash,format=raw,file={vars_fd}",
               "-drive", f"file={disk},format=raw,if=virtio", "-device", "virtio-keyboard-pci", "-device", "virtio-tablet-pci"]
        self.p = subprocess.Popen(cmd, stdout=self.log, stderr=self.log)
        self.ser = self._connect("ser.sock"); self.mon = self._connect("mon.sock")
        threading.Thread(target=self._rd, daemon=True).start()

    @staticmethod
    def _connect(path):
        for _ in range(150):
            if os.path.exists(path):
                s = socket.socket(socket.AF_UNIX)
                try: s.connect(path); return s
                except OSError: s.close()
            time.sleep(0.1)
        raise RuntimeError(f"no se pudo abrir {path}")

    def _rd(self):
        while True:
            try: d = self.ser.recv(4096)
            except OSError: return
            if not d: return
            self.log.write(d); self.log.flush()
            with self.lock: self.buf += d

    def text(self):
        with self.lock: return self.buf

    def wait(self, rx, timeout, start=0):
        end = time.time() + timeout
        while time.time() < end:
            m = rx.search(self.text(), start)
            if m: return m
            if self.p.poll() is not None: return None
            time.sleep(0.3)

    def run(self, cmd, key, timeout=30):
        start = len(self.text()); self.ser.sendall(cmd.encode() + b"\r")
        m = self.wait(re.compile(rb"[\r\n]MARK_" + key.encode() + rb"=([^\r\n$]*)\r?\n"), timeout, start)
        return m.group(1).decode(errors="replace") if m else None

    def screenshot(self, path):
        self.mon.sendall(f"screendump {os.path.abspath(path)} -f png\n".encode()); time.sleep(2)

    def kill(self):
        if self.p.poll() is None: self.p.kill()
        self.p.wait()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("disk"); ap.add_argument("--shot", default="escritorio.png")
    ap.add_argument("--workdir"); ap.add_argument("--timeout", type=int, default=240)
    a = ap.parse_args()
    work = os.path.abspath(a.workdir or tempfile.mkdtemp(prefix="gui-")); os.makedirs(work, exist_ok=True); os.chdir(work)
    for f in ("ser.sock", "mon.sock"):
        if os.path.exists(f): os.unlink(f)
    shutil.copyfile(VARS_SRC, "vars.fd"); log = os.path.join(work, "console.log")
    shot = a.shot if os.path.isabs(a.shot) else os.path.join(work, a.shot)
    vm = Vm(os.path.abspath(a.disk), os.path.join(work, "vars.fd"), log)
    fails = []
    try:
        t0 = time.time()
        if not vm.wait(PROMPT, 180): fails.append("no llegó al prompt de la consola serie"); raise SystemExit
        print(f"consola serie lista a los {time.time() - t0:.0f}s", flush=True)
        print("estado:", vm.run(r"echo MARK_ST=$(owee-status | tr '\n' ' ')", "ST"), flush=True)
        print("ostree /usr:", vm.run(r"echo MARK_RO=$(findmnt -n -o OPTIONS /usr | cut -c1-2)", "RO"), flush=True)
        seen = {}
        end = time.time() + a.timeout
        while time.time() < end and not ("sddm" in seen and "plasmashell" in seen):
            for name in ("sddm", "plasmashell"):
                if name not in seen and vm.run(f"echo MARK_P=$(pgrep -x {name} | head -1)", "P", 10):
                    seen[name] = time.time() - t0; print(f"  {name} corriendo a los {seen[name]:.0f}s", flush=True)
            time.sleep(5)
        for name in ("sddm", "plasmashell"):
            if name not in seen: fails.append(f"{name} no apareció en {a.timeout}s")
        print("units fallidas:", vm.run(r"echo MARK_F=$(systemctl --failed --no-legend | awk '{print $2}' | tr '\n' ' ')", "F", 20), flush=True)
        if "plasmashell" in seen: time.sleep(25)       # que termine de pintar el escritorio
        vm.screenshot(shot); print("captura:", shot, os.path.getsize(shot) if os.path.exists(shot) else "NO SE CREÓ", flush=True)
    except SystemExit:
        pass
    finally:
        vm.kill()
    print("PASA" if not fails else "FALLA: " + "; ".join(fails)); sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
