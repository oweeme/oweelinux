"""Texto y ventanas: tamaño y tipo de letra de todo el escritorio (panel, Ajustes, apps GTK y Qt/KDE, barras de título) y altura de las barras de las ventanas.
Se guarda en settings.json (font_size, font_family, font_mono, window_density); el panel y esta ventana cambian al instante, las apps abiertas al volver a abrirlas.
Para agrandar TODO (iconos, paneles, imagen) se usa la Escala de Pantalla."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Pango
import owee_config, owee_theme
from .base import Page, page_box, scrolled, heading, row, dropdown, slider, Debounce
from . import rcxml
from owee_i18n import _

def families(mono=False):
    fm = Gdk.Display.get_default() and Pango.cairo_font_map_get_default()
    out = []
    for f in (fm.list_families() if fm else []):
        if mono and not f.is_monospace(): continue
        out.append(f.get_name())
    return sorted(set(out), key=str.lower)

class Tipografia(Page):
    title = _("Texto y ventanas"); icon = "owee-set-fonts"; group = "Personal"; order = 15; keywords = _("letra fuente tipografía tamaño texto ventanas barra de título")
    def build(self, app):
        self.app = app; c = app.cfg; self.deb = Debounce(350)
        b = page_box(_("Texto y ventanas"), _("Tamaño y tipo de letra, y la altura de las barras de las ventanas. Las apps abiertas cambian al volver a abrirlas."))
        b.append(heading(_("Texto")))
        b.append(row(_("Tamaño del texto"), slider(8, 24, c.get("font_size", 10), lambda v: self.deb(self.apply, {"font_size": round(v)}), width=260)))
        fam = families(); mono = families(True)
        b.append(row(_("Tipo de letra"), dropdown([("", _("Predeterminada"))] + [(f, f) for f in fam], c.get("font_family", ""), lambda k: self.apply({"font_family": k}))))
        b.append(row(_("Letra de ancho fijo (terminal, código)"), dropdown([("", _("Predeterminada"))] + [(f, f) for f in mono], c.get("font_mono", ""), lambda k: self.apply({"font_mono": k}))))
        self.prev = Gtk.Label(label=_("El veloz murciélago hindú comía feliz cardillo y kiwi 0123456789"), xalign=0, wrap=True, css_classes=["card"]); b.append(self.prev)
        b.append(heading(_("Ventanas")))
        b.append(row(_("Barras de título"), dropdown([("compact", _("Compactas")), ("normal", _("Normales")), ("large", _("Amplias"))], c.get("window_density", "normal"), lambda k: self.apply({"window_density": k}))))
        b.append(Gtk.Label(label=_("Para agrandar todo (iconos, paneles e imágenes) usa la Escala en Pantalla."), xalign=0, wrap=True, css_classes=["dim-label"]))
        return scrolled(b)

    def apply(self, kw):
        self.app.change(**kw); cfg = self.app.cfg
        owee_theme.write_fonts(cfg); owee_theme.write_window_theme(cfg)
        fam, size, _m = owee_config.fonts(cfg)
        def fix(root):
            f = rcxml.find(root, "theme/font[place=]", create=True); f.set("place", ""); f.set("name", fam); f.set("size", str(size))
        rcxml.edit(fix)                                                      # barras de título de labwc (recarga solo)
