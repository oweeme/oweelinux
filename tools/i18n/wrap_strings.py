#!/usr/bin/env python3
"""Herramienta de desarrollo (se usó una vez, queda por si se añaden apps): envuelve en _() los textos de interfaz en español de los archivos .py indicados.
Reglas (conservadoras): solo cadenas que parecen texto para personas (letras y espacios o mayúscula inicial, con ≥ 3 letras); NO toca docstrings, claves de diccionario, comparaciones,
subíndices, argumentos de funciones «técnicas» (get, startswith, join, icon_name, css_classes…), ni f-strings con formatos anidados. Los f-strings se convierten a _("plantilla {0}", expr).
Uso: wrap_strings.py archivo.py [...]      (reescribe el archivo; revisa el resultado con git diff)"""
import ast, re, sys

TECH_CALLS = {"get", "startswith", "endswith", "join", "replace", "split", "strip", "rstrip", "lstrip", "find", "index", "count", "open", "exists", "makedirs", "remove", "getenv", "setdefault",
              "add_css_class", "remove_css_class", "set_css_classes", "has_css_class", "connect", "new_for_path", "find_program_in_path", "get_string", "format_time", "format", "strftime",
              "require_version", "import_module", "parse", "subprocess", "run", "Popen", "check_output", "Subprocess", "new", "bool", "int", "float", "isinstance", "getattr", "hasattr", "setattr",
              "print", "write", "read", "load", "dump", "dumps", "loads", "search", "match", "fullmatch", "sub", "compile", "set_property", "set_visible_child_name", "add_named", "get_property",
              "SubElement", "Element", "find", "findall", "iter", "set", "have", "which", "write_text", "read_text", "expanduser", "abspath", "basename", "dirname", "relpath", "glob", "list_timezones", "action", "emit_signal", "call", "bus_watch_name", "own_name",
              "load_from_data", "load_from_string", "load_from_path", "new_from_icon_name", "set_from_icon_name", "lookup_icon", "has_icon", "unpack", "Variant", "VariantType", "set_default_for_type", "get_default_for_type", "get_all_for_type",
              "launch_default_for_uri", "set_icon_name", "Image", "from_url", "create", "insert", "append_values", "encode", "decode"}
TECH_KW = {"icon_name", "css_classes", "application_id", "name", "id", "key", "mode", "type", "action", "command", "cmd", "encoding", "errors", "default", "flags", "namespace", "layer",
           "orientation", "xalign", "halign", "valign", "icon", "target", "path", "file", "url", "uri", "pattern", "category", "tag", "attrs", "label_class", "class", "cls", "group", "kind"}
UI_KW = {"label", "title", "placeholder_text", "tooltip_text", "text", "subtitle", "description", "hint", "heading", "name_label", "message"}
UI_CALLS = {"set_text", "set_label", "set_title", "set_tooltip_text", "set_placeholder_text", "row", "heading", "page_box", "say", "notify", "msg", "Label", "Button", "ToggleButton", "CheckButton",
            "MenuButton", "add_titled", "append_text", "LinkButton", "new_with_label", "Entry", "SearchEntry", "set_markup"}

def looks_ui(t):
    letters = len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", t))
    if letters < 3: return False
    if re.fullmatch(r"[\w./#:%@\-\[\]=*+~(),;<>]+", t) and " " not in t and not t[0].isupper(): return False       # identificadores, rutas, claves
    if re.fullmatch(r"(https?://|/|~|\.|#|org\.|com\.|@)\S*", t): return False
    if t.isupper() and " " not in t: return False                                                              # constantes (BEL, RAD)
    return " " in t or t[0].isupper() or bool(re.search(r"[áéíóúñÁÉÍÓÚ¿¡…]", t))

def main(path):
    src = open(path, encoding="utf-8").read(); tree = ast.parse(src); lines = src.splitlines(keepends=True)
    parent = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n): parent[c] = n
    starts = [0]
    for l in lines: starts.append(starts[-1] + len(l.encode("utf-8")))
    sb = src.encode("utf-8")
    def off(lineno, col): return starts[lineno - 1] + col
    def call_name(c):
        f = c.func
        return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
    def is_docstring(n):
        p = parent.get(n); return isinstance(p, ast.Expr) and isinstance(parent.get(p), (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))
    def context_ok(n):
        p = parent.get(n)
        if isinstance(p, (ast.Compare, ast.Subscript, ast.Import, ast.ImportFrom, ast.FormattedValue, ast.JoinedStr)): return False
        if isinstance(p, ast.Dict) and n in p.keys: return False
        if isinstance(p, ast.keyword):
            if p.arg in TECH_KW: return False
            call = parent.get(p)
            return p.arg in UI_KW or (isinstance(call, ast.Call) and call_name(call) in UI_CALLS)
        if isinstance(p, ast.Call):
            nm = call_name(p)
            if nm == "_" or nm in TECH_CALLS: return False
            if nm in UI_CALLS: return True
            return False
        if isinstance(p, (ast.Tuple, ast.List, ast.Set)):
            gp = parent.get(p)
            if isinstance(gp, ast.Compare) or (isinstance(gp, ast.Call) and call_name(gp) in TECH_CALLS): return False
            if isinstance(gp, ast.keyword) and gp.arg in TECH_KW: return False
            return True                                                                                         # tablas de textos (ACTIONS, TYPES…)
        if isinstance(p, (ast.Assign, ast.AnnAssign)):
            t = p.targets[0] if isinstance(p, ast.Assign) else p.target
            nm = t.id if isinstance(t, ast.Name) else ""
            return nm in ("title", "keywords", "heading", "PLACEHOLDER") if nm else False
        if isinstance(p, ast.Dict):                                                                              # valores de diccionario: solo claves de texto de interfaz
            i = p.values.index(n) if n in p.values else -1
            k = p.keys[i] if i >= 0 else None
            return isinstance(k, ast.Constant) and k.value in ("text", "title", "tooltip", "placeholder", "name", "label", "hint", "heading", "msg") or (isinstance(k, ast.Constant) and isinstance(k.value, str) and False)
        if isinstance(p, (ast.IfExp, ast.BoolOp, ast.BinOp)):
            return context_ok_up(p)
        if isinstance(p, ast.Return): return False
        return False
    def context_ok_up(p):
        q = parent.get(p)
        if q is None: return False
        return context_ok_node(p)
    def context_ok_node(n):
        return context_ok(n)
    edits = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and not is_docstring(n):
            if not looks_ui(n.value) or not context_ok(n): continue
            if parent.get(n) and isinstance(parent[n], ast.BinOp) and not isinstance(parent[n].op, ast.Mod): pass
            a, b = off(n.lineno, n.col_offset), off(n.end_lineno, n.end_col_offset)
            edits.append((a, b, "_(" + sb[a:b].decode() + ")"))
        elif isinstance(n, ast.JoinedStr) and not is_docstring(n):
            if not context_ok(n): continue
            tpl, args, bad = "", [], False
            for v in n.values:
                if isinstance(v, ast.Constant): tpl += v.value.replace("{", "{{").replace("}", "}}")
                else:
                    if v.format_spec is not None and not all(isinstance(x, ast.Constant) for x in v.format_spec.values): bad = True; break
                    spec = "".join(x.value for x in v.format_spec.values) if v.format_spec else ""
                    conv = {115: "!s", 114: "!r", 97: "!a"}.get(v.conversion, "")
                    tpl += "{%d%s%s}" % (len(args), conv, (":" + spec) if spec else ""); args.append(ast.get_source_segment(src, v.value))
            lit = re.sub(r"\{\d+[^}]*\}", "", tpl)
            if bad or not looks_ui(lit) or len(re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñ]", lit)) < 3: continue
            a, b = off(n.lineno, n.col_offset), off(n.end_lineno, n.end_col_offset)
            edits.append((a, b, "_(" + repr(tpl) + "".join(", " + x for x in args) + ")"))
    # evitar solapes (un f-string dentro de otro)
    edits.sort(); out = []; last = -1
    for a, b, t in edits:
        if a >= last: out.append((a, b, t)); last = b
    for a, b, t in reversed(out): sb = sb[:a] + t.encode() + sb[b:]
    text = sb.decode()
    if out and "from owee_i18n import" not in text:
        m = re.search(r"^(import [^\n]*\n|from [^\n]* import [^\n]*\n)(?!.*^(import|from) )", text, re.M | re.S)
        # insertar tras el último import del bloque inicial
        ims = [x for x in ast.parse(text).body if isinstance(x, (ast.Import, ast.ImportFrom))]
        last_imp = ims[-1].end_lineno if ims else 0
        tl = text.splitlines(keepends=True); tl.insert(last_imp, "from owee_i18n import _\n"); text = "".join(tl)
    open(path, "w", encoding="utf-8").write(text); print(f"{path}: {len(out)} textos envueltos")

if __name__ == "__main__":
    for p in sys.argv[1:]: main(p)
