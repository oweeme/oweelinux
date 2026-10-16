#!/usr/bin/env python3
"""Generador de los iconos PROPIOS de OweeLinux (tema "Owee"). Dibujos originales de línea (trazo redondeado de 1,8 px sobre 24x24), hechos aquí
con formas simples para que cualquiera pueda cambiarlos. Uso: gen_icons.py DESTINO [COLOR_TRAZO [NOMBRE]]   (por defecto #EFF0F1 y "Owee", para barras oscuras; el tema claro es #17231e y "Owee-Light").
Escribe DESTINO/Owee/{index.theme,scalable/actions/*.svg}. Para otro estilo (p. ej. modo claro) basta otro color o cambiar STROKE."""
import os, sys
col = sys.argv[2] if len(sys.argv) > 2 else "#EFF0F1"; NAME = sys.argv[3] if len(sys.argv) > 3 else "Owee"
dest = os.path.join(sys.argv[1], NAME)
out = os.path.join(dest, "scalable", "actions"); os.makedirs(out, exist_ok=True)
STROKE = 1.8
def svg(name, body, fill_none=True):
    open(os.path.join(out, name + ".svg"), "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{col}" stroke-width="{STROKE}" stroke-linecap="round" stroke-linejoin="round">{body}</svg>\n')
P = lambda d, extra="": f'<path d="{d}" {extra}/>'
svg("owee-power", P("M7.2 5.6a8 8 0 1 0 9.6 0") + P("M12 3.5v8"))
svg("owee-restart", P("M19.5 12a7.5 7.5 0 1 1-2.4-5.5") + P("M19.5 4v4.2h-4.2"))
svg("owee-logout", P("M10 4.5H6.5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2H10") + P("M15 8l4 4-4 4M19 12H9.5"))
svg("owee-lock", '<rect x="5" y="11" width="14" height="9.5" rx="2.5"/>' + P("M8.2 11V8.2a3.8 3.8 0 0 1 7.6 0V11") + '<circle cx="12" cy="15.7" r="1" fill="%s" stroke="none"/>' % col)
svg("owee-network-wifi", P("M2.5 9.2a14.5 14.5 0 0 1 19 0M5.6 12.6a10 10 0 0 1 12.8 0M8.8 16a5.4 5.4 0 0 1 6.4 0") + f'<circle cx="12" cy="19.4" r="1.1" fill="{col}" stroke="none"/>')
svg("owee-network-wired", '<rect x="3.5" y="5" width="17" height="9" rx="2"/>' + P("M7.5 14v3h9v-3M12 17v3M8 20h8M8 8.5v2.5M12 8.5v2.5M16 8.5v2.5"))
svg("owee-network-offline", P("M2.5 9.2a14.5 14.5 0 0 1 19 0M5.6 12.6a10 10 0 0 1 12.8 0M8.8 16a5.4 5.4 0 0 1 6.4 0", 'opacity="0.55"') + f'<circle cx="12" cy="19.4" r="1.1" fill="{col}" stroke="none" opacity="0.55"/>' + P("M4.5 3.5l15 17", 'stroke="#F06548"'))
spk = P("M4 9.5v5h3.8L13 18.5v-13L7.8 9.5z")
svg("owee-volume-muted", spk + P("M16.2 9.6l4.6 4.8M20.8 9.6l-4.6 4.8"))
svg("owee-volume-low", spk + P("M16.3 9.5a3.6 3.6 0 0 1 0 5"))
svg("owee-volume-high", spk + P("M16.3 9.5a3.6 3.6 0 0 1 0 5M18.8 6.8a7.4 7.4 0 0 1 0 10.4"))
for lvl in (0, 20, 40, 60, 80, 100):
    w = round(13 * lvl / 100, 1); fill = f'<rect x="4.5" y="9.5" width="{w}" height="5" rx="0.8" fill="{col}" stroke="none"/>' if lvl else ""
    shell = '<rect x="2.5" y="7" width="16" height="10" rx="2.2"/>' + P("M21 10.5v3")
    svg(f"owee-battery-{lvl}", shell + fill)
    svg(f"owee-battery-{lvl}-charging", shell + fill + '<path d="M11 8.6l-2.6 4h3.4l-2.6 4" stroke="#F06548" stroke-width="1.6"/>')
# --- iconos de la app de Ajustes
svg("owee-set-appearance", P("M12 3a9 9 0 1 0 0 18c1.2 0 1.8-.9 1.4-1.9-.5-1.1.1-2.1 1.3-2.1H17a4 4 0 0 0 4-4c0-5-4-10-9-10z") + f'<circle cx="7.6" cy="11" r="1.1" fill="{col}" stroke="none"/><circle cx="10.2" cy="7.3" r="1.1" fill="{col}" stroke="none"/><circle cx="14.8" cy="7.3" r="1.1" fill="{col}" stroke="none"/>')
svg("owee-set-wallpaper", '<rect x="3" y="4.5" width="18" height="15" rx="2.5"/>' + P("M3.5 16l5-5 4 4 3-3 5 5") + f'<circle cx="16.5" cy="9" r="1.4" fill="{col}" stroke="none"/>')
svg("owee-set-display", '<rect x="3" y="4.5" width="18" height="12" rx="2"/>' + P("M9 20h6M12 16.5V20"))
svg("owee-set-keyboard", '<rect x="2.8" y="6" width="18.4" height="12" rx="2.2"/>' + P("M6.5 10h.01M10 10h.01M14 10h.01M17.5 10h.01M6.5 13.5h.01M17.5 13.5h.01M9 14h6"))
svg("owee-set-mouse", '<rect x="6.5" y="3" width="11" height="18" rx="5.5"/>' + P("M12 3v6M6.5 9h11"))
svg("owee-set-power", P("M13 2.8L5.5 13h5.5l-1 8.2L18.5 11H13z"))
svg("owee-set-clock", '<circle cx="12" cy="12" r="9"/>' + P("M12 7v5.2l3.2 2"))
svg("owee-set-info", '<circle cx="12" cy="12" r="9"/>' + P("M12 11v5.5") + f'<circle cx="12" cy="7.8" r="1" fill="{col}" stroke="none"/>')
svg("owee-set-update", P("M20 12a8 8 0 0 1-14 5.3M4 12a8 8 0 0 1 14-5.3") + P("M18.5 3v4h-4M5.5 21v-4h4"))
svg("owee-set-bluetooth", P("M7 7.5l10 9-5 4.5V3l5 4.5-10 9"))
svg("owee-bluetooth", P("M7 7.5l10 9-5 4.5V3l5 4.5-10 9"))
svg("owee-set-apps", ''.join(f'<rect x="{x}" y="{y}" width="6" height="6" rx="1.6"/>' for x in (4, 14) for y in (4, 14)))
svg("owee-set-desktops", '<rect x="3" y="5" width="8" height="6" rx="1.6"/><rect x="13" y="5" width="8" height="6" rx="1.6"/><rect x="3" y="13" width="8" height="6" rx="1.6"/>' + '<rect x="13" y="13" width="8" height="6" rx="1.6" fill="%s" stroke="none"/>' % col)
svg("owee-set-shortcuts", P("M12 3v18M3 12h18") + '<circle cx="12" cy="12" r="2.4"/>')
svg("owee-set-language", '<circle cx="12" cy="12" r="9"/>' + P("M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"))
svg("owee-set-users", '<circle cx="12" cy="8" r="3.6"/>' + P("M5 20c0-4 3.2-6.5 7-6.5s7 2.5 7 6.5"))
svg("owee-set-fonts", P("M3.5 19l5-13 5 13M5.4 14h6.2") + P("M15.5 19l3-7.5 3 7.5M16.6 16.5h3.8"))
svg("owee-set-network", P("M3.5 9.5a12 12 0 0 1 17 0M6.5 13a7.7 7.7 0 0 1 11 0M9.5 16.4a3.4 3.4 0 0 1 5 0") + f'<circle cx="12" cy="19.2" r="1.2" fill="{col}" stroke="none"/>')
svg("owee-clipboard", '<rect x="5" y="4.5" width="14" height="16.5" rx="2.2"/>' + P("M9 4.5V3.6h6v.9M8.5 10h7M8.5 13.5h7M8.5 17h4"))
svg("owee-calendar", '<rect x="3.5" y="5" width="17" height="15.5" rx="2.6"/>' + P("M3.5 10h17M8 3v4M16 3v4M8 14h.01M12 14h.01M16 14h.01M8 17.5h.01M12 17.5h.01"))
svg("owee-set-backup", P("M4 13a8 8 0 1 0 2.4-5.7M4 4.5V9h4.5") + P("M12 8v4.5l3 1.8"))
svg("owee-set-lock", '<rect x="5" y="10.5" width="14" height="10" rx="2.4"/>' + P("M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"))
# --- Calculadora (icono de la app y del historial)
open(os.path.join(out, "owee-calc.svg"), "w").write('''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect x="8" y="4" width="48" height="56" rx="10" fill="#102019"/><rect x="14" y="10" width="36" height="14" rx="4" fill="#2A9D8F"/><g fill="#EFF0F1"><circle cx="21" cy="34" r="3.4"/><circle cx="32" cy="34" r="3.4"/><circle cx="43" cy="34" r="3.4"/><circle cx="21" cy="45" r="3.4"/><circle cx="32" cy="45" r="3.4"/><circle cx="21" cy="55" r="0"/></g><rect x="38" y="41" width="10" height="14" rx="5" fill="#F06548"/></svg>\n''')
svg("owee-calc-history", P("M3.5 12a8.5 8.5 0 1 0 2.6-6.1M3.5 4v4.5H8") + P("M12 7.5V12l3 2"))
open(os.path.join(out, "owee-capture.svg"), "w").write('''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect x="6" y="12" width="52" height="40" rx="9" fill="#102019"/><path d="M6 24V21a9 9 0 0 1 9-9h6M43 12h6a9 9 0 0 1 9 9v3M58 40v3a9 9 0 0 1-9 9h-6M21 52h-6a9 9 0 0 1-9-9v-3" fill="none" stroke="#2A9D8F" stroke-width="4" stroke-linecap="round"/><circle cx="32" cy="32" r="8" fill="#F06548"/></svg>\n''')
# Logo de OweeLinux (el pez koi del autor, desktop/theme/branding): PNG de 32 px (basta para el panel y pesa poco en memoria; el original grande queda en branding/)
import shutil
for sz in (32, 64, 128):        # el logo en varios tamaños (reducidos del original de 945 px con lanczos): con uno solo de 32 px se veía borroso al agrandarlo (asistente de primer arranque)
    os.makedirs(os.path.join(dest, f"{sz}x{sz}", "apps"), exist_ok=True)
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "branding", f"owee-logo-{sz}.png"), os.path.join(dest, f"{sz}x{sz}", "apps", "owee-logo.png"))
open(os.path.join(dest, "index.theme"), "w").write("""[Icon Theme]
Name=%s
Comment=Iconos propios de OweeLinux (línea, redondeados)
Inherits=breeze,Adwaita,hicolor
Directories=scalable/actions,32x32/apps,64x64/apps,128x128/apps

[scalable/actions]
Size=24
MinSize=8
MaxSize=512
Type=Scalable
Context=Actions

[32x32/apps]
Size=32
MinSize=16
MaxSize=48
Type=Scalable
Context=Applications

[64x64/apps]
Size=64
MinSize=49
MaxSize=96
Type=Scalable
Context=Applications

[128x128/apps]
Size=128
MinSize=97
MaxSize=512
Type=Scalable
Context=Applications
""" % NAME)
print("iconos escritos en", dest, "(%d)" % len(os.listdir(out)))
