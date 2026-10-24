#!/usr/bin/env python3
"""Panel superior de OweeLinux Lite — PROTOTIPO de riesgos (v0.0): Python + GTK4 + gtk4-layer-shell.
Muestra: lanzador de aplicaciones (búsqueda), reloj y fecha centrados y los WIDGETS (scripts: volumen, red, batería, los del usuario...).
Regla de diseño (docs/ESCRITORIO.md): llamadas D-Bus asíncronas; el panel nunca se bloquea esperando a un servicio.
Al arrancar escribe en $XDG_RUNTIME_DIR/owee-panel.log su memoria (Rss/Pss) para medirla."""
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import owee_config, owee_i18n
from gi.repository import Gtk, Gtk4LayerShell as LS, GLib, Gdk, Gio
os.environ.pop("LD_PRELOAD", None)          # la capa de paneles ya está cargada en ESTE proceso; los programas que lance (terminales, cajas de desarrollo…) no deben heredarla: en otros entornos no existe y escribía un error en cada comando
from owee_i18n import _
import owee_i18n as _i18n; _i18n.apply_direction()
import owee_keys
CSS_TEMPLATE = """
window.owee-panel { background: @bg@; color: @fg@; border-radius: 12px; }
button.owee-task { padding: 2px 6px; border-radius: 8px; min-height: 0; min-width: 0; background: transparent; background-image: none; border: none; box-shadow: none; } button.owee-task image { opacity: 1; } button.owee-task.min image { opacity: .4; }
button.owee-task:hover, button.owee-task.act { background: @hover@; }
.owee-rec label { color: #F06548; padding: 0 6px; font-weight: bold; } .owee-rec button { background: transparent; background-image: none; border: none; box-shadow: none; padding: 0 6px; min-height: 0; min-width: 0; color: @fg@; } .owee-rec button:hover { background: @hover@; }
window.owee-overview { background: alpha(@win@, 0.94); color: @fg@; } .ov-head { font-weight: bold; color: @dim@; margin-top: 10px; }
.ov-card { padding: 10px 6px; border-radius: 14px; } .ov-btn:hover .ov-card { background: @hover@; } .ov-card.act { background: alpha(@fg@, 0.10); } .ov-card.min image { opacity: .4; } .ov-name { color: @fg@; font-size: 10pt; }
.ov-card.sel { background: alpha(@fg@, 0.22); } .dv-col { padding: 10px; border-radius: 14px; background: alpha(@fg@, 0.05); } .dv-col.dv-cur { background: alpha(@fg@, 0.10); } .dv-head { font-weight: bold; } button.dv-move { padding: 0 6px; min-height: 0; min-width: 0; border-radius: 6px; background: alpha(@fg@, 0.10); background-image: none; box-shadow: none; border: none; color: @fg@; } button.dv-move:hover { background: @hover@; }
window.owee-overview button.ov-btn { background: transparent; background-image: none; border: none; box-shadow: none; }
label.task-count { font-size: 7pt; font-weight: bold; background: @accent@; color: @on@; border-radius: 999px; padding: 0 4px; min-width: 8px; }
window.owee-panel.vertical label { padding: 0; font-size: 8pt; }
window.owee-panel.vertical menubutton.launcher > button { padding: 2px 0; margin: 3px 2px; }
window.owee-panel.vertical button.owee-desk { padding: 1px 0; min-width: 22px; }
window.owee-panel.vertical button.owee-task { padding: 2px 2px; }
window.owee-panel.vertical button.owee-tray { padding: 2px 1px; }
window.owee-panel.vertical menubutton.owee-widget > button { padding: 0; }
window.owee-panel.compact { border-radius: 0; background: @win@; border-bottom: 1px solid @line@; }
.owee-panel label { padding: 0 10px; }
.owee-panel label.warn { color: #F06548; }
menubutton.owee-widget > button, menubutton.owee-widget > button label { background: transparent; background-image: none; color: @fg@; border: none; box-shadow: none; padding: 0 2px; min-height: 0; }
menubutton.owee-widget > button:hover, menubutton.owee-widget > button:checked { background: @hover@; background-image: none; }
popover > contents { background: @pop@; color: @fg@; border: 1px solid @accent@; border-radius: 12px; }
label.clock-big { font-size: 26pt; font-weight: bold; padding: 0; }
popover label.clock-big { color: @fg@; }
popover label.heading { color: @accent@; font-weight: bold; }
popover button { background: @accent@; color: @on@; border: none; border-radius: 8px; box-shadow: none; }
popover passwordentry, popover text { background: @entry@; color: @fg@; } popover passwordentry { border: 1px solid @line@; border-radius: 8px; padding: 2px 6px; }
popover scale trough { background: @line@; } popover scale highlight { background: @accent@; } popover scale slider { background: @fg@; }
popover calendar { background: transparent; color: @fg@; border-color: @line@; }
popover calendar:selected, popover calendar label:selected, popover calendar .day-number:selected { background: @accent@; color: @on@; border-radius: 6px; }
popover calendar.view, popover calendar button { color: @fg@; background: transparent; }
button.owee-desk { background: transparent; background-image: none; border: none; box-shadow: none; color: @fg@; opacity: 0.55; min-width: 0; min-height: 0; padding: 1px 7px; border-radius: 999px; }
button.owee-desk:hover { opacity: 1; background: @hover@; }
button.owee-desk.on { opacity: 1; background: @accent@; color: @on@; font-weight: bold; }
window.owee-corner, window.owee-corner > box { background: rgba(0,0,0,0.01); }
button.owee-tray { background: transparent; background-image: none; border: none; box-shadow: none; padding: 2px 4px; min-height: 0; min-width: 0; }
button.owee-tray:hover { background: @hover@; }
button.owee-row { background: transparent; background-image: none; color: @fg@; border: none; box-shadow: none; border-radius: 8px; padding: 6px 10px; min-width: 200px; }
button.owee-row:hover { background: @hover@; }
button.owee-row label.warn { color: #F06548; padding: 0; }
menubutton.launcher > button { background: @accent@; background-image: none; color: @on@; border: none; box-shadow: none; border-radius: 8px; padding: 2px 12px; margin: 3px 4px; min-height: 0; }
popover entry { background: @entry@; color: @fg@; border: 1px solid @line@; border-radius: 8px; box-shadow: none; }
popover list, popover row { background: transparent; color: @fg@; }
popover row { border-radius: 8px; padding: 4px 6px; } popover row:hover, popover row:selected { background: @hover@; }
"""

def css_for(pal):
    s = CSS_TEMPLATE
    for k, v in pal.items(): s = s.replace("@%s@" % k, v)
    return s.encode()

def mem(tag):
    d = {}
    try:
        for l in open("/proc/self/smaps_rollup"):
            k, _x, v = l.partition(":")
            if k in ("Rss", "Pss"): d[k] = int(v.split()[0]) / 1024
    except OSError: return
    print(f"[mem] {tag}: Rss={d.get('Rss',0):.0f} MB Pss={d.get('Pss',0):.0f} MB", flush=True)

WIDGET_DIRS = ["/usr/share/owee/widgets", os.path.expanduser("~/.config/owee/widgets")]

VERT = False                                                           # panel lateral: los textos de los widgets pasan a varias líneas (así el panel es delgado)

class ScriptWidget:
    """Widget hecho con un script en CUALQUIER lenguaje (Python, JavaScript/GJS, shell...): ejecutable que imprime una línea
    JSON. Campos (todos opcionales salvo "text"):
      "text", "tooltip", "class"
      "on_click": ["comando", "arg"...]            se ejecuta al hacer clic y el widget se actualiza
      "popup": {"title": "...", "items": [...]}    ventanita que se abre al hacer clic; items:
          {"type":"label","text":"..."} · {"type":"button","text":"...","command":[...]} ·
          {"type":"slider","min":0,"max":100,"value":50,"command":[...]}  (se llama con el valor como último argumento) ·
          {"type":"calendar"} · {"type":"separator"} ·
          {"type":"entry","placeholder":"...","password":true,"command":[...]}  (al pulsar Intro se llama al comando con el texto como último argumento)
    Se ejecuta de forma asíncrona cada N segundos (comentario `owee-interval: N`), con límite de 5 s (`timeout` mata también
    a los procesos hijos); un fallo no afecta al panel (se muestra "⚠ nombre")."""
    def __init__(self, path, box):
        self.path, self.name = path, os.path.splitext(os.path.basename(path))[0]
        self.data = {}; self.pending = None
        self.label = Gtk.Label(label=self.name + "…"); self.icon = Gtk.Image(pixel_size=18); self.icon.set_visible(False)
        inner = Gtk.Box(spacing=0); inner.append(self.icon); inner.append(self.label)
        self.btn = Gtk.MenuButton(has_frame=False, child=inner); self.btn.add_css_class("owee-widget"); self.btn.set_visible(False)   # visible al llegar el primer dato
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

    def retext(self):
        """Vuelve a poner el texto con el formato del panel actual (en columna si es lateral) sin esperar al siguiente ciclo del widget."""
        t = str(self.data.get("text", ""))
        if t: self.label.set_text(t.replace(" ", "\n") if VERT else t)

    def done(self, p, res):
        try:
            ok, out, _x = p.communicate_utf8_finish(res); d = json.loads(out.strip().splitlines()[-1]); self.data = d
            self.btn.set_visible(not d.get("hidden")); 
            if d.get("hidden"): return
            self.label.set_text(str(d.get("text", "")).replace(" ", "\n") if VERT else str(d.get("text", ""))); self.label.set_visible(bool(d.get("text"))); self.btn.set_tooltip_text(d.get("tooltip"))
            if d.get("icon"): self.icon.set_from_icon_name(d["icon"]); self.icon.set_visible(True)
            else: self.icon.set_visible(False)
            self.label.remove_css_class("warn")
            if d.get("class"): self.label.add_css_class(d["class"])
            has = bool(d.get("popup"))                      # reasignar la ventanita en cada refresco la CERRABA (bug visto con refrescos de 3 s)
            if has != getattr(self, "has_popup", None): self.has_popup = has; self.btn.set_popover(self.pop if has else None)
        except Exception as e:
            self.btn.set_visible(True); self.label.set_visible(True); self.icon.set_visible(False); self.label.set_text("⚠ " + self.name); self.label.set_tooltip_text(_("el widget falló: %s") % e)

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
            if t == "label": box.append(Gtk.Label(label=it.get("text", ""), xalign=0, css_classes=[it["class"]] if it.get("class") else []))
            elif t == "entry":                                           # campo de texto (p. ej. contraseña de WiFi): al pulsar Intro se llama al comando con el texto como último argumento
                e = Gtk.PasswordEntry(placeholder_text=it.get("placeholder", ""), show_peek_icon=True) if it.get("password") else Gtk.Entry(placeholder_text=it.get("placeholder", ""))
                e.connect("activate", lambda w, c=it.get("command", []): (self.act(c, [w.get_text()]), self.pop.popdown())); e.set_size_request(260, -1); box.append(e)
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

class TaskBar:
    """Barra de ventanas del panel: un icono por ventana abierta (también las minimizadas, atenuadas). Clic: restaura / trae al frente / minimiza; clic central: cierra.
    Los datos vienen de wlr-foreign-toplevel (owee_windows.WindowWatcher); si el protocolo no está, queda vacía."""
    MAX = 12
    def __init__(self, watcher_get):
        self.box = Gtk.Box(spacing=2); self.box.add_css_class("owee-tasks"); self.get = watcher_get

    classes = None
    @classmethod
    def by_class(cls, app):
        """Icono del lanzador cuyo StartupWMClass (o identificador) coincide con el app_id de la ventana; se recorre una vez y se guarda (se renueva si no aparece)."""
        if cls.classes is None or app.lower() not in cls.classes:
            cls.classes = {}
            for ai in Gio.AppInfo.get_all():
                try:
                    c = (ai.get_startup_wm_class() or "").lower(); i = ai.get_id() or ""
                    if c: cls.classes.setdefault(c, ai.get_icon())
                    cls.classes.setdefault(i.lower().removesuffix(".desktop"), ai.get_icon())
                except Exception: pass
        return cls.classes.get(app.lower())

    @staticmethod
    def icon_for(app):
        """Icono del lanzador (.desktop) de esa app; si no, el icono con el mismo nombre; si no, uno genérico."""
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        ic = TaskBar.by_class(app)
        if ic: return ic
        for cand in (app, app.lower(), app.split(".")[-1].lower()):
            if not cand: continue
            for n in (cand + ".desktop",):
                try:
                    ai = Gio.DesktopAppInfo.new(n)
                    if ai and ai.get_icon(): return ai.get_icon()
                except Exception: pass
            if theme.has_icon(cand): return Gio.ThemedIcon.new(cand)
        return Gio.ThemedIcon.new("application-x-executable")

    pos = "top"                                                                            # lo fija el panel (apply_layout): hacia dónde se abre la lista de un grupo

    def update(self, wins):
        while (c := self.box.get_first_child()):
            if getattr(c, "pop", None): c.pop.unparent()
            self.box.remove(c)
        groups = {}
        for w in wins: groups.setdefault(w["app"], []).append(w)                         # una sola entrada por aplicación (con varias ventanas: contador y lista)
        for app, ws in list(groups.items())[:self.MAX]:
            if len(ws) == 1: self.single(ws[0])
            else: self.group(app, ws)

    def single(self, w):
        img = Gtk.Image(gicon=self.icon_for(w["app"]), pixel_size=18); b = Gtk.Button(child=img, has_frame=False, tooltip_text=w["title"] or w["app"])
        b.add_css_class("owee-task")
        if w["minimized"]: b.add_css_class("min")
        if w["active"] and not w["minimized"]: b.add_css_class("act")
        b.connect("clicked", lambda _b, h=w["handle"]: self.get().toggle(h))
        mid = Gtk.GestureClick(button=2); mid.connect("released", lambda *a, h=w["handle"]: self.get().close(h)); b.add_controller(mid)
        self.box.append(b)

    def group(self, app, ws):
        """Varias ventanas de la misma aplicación: un solo icono con el número de ventanas; al pulsarlo se abre la lista para elegir una (así el panel no se llena ni el reloj se desplaza)."""
        ov = Gtk.Overlay(child=Gtk.Image(gicon=self.icon_for(app), pixel_size=18))
        ov.add_overlay(Gtk.Label(label=str(len(ws)), css_classes=["task-count"], halign=Gtk.Align.END, valign=Gtk.Align.END))
        b = Gtk.Button(child=ov, has_frame=False, tooltip_text=f"{ws[0]['title'] or app} ({len(ws)})"); b.add_css_class("owee-task")
        if all(w["minimized"] for w in ws): b.add_css_class("min")
        if any(w["active"] and not w["minimized"] for w in ws): b.add_css_class("act")
        pop = Gtk.Popover(); pop.set_parent(b); b.pop = pop
        pop.set_position({"top": Gtk.PositionType.BOTTOM, "bottom": Gtk.PositionType.TOP, "left": Gtk.PositionType.RIGHT, "right": Gtk.PositionType.LEFT}.get(self.pos, Gtk.PositionType.BOTTOM))
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, margin_top=6, margin_bottom=6, margin_start=6, margin_end=6)
        for w in ws:
            lab = Gtk.Label(label=(w["title"] or app) + ("  ⌄" if w["minimized"] else ""), xalign=0, ellipsize=3, max_width_chars=34)
            r = Gtk.Button(child=lab, has_frame=False, css_classes=["owee-row"]); r.connect("clicked", lambda _b, h=w["handle"], p=pop: (p.popdown(), self.get().toggle(h)))
            mid = Gtk.GestureClick(button=2); mid.connect("released", lambda *a, h=w["handle"]: self.get().close(h)); r.add_controller(mid); col.append(r)
        pop.set_child(col); b.connect("clicked", lambda _b, p=pop: p.popup())
        self.box.append(b)

class RecIndicator:
    """Controles de la grabación de pantalla DENTRO del panel (tiempo, dibujar, cámara, detener): así no flotan sobre la pantalla ni salen en el vídeo. La Capturadora escribe la hora de inicio en
    $XDG_RUNTIME_DIR/owee-recording mientras graba y acepta las acciones stop / present / camera (`gapplication action org.oweelinux.Capture …`). Sin grabación, no se ve."""
    STATE = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "owee-recording")
    def __init__(self):
        self.box = Gtk.Box(spacing=0); self.box.add_css_class("owee-rec"); self.box.set_visible(False)
        self.lab = Gtk.Label(label="●  00:00"); self.box.append(self.lab)
        for sym, act, tip in (("✎", "present", _("Modo presentación (dibujar)")), ("📷", "camera", _("Mostrar u ocultar la cámara")), ("■", "stop", _("■ Detener"))):
            b = Gtk.Button(label=sym, tooltip_text=tip); b.connect("clicked", lambda _b, a=act: self.act(a)); self.box.append(b)
        self.src = 0; self.check()
        try:                                                         # se vigila el archivo de estado en vez de leerlo cada segundo: sin grabación, ningún despertar
            self.mon = Gio.File.new_for_path(os.path.dirname(self.STATE)).monitor_directory(Gio.FileMonitorFlags.NONE, None)
            self.mon.connect("changed", lambda m, f, o, ev: f.get_basename() == "owee-recording" and GLib.idle_add(lambda: (self.check(), False)[1]))
        except GLib.Error: GLib.timeout_add_seconds(3, lambda: (self.check(), True)[1])

    def check(self):
        if os.path.exists(self.STATE) and not self.src: self.src = GLib.timeout_add_seconds(1, self.tick)
        self.tick()

    @staticmethod
    def alive():
        for d in os.listdir("/proc"):
            if d.isdigit():
                try:
                    if open(f"/proc/{d}/comm").read().strip() == "wf-recorder": return True
                except OSError: pass
        return False

    def act(self, name):
        try: Gio.Subprocess.new(["gapplication", "action", "org.oweelinux.Capture", name], Gio.SubprocessFlags.STDERR_SILENCE)
        except GLib.Error: pass

    def tick(self):
        try: t0 = int(open(self.STATE).read().strip())
        except (OSError, ValueError): self.box.set_visible(False); self.src = 0; return False
        self.n = getattr(self, "n", 0) + 1
        if self.n % 5 == 0 and not self.alive():                      # la grabación terminó sin avisar (la Capturadora falló): se quita el aviso para que no quede un «detener» que no hace nada
            try: os.remove(self.STATE)
            except OSError: pass
            self.box.set_visible(False); self.src = 0; return False
        s = max(0, int(time.time()) - t0); self.lab.set_text(f"●  {s // 60:02d}:{s % 60:02d}"); self.box.set_visible(True); return True

class Reminders:
    """Avisos del Calendario: cada 20 s mira ~/.local/share/owee/calendar.json (solo lo relee si cambió) y, a la hora de un evento de hoy, lanza una notificación (una sola vez por evento)."""
    DATA = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "owee", "calendar.json")
    def __init__(self):
        self.mtime = None; self.ev = {}; self.done = set(); GLib.timeout_add_seconds(20, self.tick)

    ALERT = "/run/owee-centinela/alert"
    def sentinel(self):
        """Aviso de Centinela (señuelo de red): si hay una alerta nueva, notificación. Solo mira la fecha de un archivo (cada 20 s, junto a los avisos del calendario)."""
        try: m = os.stat(self.ALERT).st_mtime
        except OSError: return
        first = getattr(self, "amtime", None) is None
        if m == getattr(self, "amtime", None): return
        self.amtime = m
        if first and time.time() - m > 120: return                       # alerta anterior a este arranque del panel
        try: a = json.load(open(self.ALERT))
        except (OSError, ValueError): return
        txt = _('Alguien está escaneando tu equipo desde {0} (puertos {1}).', str(a.get("ip", "?"))[:45], ", ".join(str(x) for x in a.get("ports", [])[:6])) + " " + (_("Lo bloqueé.") if a.get("blocked") else _("Quedó anotado."))
        try: Gio.Subprocess.new(["notify-send", "-u", "critical", "-a", "Centinela", "-i", "security-low", _("Centinela"), txt], Gio.SubprocessFlags.NONE)
        except GLib.Error: pass

    def tick(self):
        self.sentinel()
        try:
            m = os.stat(self.DATA).st_mtime
            if m != self.mtime: self.mtime = m; self.ev = json.load(open(self.DATA, encoding="utf-8"))
        except (OSError, ValueError): self.ev = {}; self.mtime = None
        now = time.localtime(); day = time.strftime("%Y-%m-%d", now); hm = time.strftime("%H:%M", now)
        for e in (self.ev.get(day, []) if isinstance(self.ev, dict) else []):
            key = (day, e.get("t"), e.get("title"))
            if e.get("t") == hm and key not in self.done:
                self.done.add(key)
                try: Gio.Subprocess.new(["notify-send", "-a", _("Calendario"), "-i", "owee-calendar", hm, str(e.get("title", ""))[:200]], Gio.SubprocessFlags.NONE)
                except GLib.Error: pass
        return True

class Clipboard:
    """Historial del portapapeles en el panel: guarda en MEMORIA (nunca en disco) los últimos textos copiados (los observa `wl-paste --watch`) y deja volver a copiar uno con un clic.
    Sin `wl-paste` (wl-clipboard) el botón no aparece. «Borrar historial» lo vacía."""
    MAX = 25
    def __init__(self):
        self.items = []; self.btn = Gtk.MenuButton(has_frame=False, child=Gtk.Image(icon_name="owee-clipboard", pixel_size=18), tooltip_text=_("Portapapeles")); self.btn.add_css_class("owee-widget")
        self.pop = Gtk.Popover(); self.btn.set_popover(self.pop); self.pop.connect("notify::visible", lambda p, _x: p.get_visible() and self.build())
        if not GLib.find_program_in_path("wl-paste"): self.btn.set_visible(False); return
        try:
            self.proc = Gio.Subprocess.new(["wl-paste", "--type", "text", "--watch", "sh", "-c", "cat; printf '\\036'"], Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE)
            self.stream = Gio.DataInputStream.new(self.proc.get_stdout_pipe()); self.read()
        except GLib.Error as e: print("[portapapeles] desactivado:", e, flush=True); self.btn.set_visible(False)

    def read(self):
        self.stream.read_upto_async("\x1e", 1, GLib.PRIORITY_DEFAULT, None, self.got)

    def got(self, stream, res):
        try: text, _n = stream.read_upto_finish(res); stream.read_byte(None)           # consume el separador (RS, 0x1e: no puede ser NUL porque PyGObject no pasa NUL en cadenas)
        except GLib.Error: return
        if text is not None:
            t = text.strip("\n")
            if t.strip():
                t = t[:4000]
                if t in self.items: self.items.remove(t)
                self.items.insert(0, t); del self.items[self.MAX:]
        self.read()

    def build(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, margin_top=6, margin_bottom=6, margin_start=6, margin_end=6, width_request=320)
        box.append(Gtk.Label(label=_("Portapapeles"), xalign=0, css_classes=["heading"], margin_start=6, margin_bottom=2))
        if not self.items: box.append(Gtk.Label(label=_("El portapapeles está vacío"), xalign=0, css_classes=["dim-label"], margin_start=6, margin_top=4, margin_bottom=4))
        for t in self.items[:12]:
            one = " ⏎ ".join(t.split("\n"))[:70] + ("…" if len(t) > 70 or "\n" in t else "")
            b = Gtk.Button(child=Gtk.Label(label=one, xalign=0, ellipsize=3, max_width_chars=44), has_frame=False, tooltip_text=t[:300]); b.add_css_class("owee-row"); b.connect("clicked", lambda _b, x=t: self.paste(x)); box.append(b)
        if self.items:
            box.append(Gtk.Separator(margin_top=4, margin_bottom=4)); clr = Gtk.Button(label=_("Borrar historial"), has_frame=False); clr.add_css_class("owee-row"); clr.connect("clicked", lambda _b: (self.items.clear(), self.pop.popdown())); box.append(clr)
        self.pop.set_child(box)

    def paste(self, text):
        self.pop.popdown(); Gdk.Display.get_default().get_clipboard().set(text)

class Launcher:
    """Lanzador de aplicaciones: botón del panel con ventanita de búsqueda + lista de las apps instaladas (archivos .desktop).
    La lista se construye al ABRIR por primera vez (no al arrancar): no cuesta memoria ni tiempo de sesión si no se usa.
    Escribir filtra; Intro lanza la primera coincidencia; Esc cierra."""
    def __init__(self):
        inner = Gtk.Box(spacing=6); inner.append(Gtk.Image(icon_name="owee-logo", pixel_size=22)); self.name = Gtk.Label(label=_("OweeLinux")); inner.append(self.name)
        self.btn = Gtk.MenuButton(child=inner, has_frame=False); self.btn.add_css_class("launcher")
        self.pop = Gtk.Popover(); self.btn.set_popover(self.pop); self.pop.connect("notify::visible", self.toggled); self.built = False; self.stale = False
        self.sig = None

    @staticmethod
    def app_dirs():
        """Carpetas de lanzadores (.desktop): la del usuario y las de XDG_DATA_DIRS (incluye las de Flatpak). Existan o no todavía."""
        home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        dirs = [home] + [d for d in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if d]
        out = []
        for d in dirs:
            a = os.path.join(d, "applications")
            if a not in out: out.append(a)
        return out

    def signature(self):
        """«Huella» barata de las carpetas (fecha de modificación): cambia cuando se instala o quita una app, incluso si la carpeta no existía al arrancar el panel."""
        sig = []
        for d in self.app_dirs():
            try: sig.append(os.stat(d).st_mtime_ns)
            except OSError: sig.append(0)
        return tuple(sig)

    def scan(self):
        """Lista de apps leída directamente de los .desktop (no de la caché de GLib, que puede quedarse desactualizada si una carpeta se crea después de arrancar)."""
        seen, apps = set(), []
        for d in self.app_dirs():
            try: names = sorted(os.listdir(d))
            except OSError: continue
            for n in names:
                if not n.endswith(".desktop") or n in seen: continue
                seen.add(n)
                try: a = Gio.DesktopAppInfo.new_from_filename(os.path.join(d, n))
                except Exception: a = None
                if a and a.should_show(): apps.append(a)
        return sorted(apps, key=lambda a: a.get_name().lower())

    def toggled(self, pop, _):
        if not pop.get_visible(): return
        sig = self.signature()
        if not self.built or sig != self.sig: self.build(); self.sig = sig
        self.entry.set_text(""); self.list.invalidate_filter(); self.entry.grab_focus()

    def build(self):
        self.built = True
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        self.entry = Gtk.SearchEntry(placeholder_text=_("Buscar aplicación…")); box.append(self.entry)
        self.list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, activate_on_single_click=True)
        self.list.set_filter_func(self.visible_row); self.list.connect("row-activated", lambda l, r: self.launch(r.app))
        for a in self.scan():
            row = Gtk.ListBoxRow(); row.app = a; row.key = (a.get_name() + " " + (a.get_generic_name() or "") + " " + (a.get_keywords() and " ".join(a.get_keywords()) or "")).lower()
            h = Gtk.Box(spacing=10)
            img = Gtk.Image.new_from_gicon(a.get_icon()) if a.get_icon() else Gtk.Image(); img.set_pixel_size(24)
            h.append(img); h.append(Gtk.Label(label=a.get_name(), xalign=0)); row.set_child(h); self.list.append(row)
        sw = self.sw = Gtk.ScrolledWindow(min_content_height=320, min_content_width=300, child=self.list); box.append(sw)
        self.entry.connect("search-changed", lambda e: (self.list.invalidate_filter(), self.select_first()))
        self.entry.connect("activate", lambda e: self.activate_selected())
        kc = Gtk.EventControllerKey(); kc.connect("key-pressed", self.on_key); self.entry.add_controller(kc)          # ↑/↓ recorren la lista sin salir del buscador; Esc cierra
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
    def activate_selected(self):
        r = self.list.get_selected_row()
        if r is not None and r.get_child_visible() and self.visible_row(r): self.launch(r.app)
        else: self.activate_first()
    def on_key(self, c, kv, code, st):
        n = Gdk.keyval_name(kv)
        if n == "Escape": self.pop.popdown(); return True
        if n in ("Down", "Up"):
            rows = []; i = 0
            while (r := self.list.get_row_at_index(i)): (rows.append(r) if r.get_child_visible() and self.visible_row(r) else None); i += 1
            if not rows: return True
            cur = self.list.get_selected_row(); k = rows.index(cur) if cur in rows else -1
            k = min(len(rows) - 1, k + 1) if n == "Down" else max(0, k - 1) if k > 0 else 0
            self.list.select_row(rows[k]); adj = self.sw.get_vadjustment(); h = rows[k].get_height(); top = sum(r.get_height() for r in rows[:k])
            if top < adj.get_value(): adj.set_value(top)
            elif top + h > adj.get_value() + adj.get_page_size(): adj.set_value(top + h - adj.get_page_size())
            return True
        return False

    def launch(self, app):
        self.pop.popdown()
        try: app.launch([], None)
        except GLib.Error as e: print("[launcher] no se pudo abrir", app.get_id(), e, flush=True)

class PowerMenu:
    """Botón de sesión: Bloquear, Cerrar sesión, Reiniciar, Apagar (con iconos propios). Reiniciar y Apagar piden un segundo clic para confirmar."""
    ACTIONS = [("owee-lock", _("Bloquear pantalla"), ["/usr/libexec/owee/owee-lock"], False),
               ("owee-logout", _("Cerrar sesión"), ["labwc", "--exit"], False),
               ("owee-restart", _("Reiniciar"), ["systemctl", "reboot"], True),
               ("owee-power", _("Apagar"), ["systemctl", "poweroff"], True)]
    def __init__(self):
        self.btn = Gtk.MenuButton(child=Gtk.Image(icon_name="owee-power", pixel_size=18), has_frame=False); self.btn.add_css_class("owee-widget")
        self.btn.set_tooltip_text(_("Sesión")); pop = Gtk.Popover(); self.btn.set_popover(pop); pop.connect("notify::visible", lambda p, _: self.reset())
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, margin_top=6, margin_bottom=6, margin_start=6, margin_end=6)
        self.rows = []
        for icon, text, cmd, confirm in self.ACTIONS:
            if cmd[0].endswith("owee-lock") and not GLib.find_program_in_path("swaylock"): continue
            lab = Gtk.Label(label=text, xalign=0, hexpand=True); row = Gtk.Box(spacing=10); row.append(Gtk.Image(icon_name=icon, pixel_size=18)); row.append(lab)
            b = Gtk.Button(child=row, has_frame=False); b.add_css_class("owee-row"); b.connect("clicked", self.clicked, cmd, confirm, lab, text, pop)
            box.append(b); self.rows.append((lab, text))
        pop.set_child(box)
    def reset(self):
        for lab, text in self.rows: lab.set_text(text); lab.remove_css_class("warn")
    def clicked(self, b, cmd, confirm, lab, text, pop):
        if confirm and not lab.has_css_class("warn"):
            self.reset(); lab.set_text(_("¿Seguro? Clic para confirmar")); lab.add_css_class("warn"); return
        pop.popdown()
        try: Gio.Subprocess.new(cmd, Gio.SubprocessFlags.NONE)
        except GLib.Error as e: print("[sesión] no se pudo ejecutar", cmd, e, flush=True)

DIAS = [_("lunes"), _("martes"), _("miércoles"), _("jueves"), _("viernes"), _("sábado"), _("domingo")]
MESES = [_("enero"), _("febrero"), _("marzo"), _("abril"), _("mayo"), _("junio"), _("julio"), _("agosto"), _("septiembre"), _("octubre"), _("noviembre"), _("diciembre")]

class Clock:
    """Reloj del centro del panel. Al hacer clic abre un calendario visual con la hora, la fecha completa y el botón «Hoy».
    Los nombres de día y mes están en español en el propio código (no dependen de que la imagen traiga el idioma instalado)."""
    def __init__(self):
        self.label = Gtk.Label(); self.btn = Gtk.MenuButton(child=self.label, has_frame=False); self.btn.add_css_class("owee-widget")
        self.vertical = False; self.label.set_justify(Gtk.Justification.CENTER)
        self.src = 0; self.pop = Gtk.Popover(); self.btn.set_popover(self.pop); self.pop.connect("notify::visible", lambda p, _: (self.pop.get_visible() and self.today(), self.refresh()))
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=12, margin_bottom=12, margin_start=14, margin_end=14)
        self.big = Gtk.Label(xalign=0, css_classes=["clock-big"]); self.date = Gtk.Label(xalign=0, css_classes=["heading"])
        self.cal = Gtk.Calendar(show_week_numbers=True); self.go = Gtk.Button(label=_("Hoy")); self.go.connect("clicked", lambda b: self.today())
        self.openc = Gtk.Button(label=_("Calendario")); self.openc.connect("clicked", lambda b: (self.pop.popdown(), self.open_app()))
        for w in (self.big, self.date, Gtk.Separator(), self.cal, self.go, self.openc): box.append(w)
        self.pop.set_child(box); self.tick()

    def open_app(self):
        for p in ("/usr/libexec/owee/apps/calendario/owee_calendar.py", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "calendario", "owee_calendar.py")):
            if os.path.exists(p): Gio.Subprocess.new([p], Gio.SubprocessFlags.NONE); return

    def today(self): self.cal.select_day(GLib.DateTime.new_now_local())

    def tick(self):
        n = GLib.DateTime.new_now_local(); c = owee_config.load()                       # (lectura pequeña y rápida; así el cambio de formato se ve al instante)
        hm = n.format("%I:%M" + (":%S" if c.get("clock_seconds") else "") + " %p") if str(c.get("clock_hours", "24")) == "12" else n.format("%H:%M" + (":%S" if c.get("clock_seconds") else ""))
        if self.vertical:                                                                   # panel lateral (delgado): hora y fecha en columna
            hh, mm = hm.split(" ")[0].split(":")[:2]; ap = hm.split(" ")[1] if " " in hm else ""
            self.label.set_text(hh + "\n" + mm + (("\n" + ap) if ap else "") + (f"\n\n{n.get_day_of_month()}\n{MESES[n.get_month() - 1][:3]}" if c.get("clock_date", True) else ""))
        else: self.label.set_text(hm + (f"   {n.get_day_of_month()} {MESES[n.get_month() - 1][:3]}" if c.get("clock_date", True) else ""))
        if self.pop.get_visible():
            self.big.set_text(n.format("%H:%M:%S")); self.date.set_text(_('{0}, {1} de {2} de {3}', DIAS[n.get_day_of_week() - 1].capitalize(), n.get_day_of_month(), MESES[n.get_month() - 1], n.get_year()))
        self.src = 0                                                                       # un despertar por minuto; por segundo solo con segundos activados o el calendario abierto
        delay = 1 if (c.get("clock_seconds") or self.pop.get_visible()) else max(1, 60 - n.get_second())
        self.src = GLib.timeout_add_seconds(delay, self.tick); return False

    def refresh(self):
        """Reprograma el reloj al instante (cambió el formato o se abrió/cerró el calendario)."""
        if self.src: GLib.source_remove(self.src); self.src = 0
        self.tick()

class InputIndicator:
    """Indicador del teclado en el panel: muestra con qué escribes ahora (US, ES, 拼 pinyin, あ Mozc, 한 Hangul, Ow Owee) y, al hacer clic, deja elegir entre el teclado normal y los métodos
    activados en Ajustes → Teclado. Habla con Fcitx5 por `fcitx5-remote` (asíncrono, con límite de tiempo); sin Fcitx5 no aparece."""
    SHORT = {"pinyin": "拼", "mozc": "あ", "hangul": "한", "owee": "Ow"}
    def __init__(self):
        self.label = Gtk.Label(label="…"); self.btn = Gtk.MenuButton(has_frame=False, child=self.label); self.btn.add_css_class("owee-widget"); self.btn.set_visible(False)
        self.pop = Gtk.Popover(); self.btn.set_popover(self.pop); self.pop.connect("notify::visible", lambda p, _x: p.get_visible() and self.build())
        self.cur = ""
        self.src = 0
        if GLib.find_program_in_path("fcitx5-remote"):               # solo se pregunta a Fcitx5 mientras esté en marcha (antes: dos procesos cada 2 s, aunque no hubiera ningún método activo)
            self.watch = Gio.bus_watch_name(Gio.BusType.SESSION, "org.fcitx.Fcitx5", Gio.BusNameWatcherFlags.NONE, self.appeared, self.vanished)

    def appeared(self, conn, name, owner=None):
        self.poll()
        if not self.src: self.src = GLib.timeout_add_seconds(2, self.poll)

    def vanished(self, conn, name):
        if self.src: GLib.source_remove(self.src); self.src = 0
        n = self.last or self.guess(); self.cur = n; self.btn.set_visible(bool(n))
        if n: self.label.set_text(self.short(n)); self.btn.set_tooltip_text(self.nice(n))

    def poll(self):
        try:
            p = Gio.Subprocess.new(["timeout", "-k", "1", "2", "fcitx5-remote", "-n"], Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE)
            p.communicate_utf8_async(None, None, self.got)
        except GLib.Error: pass
        return True

    def got(self, p, res):
        try: _ok, out, _e = p.communicate_utf8_finish(res)
        except GLib.Error: return
        name = (out or "").strip()
        if not name:                                   # Fcitx5 solo dice el método de la ventana ENFOCADA; sin ventana enfocada se muestra el último conocido o el que se usará al enfocar una
            name = self.last or self.guess()
        else: self.last = name
        self.cur = name; self.btn.set_visible(bool(name))
        if name: self.label.set_text(self.short(name)); self.btn.set_tooltip_text(self.nice(name))

    last = ""
    def guess(self):
        from ajustes import metodos
        items = metodos.read_items()
        if not items: return "keyboard-us"
        return items[1] if metodos.active_by_default() and len(items) > 1 else items[0]

    def short(self, name): return owee_keys.short(owee_keys.active()) if name.startswith("keyboard-") else self.SHORT.get(name, name[:2])
    def nice(self, name):
        if name.startswith("keyboard-"): return _("Teclado normal ({0})", self.layout_name(owee_keys.active()))
        from ajustes import metodos
        return next((t for n, t, _l in metodos.CATALOG if n == name), name)

    def layout_name(self, key):
        from ajustes.teclado import LAYOUTS
        return next((n for l, v, n in LAYOUTS if (f"{l}({v})" if v else l) == key), key)

    def build(self):
        from ajustes import metodos
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, margin_top=6, margin_bottom=6, margin_start=6, margin_end=6)
        box.append(Gtk.Label(label=_("Escribir con"), xalign=0, css_classes=["heading"], margin_start=6, margin_bottom=2))
        lst, idx = owee_keys.state(); kbd = self.cur.startswith("keyboard-") or not self.cur
        def add(short, text, on, mark):
            row = Gtk.Box(spacing=10); row.append(Gtk.Label(label=short, width_chars=3)); row.append(Gtk.Label(label=text, xalign=0, hexpand=True))
            if mark: row.append(Gtk.Label(label="✓"))
            b = Gtk.Button(child=row, has_frame=False); b.add_css_class("owee-row"); b.connect("clicked", lambda _b: on()); box.append(b)
        for i, key in enumerate(lst): add(owee_keys.short(key), _("Teclado normal ({0})", self.layout_name(key)), lambda i=i: self.choose_layout(i), kbd and i == idx)
        for name in metodos.read_items():
            if not name.startswith("keyboard-"): add(self.short(name), self.nice(name), lambda n=name: self.choose(n), name == self.cur)
        box.append(Gtk.Separator(margin_top=4, margin_bottom=4))
        more = Gtk.Button(label=_("Ajustes del teclado…"), has_frame=False); more.add_css_class("owee-row"); more.connect("clicked", lambda _b: (self.pop.popdown(), self.settings())); box.append(more)
        self.pop.set_child(box)

    def choose_layout(self, i):
        """Otra distribución del teclado normal: la cambia labwc (owee_keys) y Fcitx5 vuelve a su teclado base."""
        self.pop.popdown(); owee_keys.select(i); self.choose("keyboard-us")

    def choose(self, name):
        self.pop.popdown()
        try: Gio.Subprocess.new(["fcitx5-remote", "-s", name], Gio.SubprocessFlags.STDERR_SILENCE)
        except GLib.Error: pass
        GLib.timeout_add(300, lambda: (self.poll(), False)[1])

    def settings(self):
        for p in ("/usr/libexec/owee/owee_settings.py", os.path.join(os.path.dirname(os.path.abspath(__file__)), "owee_settings.py")):
            if os.path.exists(p):
                try: Gio.Subprocess.new([p], Gio.SubprocessFlags.NONE)
                except GLib.Error: pass
                return

class Panel(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.oweelinux.PanelPrototype")

    def do_activate(self):
        self.prov = Gtk.CssProvider(); self.apply_settings()
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        try:                                           # cambios en los ajustes (app de ajustes) se aplican al instante, sin reiniciar el panel
            os.makedirs(os.path.dirname(owee_config.PATH), exist_ok=True)
            self.mon = Gio.File.new_for_path(os.path.dirname(owee_config.PATH)).monitor_directory(Gio.FileMonitorFlags.NONE, None)
            self.mon.connect("changed", lambda m, f, o, ev: f.get_basename() == "settings.json" and GLib.timeout_add(150, lambda: (self.apply_settings(), False)[1]))
        except GLib.Error as e: print("[ajustes] sin vigilancia:", e, flush=True)
        for name, fn in (("launcher", lambda *a: self.launcher.btn.popup()), ("calendar", lambda *a: self.clock.btn.popup()), ("power", lambda *a: self.power.btn.popup()), ("overview", lambda *a: self.overview.toggle()), ("switcher-next", lambda *a: self.switcher.step(1)), ("switcher-prev", lambda *a: self.switcher.step(-1)), ("desktops", lambda *a: self.desktops_view.toggle())):
            act = Gio.SimpleAction.new(name, None); act.connect("activate", fn); self.add_action(act)    # `gapplication action org.oweelinux.PanelPrototype launcher` (atajos de labwc)
        win = Gtk.ApplicationWindow(application=self); win.add_css_class("owee-panel")
        LS.init_for_window(win); LS.set_layer(win, LS.Layer.TOP); LS.set_namespace(win, "owee-panel")
        for e in (LS.Edge.TOP, LS.Edge.LEFT, LS.Edge.RIGHT): LS.set_anchor(win, e, True)
        LS.set_margin(win, LS.Edge.TOP, 6); LS.set_margin(win, LS.Edge.LEFT, 8); LS.set_margin(win, LS.Edge.RIGHT, 8)
        LS.auto_exclusive_zone_enable(win); win.set_default_size(-1, 30)
        LS.set_keyboard_mode(win, LS.KeyboardMode.ON_DEMAND)         # que las ventanitas (popovers) reciban teclado al hacer clic
        bar = self.bar = Gtk.CenterBox(); win.set_child(bar)
        self.launcher = Launcher(); left = self.left_box = Gtk.Box(spacing=4); left.append(self.launcher.btn); bar.set_start_widget(left)
        try:
            from owee_desktops import DesktopSwitcher, Corners
            self.desks = DesktopSwitcher(); left.append(self.desks.box); self.corners = Corners(self, self.corner_action); self.corners.set_actions(owee_config.load().get("corners", {}))
        except Exception as e: print("[escritorios] desactivados:", e, flush=True)
        self.tasks = TaskBar(lambda: self.watcher); left.append(self.tasks.box)
        self.clock = Clock(); bar.set_center_widget(self.clock.btn)
        right = self.right_box = Gtk.Box(spacing=4); bar.set_end_widget(right)
        self.reminders = Reminders()                                          # avisos de eventos del Calendario
        self.clip = Clipboard(); right.append(self.clip.btn)                   # historial del portapapeles
        self.rec = RecIndicator(); right.append(self.rec.box)             # controles de la grabación de pantalla (solo mientras se graba)
        try:                                           # la bandeja es opcional: si falla, el panel sigue sin ella
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from owee_tray import Tray
            self.tray = Tray(); right.append(self.tray.box)
        except Exception as e: print("[tray] desactivada:", e, flush=True)
        self.input = InputIndicator(); right.append(self.input.btn)       # con qué teclado/método escribes
        self.widgets = load_widgets(right)
        self.power = PowerMenu(); right.append(self.power.btn)             # widgets de usuario (Python, JavaScript...) a la izquierda de los del sistema
        self.tick()
        self.win = win; self.compact = False
        from owee_switcher import Registry, WindowSwitcher, DesktopsView; self.registry = Registry()      # uso reciente y escritorio de cada ventana (antes del vigilante, que lo alimenta)
        try:                                           # con una ventana maximizada el panel se pega a los bordes y pierde las esquinas (como la barra de menús de macOS)
            from owee_windows import WindowWatcher
            self.watcher = WindowWatcher(self.set_compact, lambda ws: (self.tasks.update(ws), self.registry.update(ws)))
        except Exception as e: print("[ventanas] desactivado:", e, flush=True)
        from owee_overview import Overview; self.overview = Overview(self)
        self.switcher = WindowSwitcher(self); self.desktops_view = DesktopsView(self)       # Alt + Tab y Super + Tab         # vista general (esquinas activas, Super + A)
        self.apply_layout(); win.present()
        if os.environ.get("OWEE_DEBUG_LAYOUT"): GLib.timeout_add_seconds(4, lambda: (self.dump_layout(win), True)[1])
        GLib.timeout_add_seconds(5, lambda: (mem("5 s tras abrir"), False)[1])
        GLib.timeout_add_seconds(40, lambda: (mem("40 s tras abrir"), False)[1])

    EDGES = {"top": (LS.Edge.TOP, LS.Edge.LEFT, LS.Edge.RIGHT), "bottom": (LS.Edge.BOTTOM, LS.Edge.LEFT, LS.Edge.RIGHT), "left": (LS.Edge.LEFT, LS.Edge.TOP, LS.Edge.BOTTOM), "right": (LS.Edge.RIGHT, LS.Edge.TOP, LS.Edge.BOTTOM)}
    ARROW = {"top": Gtk.ArrowType.DOWN, "bottom": Gtk.ArrowType.UP, "left": Gtk.ArrowType.RIGHT, "right": Gtk.ArrowType.LEFT}
    THICK = {"compact": 26, "normal": 30, "large": 40}

    def set_margins(self, flat):
        """Margen flotante (6 px al borde y 8 a los lados); sin margen cuando la ventana activa está maximizada (modo compacto)."""
        main, a, b = self.EDGES[getattr(self, "pos", "top")]
        for e in (LS.Edge.TOP, LS.Edge.BOTTOM, LS.Edge.LEFT, LS.Edge.RIGHT): LS.set_margin(self.win, e, 0)
        if not flat: LS.set_margin(self.win, main, 6); LS.set_margin(self.win, a, 8); LS.set_margin(self.win, b, 8)

    def apply_layout(self):
        """Posición (arriba, abajo, izquierda o derecha) y tamaño del panel, de Ajustes → Escritorios. Las ventanitas se abren hacia el lado contrario al borde."""
        cfg = owee_config.load(); pos = cfg.get("panel_pos", "top"); size = cfg.get("panel_size", "normal")
        if (pos, size) == getattr(self, "layout", None): return
        self.layout = (pos, size); self.pos = pos; vertical = pos in ("left", "right"); win = self.win
        global VERT; VERT = vertical
        if hasattr(self, "tasks"): self.tasks.pos = pos
        for e in (LS.Edge.TOP, LS.Edge.BOTTOM, LS.Edge.LEFT, LS.Edge.RIGHT): LS.set_anchor(win, e, False)
        for e in self.EDGES[pos]: LS.set_anchor(win, e, True)
        o = Gtk.Orientation.VERTICAL if vertical else Gtk.Orientation.HORIZONTAL; thick = self.THICK[size]
        for box in (self.bar, self.left_box, self.right_box, getattr(getattr(self, "desks", None), "box", None), getattr(getattr(self, "tasks", None), "box", None), getattr(getattr(self, "rec", None), "box", None), getattr(getattr(self, "tray", None), "box", None)):
            if box is not None: box.set_orientation(o)
        self.bar.set_size_request(thick + 8 if vertical else -1, -1 if vertical else thick); win.set_default_size(thick + 8 if vertical else -1, -1 if vertical else thick)
        (win.add_css_class if vertical else win.remove_css_class)("vertical")
        for box in (self.left_box, self.right_box):
            c = box.get_first_child()
            while c: c.set_halign(Gtk.Align.CENTER if vertical else Gtk.Align.FILL); c = c.get_next_sibling()
        self.set_margins(self.compact)
        for sw in getattr(self, "widgets", []): sw.retext()
        if hasattr(self, "launcher"): self.launcher.name.set_visible(not vertical)           # lateral: solo el logo, para que el panel sea tan delgado como el de arriba o abajo
        if hasattr(self, "clock"): self.clock.vertical = vertical; self.clock.tick()
        def narrow(w):                                                                      # etiquetas de los widgets en columna: se parten en varias líneas en vez de ensanchar el panel
            while w:
                if isinstance(w, Gtk.Popover): w = w.get_next_sibling(); continue
                if isinstance(w, Gtk.Box) and isinstance(w.get_first_child(), Gtk.Image) and isinstance(w.get_last_child(), Gtk.Label): w.set_orientation(Gtk.Orientation.VERTICAL if vertical else Gtk.Orientation.HORIZONTAL)     # icono encima del texto
                if isinstance(w, Gtk.Label) and not w.has_css_class("clock-big") and w is not getattr(getattr(self, "clock", None), "label", None) and w is not getattr(getattr(self, "launcher", None), "name", None):
                    w.set_wrap(vertical); w.set_max_width_chars(4 if vertical else -1); w.set_justify(Gtk.Justification.CENTER if vertical else Gtk.Justification.LEFT)
                narrow(w.get_first_child()); w = w.get_next_sibling()
        narrow(self.bar)
        def arrows(w):
            while w:
                if isinstance(w, Gtk.MenuButton): w.set_direction(self.ARROW[pos])
                arrows(w.get_first_child()); w = w.get_next_sibling()
        arrows(self.bar)
        if os.environ.get("OWEE_DEBUG_LAYOUT"): print("[panel]", pos, size, flush=True)

    def set_compact(self, on):
        """Modo compacto: sin margen ni esquinas redondeadas mientras la ventana activa está maximizada o a pantalla completa."""
        self.compact = bool(on); self.set_margins(on)
        (self.win.add_css_class if on else self.win.remove_css_class)("compact")
        if os.environ.get("OWEE_DEBUG_LAYOUT"): print("[compacto]", on, flush=True)

    def corner_action(self, name):
        """Acciones de las esquinas activas (Ajustes → Escritorios)."""
        import owee_desktops
        if name == "overview": self.overview.toggle()
        elif name == "launcher": self.launcher.btn.popup()
        elif name == "calendar": self.clock.btn.popup()
        elif name == "next": owee_desktops.go(owee_desktops.current() % owee_desktops.desktop_count() + 1)
        elif name == "prev": owee_desktops.go((owee_desktops.current() - 2) % owee_desktops.desktop_count() + 1)
        elif name == "lock": Gio.Subprocess.new(["/usr/libexec/owee/owee-lock"], Gio.SubprocessFlags.NONE)
        elif name == "capture": Gio.Subprocess.new(["/usr/libexec/owee/apps/capturadora/owee_capture.py"], Gio.SubprocessFlags.NONE)

    def apply_settings(self):
        cfg = owee_config.load()
        if cfg.get("lang") and cfg["lang"] != owee_i18n.LANG:             # cambió el idioma en Ajustes: el panel se reinicia a sí mismo para mostrarse en el idioma nuevo
            GLib.timeout_add(400, lambda: os.execv(sys.executable, [sys.executable] + sys.argv))
        if hasattr(self, "corners"): self.corners.set_actions(cfg.get("corners", {}))
        if hasattr(self, "bar") and hasattr(self, "win"): self.apply_layout()
        if hasattr(self, "clock"): self.clock.refresh()
        pal = owee_config.palette(cfg)
        self.prov.load_from_data(css_for(pal))
        Gtk.Settings.get_default().set_property("gtk-icon-theme-name", pal["icons"])       # iconos propios; el resto cae a breeze/Adwaita/hicolor
        fam, size, _m = owee_config.fonts(cfg); Gtk.Settings.get_default().set_property("gtk-font-name", f"{fam} {size}")          # letra del panel al instante (Ajustes → Texto y ventanas)

    def dump_layout(self, win):                                  # solo depuración: posición de cada widget (para pruebas con el ratón)
        out = {}
        for w in self.widgets:
            ok, r = w.btn.compute_bounds(win)
            if ok: out[w.name] = [int(r.get_x() + 8 + r.get_width() / 2), int(r.get_y() + 6 + r.get_height() / 2)]
        for k, it in getattr(getattr(self, "tray", None), "items", {}).items():
            ok, r = it.btn.compute_bounds(win)
            if ok: out["tray"] = [int(r.get_x() + 8 + r.get_width() / 2), int(r.get_y() + 6 + r.get_height() / 2)]
        print("[layout] " + json.dumps(out), flush=True)

    def tick(self): self.clock.refresh()

if __name__ == "__main__":
    t0 = time.time(); mem("tras importar"); Panel().run(sys.argv)
