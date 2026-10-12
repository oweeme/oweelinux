#!/usr/bin/env python3
# App FALSA con icono de bandeja (protocolo StatusNotifierItem) para pruebas: dibuja un cuadrado coral y anota en /tmp/sni.log los clics recibidos.
# Uso (con el bus de sesión): mock-sni.py
import struct
from gi.repository import Gio, GLib
XML = """<node><interface name="org.kde.StatusNotifierItem">
 <method name="Activate"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
 <method name="ContextMenu"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
 <property name="Category" type="s" access="read"/><property name="Id" type="s" access="read"/><property name="Title" type="s" access="read"/>
 <property name="Status" type="s" access="read"/><property name="IconName" type="s" access="read"/><property name="IconPixmap" type="a(iiay)" access="read"/>
 <signal name="NewIcon"/></interface></node>"""
W = 22; PIX = b"".join(struct.pack("BBBB", 255, 0xF0, 0x65, 0x48) for _ in range(W * W))      # ARGB: coral opaco
def log(t): open("/tmp/sni.log", "a").write(t + "\n")
def method(c, sender, path, iface, m, params, inv): log(m); inv.return_value(None)
def get(c, sender, path, iface, p):
    return {"Category": GLib.Variant("s", "ApplicationStatus"), "Id": GLib.Variant("s", "mock"), "Title": GLib.Variant("s", "App de prueba"), "Status": GLib.Variant("s", "Active"),
            "IconName": GLib.Variant("s", ""), "IconPixmap": GLib.Variant("a(iiay)", [(W, W, PIX)])}.get(p)
def bus(c, name):
    c.register_object("/StatusNotifierItem", Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0], method, get, None)
    c.call("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher", "org.kde.StatusNotifierWatcher", "RegisterStatusNotifierItem",
           GLib.Variant("(s)", (name,)), None, Gio.DBusCallFlags.NONE, 3000, None, lambda *a: log("registrado"))
Gio.bus_own_name(Gio.BusType.SESSION, "org.test.MockSni", Gio.BusNameOwnerFlags.NONE, bus, None, None)
GLib.MainLoop().run()
