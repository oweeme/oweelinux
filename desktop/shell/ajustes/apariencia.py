"""Apariencia: modo claro/oscuro, color de acento. Además del panel, se avisa a las apps GTK (settings.ini) y a las Qt/KDE (kdeglobals con el esquema Breeze)."""
import configparser, os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
import owee_config
from .base import Page, page_box, scrolled, heading, run, have
from . import rcxml
from owee_theme import write_gtk_prefs, write_gtk_css, write_qt_scheme, write_window_theme
from owee_i18n import _

def notify_running_apps(mode):
    """Avisa a las apps YA abiertas: las de Qt/KDE (señal KGlobalSettings: releen kdeglobals y repintan), las de GTK4/libadwaita y el portal (gsettings color-scheme)
    y a labwc (variante clara u oscura del tema de ventanas)."""
    # Apps Qt6/KDE (KF6): vigilan ~/.config/kdeglobals con KConfigWatcher, que escucha esta señal de D-Bus (grupo → claves cambiadas); sin ella solo leen el archivo al abrirse
    if have("gdbus"):
        keys = "[b'BackgroundNormal', b'BackgroundAlternate', b'ForegroundNormal', b'ForegroundInactive', b'ForegroundActive', b'DecorationFocus', b'DecorationHover']"
        groups = ["Colors:Window", "Colors:View", "Colors:Button", "Colors:Selection", "Colors:Tooltip", "Colors:Complementary", "Colors:Header"]
        arg = "{" + ", ".join(f"'{g}': {keys}" for g in groups) + ", 'General': [b'ColorScheme', b'AccentColor'], 'Icons': [b'Theme']}"
        run(["gdbus", "emit", "--session", "--object-path", "/kconfig/kdeglobals", "--signal", "org.kde.kconfig.notify.ConfigChanged", arg])
        for t in ("0", "2", "4"):     # señal clásica de KDE (la que repinta de verdad a Dolphin/Kate abiertos): 0 = paleta, 2 = estilo (repinta la barra de herramientas), 4 = iconos
            run(["gdbus", "emit", "--session", "--object-path", "/KGlobalSettings", "--signal", "org.kde.KGlobalSettings.notifyChange", t, "0"])
    if have("gsettings"):
        run(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "prefer-dark" if mode == "dark" else "prefer-light"])
    rcxml.set_values([("theme/name", "Owee-Tema")])

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
