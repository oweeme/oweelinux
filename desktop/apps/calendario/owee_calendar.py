#!/usr/bin/env python3
"""Calendario de OweeLinux: vista mensual (semana desde el lunes), eventos con hora por día y avisos (los lanza el panel a la hora del evento). Python + GTK4, sin servicios ni cuentas:
los eventos viven en ~/.local/share/owee/calendar.json {"AAAA-MM-DD": [{"t": "HH:MM", "title": "…"}]}. Se abre desde el lanzador o al hacer clic en la fecha del panel (botón «Abrir calendario»)."""
import calendar, datetime, json, os, re, sys
for d in ("/usr/libexec/owee", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shell")): sys.path.insert(0, d)
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib
from owee_i18n import _
import owee_i18n as _i18n; _i18n.apply_direction()
import owee_config

DATA = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "owee", "calendar.json")
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
HORA = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")

def load():
    try: d = json.load(open(DATA, encoding="utf-8"))
    except (OSError, ValueError): return {}
    return {k: [e for e in v if isinstance(e, dict) and "title" in e] for k, v in d.items() if isinstance(v, list)} if isinstance(d, dict) else {}

def save(ev):
    os.makedirs(os.path.dirname(DATA), exist_ok=True); tmp = DATA + ".tmp"; json.dump({k: v for k, v in ev.items() if v}, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(tmp, DATA)

CSS = """
window.background { background: @win@; color: @fg@; } .cal-title { font-size: 18pt; font-weight: bold; } .dow { color: @dim@; font-size: 9pt; }
button.day { background: transparent; background-image: none; border: none; box-shadow: none; border-radius: 10px; min-width: 56px; min-height: 48px; color: @fg@; }
button.day:hover { background: @hover@; } button.day.other { color: @dim@; } button.day.today { border: 2px solid @accent@; } button.day.sel { background: @accent@; color: @on@; }
button.day label.dot { color: @accent@; font-size: 8pt; } button.day.sel label.dot { color: @on@; }
entry { background: @entry@; color: @fg@; } button.flat { background: transparent; background-image: none; box-shadow: none; color: @fg@; } button.flat:hover { background: @hover@; }
button.suggested-action { background: @accent@; color: @on@; background-image: none; } .evrow { padding: 6px 8px; border-bottom: 1px solid @line@; }
"""

class Cal(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.oweelinux.Calendar")

    def do_activate(self):
        if self.get_active_window(): self.get_active_window().present(); return
        cfg = owee_config.load(); pal = owee_config.palette(cfg); css = CSS
        for k in ("win", "fg", "dim", "hover", "accent", "on", "entry", "line"): css = css.replace("@%s@" % k, pal[k])
        prov = Gtk.CssProvider(); prov.load_from_string(css); Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", pal["mode"] == "dark"); Gtk.Settings.get_default().set_property("gtk-icon-theme-name", pal["icons"])
        fam, size, _m = owee_config.fonts(cfg); Gtk.Settings.get_default().set_property("gtk-font-name", f"{fam} {size}")
        self.ev = load(); t = datetime.date.today(); self.y, self.m, self.sel = t.year, t.month, t
        win = Gtk.ApplicationWindow(application=self, title=_("Calendario"), icon_name="owee-calendar", default_width=860, default_height=560)
        root = Gtk.Box(spacing=18, margin_top=16, margin_bottom=16, margin_start=18, margin_end=18); win.set_child(root)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, hexpand=True); root.append(left)
        head = Gtk.Box(spacing=6); self.title = Gtk.Label(xalign=0, hexpand=True, css_classes=["cal-title"]); head.append(self.title)
        for sym, d in (("‹", -1), ("›", 1)):
            b = Gtk.Button(label=sym, css_classes=["flat"]); b.connect("clicked", lambda _b, d=d: self.move(d)); head.append(b)
        hoy = Gtk.Button(label=_("Hoy"), css_classes=["flat"]); hoy.connect("clicked", lambda _b: self.today()); head.append(hoy); left.append(head)
        self.grid = Gtk.Grid(column_homogeneous=True, row_spacing=2, column_spacing=2); left.append(self.grid)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, width_request=280); root.append(side)
        self.day_l = Gtk.Label(xalign=0, css_classes=["cal-title"], wrap=True); side.append(self.day_l)
        self.list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); side.append(Gtk.ScrolledWindow(child=self.list, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER))
        add = Gtk.Box(spacing=6); self.hh = Gtk.Entry(placeholder_text="HH:MM", width_chars=6, max_width_chars=6); self.tt = Gtk.Entry(placeholder_text=_("Título del evento"), hexpand=True)
        ok = Gtk.Button(label=_("Añadir"), css_classes=["suggested-action"]); ok.connect("clicked", lambda _b: self.add()); self.tt.connect("activate", lambda _e: self.add())
        add.append(self.hh); add.append(self.tt); add.append(ok); side.append(add); self.err = Gtk.Label(xalign=0, css_classes=["dim-label"]); side.append(self.err)
        self.draw(); win.present()

    def move(self, d):
        m = self.m + d; self.y += (m - 1) // 12; self.m = (m - 1) % 12 + 1; self.draw()
    def today(self): t = datetime.date.today(); self.y, self.m, self.sel = t.year, t.month, t; self.draw()
    def pick(self, d): self.sel = d; self.y, self.m = d.year, d.month; self.draw()

    def draw(self):
        self.title.set_text(f"{_(MESES[self.m - 1]).capitalize()} {self.y}")
        while (c := self.grid.get_first_child()): self.grid.remove(c)
        for i, n in enumerate(DIAS): self.grid.attach(Gtk.Label(label=_(n)[:3].capitalize(), css_classes=["dow"], margin_bottom=4), i, 0, 1, 1)
        today = datetime.date.today()
        for r, week in enumerate(calendar.Calendar(0).monthdatescalendar(self.y, self.m), 1):
            for c, d in enumerate(week):
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign=Gtk.Align.CENTER); box.append(Gtk.Label(label=str(d.day)))
                box.append(Gtk.Label(label="●" if self.ev.get(d.isoformat()) else " ", css_classes=["dot"]))
                b = Gtk.Button(child=box, css_classes=["day"] + (["other"] if d.month != self.m else []) + (["today"] if d == today else []) + (["sel"] if d == self.sel else []))
                b.connect("clicked", lambda _b, d=d: self.pick(d)); self.grid.attach(b, c, r, 1, 1)
        self.day_l.set_text(f"{_(DIAS[self.sel.weekday()]).capitalize()} {self.sel.day} · {_(MESES[self.sel.month - 1])} {self.sel.year}")
        while (c := self.list.get_first_child()): self.list.remove(c)
        items = sorted(self.ev.get(self.sel.isoformat(), []), key=lambda e: e.get("t", ""))
        if not items: self.list.append(Gtk.Label(label=_("No hay eventos este día."), xalign=0, css_classes=["dim-label"], margin_top=6))
        for e in items:
            r = Gtk.Box(spacing=8, css_classes=["evrow"]); r.append(Gtk.Label(label=e.get("t", ""), css_classes=["dim-label"])); r.append(Gtk.Label(label=e["title"], xalign=0, hexpand=True, wrap=True))
            x = Gtk.Button(label="✕", css_classes=["flat"], tooltip_text=_("Eliminar")); x.connect("clicked", lambda _b, e=e: self.remove(e)); r.append(x); self.list.append(r)

    def add(self):
        t, title = self.hh.get_text().strip(), self.tt.get_text().strip()
        if not title: return
        if t and not HORA.match(t): self.err.set_text(_("Hora (HH:MM)")); return
        if t: h, m = t.split(":"); t = f"{int(h):02d}:{m}"
        self.ev.setdefault(self.sel.isoformat(), []).append({"t": t, "title": title}); save(self.ev); self.hh.set_text(""); self.tt.set_text(""); self.err.set_text(""); self.draw()

    def remove(self, e):
        self.ev[self.sel.isoformat()].remove(e); save(self.ev); self.draw()

if __name__ == "__main__": sys.exit(Cal().run(sys.argv))
