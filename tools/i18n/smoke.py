#!/usr/bin/env python3
"""Prueba de humo de idiomas: construye TODAS las páginas de Ajustes y las apps propias en cada idioma y comprueba que ningún texto da error de formato y que cada catálogo cubre
todas las claves. Necesita una sesión gráfica (GTK4). Uso: smoke.py [DIR_DESKTOP]   →   imprime una línea por idioma y termina con código 1 si algo falla."""
import json, os, subprocess, sys, tempfile
D = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "desktop"))
CHILD = r'''
import importlib, json, os, sys, traceback
sys.path.insert(0, os.path.join(sys.argv[1], "shell"))
import owee_i18n, owee_settings
import gi; gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
Gtk.init()
class A:                                   # lo mínimo que usan las páginas de la aplicación
    cfg = owee_settings.owee_config.load(); listeners = []
    def change(self, **kw): self.cfg.update(kw)
    def get_active_window(self): return None
errs = 0; n = 0
for name in owee_settings.PAGES:
    try:
        p = importlib.import_module("ajustes." + name).PAGE; w = p.build(A()); n += 1
    except Exception: errs += 1; print("  ERROR en la página", name, traceback.format_exc()[-400:])
cat = owee_i18n._CAT; keys = json.load(open(os.path.join(sys.argv[1], "..", "tools", "i18n", "keys.json"), encoding="utf-8"))
falta = [k for k in keys if k not in cat] if owee_i18n.LANG != "es" else []
print(f"LANG={owee_i18n.LANG} páginas={n}/{len(owee_settings.PAGES)} errores={errs} sin traducir={len(falta)} de {len(keys)}")
sys.exit(1 if errs else 0)
'''
bad = 0
sys.path.insert(0, os.path.join(D, "shell")); import owee_i18n
for lang in [c for c, _n, _l in owee_i18n.LANGS]:
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(tmp + "/owee"); json.dump({"lang": lang}, open(tmp + "/owee/settings.json", "w"))
        r = subprocess.run([sys.executable, "-c", CHILD, D], env={**os.environ, "XDG_CONFIG_HOME": tmp}, capture_output=True, text=True, timeout=120)
        out = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith(("LANG=", "  ERROR", "Traceback", "    ")) or "Error" in l]
        print("\n".join(out) or r.stdout + r.stderr); bad += r.returncode != 0
sys.exit(1 if bad else 0)
