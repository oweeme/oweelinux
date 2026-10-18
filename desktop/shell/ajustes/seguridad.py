"""Seguridad: cortafuegos (bloquea lo entrante; se pueden abrir puertos) y Centinela, un señuelo de red pasivo que avisa —y si quieres bloquea— a quien escanee tu equipo.
Todo lo que cambia el sistema pasa por pkexec (owee-firewall, owee-centinela-ctl) y pide la contraseña de administrador."""
import json, re, time
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, switch, run, have
from owee_i18n import _

FW = "/usr/libexec/owee/owee-firewall"; CT = "/usr/libexec/owee/owee-centinela-ctl"

class Seguridad(Page):
    title = _("Seguridad"); icon = "owee-set-access"; group = "Sistema"; order = 70; keywords = _("cortafuegos firewall puertos centinela honeypot señuelo escaneo intrusos bloquear")
    def build(self, app):
        self.b = page_box(_("Seguridad"), _("El cortafuegos bloquea todo lo que llega desde fuera, salvo lo que tú abras. Navegar, actualizar y compartir internet siguen igual."))
        self.loading = False; self.msg = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"])
        self.b.append(heading(_("Cortafuegos")))
        self.fw_sw = switch(True, lambda on: not self.loading and self.admin([FW, "on" if on else "off"]))
        self.b.append(row(_("Bloquear lo entrante"), self.fw_sw, _("Recomendado. Con él apagado, cualquier servicio que abras en tu equipo es visible en la red")))
        self.ports = Gtk.Label(xalign=0, wrap=True, selectable=True); self.b.append(row(_("Puertos abiertos"), self.ports))
        add = Gtk.Box(spacing=6); self.entry = Gtk.Entry(placeholder_text=_("Puerto, p. ej. 22/tcp"), width_chars=18); ob = Gtk.Button(label=_("Abrir")); cb = Gtk.Button(label=_("Cerrar"))
        ob.connect("clicked", lambda b: self.port("allow")); cb.connect("clicked", lambda b: self.port("deny")); add.append(self.entry); add.append(ob); add.append(cb); self.b.append(add)
        self.b.append(heading(_("Centinela (señuelo de red)")))
        self.b.append(Gtk.Label(label=_("Escucha en puertos que nadie legítimo usa. Si alguien los prueba (un escaneo), te avisa y lo anota. No ejecuta nada de lo que recibe: no hay ningún servicio detrás. Útil sobre todo en wifis públicas."), xalign=0, wrap=True, css_classes=["dim-label"]))
        self.ct_sw = switch(False, lambda on: not self.loading and self.admin([CT, "on" if on else "off"]))
        self.b.append(row(_("Activar Centinela"), self.ct_sw))
        self.ab_sw = switch(True, lambda on: not self.loading and self.admin([CT, "autoblock", "on" if on else "off"]))
        self.b.append(row(_("Bloquear automáticamente a quien escanee"), self.ab_sw, _("Durante una hora; nunca bloquea tu router")))
        self.events = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2); self.b.append(heading(_("Últimos intentos"))); self.b.append(self.events)
        clr = Gtk.Button(label=_("Borrar el registro"), halign=Gtk.Align.START); clr.connect("clicked", lambda b: self.admin([CT, "clear"])); self.b.append(clr)
        self.b.append(self.msg); self.refresh(); return scrolled(self.b)

    def admin(self, cmd):
        self.msg.set_text(_("Pidiendo permiso…"))
        run(["pkexec"] + cmd, lambda out, code: (self.msg.set_text(_("Hecho.") if code == 0 else _("No se pudo (¿cancelaste la contraseña?).")), self.refresh()), timeout=60)

    def port(self, what):
        p = self.entry.get_text().strip().lower()
        if not re.fullmatch(r"\d{1,5}/(tcp|udp)", p): self.msg.set_text(_("Escribe el puerto así: 22/tcp o 5353/udp.")); return
        self.entry.set_text(""); self.admin([FW, what, p])

    def refresh(self):
        if not hasattr(self, "ports"): return
        run([FW, "status"], self.on_fw); run([CT, "status"], self.on_ct); run([CT, "events", "12"], self.on_events)

    def on_fw(self, out, code):
        d = dict(l.split("=", 1) for l in out.splitlines() if "=" in l)
        self.loading = True; self.fw_sw.set_active(d.get("estado") == "activo"); self.loading = False; self.ports.set_text(d.get("permitidos", "").strip() or _("ninguno"))

    def on_ct(self, out, code):
        d = dict(l.split("=", 1) for l in out.splitlines() if "=" in l)
        self.loading = True; self.ct_sw.set_active(d.get("activo") == "active"); self.ab_sw.set_active(d.get("bloqueo", "1") != "0"); self.loading = False

    def on_events(self, out, code):
        while (c := self.events.get_first_child()): self.events.remove(c)
        evs = []
        for l in out.splitlines():
            try: evs.append(json.loads(l))
            except ValueError: pass
        if not evs: self.events.append(Gtk.Label(label=_("Ninguno todavía."), xalign=0, css_classes=["dim-label"])); return
        for e in reversed(evs):
            self.events.append(Gtk.Label(label=f"{time.strftime('%d/%m %H:%M:%S', time.localtime(e.get('t', 0)))}   {e.get('ip', '?')}  →  {e.get('port', '?')}", xalign=0, selectable=True))

PAGE = Seguridad()
