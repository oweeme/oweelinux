"""Acceso: la pantalla de bloqueo (colores del tema y, si quieres, el fondo) y el inicio de sesión (SDDM): entrar solo al encender y sesión predeterminada.
El tiempo de bloqueo por inactividad se cambia en Energía. Los cambios del inicio de sesión son del sistema: pasan por `owee-account-helper` con `pkexec`."""
import configparser, glob, os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gio
from .base import Page, page_box, scrolled, heading, row, dropdown, switch, run, have
from .usuarios import helper, list_users
from owee_i18n import _

def sessions():
    """[(archivo.desktop, nombre)] de las sesiones instaladas (Wayland y X11)."""
    out = []
    for d in ("/usr/share/wayland-sessions", "/usr/share/xsessions"):
        for f in sorted(glob.glob(d + "/*.desktop")):
            cp = configparser.ConfigParser(interpolation=None, strict=False)
            try: cp.read(f, encoding="utf-8"); name = cp["Desktop Entry"].get("Name", "") ; hidden = cp["Desktop Entry"].get("Hidden", "") == "true" or cp["Desktop Entry"].get("NoDisplay", "") == "true"
            except (configparser.Error, KeyError, OSError): continue
            if name and not hidden and not any(o[0] == os.path.basename(f) for o in out): out.append((os.path.basename(f), name))
    return out

def autologin_state():
    """(usuario, sesión) con que SDDM entra solo, mirando /etc/sddm.conf y /etc/sddm.conf.d/*.conf (el último que lo define manda); ('', '') si no entra solo."""
    user = sess = ""
    for f in ["/etc/sddm.conf"] + sorted(glob.glob("/etc/sddm.conf.d/*.conf")) + sorted(glob.glob("/usr/lib/sddm/sddm.conf.d/*.conf")):
        cp = configparser.ConfigParser(interpolation=None, strict=False)
        try: cp.read(f, encoding="utf-8")
        except (configparser.Error, OSError): continue
        if cp.has_section("Autologin"):
            if cp.has_option("Autologin", "User"): user = cp.get("Autologin", "User")
            if cp.has_option("Autologin", "Session"): sess = cp.get("Autologin", "Session")
    return user, sess

class Acceso(Page):
    title = _("Acceso"); icon = "owee-set-lock"; group = "Sistema"; order = 15; keywords = _("acceso inicio de sesión login bloqueo pantalla contraseña automático sddm")
    def build(self, app):
        self.app = app; b = page_box(_("Acceso"), _("Cómo se bloquea la pantalla y cómo se entra al encender el equipo."))
        b.append(heading(_("Pantalla de bloqueo")))
        b.append(row(_("Mostrar el fondo de pantalla al bloquear"), switch(app.cfg.get("lock_wallpaper", True), lambda on: app.change(lock_wallpaper=on)), _("Si no, se usa el color del tema")))
        test = Gtk.Button(label=_("Bloquear ahora"), halign=Gtk.Align.START); test.connect("clicked", lambda _b: self.lock_now()); b.append(test)
        b.append(Gtk.Label(label=_("Super + L bloquea al instante. El bloqueo por inactividad y la suspensión se eligen en Energía. Para volver, escribe tu contraseña."), xalign=0, wrap=True, css_classes=["dim-label"]))
        b.append(heading(_("Inicio de sesión")))
        self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); b.append(self.holder)
        self.status = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); b.append(self.status)
        self.loading = False; self.fill(); return scrolled(b)

    def lock_now(self):
        for p in ("/usr/libexec/owee/owee-lock", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "session", "owee-lock")):
            if os.path.exists(p): GLib.timeout_add(400, lambda p=p: (Gio.Subprocess.new([p], Gio.SubprocessFlags.NONE), False)[1]); return

    def refresh(self):
        if hasattr(self, "holder"): self.fill()

    def fill(self):
        while (c := self.holder.get_first_child()): self.holder.remove(c)
        if not os.path.isdir("/usr/share/sddm") and not os.path.isdir("/etc/sddm.conf.d"):
            self.holder.append(Gtk.Label(label=_("Este equipo no usa SDDM para iniciar sesión."), xalign=0)); return
        user, sess = autologin_state(); users = list_users(); ses = sessions()
        self.loading = True; self.user = user or (users[0][0] if users else ""); self.sess = sess or ("owee-lite.desktop" if any(x[0] == "owee-lite.desktop" for x in ses) else (ses[0][0] if ses else ""))
        self.holder.append(row(_("Entrar sin escribir la contraseña"), switch(bool(user), self.toggle), _("Al encender, el equipo entra solo con el usuario elegido. Cualquiera que lo encienda verá tus archivos.")))
        if users: self.holder.append(row(_("Usuario"), dropdown([(u[0], u[1]) for u in users], self.user, self.pick_user)))
        if ses: self.holder.append(row(_("Sesión"), dropdown(ses, self.sess if any(s[0] == self.sess for s in ses) else ses[0][0], self.pick_session), _("El escritorio que se abre al entrar")))
        self.loading = False

    def toggle(self, on):
        if self.loading: return
        self.apply(["autologin", self.user, self.sess] if on else ["autologin", "off"])

    def pick_user(self, k):
        self.user = k
        if not self.loading and autologin_state()[0]: self.apply(["autologin", self.user, self.sess])

    def pick_session(self, k):
        self.sess = k
        if not self.loading and autologin_state()[0]: self.apply(["autologin", self.user, self.sess])

    def apply(self, argv):
        if not have("pkexec"): self.status.set_text(_("Falta `pkexec` (polkit).")); return
        self.status.set_text(_("Esperando la clave de administrador…"))
        def done(out, code):
            ok = code == 0 and out.strip().endswith("ok"); self.status.set_text(_("Guardado: se aplica al próximo arranque") if ok else _("No se pudo: {0}", out.strip().removeprefix("ERR: ") or _("cancelado o sin permiso"))); self.fill()
        run(["pkexec", helper()] + argv, done, timeout=180)
PAGE = Acceso()
