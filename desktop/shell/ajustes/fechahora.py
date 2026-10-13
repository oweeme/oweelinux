"""Fecha y hora: formato del reloj del panel (24 h / 12 h, mostrar segundos y fecha) y zona horaria (timedatectl; cambiarla pide permisos de administrador)."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, dropdown, switch, run, have

class FechaHora(Page):
    title = "Fecha y hora"; icon = "owee-set-clock"; group = "Sistema"; order = 10; keywords = "reloj zona horaria 24 horas calendario"
    def build(self, app):
        self.app = app; c = app.cfg; b = page_box("Fecha y hora"); b.append(heading("Reloj del panel"))
        b.append(row("Formato de hora", dropdown([("24", "24 horas"), ("12", "12 horas (a. m. / p. m.)")], str(c.get("clock_hours", "24")), lambda k: app.change(clock_hours=k))))
        b.append(row("Mostrar segundos", switch(bool(c.get("clock_seconds", False)), lambda on: app.change(clock_seconds=on))))
        b.append(row("Mostrar la fecha junto a la hora", switch(bool(c.get("clock_date", True)), lambda on: app.change(clock_date=on))))
        b.append(heading("Zona horaria")); self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); b.append(self.holder)
        if have("timedatectl"): run(["timedatectl", "show", "-p", "Timezone", "-p", "NTP", "-p", "NTPSynchronized", "--value"], self.on_tz)
        return scrolled(b)
    def on_tz(self, out, code):
        v = out.split(); tz = v[0] if v else "?"
        self.holder.append(row("Zona horaria actual", Gtk.Label(label=tz)))
        if len(v) > 1: self.holder.append(row("Sincronizar la hora por internet", Gtk.Label(label="activado" if v[1] == "yes" else "desactivado")))
        region = Gtk.Entry(placeholder_text="America/La_Paz", text=""); region.set_width_chars(28)
        region.connect("activate", lambda e: run(["timedatectl", "set-timezone", e.get_text().strip()], lambda o, c: self.msg.set_text("Zona horaria cambiada." if c == 0 else "No se pudo cambiar (¿nombre válido y permisos de administrador?).")))
        self.holder.append(row("Cambiar zona (Intro)", region, "Ejemplos: America/La_Paz, America/Lima, Europe/Madrid. Pide la contraseña de administrador.")); self.msg = Gtk.Label(xalign=0); self.holder.append(self.msg)
PAGE = FechaHora()
