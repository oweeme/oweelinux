#!/usr/bin/env python3
# owee-interval: 10
# Widget del sistema: RED (NetworkManager, con `nmcli`). Icono de cable/WiFi/sin red. Clic: datos de la conexión, interruptor de WiFi y lista de redes
# cercanas para conectarse (las redes con clave piden la contraseña en un campo; las ya guardadas se conectan con un clic).
# Para cambiarlo, copia este archivo a ~/.config/owee/widgets/ con el MISMO nombre.
import json, os, re, subprocess, sys
import sys as _sys, os as _os
for _d in ('/usr/libexec/owee', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'shell')): _sys.path.append(_d)       # biblioteca de idiomas de OweeLinux
from owee_i18n import _
def nm(*a):
    try: return subprocess.run(["nmcli", *a], capture_output=True, text=True, timeout=4).stdout.strip()
    except Exception: return ""
def split(line): return [p.replace("\\:", ":") for p in re.split(r"(?<!\\):", line)]       # nmcli -t escapa los ':' de los valores como '\:'
me = os.path.abspath(sys.argv[0])
def saved(): return {split(l)[0] for l in nm("-t", "-f", "NAME,TYPE", "connection", "show").splitlines() if len(split(l)) > 1 and "wireless" in split(l)[1]}
if len(sys.argv) > 1 and sys.argv[1] in ("wifi-on", "wifi-off"): nm("radio", "wifi", sys.argv[1][5:])
elif len(sys.argv) > 2 and sys.argv[1] == "connect":                  # conectar tarda más que el límite de 5 s del panel: se lanza aparte y no se espera
    ssid = sys.argv[2]; pw = sys.argv[3] if len(sys.argv) > 3 else ""
    cmd = ["nmcli", "connection", "up", "id", ssid] if ssid in saved() and not pw else ["nmcli", "device", "wifi", "connect", ssid] + (["password", pw] if pw else [])
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
elif len(sys.argv) > 1 and sys.argv[1] == "rescan": nm("device", "wifi", "rescan")
dev = typ = con = ""; has_wifi = False
for line in nm("-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device").splitlines():
    p = split(line)
    if len(p) >= 4 and p[1] == "wifi": has_wifi = True
    if len(p) >= 4 and p[2] == "connected" and p[1] in ("ethernet", "wifi") and not dev: dev, typ, con = p[0], p[1], p[3]
wifi_on = nm("radio", "wifi") == "enabled"
items = []
if dev:
    ip = nm("-g", "IP4.ADDRESS", "device", "show", dev).splitlines()[:1]
    items += [{"type": "label", "text": _('Conexión: {0}', con)}, {"type": "label", "text": _('Dispositivo: {0} ({1})', dev, typ)}, {"type": "label", "text": _('Dirección: {0}', ip[0] if ip else 'sin IP')}]
else: items.append({"type": "label", "text": _("Sin conexión")})
sig_now = ""
if has_wifi:
    items += [{"type": "separator"}, {"type": "button", "text": _("Desactivar WiFi") if wifi_on else _("Activar WiFi"), "command": [me, "wifi-off" if wifi_on else "wifi-on"]}]
    if wifi_on:
        nets = {}
        for line in nm("-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list").splitlines():
            p = split(line)
            if len(p) < 4 or not p[1]: continue
            n = {"use": p[0] == "*", "ssid": p[1], "sig": int(p[2] or 0), "sec": p[3] not in ("", "--")}
            if n["ssid"] not in nets or n["sig"] > nets[n["ssid"]]["sig"]: nets[n["ssid"]] = n
            if n["use"]: sig_now = f"{n['sig']}%"
        known = saved()
        items += [{"type": "label", "text": _("Redes cercanas"), "class": "heading"}]
        for n in sorted(nets.values(), key=lambda n: (not n["use"], -n["sig"]))[:8]:
            tag = "  ✓ conectada" if n["use"] else "  (guardada)" if n["ssid"] in known else "  (con clave)" if n["sec"] else ""
            if n["use"]: items.append({"type": "label", "text": f"{n['ssid']}  {n['sig']}%{tag}"})
            elif n["sec"] and n["ssid"] not in known: items.append({"type": "entry", "placeholder": _('{0} · clave + Intro', n['ssid']), "password": True, "command": [me, "connect", n["ssid"]]})
            else: items.append({"type": "button", "text": f"{n['ssid']}  {n['sig']}%{tag}", "command": [me, "connect", n["ssid"]]})
        if not nets: items.append({"type": "label", "text": _("No se ven redes (¿buscando?)")})
        items.append({"type": "button", "text": _("Buscar redes"), "command": [me, "rescan"]})
if not dev:
    print(json.dumps({"icon": "owee-network-offline", "text": "", "tooltip": _("Sin conexión"), "class": "warn", "popup": {"title": _("Red"), "items": items}})); sys.exit(0)
text = sig_now if typ == "wifi" else ""
print(json.dumps({"icon": "owee-network-wifi" if typ == "wifi" else "owee-network-wired", "text": text, "tooltip": f"{con} ({dev})", "popup": {"title": _("Red"), "items": items}}))
