"""Escritura del tema en archivos (sin interfaz gráfica): lo usan Ajustes → Apariencia y `owee-apply-theme` (primer arranque de un usuario).
 · gtk-3.0/4.0: settings.ini (modo oscuro) y gtk.css (@define-color de libadwaita/GTK) · Qt/KDE: ~/.config/kdeglobals (esquema Breeze + colores del tema)
 · labwc: tema de barras de título «Owee-Tema». Todo parte de owee_config.palette()."""
import configparser, os
import owee_config

SCHEME_DIRS = ["/usr/share/color-schemes", os.path.expanduser("~/.local/share/color-schemes")]

def write_gtk_prefs(mode):
    for v in ("3.0", "4.0"):
        d = os.path.expanduser(f"~/.config/gtk-{v}"); os.makedirs(d, exist_ok=True); p = os.path.join(d, "settings.ini")
        lines = [l for l in (open(p).read().splitlines() if os.path.exists(p) else []) if not l.startswith("gtk-application-prefer-dark-theme") and l != "[Settings]"]
        open(p, "w").write("\n".join(["[Settings]", f"gtk-application-prefer-dark-theme={1 if mode == 'dark' else 0}"] + lines) + "\n")

def write_qt_scheme(cfg):
    """Apps Qt/KDE: se parte del esquema Breeze (BreezeDark o BreezeLight, según el tema) y se pintan por encima los colores del tema de OweeLinux en kdeglobals
    (ventana, vistas, botones, selección con el acento, tooltips). Las apps ya abiertas se repintan con la señal de KGlobalSettings; las nuevas lo leen al abrir."""
    pal = owee_config.palette(cfg); mode = pal["mode"]; name = "BreezeDark" if mode == "dark" else "BreezeLight"
    src = next((os.path.join(d, name + ".colors") for d in SCHEME_DIRS if os.path.exists(os.path.join(d, name + ".colors"))), None)
    if not src and mode != "dark": src = next((os.path.join(d, "BreezeClassic.colors") for d in SCHEME_DIRS if os.path.exists(os.path.join(d, "BreezeClassic.colors"))), None)
    if not src: return False
    cp = configparser.RawConfigParser(strict=False); cp.optionxform = str; dst = os.path.expanduser("~/.config/kdeglobals")
    cp.read(dst, encoding="utf-8"); sch = configparser.RawConfigParser(strict=False); sch.optionxform = str; sch.read(src, encoding="utf-8")
    for sec in sch.sections():
        if sec.startswith("Colors:") or sec in ("WM",):
            if not cp.has_section(sec): cp.add_section(sec)
            for k, v in sch.items(sec): cp.set(sec, k, v)
    fg, win, acc = pal["fg"], pal["win"], pal["accent"]; alt = owee_config.mix(win, fg, 0.06); view = pal["entry"] if mode == "dark" else owee_config.mix(win, "#FFFFFF", 0.65)
    over = {"Colors:Window": dict(BackgroundNormal=win, BackgroundAlternate=alt, ForegroundNormal=fg, ForegroundInactive=pal["dim"], DecorationFocus=acc, DecorationHover=acc),
            "Colors:View": dict(BackgroundNormal=view, BackgroundAlternate=owee_config.mix(view, fg, 0.05), ForegroundNormal=fg, ForegroundInactive=pal["dim"], DecorationFocus=acc, DecorationHover=acc),
            "Colors:Button": dict(BackgroundNormal=pal["key"], BackgroundAlternate=pal["keyh"], ForegroundNormal=fg, ForegroundInactive=pal["dim"], DecorationFocus=acc, DecorationHover=acc),
            "Colors:Selection": dict(BackgroundNormal=acc, BackgroundAlternate=acc, ForegroundNormal=pal["on"], ForegroundActive=pal["on"], ForegroundInactive=pal["on"], DecorationFocus=acc, DecorationHover=acc),
            "Colors:Tooltip": dict(BackgroundNormal=pal["pop"], BackgroundAlternate=pal["pop"], ForegroundNormal=fg, DecorationFocus=acc, DecorationHover=acc),
            "Colors:Complementary": dict(BackgroundNormal=win, BackgroundAlternate=alt, ForegroundNormal=fg, DecorationFocus=acc, DecorationHover=acc),
            "Colors:Header": dict(BackgroundNormal=pal["title_active"], BackgroundAlternate=pal["title_inactive"], ForegroundNormal=fg, DecorationFocus=acc, DecorationHover=acc)}
    for sec, vals in over.items():
        if not cp.has_section(sec): cp.add_section(sec)
        for k, v in vals.items(): cp.set(sec, k, _rgbs(v))
    if not cp.has_section("General"): cp.add_section("General")
    cp.set("General", "ColorScheme", "OweeLinux-" + pal["theme"]); cp.set("General", "AccentColor", _rgbs(acc))
    os.makedirs(os.path.dirname(dst), exist_ok=True); tmp = dst + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: cp.write(f, space_around_delimiters=False)
    os.replace(tmp, dst); return True

def write_gtk_css(cfg):
    """Apps GTK3/GTK4 (incluida libadwaita): colores del tema mediante @define-color en gtk.css del usuario."""
    pal = owee_config.palette(cfg); defs = owee_config.gtk_colors(pal)
    css = "/* Generado por Ajustes de OweeLinux (Apariencia). No lo edites a mano: se reescribe al cambiar de tema. */\n" + "".join(f"@define-color {k} {v};\n" for k, v in defs.items())
    for v in ("3.0", "4.0"):
        d = os.path.expanduser(f"~/.config/gtk-{v}"); os.makedirs(d, exist_ok=True); p = os.path.join(d, "gtk.css")
        tmp = p + ".tmp"; open(tmp, "w").write(css); os.replace(tmp, p)

def write_window_theme(cfg):
    """Barras de título y menús de labwc con los colores del tema (se escribe un tema de usuario «Owee-Tema» y labwc lo recarga)."""
    pal = owee_config.palette(cfg); fg, acc = pal["fg"], pal["accent"]
    t = f"""# Generado por Ajustes de OweeLinux (Apariencia)
border.width: 1
padding.height: 4
window.active.border.color: {acc}
window.inactive.border.color: {pal["line"]}
window.active.title.bg.color: {pal["title_active"]}
window.inactive.title.bg.color: {pal["title_inactive"]}
window.active.label.text.color: {fg}
window.inactive.label.text.color: {pal["dim"]}
window.active.button.unpressed.image.color: {fg}
window.inactive.button.unpressed.image.color: {pal["dim"]}
window.active.button.hover.image.color: #F06548
menu.items.bg.color: {pal["pop"]}
menu.items.text.color: {fg}
menu.items.active.bg.color: {acc}
menu.items.active.text.color: {pal["on"]}
osd.bg.color: {pal["pop"]}
osd.border.color: {acc}
osd.label.text.color: {fg}
"""
    d = os.path.expanduser("~/.local/share/themes/Owee-Tema/openbox-3"); os.makedirs(d, exist_ok=True); p = os.path.join(d, "themerc"); tmp = p + ".tmp"; open(tmp, "w").write(t); os.replace(tmp, p)

