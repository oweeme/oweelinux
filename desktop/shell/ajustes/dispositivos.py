"""Dispositivos y controladores: qué hardware tiene el equipo y si cada pieza tiene su controlador (módulo del kernel) cargado — como el «gestor de dispositivos» de otros sistemas.
Solo lee (lspci, lsblk, /sys, /proc): no cambia nada. Un dispositivo PCI sin «Kernel driver in use» se marca en rojo: o falta el controlador o su firmware. Incluye accesos al gestor de discos."""
import glob, os, re
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib
from .base import Page, page_box, scrolled, heading, run, have
from owee_i18n import _

def read(path, default=""):
    try: return open(path).read().strip()
    except OSError: return default

class Dispositivos(Page):
    title = _("Dispositivos"); icon = "owee-set-info"; group = "Sistema"; order = 80; keywords = _("hardware controladores drivers cpu memoria gráficos red sonido batería discos cámara tableta wacom")
    def build(self, app):
        self.b = page_box(_("Dispositivos y controladores"), _("Lo que tiene tu equipo y si cada pieza tiene su controlador. En rojo: sin controlador (puede faltar el controlador o su firmware)."))
        tools = Gtk.Box(spacing=8)
        if GLib.find_program_in_path("partitionmanager"):
            bt = Gtk.Button(label=_("Abrir el gestor de discos")); bt.connect("clicked", lambda b: self.launch("org.kde.partitionmanager.desktop", ["partitionmanager"])); tools.append(bt)
        mon = Gtk.Button(label=_("Abrir el monitor del sistema")); mon.connect("clicked", lambda b: self.launch("owee-monitor.desktop", ["/usr/libexec/owee/apps/monitor/owee_monitor.py"])); tools.append(mon)
        self.b.append(tools); self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10); self.b.append(self.holder)
        self.scan(); return scrolled(self.b)

    def refresh(self): self.scan()

    @staticmethod
    def launch(desktop_id, argv):
        ai = Gio.DesktopAppInfo.new(desktop_id)
        try:
            if ai: ai.launch([], None)
            else: Gio.Subprocess.new(argv, Gio.SubprocessFlags.NONE)
        except GLib.Error as e: print("[dispositivos]", e, flush=True)

    def card(self, title, rows):
        """rows = [(texto, estado)] con estado 'ok' | 'bad' | ''."""
        c = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3); c.add_css_class("card"); c.append(heading(title))
        for text, st in rows:
            lab = Gtk.Label(label=text, xalign=0, wrap=True, selectable=True)
            if st: lab.add_css_class(st)
            c.append(lab)
        self.holder.append(c)

    def scan(self):
        while (ch := self.holder.get_first_child()): self.holder.remove(ch)
        self.card(_("Procesador"), [(self.cpu(), "")])
        self.card(_("Memoria"), [(self.mem(), "")])
        run(["lspci", "-k"], self.on_pci)

    @staticmethod
    def cpu():
        name = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "?") if os.path.exists("/proc/cpuinfo") else "?"
        n = sum(1 for l in open("/proc/cpuinfo") if l.startswith("processor")) if os.path.exists("/proc/cpuinfo") else 0
        return f"{name}  ·  {n} " + _("hilos")

    @staticmethod
    def mem():
        d = {}
        for l in open("/proc/meminfo"):
            k, _s, v = l.partition(":"); d[k] = int(v.split()[0]) if v.split() else 0
        return f"{d.get('MemTotal', 0) / 1048576:.1f} GB  ·  " + _("zram/swap") + f" {d.get('SwapTotal', 0) / 1048576:.1f} GB"

    def on_pci(self, out, code):
        groups = {"gpu": [], "audio": [], "net": [], "other": []}
        for blk in out.strip().split("\n\n"):
            lines = blk.splitlines()
            if not lines: continue
            head = lines[0].split(" ", 1)[1] if " " in lines[0] else lines[0]
            drv = next((l.split(":", 1)[1].strip() for l in lines if "Kernel driver in use" in l), "")
            low = head.lower()
            key = "gpu" if re.search(r"vga|3d controller|display controller", low) else "audio" if "audio" in low else "net" if re.search(r"network|ethernet|wireless", low) else "other"
            name = head.split(": ", 1)[1] if ": " in head else head
            text = f"{name}  →  " + (_('controlador {0}', drv) if drv else _("SIN controlador"))
            groups[key].append((text, "ok" if drv else "bad"))
        if code != 0 or not out.strip(): groups["other"].append((_("No se pudo leer la lista de dispositivos PCI (falta pciutils)."), ""))
        for key, title in (("gpu", _("Gráficos")), ("audio", _("Sonido")), ("net", _("Red"))):
            if groups[key]: self.card(title, groups[key])
        self.card(_("Almacenamiento"), [(l, "") for l in self.disks()] or [("?", "")])
        bat = self.battery()
        if bat: self.card(_("Batería"), bat)
        cams = [read(p) for p in sorted(glob.glob("/sys/class/video4linux/video*/name"))]
        self.card(_("Cámara"), [(c, "ok") for c in dict.fromkeys(cams)] or [(_("No se detecta ninguna cámara."), "")])
        self.card(_("Bluetooth"), [(_("Adaptador detectado") if glob.glob("/sys/class/bluetooth/hci*") else _("No se detecta ningún adaptador Bluetooth."), "ok" if glob.glob("/sys/class/bluetooth/hci*") else "")])
        run(["sh", "-c", "grep -E '^N: Name=' /proc/bus/input/devices"], self.on_input)

    @staticmethod
    def disks():
        out = []
        for d in sorted(glob.glob("/sys/block/*")):
            n = os.path.basename(d)
            if re.match(r"(loop|ram|zram|dm-|sr)", n): continue
            size = int(read(d + "/size", "0")) * 512 / 1e9; model = read(d + "/device/model") or read(d + "/device/name")
            kind = "SSD/NVMe" if read(d + "/queue/rotational") == "0" else "HDD"
            out.append(f"/dev/{n}  ·  {model or '?'}  ·  {size:.0f} GB  ·  {kind}")
        return out

    @staticmethod
    def battery():
        rows = []
        for b in sorted(glob.glob("/sys/class/power_supply/BAT*")):
            cap, st = read(b + "/capacity"), read(b + "/status"); full = read(b + "/energy_full") or read(b + "/charge_full"); des = read(b + "/energy_full_design") or read(b + "/charge_full_design")
            health = f"  ·  " + _('salud {0} %', round(int(full) * 100 / int(des))) if full.isdigit() and des.isdigit() and int(des) else ""
            rows.append((f"{read(b + '/model_name', os.path.basename(b))}  ·  {cap} %  ·  {st}{health}", "ok"))
        return rows

    def on_input(self, out, code):
        names = [l.split("=", 1)[1].strip().strip('"') for l in out.splitlines() if "Name=" in l]
        skip = re.compile(r"power button|sleep button|lid switch|video bus|hdmi|pc speaker|speaker|headphone|mic|extra buttons|intel hid|thinkpad extra|wmi", re.I)
        shown = [n for n in dict.fromkeys(names) if not skip.search(n)]
        tablets = [n for n in shown if re.search(r"wacom|tablet|pen|stylus|huion|xp-pen", n, re.I)]
        self.card(_("Teclado, ratón y tabletas"), [(n, "ok") for n in shown] or [("?", "")])
        if tablets: self.card(_("Tableta gráfica"), [(n, "ok") for n in tablets] + [(_("Las tabletas Wacom y similares se reconocen solas (libinput)."), "")])

PAGE = Dispositivos()
