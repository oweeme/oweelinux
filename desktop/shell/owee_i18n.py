"""Idiomas de OweeLinux: `_("texto en español")` devuelve el texto en el idioma elegido en Ajustes → Idioma (guardado en ~/.config/owee/settings.json, clave «lang»).
El texto original es el español del código; cada idioma tiene un catálogo `i18n/<código>.json` {"español": "traducción"}. Si falta una cadena se muestra en español (nunca falla).
Marcadores: `{0}`, `{1}`… se rellenan con los argumentos extra:  _("Monitor {0}", nombre).
Idiomas con catálogo propio de Owee: «qow» (romano) y «qow@owee» (escritura Owee Script, necesita la fuente Owee Sans).
El idioma se lee UNA vez al arrancar (las apps se reinician al cambiarlo)."""
import json, os, re

LANGS = [  # (código, nombre en su propio idioma, locale del sistema): la ÚNICA lista de idiomas; Idioma, Teclado, Métodos de escritura y la sesión salen de aquí
    ("es", "Español", "es_ES.UTF-8"), ("en", "English", "en_US.UTF-8"), ("pt", "Português", "pt_BR.UTF-8"), ("fr", "Français", "fr_FR.UTF-8"), ("de", "Deutsch", "de_DE.UTF-8"),
    ("it", "Italiano", "it_IT.UTF-8"), ("ru", "Русский", "ru_RU.UTF-8"), ("uk", "Українська", "uk_UA.UTF-8"), ("zh", "中文（简体）", "zh_CN.UTF-8"), ("ja", "日本語", "ja_JP.UTF-8"),
    ("ko", "한국어", "ko_KR.UTF-8"), ("ar", "العربية", "ar_SA.UTF-8"), ("fa", "فارسی", "fa_IR.UTF-8"), ("hi", "हिन्दी", "hi_IN.UTF-8"), ("ur", "اردو", "ur_PK.UTF-8"),
    ("id", "Bahasa Indonesia", "id_ID.UTF-8"), ("ms", "Bahasa Melayu", "ms_MY.UTF-8"),
    ("qow", "Owee (romano)", "qow_BO.UTF-8"), ("qow@owee", "Owee (Owee Script)", "qow_BO.UTF-8"),
]
# Para cada idioma: distribución(es) de teclado XKB que se ponen al elegirlo (la primera es la principal; con dos, Alt + Mayús alterna), método de escritura de Fcitx5 que se
# activa desde el principio (None = solo el teclado) y si se escribe de derecha a izquierda. Cada distribución debe existir en ajustes/teclado.py (lo comprueba tools/i18n/smoke.py).
LANG_INFO = {
    "es": ("latam", None, False), "en": ("us", None, False), "pt": ("br", None, False), "fr": ("fr", None, False), "de": ("de", None, False), "it": ("it", None, False),
    "ru": ("us,ru", None, False), "uk": ("us,ua", None, False), "zh": ("us", "pinyin", False), "ja": ("jp", "mozc", False), "ko": ("us", "hangul", False),
    "ar": ("us,ara", None, True), "fa": ("us,ir", None, True), "hi": ("us,in", None, False), "ur": ("us,pk", None, True), "id": ("us", None, False), "ms": ("us,my", None, False),
    "qow": ("us", "owee", False), "qow@owee": ("us", "owee", False),
}
def all_layouts(): return sorted({k for v in LANG_INFO.values() for k in v[0].split(",")} | {"us(intl)"})
def layout_for(code): return LANG_INFO.get(code, ("us",))[0]
def method_for(code): return LANG_INFO.get(code, ("us", None))[1]
NATIVE_SCRIPT = {"ru", "uk", "ar", "fa", "hi", "ur"}          # idiomas que no se escriben con letras latinas: al elegirlos queda activa su distribución propia (la última)
def is_rtl(code): return LANG_INFO.get(code, ("us", None, False))[2]
SETTINGS = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "owee", "settings.json")
HERE = os.path.dirname(os.path.realpath(__file__))
CAT_DIRS = [os.path.join(HERE, "..", "i18n"), "/usr/share/owee/i18n"]

LOCDIR = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "owee", "locales")      # idiomas añadidos por el usuario (sin permisos de administrador)

def extra_langs():
    """Idiomas añadidos en Ajustes → Idioma → «Añadir otro idioma»: {código: (nombre, locale)}. Su locale se genera en LOCDIR y se usa con LOCPATH."""
    try: d = json.load(open(SETTINGS)).get("extra_langs", {})
    except (OSError, ValueError, AttributeError): return {}
    if not isinstance(d, dict): return {}
    return {c: (str(v.get("name", c)), str(v.get("loc", c + ".UTF-8"))) for c, v in d.items() if isinstance(v, dict) and re.fullmatch(r"[a-z]{2,3}", c) and re.fullmatch(r"[A-Za-z_@.0-9-]{2,30}", str(v.get("loc", "")))}

def all_langs(): return LANGS + [(c, n, l) for c, (n, l) in extra_langs().items()]

def locale_of(code):
    return next((l for c, _n, l in all_langs() if c == code), "es_ES.UTF-8")

def system_default():
    """Idioma por defecto: el del entorno (LANG) si OweeLinux lo trae, si no el español."""
    code = (os.environ.get("LANGUAGE") or os.environ.get("LANG") or "es").split(":")[0].split(".")[0]
    if code.startswith("qow"): return "qow@owee" if "@owee" in os.environ.get("LANG", "") else "qow"
    short = code.split("_")[0]
    return short if short in dict((c, n) for c, n, _l in all_langs()) else "es"

def current():
    try: v = json.load(open(SETTINGS)).get("lang")
    except (OSError, ValueError, AttributeError): v = None
    return v if v in dict((c, n) for c, n, _l in all_langs()) else system_default()

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
    if os.path.isdir(LOCDIR): os.environ["LOCPATH"] = LOCDIR + (":" + os.environ["LOCPATH"] if os.environ.get("LOCPATH") else "")
    loc = locale_of(LANG)
    for cand in (loc, loc.replace("UTF-8", "utf8")):
        try: locale.setlocale(locale.LC_ALL, cand)
        except locale.Error: continue
        os.environ["LANG"] = cand; os.environ["LANGUAGE"] = cand.split(".")[0] + ":" + LANG.split("@")[0] + ("" if any(c == LANG for c, _n, _l in LANGS) else ":en")
        return True
    return False
_CAT = {} if LANG == "es" else (_load(LANG) or _load("en"))      # idioma sin traducción propia (uno añadido por el usuario): los textos de OweeLinux salen en inglés, no en español
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

def apply_direction():
    """Dirección del texto según el idioma elegido (no según un LANG heredado): derecha→izquierda en árabe, persa y urdu. Llamar después de importar Gtk."""
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk
    Gtk.Widget.set_default_direction(Gtk.TextDirection.RTL if is_rtl(LANG) else Gtk.TextDirection.LTR)
