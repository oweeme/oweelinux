#!/usr/bin/env python3
"""Plantilla "hola mundo" de una app de OweeLinux: Python + GTK4 + libadwaita."""
import gi
gi.require_version("Gtk", "4.0"); gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.oweelinux.HolaMundo")

    def do_activate(self):
        win = Adw.ApplicationWindow(application=self, title="Hola OweeLinux", default_width=360, default_height=200)
        boton = Gtk.Button(label="Hola, mundo")
        boton.connect("clicked", lambda b: b.set_label("¡Funciona!"))
        win.set_content(boton)
        win.present()


App().run()
