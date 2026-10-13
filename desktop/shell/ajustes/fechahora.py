"""Fecha y hora: formato del reloj del panel (24 h / 12 h, mostrar segundos y fecha) y zona horaria (timedatectl; cambiarla pide permisos de administrador)."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, dropdown, switch, run, have
from owee_i18n import _

class FechaHora(Page):
    title = _("Fecha y hora"); icon = "owee-set-clock"; group = "Sistema"; order = 10; keywords = _("reloj zona horaria 24 horas calendario")
    def build(self, app):
        self.app = app; c = app.cfg; b = page_box(_("Fecha y hora")); b.append(heading(_("Reloj del panel")))
        b.append(row(_("Formato de hora"), dropdown([("24", _("24 horas")), ("12", _("12 horas (a. m. / p. m.)"))], str(c.get("clock_hours", "24")), lambda k: app.change(clock_hours=k))))
        b.append(row(_("Mostrar segundos"), switch(bool(c.get("clock_seconds", False)), lambda on: app.change(clock_seconds=on))))
        b.append(row(_("Mostrar la fecha junto a la hora"), switch(bool(c.get("clock_date", True)), lambda on: app.change(clock_date=on))))
        b.append(heading(_("Zona horaria"))); self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); b.append(self.holder)
        if have("timedatectl"): run(["timedatectl", "show", "-p", "Timezone", "-p", "NTP", "-p", "NTPSynchronized", "--value"], self.on_tz)
        return scrolled(b)
    def on_tz(self, out, code):
        v = out.split(); tz = v[0] if v else "?"
        self.holder.append(row(_("Zona horaria actual"), Gtk.Label(label=tz, selectable=True)))
        if len(v) > 1: self.holder.append(row(_("Sincronizar la hora por internet"), Gtk.Label(label="activado" if v[1] == "yes" else "desactivado")))
        self.msg = Gtk.Label(xalign=0); self.zones = Gtk.StringList()
        self.dd = Gtk.DropDown(model=self.zones, enable_search=True, expression=Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"))
        try: self.dd.set_search_match_mode(Gtk.StringFilterMatchMode.SUBSTRING)          # buscar «La_Paz» dentro de «America/La_Paz» (por defecto solo busca por el principio; GTK ≥ 4.12)
        except AttributeError: pass
        self.dd.set_size_request(260, -1); self.cur_tz = tz; self.loading_tz = True
        self.holder.append(row(_("Cambiar zona horaria"), self.dd, _("Escribe para buscar (por ejemplo «La_Paz»). Pide la contraseña de administrador."))); self.holder.append(self.msg)
        self.dd.connect("notify::selected", self.on_pick)
        run(["timedatectl", "list-timezones"], self.on_list)
    def on_list(self, out, code):
        names = [l.strip() for l in out.splitlines() if l.strip()]
        for n in names: self.zones.append(n)
        if self.cur_tz in names: self.dd.set_selected(names.index(self.cur_tz))
        self.loading_tz = False
    def on_pick(self, dd, _p):
        if self.loading_tz: return
        item = dd.get_selected_item()
        if not item: return
        z = item.get_string()
        if z == self.cur_tz: return
        self.msg.set_text(_("Cambiando…"))
        run(["timedatectl", "set-timezone", z], lambda o, c: (self.msg.set_text(_('Zona horaria: {0}', z) if c == 0 else _("No se pudo cambiar (¿cancelaste la contraseña?).")), setattr(self, "cur_tz", z if c == 0 else self.cur_tz)), timeout=60)
PAGE = FechaHora()
