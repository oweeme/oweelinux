# Resiliencia de la sesión (F-R) — mediciones

Fecha: 2026-10-12. Imagen: Debian 13 + Plasma (X11) sobre ostree, en QEMU/KVM. Pruebas en
`tools/ostree-proto/` (`resilience-test.py`, `lock-test.py`). **Una sola ejecución por escenario**: son
mediciones orientativas, no estadísticas. La resolución de la latencia es ~0,3 s.

## Motivación
El autor tuvo una pantalla de bloqueo de Deepin que no respondió ~10 minutos durante una compilación de
Java/Android (ver `docs/FASES.md`, F-R). El journal mostró que el kernel y la consola seguían vivos; el
servicio de red de la sesión de Deepin desapareció a la hora del cuelgue. **No se reprodujo ese cuelgue**
y la causa sigue sin conocerse.

## 1. Un proceso que consume toda la memoria (VM 3 GB, disco rápido)
Un proceso (`tail /dev/zero`) que consume memoria de golpe, 90 s. Latencia máxima de la consola y del servidor gráfico:
| Escenario | Consola | Pantalla | ¿Qué pasó con el proceso? | Sobreviven plasmashell/kwin/Xorg/sddm |
|---|---|---|---|---|
| S0 control | 0,3 s | 0,3 s | — | sí |
| S1 sin protección, sin swap | 0,3 s | 0,3 s | OOM del kernel lo mató | sí |
| S2 con swap en disco | 0,3 s | 0,3 s | OOM lo mató | sí |
| S3 con `MemoryMax=1G` | 0,3 s | 0,3 s | contenido, sigue vivo | sí |
| S4 sesión protegida (`oom_score_adj=-900`) | 0,3 s | 0,6 s | OOM lo mató | sí |
**Lectura:** con un agotamiento abrupto, el kernel mata al culpable al instante y **no** al escritorio. Esta
prueba **no** reproduce un cuelgue. Es el peor caso de velocidad, pero no de *thrashing*.

## 2. Presión gradual (~60 MB/s) con disco lento (VM 2 GB, swap 1,5 GB, 250 IOPS y 30 MB/s)
Disco limitado con QEMU para acercarse a un disco mecánico o a un SSD saturado. 150 s de ventana.
| Escenario | Latencia máx. consola | Latencia máx. pantalla | El proceso desbocado… | Muertes por OOM |
|---|---|---|---|---|
| T0 control (sin proceso) | 0,3 s | 0,3 s | — | 0 |
| T1 **sin protección** | **2,1 s** | **2,4 s** | lo mató el kernel a los **138 s** | 1 (el culpable) |
| T2 con `MemoryMax=900M`/`MemoryHigh=700M` | 0,3 s | 0,3 s | contenido (sigue vivo y frenado) | 0 |
| T3 con **`earlyoom`** | 0,3 s | 0,3 s | lo mató `earlyoom` a los **67 s** | 0 del kernel |
En los cuatro, el escritorio sobrevivió y respondió al final.
**Lectura:** sin protección el sistema se ralentizó hasta ~2 s y el kernel tardó 138 s en actuar. Con el
límite de memoria el escritorio no notó nada; con `earlyoom` el culpable cayó a la mitad del tiempo y sin
retraso apreciable. **Tampoco se reprodujo un cuelgue de minutos.**

## 3. Pantalla de bloqueo de Plasma con servicios caídos
Bloquear con `loginctl lock-sessions`; en un caso se detienen NetworkManager, upower, power-profiles-daemon y
se matan pipewire, wireplumber y powerdevil **con la pantalla ya bloqueada**; luego pulsar Enter (el usuario de
prueba no tiene contraseña) con el teclado virtual de QEMU. Captura: `docs/img/f-r-bloqueo-kde.png`.
| Caso | Bloqueo activo | Desbloqueo con Enter | Escritorio responde |
|---|---|---|---|
| Sin fallos inyectados | sí | 1,1 s | sí |
| Con red, energía y audio caídos | sí | 1,1 s | sí |
**Lectura:** el bloqueo de KDE (`kscreenlocker`) **no depende** de esos servicios en estas condiciones y su
interfaz es mínima (avatar, usuario, botón). Es un punto de referencia para el bloqueo de OweeLinux.
No se probó la receta de recuperación `loginctl unlock-sessions` (solo hizo falta el camino A).

## Qué se puede concluir y qué no
- ✔ Un agotamiento de memoria **gradual** sin protección sí degrada la respuesta (≈2 s en esta VM) y deja al kernel tardar más de 2 minutos en actuar; **`earlyoom` y los límites de cgroup lo evitan** en estas pruebas.
- ✔ El bloqueo de KDE aguantó la caída de red/energía/audio.
- ✘ **No se reprodujo el cuelgue del autor**; no se puede afirmar que estas medidas lo habrían evitado.
- ✘ Límites del montaje: VM de 2-3 GB, disco simulado, una sola ejecución, sin Java real, sesión X11, consumo sintético.

## Siguiente
- Repetir la serie 2 con varias ejecuciones y un consumo parecido al de Gradle (picos y lecturas de disco).
- Probar `systemd-oomd` además de `earlyoom` (no está en la imagen) y decidir cuál adoptar.
- Probar la receta `loginctl unlock-sessions` y qué pasa si el bloqueador **muere**.
- Un bloqueo propio (cuando exista el shell) debe pasar la misma prueba de fallos.
