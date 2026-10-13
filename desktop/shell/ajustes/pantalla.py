"""Pantalla: resolución, escala y rotación de cada monitor (wlr-randr) con confirmación de 10 s y vuelta atrás; brillo (brightnessctl) si hay luz regulable.
Lo elegido se guarda en ~/.config/owee/display.json y `owee-apply-display` lo aplica al iniciar sesión."""
import json, os, re
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from .base import Page, page_box, scrolled, heading, row, dropdown, slider, run, have, Debounce, config_home

SCALES = [("1", "100 %"), ("1.25", "125 %"), ("1.5", "150 %"), ("1.75", "175 %"), ("2", "200 %")]       # claves en formato %g (como se normaliza lo que dice wlr-randr)
ROT = [("normal", "Normal"), ("90", "90° a la derecha"), ("180", "180°"), ("270", "90° a la izquierda")]
SAVE = os.path.join(config_home(), "owee", "display.json")

def parse_randr(text):
    """[{'name','modes':[(w,h,hz,actual)],'scale','transform','enabled'}]"""
    outs = []; cur = None; in_modes = False
    for line in text.splitlines():
        if line and not line[0].isspace(): cur = {"name": line.split()[0], "modes": [], "scale": "1", "transform": "normal", "enabled": True}; outs.append(cur); in_modes = False; continue
        if cur is None: continue
        s = line.strip()
        if s.startswith("Modes:"): in_modes = True; continue
        m = re.match(r"(\d+)x(\d+) px, ([\d.]+) Hz(.*)", s)
        if in_modes and m: cur["modes"].append((int(m.group(1)), int(m.group(2)), float(m.group(3)), "current" in m.group(4))); continue
        in_modes = False
        if s.startswith("Scale:"): cur["scale"] = "%g" % float(s.split(":")[1])
        elif s.startswith("Transform:"): cur["transform"] = s.split(":")[1].strip()
        elif s.startswith("Enabled:"): cur["enabled"] = "yes" in s
    return outs

def randr_args(o, mode, scale, transform): return ["wlr-randr", "--output", o, "--mode", f"{mode[0]}x{mode[1]}@{mode[2]:.3f}Hz", "--scale", str(scale), "--transform", transform]

class Pantalla(Page):
    title = "Pantalla"; icon = "owee-set-display"; group = "Dispositivos"; order = 10; keywords = "resolución escala brillo monitor rotación"
    def build(self, app):
        self.b = page_box("Pantalla"); self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); self.b.append(self.holder); self.deb = Debounce(300); self.confirm_id = 0
        self.bar = Gtk.Box(spacing=10, css_classes=["card"], visible=False); self.msg = Gtk.Label(hexpand=True, xalign=0); self.bar.append(self.msg)
        keep = Gtk.Button(label="Mantener"); keep.connect("clicked", lambda b: self.finish(True)); rev = Gtk.Button(label="Revertir"); rev.connect("clicked", lambda b: self.finish(False)); self.bar.append(keep); self.bar.append(rev)
        self.b.append(self.bar); self.refresh(); return scrolled(self.b)

    def refresh(self):
        if not hasattr(self, "holder"): return
        if not have("wlr-randr"): self.holder.append(Gtk.Label(label="No se encontró `wlr-randr`.", xalign=0)); return
        run(["wlr-randr"], self.on_randr); run(["brightnessctl", "-m", "-c", "backlight"], self.on_bright)

    def on_randr(self, out, code):
        while (c := self.holder.get_first_child()):
            if getattr(c, "is_bright", False): break
            self.holder.remove(c)
        self.outputs = parse_randr(out) if code == 0 else []; self.loading = True
        if not self.outputs: self.holder.prepend(Gtk.Label(label="No se pudo leer la configuración de pantalla.", xalign=0)); self.loading = False; return
        for o in reversed(self.outputs):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); box.append(heading(f"Monitor {o['name']}"))
            cur = next((m for m in o["modes"] if m[3]), o["modes"][0] if o["modes"] else None)
            if cur:
                opts = [(f"{w}x{h}@{hz:.3f}", f"{w} × {h}  ({hz:.0f} Hz)") for w, h, hz, _c in o["modes"]]
                box.append(row("Resolución", dropdown(opts, f"{cur[0]}x{cur[1]}@{cur[2]:.3f}", lambda k, o=o: self.apply(o, mode=k))))
            box.append(row("Escala", dropdown(SCALES, o["scale"] if o["scale"] in dict(SCALES) else "1", lambda k, o=o: self.apply(o, scale=k)), "Más grande = textos e iconos mayores"))
            box.append(row("Rotación", dropdown(ROT, o["transform"] if o["transform"] in dict(ROT) else "normal", lambda k, o=o: self.apply(o, transform=k))))
            box.is_out = True; self.holder.prepend(box)
        self.loading = False

    def on_bright(self, out, code):
        for c in list(self.holder):
            if getattr(c, "is_bright", False): self.holder.remove(c)
        line = out.strip().splitlines()[0] if out.strip() else ""
        p = line.split(",")
        if code != 0 or len(p) < 5: return
        self.loading = True; box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); box.is_bright = True; box.append(heading("Brillo"))
        box.append(row("Brillo de la pantalla", slider(1, 100, int(p[3].rstrip("%")), lambda v: not self.loading and self.deb(lambda: run(["brightnessctl", "set", f"{round(v)}%"])), width=260)))
        self.holder.append(box); self.loading = False

    def apply(self, o, mode=None, scale=None, transform=None):
        if self.loading or getattr(self, "pending", None): return
        cur = next((m for m in o["modes"] if m[3]), None)
        old = (cur, o["scale"], o["transform"])
        if mode is None: mode = f"{cur[0]}x{cur[1]}@{cur[2]:.3f}" if cur else None
        w, h, hz = re.match(r"(\d+)x(\d+)@([\d.]+)", mode).groups() if mode else (0, 0, 0)
        new = ((int(w), int(h), float(hz), True), scale or o["scale"], transform or o["transform"])
        if mode is None: return
        self.pending = (o, old, new); self.msg.set_text(f"Pantalla {o['name']} cambiada. ¿Mantener estos cambios? Se revertirán en 10 s."); self.bar.set_visible(True); self.left = 10
        run(randr_args(o["name"], new[0], new[1], new[2]))
        self.confirm_id = GLib.timeout_add_seconds(1, self.tick)

    def tick(self):
        self.left -= 1; self.msg.set_text(f"¿Mantener estos cambios? Se revertirán en {self.left} s.")
        if self.left <= 0: self.finish(False); return False
        return True

    def finish(self, keep):
        if not getattr(self, "pending", None): return
        o, old, new = self.pending; self.pending = None
        if self.confirm_id: GLib.source_remove(self.confirm_id); self.confirm_id = 0
        self.bar.set_visible(False)
        if keep: self.save(o["name"], new)
        else:
            if old[0]: run(randr_args(o["name"], old[0], old[1], old[2]), lambda *a: self.refresh())
            else: self.refresh()
        if keep: self.refresh()

    def save(self, name, new):
        try: d = json.load(open(SAVE))
        except (OSError, ValueError): d = {}
        d[name] = {"mode": f"{new[0][0]}x{new[0][1]}@{new[0][2]:.3f}Hz", "scale": new[1], "transform": new[2]}
        os.makedirs(os.path.dirname(SAVE), exist_ok=True); tmp = SAVE + ".tmp"; open(tmp, "w").write(json.dumps(d, indent=1)); os.replace(tmp, SAVE)
PAGE = Pantalla()
