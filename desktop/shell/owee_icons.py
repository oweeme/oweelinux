#!/usr/bin/env python3
"""Iconos del escritorio de OweeLinux: muestra el contenido de la carpeta Escritorio (~/Desktop o la de XDG) sobre el fondo, como en Deepin.
 · Doble clic: abre (carpetas, documentos y lanzadores .desktop). Un clic selecciona; Ctrl+clic selecciona varios.
 · Clic derecho en un hueco: Nueva carpeta, Nuevo documento, Seleccionar todo, Pegar, Actualizar, Ordenar por, Configuración del escritorio, Abrir en terminal, Configuración de pantalla, Establecer fondo.
 · Clic derecho en un icono: Abrir, Copiar, Cortar, Cambiar nombre, Mover a la papelera.
Es una capa de layer-shell POR DEBAJO de las ventanas y por encima del fondo, respeta el panel y no roba el teclado salvo para escribir un nombre. Se apaga en Ajustes → Fondo de pantalla («Mostrar iconos en el escritorio»)."""
import json, os, subprocess, sys
for d in ("/usr/libexec/owee", os.path.dirname(os.path.abspath(__file__))): sys.path.append(d)
_LS = "/usr/lib/x86_64-linux-gnu/libgtk4-layer-shell.so.0"
if "libgtk4-layer-shell" not in os.environ.get("LD_PRELOAD", "") and os.path.exists(_LS):
    os.environ["LD_PRELOAD"] = (_LS + " " + os.environ.get("LD_PRELOAD", "")).strip(); os.execv(sys.executable, [sys.executable] + sys.argv)
import gi
gi.require_version("Gtk", "4.0"); gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Gtk4LayerShell as LS
from owee_i18n import _
import owee_i18n; owee_i18n.apply_direction()

HOME = os.path.expanduser("~"); STATE = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "owee", "desktop.json")
SETTINGS = "/usr/libexec/owee/owee_settings.py"
CSS = b"""
window.desk { background: transparent; }
flowboxchild.desk-item { padding: 6px 4px; margin: 2px; border-radius: 10px; background: transparent; }
flowboxchild.desk-item:selected { background: alpha(#2A9D8F, 0.50); }
flowboxchild.desk-item:hover { background: alpha(#ffffff, 0.14); }
label.desk-name { color: #ffffff; font-size: 10pt; text-shadow: 0 1px 3px rgba(0,0,0,0.9), 0 0 2px rgba(0,0,0,0.9); }
"""

def desktop_dir():
    try: d = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, timeout=3).stdout.strip()
    except Exception: d = ""
    if not d or d == HOME: d = os.path.join(HOME, "Desktop")
    os.makedirs(d, exist_ok=True); return d

def load_sort():
    try: s = json.load(open(STATE)).get("sort", "name")
    except (OSError, ValueError, AttributeError): s = "name"
    return s if s in ("name", "date", "size", "type") else "name"

def save_sort(s):
    try: os.makedirs(os.path.dirname(STATE), exist_ok=True); json.dump({"sort": s}, open(STATE, "w"))
    except OSError: pass

def unique(d, name, ext=""):
    n, i = name + ext, 2
    while os.path.exists(os.path.join(d, n)): n = f"{name} {i}{ext}"; i += 1
    return os.path.join(d, n)

def open_path(path):
    try:
        if path.endswith(".desktop"):
            ai = Gio.DesktopAppInfo.new_from_filename(path)
            if ai: ai.launch([], None); return
        subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception as e: print("[icons] no se pudo abrir:", e, flush=True)

def settings(page=""):
    env = dict(os.environ); env["OWEE_PAGE"] = page
    subprocess.Popen([SETTINGS], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

class Desk(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.oweelinux.DesktopIcons"); self.cut = []; self.sort = load_sort()

    def do_activate(self):
        if self.get_windows(): return
        self.dir = desktop_dir(); prov = Gtk.CssProvider(); prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        w = self.win = Gtk.ApplicationWindow(application=self, decorated=False); w.add_css_class("desk")
        LS.init_for_window(w); LS.set_layer(w, LS.Layer.BOTTOM); LS.set_namespace(w, "owee-desktop-icons")
        for e in (LS.Edge.TOP, LS.Edge.BOTTOM, LS.Edge.LEFT, LS.Edge.RIGHT): LS.set_anchor(w, e, True)
        LS.set_keyboard_mode(w, LS.KeyboardMode.NONE)
        self.flow = Gtk.FlowBox(orientation=Gtk.Orientation.VERTICAL, selection_mode=Gtk.SelectionMode.MULTIPLE, homogeneous=True, halign=Gtk.Align.START, valign=Gtk.Align.START,
                                 activate_on_single_click=False, column_spacing=4, row_spacing=4, margin_top=10, margin_start=10, max_children_per_line=6, min_children_per_line=1)
        self.flow.connect("child-activated", lambda f, c: open_path(c.path))
        self.root = Gtk.Box(hexpand=True, vexpand=True); self.root.append(self.flow); w.set_child(self.root)
        bg = Gtk.GestureClick(button=3); bg.connect("pressed", self.on_bg_menu); self.root.add_controller(bg)
        bl = Gtk.GestureClick(button=1); bl.connect("pressed", lambda g, n, x, y: self.on_bg_left(x, y)); self.root.add_controller(bl)
        self.build_actions(); self.reload()
        try: self.mon = Gio.File.new_for_path(self.dir).monitor_directory(Gio.FileMonitorFlags.NONE, None); self.mon.connect("changed", lambda *a: GLib.idle_add(self.reload))
        except GLib.Error: pass
        w.present(); w.realize()
        try: w.get_surface().connect("layout", lambda s, wd, ht: self.fit(ht))
        except Exception: pass
        GLib.timeout_add(800, lambda: (self.fit(self.root.get_height()), False)[1])

    # --- lista
    def fit(self, height):
        rows = max(1, (height - 20) // 112)
        if rows != self.flow.get_max_children_per_line(): self.flow.set_max_children_per_line(rows)

    def entries(self):
        out = []
        try: names = [n for n in os.listdir(self.dir) if not n.startswith(".")]
        except OSError: names = []
        for n in names:
            p = os.path.join(self.dir, n)
            try: st = os.stat(p)
            except OSError: continue
            out.append((n, p, os.path.isdir(p), st.st_mtime, st.st_size))
        key = {"name": lambda e: (not e[2], e[0].lower()), "date": lambda e: (not e[2], -e[3]), "size": lambda e: (not e[2], -e[4]), "type": lambda e: (not e[2], os.path.splitext(e[0])[1].lower(), e[0].lower())}[self.sort]
        return sorted(out, key=key)

    def icon_for(self, path):
        if path.endswith(".desktop"):
            ai = Gio.DesktopAppInfo.new_from_filename(path)
            if ai and ai.get_icon(): return ai.get_icon(), ai.get_name()
        try:
            info = Gio.File.new_for_path(path).query_info("standard::icon,standard::display-name", 0, None); return info.get_icon(), info.get_display_name()
        except GLib.Error: return Gio.ThemedIcon.new("text-x-generic"), os.path.basename(path)

    def reload(self):
        while (c := self.flow.get_first_child()) is not None: self.flow.remove(c)
        for n, p, isdir, _m, _s in self.entries():
            icon, label = self.icon_for(p)
            if p.endswith(".desktop") and label: n = label
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, width_request=92)
            box.append(Gtk.Image(gicon=icon, pixel_size=56))
            box.append(Gtk.Label(label=n, wrap=True, wrap_mode=2, lines=2, ellipsize=3, max_width_chars=11, justify=Gtk.Justification.CENTER, css_classes=["desk-name"]))
            child = Gtk.FlowBoxChild(child=box, css_classes=["desk-item"]); child.path = p
            rc = Gtk.GestureClick(button=3); rc.connect("pressed", lambda g, n_, x, y, c=child: self.on_item_menu(c, x, y)); child.add_controller(rc)
            self.flow.append(child)
        return False

    # --- acciones y menús
    def act(self, name, fn, state=None):
        a = Gio.SimpleAction.new(name, None) if state is None else Gio.SimpleAction.new_stateful(name, GLib.VariantType.new("s"), GLib.Variant.new_string(state))
        a.connect("activate" if state is None else "change-state", fn); self.win.add_action(a)

    def build_actions(self):
        self.act("new-folder", lambda *a: self.new_item(True)); self.act("new-text", lambda *a: self.new_item(False))
        self.act("select-all", lambda *a: self.flow.select_all()); self.act("paste", lambda *a: self.paste()); self.act("refresh", lambda *a: self.reload())
        self.act("sort", self.on_sort, self.sort)
        self.act("desk-settings", lambda *a: settings("fondo")); self.act("display-settings", lambda *a: settings("pantalla")); self.act("wallpaper", lambda *a: settings("fondo"))
        self.act("terminal", lambda *a: subprocess.Popen(["foot", "-D", self.dir], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        self.act("open", lambda *a: [open_path(c.path) for c in self.flow.get_selected_children()]); self.act("copy", lambda *a: self.copy(False)); self.act("cut", lambda *a: self.copy(True))
        self.act("rename", lambda *a: self.rename()); self.act("trash", lambda *a: self.trash())

    def bg_model(self):
        m = Gio.Menu(); m.append(_("Nueva carpeta"), "win.new-folder")
        doc = Gio.Menu(); doc.append(_("Documento de texto"), "win.new-text"); m.append_submenu(_("Nuevo documento"), doc)
        s1 = Gio.Menu(); s1.append(_("Seleccionar todo"), "win.select-all"); s1.append(_("Pegar"), "win.paste"); s1.append(_("Actualizar"), "win.refresh"); m.append_section(None, s1)
        srt = Gio.Menu()
        for k, t in (("name", _("Nombre")), ("date", _("Fecha de modificación")), ("size", _("Tamaño")), ("type", _("Tipo"))): srt.append(t, f"win.sort::{k}")
        s2 = Gio.Menu(); s2.append_submenu(_("Ordenar por"), srt); s2.append(_("Configuración del escritorio"), "win.desk-settings"); m.append_section(None, s2)
        s3 = Gio.Menu(); s3.append(_("Abrir en terminal"), "win.terminal"); s3.append(_("Configuración de pantalla"), "win.display-settings"); s3.append(_("Establecer fondo"), "win.wallpaper"); m.append_section(None, s3)
        return m

    def item_model(self):
        m = Gio.Menu(); m.append(_("Abrir"), "win.open")
        s = Gio.Menu(); s.append(_("Copiar"), "win.copy"); s.append(_("Cortar"), "win.cut"); m.append_section(None, s)
        s = Gio.Menu(); s.append(_("Cambiar nombre"), "win.rename"); s.append(_("Mover a la papelera"), "win.trash"); m.append_section(None, s)
        return m

    def popup(self, model, parent, x, y):
        LS.set_keyboard_mode(self.win, LS.KeyboardMode.ON_DEMAND)
        pop = Gtk.PopoverMenu.new_from_model(model); pop.set_parent(parent); pop.set_has_arrow(False); pop.set_halign(Gtk.Align.START)
        r = Gdk.Rectangle(); r.x, r.y, r.width, r.height = int(x), int(y), 1, 1; pop.set_pointing_to(r)
        pop.connect("closed", lambda p: (LS.set_keyboard_mode(self.win, LS.KeyboardMode.NONE), GLib.idle_add(p.unparent)))
        pop.popup()

    def on_bg_menu(self, g, n, x, y): self.flow.unselect_all(); self.popup(self.bg_model(), self.root, x, y)
    def on_bg_left(self, x, y):
        pick = self.flow.get_child_at_pos(int(x - self.flow.get_allocation().x), int(y - self.flow.get_allocation().y)) if hasattr(self.flow, "get_child_at_pos") else None
        if pick is None: self.flow.unselect_all()
    def on_item_menu(self, child, x, y):
        if not child.is_selected(): self.flow.unselect_all(); self.flow.select_child(child)
        self.popup(self.item_model(), child, x, y)
    def on_sort(self, action, value): self.sort = value.get_string(); action.set_state(value); save_sort(self.sort); self.reload()

    # --- operaciones con archivos
    def new_item(self, folder):
        p = unique(self.dir, _("Nueva carpeta") if folder else _("Documento de texto"), "" if folder else ".txt")
        try: os.mkdir(p) if folder else open(p, "w").close()
        except OSError as e: print("[icons]", e, flush=True); return
        self.reload(); GLib.timeout_add(300, lambda: (self.ask_name(p), False)[1])

    def selected(self): return [c.path for c in self.flow.get_selected_children()]

    def ask_name(self, path):
        d = Gtk.Window(title=_("Cambiar nombre"), default_width=380, resizable=False); b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=14, margin_bottom=14, margin_start=14, margin_end=14)
        e = Gtk.Entry(text=os.path.basename(path)); b.append(e); ok = Gtk.Button(label=_("Aceptar"), css_classes=["suggested-action"], halign=Gtk.Align.END); b.append(ok); d.set_child(b)
        def done(*_a):
            new = e.get_text().strip().replace("/", "")
            if new and new != os.path.basename(path):
                dst = os.path.join(self.dir, new)
                if not os.path.exists(dst):
                    try: os.rename(path, dst)
                    except OSError as ex: print("[icons]", ex, flush=True)
            d.close(); self.reload()
        ok.connect("clicked", done); e.connect("activate", done); d.present(); e.grab_focus(); e.select_region(0, len(os.path.splitext(os.path.basename(path))[0]))

    def rename(self):
        s = self.selected()
        if s: self.ask_name(s[0])

    def trash(self):
        for p in self.selected():
            try: Gio.File.new_for_path(p).trash(None)
            except GLib.Error as e: print("[icons] papelera:", e, flush=True)
        self.reload()

    def copy(self, cut):
        files = [Gio.File.new_for_path(p) for p in self.selected()]
        if not files: return
        self.cut = self.selected() if cut else []
        self.win.get_clipboard().set_content(Gdk.ContentProvider.new_typed(Gdk.FileList, Gdk.FileList.new_from_list(files)))

    def paste(self):
        cb = self.win.get_clipboard()
        def got(c, res):
            try: fl = c.read_value_finish(res)
            except GLib.Error: return
            for f in fl.get_files():
                src = f.get_path()
                if not src: continue
                dst = unique(self.dir, os.path.splitext(os.path.basename(src))[0] if os.path.isfile(src) else os.path.basename(src), os.path.splitext(src)[1] if os.path.isfile(src) else "") if os.path.exists(os.path.join(self.dir, os.path.basename(src))) else os.path.join(self.dir, os.path.basename(src))
                try:
                    if src in self.cut: os.rename(src, dst) if os.stat(src).st_dev == os.stat(self.dir).st_dev else subprocess.run(["mv", src, dst])
                    else: subprocess.run(["cp", "-a", src, dst])
                except OSError as e: print("[icons] pegar:", e, flush=True)
            self.cut = []; self.reload()
        cb.read_value_async(Gdk.FileList, GLib.PRIORITY_DEFAULT, None, got)

if __name__ == "__main__": sys.exit(Desk().run([]))
