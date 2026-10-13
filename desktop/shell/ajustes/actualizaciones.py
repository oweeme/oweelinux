"""Actualizaciones (ostree): qué versión corre, cuál está confirmada, y buscar/instalar la siguiente o volver a la anterior. Instalar y volver atrás necesitan permisos
de administrador (pkexec); el arranque «a prueba» y el rollback automático siguen funcionando igual que desde la terminal (owee-update, owee-rollback)."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, run, have

class Actualizaciones(Page):
    title = "Actualizaciones"; icon = "owee-set-update"; group = "Sistema"; order = 80; keywords = "actualizar versión rollback volver atrás ostree"
    def build(self, app):
        self.b = page_box("Actualizaciones", "El sistema se actualiza por versiones completas: si una versión nueva no arranca bien, el equipo vuelve solo a la anterior.")
        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); self.b.append(self.card); self.msg = Gtk.Label(xalign=0, wrap=True)
        up = Gtk.Button(label="Buscar e instalar actualizaciones", halign=Gtk.Align.START); up.connect("clicked", lambda b: self.go(["pkexec", "owee-update"], "Buscando… (puede tardar)"))
        rb = Gtk.Button(label="Volver a la versión anterior…", halign=Gtk.Align.START); rb.connect("clicked", lambda b: self.go(["pkexec", "owee-rollback"], "Volviendo a la versión anterior…"))
        self.b.append(up); self.b.append(rb); self.b.append(self.msg); self.refresh(); return scrolled(self.b)
    def go(self, cmd, text):
        self.msg.set_text(text); run(cmd, lambda o, c: (self.msg.set_text((o.strip() or "Listo.") + ("" if c == 0 else f"  (código {c}: ¿cancelaste la contraseña o falta permiso?)")), self.refresh()), timeout=600)
    def refresh(self):
        if not hasattr(self, "card"): return
        run(["owee-status"], self.on_status)
    def on_status(self, out, code):
        while (c := self.card.get_first_child()): self.card.remove(c)
        d = dict(l.split("=", 1) for l in out.splitlines() if "=" in l)
        if code != 0 or not d: self.card.append(Gtk.Label(label="No se pudo leer el estado del sistema (¿no es una instalación ostree o falta permiso?).", xalign=0, wrap=True)); return
        ok = d.get("booted") == d.get("confirmed") and d.get("trial", "0") == "0"
        for k, v in (("Versión en uso", d.get("booted", "?")), ("Última confirmada", d.get("confirmed", "?")), ("Publicación", d.get("release", "?") or "?"), ("Estado", "estable ✓" if ok else "a prueba (se confirma si el sistema queda sano)")):
            self.card.append(row(k, Gtk.Label(label=v, selectable=True, css_classes=["ok"] if (k == "Estado" and ok) else [])))
PAGE = Actualizaciones()
