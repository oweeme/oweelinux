"""Energía: perfil de rendimiento (power-profiles-daemon), bloqueo automático de pantalla y suspensión por inactividad (swayidle, ver session/owee-idle)."""
import json, os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib
from .base import Page, page_box, scrolled, heading, row, dropdown, run, have, config_home
SAVE = os.path.join(config_home(), "owee", "power.json")
TIMES = [("0", "Nunca"), ("1", "1 minuto"), ("2", "2 minutos"), ("5", "5 minutos"), ("10", "10 minutos"), ("15", "15 minutos"), ("30", "30 minutos"), ("60", "1 hora")]
PROFILES = {"performance": "Rendimiento", "balanced": "Equilibrado", "power-saver": "Ahorro de energía"}

def load():
    try: d = json.load(open(SAVE))
    except (OSError, ValueError): d = {}
    return {"lock_min": str(d.get("lock_min", "10")), "suspend_min": str(d.get("suspend_min", "0"))}

class Energia(Page):
    title = "Energía"; icon = "owee-set-power"; group = "Dispositivos"; order = 50; keywords = "batería suspender bloqueo inactividad rendimiento ahorro"
    def build(self, app):
        self.cfg = load(); b = page_box("Energía"); self.holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); b.append(self.holder)
        if have("powerprofilesctl"):
            self.holder.append(heading("Perfil de rendimiento")); self.prof_row = Gtk.Box(); self.holder.append(self.prof_row)
            run(["powerprofilesctl", "list"], self.on_profiles)
        self.holder.append(heading("Inactividad"))
        self.holder.append(row("Bloquear la pantalla tras", dropdown(TIMES, self.cfg["lock_min"], lambda k: self.set(lock_min=k))))
        self.holder.append(row("Suspender el equipo tras", dropdown(TIMES, self.cfg["suspend_min"], lambda k: self.set(suspend_min=k)), "Suspender necesita un equipo que lo admita"))
        return scrolled(b)
    def on_profiles(self, out, code):
        names = [l.strip().rstrip(":").lstrip("* ").strip() for l in out.splitlines() if l.strip().endswith(":") and l.strip().rstrip(":").lstrip("* ").strip() in PROFILES]
        cur = next((l.strip().rstrip(":").lstrip("* ").strip() for l in out.splitlines() if l.strip().startswith("*")), "balanced")
        if names: self.prof_row.append(row("Perfil", dropdown([(n, PROFILES[n]) for n in names], cur, lambda k: run(["powerprofilesctl", "set", k]))))
    def set(self, **kw):
        self.cfg.update(kw); os.makedirs(os.path.dirname(SAVE), exist_ok=True); tmp = SAVE + ".tmp"; open(tmp, "w").write(json.dumps(self.cfg)); os.replace(tmp, SAVE)
        h = "/usr/libexec/owee/owee-idle"
        if not os.path.exists(h): h = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "session", "owee-idle")
        try: Gio.Subprocess.new([h], Gio.SubprocessFlags.NONE)                       # reinicia swayidle con los valores nuevos
        except GLib.Error as e: print("[ajustes] owee-idle:", e, flush=True)
PAGE = Energia()
