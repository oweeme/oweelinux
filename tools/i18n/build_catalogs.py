#!/usr/bin/env python3
"""Genera desktop/i18n/<idioma>.json (clave = texto en español del código, valor = traducción) a partir de tools/i18n/keys.json y de las traducciones tr/t*.py.
Comprueba que no falte ninguna clave y que se conserven los marcadores {0}, {1:.0f}, %s. Uso: build_catalogs.py"""
import glob, importlib.util, json, os, re, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
LANGS = ["en", "pt", "fr", "de", "ru", "zh", "ja"]                      # tr/t*.py (índice → tupla en este orden)
LANGS9 = ["it", "uk", "ko", "ar", "fa", "hi", "ur", "id", "ms"]            # tr9/a*.py (mismo formato, idiomas nuevos)
LANGS10 = ["pl", "fi", "sv"]                                              # tr10/b*.py
keys = json.load(open(os.path.join(AQUI, "keys.json"), encoding="utf-8"))
def load(pattern):
    out = {}
    for f in sorted(glob.glob(os.path.join(AQUI, pattern))):
        spec = importlib.util.spec_from_file_location("t", f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); out.update(m.T)
    return out
T, T9, T10 = load("tr/t*.py"), load("tr9/a*.py"), load("tr10/b*.py")
import ast                                                                         # textos que el código ya no usa: no hace falta traducirlos
usados = set()
for f in glob.glob(os.path.join(RAIZ, "desktop", "**", "*.py"), recursive=True) + [x for x in glob.glob(os.path.join(RAIZ, "desktop", "session", "*")) if os.path.isfile(x)]:
    try: tree = ast.parse(open(f, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError): continue
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("_", "N_") and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str): usados.add(n.args[0].value)
ph = lambda s: sorted(re.findall(r"\{\d+[^}]*\}|%s", s))
errores = 0
for i, k in enumerate(keys):
    if k not in usados and i in T and i in T9 and i in T10: continue
    for tabla, langs, nombre in ((T, LANGS, "tr"), (T9, LANGS9, "tr9"), (T10, LANGS10, "tr10")):
        if i not in tabla:
            if k in usados: print(f"FALTA la traducción {i} ({nombre}): {k!r}"); errores += 1
            continue
        if len(tabla[i]) != len(langs): print(f"#{i} ({nombre}): {len(tabla[i])} traducciones, se esperaban {len(langs)}"); errores += 1; continue
        for lg, tr in zip(langs, tabla[i]):
            if ph(k) != ph(tr) and not (i == 305):                               # 305 (fecha) puede reordenar los marcadores
                print(f"MARCADORES distintos en {lg} #{i}: {k!r} → {tr!r}"); errores += 1
out = os.path.join(RAIZ, "desktop", "i18n"); os.makedirs(out, exist_ok=True)
for tabla, langs in ((T, LANGS), (T9, LANGS9), (T10, LANGS10)):
    for j, lg in enumerate(langs):
        cat = {k: tabla[i][j] for i, k in enumerate(keys) if i in tabla and k in usados}
        json.dump(cat, open(os.path.join(out, lg + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=False)
print(f"{len(usados)} textos en uso × {len(LANGS) + len(LANGS9) + len(LANGS10)} idiomas → {out}   ({errores} problemas)")
sys.exit(1 if errores else 0)
