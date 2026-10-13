"""Idiomas de OweeLinux: `_("texto en español")` devuelve el texto en el idioma elegido en Ajustes → Idioma (guardado en ~/.config/owee/settings.json, clave «lang»).
El texto original es el español del código; cada idioma tiene un catálogo `i18n/<código>.json` {"español": "traducción"}. Si falta una cadena se muestra en español (nunca falla).
Marcadores: `{0}`, `{1}`… se rellenan con los argumentos extra:  _("Monitor {0}", nombre).
Idiomas con catálogo propio de Owee: «qow» (romano) y «qow@owee» (escritura Owee Script, necesita la fuente Owee Sans).
El idioma se lee UNA vez al arrancar (las apps se reinician al cambiarlo)."""
import json, os

LANGS = [  # (código, nombre en su propio idioma, locale del sistema, familia de teclado/IM)
    ("es", "Español", "es_ES.UTF-8"), ("en", "English", "en_US.UTF-8"), ("pt", "Português", "pt_BR.UTF-8"), ("fr", "Français", "fr_FR.UTF-8"), ("de", "Deutsch", "de_DE.UTF-8"),
    ("ru", "Русский", "ru_RU.UTF-8"), ("zh", "中文（简体）", "zh_CN.UTF-8"), ("ja", "日本語", "ja_JP.UTF-8"),
    ("qow", "Owee (romano)", "qow_BO.UTF-8"), ("qow@owee", "Owee (Owee Script)", "qow_BO.UTF-8"),
]
SETTINGS = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "owee", "settings.json")
HERE = os.path.dirname(os.path.realpath(__file__))
CAT_DIRS = [os.path.join(HERE, "..", "i18n"), "/usr/share/owee/i18n"]

def locale_of(code):
    return next((l for c, _n, l in LANGS if c == code), "es_ES.UTF-8")

def system_default():
    """Idioma por defecto: el del entorno (LANG) si OweeLinux lo trae, si no el español."""
    code = (os.environ.get("LANGUAGE") or os.environ.get("LANG") or "es").split(":")[0].split(".")[0]
    if code.startswith("qow"): return "qow@owee" if "@owee" in os.environ.get("LANG", "") else "qow"
    short = code.split("_")[0]
    return short if short in dict((c, n) for c, n, _l in LANGS) else "es"

def current():
    try: v = json.load(open(SETTINGS)).get("lang")
    except (OSError, ValueError, AttributeError): v = None
    return v if v in dict((c, n) for c, n, _l in LANGS) else system_default()

def _load(code):
    for d in CAT_DIRS:
        p = os.path.join(d, code + ".json")
        try: return json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError): continue
    return {}

LANG = current()
def _apply_locale():
    """Las bibliotecas (GTK: calendario, diálogos de archivos, «Cancelar»…) toman el idioma de LANG: se ajusta ANTES de que se cargue GTK, solo si ese locale existe en el sistema."""
    import locale
    loc = locale_of(LANG)
    for cand in (loc, loc.replace("UTF-8", "utf8")):
        try: locale.setlocale(locale.LC_ALL, cand)
        except locale.Error: continue
        os.environ["LANG"] = cand; os.environ["LANGUAGE"] = cand.split(".")[0] + ":" + LANG.split("@")[0]
        return True
    return False
_CAT = {} if LANG == "es" else _load(LANG)
LOCALE_OK = _apply_locale()           # False: el locale del sistema no está generado (los textos propios sí cambian; los de GTK quedan en el idioma anterior)

def _(msg, *args):
    """Traduce `msg` (español). Con argumentos, rellena {0}, {1}…"""
    out = _CAT.get(msg) or msg
    if args:
        try: out = out.format(*args)
        except (IndexError, KeyError, ValueError): out = msg.format(*args)       # catálogo mal formado: se usa el español
    return out

def N_(msg): return msg      # marcar sin traducir todavía (tablas que se traducen al mostrar)

def installed_locales():
    """Locales UTF-8 generados en el sistema (`locale -a`); sirve para mostrar solo idiomas que de verdad funcionan."""
    import subprocess
    try: out = subprocess.run(["locale", "-a"], capture_output=True, text=True, timeout=5).stdout
    except Exception: return set()
    return {l.lower().replace("utf8", "utf-8") for l in out.split()}
