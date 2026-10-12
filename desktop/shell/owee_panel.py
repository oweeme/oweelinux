#!/usr/bin/env python3
"""Panel superior de OweeLinux Lite — PROTOTIPO de riesgos (v0.0): Python + GTK4 + gtk4-layer-shell.
Muestra: botón de lanzador (maqueta), reloj y fecha centrados, red (NetworkManager) y batería (UPower).
Regla de diseño (docs/ESCRITORIO.md): llamadas D-Bus asíncronas; el panel nunca se bloquea esperando a un servicio.
Al arrancar escribe en /tmp/owee-panel.log su memoria (Rss/Pss) para medirla."""
import os, sys, time

# gtk4-layer-shell debe cargarse ANTES que libwayland; con Python eso exige LD_PRELOAD (si no, el panel sale como
# una ventana normal y no se acopla). El script se relanza a sí mismo con la variable puesta.
_LS = "/usr/lib/x86_64-linux-gnu/libgtk4-layer-shell.so.0"
if "libgtk4-layer-shell" not in os.environ.get("LD_PRELOAD", "") and os.path.exists(_LS):
    os.environ["LD_PRELOAD"] = (_LS + " " + os.environ.get("LD_PRELOAD", "")).strip()
    os.execv(sys.executable, [sys.executable] + sys.argv)
import gi
gi.require_version("Gtk", "4.0"); gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gtk4LayerShell as LS, GLib, Gdk
try:
    gi.require_version("NM", "1.0"); from gi.repository import NM
except Exception: NM = None
try:
    gi.require_version("UPowerGlib", "1.0"); from gi.repository import UPowerGlib
except Exception: UPowerGlib = None

CSS = b"""
window.owee-panel { background: rgba(16,32,25,0.92); color: #EFF0F1; border-radius: 12px; }
.owee-panel label { padding: 0 10px; }
button.launcher { background: #2A9D8F; color: #102019; border-radius: 8px; padding: 2px 12px; margin: 3px 4px; }
"""

def mem(tag):
    d = {}
    try:
        for l in open("/proc/self/smaps_rollup"):
            k, _, v = l.partition(":")
            if k in ("Rss", "Pss"): d[k] = int(v.split()[0]) / 1024
    except OSError: return
    print(f"[mem] {tag}: Rss={d.get('Rss',0):.0f} MB Pss={d.get('Pss',0):.0f} MB", flush=True)

class Panel(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.oweelinux.PanelPrototype")

    def do_activate(self):
        prov = Gtk.CssProvider(); prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        win = Gtk.ApplicationWindow(application=self); win.add_css_class("owee-panel")
        LS.init_for_window(win); LS.set_layer(win, LS.Layer.TOP); LS.set_namespace(win, "owee-panel")
        for e in (LS.Edge.TOP, LS.Edge.LEFT, LS.Edge.RIGHT): LS.set_anchor(win, e, True)
        LS.set_margin(win, LS.Edge.TOP, 6); LS.set_margin(win, LS.Edge.LEFT, 8); LS.set_margin(win, LS.Edge.RIGHT, 8)
        LS.auto_exclusive_zone_enable(win); win.set_default_size(-1, 30)
        bar = Gtk.CenterBox(); win.set_child(bar)
        bar.set_start_widget(Gtk.Button(label="OweeLinux", css_classes=["launcher"]))
        self.clock = Gtk.Label(); bar.set_center_widget(self.clock)
        right = Gtk.Box(spacing=4); bar.set_end_widget(right)
        self.net = Gtk.Label(label="red…"); self.bat = Gtk.Label(label="…"); right.append(self.net); right.append(self.bat)
        self.tick(); GLib.timeout_add_seconds(1, self.tick)
        self.setup_net(); self.setup_power()
        win.present()
        GLib.timeout_add_seconds(5, lambda: (mem("5 s tras abrir"), False)[1])
        GLib.timeout_add_seconds(40, lambda: (mem("40 s tras abrir"), False)[1])

    def tick(self):
        self.clock.set_text(GLib.DateTime.new_now_local().format("%H:%M  %d %b")); return True

    def setup_net(self):                                   # asíncrono: nunca bloquea el panel
        if NM is None: self.net.set_text("sin NM"); return
        def ready(_src, res):
            try: self.nm = NM.Client.new_finish(res)
            except Exception as e: self.net.set_text("error NM"); print("NM:", e, flush=True); return
            self.nm.connect("notify::primary-connection", lambda *a: self.show_net()); self.show_net()
        NM.Client.new_async(None, ready)

    def show_net(self):
        c = self.nm.get_primary_connection(); self.net.set_text(c.get_id() if c else "sin red")

    def setup_power(self):
        if UPowerGlib is None: self.bat.set_text("sin UPower"); return
        try:
            self.up = UPowerGlib.Client.new(); dev = self.up.get_display_device()
            self.bat.set_text(f"{dev.props.percentage:.0f}%" if dev.props.is_present else "CA")
        except Exception as e: self.bat.set_text("CA"); print("UPower:", e, flush=True)

if __name__ == "__main__":
    t0 = time.time(); mem("tras importar"); Panel().run(sys.argv)
