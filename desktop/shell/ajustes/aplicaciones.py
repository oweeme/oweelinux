"""Aplicaciones predeterminadas: qué app abre cada tipo de archivo (se guarda en ~/.config/mimeapps.list con Gio, igual que en cualquier escritorio)."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio
from .base import Page, page_box, scrolled, heading, row, dropdown
from owee_i18n import _

TYPES = [("x-scheme-handler/http", _("Navegador web")), ("inode/directory", _("Archivos (carpetas)")), ("text/plain", _("Texto")), ("application/pdf", _("Documentos PDF")),
         ("image/png", _("Imágenes")), ("audio/mpeg", _("Música")), ("video/mp4", _("Vídeo")), ("x-scheme-handler/mailto", _("Correo electrónico")), ("application/zip", _("Archivos comprimidos"))]

class Aplicaciones(Page):
    title = _("Aplicaciones"); icon = "owee-set-apps"; group = "Sistema"; order = 20; keywords = _("predeterminadas navegador abrir con tipos de archivo")
    def build(self, app):
        b = page_box(_("Aplicaciones predeterminadas"), _("Elige con qué app se abre cada tipo de archivo o enlace."))
        for mime, name in TYPES:
            apps = [a for a in Gio.AppInfo.get_all_for_type(mime) if a.should_show()]
            if not apps:                                                    # sin caché mimeinfo (imagen inmutable): se busca en los propios .desktop (MimeType=)
                apps = [a for a in Gio.AppInfo.get_all() if a.should_show() and mime in (a.get_supported_types() or [])]
            if not apps: continue
            cur = Gio.AppInfo.get_default_for_type(mime, False); cur_id = cur.get_id() if cur else apps[0].get_id()
            opts = [(a.get_id(), a.get_name()) for a in apps]
            def on(k, mime=mime, apps=apps): next(a for a in apps if a.get_id() == k).set_as_default_for_type(mime)
            b.append(row(name, dropdown(opts, cur_id, on)))
        return scrolled(b)
PAGE = Aplicaciones()
