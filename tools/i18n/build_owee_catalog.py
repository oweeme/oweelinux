#!/usr/bin/env python3
"""Genera los catálogos de Owee de la interfaz (qow.json en romano y qow@owee.json en Owee Script) a partir del glosario del proyecto Owee (08_Integracion/datos/ui_glosario.tsv,
columnas en / es / owee) y de los catálogos en español→inglés. Una cadena se traduce solo si coincide por completo con una entrada del glosario (por el español o por el inglés);
el resto se muestra en español (así nunca se inventa vocabulario). Uso: build_owee_catalog.py REPO_OWEE [DIR_SALIDA]"""
import json, os, sys
repo = os.path.abspath(sys.argv[1]); AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(RAIZ, "desktop", "i18n")
sys.path.insert(0, os.path.join(repo, "08_Integracion", "herramientas"))
from owee_script import to_script
en_cat = json.load(open(os.path.join(RAIZ, "desktop", "i18n", "en.json"), encoding="utf-8"))
glos = {}
for l in open(os.path.join(repo, "08_Integracion", "datos", "ui_glosario.tsv"), encoding="utf-8").read().splitlines()[1:]:
    c = l.split("\t") + ["", "", ""]
    if c[2]: glos[("es", c[1].strip().lower())] = c[2].strip(); glos[("en", c[0].strip().lower())] = c[2].strip()
norm = lambda s: s.strip().lower().rstrip(":").strip()
roman, script, hits = {}, {}, 0
for es, en in en_cat.items():
    o = glos.get(("es", norm(es))) or glos.get(("en", norm(en)))
    if o: roman[es] = o; script[es] = to_script(o); hits += 1
json.dump(roman, open(os.path.join(out, "qow.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(script, open(os.path.join(out, "qow@owee.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
# Lista de textos de la interfaz SIN traducción (etiquetas cortas): el autor del idioma decide la palabra y la añade a ui_glosario.tsv (columnas en, es, owee)
pend = [(en_cat[k], k) for k in en_cat if k not in roman and len(k) <= 40 and "{" not in k and "%" not in k and not k.startswith(("[", "`")) and len(k.split()) <= 5 and k.strip() and en_cat[k] != k]
with open(os.path.join(RAIZ, "docs", "glosario-owee-pendiente.tsv"), "w", encoding="utf-8") as f:
    f.write("en\tes\towee\n"); f.write("".join(f"{e}\t{k}\t\n" for e, k in sorted(pend, key=lambda x: x[0].lower())))
print(f"{len(pend)} etiquetas sin traducir → docs/glosario-owee-pendiente.tsv")
print(f"{hits} de {len(en_cat)} cadenas de la interfaz tienen traducción en el glosario de Owee → {out}/qow.json y qow@owee.json")
