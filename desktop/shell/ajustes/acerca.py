"""Acerca de: versión de OweeLinux, equipo (CPU, memoria, disco), kernel y sesión."""
import os, platform, shutil
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, row

def osrel():
    d = {}
    for p in ("/usr/lib/os-release", "/etc/os-release"):
        try:
            for l in open(p):
                if "=" in l: k, _, v = l.strip().partition("="); d[k] = v.strip('"')
            break
        except OSError: pass
    return d

def cpu():
    try: return next(l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
    except (OSError, StopIteration): return "desconocida"
def mem():
    try: kb = int(next(l for l in open("/proc/meminfo") if l.startswith("MemTotal")).split()[1]); return f"{kb / 1048576:.1f} GB"
    except (OSError, StopIteration): return "?"

class Acerca(Page):
    title = "Acerca de"; icon = "owee-set-info"; group = "Sistema"; order = 90; keywords = "versión sistema equipo kernel memoria"
    def build(self, app):
        o = osrel(); b = page_box("Acerca de")
        head = Gtk.Box(spacing=16, margin_bottom=8); head.append(Gtk.Image(icon_name="owee-logo", pixel_size=64))
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, valign=Gtk.Align.CENTER); v.append(Gtk.Label(label=o.get("PRETTY_NAME", "OweeLinux"), xalign=0, css_classes=["title"]))
        v.append(Gtk.Label(label="Escritorio Lite · Python + GTK4 · GPLv3", xalign=0, css_classes=["dim-label"])); head.append(v); b.append(head)
        b.append(row("Sitio web", Gtk.LinkButton.new_with_label("https://www.oweeme.com", "www.oweeme.com")))
        du = shutil.disk_usage("/var" if os.path.exists("/var") else "/")
        for k, val in (("Equipo", platform.node()), ("Procesador", cpu()), ("Memoria", mem()), ("Disco (datos)", f"{du.free / 2**30:.0f} GB libres de {du.total / 2**30:.0f} GB"),
                       ("Kernel", platform.release()), ("Sesión", os.environ.get("XDG_CURRENT_DESKTOP", "OweeLite") + " (" + os.environ.get("XDG_SESSION_TYPE", "wayland") + ")"),
                       ("GTK", f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}")):
            b.append(row(k, Gtk.Label(label=val, selectable=True)))
        return scrolled(b)
PAGE = Acerca()
