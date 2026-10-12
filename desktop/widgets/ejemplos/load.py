#!/usr/bin/env python3
# owee-interval: 5
# Widget de ejemplo en PYTHON: muestra la carga del sistema. Un widget es un ejecutable que imprime UNA línea JSON:
#   {"text": "...", "tooltip": "...", "class": "warn"}   (todo opcional salvo "text")
# El panel lo ejecuta cada "owee-interval" segundos; si falla o tarda más de 5 s, muestra un aviso y sigue funcionando.
import json
l1, l5, l15 = open("/proc/loadavg").read().split()[:3]
print(json.dumps({"text": f"carga {l1}", "tooltip": f"1 min {l1} · 5 min {l5} · 15 min {l15}", "class": "warn" if float(l1) > 2 else ""}))
