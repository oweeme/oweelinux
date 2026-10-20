#!/usr/bin/env python3
"""Arranca un disco en QEMU SIN consola serie (como en un equipo real) y guarda capturas de pantalla (screendump por QMP) a los N segundos indicados.
Sirve para ver qué muestra un sistema recién instalado (p. ej. el asistente de primer arranque). Uso: boot-shot.py DISCO.img SALIDA_PREFIJO [seg1 seg2 …]   (por defecto 60 120)
Opcionales (variables de entorno): BOOT_EXTRA=disco1.img,disco2.img (discos extra, que SÍ se escriben) y BOOT_DO="40:click:864,686;45:type:hola;50:key:ret" (acciones con el ratón y el teclado a los N segundos)."""
import json, os, shutil, socket, subprocess, sys, tempfile, time
disk, prefix = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); times = [int(x) for x in sys.argv[3:]] or [60, 120]
W = tempfile.mkdtemp(prefix="bootshot", dir=os.path.expanduser("~/.cache/oweelinux/tmp")) if os.path.isdir(os.path.expanduser("~/.cache/oweelinux/tmp")) else tempfile.mkdtemp()
vars_fd = os.path.join(W, "vars.fd"); SB = os.environ.get("BOOT_SECBOOT") == "1"; OV = os.path.expanduser("~/.cache/oweelinux/ovmf"); shutil.copyfile(os.path.join(OV, "OVMF_VARS_4M.ms.fd") if SB else "/usr/share/OVMF/OVMF_VARS_4M.fd", vars_fd); sock = os.path.join(W, "qmp.sock")
p = subprocess.Popen(["qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-smp", "2", "-m", os.environ.get("BOOT_MEM", "3072"), "-machine", "q35,smm=on" if SB else "q35", "-display", "none", "-device", "virtio-vga,xres=1280,yres=800", "-nic", "user" + os.environ.get("BOOT_NICOPT", ""), "-snapshot",
    *(["-global", "driver=cfi.pflash01,property=secure,value=on"] if SB else []), "-qmp", f"unix:{sock},server=on,wait=off", "-drive", "if=pflash,format=raw,readonly=on,file=" + (os.path.join(OV, "OVMF_CODE_4M.secboot.fd") if SB else "/usr/share/OVMF/OVMF_CODE_4M.fd"), "-drive", f"if=pflash,format=raw,file={vars_fd}",
    *(["-device", "ich9-ahci,id=ahci", "-drive", f"if=none,id=cd0,file={disk},media=cdrom,readonly=on", "-device", "ide-cd,drive=cd0,bus=ahci.0,bootindex=0"] if disk.endswith(".iso") else ["-drive", f"file={disk},format=raw,if=virtio"]), "-serial", (os.environ["BOOT_SERIAL"] if os.environ.get("BOOT_SERIAL", "").startswith("pipe:") else "file:" + os.environ.get("BOOT_SERIAL", "/dev/null")), "-device", "qemu-xhci", "-device", "usb-tablet", "-device", "usb-kbd"] + [a for d in os.environ.get("BOOT_EXTRA", "").split(",") if d for a in ("-drive", f"file={d},format=raw,if=virtio,snapshot=off")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    KEYS = {" ": "spc", "\n": "ret", ".": "dot", "-": "minus", "_": "shift+minus", "/": "slash", ",": "comma", "(": "shift+9", ")": "shift+0", "$": "shift+4", "=": "equal", ";": "semicolon", ":": "shift+semicolon", "'": "apostrophe", "|": "shift+backslash", "&": "shift+7", ">": "shift+dot", "<": "shift+comma", "*": "shift+8", "#": "shift+3", "~": "shift+grave", "%": "shift+5", "!": "shift+1", "\"": "shift+apostrophe", "[": "bracket_left", "]": "bracket_right", "\\": "backslash"}
    def press(k): cmd("send-key", keys=[{"type": "qcode", "data": q} for q in k.split("+")]); time.sleep(0.12)
    def typ(text):
        for ch in text: press(KEYS.get(ch) or ("shift+" + ch.lower() if ch.isupper() else ch))
    def click(x, y):
        for ax, v, m in (("x", x, 1280), ("y", y, 800)): pass
        cmd("input-send-event", events=[{"type": "abs", "data": {"axis": "x", "value": int(x * 32767 / 1280)}}, {"type": "abs", "data": {"axis": "y", "value": int(y * 32767 / 800)}}]); time.sleep(0.2)
        cmd("input-send-event", events=[{"type": "btn", "data": {"down": True, "button": "left"}}]); time.sleep(0.12); cmd("input-send-event", events=[{"type": "btn", "data": {"down": False, "button": "left"}}])
    todo = [(int(x.split(":", 1)[0]), "do", x.split(":", 1)[1]) for x in os.environ.get("BOOT_DO", "").split(";") if x]
    for t, act, arg in sorted(todo + [(t, "shot", "") for t in times], key=lambda e: (e[0], e[1] == "shot")):      # acciones y capturas en una sola línea de tiempo
        time.sleep(max(0, t - (time.time() - t0)))
        if act == "shot":
            out = f"{prefix}-{t}s.ppm"; cmd("screendump", filename=out)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out, out[:-4] + ".png"]); os.remove(out); print("captura", out[:-4] + ".png", flush=True)
            continue
        kind, _s, a2 = arg.partition(":")
        if kind == "click": click(*[int(v) for v in a2.split(",")])
        elif kind == "type": typ(a2)
        elif kind == "key": press(a2)
        elif kind in ("keydown", "keyup"): cmd("input-send-event", events=[{"type": "key", "data": {"down": kind == "keydown", "key": {"type": "qcode", "data": a2}}}])
finally:
    p.kill(); shutil.rmtree(W, ignore_errors=True)
