#!/usr/bin/env python3
"""Segunda serie de fondos de carpas (koi) de OweeLinux: 10 escenas con SIGNIFICADO (buena suerte, la sabia, adoración, la guerrera que sube la cascada, la inteligente…), con la misma carpa del
logo y de la primera serie (generar_koi.py), en grupos y de distintos tamaños, al estilo de dibujo animado. Todo dibujado aquí en SVG (sin fotos de nadie); semilla fija: reproducibles.
Uso: generar_koi2.py DESTINO [ANCHO] [filtro]   → escribe DESTINO/koi-<nn>-<nombre>.jpg (3840×2160 por defecto; numeración 11-20). Necesita rsvg-convert y ffmpeg."""
import math, os, random, subprocess, sys, tempfile
import generar_koi as G
from generar_koi import carpa, pal, ripple, lily, lotus, svg, fondo, CREMA

def W(): return G.W
def H(): return G.H

def bigas(c, L, x, y, rot, flip=False, op=1.0):
    """Los bigotes (barbillas) de una carpa vieja y sabia: dos finos hilos blancos junto a la boca. Se dibujan en las mismas coordenadas que carpa()."""
    s = -1 if flip else 1; hx = L * .5 * s; w = L * .012
    d = "".join(f'<path d="M{hx:.0f},{k * L * .012:.0f} q{s * L * .06:.0f},{k * L * .05:.0f} {s * L * .11:.0f},{k * L * .035 + 8 * k:.0f} q{s * L * .03:.0f},{k * L * .01:.0f} {s * L * .06:.0f},{-k * L * .02:.0f}" fill="none" stroke="{c}" stroke-width="{w:.1f}" stroke-linecap="round"/>' for k in (-1, 1))
    return f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})" opacity="{op}">{d}</g>'

def sombras(koi):
    out = ""
    for i, (px, py, L, rot, bend, flip, p) in enumerate(koi):
        out += f'<g filter="url(#b30)" opacity=".22" transform="translate(30,60)">{carpa(dict(body="#000", fin="#000", spot="#000", eye="#000"), L, bend, rot, px * W(), py * H(), flip, 1, f"s{i}")}</g>'
    return out

def pez(koi, base="k"): return "".join(carpa(p, L, bend, rot, px * W(), py * H(), flip, 1, f"{base}{i}") for i, (px, py, L, rot, bend, flip, p) in enumerate(koi))

def hacia(x, y, cx, cy): return math.degrees(math.atan2(cy - y, cx - x))        # ángulo para que la cabeza mire al punto (cx, cy)

def estrellas(r, n, color="#fff", ymax=1.0):
    return "".join(f'<circle cx="{r.uniform(0, W()):.0f}" cy="{r.uniform(0, H() * ymax):.0f}" r="{r.choice([1.5, 2, 3, 4]):.1f}" fill="{color}" opacity="{r.uniform(.3, .95):.2f}"/>' for _ in range(n))

def halo(cx, cy, r, color, op=.55, rayos=0):
    d = f'<radialGradient id="h{int(cx)}"><stop offset="0" stop-color="{color}" stop-opacity="{op}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient><circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="url(#h{int(cx)})"/>'
    for k in range(rayos):
        a = k * 2 * math.pi / rayos; d += f'<path d="M{cx:.0f},{cy:.0f} L{cx + r * 1.6 * math.cos(a - .045):.0f},{cy + r * 1.6 * math.sin(a - .045):.0f} L{cx + r * 1.6 * math.cos(a + .045):.0f},{cy + r * 1.6 * math.sin(a + .045):.0f} Z" fill="{color}" opacity=".10"/>'
    return d

def moneda(x, y, r, color="#ffd23f", edge="#b8860b"):
    return f'<g transform="translate({x:.0f},{y:.0f})"><circle r="{r:.0f}" fill="{color}" stroke="{edge}" stroke-width="{r * .08:.1f}"/><rect x="{-r * .28:.0f}" y="{-r * .28:.0f}" width="{r * .56:.0f}" height="{r * .56:.0f}" fill="#0000" stroke="{edge}" stroke-width="{r * .07:.1f}"/></g>'

def escena(seed, bg, koi, extra="", rip="#ffffff", n_rip=4, ripop=.14, delante=""):
    r = random.Random(seed); d, b = fondo(*bg)
    for _ in range(n_rip): b += ripple(int(r.uniform(.1, .9) * W()), int(r.uniform(.15, .9) * H()), r.uniform(70, 200), rip, ripop, 4)
    return svg(b + extra + sombras(koi) + pez(koi) + delante, d)

ORO = pal("#ffe9a8", "#ff9f1c", "#7a1f10", "#c8512f"); ROJA = pal("#ffd9c0", "#e63946", "#3a0d12", "#ffd166"); PLATA = pal("#f4f6f8", "#9fb4c7", "#3b4a5a", "#ffd166")
AZUL = pal("#d8efff", "#3b9cff", "#0a2a4a", "#2de2b4"); VERDE = pal("#eaf7d0", "#52b788", "#1b4332", "#ffd166"); ROSA = pal("#ffe3ef", "#ff6fa5", "#4a1d3a", "#ffb347")

def f11():                                                                                           # BUENA SUERTE: nueve carpas (el nueve es el número de la fortuna) girando alrededor de un anillo de oro
    cx, cy = .5, .5; koi = []; ex = halo(W() * cx, H() * cy, H() * .5, "#ffb703", .35) + f'<circle cx="{W() * cx:.0f}" cy="{H() * cy:.0f}" r="{H() * .30:.0f}" fill="none" stroke="#ffd23f" stroke-width="10" opacity=".55"/>'
    for k in range(9):
        a = k * 2 * math.pi / 9 - .6; x = cx + .22 * math.cos(a) * H() / W() * 1.0 + 0; px = cx + (H() * .30 * math.cos(a)) / W(); py = cy + .30 * math.sin(a)
        koi.append((px, py, 420 if k % 3 else 520, math.degrees(a) + 90, .16, False, [ORO, ROJA, CREMA][k % 3]))
    r = random.Random(11); ex += "".join(moneda(r.uniform(.05, .95) * W(), r.uniform(.08, .92) * H(), r.uniform(26, 60)) for _ in range(14))
    return escena(11, ("#2a0a0a", "#5c1212", "#3d0e0e"), koi, ex, "#ffd23f", 4, .18)

def f12():                                                                                           # LA SABIA: una carpa enorme y antigua, con bigotes y aureola; las demás la miran
    big = (.55, .46, 1750, -8, .12, False, PLATA); koi = [big]
    for k, (px, py, L) in enumerate(((.17, .74, 420), (.30, .86, 360), (.14, .30, 380), (.85, .80, 400), (.90, .22, 330))):
        koi.append((px, py, L, hacia(px, py, .5, .46) , .16, False, [CREMA, ORO, AZUL][k % 3]))
    ex = halo(.62 * W(), .43 * H(), H() * .62, "#cfe8ff", .45, 18); b = bigas("#ffffff", 1750, .55 * W(), .46 * H(), -8)
    return escena(12, ("#0b1d33", "#16365a", "#102a47"), koi, ex, "#9ec9ff", 5, .18, b)

def f13():                                                                                           # ADORACIÓN: todas las carpas en círculo, con la cabeza hacia una carpa dorada que brilla
    cx, cy = .5, .5; koi = [(cx, cy, 760, -90, .14, False, ORO)]
    for k in range(10):
        a = k * 2 * math.pi / 10 + .3; px = cx + (H() * .36 * math.cos(a)) / W(); py = cy + .36 * math.sin(a)
        koi.append((px, py, 330 + 40 * (k % 3), hacia(px * W(), py * H(), cx * W(), cy * H()), .17, False, [CREMA, ROJA, PLATA, ROSA, AZUL][k % 5]))
    return escena(13, ("#1b1030", "#3a1f5c", "#2a1748"), koi, halo(cx * W(), cy * H(), H() * .55, "#ffd23f", .6, 24) + f'<circle cx="{cx * W():.0f}" cy="{cy * H():.0f}" r="{H() * .36:.0f}" fill="none" stroke="#ffd23f" stroke-width="5" opacity=".35" stroke-dasharray="4 26"/>', "#ffd23f", 3, .12)

def f14():                                                                                           # GUERRERA: la carpa que sube la cascada hasta la Puerta del Dragón
    r = random.Random(14); ex = ""
    for k in range(9):
        x = W() * (.08 + .1 * k) + r.uniform(-30, 30); ex += f'<path d="M{x:.0f},{-20} L{x - 120:.0f},{H() + 20}" stroke="#d6ecff" stroke-width="{r.uniform(10, 40):.0f}" opacity="{r.uniform(.08, .2):.2f}" stroke-linecap="round"/>'
    ex += "".join(f'<circle cx="{r.uniform(.2, .9) * W():.0f}" cy="{r.uniform(.05, .95) * H():.0f}" r="{r.uniform(5, 16):.0f}" fill="#d6ecff" opacity="{r.uniform(.3, .8):.2f}"/>' for _ in range(90))
    ex += f'<path d="M{.74 * W():.0f},{.05 * H():.0f} h{.2 * W():.0f} v{.06 * H():.0f} h-{.025 * W():.0f} v{.14 * H():.0f} h-{.03 * W():.0f} v-{.14 * H():.0f} h-{.1 * W():.0f} v{.14 * H():.0f} h-{.03 * W():.0f} v-{.14 * H():.0f} h-{.0 * W():.0f} Z" fill="#7a1f10" opacity=".55"/>'
    koi = [(.50, .46, 1500, -62, .2, False, ROJA), (.30, .80, 420, -70, .18, False, ORO), (.20, .62, 330, -75, .17, False, CREMA), (.72, .84, 380, -64, .18, False, ROJA)]
    return escena(14, ("#12060a", "#4a0f1c", "#2b0a14"), koi, ex, "#ffb3b3", 3, .1)

def f15():                                                                                           # LA INTELIGENTE: carpas en espiral áurea unidas por una red de estrellas (una mente)
    r = random.Random(15); ex = estrellas(r, 220, "#9ee7ff"); pts = []; koi = []
    for k in range(8):
        a = k * 2.399; rad = 0.04 + 0.052 * math.sqrt(k + .5) * 2.4; px = .5 + rad * math.cos(a) * H() / W(); py = .5 + rad * math.sin(a) * .9; pts.append((px * W(), py * H()))
        koi.append((px, py, 560 - 45 * k, math.degrees(a) + 100, .16, False, [AZUL, PLATA, CREMA, VERDE][k % 4]))
    ex += "".join(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#2de2b4" stroke-width="3" opacity=".35"/>' for (x1, y1) in pts for (x2, y2) in pts if 0 < math.hypot(x1 - x2, y1 - y2) < W() * .24)
    ex += "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="14" fill="#2de2b4" opacity=".8"/>' for x, y in pts)
    return escena(15, ("#030b1a", "#08284a", "#051a33"), koi, ex, "#2de2b4", 3, .12)

def f16():                                                                                           # LUNA LLENA: una luna enorme y tres carpas nadando en su reflejo
    cx, cy = .5, .36; ex = halo(cx * W(), cy * H(), H() * .6, "#fff6d6", .5) + f'<circle cx="{cx * W():.0f}" cy="{cy * H():.0f}" r="{H() * .22:.0f}" fill="#fff8e1"/><circle cx="{cx * W() - 90:.0f}" cy="{cy * H() - 40:.0f}" r="48" fill="#f0e6c0" opacity=".6"/><circle cx="{cx * W() + 110:.0f}" cy="{cy * H() + 50:.0f}" r="34" fill="#f0e6c0" opacity=".5"/>'
    ex += estrellas(random.Random(16), 120, "#fff", .35)
    koi = [(.38, .72, 900, -6, .17, False, PLATA), (.64, .82, 680, 172, .17, True, CREMA), (.80, .62, 420, 200, .16, True, AZUL)]
    return escena(16, ("#050b17", "#0d2644", "#071a33"), koi, ex, "#dce8ff", 6, .2)

def f17():                                                                                           # FAMILIA: la madre grande y cinco crías siguiéndola en fila
    koi = [(.70, .46, 1250, 172, .18, True, ORO)]; r = random.Random(17)
    for k in range(5): koi.append((.52 - .105 * k, .54 + .05 * math.sin(k * 1.1), 300 - 24 * k, 176 - 6 * math.sin(k), .2, True, [CREMA, ROJA, CREMA, ROSA, CREMA][k]))
    return escena(17, ("#0f3d3e", "#1f7a70", "#176158"), koi, "".join(lily(int(r.uniform(.03, .97) * W()), int(r.uniform(.05, .95) * H()), r.uniform(70, 170), "#3fa88c", r.uniform(0, 360)) for _ in range(7)), "#a8f0dc", 5, .2)

def f18():                                                                                           # TORBELLINO DE ORO: veinte carpas de todos los tamaños girando en un remolino
    koi = []; r = random.Random(18)
    for k in range(20):
        a = k * .62; rad = .05 + .021 * k; px = .5 + rad * math.cos(a) * H() / W() * 1.15; py = .5 + rad * math.sin(a)
        koi.append((px, py, 150 + 24 * k, math.degrees(a) + 100, .17, False, [ORO, CREMA, ROJA][k % 3]))
    return escena(18, ("#2b1500", "#6b3a00", "#4a2800"), list(reversed(koi)), halo(.5 * W(), .5 * H(), H() * .5, "#ffcf5a", .35), "#ffd98a", 4, .18)

def f19():                                                                                           # JARDÍN ZEN: claro, con piedras y anillos de agua; tres carpas tranquilas
    r = random.Random(19); ex = ""
    for (x, y, rr) in ((.22, .30, 150), (.78, .68, 190), (.60, .22, 110)):
        ex += ripple(int(x * W()), int(y * H()), rr * 1.3, "#6d8f86", .35, 5) + f'<ellipse cx="{x * W():.0f}" cy="{y * H():.0f}" rx="{rr}" ry="{rr * .7:.0f}" fill="#7d8c88"/><ellipse cx="{x * W() - rr * .15:.0f}" cy="{y * H() - rr * .2:.0f}" rx="{rr * .6:.0f}" ry="{rr * .35:.0f}" fill="#a3b1ad"/>'
    koi = [(.40, .56, 760, -18, .17, False, CREMA), (.62, .40, 520, 160, .17, True, pal("#fff7e0", "#f2573f", "#2e3a30")), (.30, .80, 400, 25, .16, False, ORO)]
    return escena(19, ("#dfeee8", "#b8d4ca", "#cde3da"), koi, ex, "#5a8f80", 5, .25)

def f20():                                                                                           # ESPIRAL DEL SABER: siete carpas de grande a pequeña en espiral alrededor de un loto
    cx, cy = .5, .5; koi = []; ex = lotus(int(cx * W()), int(cy * H()), 150, "#ffb3d1", "#ff7eb6")
    for k in range(7):
        a = -1.2 + k * .95; rad = .30 - .035 * k; px = cx + rad * math.cos(a) * H() / W() * 1.25; py = cy + rad * math.sin(a) * 1.15
        koi.append((px, py, 820 - 100 * k, math.degrees(a) + 105, .18, False, [CREMA, ORO, ROSA, PLATA, ROJA, AZUL, VERDE][k]))
    return escena(20, ("#2a1636", "#5a2a6b", "#411f50"), koi, ex, "#ffd1f0", 4, .16)

FONDOS = [("buena-suerte", f11), ("la-sabia", f12), ("adoracion", f13), ("guerrera-de-la-cascada", f14), ("la-inteligente", f15), ("luna-llena", f16), ("familia", f17), ("torbellino-de-oro", f18), ("jardin-zen", f19), ("espiral-del-saber", f20)]

def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2].isdigit(): G.W = int(sys.argv[2]); G.H = G.W * 9 // 16
    solo = sys.argv[3:]
    for i, (nombre, fn) in enumerate(FONDOS, 11):
        if solo and not any(s in nombre for s in solo): continue
        with tempfile.TemporaryDirectory() as t:
            open(f"{t}/a.svg", "w").write(fn()); subprocess.run(["rsvg-convert", "-w", str(G.W), f"{t}/a.svg", "-o", f"{t}/a.png"], check=True)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{t}/a.png", "-q:v", "3", f"{out}/koi-{i:02d}-{nombre}.jpg"], check=True)
        print("ok", nombre, os.path.getsize(f"{out}/koi-{i:02d}-{nombre}.jpg") // 1024, "KB", flush=True)

if __name__ == "__main__": main()
