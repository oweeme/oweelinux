"""Estado de las ventanas para el panel (wlr-foreign-toplevel-management v3, con pywayland): avisa cuando la ventana ACTIVA está maximizada o a pantalla completa,
para que el panel se compacte (ancho completo, sin esquinas ni margen) como la barra de menús de macOS. Si el protocolo o los enlaces no están, no hace nada
(el panel se queda flotante): nunca bloquea ni rompe el panel. Los enlaces se generan al construir la imagen: `python3 -m pywayland.scanner -i protocols/*.xml`."""
import os, sys
import gi
from gi.repository import GLib

class WindowWatcher:
    def __init__(self, on_change):
        self.on_change = on_change; self.wins = {}; self.last = None; self.ok = False
        gen = os.environ.get("OWEE_WLGEN", "/usr/lib/owee/wlgen"); sys.path.insert(0, os.path.dirname(gen))          # los módulos generados se importan como paquete «wlgen.…» (se enlazan entre sí)
        try:
            from pywayland.client import Display
            from wlgen.wlr_foreign_toplevel_management_unstable_v1 import ZwlrForeignToplevelManagerV1
        except Exception as e:
            print("[ventanas] sin pywayland/protocolo:", e, flush=True); return
        try:
            self.d = Display(); self.d.connect(); self.reg = self.d.get_registry(); self.Mgr = ZwlrForeignToplevelManagerV1
            self.reg.dispatcher["global"] = self.on_global; self.d.roundtrip(); self.d.roundtrip()
        except Exception as e:
            print("[ventanas] no se pudo conectar:", e, flush=True); return
        if not hasattr(self, "mgr"): print("[ventanas] el compositor no ofrece wlr-foreign-toplevel-management", flush=True); return
        self.ok = True; GLib.io_add_watch(self.d.get_fd(), GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR, self.readable)

    def on_global(self, reg, name, interface, version):
        if interface == "zwlr_foreign_toplevel_manager_v1":
            self.mgr = reg.bind(name, self.Mgr, min(version, 3)); self.mgr.dispatcher["toplevel"] = self.on_toplevel

    def on_toplevel(self, mgr, handle):
        info = self.wins.setdefault(handle, {"state": set(), "title": "", "app": ""})
        def state(h, st): info["pending"] = set(self._states(st))
        def title(h, t): info["title"] = t
        def app_id(h, a): info["app"] = a
        def done(h): info["state"] = info.pop("pending", info["state"]); self.check()
        def closed(h): self.wins.pop(h, None); self.check()
        handle.dispatcher["state"] = state; handle.dispatcher["title"] = title; handle.dispatcher["app_id"] = app_id; handle.dispatcher["done"] = done; handle.dispatcher["closed"] = closed      # (cada uno devuelve None: pywayland no admite otro valor)

    @staticmethod
    def _states(arr):
        try: return [int.from_bytes(bytes(arr[i:i + 4]), "little") for i in range(0, len(arr), 4)]
        except Exception: return []

    def check(self):
        full = any(0 in w["state"] and 2 in w["state"] and 1 not in w["state"] for w in self.wins.values()) or any(3 in w["state"] and 2 in w["state"] for w in self.wins.values())
        if full != self.last: self.last = full; self.on_change(full)

    def readable(self, fd, cond):
        try:
            if cond & (GLib.IO_HUP | GLib.IO_ERR): return False
            self.d.read(); self.d.dispatch(block=False); self.d.flush()          # leer del socket (read) y entregar los eventos; dispatch(block=False) por sí solo no lee
        except Exception as e:
            print("[ventanas] error:", e, flush=True); return False
        return True
