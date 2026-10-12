#!/usr/bin/env python3
# owee-interval: 30
# Widget en PYTHON con VENTANITA: un control deslizante. El panel llama a este mismo script con "set N" al mover el control.
# (Maqueta: guarda el valor en un archivo; un widget real llamaría a brightnessctl.)
import json, os, sys
f = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "owee-brillo")
if len(sys.argv) > 2 and sys.argv[1] == "set":
    os.makedirs(os.path.dirname(f), exist_ok=True); open(f, "w").write(sys.argv[2])
v = int(open(f).read()) if os.path.exists(f) else 50
me = os.path.abspath(sys.argv[0])
print(json.dumps({"text": f"brillo {v}%", "popup": {"title": "Brillo", "items": [
    {"type": "slider", "min": 0, "max": 100, "value": v, "command": [me, "set"]},
    {"type": "button", "text": "Poner al 50 %", "command": [me, "set", "50"]}]}}))
