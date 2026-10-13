#!/usr/bin/env python3
"""Calculadora de OweeLinux: botones grandes y redondeados, resultado en vivo, historial, modo científico (sen, cos, tan, ln, log, √, π, e, ^, !), grados/radianes,
teclado completo (también Ctrl+C / Ctrl+V). Sigue el modo claro/oscuro y el color de acento de Ajustes. Python + GTK4; el cálculo está en calc_engine.py (sin eval)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for p in ("/usr/libexec/owee", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shell")): sys.path.append(p)
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio, GLib
import calc_engine as eng
try: import owee_config
except Exception: owee_config = None

HIST = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "owee", "calc-history.json")
DEBUG = os.environ.get("OWEE_CALC_DEBUG")                     # pruebas: anota el último resultado en un archivo
CSS = """
window.calc { background: @bg@; color: @fg@; }
label.expr { font-size: 26pt; font-weight: 500; } label.expr.s24 { font-size: 21pt; } label.expr.s18 { font-size: 16pt; } label.expr.s14 { font-size: 12pt; }
label.preview { font-size: 13pt; opacity: 0.6; }
label.prev { font-size: 11pt; opacity: 0.5; }
button.k { font-size: 15pt; border-radius: 999px; min-height: 42px; padding: 0; border: none; box-shadow: none; background-image: none; background: @key@; color: @fg@; }
button.k:hover { background: @keyh@; }
button.k.op { background: @opbg@; color: @accent@; font-weight: bold; } button.k.op:hover { background: @opbgh@; }
button.k.eq { background: @accent@; color: @on@; font-weight: bold; } button.k.eq:hover { background: @accenth@; }
button.k.clr { color: #F06548; font-weight: bold; }
button.k.sci { font-size: 12pt; min-height: 34px; background: transparent; } button.k.sci:hover { background: @keyh@; }
button.tool { background: transparent; background-image: none; border: none; box-shadow: none; color: @fg@; border-radius: 999px; min-width: 40px; min-height: 40px; padding: 0; } button.tool:hover { background: @keyh@; }
menubutton.tool > button { background: transparent; background-image: none; border: none; box-shadow: none; color: @fg@; border-radius: 999px; min-width: 40px; min-height: 40px; padding: 0; } menubutton.tool > button:hover { background: @keyh@; }
button.tool.on { background: @opbg@; color: @accent@; }
popover > contents { background: @pop@; color: @fg@; border: 1px solid @accent@; border-radius: 12px; }
popover row { border-radius: 8px; } popover row:hover { background: @keyh@; }
"""
BASIC = [["AC", "⌫", "%", "÷"], ["7", "8", "9", "×"], ["4", "5", "6", "−"], ["1", "2", "3", "+"], ["±", "0", ".", "="]]
SCI = [["sin(", "cos(", "tan(", "ln("], ["log(", "√(", "π", "e"], ["^", "(", ")", "!"]]

def colors():
    pal = owee_config.palette(owee_config.load()) if owee_config else {"fg": "#EFF0F1", "accent": "#2A9D8F", "on": "#102019", "pop": "#16251f", "hover": "rgba(42,157,143,0.35)", "bg": "rgba(16,32,25,0.92)", "icons": "Owee"}
    light = pal["fg"].lower().startswith("#17")
    acc = pal["accent"]; r, g, b = (int(acc[i:i + 2], 16) for i in (1, 3, 5))
    return dict(bg="#F6F8F7" if light else "#102019", fg=pal["fg"], key="#E7EEEB" if light else "#1b3128", keyh="#D8E3DF" if light else "#264438", accent=acc, accenth=acc, on=pal["on"],
                opbg=f"rgba({r},{g},{b},0.18)", opbgh=f"rgba({r},{g},{b},0.30)", pop=pal["pop"]), pal["icons"]

class Calc(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.oweelinux.Calculator"); self.expr = ""; self.degrees = True; self.history = []; self.just_evaluated = False

    def do_activate(self):
        self.prov = Gtk.CssProvider(); Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION); self.restyle()
        try:
            self.load_history(); self.mon = Gio.File.new_for_path(os.path.dirname(owee_config.PATH)).monitor_directory(Gio.FileMonitorFlags.NONE, None) if owee_config else None
            if self.mon: self.mon.connect("changed", lambda *a: GLib.timeout_add(200, lambda: (self.restyle(), False)[1]))
        except Exception: pass
        self.win = win = Gtk.ApplicationWindow(application=self, title="Calculadora", icon_name="owee-calc", default_width=320, default_height=500); win.add_css_class("calc")
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=8, margin_bottom=12, margin_start=12, margin_end=12); win.set_child(root)
        bar = Gtk.Box(spacing=4); root.append(bar)
        self.sci_btn = Gtk.ToggleButton(label="f(x)", css_classes=["tool"]); self.sci_btn.connect("toggled", self.toggle_sci); bar.append(self.sci_btn)
        self.deg_btn = Gtk.Button(label="DEG", css_classes=["tool"]); self.deg_btn.connect("clicked", self.toggle_deg); bar.append(self.deg_btn)
        bar.append(Gtk.Box(hexpand=True))
        self.hist_btn = Gtk.MenuButton(icon_name="owee-calc-history", css_classes=["tool"], tooltip_text="Historial"); self.hpop = Gtk.Popover(); self.hist_btn.set_popover(self.hpop); self.hpop.connect("notify::visible", lambda p, _: p.get_visible() and self.fill_history()); bar.append(self.hist_btn)
        disp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, vexpand=True, valign=Gtk.Align.END); root.append(disp)
        self.prev = Gtk.Label(xalign=1, css_classes=["prev"], ellipsize=3); disp.append(self.prev)
        self.expr_l = Gtk.Label(xalign=1, css_classes=["expr"], ellipsize=1, selectable=False); disp.append(self.expr_l)
        self.preview = Gtk.Label(xalign=1, css_classes=["preview"]); disp.append(self.preview)
        self.sci_grid = self.grid(SCI, True); self.sci_rev = Gtk.Revealer(child=self.sci_grid, transition_type=Gtk.RevealerTransitionType.SLIDE_UP); root.append(self.sci_rev)
        root.append(self.grid(BASIC, False))
        ctl = Gtk.EventControllerKey(); ctl.set_propagation_phase(Gtk.PropagationPhase.CAPTURE); ctl.connect("key-pressed", self.on_key); win.add_controller(ctl)       # captura: Intro no debe activar el botón con foco
        self.update(); win.present()

    def grid(self, rows, sci):
        g = Gtk.Grid(row_spacing=6, column_spacing=6, row_homogeneous=True, column_homogeneous=True)
        for r, row in enumerate(rows):
            for c, t in enumerate(row):
                b = Gtk.Button(label=t, css_classes=["k"], focusable=False, focus_on_click=False); b.set_hexpand(True)
                if sci: b.add_css_class("sci")
                elif t in "÷×−+": b.add_css_class("op")
                elif t == "%": b.add_css_class("op")
                elif t == "=": b.add_css_class("eq")
                elif t == "AC": b.add_css_class("clr")
                b.connect("clicked", lambda _b, t=t: self.press(t)); g.attach(b, c, r, 1, 1)
        return g

    def restyle(self):
        col, icons = colors(); css = CSS
        for k, v in col.items(): css = css.replace("@%s@" % k, v)
        self.prov.load_from_string(css); Gtk.Settings.get_default().set_property("gtk-icon-theme-name", icons)
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", not col["fg"].lower().startswith("#17"))

    # --- lógica de teclas
    def press(self, t):
        if t == "AC": self.expr = ""; self.just_evaluated = False; self.prev.set_text("")
        elif t == "⌫": self.expr = self.expr[:-1] if not self.just_evaluated else ""; self.just_evaluated = False; self.prev.set_text("")
        elif t == "=": self.evaluate(); return
        elif t == "±": self.negate()
        else:
            if self.just_evaluated:
                if t not in "÷×−+^%!": self.expr = ""                              # tras «=», un operador sigue con el resultado; un número empieza de nuevo
                self.just_evaluated = False; self.prev.set_text("")
            if t == ".":
                if self.last_number_has_dot(): return
                if not self.expr or not self.expr[-1].isdigit(): self.expr += "0"
            if t in "÷×−+" and self.expr and self.expr[-1] in "÷×−+": self.expr = self.expr[:-1]           # cambiar de operador
            elif t in "÷×+" and not self.expr: return
            self.expr += t
        self.update()

    def last_number_has_dot(self):
        i = len(self.expr)
        while i > 0 and (self.expr[i - 1].isdigit() or self.expr[i - 1] == "."): i -= 1
        return "." in self.expr[i:]

    def negate(self):
        i = len(self.expr)
        while i > 0 and (self.expr[i - 1].isdigit() or self.expr[i - 1] == "."): i -= 1
        if i < len(self.expr):
            if i >= 2 and self.expr[i - 2:i] == "(−": self.expr = self.expr[:i - 2] + self.expr[i:].rstrip(")") if self.expr.endswith(")") else self.expr[:i - 2] + self.expr[i:]
            else: self.expr = self.expr[:i] + "(−" + self.expr[i:] + ")"
        elif not self.expr: self.expr = "−"

    def evaluate(self):
        if not self.expr: return
        res, err = eng.calc(self.expr, self.degrees)
        if err: self.preview.set_text(err); return
        self.prev.set_text(self.expr + " ="); self.add_history(self.expr, res); self.expr = res.replace("e+", "×10^").replace("e-", "×10^−") if "e" in res else res
        self.just_evaluated = True; self.update()
        if DEBUG: open(DEBUG, "w").write(res)

    def update(self):
        self.expr_l.set_text(self.expr or "0"); n = len(self.expr)
        self.expr_l.set_css_classes(["expr"] + ([] if n <= 10 else ["s24"] if n <= 16 else ["s18"] if n <= 26 else ["s14"]))   # letra más pequeña cuando crece, como en el móvil
        text = ""
        if not self.just_evaluated and self.expr and self.expr[-1] not in "÷×−+^(.":
            res, err = eng.calc(self.expr, self.degrees)
            if res and res != self.expr: text = res
        self.preview.set_text(text)
        if DEBUG: open(DEBUG + ".expr", "w").write(self.expr)

    def toggle_sci(self, b): self.sci_rev.set_reveal_child(b.get_active()); (b.add_css_class if b.get_active() else b.remove_css_class)("on")
    def toggle_deg(self, b): self.degrees = not self.degrees; b.set_label("DEG" if self.degrees else "RAD"); self.update()

    # --- teclado
    def on_key(self, ctl, keyval, code, state):
        name = Gdk.keyval_name(keyval) or ""; ch = chr(Gdk.keyval_to_unicode(keyval)) if Gdk.keyval_to_unicode(keyval) else ""
        if state & Gdk.ModifierType.CONTROL_MASK:
            if name in ("c", "C"): Gdk.Display.get_default().get_clipboard().set(self.expr_l.get_text() if not self.preview.get_text() or self.just_evaluated else self.preview.get_text()); return True
            if name in ("v", "V"): Gdk.Display.get_default().get_clipboard().read_text_async(None, self.pasted); return True
            return False
        if name in ("Return", "KP_Enter") or ch == "=": self.press("="); return True
        if name == "BackSpace": self.press("⌫"); return True
        if name in ("Escape", "Delete"): self.press("AC"); return True
        m = {"*": "×", "x": "×", "X": "×", "/": "÷", "-": "−", ",": ".", "p": "π"}
        ch = m.get(ch, ch)
        if ch and (ch.isdigit() or ch in "+−×÷.%^()!π"): self.press(ch); return True
        return False

    def pasted(self, clip, res):
        try: t = clip.read_text_finish(res) or ""
        except GLib.Error: return
        for ch in t.strip():
            if ch.isdigit() or ch in "+-*/.,%^()": self.press({"*": "×", "/": "÷", "-": "−", ",": "."}.get(ch, ch))

    # --- historial
    def load_history(self):
        try: self.history = json.load(open(HIST))[-50:]
        except (OSError, ValueError): self.history = []
    def add_history(self, e, r):
        self.history.append([e, r]); self.history = self.history[-50:]
        try: os.makedirs(os.path.dirname(HIST), exist_ok=True); tmp = HIST + ".tmp"; open(tmp, "w").write(json.dumps(self.history)); os.replace(tmp, HIST)
        except OSError: pass
    def clear_history(self):
        self.history = []
        try: os.remove(HIST)
        except OSError: pass
    def fill_history(self):
        """Ventanita del historial: lista (con desplazamiento solo si hay muchas operaciones) y el botón «Borrar» siempre visible debajo."""
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        lst = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        if not self.history: lst.append(Gtk.Label(label="Todavía no hay operaciones", margin_top=8, margin_bottom=8))
        for e, r in reversed(self.history[-30:]):
            b = Gtk.Button(has_frame=False, child=Gtk.Label(label=f"{e} = {r}", xalign=1)); b.connect("clicked", lambda _b, r=r: (self.hpop.popdown(), self.use(r))); lst.append(b)
        sc = Gtk.ScrolledWindow(child=lst, propagate_natural_height=True, max_content_height=240, min_content_width=250, hscrollbar_policy=Gtk.PolicyType.NEVER); outer.append(sc)
        if self.history:
            clr = Gtk.Button(label="Borrar historial", css_classes=["k"]); clr.connect("clicked", lambda b: (self.clear_history(), self.hpop.popdown())); outer.append(clr)
        self.hpop.set_child(outer)
    def use(self, r): self.expr = r; self.just_evaluated = False; self.update()

if __name__ == "__main__": sys.exit(Calc().run(sys.argv))
