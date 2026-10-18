"""Sonido (PipeWire/WirePlumber con `wpctl` y `pactl`): salida y entrada por defecto, puerto (altavoces, auriculares, micrófono interno…), volumen (con opción de superar el 100 %) y silencio."""
import json, re
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, dropdown, switch, slider, run, have, Debounce
from owee_i18n import _

LINE = re.compile(r"^[\s│├└─]*(\*)?\s*(\d+)\.\s+(.*?)\s*(?:\[vol:\s*([\d.]+)(\s+MUTED)?\])?\s*$")

def parse_status(text):
    """Devuelve {'sinks': [(id, nombre, es_defecto)], 'sources': [...]} a partir de `wpctl status`."""
    out = {"sinks": [], "sources": []}; sec = None
    for line in text.splitlines():
        t = re.sub(r"^[\s│├└─]+", "", line).strip()
        if t in ("Sinks:", "Sources:"): sec = "sinks" if t == "Sinks:" else "sources"; continue
        if t.endswith(":") and not t[0].isdigit() and t[:1] != "*": sec = None; continue
        m = LINE.match(line)
        if sec and m: out[sec].append((int(m.group(2)), m.group(3), bool(m.group(1))))
    return out

class Sonido(Page):
    title = _("Sonido"); icon = "owee-volume-high"; group = "Dispositivos"; order = 20; keywords = _("audio volumen altavoz micrófono salida entrada")
    def build(self, app):
        self.deb = Debounce(250); self.b = page_box(_("Sonido"))
        if not have("wpctl"): self.b.append(Gtk.Label(label=_("No se encontró `wpctl` (PipeWire/WirePlumber)."), xalign=0)); return self.b
        self.app = app; self.boost = bool(app.cfg.get("audio_boost", False))
        self.b.append(row(_("Permitir superar el 100 % (hasta 150 %)"), switch(self.boost, self.set_boost), _("Sube más el volumen de los altavoces o del micrófono; por encima del 100 % el sonido puede distorsionarse")))
        self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); self.b.append(self.holder); self.loading = False; self.refresh(); return scrolled(self.b)

    def set_boost(self, on): self.boost = on; self.app.change(audio_boost=on); self.refresh()

    def ports(self, kind, cb):
        """Puertos de cada dispositivo por defecto (pactl, si está): [(nombre, descripción, activo)] y el nombre del dispositivo. cb(puertos, dispositivo)."""
        if not have("pactl"): cb([], None); return
        sub = "sinks" if kind == "sinks" else "sources"
        def done(out, code):
            try:
                devs = [d for d in json.loads(out) if not d.get("name", "").endswith(".monitor")]
                run(["pactl", "get-default-sink" if kind == "sinks" else "get-default-source"], lambda o2, c2: cb(*self.pick_ports(devs, o2.strip())))
            except (ValueError, TypeError): cb([], None)
        run(["pactl", "--format=json", "list", sub], done)

    @staticmethod
    def pick_ports(devs, name):
        d = next((x for x in devs if x.get("name") == name), devs[0] if devs else None)
        if not d: return [], None
        act = d.get("active_port"); return [(p["name"], p.get("description", p["name"]), p["name"] == act) for p in d.get("ports", []) if p.get("availability") != "not available"], d["name"]

    def vol(self, target, cb): run(["wpctl", "get-volume", target], lambda o, c: cb(float(o.split()[1]) if c == 0 and "Volume" in o else None, "[MUTED]" in o))

    def refresh(self):
        if not hasattr(self, "holder"): return
        run(["wpctl", "status"], self.on_status)

    def on_status(self, out, code):
        st = parse_status(out) if code == 0 else {"sinks": [], "sources": []}
        self.loading = True
        while (c := self.holder.get_first_child()): self.holder.remove(c)
        if not st["sinks"] and not st["sources"]:
            self.holder.append(Gtk.Label(label=_("No hay dispositivos de audio (¿WirePlumber está en marcha?)."), xalign=0)); self.loading = False; return
        for kind, title, target in (("sinks", _("Salida"), "@DEFAULT_AUDIO_SINK@"), ("sources", _("Entrada"), "@DEFAULT_AUDIO_SOURCE@")):
            devs = st[kind]
            if not devs: continue
            self.holder.append(heading(title)); cur = next((d[0] for d in devs if d[2]), devs[0][0])
            opts = [(str(i), n) for i, n, _d in devs]
            self.holder.append(row(_("Dispositivo"), dropdown(opts, str(cur), lambda k: not self.loading and run(["wpctl", "set-default", k], lambda *a: self.refresh()))))
            top = 150 if self.boost else 100
            vs = slider(0, top, 0, lambda v, t=target: not self.loading and self.deb(lambda: run(["wpctl", "set-volume", "-l", "1.5" if self.boost else "1.0", t, f"{round(v)}%"])), width=260)
            ms = switch(False, lambda on, t=target: not self.loading and run(["wpctl", "set-mute", t, "1" if on else "0"]))
            pbox = Gtk.Box(); pbox.is_port = True; self.holder.append(row(_("Puerto"), pbox))
            self.ports(kind, lambda ps, dev, pbox=pbox: self.fill_ports(pbox, ps, dev, kind))
            self.holder.append(row(_("Volumen"), vs)); self.holder.append(row(_("Silenciar"), ms))
            self.vol(target, lambda v, muted, vs=vs, ms=ms: (setattr(self, "loading", True), vs.set_value(round((v or 0) * 100)), ms.set_active(muted), setattr(self, "loading", False)))
        self.loading = False
    def fill_ports(self, box, ports, dev, kind):
        if not ports:
            h = box.get_parent(); r = h.get_parent() if h else None
            if r: r.set_visible(False)
            return
        cur = next((n for n, _d, a in ports if a), ports[0][0])
        cmd = "set-sink-port" if kind == "sinks" else "set-source-port"
        box.append(dropdown([(n, d) for n, d, _a in ports], cur, lambda k, dev=dev, cmd=cmd: not self.loading and run(["pactl", cmd, dev, k])))

PAGE = Sonido()
