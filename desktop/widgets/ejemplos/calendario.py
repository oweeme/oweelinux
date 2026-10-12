#!/usr/bin/env python3
# owee-interval: 60
# Widget en PYTHON con VENTANITA: un calendario. Muestra la fecha; al hacer clic se abre el calendario del mes.
import json, time
print(json.dumps({"text": time.strftime("cal %d %b"), "tooltip": time.strftime("%A %d de %B de %Y"),
                  "popup": {"title": time.strftime("%B %Y"), "items": [{"type": "calendar"}]}}))
