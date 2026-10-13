"""Idioma: idioma de todo el sistema (OweeLinux, español, inglés, portugués, francés, alemán, ruso, chino, japonés y Owee). Al elegirlo:
 · se guarda en settings.json (el panel, Ajustes y las apps propias lo leen) y el panel y esta ventana se reinician solos;
 · LANG y LANGUAGE se escriben en ~/.config/labwc/environment (las apps que lancen los atajos) y ~/.config/plasma-localerc (apps de KDE);
 · la sesión siguiente arranca ya con ese idioma (owee-session lee settings.json);
 · se activa el método de escritura que le corresponde (chino → pinyin, japonés → Mozc, Owee → teclado Owee) y la distribución de teclas adecuada.
Las apps que ya estaban abiertas siguen en el idioma anterior hasta que las cierres y las abras de nuevo."""
import json, os, sys
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
import owee_i18n
from owee_i18n import _
from .base import Page, page_box, scrolled, heading, row, dropdown, run, config_home
from . import teclado, metodos
import shutil

NUM_RULE_SRC = ["/usr/share/owee/fontconfig/60-owee-numerals.conf", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "i18n", "60-owee-numerals.conf")]
NUM_RULE = os.path.join(config_home(), "fontconfig", "conf.d", "60-owee-numerals.conf")
ACTIVE_LANGS = ("zh", "ja", "qow", "qow@owee")             # idiomas cuyo método de escritura se activa desde el principio (como el pinyin en un equipo chino)

def set_numerals(on):
    """Cifras Owee Script (0-9) en todas las apps SOLO con el idioma «Owee (Owee Script)»: regla de fontconfig del usuario (se lee al abrir cada app). En otros idiomas se quita."""
    if on:
        src = next((p for p in NUM_RULE_SRC if os.path.exists(p)), None)
        if src and any(os.path.exists(p) for p in ("/usr/share/fonts/truetype/owee-numerals/OweeNumerals-Regular.ttf",)):
            os.makedirs(os.path.dirname(NUM_RULE), exist_ok=True); shutil.copyfile(src, NUM_RULE)
    else:
        try: os.remove(NUM_RULE)
        except OSError: pass

LAYOUT_FOR = {"es": "latam", "en": "us", "pt": "br", "fr": "fr", "de": "de", "ru": "us,ru", "zh": "us", "ja": "jp", "qow": "us", "qow@owee": "us"}

def write_locale_files(code):
    loc = owee_i18n.locale_of(code); lang2 = code.split("@")[0]
    chain = {"qow@owee": "qow@owee:qow:es", "qow": "qow:es"}.get(code, f"{lang2}:en" if lang2 != "en" else "en")
    teclado.write_env({"LANG": loc, "LANGUAGE": chain})
    f = os.path.join(config_home(), "plasma-localerc"); os.makedirs(os.path.dirname(f), exist_ok=True)
    tmp = f + ".tmp"; open(tmp, "w").write(f"[Formats]\nLANG={loc}\n\n[Translations]\nLANGUAGE={chain}\n"); os.replace(tmp, f)

class Idioma(Page):
    title = _("Idioma"); icon = "owee-set-language"; group = "Personal"; order = 40; keywords = _("idioma español inglés owee chino japonés ruso traducción")
    def build(self, app):
        self.app = app; b = page_box(_("Idioma"), _("Cambia el idioma de todo el sistema. El panel y esta ventana se reinician solos; las apps abiertas cambian cuando las vuelvas a abrir."))
        b.append(heading(_("Idioma de la interfaz")))
        have = owee_i18n.installed_locales()
        opts = []
        for code, name, loc in owee_i18n.LANGS:
            ok = loc.lower().replace("utf8", "utf-8") in have or code == "es"
            opts.append((code, name if ok else name + "  ·  " + _("(sin instalar)")))
        self.dd = dropdown(opts, owee_i18n.LANG, self.choose)
        b.append(row(_("Idioma"), self.dd, _("Español, inglés, portugués, francés, alemán, ruso, chino, japonés y Owee")))
        self.note = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); b.append(self.note)
        b.append(heading(_("Escribir en otros idiomas")))
        b.append(Gtk.Label(label=_("Al elegir un idioma se activa su método de escritura (por ejemplo pinyin para chino). Se cambia entre métodos con Ctrl + Espacio. Los métodos se gestionan en Teclado."), xalign=0, wrap=True, css_classes=["dim-label"]))
        return scrolled(b)

    def choose(self, code):
        if code == owee_i18n.LANG: return
        write_locale_files(code)
        # método de escritura y distribución sugeridos
        methods = [m for m in metodos.enabled() if m not in ("pinyin", "mozc", "owee")]
        for n, _t, langs in metodos.available():
            if code in langs and n not in methods: methods.append(n)
        lay = LAYOUT_FOR.get(code, "us"); first = lay.split(",")[0]
        env = teclado.read_env()
        if env.get("XKB_DEFAULT_LAYOUT", "us") in ("us", "latam", "es", "br", "pt", "fr", "de", "it", "gb", "jp", "ru", "us,ru"):
            teclado.write_env({"XKB_DEFAULT_LAYOUT": lay, "XKB_DEFAULT_VARIANT": "", "XKB_DEFAULT_OPTIONS": "grp:alt_shift_toggle" if "," in lay else ""})
        metodos.write_profile(lay, methods, active=code in ACTIVE_LANGS and len(methods) > 0)
        set_numerals(code == "qow@owee")
        self.app.change(lang=code)                                    # el panel vigila settings.json y se reinicia con el idioma nuevo
        self.note.set_text(_("Idioma cambiado. Reiniciando esta ventana…"))
        from . import rcxml; rcxml.reconfigure()
        GLib.timeout_add(900, self.restart)

    def restart(self):
        """Reinicia Ajustes en el idioma nuevo (los textos se fijan al arrancar)."""
        os.execv(sys.executable, [sys.executable] + sys.argv); return False
PAGE = Idioma()
