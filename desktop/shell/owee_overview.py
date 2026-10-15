"""Vista general de OweeLinux: una capa a pantalla completa con las VENTANAS abiertas (tarjetas con icono y título; las minimizadas, atenuadas) y debajo todas las APLICACIONES en una
cuadrícula, con un buscador que filtra ambas. Se abre desde las esquinas activas («Vista general»), con el atajo Super + A o desde el panel. Clic en una ventana: la trae al frente (y la restaura si estaba
minimizada); clic en una aplicación: la abre; clic central en una ventana: la cierra; Esc o un clic fuera: cierra la vista general. No necesita capturas de las ventanas (labwc 0.8 no las ofrece)."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Gtk4LayerShell as LS
from owee_i18n import _

class Overview:
    def __init__(self, panel):
        self.panel = panel; self.win = None

    def toggle(self):
        if self.win: self.close()
        else: self.open()

    def close(self):
        if self.win: self.win.close(); self.win = None

    def open(self):
        w = self.win = Gtk.Window(application=self.panel, decorated=False); w.add_css_class("owee-overview")
        LS.init_for_window(w); LS.set_layer(w, LS.Layer.OVERLAY); LS.set_namespace(w, "owee-overview"); LS.set_keyboard_mode(w, LS.KeyboardMode.EXCLUSIVE)
        for e in (LS.Edge.TOP, LS.Edge.BOTTOM, LS.Edge.LEFT, LS.Edge.RIGHT): LS.set_anchor(w, e, True)
        LS.set_exclusive_zone(w, -1)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, halign=Gtk.Align.CENTER, margin_top=70, margin_bottom=40, width_request=900)
        self.entry = Gtk.SearchEntry(placeholder_text=_("Buscar aplicación…"), width_request=420, halign=Gtk.Align.CENTER); outer.append(self.entry)
        self.entry.connect("search-changed", lambda e: self.refresh())
        self.wins_l = Gtk.Label(label=_("Ventanas abiertas"), xalign=0, css_classes=["ov-head"]); outer.append(self.wins_l)
        self.wins = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=6, min_children_per_line=2, homogeneous=True, column_spacing=10, row_spacing=10, activate_on_single_click=True); outer.append(self.wins)
        outer.append(Gtk.Label(label=_("Aplicaciones"), xalign=0, css_classes=["ov-head"]))
        self.apps = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=8, min_children_per_line=3, homogeneous=True, column_spacing=6, row_spacing=6, activate_on_single_click=True)
        sc = Gtk.ScrolledWindow(child=self.apps, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER, min_content_height=260); outer.append(sc)
        w.set_child(outer)
        k = Gtk.EventControllerKey(); k.connect("key-pressed", lambda c, kv, kc, st: (self.close(), True)[1] if kv == Gdk.KEY_Escape else False); w.add_controller(k)
        bg = Gtk.GestureClick(button=1); bg.connect("released", self.bg_click); w.add_controller(bg)
        self.outer = outer; self.all_apps = self.panel.launcher.scan(); self.refresh(); w.present(); self.entry.grab_focus()

    def bg_click(self, gesture, n, x, y):
        pick = self.win.pick(x, y, Gtk.PickFlags.DEFAULT) if self.win else None
        if pick is self.win or pick is self.outer or (pick is not None and pick.get_parent() is self.win): self.close()

    def refresh(self):
        q = self.entry.get_text().strip().lower()
        for fb in (self.wins, self.apps):
            while (c := fb.get_first_child()): fb.remove(c)
        watcher = getattr(self.panel, "watcher", None); ws = watcher.windows() if watcher and getattr(watcher, "ok", False) else []
        ws = [x for x in ws if not q or q in (x["title"] + " " + x["app"]).lower()]
        self.wins_l.set_visible(bool(ws)); self.wins.set_visible(bool(ws))
        for x in ws:
            img = Gtk.Image(gicon=self.panel.tasks.icon_for(x["app"]), pixel_size=44); lab = Gtk.Label(label=x["title"] or x["app"], ellipsize=3, max_width_chars=18, css_classes=["ov-name"])
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); card.add_css_class("ov-card"); card.append(img); card.append(lab)
            if x["minimized"]: card.add_css_class("min")
            if x["active"] and not x["minimized"]: card.add_css_class("act")
            b = Gtk.Button(child=card, has_frame=False); b.add_css_class("ov-btn"); b.connect("clicked", lambda _b, h=x["handle"]: (self.close(), watcher.toggle_front(h)))
            mid = Gtk.GestureClick(button=2); mid.connect("released", lambda *a, h=x["handle"]: (watcher.close(h), GLib.timeout_add(300, lambda: (self.refresh(), False)[1]))); b.add_controller(mid); self.wins.append(b)
        for a in self.all_apps:
            if q and q not in (a.get_name() + " " + (a.get_generic_name() or "") + " " + (a.get_keywords() and " ".join(a.get_keywords()) or "")).lower(): continue
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); card.add_css_class("ov-card"); card.append(Gtk.Image(gicon=a.get_icon() or Gio.ThemedIcon.new("application-x-executable"), pixel_size=52))
            card.append(Gtk.Label(label=a.get_name(), ellipsize=3, max_width_chars=14, css_classes=["ov-name"]))
            b = Gtk.Button(child=card, has_frame=False); b.add_css_class("ov-btn"); b.connect("clicked", lambda _b, ap=a: (self.close(), self.panel.launcher.launch(ap))); self.apps.append(b)
