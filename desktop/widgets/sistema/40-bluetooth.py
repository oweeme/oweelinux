#!/usr/bin/env python3
# owee-interval: 30
# Widget del sistema: BLUETOOTH (BlueZ, con `bluetoothctl`). Clic: enciende/apaga y conecta o desconecta los dispositivos ya emparejados. Sin adaptador, se oculta.
# Para cambiarlo, copia este archivo a ~/.config/owee/widgets/ con el MISMO nombre.
import json, os, re, subprocess, sys
import sys as _sys, os as _os
for _d in ('/usr/libexec/owee', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'shell')): _sys.path.append(_d)       # biblioteca de idiomas de OweeLinux
from owee_i18n import _
def bt(*a, t=4):
    try: return subprocess.run(["bluetoothctl", *a], capture_output=True, text=True, timeout=t)
    except (OSError, subprocess.TimeoutExpired): return None
me = os.path.abspath(sys.argv[0])
def hay_adaptador():                    # sin adaptador no se llama a bluetoothctl (esperaría al servicio): se oculta al instante. OWEE_BT_SYSFS cambia la carpeta (pruebas)
    try: return bool(os.listdir(os.environ.get("OWEE_BT_SYSFS", "/sys/class/bluetooth")))
    except OSError: return False
if not hay_adaptador(): print(json.dumps({"hidden": True})); sys.exit(0)
if len(sys.argv) > 2 and sys.argv[1] in ("connect", "disconnect") and re.fullmatch(r"[0-9A-Fa-f:]{17}", sys.argv[2]): bt(sys.argv[1], sys.argv[2], t=20)
elif len(sys.argv) > 1 and sys.argv[1] == "toggle":
    r = bt("show"); bt("power", "off" if r and "Powered: yes" in r.stdout else "on")
r = bt("show")
if not r or r.returncode != 0 or "Powered:" not in r.stdout: print(json.dumps({"hidden": True})); sys.exit(0)
on = "Powered: yes" in r.stdout; devs = []
if on:
    d = bt("devices", "Paired"); devs = [(m.group(1), m.group(2)) for m in (re.match(r"Device\s+([0-9A-F:]{17})\s+(.*)", l.strip()) for l in (d.stdout if d else "").splitlines()) if m]
conn = [(mac, n) for mac, n in devs if "Connected: yes" in ((bt("info", mac) or subprocess.CompletedProcess([], 1, "", "")).stdout)]
items = [{"type": "button", "text": _("Apagar Bluetooth") if on else _("Encender Bluetooth"), "command": [me, "toggle"]}]
for mac, n in devs: items.append({"type": "button", "text": (_("Desconectar {0}", n) if (mac, n) in conn else _("Conectar {0}", n)), "command": [me, "disconnect" if (mac, n) in conn else "connect", mac]})
print(json.dumps({"icon": "owee-bluetooth", "text": str(len(conn)) if conn else "", "class": "" if on else "warn", "tooltip": (_("Bluetooth: {0}", ", ".join(n for _m, n in conn)) if conn else _("Bluetooth encendido")) if on else _("Bluetooth apagado"),
    "popup": {"title": _("Bluetooth"), "items": items}}))
