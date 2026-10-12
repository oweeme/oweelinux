# Medición GTK4 frente a Qt6 en Python (2026-10-12)
`tg.py` (GTK4/PyGObject) y `tq.py` (Qt6/PySide6) abren una ventana mínima y miden su memoria (`mem.py`: Rss, Pss y USS =
memoria privada). `qt-vs-gtk-harness.py` las ejecuta en la sesión Lite de una VM; `base-ram-harness.py` lista qué procesos
ocupan la memoria. **Son scripts de una sola vez**: tienen rutas de la sesión de trabajo escritas dentro (carpeta de
scratchpad, `~/.cache/oweelinux/vm/`); hay que adaptarlas. PySide6 no está en la imagen: se descargaron los .deb
(`libshiboken6-py3-6.8`, `libpyside6-py3-6.8`, `python3-pyside6.qt{core,gui,widgets}`, ~8 MB), se extrajeron a un `.tgz` y se
usaron desde `/tmp` con `PYTHONPATH` y `LD_LIBRARY_PATH`. Resultados en `docs/ESCRITORIO.md`.
