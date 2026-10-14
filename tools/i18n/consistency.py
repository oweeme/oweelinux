#!/usr/bin/env python3
"""Coherencia de idiomas: la tabla única (owee_i18n.LANGS / LANG_INFO) debe coincidir con lo que ofrecen Teclado, Métodos de escritura, los catálogos y los locales de la imagen.
No necesita GTK. Uso: consistency.py   →   imprime los problemas y termina con código 1 si hay alguno."""
import ast, json, os, re, sys
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(R, "desktop", "shell"))
import owee_i18n
errs = []
def lit(path, name):
    for n in ast.walk(ast.parse(open(os.path.join(R, path), encoding="utf-8").read())):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets): return n.value
    raise SystemExit(f"no encuentro {name} en {path}")
# distribuciones de Teclado: ("us", "intl", _("…")) → clave «us(intl)»
layouts = set()
for e in lit("desktop/shell/ajustes/teclado.py", "LAYOUTS").elts:
    l, v = e.elts[0].value, e.elts[1].value; layouts.add(f"{l}({v})" if v else l)
# métodos de escritura: ("hangul", _("…"), ("ko",))
methods = {e.elts[0].value: [c.value for c in e.elts[2].elts] for e in lit("desktop/shell/ajustes/metodos.py", "CATALOG").elts}
codes = [c for c, _n, _l in owee_i18n.LANGS]
if len(set(codes)) != len(codes): errs.append("códigos de idioma repetidos")
for c in codes:
    if c not in owee_i18n.LANG_INFO: errs.append(f"{c}: falta en LANG_INFO")
for c in owee_i18n.LANG_INFO:
    if c not in codes: errs.append(f"{c}: está en LANG_INFO pero no en LANGS")
used = set()
for c, (lay, method, rtl) in owee_i18n.LANG_INFO.items():
    for k in lay.split(","):
        used.add(k)
        if k not in layouts: errs.append(f"{c}: la distribución «{k}» no existe en Teclado")
    if method and method not in methods: errs.append(f"{c}: el método «{method}» no existe en Métodos de escritura")
    elif method and c not in methods[method]: errs.append(f"{c}: Métodos de escritura no lo sugiere para «{method}»")
for m, langs in methods.items():
    for c in langs:
        if owee_i18n.LANG_INFO.get(c, (0, None))[1] != m: errs.append(f"el método «{m}» sugiere «{c}» pero LANG_INFO no lo activa")
ALIAS = {"us(intl)": "en", "gb": "en", "es": "es", "pt": "pt", "kr": "ko", "jp": "ja", "latam": "es", "in(bolnagri)": "hi", "id": "id"}          # variantes de un idioma que ya tiene su propia entrada
for k in sorted(layouts - used):
    if k not in ALIAS: errs.append(f"la distribución «{k}» de Teclado no tiene un idioma de interfaz")
for c in ("ar", "fa", "ur"):
    if not owee_i18n.is_rtl(c): errs.append(f"{c} debería ser de derecha a izquierda")
cat = os.path.join(R, "desktop", "i18n")
for c in codes:
    if c == "es": continue
    if not os.path.exists(os.path.join(cat, c + ".json")): errs.append(f"{c}: falta el catálogo desktop/i18n/{c}.json" + (" (se genera con build_owee_catalog.py)" if c.startswith("qow") else ""))
ov = open(os.path.join(R, "tools", "ostree-proto", "overlay-lite.sh"), encoding="utf-8").read()
m = re.search(r"for l in ([A-Za-z_ ]+); do chroot \"\$R\" localedef", ov)
gen = set(m.group(1).split()) if m else set()
for c, _n, loc in owee_i18n.LANGS:
    base = loc.split(".")[0]
    if not c.startswith("qow") and base not in gen: errs.append(f"{c}: el locale {base} no se genera en overlay-lite.sh")
keys = json.load(open(os.path.join(R, "tools", "i18n", "keys.json"), encoding="utf-8"))
for c in codes:
    p = os.path.join(cat, c + ".json")
    if os.path.exists(p):
        have = json.load(open(p, encoding="utf-8")); n = sum(1 for k in keys if k in have)
        print(f"  {c:9s} {n:4d} textos traducidos")
print(f"{len(codes)} idiomas · {len(layouts)} distribuciones · {len(methods)} métodos · {len(errs)} problemas")
for e in errs: print("  PROBLEMA:", e)
sys.exit(1 if errs else 0)
