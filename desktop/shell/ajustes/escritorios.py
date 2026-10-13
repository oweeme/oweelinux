"""Escritorios: cuántos escritorios virtuales hay, rueda del ratón sobre el fondo y esquinas activas (qué hace cada esquina de la pantalla al llevar el puntero)."""
import xml.etree.ElementTree as ET
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, dropdown, switch
from . import rcxml

ACTIONS = [("none", "Ninguna"), ("overview", "Vista general (todas las ventanas)"), ("next", "Escritorio siguiente"), ("prev", "Escritorio anterior"),
           ("launcher", "Abrir el lanzador de apps"), ("calendar", "Abrir el calendario"), ("lock", "Bloquear la pantalla"), ("capture", "Capturar la pantalla")]
CORNERS = [("tl", "Esquina superior izquierda"), ("tr", "Esquina superior derecha"), ("bl", "Esquina inferior izquierda"), ("br", "Esquina inferior derecha")]
OWEE = "/usr/libexec/owee/owee-desktop"

def wheel_on():
    def has(root):
        ctx = rcxml.find(root, "mouse/context[name=Root]")
        return ctx is not None and any(mb.get("action") == "Scroll" for mb in ctx)
    import os
    try: return has(rcxml._parse(rcxml.USER if os.path.exists(rcxml.USER) else rcxml.SYSTEM).getroot())
    except Exception: return False

def set_wheel(on):
    def fn(root):
        mouse = rcxml.find(root, "mouse", create=True); ctx = rcxml.find(root, "mouse/context[name=Root]")
        if ctx is not None: mouse.remove(ctx)
        if on:
            ctx = ET.SubElement(mouse, "context", {"name": "Root"})
            for btn, d, to in (("Up", "Up", "left"), ("Down", "Down", "right")):
                mb = ET.SubElement(ctx, "mousebind", {"button": btn, "direction": d, "action": "Scroll"})
                ET.SubElement(mb, "action", {"name": "Execute", "command": f"{OWEE} {to}"}); ET.SubElement(mb, "action", {"name": "GoToDesktop", "to": to})
    rcxml.edit(fn)

class Escritorios(Page):
    title = "Escritorios"; icon = "owee-set-desktops"; group = "Personal"; order = 30; keywords = "esquinas activas escritorios virtuales vista general ventanas espacios de trabajo"
    def build(self, app):
        self.app = app; b = page_box("Escritorios y esquinas", "Varios escritorios para ordenar tus ventanas. Atajos: Super+1…4 (ir), Super+Mayús+1…4 (mover la ventana), Ctrl+Alt+←/→, Super+Tab (vista general).")
        b.append(heading("Escritorios virtuales"))
        n = rcxml.get("desktops/number", default="4") or "4"
        b.append(row("Cantidad de escritorios", dropdown([(str(i), str(i)) for i in range(1, 10)], n, lambda k: rcxml.set_values([("desktops/number", k)])), "El panel muestra un punto por escritorio; clic en uno para ir a él"))
        b.append(row("Cambiar de escritorio con la rueda del ratón sobre el fondo", switch(wheel_on(), set_wheel)))
        b.append(heading("Esquinas activas")); cur = app.cfg.get("corners", {})
        for k, name in CORNERS:
            b.append(row(name, dropdown(ACTIONS, cur.get(k, "none"), lambda a, k=k: self.set_corner(k, a))))
        b.append(Gtk.Label(label="Lleva el puntero a la esquina y espera un instante. Para repetir, sal de la esquina y vuelve a entrar.", xalign=0, wrap=True, css_classes=["dim-label"]))
        return scrolled(b)
    def set_corner(self, k, action):
        c = dict(self.app.cfg.get("corners", {})); c[k] = action; self.app.change(corners=c)
PAGE = Escritorios()
