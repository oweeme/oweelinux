"""Métodos de escritura (Fcitx5): pinyin (chino), mozc (japonés), hangul (coreano), Owee. El perfil va en ~/.config/fcitx5/profile; el programa fcitx5 está siempre en marcha en la
sesión (owee-lite-start) y se le pide recargar con `fcitx5-remote -r`. Cambiar de método: Ctrl + Espacio (valor por defecto de Fcitx5)."""
import os
from owee_i18n import _
from .base import config_home, run, have

PROFILE = os.path.join(config_home(), "fcitx5", "profile")
CATALOG = [  # (nombre en fcitx5, texto, idiomas que lo sugieren)
    ("pinyin", _("Chino (pinyin)"), ("zh",)), ("mozc", _("Japonés (Mozc)"), ("ja",)), ("hangul", _("Coreano (Hangul)"), ("ko",)), ("owee", _("Owee (escritura Owee Script)"), ("qow", "qow@owee")),
]

def available():
    """Métodos instalados en el sistema (hay un archivo .conf en /usr/share/fcitx5/inputmethod)."""
    return [(n, t, s) for n, t, s in CATALOG if os.path.exists(f"/usr/share/fcitx5/inputmethod/{n}.conf") or os.path.exists(os.path.expanduser(f"~/.local/share/fcitx5/inputmethod/{n}.conf"))]

def read_items():
    """Lista de entradas del grupo por defecto: ['keyboard-us', 'pinyin', ...]."""
    import re
    try: txt = open(PROFILE).read()
    except OSError: return []
    items = [(int(m.group(1)), m.group(2).strip()) for m in re.finditer(r"\[Groups/0/Items/(\d+)\]\s*\nName=([^\n]+)", txt)]
    return [n for _i, n in sorted(items)]

CONFIG = os.path.join(config_home(), "fcitx5", "config")

def active_by_default():
    """¿El método de escritura está activo desde el principio (sin pulsar Ctrl + Espacio)?"""
    try: return "ActiveByDefault=True" in open(CONFIG).read()
    except OSError: return False

def write_profile(layout, methods, active=None):
    """Escribe el perfil: primero el teclado normal con la distribución actual y luego los métodos pedidos. Fcitx5 NO relee el perfil en marcha (`fcitx5-remote -r` solo recarga la
    configuración) y al salir reescribe el archivo con lo que tiene en memoria: por eso primero se le pide salir, luego se escribe el perfil y por último se vuelve a lanzar."""
    from gi.repository import Gio, GLib
    if active is None: active = active_by_default()
    base = (layout or "us").split(",")[0].split("(")[0]; first = "keyboard-" + (base if base == "jp" else "us")        # la distribución real la pone labwc (owee_keys); Fcitx5 solo necesita la base de los métodos
    names = [first] + [m for m in methods if m != first]
    out = f"[Groups/0]\nName=Default\nDefault Layout={first[9:]}\nDefaultIM={first}\n\n"
    for i, n in enumerate(names): out += f"[Groups/0/Items/{i}]\nName={n}\nLayout=\n\n"
    out += "[GroupOrder]\n0=Default\n"
    def write_and_start(*_a):
        os.makedirs(os.path.dirname(PROFILE), exist_ok=True); tmp = PROFILE + ".tmp"; open(tmp, "w").write(out); os.replace(tmp, PROFILE)
        tmp = CONFIG + ".tmp"
        open(tmp, "w").write("[Behavior]\nActiveByDefault=" + ("True" if active and len(names) > 1 else "False") + "\nDisabledAddons=notificationitem\n\n"          # sin el icono de Fcitx5 en la bandeja: el indicador del panel lo reemplaza\n                             
                             "[Hotkey/TriggerKeys]\n0=Control+space\n1=Control+Shift+space\n")      # alternar método: Ctrl+Espacio o Ctrl+Mayús+Espacio (si otro programa o el equipo anfitrión se queda con la primera)
        os.replace(tmp, CONFIG)
        if have("fcitx5"):
            try: Gio.Subprocess.new(["env", "FCITX_NO_WAYLAND_DIAGNOSE=1", "fcitx5", "-d"], Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_SILENCE)
            except GLib.Error: pass
        return False
    def running():
        for d in os.listdir("/proc"):
            if d.isdigit():
                try:
                    if open(f"/proc/{d}/comm").read().strip() == "fcitx5" and os.getuid() == os.stat(f"/proc/{d}").st_uid: return True
                except OSError: pass
        return False
    def wait_exit(tries=[0]):
        tries[0] += 1
        if running() and tries[0] < 25: return True                      # sigue vivo (guarda su perfil al salir): esperar hasta 5 s
        write_and_start(); return False
    if have("fcitx5-remote") and running(): run(["fcitx5-remote", "-e"], lambda *a: GLib.timeout_add(200, wait_exit), timeout=3)
    else: write_and_start()

def enabled():
    return [n for n in read_items() if not n.startswith("keyboard-")]
