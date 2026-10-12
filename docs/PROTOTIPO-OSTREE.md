# Prototipo ostree (F3a–F3d) e imagen real con Plasma (F3h) — resultado

Fecha: 2026-10-11. **Estado: F3a, F3b, F3c y F3d superadas.** Un Debian 13 mínimo arranca desde un
despliegue ostree en QEMU/KVM con UEFI, con `/usr` de solo lectura.

## Qué se probó (`tools/ostree-proto/boot-test.sh`, 4/4 pasa)
- UEFI (OVMF) → GRUB → kernel 6.12.107 → initramfs (dracut + `ostree-prepare-root`) → systemd.
- `/usr` montado `ro`; `touch /usr/x` falla ("Read-only file system").
- `/var` escribible; `/home` es enlace a `var/home`.
- `ostree admin status` muestra el despliegue activo.

## Cómo se reproduce (dentro del pod)
```bash
mmdebstrap --mode=root --variant=minbase \
  --include=systemd-sysv,linux-image-amd64,ostree,dbus trixie ROOTFS http://deb.debian.org/debian
# instalar en ROOTFS (chroot): ostree-boot dracut-core kmod
tools/ostree-proto/prepare-rootfs.sh ROOTFS      # estructura ostree, kernel+initramfs en /usr/lib/modules
tools/ostree-proto/build.sh ROOTFS /var/tmp/ostree-proto   # commit + despliegue + disco UEFI
# en el host:
tools/ostree-proto/boot-test.sh disk.img
```

## Hallazgos
1. **Debian 13 sí trae el arranque de ostree** (`ostree-boot`: módulo dracut, `ostree-prepare-root`, units y GRUB). Requiere initramfs hecho con **dracut**, no `initramfs-tools`.
2. **El árbol necesita `/sysroot` y el enlace `/ostree -> sysroot/ostree`.** Sin ellos `ostree-prepare-root` falla con "failed to MS_MOVE '/sysroot'". Ya lo hace `prepare-rootfs.sh`.
3. **El QEMU de Deepin no trae ROMs** (`linuxboot_dma.bin`, `kvmvapic.bin`): no sirve `-kernel` directo. Se usa OVMF + GRUB, que además es el camino real.
4. **ESP FAT32 pequeña:** con pocos clusters OVMF no la reconoce; se fuerza `-s 1` (clusters de 512 B).
5. **El rootfs tardó ~2,5 horas por la red**, no por CPU. Hace falta una caché de paquetes (apt-cacher-ng o volumen) antes de F1.
6. Todo se crea **sin montar nada ni privilegios** (`mke2fs -d`, `mcopy`, `sfdisk`), así que cabe en el pod rootless y en CI.

## Limitaciones conocidas del prototipo (no es la imagen final)
- Sin entorno gráfico, sin Nvidia, sin Secure Boot, sin Calamares.
- `grub.cfg` escrito a mano a partir de la entrada BLS (la integración real de GRUB con ostree está por hacer).
- `/root` no existe (falta el `tmpfiles` de `var/roothome`); login automático en consola serie solo para pruebas.
- El `/var` del commit se vació y la base de dpkg se guardó en `/usr/share/owee/dpkg-db`; falta definir cómo se construye la imagen real.
- `--no-xattrs` en el commit (por el contenedor rootless): hay que revisar si afecta a capabilities y SELinux/AppArmor.

## F3b — ciclo de actualización por red (`tools/ostree-proto/update-test.sh`, 4/4 pasa)
Flujo: `publish.sh` crea un repo ostree "archive" servible por HTTP → el sistema (release 1)
ejecuta `owee-update` → descarga la release 2 desde `http://10.0.2.2:8000/pub` (el host,
vía red de QEMU) → reinicia → arranca en la release 2 y conserva la 1.
- `ostree admin status` tras reiniciar: release 2 activa (`*`), release 1 marcada `(rollback)`.
- Publicar la release 2 (cambia un solo archivo) importó solo **5 objetos de metadatos y 1 de contenido**: ostree deduplica por contenido, así que actualizar poco cuesta poco.

### Hallazgos de F3b
1. **El menú de arranque no puede ser fijo.** ostree alterna `boot.0` / `boot.1` en cada cambio de despliegues; un `grub.cfg` escrito a mano dejó el sistema en el modo de emergencia tras reiniciar ("Couldn't find specified OSTree root"). Solución del prototipo: `owee-bootcfg` regenera `/boot/owee/grub.cfg` desde las entradas BLS y `owee-update` lo ejecuta tras cada `upgrade`. La integración definitiva (hook de ostree/GRUB, o systemd-boot) queda por decidir.
2. **El remoto de actualizaciones se define una sola vez** (en `/etc/ostree/remotes.d/`, dentro de la imagen). Definirlo también en el repo del sysroot da "Multiple specifications found for remote".
3. **`ostree pull-local` no admite `rama@commit`**: para instalar una versión concreta se trae el commit y se crea la ref a mano (`build.sh DIR COMMIT`).
4. **Seguridad:** el prototipo no firma commits (`gpg-verify=false`) y usa HTTP. **Antes de cualquier uso real hace falta firma y HTTPS.**
5. **Nota de método:** un fallo de la primera prueba (parecía error de actualización) era del montaje (el disco ya estaba en la release 2). Las pruebas deben fijar la versión de partida.

## F3c — rollback manual y automático (`tools/ostree-proto/rollback-test.sh`, 12/12 pasa)
Una sola sesión de QEMU con 5 arranques:
1. Release 1 (confirmada) → se crea `/home/dato.txt` → `owee-update` a la 2 (queda "a prueba").
2. Release 2: `owee-health` comprueba que systemd llega a `running` y la **confirma sola**.
3. `owee-rollback` (manual) → vuelve a la 1. `/home/dato.txt` intacto.
4. `owee-update` a la release 3, que lleva un servicio roto a propósito → arranca a prueba.
5. La 3 arranca, `owee-health` ve el sistema `degraded`, la **rechaza y reinicia**; GRUB vuelve a la 1 sola. `/home/dato.txt` intacto; el registro `/var/lib/owee/health.log` guarda 1 rechazo. 4 reinicios en total: sin bucle.

**Mecanismo:** la versión nueva tiene UN intento (`trial=1`, que GRUB borra con `save_env` al elegirla). Solo se "confirma" (`confirmed=ID`) si la comprobación de salud pasa. Sin confirmación, el siguiente arranque va a la última versión confirmada. `rd.emergency=reboot panic=5` evita quedarse colgado si el fallo ocurre en el initramfs/kernel.

### Hallazgos de F3c (los dos fallaron antes de pasar)
1. **El id de versión debe ser único por despliegue.** `<bootcsum>-<n>` (de la ruta `ostree=`) es igual para todas las versiones que comparten kernel, así que "en uso" y "confirmada" siempre coincidían y el rollback nunca actuaba. Se usa `<commit>.<serie>` resuelto con `owee-id`.
2. **GRUB interpreta un `default` que empieza por dígitos como NÚMERO de entrada.** Un id `5be8…` se leía como "entrada 5", no existía y GRUB caía en la entrada 0 (la versión rota) → bucle de reinicios. Los ids de GRUB llevan el prefijo `owee-`. Este fallo estuvo oculto mientras la versión confirmada coincidía con la entrada 0.
3. Tras un `upgrade`, ostree renombra `boot.0`/`boot.1`: la ruta `ostree=` del kernel en marcha deja de existir. `owee-id` pregunta entonces a `ostree admin status`.
4. `save_env` de GRUB sobre ext4 en UEFI **sí funciona** (comprobado aparte: `trial` pasa de 1 a 0 entre arranques).

### Qué NO cubre todavía
- Solo se probó la rotura por **servicio fallido** (`degraded`). La rotura de **initramfs/kernel** (`publish.sh ... initrd`) está implementada pero **no se ha probado**.
- La comprobación de salud solo mira `systemctl is-system-running`; falta una lista de servicios críticos (red, gráficos, etc.).
- Un sistema colgado sin reiniciar (p. ej. pantalla negra con systemd arriba) no lo detectaría; haría falta un temporizador *watchdog*.
- Un mismo despliegue confirmado y luego desplegado otra vez conserva el mismo `<commit>.<serie>`; hay que revisar qué pasa si se reutiliza una serie.

## F3d — corte de energía (`tools/ostree-proto/powerloss-test.py`, 40 iteraciones válidas sin fallos)
Un único disco persistente; en cada iteración la VM arranca (eso comprueba el corte anterior) y se
vuelve a cortar con SIGKILL en un momento aleatorio:
- **Corrección (2026-10-12):** esta tanda pidió 60 iteraciones pero solo existían 40 versiones `step`; desde la 41 `owee-update` fallaba al instante y esas iteraciones **no probaban nada** (el script no lo detectaba). Cifras válidas, iteraciones 1-40: 19 cortes en mitad de `owee-update`, 8 justo tras terminar, 5 con actualización completa y 8 en mitad del **propio arranque**. El script ahora aborta si faltan versiones y falla si `owee-update` devuelve error.
- Tras cada corte: arrancó en un despliegue válido, `/usr` de solo lectura, ≥1 despliegue; una versión nueva sana se confirmó sola.
- `ostree fsck` del repo cada 5 iteraciones: sin errores. `e2fsck -fn` final tras apagado limpio: rc=0, 0 problemas.
- Una versión nueva que no llega a confirmarse antes del corte se descarta y el sistema vuelve a la última confirmada (diseño de F3c).

### Hallazgos de F3d
1. **La primera tanda "falló" por un defecto de mi generador de versiones, no del sistema:** `--tree=dir=` copia los permisos de las carpetas del overlay y `mktemp -d` crea la raíz con 0700 → `/` quedó 0700 en el commit y los servicios no podían recorrerla; todas esas versiones arrancaron `degraded`. **`owee-health` las rechazó siempre y el sistema volvió a la versión buena**: validación inesperada del rollback automático. Lección: tras `commit --tree=dir`, comprobar `ostree ls ... /` (debe ser `d00755`).
2. El script debe esperar a que una versión sana se confirme antes de ejecutar comandos pesados, o el reinicio de un rechazo confunde la prueba.
3. Los sockets de la consola serie deben ir con ruta relativa (límite de ~108 caracteres).

### Limitaciones de la prueba de corte
- `kill -9` de QEMU conserva todo lo que el invitado ya escribió: prueba consistencia ante cortes en cualquier punto, **no** la pérdida de la caché volátil del disco ni el reordenamiento de escrituras de un disco real. Habría que complementarla con hardware real (cortar la corriente de verdad) o con un dispositivo de bloques que descarte escrituras sin vaciar.
- La actualización de prueba cambia un solo archivo (rápida): una actualización grande tiene más ventana de riesgo.
- Falta el caso de rotura de initramfs/kernel y el *watchdog* (F3c-bis).

## F3h — imagen real: Debian 13 + Plasma sobre ostree (`tools/ostree-proto/gui-boot-test.py`)
**Resultado: arranca hasta el escritorio de Plasma en QEMU** (captura: `docs/img/f3h-plasma-ostree.png`).
- Rootfs de **1.092 paquetes / 2,5 GB** (`packages-plasma.txt`, `build-rootfs-plasma.sh`); commit ostree de 2,4 GB; disco UEFI de 5,6 GB.
- En la VM (KVM, 2 CPU, 3 GB, gráficos por software): consola serie a los 18 s, **SDDM a los 19 s, `plasmashell` a los 24 s**, `systemctl --failed` vacío, `/usr` de solo lectura, versión confirmada. Son tiempos de una VM, **no comparables con hardware real**.
- Es Plasma "de fábrica": **sin el branding de OweeLinux** (fondos, esquema de color, SDDM, GRUB), que aún vive solo en `livebuild-profile/`.

### Hallazgos de F3h
1. **La red decide el calendario:** descargar los 838 paquetes del escritorio a ~40-60 KB/s lleva horas. Una caché `apt-cacher-ng` en el pod (volumen persistente) convirtió la reconstrucción en 10 minutos. Un corte de red tumbó el primer intento: `Acquire::Retries` alto.
2. **`/var` vacío rompe servicios:** los paquetes dejan directorios en `/var` (p. ej. `/var/lib/sddm`). Se guarda una copia de fábrica en `/usr/share/factory/var` y `systemd-tmpfiles` la restaura (`owee-factory.conf`). Limitación: solo copia si el directorio no existe; un paquete nuevo que añada subdirectorios en una actualización necesitará reglas más finas.
3. **`/home` es un enlace a `var/home`** que no existe en la imagen: `useradd -m` falla en el montaje; el directorio personal se crea al arrancar con `tmpfiles`.
4. Los scripts de preparación deben ser **reintentables** (`prepare-rootfs.sh` ya lo es: no rehace el initramfs ni vuelve a mover `/etc`).
5. El usuario `oweeuser` **sin contraseña** con inicio automático de SDDM (`overlay-test-user.sh`) es **solo para pruebas en VM**, y solo se aplica con `OWEE_TEST_USER=1`.

### Actualizar, rollback y corte de energía sobre la imagen Plasma (2026-10-12)
Actualizaciones realistas: cada release añade ~3.000 archivos pequeños + 15 de 10 MB (~150 MB); las
versiones de la prueba de cortes, ~400 archivos + 12 MB. VM de 3 GB / 2 CPU.
- **`rollback-test.sh`: 12/12.** Release 2 (buena) arranca a prueba y se confirma sola; rollback manual vuelve a la 1 con `/home` intacto; la release 3 (servicio roto) arranca, `owee-health` la rechaza y el sistema vuelve solo a la 1 (1 rechazo, sin bucle).
- **`powerloss-test.py`, dos tandas válidas de 40 iteraciones (semillas 20261012 y 777), 0 fallos:**
  - Tanda 1 (iteraciones 1-40): 31 cortes en mitad de `owee-update`, 5 con la actualización completa, 4 en mitad del arranque.
  - Tanda 2: 30 cortes en mitad de `owee-update`, 8 actualizaciones completas (todas `rc=0`), 2 en mitad del arranque.
  - **Total: 61 cortes a mitad de una actualización, 13 actualizaciones completas, 6 cortes en el arranque.** Tras cada corte arrancó en un despliegue válido con `/usr` de solo lectura; las versiones nuevas sanas se confirmaron solas (`ostree fsck` cada 5 iteraciones sin errores; `e2fsck -fn` final de ambas tandas con rc=0).
- La tanda 1 se pidió con 60 iteraciones y solo había 40 versiones: de la 41 a la 60 no se probó nada (ver corrección arriba); **solo cuentan las iteraciones 1-40**.
- Límites que siguen: `kill -9` de QEMU no simula la pérdida de la caché del disco; las actualizaciones de prueba (≤150 MB) son menores que las reales (cientos de MB o más); solo sesión X11 y gráficos por software.

### F3c-bis — fallos tempranos de arranque (`earlyfail-test.py`, 3/3 sobre la imagen Plasma)
Desde la release 1 confirmada, se actualiza a una versión defectuosa y el sistema debe volver **solo**, sin bucle:
| Escenario | Qué falla | Mecanismo de rescate | Tiempo | Menús GRUB |
|---|---|---|---|---|
| `initrd` | initramfs corrupto | el kernel no monta la raíz → *panic* → reinicio (`panic=5`) | 45 s | 2 |
| `neverready` | un servicio bloquea el arranque para siempre | `owee-health` espera 90 s, rechaza y reinicia | 140 s | 2 |
| `hang` | el sistema se cuelga del todo (CPUs acaparadas con prioridad de tiempo real) | *watchdog* de systemd (`RuntimeWatchdogSec=30s`; en la VM, dispositivo `i6300esb`) | 88 s | 2 |
Cada uno con evidencia de que la versión rota llegó a intentar arrancar (mensaje del kernel o marca que escribe en `/var`).

**Tres defectos reales encontrados y corregidos:**
1. **`owee-health.service` arrancaba tras `multi-user.target`**, que espera a todo lo que enlaza (incluido un servicio que nunca termina): con una versión bloqueante la comprobación **nunca llegaba a ejecutarse**. Ahora arranca desde `basic.target` y sin dependencias por defecto.
2. **Confirmación demasiado temprana.** Una versión que llega a `running` y se cuelga un instante después se confirmaba antes de colgarse; quedaba como "la buena" y el watchdog solo producía un **bucle de reinicios** (8 en 5 minutos). `owee-health` confirma ahora en dos fases: `running` **y** aguantar `OWEE_HEALTH_STABLE` segundos (60 por defecto; 20 en las pruebas) sin degradarse.
3. **El script de prueba** tomaba el prompt que el shell reimprime *antes* de reiniciarse como si fuera el arranque nuevo (los comandos acababan escritos en el menú de GRUB). Hay que esperar el menú de GRUB y recién después un prompt nuevo.

Efecto a explicar al usuario: si reinicia a mano dentro de esa ventana de estabilidad tras una actualización, la versión nueva aún no está confirmada y el sistema vuelve a la anterior (seguro, pero puede confundir).

**Regresión tras el cambio de salud:** `rollback-test.sh` **12/12** otra vez (releases buena y rota nuevas, con ~150 MB y la nueva comprobación). La regresión de cortes de energía con versiones nuevas queda **en curso** (ver "Pendiente").

**Experimentos que descartaron causas** (conviene recordarlos): el driver `i6300esb` ya está en el initramfs y carga a ~2 s; systemd arma el watchdog a ~3,4 s con la configuración en `/etc`; armado a mano y con la CPU acaparada, la VM se reinicia a los ~55 s. Con `sched_rt_runtime_us` por defecto (95 %) la CPU **no** se acapara del todo y el watchdog no actúa: el escenario `hang` lo desactiva (`-1`).

**Límites que siguen:** el watchdog solo protege **después** de que systemd arranque; un cuelgue en el initramfs, antes de eso, no está cubierto (solo los fallos que acaban en *panic* o en el modo de emergencia con `rd.emergency=reboot`). Un sistema que se cuelga **después de confirmarse** reinicia en bucle la versión confirmada (inevitable con esta política). En hardware real hay que usar el driver de watchdog de la placa (`iTCO_wdt`, `sp5100_tco`...), no `i6300esb`.

### Qué NO está verificado todavía en la imagen real
- Nvidia, Secure Boot, red real (WiFi), audio, Bluetooth, suspensión y gráficos con GPU: no se pueden probar en la VM.
- Sesión Wayland (solo se arrancó X11); instalación en disco real; tamaño de las actualizaciones reales (el prototipo cambiaba un archivo).

## Pendiente
- Regresión de cortes de energía con las versiones nuevas (comprobación en dos fases): en curso.
- Repetir actualización, rollback y corte de energía sobre la imagen Plasma.
- Aplicar el branding de OweeLinux a la imagen.
