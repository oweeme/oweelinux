#!/usr/bin/env python3
"""Genera los catálogos de Owee de la interfaz (qow.json en romano y qow@owee.json en Owee Script) para TODOS los textos de la interfaz.
Orden de prioridad por cada texto:
  1. GLOSARIO del autor (08_Integracion/datos/ui_glosario.tsv, columnas en / es / owee): coincidencia completa por el español o por el inglés. Es la palabra OFICIAL.
  2. PROPUESTA (tools/i18n/owee/p*.py): frase armada por el desarrollador SOLO con raíces del léxico de Owee y la Gramática 1.1; no está aprobada por el autor del idioma. Antes de
     usarla se valida (fonología V/CV sin «i», cada raíz en lexico.tsv o lexico_ciencias.tsv); lo que no pasa se descarta.
  3. Si no hay ninguna, se muestra el español (nunca se inventa vocabulario fuera de las reglas).
Escribe también docs/owee-propuestas.tsv: una fila por texto con su origen (GLOSARIO / PROPUESTA / SIN TRADUCIR) para que el autor revise, apruebe o corrija.
Uso: build_owee_catalog.py REPO_OWEE [DIR_SALIDA]"""
import glob, importlib.util, json, os, re, sys
repo = os.path.abspath(sys.argv[1]); AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(RAIZ, "desktop", "i18n")
sys.path.insert(0, os.path.join(repo, "08_Integracion", "herramientas"))
from owee_script import to_script
keys = json.load(open(os.path.join(AQUI, "keys.json"), encoding="utf-8"))
en_cat = json.load(open(os.path.join(RAIZ, "desktop", "i18n", "en.json"), encoding="utf-8"))
glos = {}
for l in open(os.path.join(repo, "08_Integracion", "datos", "ui_glosario.tsv"), encoding="utf-8").read().splitlines()[1:]:
    c = l.split("\t") + ["", "", ""]
    if c[2]: glos[("es", c[1].strip().lower())] = c[2].strip(); glos[("en", c[0].strip().lower())] = c[2].strip()
norm = lambda s: s.strip().lower().rstrip(":").strip()
# léxico para validar las propuestas
LEX = set(); dd = os.path.join(repo, "02_Diccionario", "datos")
try:
    LEX = {l.split("\t")[0] for l in open(os.path.join(dd, "lexico.tsv"), encoding="utf-8").read().splitlines()[1:]}
    LEX |= {p for l in open(os.path.join(dd, "lexico_ciencias.tsv"), encoding="utf-8").read().splitlines()[1:] for p in l.split("\t")[0].split("-")}
except OSError: print("(aviso: sin léxico de Owee: no se usan propuestas)")
SIL = re.compile(r"(?:sh|ch|[pbtdkgfsmnlr])?[aeou]")
def valida(texto):
    t = re.sub(r"«[^»]*»", "", texto); t = re.sub(r"\{[^}]*\}|%s", "", t); t = re.sub(r"\((?=[^)]*[A-Z0-9+/])[^)]*\)", "", t)
    for tok in re.findall(r"[a-z]+(?:-[a-z]+)*", t.lower()):
        for r in tok.split("-"):
            if "".join(SIL.findall(r)) != r or (r not in LEX and re.sub(r"([aeou])\1+", r"\1", r) not in LEX): return False
    return True
props = {}
for f in sorted(glob.glob(os.path.join(AQUI, "owee", "p*.py"))):
    spec = importlib.util.spec_from_file_location("p", f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); props.update(m.P)
def escritura(texto):
    """Owee Script solo en las partes en Owee: los marcadores {0}, %s y los nombres «entre comillas» quedan tal cual."""
    return "".join(p if (p.startswith("{") or p == "%s" or p.startswith("«")) else to_script(p) for p in re.split(r"(\{[^}]*\}|%s|«[^»]*»)", texto) if p)
roman, script, filas = {}, {}, []
for i, es in enumerate(keys):
    en = en_cat.get(es, "")
    o = glos.get(("es", norm(es))) or glos.get(("en", norm(en)))
    origen = "GLOSARIO"
    if not o and es in en_cat and i in props and LEX and valida(props[i]): o, origen = props[i], "PROPUESTA"
    elif not o: origen = "SIN TRADUCIR"
    if o:
        m1 = re.fullmatch(r"«([^»]*)»", o)
        if m1: o = m1.group(1)                        # un nombre solo (p. ej. «Bluetooth») se muestra sin comillas
        roman[es] = o; script[es] = escritura(o)
    if es in en_cat: filas.append((es, en, o or "", origen))
json.dump(roman, open(os.path.join(out, "qow.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(script, open(os.path.join(out, "qow@owee.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
with open(os.path.join(RAIZ, "docs", "owee-propuestas.tsv"), "w", encoding="utf-8") as f:
    f.write("es\ten\towee\torigen\n"); f.write("".join("\t".join(r) + "\n" for r in filas))
n = lambda o: sum(1 for r in filas if r[3] == o)
print(f"Owee: {n('GLOSARIO')} del glosario del autor + {n('PROPUESTA')} propuestas (sin aprobar) + {n('SIN TRADUCIR')} sin traducir, de {len(filas)} textos → {out}/qow.json y qow@owee.json; revisión en docs/owee-propuestas.tsv")
