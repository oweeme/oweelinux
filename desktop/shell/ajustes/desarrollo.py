"""Opciones de desarrollador: apagadas por defecto. Encendidas, ofrecen DOS caminos para modificar OweeLinux sin poder romperlo:
 1) «Mi copia de la interfaz» (segura): una copia editable del panel y de Ajustes en ~/.local/share/owee/shell. Si tu copia falla al arrancar, el sistema vuelve solo a la original (session/owee-panel-run).
 2) «Desbloquear /usr» (avanzada): `ostree admin unlock` deja /usr escribible hasta el próximo reinicio; al reiniciar, OweeLinux vuelve exactamente a como estaba (los cambios se descartan).
Ninguno toca el sistema de forma permanente: lo permanente se hace con una imagen propia (docs/CONSTRUIR.md)."""
import glob, os, shutil
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib
from .base import Page, page_box, scrolled, heading, row, switch, run, have
from owee_i18n import _

SRC = "/usr/libexec/owee"
DEST = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "owee", "shell")

def unlocked():
    """/usr está protegido si se monta solo de lectura (ostree); tras `ostree admin unlock` se monta con una capa escribible."""
    try: return "ro" not in os.popen("findmnt -no OPTIONS /usr 2>/dev/null").read().strip().split(",")
    except OSError: return False

class Desarrollo(Page):
    title = _("Opciones de desarrollador"); icon = "owee-set-info"; group = "Sistema"; order = 95; keywords = _("desarrollo modificar interfaz código root usr desbloquear registros")
    def build(self, app):
        self.app = app; self.b = page_box(_("Opciones de desarrollador"), _("Para quien quiera cambiar OweeLinux. Desactivado, el sistema queda protegido."))
        self.b.append(row(_("Modo desarrollador"), switch(bool(app.cfg.get("dev_mode", False)), self.toggle), _("Ninguna de estas opciones cambia el sistema de forma permanente")))
        self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); self.b.append(self.holder); self.fill(); return scrolled(self.b)

    def toggle(self, on): self.app.change(dev_mode=on); self.fill()
    def refresh(self): self.fill() if hasattr(self, "holder") else None

    def fill(self):
        while (c := self.holder.get_first_child()): self.holder.remove(c)
        if not self.app.cfg.get("dev_mode", False): return
        h = self.holder
        h.append(heading(_("Mi copia de la interfaz (segura)")))
        h.append(Gtk.Label(label=_("Crea una copia del panel y de Ajustes en tu carpeta personal, modifícala y actívala. Si tu copia falla al arrancar, OweeLinux usa la original solo. «Volver al original» borra tu copia."), xalign=0, wrap=True, css_classes=["dim-label"]))
        have_copy = os.path.exists(os.path.join(DEST, "owee_panel.py")); active = os.path.exists(os.path.join(DEST, ".enabled"))
        state = _("Copia activa") if have_copy and active else _("Copia creada, desactivada") if have_copy else _("Aún no has creado una copia")
        self.state = Gtk.Label(label=state, xalign=0, css_classes=["ok" if active else "dim-label"]); h.append(self.state)
        bar = Gtk.Box(spacing=8)
        for label, fn, show in ((_("Crear copia editable"), self.make_copy, not have_copy), (_("Activar mi copia"), lambda: self.set_active(True), have_copy and not active), (_("Usar la original"), lambda: self.set_active(False), have_copy and active),
                                (_("Abrir la carpeta"), self.open_dir, have_copy), (_("Reiniciar el panel"), self.restart_panel, True), (_("Volver al original"), self.reset_copy, have_copy)):
            if show: b = Gtk.Button(label=label); b.connect("clicked", lambda _b, fn=fn: fn()); bar.append(b)
        h.append(bar)
        h.append(heading(_("Sistema (avanzado)")))
        h.append(Gtk.Label(label=_("«Desbloquear /usr» permite editar los archivos del sistema hasta que reinicies; al reiniciar, OweeLinux vuelve exactamente a como estaba."), xalign=0, wrap=True, css_classes=["dim-label"]))
        self.ustate = Gtk.Label(label=_("/usr está desbloqueado (hasta el próximo reinicio)") if unlocked() else _("/usr está protegido (solo lectura)"), xalign=0, css_classes=["bad" if unlocked() else "ok"]); h.append(self.ustate)
        if have("ostree") and not unlocked():
            ub = Gtk.Button(label=_("Desbloquear /usr hasta el reinicio"), halign=Gtk.Align.START); ub.connect("clicked", lambda b: self.confirm_unlock()); h.append(ub)
        h.append(heading(_("Diagnóstico")))
        lb = Gtk.Button(label=_("Ver los errores del sistema"), halign=Gtk.Align.START); lb.connect("clicked", lambda b: self.show_log()); h.append(lb)
        self.msg = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); h.append(self.msg)

    def make_copy(self):
        try:
            os.makedirs(DEST, exist_ok=True)
            for f in glob.glob(os.path.join(SRC, "*.py")): shutil.copy2(f, DEST)
            shutil.copytree(os.path.join(SRC, "ajustes"), os.path.join(DEST, "ajustes"), dirs_exist_ok=True)
            if os.path.isdir(os.path.join(SRC, "protocols")): shutil.copytree(os.path.join(SRC, "protocols"), os.path.join(DEST, "protocols"), dirs_exist_ok=True)
            self.msg.set_label(_('Copia creada en {0}. Edítala y pulsa «Activar mi copia».', DEST))
        except OSError as e: self.msg.set_label(str(e))
        self.fill()

    def set_active(self, on):
        mark = os.path.join(DEST, ".enabled")
        try:
            if on: open(mark, "w").close()
            elif os.path.exists(mark): os.remove(mark)
        except OSError as e: self.msg.set_label(str(e))
        self.restart_panel(); self.fill()

    def open_dir(self):
        try: Gio.AppInfo.launch_default_for_uri("file://" + DEST, None)
        except GLib.Error as e: self.msg.set_label(str(e))

    def restart_panel(self):
        run(["sh", "-c", "pkill -f owee_panel.py; sleep 0.7; setsid /usr/libexec/owee/owee-panel-run >/dev/null 2>&1 &"])

    def reset_copy(self):
        shutil.rmtree(DEST, ignore_errors=True); self.restart_panel(); self.msg.set_label(_("Copia borrada: OweeLinux usa la interfaz original.")); self.fill()

    def confirm_unlock(self):
        d = Gtk.AlertDialog(); d.set_message(_("¿Desbloquear /usr?")); d.set_detail(_("Podrás modificar archivos del sistema hasta el próximo reinicio. Al reiniciar se descartan todos los cambios. Pide la contraseña de administrador."))
        d.set_buttons([_("Cancelar"), _("Desbloquear")]); d.set_cancel_button(0); d.set_default_button(0)
        d.choose(self.b.get_root(), None, lambda dlg, res: self.do_unlock(dlg, res))

    def do_unlock(self, dlg, res):
        try:
            if dlg.choose_finish(res) != 1: return
        except GLib.Error: return
        run(["pkexec", "ostree", "admin", "unlock"], lambda out, code: (self.msg.set_label(_("/usr desbloqueado hasta el reinicio.") if code == 0 else _("No se pudo desbloquear (¿cancelaste la contraseña?).")), self.fill()), timeout=120)

    def show_log(self):
        term = next((t for t in ("foot", "konsole") if have(t)), None)
        if not term: self.msg.set_label(_("No hay ninguna terminal instalada.")); return
        try: Gio.Subprocess.new([term, "-e", "sh", "-c", "journalctl -b -p err --no-pager | less -R; echo; read -p 'Intro para cerrar' x"] if term == "foot" else [term, "-e", "sh", "-c", "journalctl -b -p err --no-pager | less -R"], Gio.SubprocessFlags.NONE)
        except GLib.Error as e: self.msg.set_label(str(e))

PAGE = Desarrollo()
