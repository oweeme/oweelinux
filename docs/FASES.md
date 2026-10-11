# OweeLinux 2 — Fases de trabajo y verificación

Estado: **plan propuesto** (aún sin aprobar fase por fase).
Decisiones base: Debian 13 · imagen inmutable con **ostree** · apps por Flatpak ·
herramientas de desarrollo en cajas (Podman/distrobox) · shell propio (labwc + Quickshell)
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
| **2** | **F3d corte de energía** (incl. F3c-bis: initramfs roto y *watchdog*) | Es la puerta de F3: sin ella no se puede confiar en la base | |
| **3** | **F3h imagen real**: Debian + Plasma + red + audio sobre ostree, que arranca hasta el login gráfico en QEMU | Hoy solo hay un Debian mínimo sin pantalla. Esto es lo que lo hace *funcional* | **M1: sistema funcional (VM)** |
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

## F6 — Shell "OweeLinux Lite" (labwc + Quickshell)
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

## Tipos de verificación usados
1. **Automática (CI):** build, arranque en QEMU, ciclo de actualización, rollback, cortes de energía.
2. **Manual en hardware real:** checklist por equipo (WiFi, batería, Bluetooth, HDMI, audio, Nvidia, suspensión).
3. **Métricas:** `systemd-analyze`, RAM en reposo y `owee bench`, siempre con el valor anterior al lado.

## Lo que se deja fuera hasta después
Kernel propio (oweeOS), compatibilidad con `.deb`/Windows, tienda de apps propia, navegador propio.
