"""Sonido (PipeWire/WirePlumber con `wpctl`): salida y entrada por defecto, volumen y silencio."""
import re
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, dropdown, switch, slider, run, have, Debounce

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
    title = "Sonido"; icon = "owee-volume-high"; group = "Dispositivos"; order = 20; keywords = "audio volumen altavoz micrófono salida entrada"
    def build(self, app):
        self.deb = Debounce(250); self.b = page_box("Sonido")
        if not have("wpctl"): self.b.append(Gtk.Label(label="No se encontró `wpctl` (PipeWire/WirePlumber).", xalign=0)); return self.b
        self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); self.b.append(self.holder); self.loading = False; self.refresh(); return scrolled(self.b)

    def vol(self, target, cb): run(["wpctl", "get-volume", target], lambda o, c: cb(float(o.split()[1]) if c == 0 and "Volume" in o else None, "[MUTED]" in o))

    def refresh(self):
        if not hasattr(self, "holder"): return
        run(["wpctl", "status"], self.on_status)

    def on_status(self, out, code):
        st = parse_status(out) if code == 0 else {"sinks": [], "sources": []}
        self.loading = True
        while (c := self.holder.get_first_child()): self.holder.remove(c)
        if not st["sinks"] and not st["sources"]:
            self.holder.append(Gtk.Label(label="No hay dispositivos de audio (¿WirePlumber está en marcha?).", xalign=0)); self.loading = False; return
        for kind, title, target in (("sinks", "Salida", "@DEFAULT_AUDIO_SINK@"), ("sources", "Entrada", "@DEFAULT_AUDIO_SOURCE@")):
            devs = st[kind]
            if not devs: continue
            self.holder.append(heading(title)); cur = next((d[0] for d in devs if d[2]), devs[0][0])
            opts = [(str(i), n) for i, n, _d in devs]
            self.holder.append(row("Dispositivo", dropdown(opts, str(cur), lambda k: not self.loading and run(["wpctl", "set-default", k], lambda *a: self.refresh()))))
            vs = slider(0, 100, 0, lambda v, t=target: not self.loading and self.deb(lambda: run(["wpctl", "set-volume", t, f"{round(v)}%"])), width=260)
            ms = switch(False, lambda on, t=target: not self.loading and run(["wpctl", "set-mute", t, "1" if on else "0"]))
            self.holder.append(row("Volumen", vs)); self.holder.append(row("Silenciar", ms))
            self.vol(target, lambda v, muted, vs=vs, ms=ms: (setattr(self, "loading", True), vs.set_value(round((v or 0) * 100)), ms.set_active(muted), setattr(self, "loading", False)))
        self.loading = False
PAGE = Sonido()
