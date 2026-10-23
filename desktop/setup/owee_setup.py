#!/usr/bin/env python3
"""Primer arranque de OweeLinux: asistente corto (idioma → teclado → zona horaria → tu cuenta → terminar) que corre en una sesión propia de SDDM (`owee-setup-session`), solo mientras
el equipo no tenga ningún usuario. Crea tu usuario (administrador) con `owee-account-helper firstboot` vía pkexec (la contraseña va por la entrada estándar), deja listo el idioma y el
teclado del equipo y de tu sesión, y vuelve a la pantalla de inicio de sesión. Variables de prueba: OWEE_SETUP_WINDOWED=1 (ventana normal), OWEE_SETUP_DRYRUN=1 (no crea nada)."""
import math, os, re, sys, time
for d in ("/usr/libexec/owee", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shell")): sys.path.insert(0, d)
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Gdk
from owee_i18n import _, N_
import owee_i18n, owee_config, owee_keys
from owee_koi import KoiPond
owee_i18n.apply_direction()
from ajustes.teclado import LAYOUTS
from ajustes.usuarios import suggest_username, HELPERS

CSS = """
window.background { background-color: @win@; color: @fg@; }
.title1 { font-size: 26pt; font-weight: bold; } .sub { color: @dim@; font-size: 12pt; }
entry, passwordentry, dropdown > button { background-color: @entry@; color: @fg@; border-color: @line@; min-height: 34px; }
button { background-image: none; background-color: @key@; color: @fg@; box-shadow: none; border-color: transparent; padding: 8px 22px; } button:hover { background-color: @keyh@; }
button.suggested-action { background-color: @acc@; color: @onacc@; } .bad { color: #F06548; } .step { color: @dim@; }
popover > contents { background-color: @pop@; color: @fg@; } popover row:hover { background-color: @key@; }
"""

def style():
    cfg = owee_config.load(); pal = owee_config.palette(cfg); css = CSS
    for k in ("win", "fg", "pop", "entry", "key", "keyh", "line", "dim"): css = css.replace("@%s@" % k, pal[k])
    css = css.replace("@acc@", pal["accent"]).replace("@onacc@", pal["on"])
    prov = Gtk.CssProvider(); prov.load_from_data(css.encode()); Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", pal["mode"] == "dark"); Gtk.Settings.get_default().set_property("gtk-icon-theme-name", pal["icons"])

def zones():
    out = []
    try:
        for l in open("/usr/share/zoneinfo/zone1970.tab", encoding="utf-8"):
            if not l.startswith("#"): out.append(l.rstrip("\n").split("\t")[2])
    except OSError: pass
    return ["UTC"] + sorted(set(out))

def current_tz():
    try: return open("/etc/timezone").read().strip() or "UTC"
    except OSError: return "UTC"

class Setup(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.oweelinux.Setup"); self.page = 0

    def do_activate(self):
        style(); self.lang = owee_i18n.LANG
        self.win = Gtk.ApplicationWindow(application=self, title=_("Bienvenido a OweeLinux"), default_width=760, default_height=560)
        if not os.environ.get("OWEE_SETUP_WINDOWED"): self.win.fullscreen()
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, spacing=14, width_request=560, margin_top=12, margin_bottom=12)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        inner.append(Gtk.Image(icon_name="owee-logo", pixel_size=96))
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT, hhomogeneous=True, vhomogeneous=False, interpolate_size=True); inner.append(self.stack)
        self.err = Gtk.Label(wrap=True, css_classes=["bad"]); inner.append(self.err)
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, propagate_natural_height=True, vexpand=True, child=inner); outer.append(scroll)      # si la pantalla es baja, el contenido se desplaza; los botones quedan SIEMPRE a la vista
        nav = Gtk.Box(spacing=10); self.back = Gtk.Button(label=_("Atrás")); self.next = Gtk.Button(label=_("Siguiente"), css_classes=["suggested-action"], hexpand=True, halign=Gtk.Align.END)
        self.back.connect("clicked", lambda _b: self.go(-1)); self.next.connect("clicked", lambda _b: self.go(1)); nav.append(self.back); nav.append(self.next); outer.append(nav)
        self.win.set_child(outer)
        self.pages = [self.p_lang(), self.p_kbd(), self.p_tz(), self.p_user()]
        for i, p in enumerate(self.pages): self.stack.add_named(p, str(i))
        self.stack.add_named(self.p_progress(), "progress")
        self.ptimer = 0; self.show(0); self.win.present()

    def box(self, title, sub=""):
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        b.append(Gtk.Label(label=title, xalign=0, css_classes=["title1"]))
        if sub: b.append(Gtk.Label(label=sub, xalign=0, wrap=True, css_classes=["sub"]))
        return b

    def p_lang(self):
        b = self.box(_("Bienvenido a OweeLinux"), _("Vamos a dejar el equipo listo en unos pasos."))
        b.append(Gtk.Label(label=_("Elige tu idioma"), xalign=0))
        names = [f"{n}" for _c, n, _l in owee_i18n.LANGS]; dd = Gtk.DropDown.new_from_strings(names)
        dd.set_selected([c for c, _n, _l in owee_i18n.LANGS].index(self.lang) if self.lang in [c for c, _n, _l in owee_i18n.LANGS] else 0)
        dd.connect("notify::selected", lambda w, _p: self.pick_lang(owee_i18n.LANGS[w.get_selected()][0])); b.append(dd); return b

    def pick_lang(self, code):
        """Cambia el idioma del asistente: se guarda y la ventana se reinicia (los textos se fijan al arrancar), con la distribución típica de ese idioma ya puesta."""
        if code == self.lang: return
        c = owee_config.load(); c["lang"] = code; owee_config.save(c); owee_keys.apply(owee_i18n.layout_for(code).split(","), len(owee_i18n.layout_for(code).split(",")) - 1 if code in owee_i18n.NATIVE_SCRIPT else 0)
        GLib.timeout_add(300, lambda: (os.execv(sys.executable, [sys.executable] + sys.argv), False)[1])

    def p_kbd(self):
        b = self.box(_("Elige tu teclado"))
        lst, idx = owee_keys.state(); cur = lst[idx]; keys = [f"{l}({v})" if v else l for l, v, _n in LAYOUTS]
        b.append(Gtk.Label(label=_("Distribución del teclado"), xalign=0))
        self.kbd = Gtk.DropDown.new_from_strings([n for _l, _v, n in LAYOUTS]); self.kkeys = keys
        self.kbd.set_selected(keys.index(cur) if cur in keys else 0); self.kbd.connect("notify::selected", lambda w, _p: self.pick_kbd(keys[w.get_selected()])); b.append(self.kbd)
        b.append(Gtk.Label(label=_("Escribe aquí para probar tu teclado"), xalign=0)); b.append(Gtk.Entry()); return b

    def pick_kbd(self, key):
        default = owee_i18n.layout_for(self.lang).split(",")
        if key in default: owee_keys.apply(default, default.index(key))
        else: owee_keys.apply([key], 0)

    def p_tz(self):
        b = self.box(_("Elige tu zona horaria")); b.append(Gtk.Label(label=_("Zona horaria"), xalign=0))
        zs = zones(); self.zs = zs; self.tz = Gtk.DropDown(model=Gtk.StringList.new(zs), enable_search=True, expression=Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"))
        try: self.tz.set_search_match_mode(Gtk.StringFilterMatchMode.SUBSTRING)
        except AttributeError: pass
        t = current_tz(); self.tz.set_selected(zs.index(t) if t in zs else 0); b.append(self.tz); return b

    def p_user(self):
        b = self.box(_("Crea tu cuenta"), _("Serás el administrador de este equipo."))
        def field(label, secret=False):
            b.append(Gtk.Label(label=label, xalign=0)); e = Gtk.PasswordEntry(show_peek_icon=True) if secret else Gtk.Entry(); b.append(e); return e
        self.full = field(_("Nombre completo")); self.user = field(_("Nombre de usuario")); self.p1 = field(_("Contraseña"), True); self.p2 = field(_("Repite la contraseña"), True)
        last = [""]
        def follow(*_a):
            if self.user.get_text() in ("", last[0]): last[0] = suggest_username(self.full.get_text()); self.user.set_text(last[0])
        self.full.connect("changed", follow); self.p2.connect("activate", lambda *_a: self.go(1)); return b

    STEPS = [N_("Creando tu cuenta"), N_("Configurando el idioma y el teclado"), N_("Ajustando la hora"), N_("Preparando tu escritorio"), N_("Casi listo…")]

    def p_progress(self):
        b = self.box(_("Preparando tu equipo…"), _("Esto tarda unos segundos."))
        b.append(KoiPond()); self.step_labels = []
        for t in self.STEPS:
            l = Gtk.Label(label="○  " + _(t), xalign=0, css_classes=["step"]); self.step_labels.append(l); b.append(l)
        self.final_msg = Gtk.Label(label="", wrap=True, xalign=0, css_classes=["sub"]); b.append(self.final_msg)
        return b

    def begin_progress(self):
        self.stack.set_visible_child_name("progress"); self.back.set_visible(False); self.next.set_visible(False); self.err.set_text(""); self.pstep = 0; self.mark(0)
        def tick():
            if self.pstep < len(self.STEPS) - 2: self.pstep += 1; self.mark(self.pstep)       # los pasos avanzan solos; el último espera a que el ayudante termine de verdad
            return self.pstep < len(self.STEPS) - 2
        self.ptimer = GLib.timeout_add(1300, tick)

    def mark(self, upto):
        for i, l in enumerate(self.step_labels): l.set_text(("✓  " if i < upto else "●  " if i == upto else "○  ") + _(self.STEPS[i]))

    def end_progress(self, ok):
        if self.ptimer: GLib.source_remove(self.ptimer); self.ptimer = 0
        if ok:
            for i, l in enumerate(self.step_labels): l.set_text("✓  " + _(self.STEPS[i]))
            self.final_msg.set_text(_("Listo. Cargando la pantalla de inicio de sesión…") + "\n" + _("En unos segundos verás el inicio de sesión; la pantalla puede quedar en negro un momento."))
        else:
            self.stack.set_visible_child_name(str(len(self.pages) - 1)); self.back.set_visible(True); self.next.set_visible(True)

    def show(self, i):
        self.page = i; self.stack.set_visible_child_name(str(i)); self.err.set_text(""); self.back.set_sensitive(i > 0)
        self.next.set_label(_("Terminar") if i == len(self.pages) - 1 else _("Siguiente"))
        if i == len(self.pages) - 1: self.full.grab_focus()

    def go(self, d):
        if d > 0 and self.page == len(self.pages) - 1: self.finish(); return
        self.show(max(0, min(len(self.pages) - 1, self.page + d)))

    def finish(self):
        full, user, p1, p2 = self.full.get_text().strip(), self.user.get_text().strip(), self.p1.get_text(), self.p2.get_text()
        if not full: self.err.set_text(_("Escribe el nombre completo")); return
        if not re.match(r"^[a-z_][a-z0-9_-]{0,30}$", user): self.err.set_text(_("Usuario: minúsculas, cifras, - y _ (empieza por letra)")); return
        if not p1: self.err.set_text(_("Escribe una contraseña")); return
        if p1 != p2: self.err.set_text(_("Las contraseñas no coinciden")); return
        lst, idx = owee_keys.state(); tz = self.zs[self.tz.get_selected()]
        argv = ["firstboot", user, full, owee_i18n.LANG, ",".join(lst), str(idx), tz]
        self.next.set_sensitive(False); self.back.set_sensitive(False); self.begin_progress()
        if os.environ.get("OWEE_SETUP_DRYRUN"): print("DRYRUN", argv, flush=True); GLib.timeout_add(800, lambda: (self.done(0, "ok"), False)[1]); return
        h = next((x for x in HELPERS if os.path.exists(x)), HELPERS[0])
        try: p = Gio.Subprocess.new(["pkexec", h] + argv, Gio.SubprocessFlags.STDIN_PIPE | Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE)
        except GLib.Error as e: self.done(1, str(e)); return
        p.communicate_utf8_async(p1 + "\n", None, lambda pr, res: self.done(pr.get_exit_status() if pr.get_if_exited() else 1, (pr.communicate_utf8_finish(res)[1] or "")))

    def sub_msg(self, t): self.err.remove_css_class("bad"); self.err.set_text(t)

    def done(self, code, out):
        if code == 0 and out.strip().endswith("ok"): self.end_progress(True); return
        self.end_progress(False); self.err.add_css_class("bad"); self.err.set_text(_("No se pudo terminar: {0}", out.strip().removeprefix("ERR: ") or _("cancelado o sin permiso")))
        self.next.set_sensitive(True); self.back.set_sensitive(True)

if __name__ == "__main__": sys.exit(Setup().run(sys.argv))
