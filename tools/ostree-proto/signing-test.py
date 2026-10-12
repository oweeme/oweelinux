#!/usr/bin/env python3
"""Verificación de la firma de las actualizaciones. Se ejecuta en el HOST.

Desde la release 1, intenta actualizar a cuatro ramas (ver publish-sig-branches.sh):
  unsigned, wrongkey, tampered -> deben RECHAZARSE sin tocar el sistema (sigue en la release 1, un solo despliegue);
  good (firmada con la clave de confianza) -> debe aceptarse, arrancar y confirmarse.
Uso: signing-test.py DISCO.img DIR_PUB [--workdir DIR]       Disco con -snapshot. QEMU_MEM / QEMU_SMP."""
import argparse, importlib.util, os, re, shutil, subprocess, sys, tempfile, time
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("pl", os.path.join(here, "powerloss-test.py"))
pl = importlib.util.module_from_spec(spec); spec.loader.exec_module(pl)
kv = lambda t, k: (re.search(k + r"=(\S+)", t or "") or [None, None])[1]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("disk"); ap.add_argument("pub"); ap.add_argument("--workdir")
    a = ap.parse_args(); work = os.path.abspath(a.workdir or tempfile.mkdtemp(prefix="sig-")); os.makedirs(work, exist_ok=True); os.chdir(work)
    os.environ["QEMU_EXTRA"] = "-snapshot"
    if os.path.exists("ser.sock"): os.unlink("ser.sock")
    shutil.copyfile(pl.OVMF_VARS, "vars.fd"); open("c.log", "wb").close()
    stage = tempfile.mkdtemp(); os.symlink(os.path.realpath(a.pub), os.path.join(stage, "pub"))
    http = subprocess.Popen(["python3", "-m", "http.server", "8000", "--bind", "127.0.0.1", "--directory", stage], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    vm = pl.Vm(os.path.abspath(a.disk), work + "/vars.fd", "ser.sock", work + "/c.log"); fails = []
    def chk(name, ok, detail=""):
        print(("PASA   " if ok else "FALLA  ") + name + (f"  ({detail})" if detail else ""), flush=True)
        if not ok: fails.append(name)
    try:
        assert vm.wait_for(pl.PROMPT, 240)
        st = vm.run(r"echo MARK_S=$(owee-status | tr '\n' ' ')", "S", 20); chk("arranca en la release 1", kv(st, "release") == "1", st[:60] if st else "")
        for name in ("unsigned", "wrongkey", "tampered"):
            out = vm.run(f"OWEE_REF=owee:sig/{name} owee-update > /tmp/u.txt 2>&1; echo MARK_R=$?", "R", 180)
            msg = vm.run("echo MARK_M=$(tr '\\n' ' ' < /tmp/u.txt | cut -c1-170)", "M", 20) or ""
            dep = vm.run("echo MARK_D=$(ostree admin status | grep -c '^[* ] oweelinux')", "D", 30)
            rel = kv(vm.run(r"echo MARK_S=$(owee-status | tr '\n' ' ')", "S", 20), "release")
            chk(f"{name}: se RECHAZA", out not in (None, "0"), f"rc={out}; {msg}")
            chk(f"{name}: el sistema no cambia", dep == "1" and rel == "1", f"despliegues={dep} release={rel}")
        out = vm.run("OWEE_REF=owee:sig/good owee-update > /tmp/u.txt 2>&1; echo MARK_R=$?", "R", 240)
        chk("good (firma de confianza): se ACEPTA", out == "0", f"rc={out}")
        pos = len(vm.text()); vm.send("systemctl reboot")
        g = vm.wait_for(re.compile(rb"GNU GRUB  version"), 180, pos); assert g
        assert vm.wait_for(pl.PROMPT, 240, g.end())
        for _ in range(30):                          # esperar la confirmación (ventana de estabilidad)
            st = vm.run(r"echo MARK_S=$(owee-status | tr '\n' ' ')", "S", 20) or ""
            if kv(st, "booted") == kv(st, "confirmed") and kv(st, "release"): break
            time.sleep(4)
        chk("good: arranca en la release nueva y se confirma", kv(st, "release") == "502" and kv(st, "booted") == kv(st, "confirmed"), st[:90])
    finally:
        vm.kill(); http.kill(); shutil.rmtree(stage, ignore_errors=True)
    print("PASA todo" if not fails else f"FALLA: {fails}"); sys.exit(1 if fails else 0)

if __name__ == "__main__": main()
