#!/usr/bin/env python3
"""Prueba de corte de energía (F3d). Se ejecuta en el HOST.

Simula cortes de luz repetidos matando QEMU con SIGKILL en momentos aleatorios y comprueba
que el sistema SIEMPRE vuelve a arrancar en un despliegue válido. El disco es un único
archivo que persiste entre iteraciones (los daños, si los hubiera, se acumulan).

Cada iteración arranca la VM (eso ya es la comprobación del corte anterior) y luego:
  update    70 %  lanza `owee-update` (pull + despliegue + menú de arranque) y corta a los
                  ~0,1-8 s (más probable al principio), es decir, en mitad de la operación
  boot      15 %  corta a mitad del PROPIO arranque
  complete  15 %  deja terminar la actualización y corta después

Uso: powerloss-test.py DISCO.img DIR_PUB_STEPS [-n ITER] [--seed S] [--workdir DIR]
Limitación: SIGKILL a QEMU conserva todo lo que el sistema invitado ya escribió (la caché del
anfitrión no se pierde). Prueba la consistencia ante cortes en cualquier punto, pero NO simula
la pérdida de la caché volátil del disco ni el reordenamiento de escrituras de un disco real.
"""
import argparse, os, random, re, shutil, signal, socket, subprocess, sys, tempfile, threading, time

OVMF_CODE = "/usr/share/OVMF/OVMF_CODE_4M.fd"
OVMF_VARS = "/usr/share/OVMF/OVMF_VARS_4M.fd"
PROMPT = re.compile(rb"root@oweelinux:[^\r\n]*# ")


class Vm:
    def __init__(self, disk, vars_fd, sock_path, log):
        self.log = open(log, "ab")
        cmd = ["qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-smp", os.environ.get("QEMU_SMP", "1"), "-m", os.environ.get("QEMU_MEM", "1536"), "-machine", "q35",
               "-display", "none", "-monitor", "none", "-nic", "user",
               "-chardev", f"socket,id=ser0,path={sock_path},server=on,wait=off", "-serial", "chardev:ser0",
               "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
               "-drive", f"if=pflash,format=raw,file={vars_fd}",
               "-drive", f"file={disk},format=raw,if=virtio"] + os.environ.get("QEMU_EXTRA", "").split()
        self.p = subprocess.Popen(cmd, stdout=self.log, stderr=self.log)
        self.buf = b""; self.lock = threading.Lock(); self.sock = None
        for _ in range(100):
            if os.path.exists(sock_path):
                try:
                    self.sock = socket.socket(socket.AF_UNIX); self.sock.connect(sock_path); break
                except OSError:
                    self.sock.close(); self.sock = None
            time.sleep(0.1)
        if not self.sock: raise RuntimeError("no se pudo abrir la consola serie")
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while True:
            try: d = self.sock.recv(4096)
            except OSError: return
            if not d: return
            self.log.write(d); self.log.flush()
            with self.lock: self.buf += d

    def text(self):
        with self.lock: return self.buf

    def wait_for(self, regex, timeout, start=0):
        end = time.time() + timeout
        while time.time() < end:
            m = regex.search(self.text(), start)
            if m: return m
            if self.p.poll() is not None: return None
            time.sleep(0.2)
        return None

    def send(self, line): self.sock.sendall(line.encode() + b"\r")

    def run(self, cmd, marker, timeout=60):
        """Ejecuta cmd y devuelve el valor de la línea 'MARK_<marker>=valor'."""
        start = len(self.text())
        self.send(cmd)
        m = self.wait_for(re.compile(rb"[\r\n]MARK_" + marker.encode() + rb"=([^\r\n$]*)\r?\n"), timeout, start)
        return m.group(1).decode(errors="replace") if m else None

    def kill(self):
        if self.p.poll() is None:
            self.p.send_signal(signal.SIGKILL)
        self.p.wait()
        try: self.sock.close()
        except OSError: pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("disk"); ap.add_argument("pub")
    ap.add_argument("-n", type=int, default=30); ap.add_argument("--seed", type=int)
    ap.add_argument("--workdir", default=None)
    a = ap.parse_args()
    missing = [k for k in range(1, a.n + 1) if not os.path.exists(os.path.join(a.pub, "refs", "heads", "steps", f"step{k}"))]
    if missing:   # una versión inexistente haría fallar `owee-update` al instante y la iteración no probaría nada
        sys.exit(f"ERROR: faltan {len(missing)} versiones step en {a.pub} (p. ej. step{missing[0]}). "
                 f"Publica más con publish-steps.sh o baja -n.")
    seed = a.seed if a.seed is not None else random.randrange(1 << 30)
    rnd = random.Random(seed)
    work = a.workdir or tempfile.mkdtemp(prefix="powerloss-")
    os.makedirs(work, exist_ok=True)
    img = os.path.join(os.path.abspath(work), "work.img"); vars_fd = os.path.join(os.path.abspath(work), "vars.fd")
    shutil.copyfile(a.disk, img); shutil.copyfile(OVMF_VARS, vars_fd)
    stage = tempfile.mkdtemp(); os.symlink(os.path.realpath(a.pub), os.path.join(stage, "pub"))
    http = subprocess.Popen(["python3", "-m", "http.server", "8000", "--bind", "127.0.0.1",
                             "--directory", stage], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # El socket va con ruta RELATIVA: las rutas de socket Unix no pueden pasar de ~108 caracteres.
    work = os.path.abspath(work); os.chdir(work)
    sock = "ser.sock"; log = os.path.join(work, "console.log")
    print(f"semilla={seed}  carpeta={work}  iteraciones={a.n}", flush=True)
    valid = {"1"} | {str(100 + i) for i in range(1, a.n + 2)}
    stats = {"update": 0, "boot": 0, "complete": 0, "update_alcanzo_a_terminar": 0}
    fails = []
    try:
        for k in range(1, a.n + 1):
            mode = rnd.choices(["update", "boot", "complete"], [70, 15, 15])[0]
            if os.path.exists(sock): os.unlink(sock)
            t0 = time.time()
            vm = Vm(img, vars_fd, sock, log)
            try:
                if mode == "boot":
                    # corte durante el propio arranque; la comprobación llega en la iteración siguiente
                    time.sleep(rnd.uniform(1.0, 14.0)); vm.kill(); stats["boot"] += 1
                    print(f"[{k:3d}] corte a mitad de arranque", flush=True); continue
                if not vm.wait_for(PROMPT, 150):
                    fails.append((k, "el sistema NO llegó al prompt tras el corte anterior")); print(f"[{k:3d}] FALLA: no arranca", flush=True); break
                boot_s = time.time() - t0
                st = vm.run(r"echo MARK_ST=$(owee-status | tr '\n' ' ')", "ST", 20) or ""
                dep = vm.run(r"echo MARK_DEP=$(ostree admin status | grep -c '^[* ] oweelinux')", "DEP", 20)
                ro = vm.run(r"echo MARK_RO=$(findmnt -n -o OPTIONS /usr | cut -c1-2)", "RO", 20)
                rel = (re.search(r"release=(\d+)", st) or [None, None])[1]
                problems = []
                if rel not in valid: problems.append(f"release inválida: {rel!r}")
                if not dep or int(dep) < 1: problems.append(f"despliegues={dep}")
                if ro != "ro": problems.append(f"/usr no es ro ({ro})")
                # Una versión nueva (a prueba) tiene que confirmarse sola; si no, owee-health la rechaza
                # y reinicia. Las versiones "step" están sanas, así que rechazarlas es un fallo.
                kvp = lambda t, key: (re.search(key + r"=(\S+)", t) or [None, ""])[1]
                if kvp(st, "booted") != kvp(st, "confirmed"):
                    confirmed_ok = False
                    for _ in range(25):
                        st2 = vm.run(r"echo MARK_ST2=$(owee-status | tr '\n' ' ')", "ST2", 10)
                        if st2 is None: break          # la VM se reinició: la rechazaron
                        if kvp(st2, "booted") == kvp(st2, "confirmed"): confirmed_ok = True; break
                        time.sleep(3)
                    if not confirmed_ok: problems.append("una versión sana no llegó a confirmarse (rechazada)")
                if k % 5 == 0 and not problems:
                    fs = vm.run(r"ostree fsck --repo=/sysroot/ostree/repo --quiet >/tmp/fsck.txt 2>&1; echo MARK_FSCK=$?", "FSCK", 600)
                    if fs != "0": problems.append(f"ostree fsck rc={fs}")
                if problems:
                    fails.append((k, "; ".join(problems))); print(f"[{k:3d}] FALLA: {problems}  estado={st}", flush=True); break
                if mode == "complete":
                    r = vm.run(f"OWEE_REF=owee:steps/step{k} owee-update >/tmp/u.log 2>&1; echo MARK_UP=$?", "UP", 120)
                    stats["complete"] += 1
                    if r != "0": fails.append((k, f"owee-update terminó con rc={r}")); print(f"[{k:3d}] FALLA: owee-update rc={r}", flush=True); break
                    print(f"[{k:3d}] ok (arranque {boot_s:4.1f}s, release {rel}, despliegues {dep}) -> actualización completa rc={r}, corte", flush=True)
                else:
                    vm.send(f"OWEE_REF=owee:steps/step{k} owee-update >/tmp/u.log 2>&1; echo MARK_UP=$?")
                    d = min(0.1 + rnd.expovariate(1 / 1.5), 8.0); time.sleep(d)   # sesgo hacia el principio: ahí está el trabajo de pull+despliegue
                    mdone = re.search(rb"[\r\n]MARK_UP=(\d+)", vm.text()); done = mdone is not None
                    if done and mdone.group(1) != b"0":
                        fails.append((k, f"owee-update terminó con rc={mdone.group(1).decode()}")); print(f"[{k:3d}] FALLA: owee-update rc={mdone.group(1).decode()}", flush=True); break
                    stats["update"] += 1; stats["update_alcanzo_a_terminar"] += done
                    print(f"[{k:3d}] ok (arranque {boot_s:4.1f}s, release {rel}, despliegues {dep}) -> corte a los {d:.1f}s de actualizar" + (" (ya había terminado)" if done else " (A MITAD)"), flush=True)
            finally:
                vm.kill()
        else:
            pass
        # comprobación final del sistema de archivos con un arranque limpio
        if not fails:
            if os.path.exists(sock): os.unlink(sock)
            vm = Vm(img, vars_fd, sock, log)
            ok = vm.wait_for(PROMPT, 150) is not None
            if ok: vm.send("poweroff"); vm.p.wait(timeout=60)
            else: fails.append((a.n + 1, "no arrancó en la comprobación final")); vm.kill()
            e2 = shutil.which("e2fsck")
            if e2 and not fails:
                off = 129 * 1024 * 1024
                r = subprocess.run([e2, "-fn", f"{img}?offset={off}"], capture_output=True, text=True)
                print("e2fsck -fn tras apagado limpio: rc=%d  %s" % (r.returncode, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""))
                if r.returncode not in (0,): fails.append((a.n + 1, f"e2fsck rc={r.returncode}"))
    finally:
        http.kill(); shutil.rmtree(stage, ignore_errors=True)
    print(f"\nresumen: {stats}  semilla={seed}")
    if fails:
        for k, why in fails: print(f"FALLA en iteración {k}: {why}")
        print(f"registro de consola: {log}"); sys.exit(1)
    print("PASA: el sistema arrancó en un despliegue válido después de cada corte")


if __name__ == "__main__":
    main()
