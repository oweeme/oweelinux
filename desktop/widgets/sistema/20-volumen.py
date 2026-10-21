#!/usr/bin/env python3
# owee-interval: 5
# Widget del sistema: VOLUMEN (WirePlumber, con `wpctl`). Para cambiarlo, copia este archivo a ~/.config/owee/widgets/ con el MISMO nombre.
# Clic: abre un deslizante y un botón de silencio. Sin tarjeta de sonido, se oculta.
import json, os, subprocess, sys
import sys as _sys, os as _os
for _d in ('/usr/libexec/owee', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'shell')): _sys.path.append(_d)       # biblioteca de idiomas de OweeLinux
from owee_i18n import _
SINK = "@DEFAULT_AUDIO_SINK@"
def wpctl(*a): return subprocess.run(["wpctl", *a], capture_output=True, text=True, timeout=3)
me = os.path.abspath(sys.argv[0])
try:
    if len(sys.argv) > 2 and sys.argv[1] == "set": wpctl("set-volume", SINK, f"{max(0, min(150, int(sys.argv[2])))}%")
    elif len(sys.argv) > 1 and sys.argv[1] == "mute": wpctl("set-mute", SINK, "toggle")
    r = wpctl("get-volume", SINK)
    if r.returncode != 0 or "Volume" not in r.stdout: raise RuntimeError("sin salida de audio")
except Exception:
    print(json.dumps({"hidden": True})); sys.exit(0)
vol = round(float(r.stdout.split()[1]) * 100); muted = "[MUTED]" in r.stdout
print(json.dumps({"icon": "owee-volume-muted" if muted else "owee-volume-low" if vol < 40 else "owee-volume-high", "text": "" if muted else f"{vol}%", "class": "warn" if muted else "", "tooltip": _("Silenciado") if muted else _('Volumen {0}%', vol),
    "popup": {"title": _("Volumen"), "items": [
        {"type": "slider", "min": 0, "max": 100, "value": vol, "command": [me, "set"]},
        {"type": "button", "text": _("Activar sonido") if muted else _("Silenciar"), "command": [me, "mute"]}]}}))
