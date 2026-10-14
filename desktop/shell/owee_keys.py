"""Distribuciones de teclado de OweeLinux Lite, compartidas por el panel, Ajustes → Teclado/Idioma y `owee-layout`.
Modelo: el usuario elige hasta dos distribuciones (p. ej. «us» y «ara»); labwc usa UNA a la vez (XKB_DEFAULT_LAYOUT en ~/.config/labwc/environment) y se cambia de una a otra con
Super + Mayús + Espacio o desde el indicador del panel. Así el indicador siempre dice la verdad (se lee de settings.json) y no depende de teclas especiales del XKB.
Las claves son «ara», «ru», «us(intl)», «in(bolnagri)»…"""
import os, re, subprocess
import owee_config

ENV = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "labwc", "environment")
SHORT = {"us": "US", "latam": "LA", "es": "ES", "gb": "GB", "br": "BR", "pt": "PT", "fr": "FR", "de": "DE", "it": "IT", "ru": "RU", "ua": "UA", "jp": "JP", "kr": "KR", "ara": "AR",
         "ir": "FA", "in": "HI", "pk": "UR", "id": "ID", "my": "MS"}

def short(key): return SHORT.get(key.split("(")[0], key.split("(")[0].upper()[:3])

def read_env():
    d = {}
    try:
        for line in open(ENV):
            m = re.match(r"\s*([A-Z_]+)=(.*)", line)
            if m: d[m.group(1)] = m.group(2).strip()
    except OSError: pass
    return d

def write_env(upd):
    d = read_env(); d.update(upd); os.makedirs(os.path.dirname(ENV), exist_ok=True); tmp = ENV + ".tmp"
    open(tmp, "w").write("".join(f"{k}={v}\n" for k, v in d.items() if v != "")); os.replace(tmp, ENV)

def from_env():
    """Distribuciones según el archivo environment (instalaciones antiguas o cambios a mano)."""
    e = read_env(); lay = [x for x in e.get("XKB_DEFAULT_LAYOUT", "us").split(",") if x]; var = e.get("XKB_DEFAULT_VARIANT", "").split(",")
    return [f"{l}({var[i]})" if i < len(var) and var[i] else l for i, l in enumerate(lay)] or ["us"]

def state():
    """(lista de distribuciones, índice de la activa)."""
    c = owee_config.load(); lst = c.get("layouts") or from_env(); idx = c.get("layout_idx", 0)
    return lst, (idx if 0 <= idx < len(lst) else 0)

def active(): lst, i = state(); return lst[i]

def reconfigure():
    """labwc recarga el teclado al instante; no espera (el panel y Ajustes no se bloquean)."""
    try: subprocess.Popen(["sh", "-c", 'LABWC_PID="${LABWC_PID:-$(pgrep -u "$(id -u)" -x labwc | head -1)}" timeout 5 labwc --reconfigure'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError: pass

def apply(lst, idx=0):
    """Guarda las distribuciones elegidas, pone la activa en labwc y recarga."""
    lst = [k for k in lst if k][:4] or ["us"]; idx = idx if 0 <= idx < len(lst) else 0
    c = owee_config.load(); c["layouts"] = lst; c["layout_idx"] = idx; owee_config.save(c)
    key = lst[idx]; base, _s, var = key.partition("(")
    write_env({"XKB_DEFAULT_LAYOUT": base, "XKB_DEFAULT_VARIANT": var.rstrip(")"), "XKB_DEFAULT_OPTIONS": ""}); reconfigure()

def select(idx): lst, _i = state(); apply(lst, idx)

def next_layout():
    lst, i = state(); apply(lst, (i + 1) % len(lst)); return lst[(i + 1) % len(lst)]

if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["next"]: print(next_layout())
    elif sys.argv[1:] == ["get"]: print(active())
