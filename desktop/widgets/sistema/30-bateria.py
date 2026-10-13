#!/usr/bin/env python3
# owee-interval: 15
# Widget del sistema: BATERÍA (/sys/class/power_supply). Se oculta en equipos sin batería.
# OWEE_POWER_SUPPLY_DIR cambia la carpeta (para pruebas con una batería simulada).
import glob, json, os
import sys as _sys, os as _os
for _d in ('/usr/libexec/owee', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'shell')): _sys.path.append(_d)       # biblioteca de idiomas de OweeLinux
from owee_i18n import _
base = os.environ.get("OWEE_POWER_SUPPLY_DIR", "/sys/class/power_supply")
def read(p, d=""):
    try: return open(p).read().strip()
    except OSError: return d
bats = sorted(glob.glob(os.path.join(base, "BAT*")))
if not bats: print(json.dumps({"hidden": True})); raise SystemExit
cap = int(read(bats[0] + "/capacity", "0") or 0); st = read(bats[0] + "/status", "Unknown")
estado = {"Charging": "cargando", "Discharging": "", "Full": "completa"}.get(st, "")
low = st == "Discharging" and cap <= 15
lvl = min(100, round(cap / 20) * 20)
print(json.dumps({"icon": f"owee-battery-{lvl}" + ("-charging" if st == "Charging" else ""), "text": f"{cap}%", "class": "warn" if low else "", "tooltip": _('Batería: {0}% ({1})', cap, st),
    "popup": {"title": _("Batería"), "items": [{"type": "label", "text": _('Carga: {0}%', cap)}, {"type": "label", "text": _('Estado: {0}', st)}]}}))
