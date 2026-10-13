"""Apariencia: modo claro/oscuro, color de acento. Además del panel, se avisa a las apps GTK (settings.ini) y a las Qt/KDE (kdeglobals con el esquema Breeze)."""
import configparser, os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
import owee_config
from .base import Page, page_box, scrolled, heading, run, have
from . import rcxml

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
    rcxml.set_values([("theme/name", "Owee" if mode == "dark" else "Owee-Light")])

def write_qt_scheme(mode, accent):
    """Aplica el esquema de colores a las apps Qt/KDE como hace KDE: copia los grupos [Colors:*] de BreezeDark/Breeze(Light).colors a ~/.config/kdeglobals y fija
    ColorScheme y AccentColor. Las apps ya abiertas no cambian; las que se abran después, sí."""
    name = "BreezeDark" if mode == "dark" else "BreezeLight"
    src = next((os.path.join(d, name + ".colors") for d in SCHEME_DIRS if os.path.exists(os.path.join(d, name + ".colors"))), None)
    if not src and mode != "dark": src = next((os.path.join(d, "BreezeClassic.colors") for d in SCHEME_DIRS if os.path.exists(os.path.join(d, "BreezeClassic.colors"))), None)
    if not src: return False
    cp = configparser.RawConfigParser(strict=False); cp.optionxform = str; dst = os.path.expanduser("~/.config/kdeglobals")
    cp.read(dst, encoding="utf-8"); sch = configparser.RawConfigParser(strict=False); sch.optionxform = str; sch.read(src, encoding="utf-8")
    for sec in sch.sections():
        if sec.startswith("Colors:") or sec in ("WM",):
            if not cp.has_section(sec): cp.add_section(sec)
            for k, v in sch.items(sec): cp.set(sec, k, v)
    if not cp.has_section("General"): cp.add_section("General")
    cp.set("General", "ColorScheme", name); r, g, b = (int(accent[i:i + 2], 16) for i in (1, 3, 5)); cp.set("General", "AccentColor", f"{r},{g},{b}")
    os.makedirs(os.path.dirname(dst), exist_ok=True); tmp = dst + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: cp.write(f, space_around_delimiters=False)
    os.replace(tmp, dst); return True

class Apariencia(Page):
    title = "Apariencia"; icon = "owee-set-appearance"; group = "Personal"; order = 10; keywords = "tema claro oscuro color acento"
    def build(self, app):
        self.app = app; b = page_box("Apariencia"); b.append(heading("Modo"))
        row = Gtk.Box(spacing=12); self.cards = {}
        for mode, name, bg, fg in (("light", "Claro", "#F6F8F7", "#17231e"), ("dark", "Oscuro", "#102019", "#EFF0F1")):
            prev = Gtk.Label(label="Aa", css_classes=["preview"]); pc = Gtk.CssProvider(); pc.load_from_string(f"label {{ background: {bg}; color: {fg}; font-size: 22pt; }}")
            prev.get_style_context().add_provider(pc, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); v.append(prev); v.append(Gtk.Label(label=name))
            btn = Gtk.Button(child=v, has_frame=False, css_classes=["modecard"]); btn.connect("clicked", lambda _b, m=mode: self.set(mode=m)); row.append(btn); self.cards[mode] = btn
        b.append(row); b.append(heading("Color de acento"))
        sw = Gtk.Box(spacing=10); self.swatches = {}
        for name, col in owee_config.ACCENTS:
            btn = Gtk.Button(css_classes=["swatch"], tooltip_text=name); c = Gtk.CssProvider(); c.load_from_string(f"button {{ background: {col}; background-image: none; }}")
            btn.get_style_context().add_provider(c, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION); btn.connect("clicked", lambda _b, x=col: self.set(accent=x)); sw.append(btn); self.swatches[col] = btn
        b.append(sw)
        b.append(Gtk.Label(label="Cambia al instante en el panel, las ventanas y las apps (GTK4/libadwaita, Qt/KDE y LibreOffice con tema del sistema). Algunas apps de terceros con tema propio pueden pedir reiniciarse.", xalign=0, wrap=True, css_classes=["dim-label"]))
        self.refresh(); return scrolled(b)
    def set(self, **kw):
        self.app.change(**kw); c = self.app.cfg
        write_gtk_prefs(c["mode"]); write_qt_scheme(c["mode"], c["accent"]); notify_running_apps(c["mode"]); self.refresh()
    def refresh(self):
        c = self.app.cfg
        for m, btn in self.cards.items(): (btn.add_css_class if m == c["mode"] else btn.remove_css_class)("sel")
        for col, btn in self.swatches.items(): (btn.add_css_class if col.lower() == c["accent"].lower() else btn.remove_css_class)("sel")
PAGE = Apariencia()
