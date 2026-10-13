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
# Logo de OweeLinux (el pez koi del autor, desktop/theme/branding): PNG de 32 px (basta para el panel y pesa poco en memoria; el original grande queda en branding/)
import shutil
os.makedirs(os.path.join(dest, "32x32", "apps"), exist_ok=True)
shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "branding", "owee-logo-32.png"), os.path.join(dest, "32x32", "apps", "owee-logo.png"))
open(os.path.join(dest, "index.theme"), "w").write("""[Icon Theme]
Name=%s
Comment=Iconos propios de OweeLinux (línea, redondeados)
Inherits=breeze,Adwaita,hicolor
Directories=scalable/actions,32x32/apps

[scalable/actions]
Size=24
MinSize=8
MaxSize=512
Type=Scalable
Context=Actions

[32x32/apps]
Size=32
MinSize=16
MaxSize=64
Type=Scalable
Context=Applications
""" % NAME)
print("iconos escritos en", dest, "(%d)" % len(os.listdir(out)))
