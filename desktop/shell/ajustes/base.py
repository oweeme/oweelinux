"""Piezas comunes de las páginas de Ajustes de OweeLinux: ejecutar órdenes SIN bloquear la ventana y construir filas de ajustes con un solo estilo.
Regla (docs/ESCRITORIO.md): ninguna orden externa se espera en el hilo de la interfaz; todas llevan tiempo límite."""
import os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib

def run(argv, cb=None, timeout=5, stdin=None):
    """Ejecuta `argv` en segundo plano con límite de `timeout` s y llama a cb(salida, código) en el hilo de la interfaz. Nunca lanza: si no existe el programa, cb("", 127)."""
    try:
        p = Gio.Subprocess.new(["timeout", "-k", "1", str(timeout)] + list(argv), Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE | (Gio.SubprocessFlags.STDIN_PIPE if stdin is not None else Gio.SubprocessFlags.NONE))
    except GLib.Error:
        if cb: GLib.idle_add(lambda: (cb("", 127), False)[1])
        return
    def done(pr, res):
        try: _ok, out, _ = pr.communicate_utf8_finish(res); code = pr.get_exit_status()
        except GLib.Error: out, code = "", 1
        if cb: cb(out or "", code)
    p.communicate_utf8_async(stdin, None, done)

def have(prog): return GLib.find_program_in_path(prog) is not None

class Page:
    """Contrato de una página: `title`, `icon`, `group` y `build(app)` que devuelve el widget. `refresh()` (opcional) se llama al mostrarla."""
    title = ""; icon = "owee-set-info"; group = "Sistema"; order = 50
    def build(self, app): raise NotImplementedError
    def refresh(self): pass

def page_box(title, subtitle=""):
    b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=20, margin_bottom=20, margin_start=24, margin_end=24)
    b.append(Gtk.Label(label=title, xalign=0, css_classes=["title"]))
    if subtitle: b.append(Gtk.Label(label=subtitle, xalign=0, wrap=True, css_classes=["dim-label"]))
    return b

def scrolled(b): return Gtk.ScrolledWindow(child=b, hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True, hexpand=True)

def heading(text): return Gtk.Label(label=text, xalign=0, css_classes=["heading"], margin_top=6)

def row(label, widget, hint=""):
    """Fila «etiqueta ........ control» con una línea de ayuda opcional debajo."""
    r = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    h = Gtk.Box(spacing=12); lab = Gtk.Label(label=label, xalign=0, hexpand=True); h.append(lab); widget.set_valign(Gtk.Align.CENTER); h.append(widget); r.append(h)
    if hint: r.append(Gtk.Label(label=hint, xalign=0, wrap=True, css_classes=["dim-label"]))
    r.add_css_class("setrow"); return r

def dropdown(options, selected, on_change):
    """options: lista de (clave, texto). on_change(clave)."""
    dd = Gtk.DropDown.new_from_strings([t for _k, t in options]); keys = [k for k, _t in options]
    if selected in keys: dd.set_selected(keys.index(selected))
    dd.connect("notify::selected", lambda w, _p: on_change(keys[w.get_selected()]) if w.get_selected() < len(keys) else None); return dd

def switch(active, on_change):
    sw = Gtk.Switch(active=active); sw.connect("notify::active", lambda w, _p: on_change(w.get_active())); return sw

def slider(lo, hi, value, on_change, step=1, width=220):
    sc = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lo, hi, step); sc.set_value(value); sc.set_size_request(width, -1); sc.set_draw_value(True)
    sc.connect("value-changed", lambda w: on_change(w.get_value())); return sc

class Debounce:
    """Agrupa cambios rápidos (un deslizante emite muchos valores): ejecuta fn una sola vez, `ms` después del último."""
    def __init__(self, ms=250): self.ms, self.id = ms, 0
    def __call__(self, fn, *a):
        if self.id: GLib.source_remove(self.id)
        self.id = GLib.timeout_add(self.ms, lambda: (setattr(self, "id", 0), fn(*a), False)[2])

def config_home(): return os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
