"""Métodos de escritura (Fcitx5): pinyin (chino), mozc (japonés), hangul (coreano), Owee. El perfil va en ~/.config/fcitx5/profile; el programa fcitx5 está siempre en marcha en la
sesión (owee-lite-start) y se le pide recargar con `fcitx5-remote -r`. Cambiar de método: Ctrl + Espacio (valor por defecto de Fcitx5)."""
import os
from owee_i18n import _
from .base import config_home, run, have

PROFILE = os.path.join(config_home(), "fcitx5", "profile")
CATALOG = [  # (nombre en fcitx5, texto, idiomas que lo sugieren)
    ("pinyin", _("Chino (pinyin)"), ("zh",)), ("mozc", _("Japonés (Mozc)"), ("ja",)), ("hangul", _("Coreano (Hangul)"), ()), ("owee", _("Owee (escritura Owee Script)"), ("qow", "qow@owee")),
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

def write_profile(layout, methods):
    """Escribe el perfil: primero el teclado normal con la distribución actual y luego los métodos pedidos."""
    first = "keyboard-" + (layout or "us").split(",")[0]
    names = [first] + [m for m in methods if m != first]
    out = f"[Groups/0]\nName=Default\nDefault Layout={(layout or 'us').split(',')[0]}\nDefaultIM={first}\n\n"
    for i, n in enumerate(names): out += f"[Groups/0/Items/{i}]\nName={n}\nLayout=\n\n"
    out += "[GroupOrder]\n0=Default\n"
    os.makedirs(os.path.dirname(PROFILE), exist_ok=True); tmp = PROFILE + ".tmp"; open(tmp, "w").write(out); os.replace(tmp, PROFILE)
    if have("fcitx5-remote"): run(["fcitx5-remote", "-r"], timeout=3)

def enabled():
    return [n for n in read_items() if not n.startswith("keyboard-")]
