"""Ratón y touchpad (libinput, vía rc.xml de labwc): velocidad, aceleración, desplazamiento natural, tocar para hacer clic, zurdos. Se aplican al instante."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, dropdown, switch, slider, Debounce
from . import rcxml
from owee_i18n import _

def yn(v): return "yes" if v else "no"

class Raton(Page):
    title = _("Ratón y touchpad"); icon = "owee-set-mouse"; group = "Dispositivos"; order = 40; keywords = _("puntero velocidad desplazamiento natural tap clic zurdo")
    def build(self, app):
        self.deb = Debounce(300); b = page_box(_("Ratón y touchpad"), _("Se aplican al instante. Los cambios no afectan a los atajos de teclado ni al resto de la configuración de labwc."))
        for cat, titulo, dev in (("mouse", _("Ratón"), "device"), ("touchpad", _("Touchpad"), "device[category=touchpad]")):
            b.append(heading(titulo))
            g = lambda k, d="", dev=dev: rcxml.get(f"libinput/{dev}/{k}", default=d)
            put = lambda k, v, dev=dev: rcxml.set_values([(f"libinput/{dev}/{k}", v)])
            speed = float(g("pointerSpeed", "0") or 0)
            b.append(row(_("Velocidad del puntero"), slider(-1, 1, speed, lambda v, put=put: self.deb(lambda: put("pointerSpeed", f"{v:.2f}")), step=0.05, width=260)))
            b.append(row(_("Aceleración"), dropdown([("adaptive", _("Adaptativa (normal)")), ("flat", _("Plana (sin aceleración)"))], g("accelProfile", "adaptive"), lambda k, put=put: put("accelProfile", k))))
            b.append(row(_("Desplazamiento natural"), switch(g("naturalScroll") == "yes", lambda on, put=put: put("naturalScroll", yn(on))), _("El contenido sigue a los dedos, como en un móvil")))
            b.append(row(_("Botones invertidos (zurdos)"), switch(g("leftHanded") == "yes", lambda on, put=put: put("leftHanded", yn(on)))))
            if cat == "touchpad":
                b.append(row(_("Tocar para hacer clic"), switch(g("tap", "yes") == "yes", lambda on, put=put: put("tap", yn(on)))))
                b.append(row(_("Desactivar al escribir"), switch(g("disableWhileTyping", "yes") == "yes", lambda on, put=put: put("disableWhileTyping", yn(on)))))
        return scrolled(b)

PAGE = Raton()
