"""Acceso: la pantalla de bloqueo (colores del tema y, si quieres, el fondo) y el inicio de sesión (SDDM): entrar solo al encender y sesión predeterminada.
El tiempo de bloqueo por inactividad se cambia en Energía. Los cambios del inicio de sesión son del sistema: pasan por `owee-account-helper` con `pkexec`."""
import shutil, configparser, glob, os
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
    allowed = ("owee-lite.desktop", "plasma.desktop", "plasmax11.desktop")             # el asistente, el instalador y «labwc» a pelo no son escritorios para usar: confundían y dejaban la pantalla negra
    return sorted([o for o in out if o[0] in allowed], key=lambda o: allowed.index(o[0]))

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
        b.append(row(_("Bloqueo animado (kois nadando)"), switch(app.cfg.get("access_anim", True), lambda on: app.change(access_anim=on)), _("Si tu equipo va lento al bloquear, apágalo")))
        b.append(row(_("Mostrar el fondo de pantalla al bloquear"), switch(app.cfg.get("lock_wallpaper", True), lambda on: app.change(lock_wallpaper=on)), _("Si no, se usa el color del tema")))
        test = Gtk.Button(label=_("Bloquear ahora"), halign=Gtk.Align.START); test.connect("clicked", lambda _b: self.lock_now()); b.append(test)
        b.append(Gtk.Label(label=_("Super + L bloquea al instante. El bloqueo por inactividad y la suspensión se eligen en Energía. Para volver, escribe tu contraseña."), xalign=0, wrap=True, css_classes=["dim-label"]))
        self.look(b)
        b.append(heading(_("Inicio de sesión")))
        self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); b.append(self.holder)
        self.status = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); b.append(self.status)
        self.loading = False; self.fill(); return scrolled(b)


    # ── aspecto del bloqueo y del inicio de sesión ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def look(self, b):
        """Posición, imagen y desenfoque. El bloqueo los usa al instante; el inicio de sesión (SDDM) es del sistema y se aplica con el botón (pide la clave de administrador)."""
        c = self.app.cfg
        b.append(heading(_("Aspecto del acceso")))
        b.append(Gtk.Label(label=_("Cómo se ven el bloqueo de pantalla y el inicio de sesión: el formulario a un lado o al centro, con una imagen de fondo."), xalign=0, wrap=True, css_classes=["dim-label"]))
        b.append(row(_("Posición del formulario"), dropdown([("left", _("Izquierda")), ("center", _("Centro")), ("right", _("Derecha"))], c.get("access_pos", "center"), lambda k: self.app.change(access_pos=k))))
        b.append(row(_("Estilo del inicio de sesión"), dropdown([("full", _("Imagen de fondo")), ("side", _("Imagen en un lado"))], c.get("access_style", "full"), lambda k: self.app.change(access_style=k)),
                     _("«Imagen en un lado» deja un panel liso para el formulario y la imagen entera al otro lado. Solo para el inicio de sesión.")))
        self.img_lbl = Gtk.Label(label=os.path.basename(c.get("access_image", "")) or "", xalign=0, css_classes=["dim-label"])
        b.append(row(_("Imagen"), dropdown([("desktop", _("La del escritorio")), ("image", _("Otra imagen…")), ("color", _("Solo color"))], c.get("access_bg", "desktop"), self.pick_image)))
        b.append(self.img_lbl)
        b.append(row(_("Desenfocar la imagen"), switch(bool(c.get("access_blur", False)), lambda on: self.app.change(access_blur=on)), _("Suaviza la foto para que el formulario se lea mejor")))
        btns = Gtk.Box(spacing=8)
        ap = Gtk.Button(label=_("Aplicar al inicio de sesión"), css_classes=["suggested-action"]); ap.connect("clicked", lambda _b: self.apply_login()); btns.append(ap)
        pv = Gtk.Button(label=_("Ver el inicio de sesión")); pv.connect("clicked", lambda _b: self.preview_login()); btns.append(pv)
        b.append(btns)
        self.std_loading = True
        b.append(row(_("Usar el aspecto de OweeLinux en el inicio de sesión"), switch(not os.path.exists("/etc/sddm.conf.d/29-owee-theme-user.conf"), self.toggle_theme), _("Si lo apagas se usa el inicio de sesión estándar de SDDM")))
        self.std_loading = False

    def pick_image(self, k):
        self.app.change(access_bg=k)
        if k != "image": return
        dlg = Gtk.FileDialog(); dlg.set_title(_("Elige una imagen")); flt = Gtk.FileFilter(); flt.set_name(_("Imágenes")); flt.add_mime_type("image/*"); dlg.set_default_filter(flt)
        def done(d, res):
            try: f = d.open_finish(res)
            except GLib.Error: return
            if f and f.get_path(): self.app.change(access_image=f.get_path()); self.img_lbl.set_text(os.path.basename(f.get_path()))
        dlg.open(self.status.get_root(), None, done)

    def login_image(self):
        c = self.app.cfg
        if c.get("access_bg") == "color": return "none"
        p = c.get("access_image") if c.get("access_bg") == "image" and c.get("access_image") else c.get("wallpaper", "")
        return p if p and os.path.isfile(p) else "none"

    def apply_login(self):
        c = self.app.cfg
        self.apply(["logintheme", "position=" + c.get("access_pos", "center"), "style=" + c.get("access_style", "full"), "blur=" + ("1" if c.get("access_blur") else "0"), "background=" + self.login_image(),
                    "password=" + _("Contraseña"), "hint=" + _("Escribe tu contraseña y pulsa Intro"), "wrong=" + _("Contraseña incorrecta"), "suspend=" + _("Reposo"), "reboot=" + _("Reiniciar"), "poweroff=" + _("Apagar")])

    def toggle_theme(self, on):
        if not self.std_loading: self.apply(["logintheme", "tema=" + ("owee" if on else "estandar")])

    def preview_login(self):
        """Abre el inicio de sesión en una ventana de prueba (modo de prueba de SDDM: no entra a ninguna sesión, ni al escribir la clave ni con los botones de energía). Para que NO quede atrapada se usa
        una copia temporal del tema con `preview=1` (aviso rojo con cuenta atrás) y Ajustes la cierra sola a los 16 s: el saludador de SDDM no tiene forma de salir por sí mismo."""
        if not have("sddm-greeter-qt6"): self.status.set_text(_("No se encontró el programa de inicio de sesión.")); return
        src = "/usr/share/sddm/themes/owee"; tmp = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "owee-login-preview")
        try:
            shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
            for f in os.listdir(src):
                if not f.startswith("theme.conf"): os.symlink(os.path.join(src, f), os.path.join(tmp, f))
            cfg = {}
            for f in ("theme.conf", "theme.conf.user"):
                try:
                    for line in open(os.path.join(src, f), encoding="utf-8"):
                        if "=" in line and not line.lstrip().startswith(("#", ";", "[")): k, v = line.split("=", 1); cfg[k.strip()] = v.strip().strip('"')
                except OSError: pass
            cfg["preview"] = "1"; cfg["previewtext"] = _("Vista previa: se cierra sola en {0} s")
            with open(os.path.join(tmp, "theme.conf"), "w", encoding="utf-8") as fh: fh.write("[General]\n" + "".join(f'{k}="{v}"\n' if " " in v or "#" in v else f"{k}={v}\n" for k, v in cfg.items()))
            proc = Gio.Subprocess.new(["sddm-greeter-qt6", "--test-mode", "--theme", tmp], Gio.SubprocessFlags.NONE)
            GLib.timeout_add_seconds(16, lambda: (proc.force_exit() if proc.get_identifier() else None, False)[1])
        except (OSError, GLib.Error) as e: self.status.set_text(str(e))

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
