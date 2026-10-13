"""Atajos de teclado: lista de los atajos activos de labwc (rc.xml del usuario o, si no existe, el del sistema). Solo lectura por ahora: para cambiarlos se edita ~/.config/labwc/rc.xml."""
import os, xml.etree.ElementTree as ET
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, row
from . import rcxml

NICE = {"W": "Super", "A": "Alt", "C": "Ctrl", "S": "Mayús", "Return": "Intro", "space": "Espacio", "Print": "Impr. Pant."}
def pretty(k): return " + ".join(NICE.get(p, p) for p in k.replace("XF86", "").split("-"))
def describe(act):
    n = act.get("name"); c = act.get("command", "")
    if n == "Execute":
        for key, txt in (("action org.oweelinux.PanelPrototype launcher", "Abrir el lanzador"), ("action org.oweelinux.PanelPrototype calendar", "Abrir el calendario"), ("foot", "Terminal"), ("dolphin", "Archivos"), ("swaylock", "Bloquear la pantalla"),
                         ("grim -g", "Captura de una zona"), ("grim", "Captura de pantalla"), ("set-volume", "Volumen"), ("set-mute", "Silenciar"), ("brightnessctl", "Brillo")):
            if key in c: return txt + (" ↑" if "5%+" in c else " ↓" if "5%-" in c else "")
        return "Ejecutar: " + c[:40]
    return {"Close": "Cerrar ventana", "ToggleMaximize": "Maximizar / restaurar", "SnapToEdge": "Acoplar al lado", "NextWindow": "Siguiente ventana", "Exit": "Cerrar sesión"}.get(n, n)

class Atajos(Page):
    title = "Atajos de teclado"; icon = "owee-set-shortcuts"; group = "Sistema"; order = 30; keywords = "teclas combinaciones super"
    def build(self, app):
        b = page_box("Atajos de teclado", "Para cambiarlos, edita ~/.config/labwc/rc.xml (se aplican al guardar con `labwc --reconfigure`).")
        try: root = ET.parse(rcxml.USER if os.path.exists(rcxml.USER) else rcxml.SYSTEM).getroot()
        except (OSError, ET.ParseError): root = None
        if root is not None:
            for kb in root.iter("keybind"):
                acts = [describe(a) for a in kb.findall("action")]
                if acts: b.append(row(" · ".join(acts), Gtk.Label(label=pretty(kb.get("key", "")), css_classes=["heading"])))
        b.append(row("Cambiar de ventana", Gtk.Label(label="Alt + Tab"))); b.append(row("Mover / redimensionar con el ratón", Gtk.Label(label="Alt + arrastrar")))
        return scrolled(b)
PAGE = Atajos()
