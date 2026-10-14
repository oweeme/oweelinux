"""Usuarios: ver las cuentas del equipo, crear, cambiar contraseña, hacer administrador y borrar. Todo lo que cambia cuentas pasa por `owee-account-helper` con `pkexec` (pide la clave
de administrador); las contraseñas viajan por la entrada estándar, nunca por argumentos. Leer la lista no necesita permisos."""
import grp, os, pwd, re
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from .base import Page, page_box, scrolled, heading, row, switch, run, have
from owee_i18n import _

HELPERS = ["/usr/libexec/owee/owee-account-helper", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "session", "owee-account-helper")]
def helper(): return next((h for h in HELPERS if os.path.exists(h)), HELPERS[0])

def list_users():
    """[(usuario, nombre completo, es_admin, directorio)] de las cuentas de personas (UID 1000–59999)."""
    try: admins = set(grp.getgrnam("sudo").gr_mem)
    except KeyError: admins = set()
    return [(u.pw_name, u.pw_gecos.split(",")[0] or u.pw_name, u.pw_name in admins, u.pw_dir) for u in sorted(pwd.getpwall(), key=lambda x: x.pw_uid) if 1000 <= u.pw_uid < 60000]

def suggest_username(full):
    import unicodedata
    s = unicodedata.normalize("NFKD", full).encode("ascii", "ignore").decode().lower().split()
    return re.sub(r"[^a-z0-9_-]", "", s[0] if s else "")[:30]

def ask(parent, title, fields, ok_text, on_ok):
    """Ventanita modal con campos (nombre, texto, es_contraseña); on_ok(valores) devuelve un mensaje de error o None para cerrar."""
    win = Gtk.Window(title=title, modal=True, transient_for=parent, default_width=360, resizable=False)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=16, margin_bottom=16, margin_start=16, margin_end=16); win.set_child(box)
    ents = []
    for label, secret in fields:
        box.append(Gtk.Label(label=label, xalign=0)); e = Gtk.PasswordEntry(show_peek_icon=True) if secret else Gtk.Entry(); e.set_hexpand(True); box.append(e); ents.append(e)
    err = Gtk.Label(xalign=0, wrap=True, css_classes=["bad"]); box.append(err)
    bt = Gtk.Box(spacing=8, halign=Gtk.Align.END); cancel = Gtk.Button(label=_("Cancelar")); go = Gtk.Button(label=ok_text, css_classes=["suggested-action"]); bt.append(cancel); bt.append(go); box.append(bt)
    cancel.connect("clicked", lambda _b: win.close())
    def submit(*_a):
        msg = on_ok([e.get_text() for e in ents], win)
        if msg: err.set_text(msg)
    go.connect("clicked", submit); ents[-1].connect("activate", submit); win.present(); return win

class Usuarios(Page):
    title = _("Usuarios"); icon = "owee-set-users"; group = "Personal"; order = 50; keywords = _("usuarios cuentas contraseña administrador añadir borrar")
    def build(self, app):
        self.app = app; self.b = page_box(_("Usuarios"), _("Las personas que usan este equipo. Para crear, borrar o cambiar contraseñas se pide la clave de administrador."))
        self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); self.b.append(self.holder)
        self.status = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); self.b.append(self.status)
        add = Gtk.Button(label=_("Añadir usuario…"), halign=Gtk.Align.START); add.connect("clicked", lambda _b: self.add_dialog()); self.b.append(add)
        return scrolled(self.b)

    def win(self): return self.b.get_root()
    def say(self, t): self.status.set_text(t)

    def refresh(self):
        if not hasattr(self, "holder"): return
        while (c := self.holder.get_first_child()): self.holder.remove(c)
        me = os.environ.get("USER") or pwd.getpwuid(os.getuid()).pw_name
        for user, full, isadmin, home in list_users():
            r = Gtk.Box(spacing=12, css_classes=["setrow"]); ini = Gtk.Label(label=(full[:1] or "?").upper(), css_classes=["tick"], width_chars=2); ini.set_size_request(34, 34); r.append(ini)
            who = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True); who.append(Gtk.Label(label=full + ("  ·  " + _("tú") if user == me else ""), xalign=0, css_classes=["heading"]))
            who.append(Gtk.Label(label=f"{user} · " + (_("Administrador") if isadmin else _("Usuario estándar")), xalign=0, css_classes=["dim-label"])); r.append(who)
            sw = switch(isadmin, lambda on, u=user: self.set_admin(u, on)); sw.set_tooltip_text(_("Administrador")); r.append(sw)
            pw = Gtk.Button(label=_("Contraseña…")); pw.connect("clicked", lambda _b, u=user: self.passwd_dialog(u)); r.append(pw)
            if user != me:
                d = Gtk.Button(label=_("Eliminar")); d.connect("clicked", lambda _b, u=user: self.delete_dialog(u)); r.append(d)
            self.holder.append(r)

    def call(self, argv, ok_text, stdin=None):
        """Ejecuta el ayudante con pkexec; muestra el resultado y vuelve a listar."""
        if not have("pkexec"): self.say(_("Falta `pkexec` (polkit).")); return
        self.say(_("Esperando la clave de administrador…"))
        def done(out, code):
            ok = code == 0 and out.strip().endswith("ok"); self.say(ok_text if ok else _("No se pudo: {0}", (out.strip().removeprefix("ERR: ") or _("cancelado o sin permiso")))); self.refresh()
        run(["pkexec", helper()] + argv, done, timeout=180, stdin=stdin)

    def set_admin(self, user, on): self.call(["admin", user, "on" if on else "off"], _("Permisos cambiados"))

    def passwd_dialog(self, user):
        def ok(v, win):
            if len(v[0]) < 1: return _("Escribe una contraseña")
            if v[0] != v[1]: return _("Las contraseñas no coinciden")
            win.close(); self.call(["passwd", user], _("Contraseña cambiada"), stdin=v[0] + "\n")
        ask(self.win(), _("Contraseña de {0}", user), [(_("Contraseña nueva"), True), (_("Repítela"), True)], _("Cambiar"), ok)

    def delete_dialog(self, user):
        def ok(v, win):
            if v[0].strip() != user: return _("Escribe «{0}» para confirmar", user)
            win.close(); self.call(["delete", user], _("Usuario eliminado (con sus archivos)"))
        ask(self.win(), _("Eliminar a {0}", user), [(_("Se borrarán también sus archivos. Escribe su nombre de usuario para confirmar:"), False)], _("Eliminar"), ok)

    def add_dialog(self):
        def ok(v, win):
            full, user, p1, p2 = (v[0].strip(), v[1].strip(), v[2], v[3])
            if not full: return _("Escribe el nombre completo")
            if not re.match(r"^[a-z_][a-z0-9_-]{0,30}$", user): return _("Usuario: minúsculas, cifras, - y _ (empieza por letra)")
            if any(u[0] == user for u in list_users()): return _("Ese usuario ya existe")
            if not p1: return _("Escribe una contraseña")
            if p1 != p2: return _("Las contraseñas no coinciden")
            win.close(); self.call(["add", user, full], _("Usuario creado"), stdin=p1 + "\n")
        w = ask(self.win(), _("Añadir usuario"), [(_("Nombre completo"), False), (_("Nombre de usuario"), False), (_("Contraseña"), True), (_("Repite la contraseña"), True)], _("Crear"), ok)
        e = w.get_child().get_first_child().get_next_sibling(); u = e.get_next_sibling().get_next_sibling()
        last = [""]
        def follow(*_a):
            if u.get_text() in ("", last[0]): last[0] = suggest_username(e.get_text()); u.set_text(last[0])        # el usuario se va sugiriendo mientras no lo toques
        e.connect("changed", follow)
PAGE = Usuarios()
