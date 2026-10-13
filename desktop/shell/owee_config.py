"""Ajustes del escritorio Lite compartidos por el panel y la app de ajustes: ~/.config/owee/settings.json
{"mode": "dark"|"light", "accent": "#RRGGBB", "wallpaper": "/ruta/imagen", "clock_hours": "24"|"12", "clock_seconds": bool, "clock_date": bool}. Si falta o está dañado se usan los valores de fábrica (nunca falla)."""
import json, os
PATH = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "owee", "settings.json")
DEFAULTS = {"mode": "dark", "accent": "#2A9D8F", "wallpaper": "/usr/share/wallpapers/OweeLinux/contents/images/1920x1080.jpg", "clock_hours": "24", "clock_seconds": False, "clock_date": True, "corners": {"tl": "overview", "tr": "none", "bl": "none", "br": "none"}}
ACCENTS = [("Teal", "#2A9D8F"), ("Coral", "#F06548"), ("Azul", "#3B82C4"), ("Violeta", "#8B6FD6"), ("Dorado", "#D9A441"), ("Verde", "#5BA85B")]

def load():
    d = dict(DEFAULTS)
    try:
        j = json.load(open(PATH))
        if j.get("mode") in ("dark", "light"): d["mode"] = j["mode"]
        a = str(j.get("accent", ""))
        if len(a) == 7 and a[0] == "#": int(a[1:], 16); d["accent"] = a
        if isinstance(j.get("wallpaper"), str): d["wallpaper"] = j["wallpaper"]
        if str(j.get("clock_hours")) in ("12", "24"): d["clock_hours"] = str(j["clock_hours"])           # reloj del panel (página Fecha y hora)
        if isinstance(j.get("corners"), dict): d["corners"] = {k: str(v) for k, v in j["corners"].items() if k in ("tl", "tr", "bl", "br")}
        for k in ("clock_seconds", "clock_date"):
            if isinstance(j.get(k), bool): d[k] = j[k]
    except (OSError, ValueError, AttributeError): pass
    return d

def save(d):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    tmp = PATH + ".tmp"; open(tmp, "w").write(json.dumps(d, indent=1)); os.replace(tmp, PATH)     # reemplazo atómico: el panel nunca lee a medias

def palette(d):
    """Colores del panel según modo y acento. El texto sobre el acento se elige claro u oscuro según la luminosidad del acento."""
    r, g, b = (int(d["accent"][i:i + 2], 16) for i in (1, 3, 5)); lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    on = "#102019" if lum > 0.5 else "#FFFFFF"
    if d["mode"] == "light":
        return dict(bg="rgba(246,248,247,0.94)", fg="#17231e", pop="#FFFFFF", line="#cfdad5", entry="#EEF3F1", accent=d["accent"], on=on, hover=f"rgba({r},{g},{b},0.22)", icons="Owee-Light")
    return dict(bg="rgba(16,32,25,0.92)", fg="#EFF0F1", pop="#16251f", line="#2b4a3d", entry="#102019", accent=d["accent"], on=on, hover=f"rgba({r},{g},{b},0.35)", icons="Owee")
