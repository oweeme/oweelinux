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
        for code, name, loc in owee_i18n.all_langs():
            ok = loc.lower().replace("utf8", "utf-8") in have or code == "es"
            opts.append((code, name if ok else name + "  ·  " + _("(sin instalar)")))
        self.dd = dropdown(opts, owee_i18n.LANG, self.choose)
        b.append(row(_("Idioma"), self.dd, _("Los mismos idiomas en los que puedes escribir (Teclado): 17 idiomas y Owee")))
        add = Gtk.Button(label=_("Añadir otro idioma…"), halign=Gtk.Align.START); add.connect("clicked", lambda x: self.add_dialog()); b.append(add)
        self.note = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); b.append(self.note)
        b.append(heading(_("Escribir en otros idiomas")))
        b.append(Gtk.Label(label=_("Al elegir un idioma se activa su método de escritura (por ejemplo pinyin para chino). Se cambia entre métodos con Ctrl + Espacio. Los métodos se gestionan en Teclado."), xalign=0, wrap=True, css_classes=["dim-label"]))
        return scrolled(b)

    # ---- añadir un idioma que OweeLinux no trae de fábrica (italiano, griego, turco…): se genera su locale en ~/.local/share/owee/locales, sin permisos de administrador
    @staticmethod
    def supported():
        """Locales UTF-8 que Debian puede generar (/usr/share/i18n/SUPPORTED) y cuyo idioma OweeLinux aún no trae: [(nombre, locale)]."""
        have = {c for c, _n, _l in owee_i18n.all_langs()}; out = []; seen = set()
        try: lines = open("/usr/share/i18n/SUPPORTED").read().splitlines()
        except OSError: return out
        for l in lines:
            p = l.split()
            if len(p) != 2 or p[1] != "UTF-8" or "@" in p[0] or not re.fullmatch(r"[a-z]{2,3}_[A-Z]{2}\.UTF-8", p[0]): continue
            loc = p[0][:-6]; lang = loc.split("_")[0]
            if lang in have or loc in seen: continue
            seen.add(loc); name = loc; lg = tr = ""
            try:
                for ln in open("/usr/share/i18n/locales/" + loc, encoding="utf-8", errors="replace"):
                    m = re.match(r'\s*(language|territory)\s+"(.*)"', ln)
                    if m and m.group(1) == "language": lg = m.group(2)
                    elif m: tr = m.group(2)
                    if lg and tr: break
            except OSError: pass
            out.append((f"{lg} ({tr})" if lg and tr else loc, loc))
        return sorted(out)

    def add_dialog(self):
        win = Gtk.Window(title=_("Añadir otro idioma"), transient_for=self.app.get_active_window(), modal=True, default_width=420, default_height=480)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12); win.set_child(box)
        entry = Gtk.SearchEntry(placeholder_text=_("Buscar idioma…")); box.append(entry)
        lst = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE); items = self.supported()
        for name, loc in items: r = Gtk.ListBoxRow(); r.loc = loc; r.name = name; r.set_child(Gtk.Label(label=f"{name}  —  {loc}", xalign=0, margin_top=4, margin_bottom=4, margin_start=6)); lst.append(r)
        lst.set_filter_func(lambda r: entry.get_text().strip().lower() in (r.name + " " + r.loc).lower()); entry.connect("search-changed", lambda e: lst.invalidate_filter())
        box.append(Gtk.ScrolledWindow(child=lst, vexpand=True))
        note = Gtk.Label(label=_("Las aplicaciones de KDE se traducen al idioma elegido; los textos propios de OweeLinux saldrán en inglés hasta que alguien aporte la traducción."), xalign=0, wrap=True, css_classes=["dim-label"]); box.append(note)
        msg = Gtk.Label(xalign=0, wrap=True); box.append(msg)
        bar = Gtk.Box(spacing=8, halign=Gtk.Align.END); cancel = Gtk.Button(label=_("Cancelar")); ok = Gtk.Button(label=_("Añadir"), css_classes=["suggested-action"]); bar.append(cancel); bar.append(ok); box.append(bar)
        cancel.connect("clicked", lambda b: win.close())
        def go(_b):
            row = lst.get_selected_row()
            if not row: return
            ok.set_sensitive(False); msg.set_text(_("Generando el idioma… (unos segundos)"))
            os.makedirs(owee_i18n.LOCDIR, exist_ok=True); loc = row.loc
            run(["localedef", "-i", loc, "-f", "UTF-8", os.path.join(owee_i18n.LOCDIR, loc + ".UTF-8")], lambda out, code: self.added(win, msg, ok, row.name, loc, code), timeout=120)
        ok.connect("clicked", go); win.present()

    def added(self, win, msg, ok, name, loc, code):
        if not os.path.isdir(os.path.join(owee_i18n.LOCDIR, loc + ".UTF-8")):
            msg.set_text(_("No se pudo generar el idioma.")); ok.set_sensitive(True); return
        lang = loc.split("_")[0]; extra = dict(self.app.cfg.get("extra_langs", {})); extra[lang] = {"name": name, "loc": loc + ".UTF-8"}
        self.app.change(extra_langs=extra); win.close(); self.choose(lang)

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
