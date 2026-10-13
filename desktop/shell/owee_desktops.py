"""Escritorios virtuales y esquinas activas del panel de OweeLinux Lite.
 · DesktopSwitcher: puntos en el panel (uno por escritorio, el activo resaltado); clic = ir a ese escritorio.
 · Corners: cuatro franjas casi invisibles en las esquinas de la pantalla; al llevar el puntero a una, se ejecuta la acción elegida en Ajustes → Escritorios.
labwc no da una orden «ir al escritorio N» fuera de sus atajos, así que el panel «pulsa» el atajo Super+Alt+F<N> con `wtype` (teclado virtual); el escritorio actual lo
anota `owee-desktop` (lo llaman los atajos de rc.xml) en $XDG_RUNTIME_DIR/owee-desktop y aquí se vigila ese archivo."""
import os, re
import gi
gi.require_version("Gtk", "4.0"); gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Gtk4LayerShell as LS

STATE = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "owee-desktop")
RC = [os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "labwc", "rc.xml"), "/etc/xdg/labwc/rc.xml"]

def desktop_count():
    for p in RC:
        try:
            m = re.search(r"<number>\s*(\d+)\s*</number>", open(p).read())
            if m: return max(1, min(9, int(m.group(1))))
        except OSError: pass
    return 4

def current():
    try: return int(open(STATE).read().strip())
    except (OSError, ValueError): return 1

def press(*keys, mods=("logo", "alt")):
    """Pulsa una combinación con el teclado virtual (wtype)."""
    if not GLib.find_program_in_path("wtype"): print("[escritorios] falta wtype", flush=True); return
    argv = ["wtype"] + [x for m in mods for x in ("-M", m)] + [x for k in keys for x in ("-k", k)] + [x for m in reversed(mods) for x in ("-m", m)]
    try: Gio.Subprocess.new(argv, Gio.SubprocessFlags.STDERR_SILENCE)
    except GLib.Error as e: print("[escritorios]", e, flush=True)

def go(n): press(f"F{n}")
def overview(): press("F9")

class DesktopSwitcher:
    def __init__(self):
        self.box = Gtk.Box(spacing=2); self.box.add_css_class("owee-desks"); self.dots = []; self.build()
        try:
            self.mon = Gio.File.new_for_path(os.path.dirname(STATE)).monitor_directory(Gio.FileMonitorFlags.NONE, None)
            self.mon.connect("changed", lambda m, f, o, ev: f.get_basename() == "owee-desktop" and GLib.idle_add(lambda: (self.mark(), False)[1]))
        except GLib.Error: pass
        sc = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.VERTICAL); sc.connect("scroll", lambda c, dx, dy: (go(max(1, min(self.n, current() + (1 if dy > 0 else -1)))), True)[1]); self.box.add_controller(sc)

    def build(self):
        while (c := self.box.get_first_child()): self.box.remove(c)
        self.n = desktop_count(); self.dots = []
        for i in range(1, self.n + 1):
            b = Gtk.Button(label=str(i), has_frame=False, focusable=False, tooltip_text=f"Escritorio {i}"); b.add_css_class("owee-desk"); b.connect("clicked", lambda _b, i=i: go(i)); self.box.append(b); self.dots.append(b)
        self.mark()

    def mark(self):
        if desktop_count() != self.n: self.build(); return
        cur = current()
        for i, b in enumerate(self.dots, 1): (b.add_css_class if i == cur else b.remove_css_class)("on")

class Corners:
    """Esquinas activas: ventanitas de 4×4 px, capa «overlay», sin teclado. Pasados 150 ms con el puntero dentro se ejecuta la acción; para repetirla hay que salir y volver a entrar."""
    NAMES = {"tl": (LS.Edge.TOP, LS.Edge.LEFT), "tr": (LS.Edge.TOP, LS.Edge.RIGHT), "bl": (LS.Edge.BOTTOM, LS.Edge.LEFT), "br": (LS.Edge.BOTTOM, LS.Edge.RIGHT)}
    def __init__(self, app, run_action):
        self.app, self.run_action, self.wins, self.timers, self.armed = app, run_action, {}, {}, {}; self.actions = {}

    def set_actions(self, actions):
        self.actions = dict(actions)
        for k in self.NAMES:
            on = self.actions.get(k, "none") != "none"
            if on and k not in self.wins: self.make(k)
            if k in self.wins: self.wins[k].set_visible(on)

    def make(self, k):
        w = Gtk.Window(application=self.app, default_width=6, default_height=6, decorated=False); w.add_css_class("owee-corner")
        LS.init_for_window(w); LS.set_layer(w, LS.Layer.OVERLAY); LS.set_namespace(w, "owee-corner"); LS.set_keyboard_mode(w, LS.KeyboardMode.NONE); LS.set_exclusive_zone(w, -1)
        for e in self.NAMES[k]: LS.set_anchor(w, e, True)
        w.set_child(Gtk.Box(width_request=6, height_request=6))
        mc = Gtk.EventControllerMotion(); mc.connect("enter", lambda c, x, y: self.enter(k)); mc.connect("leave", lambda c: self.leave(k)); w.add_controller(mc)
        self.armed[k] = True; self.wins[k] = w; w.present()
        if os.environ.get("OWEE_DEBUG_LAYOUT"): print("[esquina] creada", k, flush=True)

    def enter(self, k):
        if os.environ.get("OWEE_DEBUG_LAYOUT"): print("[esquina] enter", k, flush=True)
        if not self.armed.get(k): return
        self.timers[k] = GLib.timeout_add(150, lambda: (self.fire(k), False)[1])

    def leave(self, k):
        t = self.timers.pop(k, None)
        if t: GLib.source_remove(t)
        self.armed[k] = True

    def fire(self, k):
        self.timers.pop(k, None); self.armed[k] = False; self.run_action(self.actions.get(k, "none"))
