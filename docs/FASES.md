# OweeLinux 2 — Fases de trabajo y verificación

Estado: **plan propuesto** (aún sin aprobar fase por fase).
Decisiones base: Debian 13 · imagen inmutable con **ostree** · apps por Flatpak ·
herramientas de desarrollo en cajas (Podman/distrobox) · shell propio (labwc + Python/GTK4; ver F6)
como **segunda sesión** junto a Plasma · licencia GPLv3.

**Regla de oro del plan:** cada fase termina con una **prueba que se puede repetir**.
Si la prueba no pasa, no se empieza la siguiente. Las metas numéricas (tiempos, RAM)
se fijan en F0 con mediciones reales; aquí solo se propone la forma de medirlas.

## Orden de ejecución (reordenado el 2026-10-11)

**Criterio:** llegar cuanto antes a un sistema **funcional y usable**, y optimizar sobre algo
real. Los números de fase (F0…F9) son nombres, no el orden: este es el orden.

| Prioridad | Qué | Por qué en este lugar | Hito |
|---|---|---|---|
| ✅ 1 | F0 base · F3a arranque ostree · F3b actualizar · F3c rollback | Hecho y probado en QEMU | |
| ✅ 2 | **F3d corte de energía** (40 iteraciones válidas sin fallos en el prototipo; F3c-bis hecho: initramfs roto, servicio bloqueante y cuelgue total rescatados solos) | Es la puerta de F3: sin ella no se puede confiar en la base | |
| ✅ 3 | **F3h imagen real**: Debian + Plasma + red + audio sobre ostree, que arranca hasta el login gráfico en QEMU | Hoy solo hay un Debian mínimo sin pantalla. Esto es lo que lo hace *funcional* | **M1 ✅ (en VM)**: arranca hasta Plasma desde ostree; actualizar, rollback automático y corte de energía verificados sobre esta imagen |
| **3b** | **R: resiliencia de la sesión ante procesos desbocados** (ver F-R abajo) | Es un dolor real y reciente del autor: una compilación grande dejó una máquina colgada 10+ minutos y obligó a reiniciar sin guardar. No depende del hardware: se prueba en la VM | |
| **4a** | **Firmware y microcódigo** en la imagen (WiFi, GPU, CPU): componente `non-free-firmware` de Debian | Sin esto no hay WiFi en muchas laptops (la imagen se construyó solo con `main`). Es una decisión de empaquetado, comprobable sin hardware | |
| **4b** | **Firma de las actualizaciones** (ostree con GPG) y luego HTTPS | Hoy las actualizaciones no se verifican: bloqueante de seguridad antes de cualquier uso fuera de la VM | |
| **4c** | **Prototipo de riesgos del escritorio "Lite"** (v0.0 de `docs/ESCRITORIO.md`) | Es barato y decide si Python/GTK4 vale para el panel antes de invertir meses | |
| 4 | F3e/F3f Nvidia y Secure Boot en la imagen real | La imagen real los necesita antes de tocar hardware | |
| 5 | F5 instalar en disco real (primero un script, luego Calamares) | Sin instalación no se puede usar fuera de la VM | **M2: instalable** |
| 6 | F4 Flatpak, cajas de desarrollo, Quadlet | Lo que lo vuelve útil a diario | **M3: usable a diario** |
| 7 | F2 dieta de servicios y arranque rápido | Se mide sobre la imagen real, no sobre un prototipo | |
| 8 | F1 ISO live/CI nocturno | Distribución a terceros; no bloquea el uso propio | |
| 9 | F6 shell Lite · F7 apps propias (`owee-capture`, `owee-app`) | Diferenciación: solo con la base estable | **M4: identidad propia** |
| 10 | F8 pulido y beta · F9 `owee-nap` | Cierre | v1 |

**Cambios respecto al orden anterior:**
- F2 (arranque) pasa de 3.º a 7.º: optimizar un prototipo mínimo da cifras que no sirven.
- F1 (ISO/CI) baja: para uso propio basta el disco de la VM; la ISO es para repartir.
- **Nuevo F3h (imagen real)** como prioridad 3: es el paso que faltaba entre "prototipo" y "funcional".
- F5 (instalador) sube por encima de F4: sin poder instalar no se prueba nada en hardware.
- Pruebas siempre en **VM o en un equipo de prueba**; la máquina de trabajo diaria no se toca.

**Qué significa cada hito:**
- **M1** — arranca desde ostree hasta el login gráfico de Plasma en QEMU; actualizar, rollback automático y corte de energía verificados.
- **M2** — se instala en un disco y arranca en un equipo de prueba (con Nvidia si aplica).
- **M3** — se instalan apps (Flatpak), se desarrolla en cajas y los datos sobreviven a actualizar/rollback.
- **M4** — escritorio propio y apps propias como segunda sesión.

---

## F0 — Base de trabajo y línea base
- [x] Medición inicial en `docs/BASELINE.md` (hardware: Lenovo i5-7200U, no el Dell)
- [x] Pod `oweelinux` + `tools/devpod/` (Debian 13, live-build, mmdebstrap, ostree)
- [ ] `docs/BASELINE.md`: `systemd-analyze` (+ `blame`, `critical-chain`), RAM en reposo y tiempo hasta la primera ventana de 5 apps, en la **máquina real** (Dell G3) y en Deepin como referencia
- [ ] Lista de hardware de prueba (Dell G3 con Nvidia, la HP sin Nvidia, una VM)

**Verificación:** `devpod.sh up` + `lb --version` + `ostree --version` funcionan; `BASELINE.md` con cifras reales y la fecha.

## F1 — Build reproducible + prueba de arranque automática
- [ ] Un comando construye la ISO actual dentro del contenedor (rootful/privilegiado o VM)
- [ ] Script QEMU que arranca la ISO sin pantalla y confirma "llegó al login" (consola serie o captura por QMP)
- [ ] Registro de la lista de paquetes de cada build (para comparar)

**Verificación:** dos builds seguidos dan la misma lista de paquetes; la prueba de arranque pasa 10/10 veces.

## F2 — Arreglos rápidos de arranque (sobre el sistema actual)
- [ ] **Investigar primero** qué consume el *loader* (en la referencia no es el menú de GRUB); luego quitar `NetworkManager-wait-online`, `apt-daily` en el arranque y otros servicios del camino crítico
- [ ] **Dieta de servicios (activación perezosa)**: clasificar cada servicio habilitado como *siempre* / *bajo demanda* (socket, D-Bus, `udev` con `SYSTEMD_WANTS`, `StopWhenUnneeded=yes`) / *nunca*; pasar a bajo demanda los de hardware que no se usa todo el tiempo (impresión, Bluetooth, módem, escáner, avahi...)
- [ ] Cada cambio uno por uno, midiendo antes y después

**Verificación:** `systemd-analyze` antes/después en `BASELINE.md`; se revierte todo cambio que no mejore; ningún servicio necesario deja de funcionar (WiFi, Bluetooth, audio, impresión).

## F3 — Imagen inmutable con ostree (el núcleo del proyecto)
Se hace con el **Plasma actual**, sin shell nuevo.

| Sub-fase | Qué | Prueba |
|---|---|---|
| F3a ✅ | rootfs → `ostree commit` → arranque en VM desde un despliegue (initramfs + GRUB; `/usr` solo lectura, `/etc`, `/var`, `/home` persistentes) | La VM arranca y `/usr` rechaza escrituras (`touch /usr/x` falla) |
| F3b ✅ | Ciclo de actualización: publicar commit 2 → `pull` → reiniciar → sistema nuevo | `ostree admin status` muestra el nuevo; los datos de `/home` intactos |
| F3c ✅ | Rollback manual y **automático**: commit roto a propósito → la comprobación de salud falla → vuelve al anterior | La VM termina en la versión buena sin intervención |
| F3d | **Corte de energía**: matar la VM (QEMU `quit`/kill) en medio de `pull` y de `deploy`, repetido cientos de veces | Siempre arranca en un despliegue válido, 0 corrupciones |
| F3e | Nvidia: módulo compilado y firmado **al construir la imagen**, junto al kernel | En el Dell G3: Wayland/X11 con la GPU activa; no existe desajuste kernel/driver |
| F3f | Secure Boot | Arranca con SB activo con la clave de OweeLinux (o aviso claro) |
| F3g | Herramienta `owee` (`update`, `rollback`, `status`, `--json`) | Cubre F3b-F3c desde un solo comando |

**Puerta de salida de F3:** F3c y F3d pasan en CI y F3e pasa en hardware real.
Si F3d falla (hay corrupción), se detiene todo hasta resolverlo.

## F4 — Apps y desarrollo sin tocar el sistema
- [ ] Flatpak preconfigurado (GIMP, Inkscape, oweecode, LibreOffice u otros del manifiesto)
- [ ] `distrobox`/Podman listos (subuid/subgid, reglas udev para adb)
- [ ] **Quadlet**: servicios como contenedores Podman rootless gestionados por systemd (`~/.config/containers/systemd/*.container`; los predeterminados de la imagen en `/usr/share/containers/systemd/`)
- [ ] `owee dev new <proyecto>`; Python con `uv`/`venv`
- [ ] Banco `owee bench`: tiempo hasta la primera ventana (frío y caliente)
- [ ] **Matriz de lenguajes** (ver `docs/INTERFAZ.md`): Python, Rust, Go, JS/TS/Vue, PHP, Ada, Dart/Flutter y C/C++ — un "hola mundo" por cada uno que compile, ejecute y (si es gráfico) abra una ventana, sin modificar la imagen

**Verificación:**
- Instalar y desinstalar 10 apps deja `ostree admin diff` **vacío**.
- `pip install`, `npm i -g`, `cargo install` dentro de una caja no cambian el host.
- Un servicio Quadlet de prueba arranca solo tras reiniciar, se reinicia si se mata el proceso, y **sobrevive a una actualización y a un rollback** del sistema (sus datos viven en `/var`/`$HOME`, fuera de la imagen).
- `owee bench` de GIMP, Inkscape y oweecode queda registrado y se compara contra `BASELINE.md`; las optimizaciones (cachés de fuentes/iconos generadas al construir, runtimes compartidos) se aceptan solo si mejoran la medición.

## F5 — Instalador y actualizaciones para usuarios
- [ ] Calamares despliega la imagen ostree (particiones: ESP, `/boot`, raíz, `/var`, `/home`)
- [ ] Actualización desde la interfaz, con aviso de reinicio y botón de volver atrás
- [ ] Espejo en red local / USB para laboratorios (sin internet)

**Verificación:** instalación completa en VM **y** en hardware real; actualizar desde un espejo local con la red externa cortada; un usuario no técnico completa instalación + actualización sin terminal.

## F6 — Shell "OweeLinux Lite" (labwc + Python/GTK4)
> Cambio (2026-10-11): **Quickshell no está en Debian 13**; habría que compilarlo y mantenerlo en la imagen. Todo lo de la ruta Python sí está empaquetado: `python3-gi` 3.50, GTK 4.18, libadwaita 1.7, `gtk4-layer-shell` 1.0.4 (con typelib para Python), `labwc` 0.8.3, `waybar` 0.12, `fuzzel`, `mako`, `gjs` 1.82. Medido aquí: una ventana mínima con reloj en Python+GTK3 = 44 MB Rss / 26 MB Pss; un panel real con bandeja, red, batería y popovers **no está medido**. Decisión por datos: prototipar el panel en Python/GTK4 y compararlo con Waybar con las mismas funciones.

> **Decisión (2026-10-11): la plataforma del shell y de las apps de usuario es GTK4 + libadwaita + `gtk4-layer-shell`, con Python (PyGObject) como lenguaje principal y GJS (JavaScript) como alternativa sobre las mismas librerías.** Un solo conjunto de herramientas para el shell y para las apps que creen los usuarios; no se mantiene un segundo toolkit (Quickshell/Qt) en paralelo. Se reabre solo si Quickshell llega a Debian y el diseño exige animaciones que GTK4 no pueda dar.
> Riesgos a probar pronto: (1) el render GTK4 en la Nvidia Pascal del Dell G3 (si falla, `GSK_RENDERER=cairo`); (2) la coherencia visual con las apps de KDE (colores/fuentes comunes en GTK y Qt); (3) RSS/Pss reales del panel con todas sus funciones.
- [ ] **Puerta de entrada (go/no-go):** labwc funciona con la Nvidia Pascal del Dell G3. Si no, se evalúa alternativa antes de escribir nada
- [ ] Panel, lanzador, ajustes rápidos, notificaciones, bloqueo, panel de estado del sistema
- [ ] Segunda sesión en SDDM; Plasma sigue disponible

**Verificación:** RAM en reposo y *login → escritorio* medidos contra Plasma (misma máquina, 5 repeticiones); sesión de 8 horas sin cierres; multimonitor y HiDPI; si el shell falla, el usuario vuelve a Plasma desde el login.

## F7 — Apps propias
- [ ] **`owee-capture`**: captura y grabación (región, anotaciones, anclar a pantalla, audio, cámara, OCR, GIF) sobre protocolos estándar de Wayland/PipeWire
- [ ] Formato `owee-app` (manifest + permisos vía portales de Flatpak) y plantilla "hola mundo" en JS/QML
- [ ] Ajustes del sistema propios (los imprescindibles)

**Verificación:** lista de aceptación por app; "hola mundo" en menos de 20 líneas, instalable en un click; una app que pide un permiso que no declaró **falla** (prueba negativa).

## F8 — Pulido y versión 1
- [ ] Prueba de CI de telemetría (la imagen no contacta dominios de seguimiento)
- [ ] Firewall que bloquea lo entrante por defecto; revisión de seguridad
- [ ] Matriz de hardware probado; guía de instalación; videos
- [ ] Beta cerrada con estudiantes / un laboratorio real

**Verificación:** beta de al menos 2 semanas sin pérdida de datos ni sistema irrecuperable; informe de incidencias.

---

## F9 — Eficiencia de memoria: `owee-nap` (idea, después de F6)
Poner a "dormir" las apps de fondo que no se usan para liberar RAM y CPU:
- Una app va a dormir tras N minutos sin foco **solo si** no reproduce audio (PipeWire), no tiene inhibidores activos (descarga, grabación, videollamada) y su uso de CPU es bajo.
- Mecanismo: congelar su unidad de systemd (cgroup v2 `cgroup.freeze`; las apps de Flatpak ya corren en una *scope* propia) y pedir al kernel que mande sus páginas frías a zram (`memory.reclaim`).
- Al recuperar el foco, se descongela de inmediato.
- Requiere cooperación del shell: marcar la ventana como dormida (para que el compositor no la dé por colgada) y excepciones configurables.

**Verificación:** con 10 apps abiertas y 2 en uso, RAM usada antes/después; tiempo de *despertar* medido (ms); pruebas negativas: una app con música, una descarga y un `cargo build` **no** se congelan; cero pérdida de datos tras 100 ciclos dormir/despertar.

## F-R — Resiliencia de la sesión: un proceso no puede colgar el escritorio
Motivación (caso real, 2026-10-12): en otra máquina con Deepin, una compilación de Java/Android dejó el
sistema inservible más de 10 minutos (pantalla de bloqueo sin respuesta). Causa probable —**sin
confirmar**— : agotamiento de memoria con *thrashing* (RAM y swap saturadas), aunque también puede ser
E/S de disco saturada o CPU. El objetivo no es "nunca se cuelga" (hay fallos de hardware o del
kernel), sino que **un proceso de usuario desbocado no pueda dejar el escritorio sin respuesta**.

**Evidencia del registro (journal del arranque anterior, aportado por el autor):**
- **Corrección (2026-10-12):** `journalctl` avisaba *"You are currently not seeing messages from other users and the system"*: el usuario no está en los grupos `adm`/`systemd-journal`, así que **los mensajes del kernel y de NetworkManager no eran visibles**. "Sin entradas" en esas consultas **no significa que no pasara nada**; hay que repetirlas con `sudo`. Lo que sigue en pie: **el sistema NO estaba totalmente colgado** (los eventos de sesión y de `sudo` sí eran visibles): se pudo cambiar a una consola de texto (`dde-lock`: *session left/resumed* a las 21:59-22:00) y usar `sudo` (22:00:50, verificación correcta en 4 s). El reinicio terminó limpio (MariaDB, nginx y contenedores se apagaron bien).
- Lo atascado fue la **pantalla de bloqueo / sesión gráfica** (`dde-lock`), que no aceptaba la contraseña. Causa exacta: **desconocida** (el bloqueo mostró a las 21:45:08 actualizaciones de los iconos de red y un aviso de dispositivo WiFi no encontrado; puede ser coincidencia).
- **Ventana 21:40-21:59 (segundo registro):** a las **21:45:08** (la hora en que el autor vio el cuelgue) el servicio de red de la sesión (`/org/deepin/dde/Network1`) **desapareció**: decenas de errores "can not find hook object" en el mismo segundo, y el bloqueo (`dde-lock`) se quejó de no encontrar el dispositivo WiFi. A las 21:52:51-52 el plan de energía intentó apagar la pantalla por inactividad y falló ("Set wm blackscreen failed"). Nada de kernel (ni OOM ni GPU). **Hipótesis (sin confirmar):** el bloqueo se quedó esperando una llamada D-Bus **síncrona** a un servicio que ya no respondía y su interfaz se congeló; el origen del corte de red (¿el WiFi se reinició con la descarga de la compilación?) está por determinar.
- Conclusión provisional: además de limitar a los procesos desbocados, la sesión necesita un **bloqueo de pantalla sencillo y robusto** y una **vía de recuperación sin reiniciar** (consola de texto + `loginctl unlock-sessions`).

Ideas, de menos a más esfuerzo (todas por medir antes de adoptarlas):
- **Matar pronto al culpable** en vez de esperar al OOM del kernel: `earlyoom` o `systemd-oomd` (PSI).
- **Proteger la sesión**: el compositor, el shell y el bloqueo de pantalla con `OOMScoreAdjust` muy bajo y `MemoryLow`; las compilaciones en su propia *slice*.
- **Compilar acotado**: `owee dev build` (o la caja de desarrollo) ejecuta con `systemd-run --user --scope` con `MemoryMax`/`MemoryHigh`, `CPUWeight` y `IOWeight` bajos.
- **zram** (ya previsto) y ajustes del kernel contra el thrashing (p. ej. `lru_gen min_ttl_ms` de MGLRU; *verificar que el kernel 6.12 de Debian lo trae*).
- **Salida de emergencia siempre disponible**: una consola de texto (Ctrl+Alt+F3), SSH opcional y Magic SysRq habilitado de forma útil (sincronizar, remontar solo lectura, reiniciar) con una guía de una página. Receta para una pantalla de bloqueo que no responde: desde la consola, `loginctl unlock-sessions` *(verificar que el bloqueo elegido lo respeta)*; un comando `owee` que lo haga.
- **Bloqueo de pantalla simple**: usar el protocolo estándar `ext-session-lock` con un bloqueador pequeño y probado (p. ej. `swaylock` o `gtklock`) y autenticación PAM sin servicios intermedios; probar qué pasa si el bloqueador muere *(se espera que la sesión siga bloqueada y se recupere relanzándolo desde una consola; verificar)*.
- **Diagnóstico al alcance del usuario**: el primer usuario se crea dentro de `systemd-journal` (y `adm`) para poder leer los registros del sistema **sin `sudo`**, y un comando `owee doctor` resume el último arranque (OOM, tareas bloqueadas, reinicios del GPU/WiFi, unidades caídas, apagado sucio, reinicios por watchdog) en una línea de tiempo. Hoy esto se hace a mano y se puede pasar por alto, como ocurrió aquí.
- **Que reiniciar no destruya trabajo**: autoguardado y "historial local" en oweecode; instantáneas periódicas de las carpetas de proyecto (sin depender de que el usuario haga *commit*).

**Regla de diseño que sale de este caso:** ningún componente de la interfaz puede bloquearse esperando a otro servicio. Las llamadas D-Bus del shell y del bloqueo son **asíncronas y con tiempo límite**; el bloqueo de pantalla **no depende** de red, audio ni energía (solo del compositor y de PAM).
**Prueba de inyección de fallos:** con la pantalla bloqueada, matar/reiniciar los servicios de red, audio y energía (y cortar la red) y comprobar que la contraseña se acepta y la sesión se desbloquea en menos de 2 s.

**Resultados de las primeras mediciones: `docs/RESILIENCIA.md`** (no reproducen el cuelgue del autor; `earlyoom` y los límites de cgroup evitan la degradación por presión gradual de memoria; el bloqueo de KDE aguanta la caída de red/energía/audio).

**Verificación (en la VM, repetible):** con un proceso que consume más memoria de la disponible (y otro que
satura CPU y otro disco), medir la latencia de respuesta del shell y de una consola; criterios a fijar con
mediciones, p. ej. *el escritorio responde en < 2 s y el proceso desbocado es limitado o terminado en < 30 s,
sin reiniciar*. Comparar con la imagen sin protecciones para tener la línea base del problema.

## Tipos de verificación usados
1. **Automática (CI):** build, arranque en QEMU, ciclo de actualización, rollback, cortes de energía.
2. **Manual en hardware real:** checklist por equipo (WiFi, batería, Bluetooth, HDMI, audio, Nvidia, suspensión).
3. **Métricas:** `systemd-analyze`, RAM en reposo y `owee bench`, siempre con el valor anterior al lado.

## Lo que se deja fuera hasta después
Kernel propio (oweeOS), compatibilidad con `.deb`/Windows, tienda de apps propia, navegador propio.
