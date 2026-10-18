#!/usr/bin/env python3
"""Monitor del sistema de OweeLinux: procesos con su uso de CPU y memoria, y dos botones para cuando algo se cuelga: «Terminar» (pide al programa que se cierre) y «Forzar cierre» (lo mata).
Lee /proc (sin dependencias); se refresca cada 2 s solo mientras la ventana está visible. Atajo: Ctrl + Mayús + Esc. Los procesos de otros usuarios (o del sistema) piden contraseña de administrador."""
import os, pwd, signal, subprocess, sys
for d in ("/usr/libexec/owee", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shell")): sys.path.insert(0, d)
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib
from owee_i18n import _
import owee_i18n as _i18n; _i18n.apply_direction()
import owee_config

CSS = """
window.background { background: @win@; color: @fg@; } .stat { font-size: 10pt; color: @dim@; } .big { font-size: 13pt; font-weight: bold; color: @fg@; }
treeview { background: @win@; color: @fg@; } treeview:selected { background: @accent@; color: @on@; } treeview header button { background: @entry@; color: @fg@; border: none; box-shadow: none; background-image: none; }
entry, searchentry { background: @entry@; color: @fg@; } button { background-image: none; background: @hover@; color: @fg@; border: none; box-shadow: none; } button.danger { background: #B8392A; color: #fff; }
"""
PAGE = os.sysconf("SC_PAGE_SIZE"); NCPU = os.cpu_count() or 1; ME = os.getuid()

def total_jiffies():
    return sum(int(x) for x in open("/proc/stat").readline().split()[1:])

def snapshot():
    """{pid: (nombre, uid, jiffies, rss_bytes)} de todos los procesos legibles."""
    out = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit(): continue
        try:
            st = open(f"/proc/{pid}/stat").read(); i = st.rindex(")"); f = st[i + 2:].split()      # tras «(nombre)»: estado en f[0]; utime f[11], stime f[12]
            name = st[st.index("(") + 1:i]; j = int(f[11]) + int(f[12])
            rss = int(open(f"/proc/{pid}/statm").read().split()[1]) * PAGE; uid = os.stat(f"/proc/{pid}").st_uid
            try: args = [a.decode(errors="replace") for a in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0") if a]
            except OSError: args = []
            if args and name.startswith(("python", "sh", "bash", "node", "perl", "ruby", "java")):        # los intérpretes se muestran con el programa que ejecutan, no «python3»
                script = next((a for a in args[1:] if not a.startswith("-")), "")
                if script: name = os.path.basename(script)[:40]
            elif args and "/" in args[0] and os.path.basename(args[0]) and name != os.path.basename(args[0])[:15]: name = os.path.basename(args[0])[:40]
            out[int(pid)] = (name, uid, j, rss)
        except (OSError, ValueError, IndexError): continue
    return out

def meminfo():
    d = {}
    for l in open("/proc/meminfo"):
        k, _s, v = l.partition(":")
        if v.split(): d[k] = int(v.split()[0]) * 1024
    return d

def username(uid):
    try: return pwd.getpwuid(uid).pw_name
    except KeyError: return str(uid)

class Monitor(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.oweelinux.Monitor"); self.prev = {}; self.prev_total = 0; self.timer = 0

    def do_activate(self):
        if self.get_active_window(): self.get_active_window().present(); return
        cfg = owee_config.load(); pal = owee_config.palette(cfg); css = CSS
        for k in ("win", "fg", "dim", "hover", "accent", "on", "entry", "line"): css = css.replace("@%s@" % k, pal[k])
        prov = Gtk.CssProvider(); prov.load_from_string(css); Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        s = Gtk.Settings.get_default(); s.set_property("gtk-application-prefer-dark-theme", pal["mode"] == "dark"); s.set_property("gtk-icon-theme-name", pal["icons"])
        fam, size, _m = owee_config.fonts(cfg); s.set_property("gtk-font-name", f"{fam} {size}")
        win = Gtk.ApplicationWindow(application=self, title=_("Monitor del sistema"), icon_name="utilities-system-monitor", default_width=820, default_height=560)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=12, margin_bottom=12, margin_start=14, margin_end=14); win.set_child(root)
        top = Gtk.Box(spacing=24); self.cpu_l = Gtk.Label(xalign=0, css_classes=["big"]); self.mem_l = Gtk.Label(xalign=0, css_classes=["big"]); self.swap_l = Gtk.Label(xalign=0, css_classes=["stat"])
        top.append(self.cpu_l); top.append(self.mem_l); top.append(self.swap_l); root.append(top)
        bar = Gtk.Box(spacing=8); self.search = Gtk.SearchEntry(placeholder_text=_("Buscar proceso…"), hexpand=True); self.search.connect("search-changed", lambda e: self.filter.refilter()); bar.append(self.search)
        self.mine = Gtk.CheckButton(label=_("Solo mis procesos"), active=True); self.mine.connect("toggled", lambda b: self.filter.refilter()); bar.append(self.mine)
        kill = Gtk.Button(label=_("Terminar")); kill.set_tooltip_text(_("Pide al programa que se cierre (puede guardar sus datos)")); kill.connect("clicked", lambda b: self.send(signal.SIGTERM)); bar.append(kill)
        force = Gtk.Button(label=_("Forzar cierre"), css_classes=["danger"]); force.set_tooltip_text(_("Mata el proceso al instante (se pierde lo no guardado): úsalo si el programa está colgado")); force.connect("clicked", lambda b: self.send(signal.SIGKILL)); bar.append(force)
        root.append(bar)
        # columnas: nombre, PID, usuario, CPU %, memoria (MB), uid oculto
        self.store = Gtk.ListStore(str, int, str, float, float, int)
        self.filter = self.store.filter_new(); self.filter.set_visible_func(self.visible); self.sort = Gtk.TreeModelSort(model=self.filter); self.sort.set_sort_column_id(3, Gtk.SortType.DESCENDING)
        self.view = Gtk.TreeView(model=self.sort, enable_search=False, headers_clickable=True)
        for i, (title, kind) in enumerate(((_("Nombre"), "t"), (_("PID"), "t"), (_("Usuario"), "t"), (_("CPU"), "p"), (_("Memoria"), "m"))):
            r = Gtk.CellRendererText(xalign=1.0 if kind != "t" or i == 1 else 0.0)
            col = Gtk.TreeViewColumn(title, r, text=i); col.set_sort_column_id(i); col.set_resizable(True); col.set_expand(i == 0)
            if kind == "p": col.set_cell_data_func(r, lambda c, cell, m, it, d: cell.set_property("text", f"{m.get_value(it, 3):.1f} %"))
            if kind == "m": col.set_cell_data_func(r, lambda c, cell, m, it, d: cell.set_property("text", f"{m.get_value(it, 4):.0f} MB"))
            self.view.append_column(col)
        sc = Gtk.ScrolledWindow(child=self.view, vexpand=True, hexpand=True); root.append(sc)
        self.msg = Gtk.Label(xalign=0, css_classes=["stat"]); root.append(self.msg)
        k = Gtk.EventControllerKey(); k.connect("key-pressed", lambda c, kv, kc, st: (win.close(), True)[1] if kv == Gdk.KEY_Escape and not self.search.get_text() else False); win.add_controller(k)
        win.connect("map", lambda w: self.start()); win.connect("unmap", lambda w: self.stop()); win.present()

    def start(self):
        if not self.timer: self.tick(); self.timer = GLib.timeout_add_seconds(2, self.tick)
    def stop(self):
        if self.timer: GLib.source_remove(self.timer); self.timer = 0

    def visible(self, model, it, _d=None):
        name, uid = model.get_value(it, 0), model.get_value(it, 5)
        if self.mine.get_active() and uid != ME: return False
        q = self.search.get_text().strip().lower()
        return not q or q in name.lower() or q in str(model.get_value(it, 1))

    def tick(self):
        snap = snapshot(); tot = total_jiffies(); dt = max(1, tot - self.prev_total); keep = {}
        sel = self.selected_pid()
        self.store.clear()
        used_cpu = 0.0
        for pid, (name, uid, j, rss) in snap.items():
            pj = self.prev.get(pid, (None, None, j, None))[2]; pct = max(0.0, (j - pj) / dt * NCPU * 100) if self.prev_total else 0.0; used_cpu += pct
            self.store.append([name, pid, username(uid), pct, rss / 1048576, uid])
        self.prev = snap; self.prev_total = tot
        m = meminfo(); used = m.get("MemTotal", 0) - m.get("MemAvailable", 0)
        self.cpu_l.set_label(_('CPU {0:.0f} %', min(100.0, used_cpu / NCPU))); self.mem_l.set_label(_('Memoria {0:.1f} de {1:.1f} GB', used / 2**30, m.get("MemTotal", 0) / 2**30))
        sw = m.get("SwapTotal", 0) - m.get("SwapFree", 0); self.swap_l.set_label(_('Intercambio {0:.1f} GB', sw / 2**30))
        if sel: self.reselect(sel)
        return True

    def selected_pid(self):
        sel = self.view.get_selection().get_selected()
        return sel[0].get_value(sel[1], 1) if sel and sel[1] else None

    def reselect(self, pid):
        it = self.sort.get_iter_first()
        while it:
            if self.sort.get_value(it, 1) == pid: self.view.get_selection().select_iter(it); return
            it = self.sort.iter_next(it)

    def send(self, sig):
        pid = self.selected_pid()
        if not pid: self.msg.set_label(_("Elige primero un proceso de la lista.")); return
        if pid == os.getpid(): self.msg.set_label(_("Ese es este mismo monitor.")); return
        try: owner = os.stat(f"/proc/{pid}").st_uid
        except OSError: self.msg.set_label(_("El proceso ya no existe.")); return
        try:
            if owner == ME: os.kill(pid, sig)
            else: subprocess.Popen(["pkexec", "kill", f"-{int(sig)}", str(pid)])
            self.msg.set_label(_('Enviado a {0}.', pid)); GLib.timeout_add(700, lambda: (self.tick(), False)[1])
        except OSError as e: self.msg.set_label(str(e))

if __name__ == "__main__": sys.exit(Monitor().run(sys.argv[:1]))
