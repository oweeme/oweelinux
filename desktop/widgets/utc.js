#!/usr/bin/env gjs
// owee-interval: 10
// Widget de ejemplo en JAVASCRIPT (GJS, sin Node): hora universal. Mismo protocolo que en Python: una línea JSON por la salida estándar.
const { GLib } = imports.gi;
const now = GLib.DateTime.new_now_utc();
print(JSON.stringify({ text: 'UTC ' + now.format('%H:%M'), tooltip: 'Hora universal coordinada, ' + now.format('%d %b %Y') }));
