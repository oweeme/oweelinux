#!/usr/bin/env python3
# owee-interval: 10
# Widget del sistema: RED (NetworkManager, con `nmcli`). Muestra cable o WiFi (con señal); el clic muestra los datos y activa/desactiva el WiFi.
import json, os, subprocess, sys
def nm(*a):
    try: return subprocess.run(["nmcli", *a], capture_output=True, text=True, timeout=4).stdout.strip()
    except Exception: return ""
me = os.path.abspath(sys.argv[0])
if len(sys.argv) > 1 and sys.argv[1] in ("wifi-on", "wifi-off"): nm("radio", "wifi", sys.argv[1][5:])
dev = typ = con = ""
for line in nm("-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device").splitlines():
    p = line.split(":")
    if len(p) >= 4 and p[2] == "connected" and p[1] in ("ethernet", "wifi"): dev, typ, con = p[0], p[1], p[3]; break
if not dev:
    print(json.dumps({"icon": "owee-network-offline", "text": "", "tooltip": "Sin conexión", "class": "warn", "popup": {"title": "Red", "items": [{"type": "label", "text": "Sin conexión"}]}})); sys.exit(0)
ip = nm("-g", "IP4.ADDRESS", "device", "show", dev).splitlines()[:1]
if typ == "wifi":
    sig = next((l.split(":")[1] for l in nm("-t", "-f", "IN-USE,SIGNAL", "device", "wifi").splitlines() if l.startswith("*")), "?")
    text = f"{sig}%"
else: text = ""
wifi_on = nm("radio", "wifi") == "enabled"
print(json.dumps({"icon": "owee-network-wifi" if typ == "wifi" else "owee-network-wired", "text": text, "tooltip": f"{con} ({dev})", "popup": {"title": "Red", "items": [
    {"type": "label", "text": f"Conexión: {con}"}, {"type": "label", "text": f"Dispositivo: {dev} ({typ})"},
    {"type": "label", "text": f"Dirección: {ip[0] if ip else 'sin IP'}"}, {"type": "separator"},
    {"type": "button", "text": "Desactivar WiFi" if wifi_on else "Activar WiFi", "command": [me, "wifi-off" if wifi_on else "wifi-on"]}]}}))
