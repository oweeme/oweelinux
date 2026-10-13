#!/usr/bin/env python3
"""Pruebas del motor de la calculadora (sin GTK): python3 test_engine.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calc_engine import calc
CASOS = [
    ("1+2", "3"), ("12+7*3", "33"), ("12+7×3", "33"), ("10/4", "2.5"), ("0.1+0.2", "0.3"), ("0,1+0,2", "0.3"), ("2^10", "1024"), ("2^-1", "0.5"), ("2^3^2", "512"),
    ("-5+3", "-2"), ("-(2+3)", "-5"), ("(1+2)*(3+4)", "21"), ("2(3+4)", "14"), ("2π", "6.28318530718"), ("5!", "120"), ("0!", "1"),
    ("50%", "0.5"), ("200+10%", "220"), ("200-10%", "180"), ("200*10%", "20"), ("9%", "0.09"), ("√16", "4"), ("√(2)", "1.41421356237"), ("√9+1", "4"),
    ("sin(90)", "1"), ("cos(60)", "0.5"), ("sin(180)", "0"), ("tan(45)", "1"), ("ln(e)", "1"), ("log(1000)", "3"), ("asin(1)", "90"), ("(2+3", "5"), ("5+", "5"),
    ("1/3", "0.333333333333"), ("1000000*1000000", "1000000000000"), ("123456789*987654321", "1.21932631113e+17"), ("0.000001", "0.000001"), ("7-10", "-3"), ("3×-2", "-6"),
]
ERRORES = [("1/0", "dividir"), ("5/(3-3)", "dividir"), ("√(-4)", "negativ"), ("ln(0)", "Logaritmo"), ("2++", None), ("abc", "no válida"), ("1..2", "no válida"), ("(-1)!", "Factorial"), ("tan(90)", "Tangente"), ("", "")]
fallos = 0
for e, esperado in CASOS:
    r, err = calc(e)
    ok = err is None and r == esperado
    if not ok: fallos += 1
    print(("ok    " if ok else "FALLA ") + f"{e!r:28} → {r or err!r}" + ("" if ok else f"   (esperado {esperado!r})"))
for e, frag in ERRORES:
    r, err = calc(e)
    ok = (err is not None and (frag is None or frag in err)) or (frag is None and err is None)
    if not ok: fallos += 1
    print(("ok    " if ok else "FALLA ") + f"{e!r:28} → error: {err!r}")
r, err = calc("sin(pi/2)", degrees=False); ok = r == "1"; fallos += not ok; print(("ok    " if ok else "FALLA ") + f"radianes sin(π/2) → {r}")
r, err = calc("__import__('os')"); ok = err is not None; fallos += not ok; print(("ok    " if ok else "FALLA ") + "no ejecuta código (eval no se usa)")
print("TODO BIEN" if not fallos else f"{fallos} FALLOS"); sys.exit(1 if fallos else 0)
