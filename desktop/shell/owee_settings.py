#!/usr/bin/env python3
"""Ajustes de OweeLinux Lite (v0.1): Apariencia (claro/oscuro y color de acento) y Fondo de pantalla. Python + GTK4, sin libadwaita.
Escribe ~/.config/owee/settings.json; el panel lo vigila y cambia al instante. Además avisa a las apps GTK (settings.ini) y Qt (esquema Breeze) y cambia el fondo."""
import os, sys, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Gdk, GdkPixbuf
import owee_config

WALL_DIRS = ["/usr/share/backgrounds/oweelinux", "/usr/share/wallpapers/OweeLinux/contents/images", os.path.expanduser("~/Pictures/Wallpapers"),
             os.path.expanduser("~/.local/share/owee/wallpapers")]
CSS = b"""
.swatch { min-width: 34px; min-height: 34px; border-radius: 999px; padding: 0; border: 3px solid transparent; }
.swatch.sel { border-color: @theme_fg_color; }
.modecard { padding: 10px; border-radius: 12px; }
.modecard.sel { background: alpha(@theme_fg_color, 0.12); }
.preview { border-radius: 8px; min-width: 150px; min-height: 90px; }
.thumb { padding: 4px; border-radius: 10px; } .thumb.sel { background: alpha(@theme_fg_color, 0.18); }
.title { font-weight: bold; font-size: 15pt; }
"""

def write_gtk_prefs(mode):
    """Las apps GTK leen gtk-application-prefer-dark-theme; las de Qt/KDE, el esquema de color (si hay kwriteconfig)."""
    for v in ("3.0", "4.0"):
        d = os.path.expanduser(f"~/.config/gtk-{v}"); os.makedirs(d, exist_ok=True); p = os.path.join(d, "settings.ini")
        lines = [l for l in (open(p).read().splitlines() if os.path.exists(p) else []) if not l.startswith("gtk-application-prefer-dark-theme") and l != "[Settings]"]
        open(p, "w").write("\n".join(["[Settings]", f"gtk-application-prefer-dark-theme={1 if mode == 'dark' else 0}"] + lines) + "\n")
    for kw in ("kwriteconfig6", "kwriteconfig5"):
        if GLib.find_program_in_path(kw):
            subprocess.Popen([kw, "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme", "BreezeDark" if mode == "dark" else "BreezeLight"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); break

def set_wallpaper(path):
    h = "/usr/libexec/owee/owee-wallpaper"
    if not os.path.exists(h): h = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "session", "owee-wallpaper")
    try: Gio.Subprocess.new([h, path], Gio.SubprocessFlags.NONE)
    except GLib.Error as e: print("[ajustes] no se pudo cambiar el fondo:", e, flush=True)

class App(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.oweelinux.Settings"); self.cfg = owee_config.load()

    def change(self, **kw):
        self.cfg.update(kw); owee_config.save(self.cfg)
        if "mode" in kw: write_gtk_prefs(self.cfg["mode"]); Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", self.cfg["mode"] == "dark")
        if "wallpaper" in kw: set_wallpaper(self.cfg["wallpaper"])
        self.refresh()

    def do_activate(self):
        prov = Gtk.CssProvider(); prov.load_from_data(CSS); Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", self.cfg["mode"] == "dark")
        win = Gtk.ApplicationWindow(application=self, title="Ajustes de OweeLinux", icon_name="preferences-system", default_width=820, default_height=540)
        stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        stack.add_titled(self.page_appearance(), "apariencia", "Apariencia"); stack.add_titled(self.page_wallpaper(), "fondo", "Fondo de pantalla")
        stack.add_titled(self.page_about(), "acerca", "Acerca de")
        side = Gtk.StackSidebar(stack=stack, width_request=190)
        box = Gtk.Box(); box.append(side); box.append(Gtk.Separator()); box.append(stack); stack.set_hexpand(True)
        win.set_child(box); self.refresh(); win.present()

    def page(self, title):
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, margin_top=20, margin_bottom=20, margin_start=24, margin_end=24)
        b.append(Gtk.Label(label=title, xalign=0, css_classes=["title"])); return b

    def page_appearance(self):
        b = self.page("Apariencia"); b.append(Gtk.Label(label="Modo", xalign=0, css_classes=["heading"]))
        row = Gtk.Box(spacing=12); self.cards = {}
        for mode, name, bg, fg in (("light", "Claro", "#F6F8F7", "#17231e"), ("dark", "Oscuro", "#102019", "#EFF0F1")):
            prev = Gtk.Label(label="Aa", css_classes=["preview"]); pc = Gtk.CssProvider(); pc.load_from_string(f"label {{ background: {bg}; color: {fg}; font-size: 22pt; }}")
            prev.get_style_context().add_provider(pc, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); v.append(prev); v.append(Gtk.Label(label=name))
            btn = Gtk.Button(child=v, has_frame=False, css_classes=["modecard"]); btn.connect("clicked", lambda _b, m=mode: self.change(mode=m)); row.append(btn); self.cards[mode] = btn
        b.append(row); b.append(Gtk.Label(label="Color de acento", xalign=0, css_classes=["heading"]))
        sw = Gtk.Box(spacing=10); self.swatches = {}
        for name, col in owee_config.ACCENTS:
            btn = Gtk.Button(css_classes=["swatch"], tooltip_text=name); c = Gtk.CssProvider(); c.load_from_string(f"button {{ background: {col}; background-image: none; }}")
            btn.get_style_context().add_provider(c, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION); btn.connect("clicked", lambda _b, x=col: self.change(accent=x)); sw.append(btn); self.swatches[col] = btn
        b.append(sw)
        b.append(Gtk.Label(label="El panel cambia al instante. Las apps GTK y Qt (Breeze) toman el modo al abrirlas de nuevo.", xalign=0, wrap=True, css_classes=["dim-label"]))
        return b

    def page_wallpaper(self):
        b = self.page("Fondo de pantalla")
        self.flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=4, min_children_per_line=2, column_spacing=8, row_spacing=8, homogeneous=True, valign=Gtk.Align.START); self.thumbs = {}
        files = []
        for d in WALL_DIRS: files += sorted(f for ext in ("jpg", "jpeg", "png", "webp") for f in glob.glob(os.path.join(d, "*." + ext)))
        for f in files: self.add_thumb(f)
        sc = Gtk.ScrolledWindow(child=self.flow, vexpand=True); b.append(sc)
        pick = Gtk.Button(label="Elegir otra imagen…", halign=Gtk.Align.START); pick.connect("clicked", self.pick_file); b.append(pick); return b

    def add_thumb(self, f):
        try: pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(f, 160, 90, True)          # miniatura pequeña: no se guarda la imagen entera en memoria
        except GLib.Error: return
        img = Gtk.Picture.new_for_pixbuf(pb); img.set_size_request(160, 90)
        btn = Gtk.Button(child=img, has_frame=False, css_classes=["thumb"], tooltip_text=os.path.basename(f), valign=Gtk.Align.START); btn.connect("clicked", lambda _b, x=f: self.change(wallpaper=x))
        self.flow.append(btn); self.thumbs[f] = btn

    def pick_file(self, _b):
        dlg = Gtk.FileDialog(title="Elige una imagen"); flt = Gtk.FileFilter(); flt.set_name("Imágenes"); flt.add_mime_type("image/jpeg"); flt.add_mime_type("image/png"); flt.add_mime_type("image/webp")
        dlg.set_default_filter(flt)
        def done(d, res):
            try: f = d.open_finish(res).get_path()
            except GLib.Error: return
            if f not in self.thumbs: self.add_thumb(f)
            self.change(wallpaper=f)
        dlg.open(self.get_active_window(), None, done)

    def page_about(self):
        b = self.page("Acerca de"); b.append(Gtk.Label(label="OweeLinux Lite · escritorio propio en Python y GTK4.\nLos ajustes se guardan en ~/.config/owee/settings.json (puedes editarlo a mano).", xalign=0, wrap=True)); return b

    def refresh(self):
        for m, btn in self.cards.items(): (btn.add_css_class if m == self.cfg["mode"] else btn.remove_css_class)("sel")
        for c, btn in self.swatches.items(): (btn.add_css_class if c.lower() == self.cfg["accent"].lower() else btn.remove_css_class)("sel")
        for f, btn in self.thumbs.items(): (btn.add_css_class if f == self.cfg["wallpaper"] else btn.remove_css_class)("sel")

if __name__ == "__main__": sys.exit(App().run(sys.argv))
