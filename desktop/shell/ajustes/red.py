"""Red (NetworkManager, con `nmcli`): conexión por cable (conectar/desconectar, IP, puerta de enlace, DNS, IP manual), WiFi (encender, redes cercanas, conectar con clave, olvidar) y
compartir internet creando una red WiFi (punto de acceso). Todo es asíncrono y con límite de tiempo (`run`); sin NetworkManager lo dice y no hace nada más."""
import socket
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from .base import Page, page_box, scrolled, heading, row, dropdown, switch, run, have
from .usuarios import ask
from owee_i18n import _

def split(line):
    """Una línea de `nmcli -t` (campos separados por «:»; los «:» dentro de un campo van como «\\:») → lista de campos."""
    out, cur, esc = [], "", False
    for ch in line:
        if esc: cur += ch; esc = False
        elif ch == "\\": esc = True
        elif ch == ":": out.append(cur); cur = ""
        else: cur += ch
    return out + [cur]

def parse_devices(text):
    """`nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status` → [(dispositivo, tipo, estado, conexión)]."""
    return [tuple((split(l) + ["", "", "", ""])[:4]) for l in text.splitlines() if l.strip()]

def parse_wifi(text):
    """`nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY device wifi list` → [(en_uso, ssid, señal, seguridad)] sin repetidos ni redes ocultas, de más a menos señal."""
    seen, out = set(), []
    for l in text.splitlines():
        f = (split(l) + ["", "", "", ""])[:4]
        if not f[1] or f[1] in seen: continue
        seen.add(f[1]); out.append((f[0] == "*", f[1], int(f[2] or 0), f[3]))
    return sorted(out, key=lambda x: (not x[0], -x[2]))

class Red(Page):
    title = _("Red"); icon = "owee-set-network"; group = "Dispositivos"; order = 12; keywords = _("red wifi cable ethernet internet compartir punto de acceso ip dns")
    def build(self, app):
        self.app = app; self.b = page_box(_("Red"), _("Conexión por cable y WiFi, compartir internet y direcciones IP."))
        self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); self.b.append(self.holder)
        self.status = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); self.b.append(self.status)
        return scrolled(self.b)

    def say(self, t): self.status.set_text(t)

    def refresh(self):
        if not hasattr(self, "holder"): return
        if not have("nmcli"):
            while (c := self.holder.get_first_child()): self.holder.remove(c)
            self.holder.append(Gtk.Label(label=_("No se encontró `nmcli` (NetworkManager)."), xalign=0)); return
        run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"], self.on_devices)

    def clear(self):
        while (c := self.holder.get_first_child()): self.holder.remove(c)

    def on_devices(self, out, code):
        self.clear(); devs = parse_devices(out); eth = [d for d in devs if d[1] == "ethernet"]; wifi = [d for d in devs if d[1] == "wifi"]
        self.holder.append(heading(_("Cable")))
        if not eth: self.holder.append(Gtk.Label(label=_("No hay tarjeta de red por cable."), xalign=0, css_classes=["dim-label"]))
        for dev, _t, state, conn in eth: self.eth_row(dev, state, conn)
        self.holder.append(heading(_("WiFi")))
        if not wifi: self.holder.append(Gtk.Label(label=_("No hay tarjeta WiFi."), xalign=0, css_classes=["dim-label"])); return
        self.wdev = wifi[0][0]; run(["nmcli", "radio", "wifi"], lambda o, c: self.wifi_section(o.strip() == "enabled"))

    # ---- cable
    def eth_row(self, dev, state, conn):
        up = state.startswith("connected"); r = Gtk.Box(spacing=10, css_classes=["setrow"]); lab = Gtk.Label(label=f"{dev}  ·  " + (_("Conectado") if up else _("Desconectado")), xalign=0, hexpand=True); r.append(lab)
        if up:
            ip = Gtk.Button(label=_("Configurar IP…")); ip.connect("clicked", lambda _b, c=conn: self.ip_dialog(c)); r.append(ip)
        btn = Gtk.Button(label=_("Desconectar") if up else _("Conectar")); btn.connect("clicked", lambda _b: self.nm(["device", "disconnect" if up else "connect", dev])); r.append(btn)
        self.holder.append(r)
        if up:
            info = Gtk.Label(xalign=0, css_classes=["dim-label"], wrap=True); self.holder.append(info)
            run(["nmcli", "-t", "-g", "IP4.ADDRESS,IP4.GATEWAY,IP4.DNS", "device", "show", dev], lambda o, c, i=info: i.set_text("  ·  ".join(x for x in (
                _("Dirección: {0}", o.split("\n")[0].split("|")[0]) if o.split("\n")[0] else "", _("Puerta de enlace: {0}", o.split("\n")[1]) if len(o.split("\n")) > 1 and o.split("\n")[1] else "",
                _("DNS: {0}", o.split("\n")[2].replace("|", " ")) if len(o.split("\n")) > 2 and o.split("\n")[2] else "") if x)))

    def ip_dialog(self, conn):
        """IP automática (DHCP) o manual (dirección/prefijo, puerta de enlace y DNS) para la conexión activa."""
        win = Gtk.Window(title=_("Dirección IP"), modal=True, transient_for=self.b.get_root(), default_width=380, resizable=False)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=16, margin_bottom=16, margin_start=16, margin_end=16); win.set_child(box)
        mode = dropdown([("auto", _("Automática (DHCP)")), ("manual", _("Manual"))], "auto", lambda k: [e.set_sensitive(k == "manual") for e in ents]); box.append(mode)
        ents = []
        for label in (_("Dirección IP"), _("Prefijo de red"), _("Puerta de enlace"), _("Servidores DNS (separados por espacios)")):
            box.append(Gtk.Label(label=label, xalign=0)); e = Gtk.Entry(sensitive=False); box.append(e); ents.append(e)
        ents[1].set_text("24"); err = Gtk.Label(xalign=0, wrap=True, css_classes=["bad"]); box.append(err)
        bt = Gtk.Box(spacing=8, halign=Gtk.Align.END); cancel = Gtk.Button(label=_("Cancelar")); go = Gtk.Button(label=_("Guardar"), css_classes=["suggested-action"]); bt.append(cancel); bt.append(go); box.append(bt)
        cancel.connect("clicked", lambda _b: win.close())
        def save(*_a):
            sel = mode.get_selected()
            if sel == 0: argv = ["connection", "modify", conn, "ipv4.method", "auto", "ipv4.addresses", "", "ipv4.gateway", "", "ipv4.dns", ""]
            else:
                ip, pre, gw, dns = (e.get_text().strip() for e in ents)
                try: socket.inet_aton(ip); assert 1 <= int(pre) <= 32
                except (OSError, ValueError, AssertionError): err.set_text(_("No se pudo: {0}", _("Dirección IP"))); return
                argv = ["connection", "modify", conn, "ipv4.method", "manual", "ipv4.addresses", f"{ip}/{pre}", "ipv4.gateway", gw, "ipv4.dns", dns]
            win.close(); self.say(_("Un momento…")); run(["nmcli"] + argv, lambda o, c: run(["nmcli", "connection", "up", conn], lambda *a: self.refresh(), timeout=30), timeout=15)
        go.connect("clicked", save); win.present()

    # ---- WiFi
    def wifi_section(self, on):
        self.holder.append(row(_("WiFi"), switch(on, lambda v: run(["nmcli", "radio", "wifi", "on" if v else "off"], lambda *a: GLib.timeout_add(800, lambda: (self.refresh(), False)[1])))))
        if not on: return
        self.holder.append(heading(_("Redes cercanas"))); self.nets = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); self.holder.append(self.nets)
        scan = Gtk.Button(label=_("Buscar redes"), halign=Gtk.Align.START); scan.connect("clicked", lambda _b: self.scan()); self.holder.append(scan)
        self.hotspot_section(); self.scan(False)

    def scan(self, rescan=True):
        run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "yes" if rescan else "no"], self.on_nets, timeout=25)

    def on_nets(self, out, code):
        while (c := self.nets.get_first_child()): self.nets.remove(c)
        for inuse, ssid, sig, sec in parse_wifi(out)[:14]:
            r = Gtk.Box(spacing=10, css_classes=["setrow"]); r.append(Gtk.Label(label=("✓ " if inuse else "") + ssid + ("  🔒" if sec else ""), xalign=0, hexpand=True)); r.append(Gtk.Label(label=f"{sig}%", css_classes=["dim-label"]))
            if inuse:
                b = Gtk.Button(label=_("Desconectar")); b.connect("clicked", lambda _b: self.nm(["device", "disconnect", self.wdev]))
                f = Gtk.Button(label=_("Olvidar")); f.connect("clicked", lambda _b, s=ssid: self.nm(["connection", "delete", "id", s])); r.append(f)
            else:
                b = Gtk.Button(label=_("Conectar")); b.connect("clicked", lambda _b, s=ssid, se=sec: self.join(s, se))
            r.append(b); self.nets.append(r)

    def join(self, ssid, sec):
        if not sec: self.nm(["device", "wifi", "connect", ssid]); return
        def ok(v, win):
            if len(v[0]) < 8: return _("Mínimo 8 caracteres")
            win.close(); self.nm(["device", "wifi", "connect", ssid, "password", v[0]]); return None
        ask(self.b.get_root(), _("Contraseña de {0}", ssid), [(_("Contraseña"), True)], _("Conectar"), ok)

    # ---- compartir internet
    def hotspot_section(self):
        self.holder.append(heading(_("Compartir internet")))
        self.holder.append(Gtk.Label(label=_("Crea una red WiFi para que otros dispositivos usen la conexión de este equipo (mejor si tu internet llega por cable)."), xalign=0, wrap=True, css_classes=["dim-label"]))
        self.hs = Gtk.Entry(text="OweeLinux-" + socket.gethostname()[:12]); self.hp = Gtk.PasswordEntry(show_peek_icon=True)
        self.holder.append(row(_("Nombre de la red"), self.hs)); self.holder.append(row(_("Contraseña"), self.hp, _("Mínimo 8 caracteres")))
        hb = Gtk.Box(spacing=8); on = Gtk.Button(label=_("Activar"), css_classes=["suggested-action"]); off = Gtk.Button(label=_("Desactivar")); on.connect("clicked", lambda _b: self.hotspot(True)); off.connect("clicked", lambda _b: self.hotspot(False)); hb.append(on); hb.append(off); self.holder.append(hb)
        run(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"], lambda o, c: [self.say(_("Compartiendo como «{0}»", f[0])) for f in map(split, o.splitlines()) if len(f) > 1 and f[0] == "Hotspot"])

    def hotspot(self, enable):
        if not enable: self.nm(["connection", "down", "Hotspot"]); return
        ssid, pw = self.hs.get_text().strip(), self.hp.get_text()
        if not ssid or len(pw) < 8: self.say(_("No se pudo: {0}", _("Mínimo 8 caracteres"))); return
        self.say(_("Un momento…")); run(["nmcli", "device", "wifi", "hotspot", "ifname", self.wdev, "con-name", "Hotspot", "ssid", ssid, "password", pw],
            lambda o, c: (self.say(_("Compartiendo como «{0}»", ssid) if c == 0 else _("No se pudo: {0}", o.strip()[:120] or "nmcli")), self.refresh()), timeout=30)

    def nm(self, argv):
        self.say(_("Un momento…")); run(["nmcli"] + argv, lambda o, c: (self.say("" if c == 0 else _("No se pudo: {0}", o.strip()[:120] or argv[0])), GLib.timeout_add(900, lambda: (self.refresh(), False)[1])), timeout=40)
PAGE = Red()
