"""Selector de ventanas (Alt + Tab) y vista de escritorios (Super + Tab) de OweeLinux Lite.
 · Alt + Tab: tarjetas grandes con el icono y el título de cada ventana, en orden de uso reciente. Mantén Alt y pulsa Tab (Mayús + Tab hacia atrás); al soltar Alt entras en la ventana elegida.
   También con flechas + Intro, con el ratón, y Esc cancela. (labwc 0.8 no ofrece capturas de ventanas: por eso iconos y no miniaturas.)
 · Super + Tab: los escritorios en columnas con sus ventanas; clic en una ventana = ir a ella; arrastrarla a otra columna (o los botones numerados de su fila) la pasa a ese escritorio.
labwc 0.8 no dice en qué escritorio está cada ventana: aquí se anota el escritorio en que estaba cuando apareció y el que se le da al moverla (se corrige solo cuando es la ventana activa)."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Gtk4LayerShell as LS
from owee_i18n import _
import owee_desktops


class Registry:
    """Orden de uso reciente (MRU) y escritorio de cada ventana, alimentado por la lista de ventanas del panel."""
    def __init__(self): self.mru = []; self.desk = {}

    def update(self, wins):
        live = [w["handle"] for w in wins]
        self.mru = [h for h in self.mru if h in live]
        cur = owee_desktops.current()
        for h in live:
            if h not in self.mru: self.mru.append(h)
            self.desk.setdefault(h, cur)
        for h in list(self.desk):
            if h not in live: del self.desk[h]
        act = next((w["handle"] for w in wins if w["active"] and not w["minimized"]), None)
        if act is not None:
            if act in self.mru: self.mru.remove(act)
            self.mru.insert(0, act); self.desk[act] = cur           # la ventana activa está en el escritorio actual


def _layer(w, name, exclusive=True, full=False):
    LS.init_for_window(w); LS.set_layer(w, LS.Layer.OVERLAY); LS.set_namespace(w, name)
    LS.set_keyboard_mode(w, LS.KeyboardMode.EXCLUSIVE if exclusive else LS.KeyboardMode.NONE); LS.set_exclusive_zone(w, -1)
    if full:
        for e in (LS.Edge.TOP, LS.Edge.BOTTOM, LS.Edge.LEFT, LS.Edge.RIGHT): LS.set_anchor(w, e, True)


def bring(panel, handle):
    """Lleva a la ventana al frente; si está en otro escritorio, va primero a ese escritorio."""
    watcher = panel.watcher; n = panel.registry.desk.get(handle); cur = owee_desktops.current()
    if n and n != cur:
        owee_desktops.go(n); GLib.timeout_add(300, lambda: (watcher.toggle_front(handle), False)[1])
    else: watcher.toggle_front(handle)


class WindowSwitcher:
    def __init__(self, panel): self.panel = panel; self.win = None; self.items = []; self.idx = 0; self.cards = []; self.done = False

    def step(self, d):
        """d = +1 / -1. Primera llamada: abre el selector; las siguientes (Tab repetido con Alt pulsado) avanzan."""
        if self.win is None: self.open(d)
        else: self.move(d)

    def open(self, d):
        watcher = getattr(self.panel, "watcher", None)
        if not watcher or not getattr(watcher, "ok", False): return
        byh = {w["handle"]: w for w in watcher.windows()}
        self.items = [byh[h] for h in self.panel.registry.mru if h in byh]
        if not self.items: return
        self.idx = (1 if d > 0 else len(self.items) - 1) if len(self.items) > 1 else 0; self.done = False
        w = self.win = Gtk.Window(application=self.panel, decorated=False); w.add_css_class("owee-overview"); w.add_css_class("owee-switcher"); _layer(w, "owee-switcher")
        row = Gtk.Box(spacing=8, margin_top=18, margin_bottom=18, margin_start=18, margin_end=18); self.cards = []
        for i, x in enumerate(self.items):
            img = Gtk.Image(gicon=self.panel.tasks.icon_for(x["app"]), pixel_size=64)
            lab = Gtk.Label(label=x["title"] or x["app"], ellipsize=3, max_width_chars=16, css_classes=["ov-name"])
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, width_request=150); card.add_css_class("ov-card"); card.append(img); card.append(lab)
            if x["minimized"]: card.add_css_class("min")
            g = Gtk.GestureClick(button=1); g.connect("released", lambda *a, i=i: self.pick(i)); card.add_controller(g)
            row.append(card); self.cards.append(card)
        sc = Gtk.ScrolledWindow(child=row, hscrollbar_policy=Gtk.PolicyType.AUTOMATIC, vscrollbar_policy=Gtk.PolicyType.NEVER, propagate_natural_width=True, max_content_width=1100)
        w.set_child(sc)
        k = Gtk.EventControllerKey(); k.connect("key-pressed", self.on_press); k.connect("key-released", self.on_release); k.connect("modifiers", self.on_mods); w.add_controller(k)
        self.mark(); w.present()
        self.polls = 0; GLib.timeout_add(80, self.poll_alt)           # Alt soltado = confirmar (también con un toque rápido: Alt ya suelto al abrirse)

    def poll_alt(self):
        """Mira cada 80 ms si Alt sigue pulsado. Se sondea el estado del teclado y no solo los eventos de tecla: con teclados virtuales (wtype, accesibilidad) la suelta de Alt llega
        como cambio de modificadores sin evento de tecla. Los primeros 240 ms se ignoran para dar tiempo a que el selector reciba el foco y el estado real."""
        if self.win is None or self.done: return False
        self.polls += 1
        if self.polls > 3:
            try:
                st = Gdk.Display.get_default().get_default_seat().get_keyboard().get_modifier_state()
                if not (st & Gdk.ModifierType.ALT_MASK): self.confirm(); return False
            except Exception: pass
        return True

    def mark(self):
        for i, c in enumerate(self.cards): (c.add_css_class if i == self.idx else c.remove_css_class)("sel")

    def move(self, d):
        if not self.items: return
        self.idx = (self.idx + d) % len(self.items); self.mark()

    def pick(self, i): self.idx = i; self.confirm()

    def on_press(self, c, kv, code, st):
        n = Gdk.keyval_name(kv)
        if n == "Escape": self.close(); return True
        if n in ("Tab", "Right", "Down"): self.move(1); return True
        if n in ("ISO_Left_Tab", "Left", "Up"): self.move(-1); return True
        if n in ("Return", "KP_Enter", "space"): self.confirm(); return True
        return False

    def on_release(self, c, kv, code, st):
        if Gdk.keyval_name(kv) in ("Alt_L", "Alt_R", "Meta_L", "Meta_R"): self.confirm()

    def on_mods(self, c, state):
        """Alt soltado (también cuando solo cambian los modificadores, p. ej. con teclados virtuales): confirmar."""
        if self.win is not None and not (state & Gdk.ModifierType.ALT_MASK): self.confirm()
        return False

    def confirm(self):
        if self.done: return
        self.done = True; x = self.items[self.idx] if self.items else None; self.close()
        if x: bring(self.panel, x["handle"])

    def close(self):
        w, self.win = self.win, None
        if w: w.close()


class DesktopsView:
    def __init__(self, panel): self.panel = panel; self.win = None

    def toggle(self):
        if self.win: self.close()
        else: self.open()

    def close(self):
        w, self.win = self.win, None
        if w: w.close()

    def open(self):
        watcher = getattr(self.panel, "watcher", None); n = owee_desktops.desktop_count(); cur = owee_desktops.current()
        w = self.win = Gtk.Window(application=self.panel, decorated=False); w.add_css_class("owee-overview"); _layer(w, "owee-desktops", full=True)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, margin_top=80, margin_bottom=40, margin_start=40, margin_end=40)
        outer.append(Gtk.Label(label=_("Escritorios — arrastra una ventana a otro escritorio"), css_classes=["ov-head"]))
        cols = Gtk.Box(spacing=14, homogeneous=True, vexpand=True); outer.append(cols); self.ids = {}
        wins = watcher.windows() if watcher and getattr(watcher, "ok", False) else []
        for k in range(1, n + 1):
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); col.add_css_class("dv-col")
            if k == cur: col.add_css_class("dv-cur")
            head = Gtk.Button(label=_('Escritorio {0}', k), has_frame=False); head.add_css_class("dv-head"); head.connect("clicked", lambda _b, k=k: (self.close(), owee_desktops.go(k))); col.append(head)
            mine = [x for x in wins if self.panel.registry.desk.get(x["handle"], cur) == k]
            if not mine: col.append(Gtk.Label(label=_("(vacío)"), css_classes=["dim-label"], vexpand=True, valign=Gtk.Align.START))
            for x in mine: col.append(self.row(x, k, n))
            dt = Gtk.DropTarget.new(str, Gdk.DragAction.MOVE); dt.connect("drop", self.on_drop, k); col.add_controller(dt)
            cols.append(col)
        w.set_child(outer)
        key = Gtk.EventControllerKey(); key.connect("key-pressed", lambda c, kv, kc, st: (self.close(), True)[1] if kv == Gdk.KEY_Escape else False); w.add_controller(key)
        bg = Gtk.GestureClick(button=1); bg.connect("released", lambda g, nn, x, y: self.bg_click(outer, x, y)); w.add_controller(bg)
        w.present()

    def bg_click(self, outer, x, y):
        pick = self.win.pick(x, y, Gtk.PickFlags.DEFAULT) if self.win else None
        if pick is self.win or pick is outer: self.close()

    def row(self, x, k, n):
        """Una ventana: icono + título (clic = ir a ella) y botones numerados para pasarla a otro escritorio; también se puede arrastrar."""
        h = x["handle"]; sid = str(id(h)); self.ids[sid] = h
        box = Gtk.Box(spacing=8); box.add_css_class("ov-card")
        box.append(Gtk.Image(gicon=self.panel.tasks.icon_for(x["app"]), pixel_size=28))
        lab = Gtk.Label(label=x["title"] or x["app"], ellipsize=3, xalign=0, hexpand=True, max_width_chars=22, css_classes=["ov-name"]); box.append(lab)
        for j in range(1, n + 1):
            if j == k: continue
            b = Gtk.Button(label=str(j), has_frame=False, tooltip_text=_('Pasar a escritorio {0}', j)); b.add_css_class("dv-move"); b.connect("clicked", lambda _b, h=h, j=j: self.move_to(h, j)); box.append(b)
        g = Gtk.GestureClick(button=1); g.connect("released", lambda *a, h=h: (self.close(), bring(self.panel, h))); lab.add_controller(g)
        src = Gtk.DragSource(actions=Gdk.DragAction.MOVE); src.connect("prepare", lambda s, px, py, sid=sid: Gdk.ContentProvider.new_for_value(sid)); box.add_controller(src)
        return box

    def on_drop(self, target, value, x, y, k):
        h = self.ids.get(value)
        if h is not None and self.panel.registry.desk.get(h) != k: self.move_to(h, k)
        return h is not None

    def move_to(self, handle, k):
        """Activa la ventana y pulsa Super + Ctrl + F<k> (atajo de rc.xml: SendToDesktop). Anota el escritorio nuevo."""
        self.close(); watcher = self.panel.watcher; self.panel.registry.desk[handle] = k
        bring_first = lambda: (watcher.toggle_front(handle), False)[1]
        bring_first(); GLib.timeout_add(250, lambda: (owee_desktops.press(f"F{k}", mods=("logo", "ctrl")), False)[1])
