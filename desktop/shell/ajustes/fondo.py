"""Fondo de pantalla: miniaturas de las carpetas de fondos y «Elegir otra imagen…». El cambio lo hace owee-wallpaper (reinicia swaybg)."""
import glob, os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, GdkPixbuf
from .base import Page, page_box, scrolled

WALL_DIRS = ["/usr/share/backgrounds/oweelinux", "/usr/share/wallpapers/OweeLinux/contents/images", os.path.expanduser("~/Pictures/Wallpapers"), os.path.expanduser("~/Imágenes/Fondos"),
             os.path.expanduser("~/.local/share/owee/wallpapers")]

def set_wallpaper(path):
    h = "/usr/libexec/owee/owee-wallpaper"
    if not os.path.exists(h): h = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "session", "owee-wallpaper")
    try: Gio.Subprocess.new([h, path], Gio.SubprocessFlags.NONE)
    except GLib.Error as e: print("[ajustes] no se pudo cambiar el fondo:", e, flush=True)

class Fondo(Page):
    title = "Fondo de pantalla"; icon = "owee-set-wallpaper"; group = "Personal"; order = 20; keywords = "imagen escritorio wallpaper"
    def build(self, app):
        self.app = app; b = page_box("Fondo de pantalla")
        self.flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=4, min_children_per_line=2, column_spacing=8, row_spacing=8, homogeneous=True, valign=Gtk.Align.START); self.thumbs = {}
        files = []
        for d in WALL_DIRS: files += sorted(f for ext in ("jpg", "jpeg", "png", "webp") for f in glob.glob(os.path.join(d, "*." + ext)))
        for f in files: self.add_thumb(f)
        b.append(Gtk.ScrolledWindow(child=self.flow, vexpand=True))
        pick = Gtk.Button(label="Elegir otra imagen…", halign=Gtk.Align.START); pick.connect("clicked", self.pick_file); b.append(pick)
        self.refresh(); return b
    def add_thumb(self, f):
        try: pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(f, 160, 90, True)          # miniatura pequeña: no se guarda la imagen entera en memoria
        except GLib.Error: return
        img = Gtk.Picture.new_for_pixbuf(pb); img.set_size_request(160, 90)
        btn = Gtk.Button(child=img, has_frame=False, css_classes=["thumb"], tooltip_text=os.path.basename(f), valign=Gtk.Align.START); btn.connect("clicked", lambda _b, x=f: self.choose(x))
        self.flow.append(btn); self.thumbs[f] = btn
    def choose(self, f): self.app.change(wallpaper=f); set_wallpaper(f); self.refresh()
    def pick_file(self, _b):
        dlg = Gtk.FileDialog(title="Elige una imagen"); flt = Gtk.FileFilter(); flt.set_name("Imágenes"); flt.add_mime_type("image/jpeg"); flt.add_mime_type("image/png"); flt.add_mime_type("image/webp"); dlg.set_default_filter(flt)
        def done(d, res):
            try: f = d.open_finish(res).get_path()
            except GLib.Error: return
            if f not in self.thumbs: self.add_thumb(f)
            self.choose(f)
        dlg.open(self.app.get_active_window(), None, done)
    def refresh(self):
        for f, btn in self.thumbs.items(): (btn.add_css_class if f == self.app.cfg["wallpaper"] else btn.remove_css_class)("sel")
PAGE = Fondo()
