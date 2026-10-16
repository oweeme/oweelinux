#!/usr/bin/env python3
"""Antes de abrir Calamares: si en este equipo ya hay un OweeLinux con datos (otra partición que el medio de instalación), ofrece REINSTALAR / REPARAR CONSERVANDO archivos, usuarios y aplicaciones
(owee-reinstall) o BORRAR EL DISCO e instalar de cero (Calamares). Si no hay ninguno, termina al instante sin mostrar nada. Después (si borras el disco o no había OweeLinux) y si hay otras particiones ext4 en otros discos, pregunta si una de ellas debe ser tu /home (se conserva sin formatear; ver owee-install-deploy).
Códigos de salida: 0 = seguir con Calamares, 20 = ya reinstalado (se reinicia)."""
import os, sys
for d in ("/usr/libexec/owee", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shell")): sys.path.insert(0, d)
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio, GLib
from owee_i18n import _
import owee_config

BASE = os.path.dirname(os.path.abspath(__file__))
def tool(n):
    for p in ("/usr/libexec/owee/installer/" + n, os.path.join(BASE, n)):
        if os.path.exists(p): return p
    return n

CSS = """window.background { background: @win@; color: @fg@; } .t1 { font-size: 22pt; font-weight: bold; } .sub { color: @dim@; } .card { background: @pop@; border-radius: 12px; padding: 14px; }
button { background-image: none; background-color: @key@; color: @fg@; box-shadow: none; padding: 8px 18px; border-color: transparent; } button:hover { background-color: @keyh@; }
button.suggested-action { background-color: @accent@; color: @on@; } button.danger { color: #F06548; } .bad { color: #F06548; } textview, textview text { background: @entry@; color: @fg@; }"""

class Choice(Gtk.Application):
    def __init__(self): super().__init__(application_id="org.oweelinux.InstallChoice", flags=Gio.ApplicationFlags.NON_UNIQUE); self.rc = 0

    def do_activate(self):
        pal = owee_config.palette(owee_config.load()); css = CSS
        for k in ("win", "fg", "pop", "entry", "key", "keyh", "dim"): css = css.replace("@%s@" % k, pal[k])
        css = css.replace("@accent@", pal["accent"]).replace("@on@", pal["on"])
        prov = Gtk.CssProvider(); prov.load_from_string(css); Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", pal["mode"] == "dark"); Gtk.Settings.get_default().set_property("gtk-icon-theme-name", pal["icons"])
        self.hold()
        try: p = Gio.Subprocess.new(["pkexec", tool("owee-installer-scan")], Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE); p.communicate_utf8_async(None, None, self.scanned)
        except GLib.Error: self.release()

    def scanned(self, p, res):
        try: _ok, out, _e = p.communicate_utf8_finish(res)
        except GLib.Error: out = ""
        self.found = [l.split("|") for l in (out or "").splitlines() if l.count("|") == 2]
        try: q = Gio.Subprocess.new(["pkexec", tool("owee-installer-scan"), "--homes"], Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE); q.communicate_utf8_async(None, None, self.scanned_homes)
        except GLib.Error: self.homes = []; self.next_step()

    def scanned_homes(self, p, res):
        try: _ok, out, _e = p.communicate_utf8_finish(res)
        except GLib.Error: out = ""
        self.homes = [l.split("|") for l in (out or "").splitlines() if l.count("|") == 4]
        self.next_step()

    def next_step(self):
        if self.found: self.show(self.found)
        elif self.homes: self.show_homes()
        else: self.release()                                       # nada que preguntar: directo a Calamares

    def after_erase(self):
        if self.homes: self.show_homes()
        else: self.rc = 0; self.quit()

    def show_homes(self):
        if getattr(self, "win", None): self.win.close()
        win = self.win = Gtk.ApplicationWindow(application=self, title=_("Instalar OweeLinux"), default_width=720, default_height=520)
        if not os.environ.get("OWEE_CHOICE_WINDOWED"): win.fullscreen()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, width_request=600); win.set_child(box)
        box.append(Gtk.Image(icon_name="owee-logo", pixel_size=96))
        box.append(Gtk.Label(label=_("¿Dónde va tu carpeta personal (/home)?"), css_classes=["t1"], xalign=0))
        box.append(Gtk.Label(label=_("Puedes usar una partición que ya tiene tus archivos: se conserva tal cual (no se formatea). Ese disco no se podrá elegir para instalar el sistema."), wrap=True, xalign=0, css_classes=["sub"]))
        opts = [(_("Dentro del mismo disco que el sistema (lo normal)"), "none")] + [(f"{d}  ·  {sz}" + (f"  ·  {lb}" if lb else "") + (f"  ·  {dirs.strip()}" if dirs.strip() else ""), uuid) for d, sz, lb, uuid, dirs in self.homes]
        self.dd = Gtk.DropDown.new_from_strings([o[0] for o in opts]); self.hopts = opts; box.append(self.dd)
        go = Gtk.Button(label=_("Continuar"), css_classes=["suggested-action"]); go.connect("clicked", lambda _b: self.save_home()); box.append(go)
        self.out = Gtk.Label(wrap=True, xalign=0, css_classes=["sub"]); box.append(self.out); win.present()

    def save_home(self):
        uuid = self.hopts[self.dd.get_selected()][1]
        try: p = Gio.Subprocess.new(["pkexec", tool("owee-installer-sethome"), uuid], Gio.SubprocessFlags.STDERR_SILENCE); p.wait_async(None, lambda pr, res: (pr.wait_finish(res), setattr(self, "rc", 0), self.quit()))
        except GLib.Error as e: self.out.set_text(str(e))

    def show(self, found):
        win = self.win = Gtk.ApplicationWindow(application=self, title=_("Instalar OweeLinux"), default_width=720, default_height=520)
        if not os.environ.get("OWEE_CHOICE_WINDOWED"): win.fullscreen()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, width_request=600); win.set_child(box)
        box.append(Gtk.Image(icon_name="owee-logo", pixel_size=96))
        box.append(Gtk.Label(label=_("Ya hay un OweeLinux en este equipo"), css_classes=["t1"], xalign=0))
        box.append(Gtk.Label(label=_("Puedes reinstalar el sistema conservando tus archivos, usuarios y aplicaciones, o borrar el disco y empezar de cero."), wrap=True, xalign=0, css_classes=["sub"]))
        self.out = Gtk.Label(wrap=True, xalign=0, css_classes=["sub"], selectable=False)
        for dev, size, users in found:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, css_classes=["card"])
            card.append(Gtk.Label(label=f"{dev}  ·  {size}" + ("  ·  " + _("usuarios: {0}", users.strip()) if users.strip() else ""), xalign=0))
            b = Gtk.Button(label=_("Reinstalar conservando mis archivos y aplicaciones"), css_classes=["suggested-action"]); b.connect("clicked", lambda _b, d=dev: self.reinstall(d)); card.append(b); box.append(card)
        self.erase = Gtk.Button(label=_("Borrar el disco e instalar de cero")); self.erase.add_css_class("danger"); self.erase.connect("clicked", lambda _b: self.after_erase()); box.append(self.erase)
        box.append(self.out); win.present()

    def reinstall(self, dev):
        self.out.remove_css_class("bad"); self.out.set_text(_("Reinstalando… (unos minutos; no apagues el equipo)")); self.erase.set_sensitive(False)
        for c in self.win.get_child(): 
            if isinstance(c, Gtk.Box): c.set_sensitive(False)
        try: p = Gio.Subprocess.new(["pkexec", tool("owee-reinstall"), dev], Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE)
        except GLib.Error as e: self.fail(str(e)); return
        p.communicate_utf8_async(None, None, self.done)

    def done(self, p, res):
        try: _ok, out, _e = p.communicate_utf8_finish(res)
        except GLib.Error as e: self.fail(str(e)); return
        if p.get_exit_status() == 0:
            self.out.set_text(_("Listo. Reiniciando…")); GLib.timeout_add_seconds(3, lambda: (Gio.Subprocess.new(["systemctl", "reboot"], Gio.SubprocessFlags.NONE), False)[1]); self.rc = 20
        else: self.fail((out or "").strip().splitlines()[-1] if out and out.strip() else "?")

    def fail(self, msg):
        self.out.add_css_class("bad"); self.out.set_text(_("No se pudo: {0}", msg[:200])); self.erase.set_sensitive(True)
        for c in self.win.get_child(): 
            if isinstance(c, Gtk.Box): c.set_sensitive(True)

if __name__ == "__main__":
    a = Choice(); a.run(sys.argv); sys.exit(a.rc)
