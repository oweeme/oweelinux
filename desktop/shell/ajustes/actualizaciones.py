"""Actualizaciones (ostree): qué versión corre, cuál está confirmada, y buscar/instalar la siguiente o volver a la anterior. Instalar y volver atrás necesitan permisos
de administrador (pkexec); el arranque «a prueba» y el rollback automático siguen funcionando igual que desde la terminal (owee-update, owee-rollback)."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, run, have
from owee_i18n import _

class Actualizaciones(Page):
    title = _("Actualizaciones"); icon = "owee-set-update"; group = "Sistema"; order = 80; keywords = _("actualizar versión rollback volver atrás ostree")
    def build(self, app):
        self.b = page_box(_("Actualizaciones"), _("El sistema se actualiza por versiones completas: si una versión nueva no arranca bien, el equipo vuelve solo a la anterior."))
        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); self.b.append(self.card); self.msg = Gtk.Label(xalign=0, wrap=True)
        up = Gtk.Button(label=_("Buscar e instalar actualizaciones"), halign=Gtk.Align.START); up.connect("clicked", lambda b: self.go(["pkexec", "owee-update"], _("Buscando… (puede tardar)")))
        rb = Gtk.Button(label=_("Volver a la versión anterior…"), halign=Gtk.Align.START); rb.connect("clicked", lambda b: self.go(["pkexec", "owee-rollback"], _("Volviendo a la versión anterior…")))
        self.b.append(up); self.b.append(rb); self.b.append(self.msg); self.refresh(); return scrolled(self.b)
    def go(self, cmd, text):
        self.msg.set_text(text); run(cmd, lambda o, c: (self.msg.set_text((o.strip() or _("Listo.")) + ("" if c == 0 else _('  (código {0}: ¿cancelaste la contraseña o falta permiso?)', c))), self.refresh()), timeout=600)
    def refresh(self):
        if not hasattr(self, "card"): return
        run(["owee-status"], self.on_status)
    def on_status(self, out, code):
        while (c := self.card.get_first_child()): self.card.remove(c)
        d = dict(l.split("=", 1) for l in out.splitlines() if "=" in l)
        if code != 0 or not d: self.card.append(Gtk.Label(label=_("No se pudo leer el estado del sistema (¿no es una instalación ostree o falta permiso?)."), xalign=0, wrap=True)); return
        ok = d.get("booted") == d.get("confirmed") and d.get("trial", "0") == "0"
        for k, v in ((_("Versión en uso"), d.get("booted", "?")), (_("Última confirmada"), d.get("confirmed", "?")), (_("Publicación"), d.get("release", "?") or "?"), (_("Estado"), _("estable ✓") if ok else _("a prueba (se confirma si el sistema queda sano)"))):
            self.card.append(row(k, Gtk.Label(label=v, selectable=True, css_classes=["ok"] if (k == _("Estado") and ok) else [])))
PAGE = Actualizaciones()
