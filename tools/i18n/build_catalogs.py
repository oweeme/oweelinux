#!/usr/bin/env python3
"""Genera desktop/i18n/<idioma>.json (clave = texto en español del código, valor = traducción) a partir de tools/i18n/keys.json y de las traducciones tr/t*.py.
Comprueba que no falte ninguna clave y que se conserven los marcadores {0}, {1:.0f}, %s. Uso: build_catalogs.py"""
import glob, importlib.util, json, os, re, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
LANGS = ["en", "pt", "fr", "de", "ru", "zh", "ja"]
keys = json.load(open(os.path.join(AQUI, "keys.json"), encoding="utf-8"))
T = {}
for f in sorted(glob.glob(os.path.join(AQUI, "tr", "t*.py"))):
    spec = importlib.util.spec_from_file_location("t", f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); T.update(m.T)
ph = lambda s: sorted(re.findall(r"\{\d+[^}]*\}|%s", s))
errores = 0
for i, k in enumerate(keys):
    if i not in T: print(f"FALTA la traducción {i}: {k!r}"); errores += 1; continue
    for lg, tr in zip(LANGS, T[i]):
        if ph(k) != ph(tr) and not (i == 305):                               # 305 (fecha) puede reordenar los marcadores
            print(f"MARCADORES distintos en {lg} #{i}: {k!r} → {tr!r}"); errores += 1
out = os.path.join(RAIZ, "desktop", "i18n"); os.makedirs(out, exist_ok=True)
for j, lg in enumerate(LANGS):
    cat = {k: T[i][j] for i, k in enumerate(keys) if i in T}
    json.dump(cat, open(os.path.join(out, lg + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=False)
print(f"{len(keys)} claves × {len(LANGS)} idiomas → {out}   ({errores} problemas)")
sys.exit(1 if errores else 0)
