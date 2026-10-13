"""Motor de la Calculadora de OweeLinux: analiza y evalúa expresiones SIN usar eval() (no se puede ejecutar código), con aritmética decimal exacta (0,1 + 0,2 = 0,3).
Admite + − × ÷ ^ % ! ( ), funciones (sin cos tan asin acos atan ln log √), constantes π y e, multiplicación implícita (2π, 3(4+1)) y el porcentaje «como en el móvil»:
«200 + 10 %» = 220 (el porcentaje se aplica al número de la izquierda en sumas y restas) y «50 %» = 0,5. Los ángulos van en grados o radianes (parámetro `degrees`)."""
import math
from decimal import Decimal, getcontext, InvalidOperation, DivisionByZero

getcontext().prec = 40
FUNCS = {"sin", "cos", "tan", "asin", "acos", "atan", "ln", "log", "√"}
SYMS = {"*": "×", "/": "÷", "x": "×", "X": "×", "−": "-", "–": "-", ",": ".", "sqrt": "√", "pi": "π"}

class CalcError(Exception):
    """Mensaje pensado para mostrarse al usuario tal cual."""

def tokenize(s):
    toks = []; i = 0; s = s.replace(" ", "")
    while i < len(s):
        c = s[i]
        if c.isdigit() or c in ".,":
            j = i
            while j < len(s) and (s[j].isdigit() or s[j] in ".,"): j += 1
            num = s[i:j].replace(",", ".")
            if num.count(".") > 1 or num == ".": raise CalcError("Expresión no válida")
            toks.append(("num", Decimal(num))); i = j; continue
        for name in ("asin", "acos", "atan", "sin", "cos", "tan", "log", "ln", "sqrt"):
            if s.startswith(name, i): toks.append(("fn", "√" if name == "sqrt" else name)); i += len(name); break
        else:
            if s.startswith("pi", i): toks.append(("const", "π")); i += 2
            elif c == "π": toks.append(("const", "π")); i += 1
            elif c == "e" and not (i + 1 < len(s) and s[i + 1].isdigit() and False): toks.append(("const", "e")); i += 1
            elif c == "√": toks.append(("fn", "√")); i += 1
            elif c in "+-−–": toks.append(("op", "+" if c == "+" else "-")); i += 1
            elif c in "*×xX": toks.append(("op", "*")); i += 1
            elif c in "/÷": toks.append(("op", "/")); i += 1
            elif c == "^": toks.append(("op", "^")); i += 1
            elif c in "()!%": toks.append((c, c)); i += 1
            else: raise CalcError("Expresión no válida")
    return toks

class Parser:
    def __init__(self, toks, degrees): self.t = toks; self.i = 0; self.deg = degrees
    def peek(self): return self.t[self.i] if self.i < len(self.t) else (None, None)
    def eat(self): tok = self.t[self.i]; self.i += 1; return tok
    def starts_primary(self): k, v = self.peek(); return k in ("num", "fn", "const", "(")

    def expr(self):
        left, _ = self.term()
        while self.peek()[0] == "op" and self.peek()[1] in "+-":
            op = self.eat()[1]; right, pct = self.term()
            if pct: right = left * right                     # 200 + 10 % → 10 % de 200
            left = left + right if op == "+" else left - right
        return left

    def term(self):
        left, pct = self.power()
        while True:
            k, v = self.peek()
            if k == "op" and v in "*/":
                self.eat(); right, _ = self.power()
                if v == "/":
                    if right == 0: raise CalcError("No se puede dividir entre 0")
                    left = left / right
                else: left = left * right
                pct = False
            elif self.starts_primary(): right, _ = self.power(); left = left * right; pct = False        # 2π, 3(4+1)
            else: return left, pct

    def power(self):
        base, pct = self.unary()
        if self.peek() == ("op", "^"):
            self.eat(); exp, _ = self.power_rhs()
            try:
                if exp == exp.to_integral_value() and abs(exp) <= 10000: base = base ** int(exp)
                else: base = Decimal(repr(math.pow(float(base), float(exp))))
            except (InvalidOperation, ValueError, OverflowError, DivisionByZero): raise CalcError("Resultado no válido")
            pct = False
        return base, pct

    def power_rhs(self): return self.power() if self.peek()[0] != "op" or self.peek()[1] not in "+-" else self.unary()

    def unary(self):
        k, v = self.peek()
        if k == "op" and v in "+-":
            self.eat(); val, pct = self.unary(); return (-val if v == "-" else val), pct
        return self.postfix()

    def postfix(self):
        val = self.primary(); pct = False
        while self.peek()[0] in ("!", "%"):
            k = self.eat()[0]
            if k == "!":
                if val != val.to_integral_value() or val < 0 or val > 170: raise CalcError("Factorial no válido")
                val = Decimal(math.factorial(int(val)))
            else: val = val / 100; pct = True
        return val, pct

    def primary(self):
        k, v = self.peek()
        if k is None: raise CalcError("Expresión incompleta")
        self.eat()
        if k == "num": return v
        if k == "const": return Decimal(repr(math.pi)) if v == "π" else Decimal(repr(math.e))
        if k == "(":
            val = self.expr()
            if self.peek()[0] != ")": raise CalcError("Falta cerrar un paréntesis")
            self.eat(); return val
        if k == "fn": return self.call(v, self.argument())
        raise CalcError("Expresión no válida")

    def argument(self):
        if self.peek()[0] == "(":
            self.eat(); val = self.expr()
            if self.peek()[0] == ")": self.eat()
            return val
        val, _ = self.power() if self.peek()[0] != "op" else self.unary(); return val

    def call(self, fn, x):
        f = float(x)
        try:
            if fn == "√":
                if x < 0: raise CalcError("Raíz de un número negativo")
                return x.sqrt()
            if fn == "ln":
                if x <= 0: raise CalcError("Logaritmo de un número no positivo")
                return x.ln()
            if fn == "log":
                if x <= 0: raise CalcError("Logaritmo de un número no positivo")
                return x.log10()
            if fn in ("sin", "cos", "tan"):
                r = math.radians(f) if self.deg else f
                if fn == "tan" and self.deg and abs((f % 180) - 90) < 1e-12: raise CalcError("Tangente no definida")
                v = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[fn](r)
                if abs(v) < 1e-15: v = 0.0                          # sin(180°) = 0, no 1,2e-16
                return Decimal(repr(v))
            if fn in ("asin", "acos", "atan"):
                if fn != "atan" and abs(f) > 1: raise CalcError("Valor fuera de rango")
                v = {"asin": math.asin, "acos": math.acos, "atan": math.atan}[fn](f)
                return Decimal(repr(math.degrees(v) if self.deg else v))
        except (ValueError, OverflowError): raise CalcError("Resultado no válido")

def evaluate(expr, degrees=True):
    """Devuelve un Decimal. Lanza CalcError con un mensaje legible."""
    toks = tokenize(expr)
    if not toks: raise CalcError("")
    # cierra los paréntesis abiertos (como hacen las calculadoras de móvil al pulsar =)
    depth = sum(1 for k, _ in toks if k == "(") - sum(1 for k, _ in toks if k == ")")
    toks += [(")", ")")] * max(0, depth)
    while toks and toks[-1][0] == "op": toks.pop()                   # «5 +» → 5
    p = Parser(toks, degrees); val = p.expr()
    if p.i != len(toks): raise CalcError("Expresión no válida")
    return val

def fmt(d, sig=12):
    """Formatea un Decimal para mostrarlo: hasta `sig` cifras significativas, sin ceros sobrantes, notación científica si es enorme o diminuto."""
    if d == 0: return "0"
    try:
        r = d.normalize(); exp = r.adjusted()
        if exp >= 15 or exp <= -10: return ("%." + str(sig - 1) + "e") % float(d)
        q = round(d, max(0, sig - 1 - exp)) if exp < sig else d
        s = format(q.normalize(), "f")
        if "." in s: s = s.rstrip("0").rstrip(".")
        return "-0" if s == "-0" else s
    except (InvalidOperation, ValueError): return "Error"

def calc(expr, degrees=True):
    """Atajo: devuelve (texto_resultado, error|None)."""
    try: return fmt(evaluate(expr, degrees)), None
    except CalcError as e: return "", str(e)
    except (InvalidOperation, ValueError, OverflowError, RecursionError): return "", "Expresión no válida"
