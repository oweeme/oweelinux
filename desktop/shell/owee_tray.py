"""Bandeja de aplicaciones de OweeLinux Lite: anfitrión del protocolo StatusNotifierItem (el que usan Qt/KDE, Electron, Telegram, Steam...).
El panel es dueño del nombre org.kde.StatusNotifierWatcher en el bus de sesión; cada app registra su icono y aquí se dibuja.
Reglas (docs/ESCRITORIO.md): todas las llamadas D-Bus son asíncronas y con tiempo límite; una app que se cuelga o desaparece nunca bloquea el panel.
Clic izquierdo = Activate, clic derecho = ContextMenu (el menú lo dibuja la propia app). Por ahora no se dibuja com.canonical.dbusmenu."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Gdk

WATCHER_XML = """<node><interface name="org.kde.StatusNotifierWatcher">
  <method name="RegisterStatusNotifierItem"><arg type="s" name="service" direction="in"/></method>
  <method name="RegisterStatusNotifierHost"><arg type="s" name="service" direction="in"/></method>
  <property name="RegisteredStatusNotifierItems" type="as" access="read"/>
  <property name="IsStatusNotifierHostRegistered" type="b" access="read"/>
  <property name="ProtocolVersion" type="i" access="read"/>
  <signal name="StatusNotifierItemRegistered"><arg type="s"/></signal>
  <signal name="StatusNotifierItemUnregistered"><arg type="s"/></signal>
  <signal name="StatusNotifierHostRegistered"/>
</interface></node>"""
TIMEOUT_MS = 2000
SIZE = 18


class TrayItem:
    def __init__(self, tray, service, bus, path):
        self.tray, self.service, self.bus, self.path = tray, service, bus, path
        self.img = Gtk.Image(pixel_size=SIZE, icon_name="image-missing")
        self.btn = Gtk.Button(child=self.img, has_frame=False); self.btn.add_css_class("owee-tray"); self.btn.set_visible(False)
        self.btn.connect("clicked", lambda b: self.call("Activate"))
        right = Gtk.GestureClick(button=3); right.connect("released", lambda *a: self.call("ContextMenu")); self.btn.add_controller(right)
        self.status = "Active"
        self.watch = Gio.bus_watch_name(Gio.BusType.SESSION, bus, Gio.BusNameWatcherFlags.NONE, None, lambda c, n: tray.remove(self.service))
        Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION, Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES | Gio.DBusProxyFlags.DO_NOT_AUTO_START,
                                  None, bus, path, "org.kde.StatusNotifierItem", None, self.proxy_ready)

    def proxy_ready(self, src, res):
        try: self.proxy = Gio.DBusProxy.new_for_bus_finish(res)
        except GLib.Error: self.tray.remove(self.service); return
        self.proxy.connect("g-signal", lambda p, sender, sig, params: self.refresh() if sig.startswith("New") else None)
        self.refresh()

    def refresh(self):
        self.proxy.get_connection().call(self.bus, self.path, "org.freedesktop.DBus.Properties", "GetAll", GLib.Variant("(s)", ("org.kde.StatusNotifierItem",)),
                                         GLib.VariantType("(a{sv})"), Gio.DBusCallFlags.NONE, TIMEOUT_MS, None, self.got_props)

    def got_props(self, conn, res):
        try: p = conn.call_finish(res).unpack()[0]
        except GLib.Error: return                              # la app no responde: se deja el último icono
        self.status = p.get("Status", "Active")
        if str(p.get("Id", "")).lower().startswith("fcitx"): self.btn.set_visible(False); return           # Fcitx5: el indicador del panel (con menú propio) lo reemplaza
        self.btn.set_visible(self.status != "Passive")
        tip = p.get("ToolTip")
        self.btn.set_tooltip_text((tip[2] if tip and tip[2] else None) or p.get("Title") or self.bus)
        icon = p.get("IconName") or ""
        if self.status == "NeedsAttention" and p.get("AttentionIconName"): icon = p["AttentionIconName"]
        pix = p.get("IconPixmap")
        if icon and Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).has_icon(icon): self.img.set_from_icon_name(icon)
        elif pix: self.set_pixmap(pix)
        elif icon: self.img.set_from_icon_name(icon)

    def set_pixmap(self, pix):
        w, h, data = max(pix, key=lambda t: t[0] * t[1] if t[0] <= 128 else 0)
        b = bytes(data)
        if w <= 0 or h <= 0 or len(b) != w * h * 4: return
        out = bytearray(len(b)); out[0::4], out[1::4], out[2::4], out[3::4] = b[1::4], b[2::4], b[3::4], b[0::4]   # ARGB (orden de red) → RGBA
        self.img.set_from_paintable(Gdk.MemoryTexture.new(w, h, Gdk.MemoryFormat.R8G8B8A8, GLib.Bytes.new(bytes(out)), w * 4))

    def call(self, method):
        if not hasattr(self, "proxy"): return
        self.proxy.call(method, GLib.Variant("(ii)", (0, 0)), Gio.DBusCallFlags.NO_AUTO_START, TIMEOUT_MS, None, lambda *a: None)

    def close(self): Gio.bus_unwatch_name(self.watch)


class Tray:
    def __init__(self):
        self.box = Gtk.Box(spacing=2); self.items = {}
        self.node = Gio.DBusNodeInfo.new_for_xml(WATCHER_XML)
        self.own = Gio.bus_own_name(Gio.BusType.SESSION, "org.kde.StatusNotifierWatcher", Gio.BusNameOwnerFlags.NONE, self.on_bus, None,
                                    lambda c, n: print("[tray] no se pudo ser el watcher (¿otro lo tiene?)", flush=True))

    def on_bus(self, conn, name):
        self.conn = conn
        conn.register_object("/StatusNotifierWatcher", self.node.interfaces[0], self.on_method, self.on_get, None)

    def on_method(self, conn, sender, path, iface, method, params, inv):
        s = params.unpack()[0]
        if method == "RegisterStatusNotifierItem": self.register(sender, s)
        elif method == "RegisterStatusNotifierHost": pass
        inv.return_value(None)

    def on_get(self, conn, sender, path, iface, prop):
        return {"RegisteredStatusNotifierItems": GLib.Variant("as", list(self.items)), "IsStatusNotifierHostRegistered": GLib.Variant("b", True),
                "ProtocolVersion": GLib.Variant("i", 0)}.get(prop)

    def register(self, sender, s):
        bus, path = (s, "/StatusNotifierItem") if not s.startswith("/") else (sender, s)
        if "/" in bus: bus, rest = bus.split("/", 1); path = "/" + rest
        key = bus + path
        if key in self.items: return
        it = TrayItem(self, key, bus, path); self.items[key] = it; self.box.append(it.btn)
        self.conn.emit_signal(None, "/StatusNotifierWatcher", "org.kde.StatusNotifierWatcher", "StatusNotifierItemRegistered", GLib.Variant("(s)", (key,)))

    def remove(self, key):
        it = self.items.pop(key, None)
        if not it: return
        it.close(); self.box.remove(it.btn)
        self.conn.emit_signal(None, "/StatusNotifierWatcher", "org.kde.StatusNotifierWatcher", "StatusNotifierItemUnregistered", GLib.Variant("(s)", (key,)))
