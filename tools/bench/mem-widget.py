#!/usr/bin/env python3
"""Mide la memoria (Rss y Pss, en MB) de una ventana mínima GTK3 con PyGObject y un reloj.
Pss reparte las librerías compartidas entre los procesos que las usan: es la cifra honesta."""
import gi, os, sys
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

def mem():
    d = {}
    for l in open(f"/proc/{os.getpid()}/smaps_rollup"):
        k, _, v = l.partition(":")
        if k in ("Rss", "Pss", "Pss_Anon"): d[k] = int(v.split()[0]) / 1024
    return d

w = Gtk.Window(title="mem-test"); lbl = Gtk.Label(label="--:--"); w.add(lbl); w.set_default_size(300, 30)
GLib.timeout_add_seconds(1, lambda: (lbl.set_text(GLib.DateTime.new_now_local().format("%H:%M:%S")), True)[1])
res = {}
def report():
    res.update(mem()); Gtk.main_quit(); return False
GLib.timeout_add_seconds(4, report)
w.show_all(); Gtk.main()
print("python+GTK3 reloj: Rss=%.0f MB  Pss=%.0f MB (Pss_Anon=%.0f MB)" % (res["Rss"], res["Pss"], res["Pss_Anon"]))
