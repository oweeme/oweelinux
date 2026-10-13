#!/usr/bin/env python3
"""Ajustes de OweeLinux (v0.2): la central de configuración propia del escritorio Lite (Python + GTK4, sin libadwaita).
Cada página es un módulo de `ajustes/` con un objeto PAGE (ver ajustes/base.py); si una página falla al cargar, las demás siguen funcionando.
Los ajustes visuales se guardan en ~/.config/owee/settings.json (el panel lo vigila); los de equipo se aplican con las herramientas del sistema
(wpctl, wlr-randr, labwc, nmcli...). Ninguna orden externa se espera en el hilo de la interfaz."""
import importlib, os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Gdk
import owee_config
from ajustes.base import Page

PAGES = ["apariencia", "fondo", "escritorios", "pantalla", "sonido", "teclado", "raton", "energia", "fechahora", "aplicaciones", "atajos", "actualizaciones", "acerca"]
GROUPS = ["Personal", "Dispositivos", "Sistema"]
CSS = b"""
.swatch { min-width: 34px; min-height: 34px; border-radius: 999px; padding: 0; border: 3px solid transparent; }
.swatch.sel { border-color: @theme_fg_color; }
.modecard { padding: 10px; border-radius: 12px; }
.modecard.sel { background: alpha(@theme_fg_color, 0.12); }
.preview { border-radius: 8px; min-width: 150px; min-height: 90px; }
.thumb { padding: 4px; border-radius: 10px; } .thumb.sel { background: alpha(@theme_fg_color, 0.18); }
.title { font-weight: bold; font-size: 15pt; }
.setrow { padding: 6px 0; border-bottom: 1px solid alpha(@theme_fg_color, 0.08); }
.navrow { padding: 6px 10px; border-radius: 8px; } .navgroup { font-size: 9pt; opacity: 0.6; padding: 10px 10px 2px 10px; }
.card { padding: 12px; border-radius: 12px; background: alpha(@theme_fg_color, 0.06); }
.ok { color: #2A9D8F; } .bad { color: #F06548; }
scale highlight { background: @acc@; } switch:checked { background: @acc@; } switch:checked slider { background: @onacc@; }
row.navrow:selected { background: @acc@; color: @onacc@; } row.navrow:selected image { color: @onacc@; }
"""

class App(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.oweelinux.Settings"); self.cfg = owee_config.load(); self.pages = []; self.built = {}; self.listeners = []

    def style(self):
        """CSS y tema de iconos de la propia app según modo y acento (los mismos del panel)."""
        pal = owee_config.palette(self.cfg); css = CSS.replace(b"@acc@", pal["accent"].encode()).replace(b"@onacc@", pal["on"].encode())
        self.prov.load_from_data(css); Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", self.cfg["mode"] == "dark")
        Gtk.Settings.get_default().set_property("gtk-icon-theme-name", pal["icons"])

    def change(self, **kw):
        """Cambia ajustes visuales (modo, acento, fondo): guarda settings.json y avisa a las páginas que lo escuchan."""
        self.cfg.update(kw); owee_config.save(self.cfg); self.style()
        for fn in self.listeners: fn(kw)

    def do_activate(self):
        self.prov = Gtk.CssProvider(); Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION); self.style()
        for name in PAGES:
            try: self.pages.append(importlib.import_module("ajustes." + name).PAGE)
            except Exception: print("[ajustes] la página", name, "no cargó:\n" + traceback.format_exc(), flush=True)
        w, h = 980, 640                                              # nunca más grande que la pantalla (con escala 150 % o 200 % la pantalla lógica es más pequeña)
        try:
            g = Gdk.Display.get_default().get_monitors().get_item(0).get_geometry(); w, h = min(w, g.width - 60), min(h, g.height - 100)
        except Exception: pass
        win = Gtk.ApplicationWindow(application=self, title="Ajustes de OweeLinux", icon_name="preferences-system", default_width=w, default_height=h)
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, hexpand=True)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, width_request=230)
        self.search = Gtk.SearchEntry(placeholder_text="Buscar ajustes…", margin_top=8, margin_start=8, margin_end=8, margin_bottom=4); side.append(self.search)
        self.nav = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE); self.nav.set_filter_func(self.nav_filter); self.nav.set_header_func(None)
        self.rows = []
        for g in GROUPS:
            ps = sorted((p for p in self.pages if p.group == g), key=lambda p: p.order)
            if not ps: continue
            hdr = Gtk.ListBoxRow(selectable=False, activatable=False, child=Gtk.Label(label=g.upper(), xalign=0, css_classes=["navgroup"])); hdr.group = g; hdr.page = None; self.nav.append(hdr); self.rows.append(hdr)
            for p in ps:
                h = Gtk.Box(spacing=10); h.append(Gtk.Image(icon_name=p.icon, pixel_size=18)); h.append(Gtk.Label(label=p.title, xalign=0))
                r = Gtk.ListBoxRow(child=h, css_classes=["navrow"]); r.page = p; r.group = g; self.nav.append(r); self.rows.append(r)
        self.nav.connect("row-selected", lambda l, r: r and r.page and self.show_page(r.page))
        self.search.connect("search-changed", lambda e: (self.nav.invalidate_filter(), self.select_first_visible()))
        side.append(Gtk.ScrolledWindow(child=self.nav, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER))
        box = Gtk.Box(); box.append(side); box.append(Gtk.Separator()); box.append(self.stack); win.set_child(box); win.present()
        first = next((r for r in self.rows if r.page), None)
        if first: self.nav.select_row(first)

    def nav_filter(self, row):
        q = self.search.get_text().strip().lower()
        if not q: return True
        if row.page is None: return any(r.page and r.group == row.group and q in (r.page.title + " " + getattr(r.page, "keywords", "")).lower() for r in self.rows)
        return q in (row.page.title + " " + getattr(row.page, "keywords", "")).lower()

    def select_first_visible(self):
        for r in self.rows:
            if r.page and self.nav_filter(r): self.nav.select_row(r); return

    def show_page(self, p):
        if p.title not in self.built:
            try: w = p.build(self)
            except Exception: traceback.print_exc(); w = Gtk.Label(label="Esta página no se pudo cargar (mira la terminal).")
            self.built[p.title] = w; self.stack.add_named(w, p.title)
        self.stack.set_visible_child_name(p.title)
        try: p.refresh()
        except Exception: traceback.print_exc()

if __name__ == "__main__": sys.exit(App().run(sys.argv))
