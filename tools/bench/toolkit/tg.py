import os, sys, gi
sys.path.insert(0, "/tmp/m"); from mem import report
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
hold = int(os.environ.get("HOLD", "0"))
app = Gtk.Application(application_id="org.t.g%d" % os.getpid())
def act(a):
    w = Gtk.ApplicationWindow(application=a); w.set_default_size(300, 40); w.set_child(Gtk.Label(label="hola")); w.present()
    def done():
        report(os.environ.get("TAG", "gtk4"))
        if hold: GLib.timeout_add_seconds(hold, a.quit)
        else: a.quit()
        return False
    GLib.timeout_add_seconds(6, done)
app.connect("activate", act); app.run()
