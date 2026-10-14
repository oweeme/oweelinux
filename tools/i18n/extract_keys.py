#!/usr/bin/env python3
"""Recoge todos los textos marcados con _("…") y N_("…") de desktop/**/*.py (y de los scripts sin extensión de desktop/session) y actualiza keys.json:
las claves que ya existen conservan su posición (los índices de tr/t*.py dependen de ello) y las nuevas se añaden al final.
Uso: extract_keys.py [--check]   (--check no escribe: lista las claves nuevas y las que ya no se usan)"""
import ast, glob, json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); D = os.path.abspath(os.path.join(AQUI, "..", "..", "desktop"))
files = [f for f in glob.glob(D + "/**/*.py", recursive=True) if "/test_" not in f] + [f for f in glob.glob(D + "/session/*") if os.path.isfile(f) and not f.endswith((".xml", ".policy", ".service"))]
found = []
for f in sorted(files):
    try: tree = ast.parse(open(f, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError): continue
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("_", "N_") and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
            s = n.args[0].value
            if s and s not in found: found.append(s)
path = os.path.join(AQUI, "keys.json"); old = json.load(open(path, encoding="utf-8"))
new = [s for s in found if s not in old]; gone = [s for s in old if s not in found]
print(f"{len(found)} textos en el código · {len(old)} en keys.json · nuevos {len(new)} · ya sin uso {len(gone)}")
for s in new: print("  + " + s)
for s in gone: print("  - " + s)
if "--check" not in sys.argv and new: json.dump(old + new, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0); print("keys.json actualizado")
