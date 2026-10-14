#!/usr/bin/env python3
"""Fondos de carpas (koi) de OweeLinux: 10 dibujos propios hechos con la carpa del logo (cuerpo crema, aletas y manchas rojas, lunares oscuros), cada uno con otros
colores, cantidad y tamaño de carpas. Todo se dibuja aquí en SVG (sin fotos de nadie); salen de una semilla fija, así que son reproducibles.
Uso: generar_koi.py DESTINO [ANCHO] [filtro]   → escribe DESTINO/koi-<nombre>.jpg (3840×2160 por defecto). Necesita rsvg-convert y ffmpeg."""
import math, os, random, subprocess, sys, tempfile
W, H = 3840, 2160

def spine(n, length, bend):
    """Puntos del eje de la carpa: de la cola (0) a la cabeza (1), curvado como en el logo."""
    pts = []
    for i in range(n + 1):
        t = i / n; pts.append((t * length - length / 2, -bend * length * math.sin(t * math.pi) * (1 - t * .4) + bend * length * .35 * (t - .5)))
    return pts

def carpa(c, length=400, bend=.16, rot=0, x=0, y=0, flip=False, op=1.0, uid="k"):
    """Una carpa. c = colores {body, fin, spot, eye}; length = largo en px; bend = cuánto se curva; rot en grados."""
    n = 24; sp = spine(n, length, bend)
    def width(t):                                                       # cola fina → vientre ancho → cabeza redonda
        if t >= .55: return length * .118 * max(0, 1 - ((t - .55) / .46) ** 2) ** .55
        return length * (.014 + .104 * math.sin((t / .55) * math.pi / 2) ** 1.3)
    up, dn = [], []
    for i, (px, py) in enumerate(sp):
        t = i / n; a = math.atan2(sp[min(i + 1, n)][1] - sp[max(i - 1, 0)][1], sp[min(i + 1, n)][0] - sp[max(i - 1, 0)][0]); w = width(t)
        up.append((px - w * math.sin(a), py + w * math.cos(a))); dn.append((px + w * math.sin(a), py - w * math.cos(a)))
    body = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in up) + " L" + " L".join(f"{px:.1f},{py:.1f}" for px, py in reversed(dn)) + " Z"
    tx, ty = sp[0]; L = length
    tail = f"M{tx + L * .02:.1f},{ty:.1f} C{tx - L * .12:.1f},{ty - L * .10:.1f} {tx - L * .22:.1f},{ty - L * .26:.1f} {tx - L * .30:.1f},{ty - L * .30:.1f} C{tx - L * .25:.1f},{ty - L * .10:.1f} {tx - L * .2:.1f},{ty - L * .02:.1f} {tx - L * .17:.1f},{ty + L * .01:.1f} C{tx - L * .21:.1f},{ty + L * .06:.1f} {tx - L * .27:.1f},{ty + L * .20:.1f} {tx - L * .24:.1f},{ty + L * .24:.1f} C{tx - L * .14:.1f},{ty + L * .14:.1f} {tx - L * .06:.1f},{ty + L * .06:.1f} {tx + L * .02:.1f},{ty + L * .02:.1f} Z"
    fx, fy = sp[int(n * .62)]; bx, by = sp[int(n * .34)]
    fins = (f'<path d="M{fx:.1f},{fy - width(.62):.1f} q{L * .08:.1f},{-L * .20:.1f} {L * .17:.1f},{-L * .06:.1f} q{-L * .08:.1f},{L * .02:.1f} {-L * .17:.1f},{L * .06:.1f} Z" fill="{c["fin"]}"/>'
            f'<path d="M{bx:.1f},{by + width(.34):.1f} q{L * .02:.1f},{L * .16:.1f} {L * .14:.1f},{L * .14:.1f} q{-L * .04:.1f},{-L * .08:.1f} {-L * .10:.1f},{-L * .15:.1f} Z" fill="{c["fin"]}" opacity=".9"/>')
    hx, hy = sp[int(n * .86)]
    patches = (f'<ellipse cx="{sp[int(n * .78)][0]:.1f}" cy="{sp[int(n * .78)][1] - L * .02:.1f}" rx="{L * .09:.1f}" ry="{L * .055:.1f}" fill="{c["fin"]}"/>'
               f'<ellipse cx="{sp[int(n * .50)][0]:.1f}" cy="{sp[int(n * .50)][1] + L * .015:.1f}" rx="{L * .07:.1f}" ry="{L * .04:.1f}" fill="{c["spot"]}"/>'
               f'<ellipse cx="{sp[int(n * .36)][0]:.1f}" cy="{sp[int(n * .36)][1] - L * .01:.1f}" rx="{L * .045:.1f}" ry="{L * .03:.1f}" fill="{c["spot"]}"/>'
               f'<ellipse cx="{sp[int(n * .64)][0]:.1f}" cy="{sp[int(n * .64)][1] - L * .03:.1f}" rx="{L * .05:.1f}" ry="{L * .028:.1f}" fill="{c["spot"]}"/>')
    eye = f'<circle cx="{sp[int(n * .93)][0]:.1f}" cy="{sp[int(n * .93)][1] + L * .006:.1f}" r="{L * .016:.1f}" fill="{c["eye"]}"/>'
    sx = -1 if flip else 1
    return (f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f}) scale({sx},1)" opacity="{op}"><clipPath id="{uid}"><path d="{body}"/></clipPath>'
            f'<path d="{tail}" fill="{c["fin"]}" opacity=".92"/>{fins}<path d="{body}" fill="{c["body"]}"/><g clip-path="url(#{uid})">{patches}</g>{eye}</g>')

def ripple(x, y, r, color, op=.18, w=4): return "".join(f'<ellipse cx="{x}" cy="{y}" rx="{r * k}" ry="{r * k * .42}" fill="none" stroke="{color}" stroke-width="{w}" opacity="{op / k:.2f}"/>' for k in (1, 1.5, 2.1))
def lily(x, y, r, color, rot=0):
    a = math.radians(14); return f'<g transform="translate({x},{y}) rotate({rot})"><path d="M0,0 L{r * math.cos(a):.0f},{-r * math.sin(a):.0f} A{r},{r} 0 1 0 {r * math.cos(a):.0f},{r * math.sin(a):.0f} Z" fill="{color}"/></g>'
def lotus(x, y, r, c1, c2): return f'<g transform="translate({x},{y})">' + "".join(f'<ellipse cx="0" cy="{-r * .5}" rx="{r * .22}" ry="{r * .5}" fill="{c1 if k % 2 else c2}" transform="rotate({k * 40 - 120})" opacity=".92"/>' for k in range(7)) + f'<circle r="{r * .12}" fill="#ffe9a8"/></g>'
def svg(body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{defs}'
            '<filter id="b30"><feGaussianBlur stdDeviation="30"/></filter><filter id="b6"><feGaussianBlur stdDeviation="6"/></filter>'
            '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="5"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .05 0"/></filter>'
            '<filter id="water" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.0022 0.005" numOctaves="4" seed="11"/>'
            '<feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1.2 -.5"/></filter></defs>'
            f'{body}<rect width="{W}" height="{H}" filter="url(#grain)"/></svg>')
def fondo(c0, c1, c2=None, angle=(0, 0, 1, 1)):
    g = f'<linearGradient id="bg" x1="{angle[0]}" y1="{angle[1]}" x2="{angle[2]}" y2="{angle[3]}"><stop offset="0" stop-color="{c0}"/>' + (f'<stop offset=".55" stop-color="{c2}"/>' if c2 else "") + f'<stop offset="1" stop-color="{c1}"/></linearGradient>'
    return g, f'<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="#fff" filter="url(#water)" opacity=".06"/>'

CREMA = dict(body="#fbeab4", fin="#f2573f", spot="#2e3a30", eye="#e8892a")
def pal(body, fin, spot, eye="#e8892a"): return dict(body=body, fin=fin, spot=spot, eye=eye)

def escena(seed, bg, koi, extra="", rip="#ffffff", n_rip=5, ripop=.16):
    """koi = lista de (x%, y%, largo, rot, curvatura, flip, paleta)."""
    r = random.Random(seed); d, b = fondo(*bg)
    for _ in range(n_rip): b += ripple(int(r.uniform(.1, .9) * W), int(r.uniform(.15, .9) * H), r.uniform(70, 200), rip, ripop, 4)
    b += extra
    for i, (px, py, L, rot, bend, flip, p) in enumerate(koi):
        b += f'<g filter="url(#b30)" opacity=".22" transform="translate(30,60)">{carpa(dict(body="#000", fin="#000", spot="#000", eye="#000"), L, bend, rot, px * W, py * H, flip, 1, f"s{i}")}</g>'
    for i, (px, py, L, rot, bend, flip, p) in enumerate(koi): b += carpa(p, L, bend, rot, px * W, py * H, flip, 1, f"k{i}")
    return svg(b, d)

def pads(seed, n, color, ymin=0, ymax=1):
    r = random.Random(seed); return "".join(lily(int(r.uniform(.03, .97) * W), int(r.uniform(ymin, ymax) * H), r.uniform(70, 190), color, r.uniform(0, 360)) for _ in range(n))

def f01(): return escena(1, ("#0e3b34", "#175a4d", "#12483f"), [(.52, .5, 1500, -12, .17, False, CREMA)], pads(1, 5, "#2f7a5f", .7, 1), "#9fe3cf", 6)
def f02(): return escena(2, ("#0c2a3a", "#12526a", "#0f3d52"), [(.30, .62, 700, 8, .16, False, CREMA), (.62, .36, 600, -20, .18, True, pal("#ffe1c6", "#ff7a45", "#7a2a1a")), (.72, .72, 520, 150, .15, False, pal("#fff3cf", "#f2573f", "#243236"))], pads(2, 6, "#2a6f6a", 0, 1), "#bfeaff")
def f03(): return escena(3, ("#1a0f2e", "#3b1d5a", "#2b1647"), [(.5, .5, 1000, 30, .2, False, pal("#fde6f0", "#ff5e8a", "#3a1f4a", "#ffb347")), (.25, .25, 420, -40, .16, True, pal("#e9dcff", "#ff8fc0", "#3a1f4a")), (.78, .78, 380, 190, .16, False, pal("#fff1c9", "#ffb347", "#3a1f4a"))], lotus(int(.15 * W), int(.8 * H), 210, "#ff9ec7", "#ffc2dd") + lotus(int(.88 * W), int(.2 * H), 170, "#ffc2dd", "#ff9ec7"), "#f0c8ff")
def f04(): return escena(4, ("#23211c", "#3d3a2f", "#2e2c24"), [(.18 + .09 * k, .30 + .11 * (k % 4), 240 + 30 * (k % 3), -25 + 12 * k, .16, k % 2 == 0, pal("#f7ecc4", ["#f2573f", "#e8892a", "#d9442f", "#ffb347"][k % 4], "#2e3a30")) for k in range(8)], "", "#f5e9c8", 7)
def f05(): return escena(5, ("#04121f", "#082c47", "#06203a"), [(.50, .50, 1250, 5, .13, False, pal("#e6f8ff", "#2de2b4", "#0a3a5a", "#2de2b4")), (.14, .22, 300, 40, .16, False, pal("#d1f3ff", "#3b9cff", "#0a3a5a")), (.86, .82, 340, 200, .16, True, pal("#d1f3ff", "#2de2b4", "#0a3a5a"))], "".join(f'<circle cx="{random.Random(k).randint(0, W)}" cy="{random.Random(k + 90).randint(0, H)}" r="{random.Random(k + 5).choice([2, 3, 5])}" fill="#8ff5e0" opacity=".5"/>' for k in range(70)), "#2de2b4", 4, .3)
def f06(): return escena(6, ("#5a1d12", "#c8512f", "#92321d"), [(.42, .46, 900, -8, .18, False, pal("#fff0c2", "#ffd23f", "#5a1d12", "#c8512f")), (.68, .62, 760, 160, .17, True, pal("#ffe6c4", "#ff8a3d", "#5a1d12")), (.22, .76, 480, 25, .15, False, pal("#fff6d8", "#ffd23f", "#5a1d12"))], pads(6, 6, "#7a2c18", 0, 1), "#ffd9a0")
def f07(): return escena(7, ("#e8f1ec", "#bfd9cf", "#d3e6dd"), [(.5, .5, 1100, -15, .17, False, pal("#fffdf4", "#f2573f", "#2e3a30"))], pads(7, 5, "#8fbfae", 0, 1) , "#5a8f80", 5, .22)
def f08(): return escena(8, ("#0b2b24", "#1e6a52", "#13493b"), [(.15 + .07 * k, .15 + .075 * ((k * 5) % 11), 130 + 25 * (k % 4), (k * 53) % 360, .15, k % 3 == 0, pal("#f9ecb8", ["#f2573f", "#e8892a", "#ffb347"][k % 3], "#2e3a30")) for k in range(12)], pads(8, 4, "#2f7a5f", .8, 1), "#9fe3cf", 8)
def f09(): return escena(9, ("#14213d", "#2c3e75", "#1c2d58"), [(.38, .44, 800, -30, .2, False, pal("#fdf0d5", "#ff6b6b", "#1c2d58", "#ffd166")), (.66, .58, 800, 150, .2, True, pal("#fdf0d5", "#ffd166", "#1c2d58", "#ff6b6b"))], lotus(int(.5 * W), int(.5 * H), 150, "#ffd6e0", "#fff0f5"), "#cfd9ff")
def f10(): return escena(10, ("#1a1d21", "#2b3036", "#22262b"), [(.5, .5, 1700, -6, .15, False, pal("#f4f1e8", "#d94a38", "#1a1d21", "#d94a38"))], "", "#cfd4da", 3, .1)

FONDOS = [("pecera-esmeralda", f01), ("trio-azul", f02), ("loto-nocturno", f03), ("banco-de-ocho", f04), ("abismo-turquesa", f05), ("atardecer-de-fuego", f06), ("niebla-de-jade", f07), ("cardumen-de-doce", f08), ("yin-yang-indigo", f09), ("grafito", f10)]

def main():
    global W, H
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2].isdigit(): W = int(sys.argv[2]); H = W * 9 // 16
    solo = sys.argv[3:]
    for i, (nombre, fn) in enumerate(FONDOS, 1):
        if solo and not any(s in nombre for s in solo): continue
        with tempfile.TemporaryDirectory() as t:
            open(f"{t}/a.svg", "w").write(fn()); subprocess.run(["rsvg-convert", "-w", str(W), f"{t}/a.svg", "-o", f"{t}/a.png"], check=True)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{t}/a.png", "-q:v", "3", f"{out}/koi-{i:02d}-{nombre}.jpg"], check=True)
        print("ok", nombre, os.path.getsize(f"{out}/koi-{i:02d}-{nombre}.jpg") // 1024, "KB", flush=True)

if __name__ == "__main__": main()
