"""Calculadora en Owee: nombres de las cifras y de las operaciones, y lectura en voz alta (en romano) de números y expresiones. Es un port a Python de
07_Sitio_Web/calculadora.js del proyecto del idioma (https://github.com/oweeme/owee): mismas reglas de Matemáticas 2.0 —coeficiente + escala (tanu 10, gabu 100, soku 1000, benu 1 000 000),
las posiciones con 0 no se leen, «be» (1) sí se lee, «doto» es la coma decimal y «po» el signo negativo—."""
import re

NOMBRES = ["cho", "be", "du", "ga", "fo", "sa", "ku", "mu", "na", "she"]
OPS = {"+": "dapa", "-": "dopo", "−": "dopo", "×": "kebu", "*": "kebu", "÷": "faku", "/": "faku", "=": "se", ".": "doto"}

def glifos(txt):
    """Cifras 0-9 → glifos numéricos de Owee Script (U+E040…E049); lo demás igual."""
    return re.sub(r"[0-9]", lambda m: chr(0xE040 + int(m.group(0))), str(txt))

def normales(txt):
    return re.sub(r"[-]", lambda m: str(ord(m.group(0)) - 0xE040), str(txt))

def _leer3(n):
    h, t, u = n // 100, (n // 10) % 10, n % 10; w = []
    if h: w.append(NOMBRES[h] + " gabu")
    if t: w.append(NOMBRES[t] + " tanu")
    if u: w.append(NOMBRES[u])
    return " ".join(w)

def leer_num(txt):
    """'247' o '25.50' → lectura Owee; None si no es un número o pasa de 999 999 999."""
    p = str(txt).split("."); 
    try: n = int(p[0])
    except ValueError: return None
    dec = p[1] if len(p) > 1 else ""; w = []
    if n >= 10**9: return None
    if n == 0: w.append("cho")
    else:
        m, k, r = n // 10**6, (n // 1000) % 1000, n % 1000
        if m: w.append(_leer3(m) + " benu")
        if k: w.append(_leer3(k) + " soku")
        if r: w.append(_leer3(r))
    if dec: w.append("doto " + " ".join(NOMBRES[int(d)] for d in dec if d.isdigit()))
    return " ".join(w)

def leer_valor(txt):
    """Resultado de la calculadora ('-12.5') → lectura con signo ('po …'); None si no se puede leer (notación científica…)."""
    s = str(txt).strip(); neg = s.startswith(("-", "−")); s = s.lstrip("-−")
    if not re.fullmatch(r"\d+(\.\d+)?", s): return None
    r = leer_num(s)
    return None if r is None else ("po " if neg else "") + r

def leer_expr(expr):
    """Expresión ('2+3') → lectura Owee ('du dapa ga'). Los paréntesis no se leen."""
    toks = re.findall(r"\d+\.?\d*|[-+*/−×÷=()]", str(expr).replace(" ", "")); out = []; prev = None
    for t in toks:
        if t[0].isdigit():
            r = leer_num(t); out.append(r if r is not None else t)
        elif t in "-−" and (prev is None or not re.match(r"\d|\)", prev)): out.append("po")
        elif t == "+" and (prev is None or not re.match(r"\d|\)", prev)): out.append("pa")
        elif t in "()": pass
        else: out.append(OPS.get(t, t))
        prev = t
    return " ".join(out)
