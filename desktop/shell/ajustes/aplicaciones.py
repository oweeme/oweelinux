"""Aplicaciones predeterminadas: qué app abre cada tipo de archivo (se guarda en ~/.config/mimeapps.list con Gio, igual que en cualquier escritorio)."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio
from .base import Page, page_box, scrolled, heading, row, dropdown

TYPES = [("x-scheme-handler/http", "Navegador web"), ("inode/directory", "Archivos (carpetas)"), ("text/plain", "Texto"), ("application/pdf", "Documentos PDF"),
         ("image/png", "Imágenes"), ("audio/mpeg", "Música"), ("video/mp4", "Vídeo"), ("x-scheme-handler/mailto", "Correo electrónico"), ("application/zip", "Archivos comprimidos")]

class Aplicaciones(Page):
    title = "Aplicaciones"; icon = "owee-set-apps"; group = "Sistema"; order = 20; keywords = "predeterminadas navegador abrir con tipos de archivo"
    def build(self, app):
        b = page_box("Aplicaciones predeterminadas", "Elige con qué app se abre cada tipo de archivo o enlace.")
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
