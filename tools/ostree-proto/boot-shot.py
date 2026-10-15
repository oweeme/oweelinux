#!/usr/bin/env python3
"""Arranca un disco en QEMU SIN consola serie (como en un equipo real) y guarda capturas de pantalla (screendump por QMP) a los N segundos indicados.
Sirve para ver qué muestra un sistema recién instalado (p. ej. el asistente de primer arranque). Uso: boot-shot.py DISCO.img SALIDA_PREFIJO [seg1 seg2 …]   (por defecto 60 120)"""
import json, os, shutil, socket, subprocess, sys, tempfile, time
disk, prefix = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); times = [int(x) for x in sys.argv[3:]] or [60, 120]
W = tempfile.mkdtemp(prefix="bootshot", dir=os.path.expanduser("~/.cache/oweelinux/tmp")) if os.path.isdir(os.path.expanduser("~/.cache/oweelinux/tmp")) else tempfile.mkdtemp()
vars_fd = os.path.join(W, "vars.fd"); shutil.copyfile("/usr/share/OVMF/OVMF_VARS_4M.fd", vars_fd); sock = os.path.join(W, "qmp.sock")
p = subprocess.Popen(["qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-smp", "2", "-m", "3072", "-machine", "q35", "-display", "none", "-device", "virtio-vga,xres=1280,yres=800", "-nic", "user", "-snapshot",
    "-qmp", f"unix:{sock},server=on,wait=off", "-drive", "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd", "-drive", f"if=pflash,format=raw,file={vars_fd}",
    "-drive", f"file={disk},format=raw,if=virtio", "-device", "qemu-xhci", "-device", "usb-tablet", "-device", "usb-kbd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(100):
        if os.path.exists(sock):
            try: s = socket.socket(socket.AF_UNIX); s.connect(sock); break
            except OSError: pass
        time.sleep(0.1)
    f = s.makefile("rw"); f.readline()
    def cmd(n, **a):
        f.write(json.dumps({"execute": n, "arguments": a}) + "\n"); f.flush()
        while True:
            r = json.loads(f.readline())
            if "return" in r or "error" in r: return r
    cmd("qmp_capabilities"); t0 = time.time()
    for t in times:
        time.sleep(max(0, t - (time.time() - t0))); out = f"{prefix}-{t}s.ppm"; cmd("screendump", filename=out)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out, out[:-4] + ".png"]); os.remove(out); print("captura", out[:-4] + ".png", flush=True)
finally:
    p.kill(); shutil.rmtree(W, ignore_errors=True)
