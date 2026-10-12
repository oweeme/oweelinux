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
import json, re
from gi.repository import Gtk, Gtk4LayerShell as LS, GLib, Gdk, Gio
try:
    gi.require_version("NM", "1.0"); from gi.repository import NM
except Exception: NM = None
try:
    gi.require_version("UPowerGlib", "1.0"); from gi.repository import UPowerGlib
except Exception: UPowerGlib = None

CSS = b"""
window.owee-panel { background: rgba(16,32,25,0.92); color: #EFF0F1; border-radius: 12px; }
.owee-panel label { padding: 0 10px; }
.owee-panel label.warn { color: #F06548; }
menubutton.owee-widget > button, menubutton.owee-widget > button label { background: transparent; background-image: none; color: #EFF0F1; border: none; box-shadow: none; padding: 0 2px; min-height: 0; }
menubutton.owee-widget > button:hover, menubutton.owee-widget > button:checked { background: rgba(42,157,143,0.35); background-image: none; }
popover > contents { background: #16251f; color: #EFF0F1; border: 1px solid #2A9D8F; border-radius: 12px; }
popover label.heading { color: #2A9D8F; font-weight: bold; }
popover button { background: #2A9D8F; color: #102019; border: none; border-radius: 8px; box-shadow: none; }
popover scale trough { background: #2b4a3d; } popover scale highlight { background: #2A9D8F; } popover scale slider { background: #EFF0F1; }
popover calendar { background: transparent; color: #EFF0F1; border-color: #2b4a3d; }
popover calendar:selected { background: #2A9D8F; color: #102019; }
popover calendar.view, popover calendar button { color: #EFF0F1; background: transparent; }
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

WIDGET_DIRS = ["/usr/share/owee/widgets", os.path.expanduser("~/.config/owee/widgets")]

class ScriptWidget:
    """Widget hecho con un script en CUALQUIER lenguaje (Python, JavaScript/GJS, shell...): ejecutable que imprime una línea
    JSON. Campos (todos opcionales salvo "text"):
      "text", "tooltip", "class"
      "on_click": ["comando", "arg"...]            se ejecuta al hacer clic y el widget se actualiza
      "popup": {"title": "...", "items": [...]}    ventanita que se abre al hacer clic; items:
          {"type":"label","text":"..."} · {"type":"button","text":"...","command":[...]} ·
          {"type":"slider","min":0,"max":100,"value":50,"command":[...]}  (se llama con el valor como último argumento) ·
          {"type":"calendar"} · {"type":"separator"}
    Se ejecuta de forma asíncrona cada N segundos (comentario `owee-interval: N`), con límite de 5 s (`timeout` mata también
    a los procesos hijos); un fallo no afecta al panel (se muestra "⚠ nombre")."""
    def __init__(self, path, box):
        self.path, self.name = path, os.path.splitext(os.path.basename(path))[0]
        self.data = {}; self.pending = None
        self.label = Gtk.Label(label=self.name + "…")
        self.btn = Gtk.MenuButton(has_frame=False, child=self.label); self.btn.add_css_class("owee-widget")
        self.pop = Gtk.Popover(); self.btn.set_popover(self.pop); self.pop.connect("notify::visible", self.on_popup_toggled)
        click = Gtk.GestureClick(); click.connect("released", lambda *a: self.click()); self.btn.add_controller(click)
        box.append(self.btn)
        m = re.search(r"owee-interval:\s*(\d+)", open(path, errors="replace").read(2000)); self.interval = max(1, int(m.group(1))) if m else 5
        self.run(); GLib.timeout_add_seconds(self.interval, self.run)

    def spawn(self, argv, cb=None):
        try:
            p = Gio.Subprocess.new(["timeout", "-k", "1", "5"] + argv, Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE)
            p.communicate_utf8_async(None, None, cb or (lambda *a: None))
        except GLib.Error as e:
            self.label.set_text("⚠ " + self.name); self.label.set_tooltip_text(str(e)); return None
        return p

    def run(self): self.spawn([self.path], self.done); return True

    def done(self, p, res):
        try:
            ok, out, _ = p.communicate_utf8_finish(res); d = json.loads(out.strip().splitlines()[-1]); self.data = d
            self.label.set_text(str(d.get("text", ""))); self.label.set_tooltip_text(d.get("tooltip"))
            self.label.remove_css_class("warn")
            if d.get("class"): self.label.add_css_class(d["class"])
            self.btn.set_popover(self.pop if d.get("popup") else None)
        except Exception as e:
            self.label.set_text("⚠ " + self.name); self.label.set_tooltip_text("el widget falló: %s" % e)

    def click(self):
        cmd = self.data.get("on_click")
        if cmd: self.spawn(list(cmd), lambda *a: self.run())

    def on_popup_toggled(self, pop, _):
        if pop.get_visible(): self.build_popup(self.data.get("popup") or {})

    def act(self, cmd, extra=()):
        self.spawn(list(cmd) + [str(x) for x in extra], lambda *a: self.run())

    def build_popup(self, spec):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=8, margin_bottom=8, margin_start=10, margin_end=10)
        if spec.get("title"): box.append(Gtk.Label(label=spec["title"], xalign=0, css_classes=["heading"]))
        for it in spec.get("items", []):
            t = it.get("type")
            if t == "label": box.append(Gtk.Label(label=it.get("text", ""), xalign=0))
            elif t == "separator": box.append(Gtk.Separator())
            elif t == "calendar": box.append(Gtk.Calendar())
            elif t == "button":
                b = Gtk.Button(label=it.get("text", "")); b.connect("clicked", lambda _b, c=it.get("command", []): self.act(c)); box.append(b)
            elif t == "slider":
                sc = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, it.get("min", 0), it.get("max", 100), 1)
                sc.set_value(it.get("value", 0)); sc.set_size_request(220, -1); sc.set_draw_value(True)
                sc.connect("value-changed", lambda w, c=it.get("command", []): self.slider_changed(c, w.get_value())); box.append(sc)
        self.pop.set_child(box)

    def slider_changed(self, cmd, value):                        # con retardo: no lanzar un proceso por cada píxel
        if self.pending: GLib.source_remove(self.pending)
        self.pending = GLib.timeout_add(250, lambda: (setattr(self, "pending", None), self.act(cmd, [round(value)]), False)[2])

def load_widgets(box):
    ws = []
    for d in WIDGET_DIRS:
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                p = os.path.join(d, f)
                if os.path.isfile(p) and os.access(p, os.X_OK): ws.append(ScriptWidget(p, box))
    return ws

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
        LS.set_keyboard_mode(win, LS.KeyboardMode.ON_DEMAND)         # que las ventanitas (popovers) reciban teclado al hacer clic
        bar = Gtk.CenterBox(); win.set_child(bar)
        bar.set_start_widget(Gtk.Button(label="OweeLinux", css_classes=["launcher"]))
        self.clock = Gtk.Label(); bar.set_center_widget(self.clock)
        right = Gtk.Box(spacing=4); bar.set_end_widget(right)
        self.widgets = load_widgets(right)             # widgets de usuario (Python, JavaScript...) a la izquierda de los del sistema
        self.net = Gtk.Label(label="red…"); self.bat = Gtk.Label(label="…"); right.append(self.net); right.append(self.bat)
        self.tick(); GLib.timeout_add_seconds(1, self.tick)
        self.setup_net(); self.setup_power()
        win.present()
        if os.environ.get("OWEE_DEBUG_LAYOUT"): GLib.timeout_add_seconds(4, lambda: (self.dump_layout(win), False)[1])
        GLib.timeout_add_seconds(5, lambda: (mem("5 s tras abrir"), False)[1])
        GLib.timeout_add_seconds(40, lambda: (mem("40 s tras abrir"), False)[1])

    def dump_layout(self, win):                                  # solo depuración: posición de cada widget (para pruebas con el ratón)
        out = {}
        for w in self.widgets:
            ok, r = w.btn.compute_bounds(win)
            if ok: out[w.name] = [int(r.get_x() + 8 + r.get_width() / 2), int(r.get_y() + 6 + r.get_height() / 2)]
        print("[layout] " + json.dumps(out), flush=True)

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
