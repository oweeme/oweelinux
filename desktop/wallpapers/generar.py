#!/usr/bin/env python3
"""Generador de los fondos de pantalla de OweeLinux: 15 paisajes utópicos de tecnología, ilusiones y sueños, DIBUJADOS aquí en SVG con formas, degradados y filtros
(sin fotos de nadie: son propios y se distribuyen con la misma licencia que el proyecto). Cada fondo sale de una semilla fija, así que son reproducibles.
Uso: generar.py DESTINO [ANCHO]   → escribe DESTINO/<nombre>.jpg (3840×2160 por defecto). Necesita rsvg-convert y ffmpeg."""
import math, os, random, subprocess, sys, tempfile
W, H = 3840, 2160
def rnd(seed): return random.Random(seed)
def defs_common():
    return f'''<filter id="blur40"><feGaussianBlur stdDeviation="40"/></filter><filter id="blur12"><feGaussianBlur stdDeviation="12"/></filter><filter id="blur4"><feGaussianBlur stdDeviation="4"/></filter>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .05 0"/></filter>
<filter id="clouds" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.0016 0.004" numOctaves="5" seed="7"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1.4 -.55"/><feGaussianBlur stdDeviation="14"/></filter>'''
def vgrad(i, stops): return f'<linearGradient id="{i}" x1="0" y1="0" x2="0" y2="1">' + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops) + '</linearGradient>'
def rgrad(i, c, o0=0.9, o1=0): return f'<radialGradient id="{i}"><stop offset="0" stop-color="{c}" stop-opacity="{o0}"/><stop offset="1" stop-color="{c}" stop-opacity="{o1}"/></radialGradient>'
def stars(r, n, ymax=H * 0.6, c="#fff"):
    return "".join(f'<circle cx="{r.uniform(0, W):.0f}" cy="{r.uniform(0, ymax):.0f}" r="{r.choice([1.2, 1.6, 2.2, 3]):.1f}" fill="{c}" opacity="{r.uniform(.25, .95):.2f}"/>' for _ in range(n))
def ridge(r, y, amp, color, op=1, seg=16, rough=.5, base=H):
    pts, yy = [], y
    for i in range(seg + 1):
        yy = y + r.uniform(-amp, amp) * (1 if i % 2 else rough); pts.append((W * i / seg, yy))
    d = f"M0,{base} L" + " L".join(f"{x:.0f},{yy:.0f}" for x, yy in pts) + f" L{W},{base} Z"
    return f'<path d="{d}" fill="{color}" opacity="{op}"/>'
def smooth(r, y, amp, color, op=1, n=9, base=H, fid=None):
    xs = [W * i / n for i in range(n + 1)]; ys = [y + r.uniform(-amp, amp) for _ in xs]
    d = f"M0,{base} L0,{ys[0]:.0f}"
    for i in range(1, len(xs)): d += f" C{(xs[i - 1] + xs[i]) / 2:.0f},{ys[i - 1]:.0f} {(xs[i - 1] + xs[i]) / 2:.0f},{ys[i]:.0f} {xs[i]:.0f},{ys[i]:.0f}"
    d += f" L{W},{base} Z"; return f'<path d="{d}" fill="{color}" opacity="{op}"' + (f' filter="url(#{fid})"' if fid else '') + '/>'
def hexpoly(cx, cy, rad, rot=0): return " ".join(f"{cx + rad * math.cos(rot + k * math.pi / 3):.0f},{cy + rad * math.sin(rot + k * math.pi / 3):.0f}" for k in range(6))
def grain(): return f'<rect width="{W}" height="{H}" filter="url(#grain)"/>'
def svg(body, defs=""): return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{defs_common()}{defs}</defs>{body}{grain()}</svg>'

def aurora_digital():
    r = rnd(1); d = vgrad("sky", [(0, "#050a1c"), (.55, "#0b1f3a"), (1, "#14334a")]); b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>' + stars(r, 420)
    for i, (c, y) in enumerate((("#2de2b4", 760), ("#3b9cff", 900), ("#b06bff", 1040), ("#2de2b4", 1180))):
        pts = [(x, y + math.sin(x / 520 + i * 1.7) * 150 + math.sin(x / 190 + i) * 40) for x in range(-100, W + 200, 100)]
        top = " L".join(f"{x},{yy:.0f}" for x, yy in pts); bot = " L".join(f"{x},{yy + 360 + 100 * math.sin(x / 700 + i):.0f}" for x, yy in reversed(pts))
        d += f'<linearGradient id="a{i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c}" stop-opacity=".0"/><stop offset=".25" stop-color="{c}" stop-opacity=".55"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></linearGradient>'
        b += f'<path d="M{top} L{bot} Z" fill="url(#a{i})" filter="url(#blur40)"/>'
    b += ridge(r, 1700, 150, "#06121f", 1, 14, .6) + ridge(r, 1850, 120, "#030a14", 1, 18, .5)
    b += '<g stroke="#2de2b4" stroke-width="3" opacity=".7">' + "".join(f'<line x1="{x}" y1="1760" x2="{x}" y2="{1760 - r.uniform(40, 140):.0f}"/>' for x in range(200, W, 330)) + '</g>'
    return svg(b, d)

def ciudad_neon():
    r = rnd(2); d = vgrad("sky", [(0, "#0a0220"), (.5, "#3a0b5c"), (.78, "#d1337f"), (1, "#ff9a5a")]) + rgrad("sun", "#ffd27a", 1, 0)
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/><circle cx="{W / 2}" cy="1250" r="620" fill="url(#sun)"/><circle cx="{W / 2}" cy="1250" r="380" fill="#ffd9a0"/>' + stars(r, 260, 900)
    for k in range(5):
        pts = ""
        x = 0
        while x < W:
            w = r.randint(120, 300); h = r.randint(220, 640) * (1 + k * .25) * .55; col = ["#1a0833", "#220a3d", "#2c0f4b", "#14052a", "#0d0320"][k]
            pts += f'<rect x="{x}" y="{1600 - h + k * 70:.0f}" width="{w}" height="{h + 700:.0f}" fill="{col}"/>'
            for _ in range(int(h / 55)):
                if r.random() < .35: pts += f'<rect x="{x + r.randint(14, max(15, w - 40))}" y="{1600 - h + k * 70 + r.randint(20, int(h)):.0f}" width="16" height="9" fill="{r.choice(["#ff4fa3", "#3ff0ff", "#ffd36b"])}" opacity="{.5 + .1 * k:.2f}"/>'
            x += w + r.randint(0, 24)
        b += pts
    b += f'<rect y="1760" width="{W}" height="400" fill="#10031f"/>' + "".join(f'<line x1="{W / 2}" y1="1760" x2="{W / 2 + (i - 18) * 460}" y2="{H}" stroke="#ff4fa3" stroke-width="3" opacity=".6"/>' for i in range(37))
    b += "".join(f'<line x1="0" y1="{1760 + (y ** 1.8) / 9:.0f}" x2="{W}" y2="{1760 + (y ** 1.8) / 9:.0f}" stroke="#3ff0ff" stroke-width="2.4" opacity=".5"/>' for y in range(1, 24, 2))
    return svg(b, d)

def nebulosa_circuitos():
    r = rnd(3); d = vgrad("sky", [(0, "#06031a"), (1, "#101a3d")]); b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    for c, x, y, s in (("#7a3cff", 1100, 700, 1300), ("#17b6ff", 2600, 1300, 1500), ("#ff4fa3", 3300, 500, 900), ("#2de2b4", 700, 1700, 900)):
        d += rgrad("n" + c[1:], c, .55, 0); b += f'<circle cx="{x}" cy="{y}" r="{s}" fill="url(#n{c[1:]})" filter="url(#blur40)"/>'
    b += stars(r, 700, H)
    paths = ""
    for _ in range(46):
        x, y = r.randrange(0, W, 80), r.randrange(0, H, 80); dd = f"M{x},{y}"
        for __ in range(r.randint(3, 7)):
            if r.random() < .5: x += r.choice([-1, 1]) * r.randrange(80, 420, 40)
            else: y += r.choice([-1, 1]) * r.randrange(80, 320, 40)
            dd += f" L{x},{y}"
        col = r.choice(["#17b6ff", "#2de2b4", "#b06bff"]); paths += f'<path d="{dd}" fill="none" stroke="{col}" stroke-width="3" opacity=".6"/><circle cx="{x}" cy="{y}" r="9" fill="{col}" filter="url(#glow)"/>'
    return svg(b + f'<g filter="url(#glow)">{paths}</g>', d)

def isla_flotante():
    r = rnd(4); d = vgrad("sky", [(0, "#2b6cc4"), (.55, "#9fd1f2"), (1, "#f8e8d0")]) + rgrad("sun", "#fff6c9", 1, 0)
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/><circle cx="3000" cy="420" r="520" fill="url(#sun)"/>' + f'<rect width="{W}" height="{H}" fill="#fff" filter="url(#clouds)" opacity=".85"/>'
    for (cx, cy, s, c) in ((1500, 1000, 1.4, "#4f8a4a"), (2900, 700, .7, "#5a9a52"), (700, 600, .5, "#4a8044"), (3350, 1400, .45, "#4f8a4a")):
        w = 760 * s; top = f'<ellipse cx="{cx}" cy="{cy}" rx="{w}" ry="{70 * s}" fill="{c}"/>'
        rock = f'<path d="M{cx - w},{cy} Q{cx - w * .7},{cy + 230 * s} {cx - w * .2},{cy + 560 * s} L{cx},{cy + 760 * s} L{cx + w * .25},{cy + 540 * s} Q{cx + w * .7},{cy + 230 * s} {cx + w},{cy} Z" fill="#6b5846"/><path d="M{cx - w * .5},{cy + 120 * s} L{cx - w * .1},{cy + 600 * s} L{cx + w * .1},{cy + 300 * s} Z" fill="#4e3f32" opacity=".7"/>'
        trees = "".join(f'<ellipse cx="{cx + r.uniform(-w * .8, w * .8):.0f}" cy="{cy - 40 * s:.0f}" rx="{r.uniform(26, 50) * s:.0f}" ry="{r.uniform(50, 100) * s:.0f}" fill="#2f6a3a"/>' for _ in range(int(14 * s) + 3))
        falls = f'<path d="M{cx + w * .55},{cy + 40} L{cx + w * .55},{cy + 1600}" stroke="#d9f3ff" stroke-width="{14 * s:.0f}" opacity=".55" filter="url(#blur4)"/>'
        b += falls + rock + top + trees
    return svg(b, d)

def horizonte_cuantico():
    r = rnd(5); d = vgrad("sky", [(0, "#020512"), (1, "#0d1030")]); b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>' + stars(r, 500, H * .7)
    cx, cy = W / 2, 1180
    for k in range(1, 15):
        rad = 150 * k ** 1.18; col = ["#2de2b4", "#3b9cff", "#b06bff", "#ff4fa3"][k % 4]
        b += f'<ellipse cx="{cx}" cy="{cy}" rx="{rad * 1.9:.0f}" ry="{rad * .5:.0f}" fill="none" stroke="{col}" stroke-width="{max(2, 6 - k * .3):.1f}" opacity="{max(.12, .8 - k * .05):.2f}" transform="rotate({-12 + k * 2.2} {cx} {cy})"/>'
    d += rgrad("core", "#ffffff", 1, 0) + rgrad("halo", "#6aa8ff", .8, 0)
    b += f'<circle cx="{cx}" cy="{cy}" r="620" fill="url(#halo)" filter="url(#blur40)"/><circle cx="{cx}" cy="{cy}" r="150" fill="url(#core)"/><circle cx="{cx}" cy="{cy}" r="46" fill="#fff"/>'
    for _ in range(90):
        a = r.uniform(0, 2 * math.pi); dist = r.uniform(300, 1700); b += f'<circle cx="{cx + dist * math.cos(a) * 1.7:.0f}" cy="{cy + dist * math.sin(a) * .5:.0f}" r="{r.uniform(3, 9):.1f}" fill="{r.choice(["#8be9ff", "#d6a8ff", "#fff"])}" filter="url(#glow)" opacity=".8"/>'
    return svg(b, d)

def bosque_de_luz():
    r = rnd(6); d = vgrad("sky", [(0, "#04140f"), (.6, "#0b3b2c"), (1, "#146b4c")]); b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    d += rgrad("beam", "#d8ffe9", .5, 0)
    for x in (900, 1700, 2500, 3200): b += f'<polygon points="{x},0 {x + 140},0 {x + 760},{H} {x - 360},{H}" fill="url(#beam)" opacity=".35" filter="url(#blur40)"/>'
    for layer in range(4):
        c = ["#0e5a3f", "#0b4733", "#073525", "#04241a"][layer]; n = 9 - layer
        for i in range(n):
            x = (i + r.uniform(.1, .9)) * W / n; w = 90 + layer * 28; top = 100 + layer * 140 + r.uniform(0, 60)
            b += f'<path d="M{x - w},{H} C{x - w * .5},{H * .6} {x - w * .35},{top + 500} {x - w * .2},{top} L{x + w * .2},{top} C{x + w * .35},{top + 500} {x + w * .5},{H * .6} {x + w},{H} Z" fill="{c}"/>'
            b += f'<ellipse cx="{x:.0f}" cy="{top:.0f}" rx="{w * 4.2:.0f}" ry="{w * 1.6:.0f}" fill="{c}" opacity=".95"/>'
    b += "".join(f'<circle cx="{r.uniform(0, W):.0f}" cy="{r.uniform(600, H):.0f}" r="{r.uniform(3, 8):.1f}" fill="{r.choice(["#e9ff9a", "#9affd0", "#fff"])}" filter="url(#glow)" opacity="{r.uniform(.5, 1):.2f}"/>' for _ in range(160))
    return svg(b, d)

def oceano_de_datos():
    r = rnd(7); d = vgrad("sky", [(0, "#031a2e"), (.52, "#0a4a6e"), (1, "#021018")]) + rgrad("moon", "#c8f1ff", 1, 0)
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/><circle cx="2700" cy="500" r="420" fill="url(#moon)" filter="url(#blur12)"/><circle cx="2700" cy="500" r="170" fill="#e9fbff"/>' + stars(r, 300, 900)
    for k in range(26):
        y = 1050 + k ** 1.7 * 9; amp = 8 + k * 3; d_ = f"M0,{y}"
        for x in range(0, W + 120, 120): d_ += f" L{x},{y + math.sin(x / (160 + k * 12) + k) * amp:.0f}"
        b += f'<path d="{d_} L{W},{H} L0,{H} Z" fill="#021018" opacity=".12"/><path d="{d_}" fill="none" stroke="{r.choice(["#3ff0ff", "#2de2b4", "#6aa8ff"])}" stroke-width="{1.5 + k * .12:.1f}" opacity="{.15 + k * .03:.2f}"/>'
    cols = ""
    for x in range(0, W, 46):
        if r.random() < .55:
            top = r.uniform(900, 1500); cols += "".join(f'<text x="{x}" y="{y}" font-family="monospace" font-size="26" fill="#3ff0ff" opacity="{max(0, .8 - (y - top) / 700):.2f}">{r.choice("01")}</text>' for y in range(int(top), int(top) + 640, 34))
    return svg(b + cols, d)

def portal():
    r = rnd(8); d = vgrad("sky", [(0, "#1a0b2e"), (1, "#3a2255")]) + rgrad("pg", "#ffe9a8", 1, 0)
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>' + stars(r, 350, H) + ridge(r, 1850, 100, "#120a22", 1, 12)
    cx, cy = W / 2, 1050
    d += rgrad("in", "#fff3c4", 1, .0)
    b += f'<ellipse cx="{cx}" cy="{cy}" rx="640" ry="820" fill="url(#pg)" filter="url(#blur40)"/>'
    for k, c in enumerate(["#ff8ad8", "#8ad7ff", "#ffe08a", "#a98aff", "#8affc9"]):
        b += f'<ellipse cx="{cx}" cy="{cy}" rx="{520 - k * 44}" ry="{690 - k * 56}" fill="none" stroke="{c}" stroke-width="{16 - k * 2}" filter="url(#glow)" opacity=".9"/>'
    b += f'<ellipse cx="{cx}" cy="{cy}" rx="330" ry="470" fill="#fff3d0"/>' 
    b += "".join(f'<circle cx="{cx + r.uniform(-900, 900):.0f}" cy="{cy + r.uniform(-900, 900):.0f}" r="{r.uniform(3, 10):.1f}" fill="#ffe9a8" filter="url(#glow)" opacity=".8"/>' for _ in range(120))
    b += f'<rect y="1800" width="{W}" height="400" fill="#0b0618"/><ellipse cx="{cx}" cy="1850" rx="620" ry="60" fill="#ffe9a8" opacity=".25" filter="url(#blur12)"/>'
    return svg(b, d)

def galaxia_espiral():
    r = rnd(9); d = vgrad("sky", [(0, "#02030c"), (1, "#080a22")]) + rgrad("core", "#fff0c8", 1, 0); b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>' + stars(r, 800, H)
    cx, cy = W * .56, H * .5
    for arm in range(3):
        for i in range(1500):
            t = i / 1500 * 5.2; ang = t + arm * 2 * math.pi / 3; rad = 80 + t * 330; x = cx + rad * math.cos(ang) * 1.6 + r.gauss(0, 34 + t * 12); y = cy + rad * math.sin(ang) * .62 + r.gauss(0, 28 + t * 9)
            col = r.choice(["#8fd0ff", "#b8a0ff", "#ffd3ee", "#fff"]); b += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r.choice([1.6, 2.2, 3.2, 4.4]):.1f}" fill="{col}" opacity="{max(.15, .9 - t * .13):.2f}"/>'
    b += f'<ellipse cx="{cx}" cy="{cy}" rx="620" ry="290" fill="url(#core)" filter="url(#blur40)"/><ellipse cx="{cx}" cy="{cy}" rx="170" ry="84" fill="#fff6d8"/>'
    d += rgrad("neb", "#6d3cff", .4, 0); b = f'<circle cx="{W * .2}" cy="{H * .3}" r="700" fill="url(#neb)" filter="url(#blur40)"/>' + b
    return svg(b, d)

def montanas_de_cristal():
    r = rnd(10); d = vgrad("sky", [(0, "#0b1d4a"), (.6, "#4a5fb3"), (1, "#c7a8ff")]) + rgrad("sun", "#fff", 1, 0)
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/><circle cx="800" cy="520" r="360" fill="url(#sun)" opacity=".8" filter="url(#blur12)"/>' + stars(r, 200, 800)
    for layer in range(4):
        base = 1500 + layer * 170; n = 7 + layer * 2; c = ["#8f7be0", "#6a57c4", "#4a3d9c", "#2b2370"][layer]
        for i in range(n):
            x = (i + r.uniform(.2, .8)) * W / n; w = r.uniform(240, 520) * (1 + (3 - layer) * .12); h = r.uniform(420, 920) * (1 - layer * .12)
            b += f'<polygon points="{x - w:.0f},{base + 400} {x:.0f},{base - h:.0f} {x + w:.0f},{base + 400}" fill="{c}"/><polygon points="{x:.0f},{base - h:.0f} {x + w:.0f},{base + 400} {x + w * .12:.0f},{base + 400}" fill="#fff" opacity="{.10 + .04 * (3 - layer):.2f}"/><polygon points="{x:.0f},{base - h:.0f} {x - w * .35:.0f},{base - h * .35:.0f} {x + w * .1:.0f},{base - h * .3:.0f}" fill="#fff" opacity=".18"/>'
    b += f'<rect y="2040" width="{W}" height="160" fill="#150f3d"/>'
    return svg(b, d)

def luna_neuronal():
    r = rnd(11); d = vgrad("sky", [(0, "#04061a"), (1, "#0f1b44")]) + rgrad("moon", "#dfe9ff", 1, 0); b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>' + stars(r, 350, H)
    b += f'<circle cx="2900" cy="700" r="760" fill="url(#moon)" filter="url(#blur40)" opacity=".7"/><circle cx="2900" cy="700" r="330" fill="#eef3ff"/><circle cx="2780" cy="650" r="58" fill="#cfd8f2"/><circle cx="3010" cy="790" r="86" fill="#cfd8f2"/><circle cx="2860" cy="820" r="40" fill="#d7dff5"/>'
    nodes = [(r.uniform(100, W - 100), r.uniform(900, H - 100)) for _ in range(70)]; ln = ""
    for i, (x, y) in enumerate(nodes):
        for (x2, y2) in sorted(nodes, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)[1:4]: ln += f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#6aa8ff" stroke-width="2" opacity=".45"/>'
    dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r.choice([8, 11, 15]):.0f}" fill="{r.choice(["#8be9ff", "#d6a8ff", "#9affd0"])}"/>' for x, y in nodes)
    return svg(b + ln + f'<g filter="url(#glow)">{dots}</g>', d)

def desierto_hologramas():
    r = rnd(12); d = vgrad("sky", [(0, "#3a1a5e"), (.45, "#e0527a"), (.75, "#ffb36b"), (1, "#ffe0a0")]); b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    d += rgrad("sun", "#fff2c4", 1, 0); b += f'<circle cx="1200" cy="1250" r="440" fill="url(#sun)"/><circle cx="1200" cy="1250" r="210" fill="#fff6dc"/>'
    for k, c in enumerate(["#c8604a", "#a14a46", "#7a3744", "#4f2a3f"]): b += smooth(r, 1450 + k * 160, 90 - k * 10, c, 1, 8)
    for x, y, s in ((2700, 1180, 1.3), (3300, 1380, .8), (2100, 1500, .6)):
        pts = hexpoly(x, y, 150 * s); b += f'<g filter="url(#glow)" fill="none" stroke="#3ff0ff" stroke-width="{4 * s:.1f}" opacity=".9"><polygon points="{pts}"/><polygon points="{hexpoly(x, y, 90 * s, .3)}" opacity=".6"/><line x1="{x}" y1="{y + 150 * s}" x2="{x}" y2="{y + 520 * s}" opacity=".5"/></g>'
    return svg(b, d)

def marea_de_particulas():
    r = rnd(13); d = vgrad("sky", [(0, "#050816"), (1, "#0c1630")]); b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    for row in range(34):
        y = 600 + row * 44; col = ["#2de2b4", "#3b9cff", "#8a7bff", "#ff6ad5"][row % 4]; dots = ""
        for x in range(0, W, 28 if row < 20 else 40):
            yy = y + math.sin(x / 230 + row * .35) * (70 + row * 3) + math.sin(x / 90 + row) * 14; dots += f'<circle cx="{x}" cy="{yy:.0f}" r="{2.8 + row * .12:.1f}" fill="{col}" opacity="{.5 + row * .015:.2f}"/>'
        b += dots
    b += f'<rect width="{W}" height="700" fill="url(#sky)" opacity=".9"/>' + stars(r, 260, 620)
    return svg(b, d)

def catedral_de_luz():
    r = rnd(14); d = vgrad("sky", [(0, "#0a0f2b"), (1, "#2a2060")]) + rgrad("g", "#ffe9b0", .9, 0); b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>' + stars(r, 250, 900)
    cx = W / 2; b += f'<ellipse cx="{cx}" cy="1100" rx="900" ry="1100" fill="url(#g)" filter="url(#blur40)"/>'
    for i in range(-8, 9):
        x = cx + i * 230; h = 1400 - abs(i) * 110
        b += f'<path d="M{x - 40},{H} L{x - 40},{H - h + 220} Q{x},{H - h - 120} {x + 40},{H - h + 220} L{x + 40},{H} Z" fill="#0b0a24" opacity=".95"/><path d="M{x - 40},{H - h + 220} Q{x},{H - h - 120} {x + 40},{H - h + 220}" fill="none" stroke="#ffe9b0" stroke-width="5" filter="url(#glow)" opacity=".9"/>'
    b += f'<polygon points="{cx - 140},0 {cx + 140},0 {cx + 520},{H} {cx - 520},{H}" fill="#ffe9b0" opacity=".22" filter="url(#blur12)"/>'
    b += f'<rect y="1900" width="{W}" height="300" fill="#0b0a24"/><ellipse cx="{cx}" cy="1960" rx="700" ry="50" fill="#ffe9b0" opacity=".3" filter="url(#blur12)"/>'
    return svg(b, d)

def sueno_lucido():
    r = rnd(15); d = vgrad("sky", [(0, "#2a1b5e"), (.5, "#6b4fbf"), (1, "#f7a8d4")]); b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>' + stars(r, 180, 700)
    b += f'<rect width="{W}" height="{H}" fill="#fff" filter="url(#clouds)" opacity=".5"/>'
    d += rgrad("m1", "#fff0fb", 1, 0); b += f'<circle cx="2600" cy="600" r="330" fill="url(#m1)" filter="url(#blur12)"/><circle cx="2600" cy="600" r="210" fill="#fff6fd"/><circle cx="3060" cy="480" r="80" fill="#ffd9f1"/>'
    for i in range(5):
        y = 1300 + i * 150; b += f'<path d="M0,{y} C{W * .25},{y - 160 - i * 20} {W * .5},{y + 120} {W * .75},{y - 80} S{W},{y + 40} {W},{y} L{W},{H} L0,{H} Z" fill="{["#9a73d6", "#7c58bf", "#5d3fa0", "#43307f", "#2b1f5e"][i]}" opacity=".96"/>'
    for i in range(14):
        x = r.uniform(200, W - 200); y = r.uniform(1000, 1700); s = r.uniform(.5, 1.4)
        b += f'<g transform="translate({x:.0f},{y:.0f}) scale({s:.2f})" filter="url(#glow)" opacity=".85"><ellipse cx="0" cy="-40" rx="26" ry="52" fill="#ffe0f6"/><ellipse cx="0" cy="40" rx="8" ry="70" fill="#c7b0ff" opacity=".6"/></g>'
    return svg(b, d)

FONDOS = [("01-aurora-digital", aurora_digital), ("02-ciudad-neon", ciudad_neon), ("03-nebulosa-de-circuitos", nebulosa_circuitos), ("04-isla-flotante", isla_flotante), ("05-horizonte-cuantico", horizonte_cuantico),
          ("06-bosque-de-luz", bosque_de_luz), ("07-oceano-de-datos", oceano_de_datos), ("08-portal", portal), ("09-galaxia-espiral", galaxia_espiral), ("10-montanas-de-cristal", montanas_de_cristal),
          ("11-luna-neuronal", luna_neuronal), ("12-desierto-de-hologramas", desierto_hologramas), ("13-marea-de-particulas", marea_de_particulas), ("14-catedral-de-luz", catedral_de_luz), ("15-sueno-lucido", sueno_lucido)]

def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True); solo = sys.argv[2:] 
    for nombre, fn in FONDOS:
        if solo and not any(s in nombre for s in solo): continue
        with tempfile.TemporaryDirectory() as t:
            open(f"{t}/a.svg", "w").write(fn()); subprocess.run(["rsvg-convert", "-w", str(W), f"{t}/a.svg", "-o", f"{t}/a.png"], check=True)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{t}/a.png", "-q:v", "3", f"{out}/{nombre}.jpg"], check=True)
        print("ok", nombre, os.path.getsize(f"{out}/{nombre}.jpg") // 1024, "KB", flush=True)

if __name__ == "__main__": main()
