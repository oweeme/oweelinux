"""Apariencia: modo claro/oscuro, color de acento. Además del panel, se avisa a las apps GTK (settings.ini) y a las Qt/KDE (kdeglobals con el esquema Breeze)."""
import configparser, os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
import owee_config
from .base import Page, page_box, scrolled, heading, run, have
from . import rcxml
from owee_i18n import _

SCHEME_DIRS = ["/usr/share/color-schemes", os.path.expanduser("~/.local/share/color-schemes")]

def write_gtk_prefs(mode):
    for v in ("3.0", "4.0"):
        d = os.path.expanduser(f"~/.config/gtk-{v}"); os.makedirs(d, exist_ok=True); p = os.path.join(d, "settings.ini")
        lines = [l for l in (open(p).read().splitlines() if os.path.exists(p) else []) if not l.startswith("gtk-application-prefer-dark-theme") and l != "[Settings]"]
        open(p, "w").write("\n".join(["[Settings]", f"gtk-application-prefer-dark-theme={1 if mode == 'dark' else 0}"] + lines) + "\n")

def notify_running_apps(mode):
    """Avisa a las apps YA abiertas: las de Qt/KDE (señal KGlobalSettings: releen kdeglobals y repintan), las de GTK4/libadwaita y el portal (gsettings color-scheme)
    y a labwc (variante clara u oscura del tema de ventanas)."""
    if have("gdbus"): run(["gdbus", "emit", "--session", "--object-path", "/KGlobalSettings", "--signal", "org.kde.KGlobalSettings.notifyChange", "0", "0"])
    if have("gsettings"):
        run(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "prefer-dark" if mode == "dark" else "prefer-light"])
    rcxml.set_values([("theme/name", "Owee-Tema")])

def _rgbs(h): return "%d,%d,%d" % tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

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

class Apariencia(Page):
    title = _("Apariencia"); icon = "owee-set-appearance"; group = "Personal"; order = 10; keywords = _("tema claro oscuro color acento gris paleta")
    def build(self, app):
        self.app = app; b = page_box(_("Apariencia"), _("Elige un tema. Todos están pensados para no cansar la vista: fondos suaves, buen contraste y colores apagados."))
        b.append(heading(_("Tema")))
        flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=4, min_children_per_line=2, column_spacing=10, row_spacing=10, homogeneous=True, valign=Gtk.Align.START); self.cards = {}
        for tid, th in owee_config.THEMES.items():
            prev = Gtk.Label(label="Aa", css_classes=["preview"]); pc = Gtk.CssProvider()
            pc.load_from_string(f"label {{ background: {th['win']}; color: {th['fg']}; font-size: 20pt; border: 3px solid {th['pop']}; border-bottom: 10px solid {th['accent']}; }}")
            prev.get_style_context().add_provider(pc, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); v.append(prev); v.append(Gtk.Label(label=th["name"], wrap=True, max_width_chars=16, justify=Gtk.Justification.CENTER))
            btn = Gtk.Button(child=v, has_frame=False, css_classes=["modecard"]); btn.connect("clicked", lambda _b, t=tid: self.set_theme(t)); flow.append(btn); self.cards[tid] = btn
        b.append(flow); b.append(heading(_("Color de acento")))
        sw = Gtk.Box(spacing=10); self.swatches = {}
        for name, col in owee_config.ACCENTS:
            btn = Gtk.Button(css_classes=["swatch"], tooltip_text=name); c = Gtk.CssProvider(); c.load_from_string(f"button {{ background: {col}; background-image: none; }}")
            btn.get_style_context().add_provider(c, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION); btn.connect("clicked", lambda _b, x=col: self.apply(accent=x)); sw.append(btn); self.swatches[col] = btn
        b.append(sw)
        b.append(Gtk.Label(label=_("Cambia al instante en el panel, las ventanas y las apps (GTK, Qt/KDE y LibreOffice con tema del sistema). Algunas apps de terceros con tema propio pueden pedir reiniciarse."), xalign=0, wrap=True, css_classes=["dim-label"]))
        self.refresh(); return scrolled(b)
    def set_theme(self, tid): self.apply(theme=tid, mode=owee_config.THEMES[tid]["mode"], accent=owee_config.THEMES[tid]["accent"])       # cada tema trae su acento; luego se puede cambiar
    def apply(self, **kw):
        self.app.change(**kw); c = self.app.cfg
        write_gtk_prefs(c["mode"]); write_gtk_css(c); write_qt_scheme(c); write_window_theme(c); notify_running_apps(c["mode"]); self.refresh()
    def refresh(self):
        c = self.app.cfg; tid = owee_config.theme_of(c)[0]
        for t, btn in self.cards.items(): (btn.add_css_class if t == tid else btn.remove_css_class)("sel")
        for col, btn in self.swatches.items(): (btn.add_css_class if col.lower() == c["accent"].lower() else btn.remove_css_class)("sel")
PAGE = Apariencia()
