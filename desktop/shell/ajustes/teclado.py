"""Teclado: distribución(es) de teclas y repetición. La distribución se guarda en ~/.config/labwc/environment (XKB_DEFAULT_*) y `labwc --reconfigure` la aplica al instante."""
import os, re
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .base import Page, page_box, scrolled, heading, row, dropdown, slider, run, Debounce, config_home
from . import rcxml, metodos
from owee_i18n import _

LAYOUTS = [("us", "", _("Inglés (EE. UU.)")), ("latam", "", _("Español (Latinoamérica)")), ("es", "", _("Español (España)")), ("us", "intl", _("Inglés (EE. UU., internacional)")),
           ("gb", "", _("Inglés (Reino Unido)")), ("br", "", _("Portugués (Brasil)")), ("pt", "", _("Portugués (Portugal)")), ("fr", "", _("Francés")), ("de", "", _("Alemán")),
           ("it", "", _("Italiano")), ("ru", "", _("Ruso")), ("ua", "", _("Ucraniano")), ("jp", "", _("Japonés")), ("kr", "", _("Coreano")), ("ara", "", _("Árabe")),
           ("ir", "", _("Persa (farsi)")), ("in", "", _("Hindi (InScript)")), ("in", "bolnagri", _("Hindi (Bolnagri, fonético)")), ("pk", "", _("Urdu")),
           ("pl", "", _("Polaco")), ("fi", "", _("Finés")), ("se", "", _("Sueco")), ("id", "", _("Indonesio")), ("my", "", _("Malayo (jawi)"))]            # el malayo en letras latinas se escribe con «Inglés (EE. UU.)»; chino, japonés (Mozc) y coreano (Hangul) usan además un método de escritura (Métodos)
BASES = {l for l, _v, _n in LAYOUTS}
import owee_keys
KEYS = [f"{l}({v})" if v else l for l, v, _n in LAYOUTS]
ENV = owee_keys.ENV
read_env, write_env = owee_keys.read_env, owee_keys.write_env

class Teclado(Page):
    title = _("Teclado"); icon = "owee-set-keyboard"; group = "Dispositivos"; order = 30; keywords = _("distribución idioma teclas repetición")
    def build(self, app):
        self.deb = Debounce(300); lst, self.idx = owee_keys.state(); self.cur = [lst[0], lst[1] if len(lst) > 1 else ""]
        b = page_box(_("Teclado"), _("El cambio se aplica al instante en toda la sesión.")); b.append(heading(_("Distribución")))
        opts = [(k, n) for k, (l, v, n) in zip(KEYS, LAYOUTS)]
        b.append(row(_("Distribución principal"), dropdown(opts, self.cur[0], lambda k: self.set(0, k))))
        b.append(row(_("Segunda distribución"), dropdown([("", _("Ninguna"))] + opts, self.cur[1], lambda k: self.set(1, k)), _("Con dos distribuciones, se cambia de una a otra con Super + Mayús + Espacio o desde el indicador del panel")))
        b.append(heading(_("Repetición de teclas")))
        rate = int(rcxml.get("keyboard/repeatRate", default="25") or 25); delay = int(rcxml.get("keyboard/repeatDelay", default="600") or 600)
        b.append(row(_("Velocidad de repetición (por segundo)"), slider(5, 60, rate, lambda v: self.deb(lambda: rcxml.set_values([("keyboard/repeatRate", round(v))])), width=260)))
        b.append(row(_("Retardo antes de repetir (ms)"), slider(150, 1000, delay, lambda v: self.deb(lambda: rcxml.set_values([("keyboard/repeatDelay", round(v))])), step=10, width=260)))
        av = metodos.available(); on = metodos.enabled()
        if av:
            b.append(heading(_("Métodos de escritura")))
            b.append(Gtk.Label(label=_("Para escribir en chino, japonés, coreano u Owee. Al activar un método se escribe con él desde el principio. Para escribir con el teclado normal: Ctrl + Espacio, Ctrl + Mayús + Espacio o un clic en el icono del teclado del panel."), xalign=0, wrap=True, css_classes=["dim-label"]))
            for name, text, _langs in av:
                sw = Gtk.Switch(active=name in on); sw.connect("notify::active", lambda w, _p, n=name: self.toggle_method(n, w.get_active())); b.append(row(text, sw))
            act = Gtk.Switch(active=metodos.active_by_default()); act.connect("notify::active", lambda w, _p: metodos.write_profile(self.cur[0].split("(")[0] if self.cur and self.cur[0] else "us", metodos.enabled(), active=w.get_active()))
            b.append(row(_("Escribir con el método activo desde el principio"), act, _("Sin esto, hay que pulsar Ctrl + Espacio para empezar a escribir con pinyin, Mozc u Owee")))
        return scrolled(b)

    def toggle_method(self, name, active):
        """Activar un método (pinyin, Mozc, Owee…) lo deja ACTIVO desde el principio: se escribe con él sin pulsar nada. El teclado normal se recupera con Ctrl + Espacio,
        con un clic en el icono del teclado del panel o quitando el método."""
        cur = [m for m in metodos.enabled() if m != name] + ([name] if active else [])
        metodos.write_profile(owee_keys.active().split("(")[0], cur, active=bool(cur))

    def set(self, idx, key):
        self.cur[idx] = key; keys = [k for k in self.cur if k]
        owee_keys.apply(keys, min(self.idx, len(keys) - 1)); self.idx = min(self.idx, len(keys) - 1)
        metodos.write_profile(keys[self.idx].split("(")[0], metodos.enabled())            # la distribución activa es también la base de Fcitx5
PAGE = Teclado()
