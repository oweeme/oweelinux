"""Bluetooth (BlueZ, con `bluetoothctl`): encender/apagar, ver los dispositivos conocidos, conectar, desconectar, olvidar y buscar nuevos para emparejarlos.
Ninguna orden se espera en el hilo de la interfaz (todas pasan por `run`, con límite de tiempo). Sin adaptador, la página lo dice y no hace nada más."""
import re
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from .base import Page, page_box, scrolled, heading, row, switch, run, have
from owee_i18n import _

DEV = re.compile(r"^Device\s+([0-9A-Fa-f:]{17})\s+(.*)$")

def parse_devices(text):
    """`bluetoothctl devices` → [(mac, nombre)]."""
    return [(m.group(1).upper(), m.group(2).strip()) for m in (DEV.match(l.strip()) for l in text.splitlines()) if m]

def parse_info(text):
    """`bluetoothctl info MAC` → {'Connected': True, 'Paired': True, 'Icon': 'audio-headset'…}."""
    d = {}
    for l in text.splitlines():
        k, _s, v = l.strip().partition(": ")
        if _s and k in ("Paired", "Connected", "Trusted", "Icon", "Alias"): d[k] = (v == "yes") if k in ("Paired", "Connected", "Trusted") else v
    return d

class Bluetooth(Page):
    title = _("Bluetooth"); icon = "owee-set-bluetooth"; group = "Dispositivos"; order = 15; keywords = _("bluetooth auriculares ratón teclado emparejar inalámbrico")
    def build(self, app):
        self.b = page_box(_("Bluetooth"), _("Auriculares, ratones, teclados y altavoces inalámbricos."))
        self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); self.b.append(self.holder); self.busy = False; self.scanning = False
        if not have("bluetoothctl"): self.holder.append(Gtk.Label(label=_("No se encontró `bluetoothctl` (BlueZ)."), xalign=0)); return scrolled(self.b)
        return scrolled(self.b)

    def refresh(self):
        if hasattr(self, "holder") and have("bluetoothctl") and not self.busy: run(["bluetoothctl", "show"], self.on_show)

    def clear(self):
        while (c := self.holder.get_first_child()): self.holder.remove(c)

    def on_show(self, out, code):
        self.clear()
        if code != 0 or "Powered:" not in out:
            self.holder.append(Gtk.Label(label=_("No se encontró ningún adaptador Bluetooth."), xalign=0)); return
        powered = "Powered: yes" in out; self.loading = True
        self.holder.append(row(_("Bluetooth"), switch(powered, lambda on: not self.loading and self.power(on)), _("Encendido, el equipo puede conectarse a dispositivos cercanos")))
        self.loading = False
        if not powered: return
        self.holder.append(heading(_("Dispositivos")))
        self.list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); self.holder.append(self.list)
        self.scan_btn = Gtk.Button(label=_("Buscar dispositivos"), halign=Gtk.Align.START); self.scan_btn.connect("clicked", lambda _b: self.scan()); self.holder.append(self.scan_btn)
        self.status = Gtk.Label(xalign=0, css_classes=["dim-label"]); self.holder.append(self.status); self.load_devices()

    def power(self, on):
        run(["bluetoothctl", "power", "on" if on else "off"], lambda *a: GLib.timeout_add(400, lambda: (self.refresh(), False)[1]), timeout=8)

    def load_devices(self):
        run(["bluetoothctl", "devices"], self.on_devices)

    def on_devices(self, out, code):
        devs = parse_devices(out); self.entries = {}
        while (c := self.list.get_first_child()): self.list.remove(c)
        if not devs: self.list.append(Gtk.Label(label=_("Todavía no hay dispositivos. Pulsa «Buscar dispositivos» con el tuyo en modo de emparejamiento."), xalign=0, wrap=True, css_classes=["dim-label"]))
        for mac, name in devs:
            r = Gtk.Box(spacing=10, css_classes=["setrow"]); lab = Gtk.Label(label=name, xalign=0, hexpand=True); st = Gtk.Label(css_classes=["dim-label"]); act = Gtk.Button(label="…", sensitive=False)
            forget = Gtk.Button(label=_("Olvidar"), sensitive=False); forget.connect("clicked", lambda _b, m=mac: self.cmd(["remove", m], _("Dispositivo olvidado"))); r.append(lab); r.append(st); r.append(act); r.append(forget); self.list.append(r)
            self.entries[mac] = (st, act, forget); run(["bluetoothctl", "info", mac], lambda o, c, m=mac, n=name: self.fill(m, n, parse_info(o)))

    def fill(self, mac, name, info):
        st, act, forget = self.entries.get(mac, (None, None, None))
        if st is None: return
        conn, paired = info.get("Connected", False), info.get("Paired", False)
        st.set_text(_("Conectado") if conn else _("Emparejado") if paired else _("Disponible")); forget.set_sensitive(paired); act.set_sensitive(True)
        act.set_label(_("Desconectar") if conn else _("Conectar") if paired else _("Emparejar"))
        try: act.disconnect_by_func(act._h)
        except Exception: pass
        act._h = lambda _b: (self.cmd(["disconnect", mac], _("Desconectado")) if conn else self.pair(mac) if not paired else self.cmd(["connect", mac], _("Conectado")))
        act.connect("clicked", act._h)

    def pair(self, mac):
        self.say(_("Emparejando… (puede pedirte confirmar en el dispositivo)"))
        run(["bluetoothctl", "pair", mac], lambda o, c: run(["bluetoothctl", "trust", mac], lambda *a: self.cmd(["connect", mac], _("Emparejado y conectado") if c == 0 else _("No se pudo emparejar")), timeout=8), timeout=40)

    def cmd(self, argv, ok_text):
        self.say(_("Un momento…")); run(["bluetoothctl"] + argv, lambda o, c: (self.say(ok_text if c == 0 else _("No se pudo: {0}", " ".join(argv[:1]))), self.load_devices()), timeout=25)

    def say(self, t):
        if hasattr(self, "status"): self.status.set_text(t)

    def scan(self):
        if self.scanning: return
        self.scanning = True; self.scan_btn.set_sensitive(False); self.say(_("Buscando… (10 s)"))
        run(["bluetoothctl", "--timeout", "10", "scan", "on"], lambda *a: (setattr(self, "scanning", False), self.scan_btn.set_sensitive(True), self.say(_("Búsqueda terminada")), self.load_devices()), timeout=15)
PAGE = Bluetooth()
