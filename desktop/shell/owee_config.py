"""Ajustes del escritorio Lite compartidos por el panel y la app de ajustes: ~/.config/owee/settings.json
{"wallpaper_mode": "single"|"slideshow", "slideshow": [rutas], "slideshow_minutes": N, "slideshow_shuffle": bool, "theme": "koi"|"claro"|"pizarra"|"niebla"|"crepusculo"|"arena"|"medianoche", "mode": "dark"|"light" (lo fija el tema), "accent": "#RRGGBB", "wallpaper": "/ruta/imagen", "clock_hours": "24"|"12", "clock_seconds": bool, "clock_date": bool}. Si falta o está dañado se usan los valores de fábrica (nunca falla)."""
import json, os
from owee_i18n import _
PATH = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "owee", "settings.json")
DEFAULTS = {"wallpaper_mode": "single", "slideshow": [], "slideshow_minutes": 10, "slideshow_shuffle": True, "lang": "", "theme": "koi", "mode": "dark", "accent": "#2A9D8F", "wallpaper": "/usr/share/wallpapers/OweeLinux/contents/images/1920x1080.jpg", "clock_hours": "24", "clock_seconds": False, "clock_date": True, "corners": {"tl": "overview", "tr": "none", "bl": "none", "br": "none"}}
ACCENTS = [(_("Teal"), "#2A9D8F"), (_("Coral"), "#F06548"), (_("Azul"), "#3B82C4"), (_("Violeta"), "#8B6FD6"), (_("Dorado"), "#D9A441"), (_("Verde"), "#5BA85B")]

WALLPAPER_DIRS = ["/usr/share/backgrounds/oweelinux", os.path.expanduser("~/Pictures/Wallpapers"), os.path.expanduser("~/Imágenes/Fondos"), os.path.expanduser("~/.local/share/owee/wallpapers")]
DEFAULT_WALLPAPER = "/usr/share/wallpapers/OweeLinux/contents/images/1920x1080.jpg"

def wallpaper_files():
    """Todas las imágenes de las carpetas de fondos (las del sistema y las del usuario), en orden de nombre."""
    import glob
    out = []
    for d in WALLPAPER_DIRS:
        for ext in ("jpg", "jpeg", "png", "webp"): out += sorted(glob.glob(os.path.join(d, "*." + ext)))
    return out

def load():
    d = dict(DEFAULTS)
    try:
        j = json.load(open(PATH))
        if j.get("mode") in ("dark", "light"): d["mode"] = j["mode"]
        if isinstance(j.get("lang"), str): d["lang"] = j["lang"]
        if j.get("wallpaper_mode") in ("single", "slideshow"): d["wallpaper_mode"] = j["wallpaper_mode"]            # fondo fijo o presentación de imágenes
        if isinstance(j.get("slideshow"), list): d["slideshow"] = [x for x in j["slideshow"] if isinstance(x, str)]
        try: d["slideshow_minutes"] = max(1, min(1440, int(j.get("slideshow_minutes", d["slideshow_minutes"]))))
        except (TypeError, ValueError): pass
        if isinstance(j.get("slideshow_shuffle"), bool): d["slideshow_shuffle"] = j["slideshow_shuffle"]
        if j.get("theme") in THEMES: d["theme"] = j["theme"]; d["mode"] = THEMES[j["theme"]]["mode"]
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

# Temas: «dark» o «light» de base + colores. Pensados para no cansar la vista: fondos suaves (nunca negro ni blanco puro), contraste de texto ≥ 7:1 y acentos apagados.
# win=fondo de ventanas, fg=texto, pop=ventanitas, line=líneas, entry=campos, accent=acento por defecto del tema (se puede cambiar).
THEMES = {
    "koi":        dict(name=_("Koi (oscuro)"),        mode="dark",  win="#102019", fg="#EFF0F1", pop="#16251f", line="#2b4a3d", entry="#102019", accent="#2A9D8F"),
    "claro":      dict(name=_("Claro"),               mode="light", win="#F6F8F7", fg="#17231e", pop="#FFFFFF", line="#cfdad5", entry="#EEF3F1", accent="#2A9D8F"),
    "pizarra":    dict(name=_("Pizarra (gris oscuro)"), mode="dark",  win="#262a30", fg="#dde1e6", pop="#2e333a", line="#3d434c", entry="#1f2328", accent="#6FA8C7"),
    "niebla":     dict(name=_("Niebla (gris claro)"), mode="light", win="#ECEDEF", fg="#23272d", pop="#F6F6F7", line="#d0d3d8", entry="#E1E3E7", accent="#4F8583"),
    "crepusculo": dict(name=_("Crepúsculo (violeta)"), mode="dark", win="#2a2833", fg="#e6e3ee", pop="#322f3d", line="#443f52", entry="#23212b", accent="#B39DDB"),
    "arena":      dict(name=_("Arena (cálido claro)"), mode="light", win="#F4EFE6", fg="#35302a", pop="#FBF8F2", line="#ddd4c5", entry="#EBE4D6", accent="#B9622F"),
    "medianoche": dict(name=_("Medianoche (azul grisáceo)"), mode="dark", win="#1d2330", fg="#d9dee8", pop="#252c3b", line="#343d52", entry="#181d28", accent="#7FB4CA"),
}
DEFAULT_THEME = "koi"

def _rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
def _hex(c): return "#%02X%02X%02X" % tuple(max(0, min(255, round(x))) for x in c)
def mix(a, b, t):
    """Mezcla dos colores #RRGGBB: t=0 → a, t=1 → b."""
    ca, cb = _rgb(a), _rgb(b); return _hex([x + (y - x) * t for x, y in zip(ca, cb)])

def theme_of(d):
    t = d.get("theme")
    if t in THEMES: return t, THEMES[t]
    return ("claro", THEMES["claro"]) if d.get("mode") == "light" else (DEFAULT_THEME, THEMES[DEFAULT_THEME])        # compatibilidad con ajustes antiguos (solo modo)

def palette(d):
    """Colores de panel, apps y ventanas según el tema y el acento. El texto sobre el acento se elige claro u oscuro según su luminosidad."""
    tid, th = theme_of(d); light = th["mode"] == "light"
    r, g, b = _rgb(d["accent"]); lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    def L(h):
        f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        rr, gg, bb = (x / 255 for x in _rgb(h)); return 0.2126 * f(rr) + 0.7152 * f(gg) + 0.0722 * f(bb)
    ratio = lambda a, b: (max(L(a), L(b)) + 0.05) / (min(L(a), L(b)) + 0.05)
    on = max(("#0F1A15", "#FFFFFF"), key=lambda c: ratio(c, d["accent"]))          # el de más contraste sobre el acento
    wr, wg, wb = _rgb(th["win"])
    return dict(bg=f"rgba({wr},{wg},{wb},0.94)" if light else f"rgba({wr},{wg},{wb},0.92)", win=th["win"], fg=th["fg"], pop=th["pop"], line=th["line"], entry=th["entry"], accent=d["accent"], on=on,
                hover=f"rgba({r},{g},{b},{0.22 if light else 0.35})", icons="Owee-Light" if light else "Owee", mode=th["mode"], theme=tid,
                key=mix(th["win"], th["fg"], 0.08), keyh=mix(th["win"], th["fg"], 0.16), dim=mix(th["fg"], th["win"], 0.45),
                title_active=mix(th["win"], th["fg"], 0.03), title_inactive=mix(th["win"], th["fg"], 0.10 if light else 0.06))


def gtk_colors(pal):
    """Colores con nombre de GTK4/libadwaita (@define-color) a partir de la paleta: los usan gtk.css del usuario y las apps propias."""
    fg, win, pop, acc = pal["fg"], pal["win"], pal["pop"], pal["accent"]
    view = pal["entry"] if pal["mode"] == "dark" else mix(win, "#FFFFFF", 0.65)
    return dict(window_bg_color=win, window_fg_color=fg, view_bg_color=view, view_fg_color=fg, headerbar_bg_color=pal["title_active"], headerbar_fg_color=fg, headerbar_border_color=pal["line"],
                card_bg_color=pop, card_fg_color=fg, popover_bg_color=pop, popover_fg_color=fg, dialog_bg_color=win, dialog_fg_color=fg, sidebar_bg_color=mix(win, fg, 0.04), sidebar_fg_color=fg,
                accent_bg_color=acc, accent_color=acc, accent_fg_color=pal["on"],
                theme_bg_color=win, theme_fg_color=fg, theme_base_color=view, theme_text_color=fg, theme_selected_bg_color=acc, theme_selected_fg_color=pal["on"],
                theme_unfocused_bg_color=win, theme_unfocused_fg_color=fg, theme_unfocused_base_color=view, theme_unfocused_text_color=fg, theme_unfocused_selected_bg_color=acc, theme_unfocused_selected_fg_color=pal["on"],
                borders=pal["line"], unfocused_borders=pal["line"], insensitive_fg_color=pal["dim"], insensitive_bg_color=mix(win, fg, 0.05))
