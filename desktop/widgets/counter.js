#!/usr/bin/env gjs
// owee-interval: 30
// Widget en JAVASCRIPT con CLIC: cuenta los clics. Al hacer clic, el panel ejecuta "on_click" (este mismo script con "inc").
const { GLib, Gio } = imports.gi;
const file = Gio.File.new_for_path(GLib.get_user_cache_dir() + '/owee-counter');
let n = 0;
try { n = parseInt(new TextDecoder().decode(file.load_contents(null)[1])) || 0; } catch (e) {}
if (ARGV[0] === 'inc') { n++; file.replace_contents(String(n), null, false, Gio.FileCreateFlags.REPLACE_DESTINATION, null); }
const me = imports.system.programInvocationName;
print(JSON.stringify({ text: 'clics ' + n, tooltip: 'Haz clic para contar', on_click: ['gjs', me, 'inc'] }));
