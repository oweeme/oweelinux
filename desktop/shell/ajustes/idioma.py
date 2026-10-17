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
import owee_keys
from . import teclado, metodos
import shutil

NUM_RULE_SRC = ["/usr/share/owee/fontconfig/60-owee-numerals.conf", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "i18n", "60-owee-numerals.conf")]
NUM_RULE = os.path.join(config_home(), "fontconfig", "conf.d", "60-owee-numerals.conf")

def set_numerals(on):
    """Cifras Owee Script (0-9) en todas las apps SOLO con el idioma «Owee (Owee Script)»: regla de fontconfig del usuario (se lee al abrir cada app). En otros idiomas se quita."""
    if on:
        src = next((p for p in NUM_RULE_SRC if os.path.exists(p)), None)
        if src and any(os.path.exists(p) for p in ("/usr/share/fonts/truetype/owee-numerals/OweeNumerals-Regular.ttf",)):
            os.makedirs(os.path.dirname(NUM_RULE), exist_ok=True); shutil.copyfile(src, NUM_RULE)
    else:
        try: os.remove(NUM_RULE)
        except OSError: pass


def write_locale_files(code):
    loc = owee_i18n.locale_of(code); lang2 = code.split("@")[0]
    chain = {"qow@owee": "qow@owee:qow:es", "qow": "qow:es"}.get(code, f"{lang2}:en" if lang2 != "en" else "en")
    teclado.write_env({"LANG": loc, "LANGUAGE": chain})
    f = os.path.join(config_home(), "plasma-localerc"); os.makedirs(os.path.dirname(f), exist_ok=True)
    tmp = f + ".tmp"; open(tmp, "w").write(f"[Formats]\nLANG={loc}\n\n[Translations]\nLANGUAGE={chain}\n"); os.replace(tmp, f)

class Idioma(Page):
    title = _("Idioma"); icon = "owee-set-language"; group = "Personal"; order = 40; keywords = _("idioma español inglés owee chino japonés coreano ruso árabe persa hindi urdu indonesio malayo traducción")
    def build(self, app):
        self.app = app; b = page_box(_("Idioma"), _("Cambia el idioma de todo el sistema. El panel y esta ventana se reinician solos; las apps abiertas cambian cuando las vuelvas a abrir."))
        b.append(heading(_("Idioma de la interfaz")))
        have = owee_i18n.installed_locales()
        opts = []
        for code, name, loc in owee_i18n.LANGS:
            ok = loc.lower().replace("utf8", "utf-8") in have or code == "es"
            opts.append((code, name if ok else name + "  ·  " + _("(sin instalar)")))
        self.dd = dropdown(opts, owee_i18n.LANG, self.choose)
        b.append(row(_("Idioma"), self.dd, _("Los mismos idiomas en los que puedes escribir (Teclado): 17 idiomas y Owee")))
        self.note = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); b.append(self.note)
        b.append(heading(_("Escribir en otros idiomas")))
        b.append(Gtk.Label(label=_("Al elegir un idioma se activa su método de escritura (por ejemplo pinyin para chino). Se cambia entre métodos con Ctrl + Espacio. Los métodos se gestionan en Teclado."), xalign=0, wrap=True, css_classes=["dim-label"]))
        return scrolled(b)

    def choose(self, code):
        if code == owee_i18n.LANG: return
        write_locale_files(code)
        # método de escritura y distribución sugeridos
        own = [n for n, _t, _l in metodos.CATALOG]
        methods = [m for m in metodos.enabled() if m not in own]; want = owee_i18n.method_for(code)
        if want and any(n == want for n, _t, _l in metodos.available()): methods.append(want)
        lay = owee_i18n.layout_for(code); keys = lay.split(",")
        cur = owee_keys.state()[0]
        if all(x.split("(")[0] in teclado.BASES for x in cur) and (set(cur) <= set(owee_i18n.all_layouts()) or len(cur) == 1):          # solo se cambia si el teclado actual es uno de los nuestros (no uno puesto a mano)
            owee_keys.apply(keys, len(keys) - 1 if code in owee_i18n.NATIVE_SCRIPT else 0)       # con dos (p. ej. US + árabe) queda activa la del propio idioma si no es latino; Super + Mayús + Espacio cambia a la otra
        metodos.write_profile(keys[0], methods, active=bool(want) and len(methods) > 0)
        set_numerals(code == "qow@owee")
        self.app.change(lang=code)                                    # el panel vigila settings.json y se reinicia con el idioma nuevo
        self.note.set_text(_("Idioma cambiado. Reiniciando esta ventana…"))
        from . import rcxml; rcxml.reconfigure()
        GLib.timeout_add(250, self.restart)

    def restart(self):
        """Reinicia Ajustes en el idioma nuevo (los textos se fijan al arrancar)."""
        os.execv(sys.executable, [sys.executable] + sys.argv); return False
PAGE = Idioma()
