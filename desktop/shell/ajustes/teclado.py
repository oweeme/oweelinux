"""Teclado: distribución(es) de teclas y repetición. La distribución se guarda en ~/.config/labwc/environment (XKB_DEFAULT_*) y `labwc --reconfigure` la aplica al instante."""
import os, re
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, dropdown, slider, run, Debounce, config_home
from . import rcxml, metodos
from owee_i18n import _

LAYOUTS = [("us", "", _("Inglés (EE. UU.)")), ("latam", "", _("Español (Latinoamérica)")), ("es", "", _("Español (España)")), ("us", "intl", _("Inglés (EE. UU., internacional)")),
           ("br", "", _("Portugués (Brasil)")), ("pt", "", _("Portugués (Portugal)")), ("fr", "", _("Francés")), ("de", "", _("Alemán")), ("it", "", _("Italiano")), ("gb", "", _("Inglés (Reino Unido)")),
           ("ru", "", _("Ruso")), ("jp", "", _("Japonés")), ("kr", "", _("Coreano")), ("ua", "", _("Ucraniano"))]
ENV = os.path.join(config_home(), "labwc", "environment")
KEYS = [f"{l}({v})" if v else l for l, v, _n in LAYOUTS]

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

def split_layout(spec):
    """'latam,us' + variantes → lista de claves 'latam', 'us(intl)'."""
    return spec

class Teclado(Page):
    title = _("Teclado"); icon = "owee-set-keyboard"; group = "Dispositivos"; order = 30; keywords = _("distribución idioma teclas repetición")
    def build(self, app):
        self.deb = Debounce(300); e = read_env(); lay = [x for x in e.get("XKB_DEFAULT_LAYOUT", "us").split(",") if x]; var = e.get("XKB_DEFAULT_VARIANT", "").split(",")
        keyof = lambda i: (f"{lay[i]}({var[i]})" if i < len(var) and var[i] else lay[i]) if i < len(lay) else None
        self.cur = [keyof(0) or "us", keyof(1) or ""]
        b = page_box(_("Teclado"), _("El cambio se aplica al instante en toda la sesión.")); b.append(heading(_("Distribución")))
        opts = [(k, n) for k, (l, v, n) in zip(KEYS, LAYOUTS)]
        b.append(row(_("Distribución principal"), dropdown(opts, self.cur[0], lambda k: self.set(0, k))))
        b.append(row(_("Segunda distribución"), dropdown([("", _("Ninguna"))] + opts, self.cur[1], lambda k: self.set(1, k)), _("Con dos distribuciones, se cambia de una a otra con Alt + Mayús")))
        b.append(heading(_("Repetición de teclas")))
        rate = int(rcxml.get("keyboard/repeatRate", default="25") or 25); delay = int(rcxml.get("keyboard/repeatDelay", default="600") or 600)
        b.append(row(_("Velocidad de repetición (por segundo)"), slider(5, 60, rate, lambda v: self.deb(lambda: rcxml.set_values([("keyboard/repeatRate", round(v))])), width=260)))
        b.append(row(_("Retardo antes de repetir (ms)"), slider(150, 1000, delay, lambda v: self.deb(lambda: rcxml.set_values([("keyboard/repeatDelay", round(v))])), step=10, width=260)))
        av = metodos.available(); on = metodos.enabled()
        if av:
            b.append(heading(_("Métodos de escritura")))
            b.append(Gtk.Label(label=_("Para escribir en chino, japonés, coreano u Owee. Cambia entre métodos con Ctrl + Espacio."), xalign=0, wrap=True, css_classes=["dim-label"]))
            for name, text, _langs in av:
                sw = Gtk.Switch(active=name in on); sw.connect("notify::active", lambda w, _p, n=name: self.toggle_method(n, w.get_active())); b.append(row(text, sw))
            act = Gtk.Switch(active=metodos.active_by_default()); act.connect("notify::active", lambda w, _p: metodos.write_profile(self.cur[0].split("(")[0] if self.cur and self.cur[0] else "us", metodos.enabled(), active=w.get_active()))
            b.append(row(_("Escribir con el método activo desde el principio"), act, _("Sin esto, hay que pulsar Ctrl + Espacio para empezar a escribir con pinyin, Mozc u Owee")))
        return scrolled(b)

    def toggle_method(self, name, active):
        cur = metodos.enabled(); cur = [m for m in cur if m != name] + ([name] if active else [])
        metodos.write_profile(self.cur[0].split("(")[0] if self.cur and self.cur[0] else "us", cur)

    def set(self, idx, key):
        self.cur[idx] = key; keys = [k for k in self.cur if k]
        lay = ",".join(k.split("(")[0] for k in keys); var = ",".join((k.split("(")[1].rstrip(")") if "(" in k else "") for k in keys)
        write_env({"XKB_DEFAULT_LAYOUT": lay, "XKB_DEFAULT_VARIANT": var if var.strip(",") else "", "XKB_DEFAULT_OPTIONS": "grp:alt_shift_toggle" if len(keys) > 1 else ""})
        rcxml.reconfigure()
        metodos.write_profile(lay, metodos.enabled())            # la distribución principal es también la base de Fcitx5
PAGE = Teclado()
