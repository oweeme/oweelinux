# Plantilla de app de OweeLinux (borrador)

`app.py` es una app completa en 20 líneas (con docstring y líneas en blanco) (Python + GTK4 + libadwaita).
`manifest.json` es el borrador del formato `owee-app`; **aún no hay herramienta que lo empaquete**
(la idea es generar un Flatpak a partir de él; ver `docs/FASES.md`, F7).

Estado: la sintaxis está comprobada (`python3 -m py_compile app.py`), pero **no se ha ejecutado**:
GTK4 y libadwaita no están instalados en la máquina de desarrollo actual. Se probará en la imagen real.

Las apps no están obligadas a usar GTK4: Flatpak permite apps en Qt, web o nativas. GTK4 + Python es
el camino recomendado y el que usa el propio shell.
