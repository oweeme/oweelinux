"""Fondo de pantalla: una imagen fija o una PRESENTACIÓN (cambia sola cada cierto tiempo con todas las imágenes o solo con las que elijas). Esta página solo guarda lo elegido en
settings.json; el demonio `owee-wallpaper --daemon` (de la sesión) lo vigila y lo aplica al instante."""
import os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, GdkPixbuf
import owee_config
from owee_i18n import _
from .base import Page, page_box, scrolled, heading, row, dropdown, switch

MINUTES = [("1", _("1 minuto")), ("5", _("5 minutos")), ("10", _("10 minutos")), ("15", _("15 minutos")), ("30", _("30 minutos")), ("60", _("1 hora")), ("180", _("3 horas")), ("1440", _("1 día"))]

class Fondo(Page):
    title = _("Fondo de pantalla"); icon = "owee-set-wallpaper"; group = "Personal"; order = 20; keywords = _("imagen escritorio wallpaper presentación diapositivas cambiar")
    def build(self, app):
        self.app = app; b = page_box(_("Fondo de pantalla")); c = app.cfg
        self.mode = dropdown([("single", _("Una imagen fija")), ("slideshow", _("Presentación (cambia sola)"))], c.get("wallpaper_mode", "single"), self.set_mode)
        b.append(row(_("Modo"), self.mode))
        b.append(row(_("Mostrar iconos en el escritorio"), switch(bool(c.get("desktop_icons", True)), self.set_icons), _("Carpetas y archivos de tu carpeta Escritorio; clic derecho para crear más")))
        self.opts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.opts.append(row(_("Cambiar de imagen cada"), dropdown(MINUTES, str(c.get("slideshow_minutes", 10)) if str(c.get("slideshow_minutes", 10)) in dict(MINUTES) else "10", lambda k: app.change(slideshow_minutes=int(k)))))
        self.opts.append(row(_("Orden aleatorio"), switch(bool(c.get("slideshow_shuffle", True)), lambda on: app.change(slideshow_shuffle=on))))
        sel = Gtk.Box(spacing=8); self.count = Gtk.Label(xalign=0, hexpand=True, css_classes=["dim-label"]); sel.append(self.count)
        for text, fn in ((_("Todas"), self.select_all), (_("Ninguna"), self.select_none)):
            btn = Gtk.Button(label=text); btn.connect("clicked", lambda _b, fn=fn: fn()); sel.append(btn)
        self.opts.append(sel); b.append(self.opts)
        self.hint = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); b.append(self.hint)
        self.flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=4, min_children_per_line=2, column_spacing=8, row_spacing=8, homogeneous=True, valign=Gtk.Align.START); self.thumbs = {}
        for f in owee_config.wallpaper_files(): self.add_thumb(f)
        b.append(Gtk.ScrolledWindow(child=self.flow, vexpand=True))
        pick = Gtk.Button(label=_("Elegir otra imagen…"), halign=Gtk.Align.START); pick.connect("clicked", self.pick_file); b.append(pick)
        self.refresh(); return b

    def add_thumb(self, f):
        try: pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(f, 160, 90, True)          # miniatura pequeña: no se guarda la imagen entera en memoria
        except GLib.Error: return
        ov = Gtk.Overlay(child=Gtk.Picture.new_for_pixbuf(pb)); ov.set_size_request(160, 90)
        tick = Gtk.Label(label="✓", halign=Gtk.Align.END, valign=Gtk.Align.END, css_classes=["tick"], visible=False); ov.add_overlay(tick)
        btn = Gtk.Button(child=ov, has_frame=False, css_classes=["thumb"], tooltip_text=os.path.basename(f), valign=Gtk.Align.START); btn.connect("clicked", lambda _b, x=f: self.clicked(x))
        btn.tick = tick; self.flow.append(btn); self.thumbs[f] = btn

    def set_icons(self, on):
        self.app.change(desktop_icons=on)
        try:
            if on: GLib.spawn_command_line_async("/usr/libexec/owee/owee_icons.py")
            else: GLib.spawn_command_line_async("pkill -f 'owee_icons.py'")
        except GLib.Error: pass

    def slideshow(self): return self.app.cfg.get("wallpaper_mode") == "slideshow"
    def chosen(self): return [f for f in self.app.cfg.get("slideshow", []) if f in self.thumbs]

    def set_mode(self, k):
        if k == "slideshow" and not self.chosen(): self.app.change(wallpaper_mode=k, slideshow=list(self.thumbs))      # al empezar, todas elegidas
        else: self.app.change(wallpaper_mode=k)
        self.refresh()
    def clicked(self, f):
        if self.slideshow():
            cur = self.chosen(); cur = [x for x in cur if x != f] if f in cur else cur + [f]; self.app.change(slideshow=cur)
        else: self.app.change(wallpaper=f)
        self.refresh()
    def select_all(self): self.app.change(slideshow=list(self.thumbs)); self.refresh()
    def select_none(self): self.app.change(slideshow=[]); self.refresh()

    def pick_file(self, _b):
        dlg = Gtk.FileDialog(title=_("Elige una imagen")); flt = Gtk.FileFilter(); flt.set_name(_("Imágenes")); flt.add_mime_type("image/jpeg"); flt.add_mime_type("image/png"); flt.add_mime_type("image/webp"); dlg.set_default_filter(flt)
        def done(d, res):
            try: f = d.open_finish(res).get_path()
            except GLib.Error: return
            if f not in self.thumbs: self.add_thumb(f)
            self.clicked(f)
        dlg.open(self.app.get_active_window(), None, done)

    def refresh(self):
        slide = self.slideshow(); ch = set(self.chosen()); self.opts.set_visible(slide)
        self.hint.set_text(_("Presentación: pulsa las imágenes para incluirlas o quitarlas. Sin ninguna elegida, se usan todas.") if slide else _("Pulsa una imagen para ponerla de fondo."))
        self.count.set_text(_("{0} de {1} imágenes en la presentación", len(ch), len(self.thumbs)))
        for f, btn in self.thumbs.items():
            on = (f in ch) if slide else (f == self.app.cfg["wallpaper"]); (btn.add_css_class if on else btn.remove_css_class)("sel"); btn.tick.set_visible(slide and f in ch)
PAGE = Fondo()
