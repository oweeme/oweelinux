#!/usr/bin/env python3
"""Panel superior de OweeLinux Lite — PROTOTIPO de riesgos (v0.0): Python + GTK4 + gtk4-layer-shell.
Muestra: lanzador de aplicaciones (búsqueda), reloj y fecha centrados y los WIDGETS (scripts: volumen, red, batería, los del usuario...).
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
button.owee-tray { background: transparent; background-image: none; border: none; box-shadow: none; padding: 2px 4px; min-height: 0; min-width: 0; }
button.owee-tray:hover { background: rgba(42,157,143,0.35); }
menubutton.launcher > button { background: #2A9D8F; background-image: none; color: #102019; border: none; box-shadow: none; border-radius: 8px; padding: 2px 12px; margin: 3px 4px; min-height: 0; }
popover entry { background: #102019; color: #EFF0F1; border: 1px solid #2b4a3d; border-radius: 8px; box-shadow: none; }
popover list, popover row { background: transparent; color: #EFF0F1; }
popover row { border-radius: 8px; padding: 4px 6px; } popover row:hover, popover row:selected { background: rgba(42,157,143,0.35); }
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
        self.btn = Gtk.MenuButton(has_frame=False, child=self.label); self.btn.add_css_class("owee-widget"); self.btn.set_visible(False)   # visible al llegar el primer dato
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
            self.btn.set_visible(not d.get("hidden")); 
            if d.get("hidden"): return
            self.label.set_text(str(d.get("text", ""))); self.label.set_tooltip_text(d.get("tooltip"))
            self.label.remove_css_class("warn")
            if d.get("class"): self.label.add_css_class(d["class"])
            has = bool(d.get("popup"))                      # reasignar la ventanita en cada refresco la CERRABA (bug visto con refrescos de 3 s)
            if has != getattr(self, "has_popup", None): self.has_popup = has; self.btn.set_popover(self.pop if has else None)
        except Exception as e:
            self.btn.set_visible(True); self.label.set_text("⚠ " + self.name); self.label.set_tooltip_text("el widget falló: %s" % e)

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
    """Carga los scripts de las carpetas de widgets. Si el usuario deja un archivo con el MISMO nombre que uno del sistema, gana el del
    usuario (así se cambia un widget del sistema sin tocar la imagen). Se ordenan por nombre: usa prefijos numéricos (10-, 20-...)."""
    found = {}
    for d in WIDGET_DIRS:
        if os.path.isdir(d):
            for f in os.listdir(d):
                p = os.path.join(d, f)
                if os.path.isfile(p) and os.access(p, os.X_OK): found[f] = p
    return [ScriptWidget(found[f], box) for f in sorted(found)]

class Launcher:
    """Lanzador de aplicaciones: botón del panel con ventanita de búsqueda + lista de las apps instaladas (archivos .desktop).
    La lista se construye al ABRIR por primera vez (no al arrancar): no cuesta memoria ni tiempo de sesión si no se usa.
    Escribir filtra; Intro lanza la primera coincidencia; Esc cierra."""
    def __init__(self):
        self.btn = Gtk.MenuButton(label="OweeLinux", has_frame=False); self.btn.add_css_class("launcher")
        self.pop = Gtk.Popover(); self.btn.set_popover(self.pop); self.pop.connect("notify::visible", self.toggled); self.built = False

    def toggled(self, pop, _):
        if not pop.get_visible(): return
        if not self.built: self.build()
        self.entry.set_text(""); self.list.invalidate_filter(); self.entry.grab_focus()

    def build(self):
        self.built = True
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        self.entry = Gtk.SearchEntry(placeholder_text="Buscar aplicación…"); box.append(self.entry)
        self.list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, activate_on_single_click=True)
        self.list.set_filter_func(self.visible_row); self.list.connect("row-activated", lambda l, r: self.launch(r.app))
        for a in sorted((a for a in Gio.AppInfo.get_all() if a.should_show()), key=lambda a: a.get_name().lower()):
            row = Gtk.ListBoxRow(); row.app = a; row.key = (a.get_name() + " " + (a.get_generic_name() or "") + " " + (a.get_keywords() and " ".join(a.get_keywords()) or "")).lower()
            h = Gtk.Box(spacing=10)
            img = Gtk.Image.new_from_gicon(a.get_icon()) if a.get_icon() else Gtk.Image(); img.set_pixel_size(24)
            h.append(img); h.append(Gtk.Label(label=a.get_name(), xalign=0)); row.set_child(h); self.list.append(row)
        sw = Gtk.ScrolledWindow(min_content_height=320, min_content_width=300, child=self.list); box.append(sw)
        self.entry.connect("search-changed", lambda e: (self.list.invalidate_filter(), self.select_first()))
        self.entry.connect("activate", lambda e: self.activate_first())
        self.pop.set_child(box)

    def visible_row(self, row): return self.entry.get_text().lower() in row.key
    def first(self):
        i = 0
        while (r := self.list.get_row_at_index(i)):
            if r.get_child_visible() and self.visible_row(r): return r
            i += 1
    def select_first(self):
        r = self.first()
        if r: self.list.select_row(r)
    def activate_first(self):
        r = self.first()
        if r: self.launch(r.app)

    def launch(self, app):
        self.pop.popdown()
        try: app.launch([], None)
        except GLib.Error as e: print("[launcher] no se pudo abrir", app.get_id(), e, flush=True)

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
        self.launcher = Launcher(); bar.set_start_widget(self.launcher.btn)
        self.clock = Gtk.Label(); bar.set_center_widget(self.clock)
        right = Gtk.Box(spacing=4); bar.set_end_widget(right)
        try:                                           # la bandeja es opcional: si falla, el panel sigue sin ella
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from owee_tray import Tray
            self.tray = Tray(); right.append(self.tray.box)
        except Exception as e: print("[tray] desactivada:", e, flush=True)
        self.widgets = load_widgets(right)             # widgets de usuario (Python, JavaScript...) a la izquierda de los del sistema
        self.tick(); GLib.timeout_add_seconds(1, self.tick)
        win.present()
        if os.environ.get("OWEE_DEBUG_LAYOUT"): GLib.timeout_add_seconds(4, lambda: (self.dump_layout(win), True)[1])
        GLib.timeout_add_seconds(5, lambda: (mem("5 s tras abrir"), False)[1])
        GLib.timeout_add_seconds(40, lambda: (mem("40 s tras abrir"), False)[1])

    def dump_layout(self, win):                                  # solo depuración: posición de cada widget (para pruebas con el ratón)
        out = {}
        for w in self.widgets:
            ok, r = w.btn.compute_bounds(win)
            if ok: out[w.name] = [int(r.get_x() + 8 + r.get_width() / 2), int(r.get_y() + 6 + r.get_height() / 2)]
        for k, it in getattr(getattr(self, "tray", None), "items", {}).items():
            ok, r = it.btn.compute_bounds(win)
            if ok: out["tray"] = [int(r.get_x() + 8 + r.get_width() / 2), int(r.get_y() + 6 + r.get_height() / 2)]
        print("[layout] " + json.dumps(out), flush=True)

    def tick(self):
        self.clock.set_text(GLib.DateTime.new_now_local().format("%H:%M  %d %b")); return True

if __name__ == "__main__":
    t0 = time.time(); mem("tras importar"); Panel().run(sys.argv)
