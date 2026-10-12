imports.gi.versions.Gtk = '4.0';
const { Gtk, GLib, Gio } = imports.gi;
function report(tag) {
  const [ok, bytes] = GLib.file_get_contents('/proc/self/smaps_rollup'); const t = new TextDecoder().decode(bytes);
  const g = k => { const m = t.match(new RegExp(k + ':\\s+(\\d+)')); return m ? parseInt(m[1]) / 1024 : 0; };
  print(`RESULT ${tag}: Rss=${g('Rss').toFixed(0)} Pss=${g('Pss').toFixed(0)} USS=${(g('Private_Clean') + g('Private_Dirty')).toFixed(0)} MB`);
}
const app = new Gtk.Application({ application_id: 'org.t.js' + GLib.getenv('USER') + Math.floor(Math.random() * 1e6) });
app.connect('activate', a => {
  const w = new Gtk.ApplicationWindow({ application: a, default_width: 300, default_height: 40 });
  w.set_child(new Gtk.Label({ label: 'hola' })); w.present();
  GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 6, () => { report('js-gjs-gtk4'); a.quit(); return GLib.SOURCE_REMOVE; });
});
app.run([]);
