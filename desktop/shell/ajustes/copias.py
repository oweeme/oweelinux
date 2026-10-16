"""Copias de seguridad: copia tu carpeta personal (archivos, configuración y datos de las apps) a un disco externo o a otra carpeta con `rsync`, y la restaura si hace falta.
Es una copia INCREMENTAL (la primera tarda; las siguientes solo copian lo que cambió) y NUNCA borra nada de la copia. No incluye cachés ni imágenes de contenedores (se pueden volver a bajar).
La copia queda en <destino>/OweeLinux-<usuario>/. Se recomienda un disco distinto del propio equipo: si falla el disco, una copia en el mismo disco se pierde con él."""
import getpass, os, time
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib
import owee_config
from .base import Page, page_box, scrolled, heading, row, dropdown, run, have
from owee_i18n import _

EXCLUDES = [".cache/", ".local/share/Trash/", ".local/share/containers/", ".var/app/*/cache/", "node_modules/", "target/debug/", ".gradle/caches/", ".npm/_cacache/", ".cargo/registry/cache/", "*.tmp"]

def candidates():
    """Carpetas donde suele montarse un disco externo: /run/media/<usuario>/*, /media/*, /mnt/* (solo las que están montadas)."""
    out = []
    for base in (f"/run/media/{getpass.getuser()}", "/media", "/mnt"):
        try:
            for n in sorted(os.listdir(base)):
                p = os.path.join(base, n)
                if os.path.ismount(p): out.append(p)
        except OSError: pass
    return out

class Copias(Page):
    title = _("Copias de seguridad"); icon = "owee-set-backup"; group = "Sistema"; order = 18; keywords = _("copia seguridad respaldo backup restaurar disco externo rsync")
    def build(self, app):
        self.app = app; self.home = os.path.expanduser("~"); self.busy = False
        b = page_box(_("Copias de seguridad"), _("Copia tu carpeta personal a un disco externo. La primera copia tarda; las siguientes solo copian lo que cambió y nunca borran nada de la copia."))
        b.append(heading(_("Destino")))
        self.dests = candidates(); cur = app.cfg.get("backup_dest", "")
        if cur and cur not in self.dests: self.dests.append(cur)
        opts = [(d, d) for d in self.dests] + [("", _("Elegir otra carpeta…"))]
        self.dd = dropdown(opts, cur if cur in self.dests else (self.dests[0] if self.dests else ""), self.pick); b.append(row(_("Copiar a"), self.dd))
        self.dest = cur if cur in self.dests else (self.dests[0] if self.dests else "")
        self.info = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); b.append(self.info)
        bt = Gtk.Box(spacing=8); self.go = Gtk.Button(label=_("Hacer copia ahora"), css_classes=["suggested-action"]); self.go.connect("clicked", lambda _b: self.backup())
        self.rs = Gtk.Button(label=_("Restaurar desde la copia…")); self.rs.connect("clicked", lambda _b: self.confirm_restore()); bt.append(self.go); bt.append(self.rs); b.append(bt)
        self.status = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"]); b.append(self.status)
        b.append(Gtk.Label(label=_("Conviene un disco distinto del equipo. Sin cachés ni imágenes de contenedores (se pueden volver a bajar)."), xalign=0, wrap=True, css_classes=["dim-label"]))
        self.refresh_info(); return scrolled(b)

    def refresh(self):
        if hasattr(self, "info"): self.refresh_info()

    def target(self): return os.path.join(self.dest, f"OweeLinux-{getpass.getuser()}") if self.dest else ""

    def refresh_info(self):
        last = self.app.cfg.get("backup_last", 0); t = self.target()
        self.info.set_text((_("Última copia: {0}", time.strftime("%Y-%m-%d %H:%M", time.localtime(last))) if last else _("Todavía no hay copias.")) + ("" if self.dest else "  ·  " + _("Conecta un disco externo o elige una carpeta.")))
        ok = bool(self.dest) and have("rsync") and not self.busy; self.go.set_sensitive(ok); self.rs.set_sensitive(ok and os.path.isdir(t))

    def pick(self, key):
        if key: self.dest = key; self.app.change(backup_dest=key); self.refresh_info(); return
        dlg = Gtk.FileDialog(title=_("Elegir otra carpeta…"))
        def done(d, res):
            try: f = d.select_folder_finish(res)
            except GLib.Error: return
            self.dest = f.get_path(); self.app.change(backup_dest=self.dest); self.refresh_info()
        dlg.select_folder(self.b_root(), None, done)

    def b_root(self): return self.go.get_root()

    def rsync(self, src, dst, ok_msg):
        if not (src and dst): return
        try: os.makedirs(dst, exist_ok=True)
        except OSError as e: self.status.set_text(_("No se pudo: {0}", str(e))); return
        same = dst != self.home and os.stat(self.home).st_dev == os.stat(dst).st_dev
        self.busy = True; self.refresh_info()
        self.status.set_text((_("Aviso: el destino está en el mismo disco que tu carpeta personal; si el disco falla, la copia se pierde con él.") + "\n" if same else "") + _("Copiando… (puede tardar; puedes seguir trabajando)"))
        argv = ["rsync", "-a", "--partial", "--safe-links"] + [f"--exclude={e}" for e in EXCLUDES] + [src.rstrip("/") + "/", dst.rstrip("/") + "/"]
        def done(out, code):
            self.busy = False
            if code in (0, 24): self.app.change(backup_last=int(time.time())); self.status.set_text(ok_msg)
            else: self.status.set_text(_("No se pudo: {0}", (out.strip().splitlines() or ["rsync " + str(code)])[-1][:160]))
            self.refresh_info()
        run(argv, done, timeout=6 * 3600)

    def backup(self): self.rsync(self.home, self.target(), _("Copia terminada"))

    def confirm_restore(self):
        dlg = Gtk.AlertDialog(message=_("¿Restaurar desde la copia?"), detail=_("Se copiarán de vuelta tus archivos de la copia; los que ya existen se sobrescriben con la versión de la copia. No se borra nada de tu carpeta."), buttons=[_("Cancelar"), _("Restaurar")], cancel_button=0, default_button=1)
        dlg.choose(self.b_root(), None, lambda d, res: self.rsync(self.target(), self.home, _("Restauración terminada")) if self._ans(d, res) == 1 else None)

    @staticmethod
    def _ans(d, res):
        try: return d.choose_finish(res)
        except GLib.Error: return 0
PAGE = Copias()
