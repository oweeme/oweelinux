# Manual de modificaciones de OweeLinux

Este documento es la referencia técnica para tocar cualquier parte del
proyecto: estructura de archivos, cómo se construye el ISO, dónde agregar o
sacar cosas, y — la parte más importante — los bugs reales que nos encontramos
armando esto y por qué el fix es como es. Si estás por tocar algo y te suena a
"esto ya lo debe haber roto antes", buscá en la sección
[Lecciones aprendidas](#lecciones-aprendidas-bugs-reales-y-su-causa-raíz) antes
de reinventar la rueda.

## Índice

- [Estructura del proyecto](#estructura-del-proyecto)
- [Cómo se construye el ISO](#cómo-se-construye-el-iso)
- [Cómo probar](#cómo-probar)
- [Agregar o sacar paquetes](#agregar-o-sacar-paquetes)
- [Sistema de includes: `before_packages` vs `after_packages`](#sistema-de-includes-before_packages-vs-after_packages)
- [Hooks](#hooks)
- [Branding](#branding)
- [Instalador gráfico (Calamares)](#instalador-gráfico-calamares)
- [Repo APT propio](#repo-apt-propio)
- [Apps opcionales post-instalación](#apps-opcionales-post-instalación)
- [Lecciones aprendidas (bugs reales y su causa raíz)](#lecciones-aprendidas-bugs-reales-y-su-causa-raíz)
- [Estado y fases](#estado-y-fases)

## Estructura del proyecto

```
oweelinux/
├── docs/
│   ├── PLAN_OWEELINUX.md        # plan de arquitectura original (puede estar desactualizado
│   │                              en detalles menores frente a este manual)
│   ├── MANUAL_MODIFICACIONES.md # este archivo
│   ├── wallpaper/               # fotos de koi originales (fuente de los wallpapers)
│   └── oweeme-koi.png           # logo original
├── packaging/
│   ├── apt-repo/                # repo APT propio (reprepro) — fuente de verdad
│   ├── oweeide-build-output/    # .deb de oweeide ya construido
│   └── wps-office/              # (vacío, el .deb real vive fuera de git, ver .gitignore)
└── livebuild-profile/           # perfil de live-build, esto es "el ISO" en forma de config
    └── config/
        ├── package-lists/oweelinux.list.chroot   # lista de paquetes a instalar
        ├── apt/apt.conf                          # fuerza IPv4 (ver Lecciones aprendidas)
        ├── includes.chroot_before_packages/      # archivos que se copian ANTES de instalar paquetes
        ├── includes.chroot_after_packages/       # archivos que se copian DESPUÉS
        └── hooks/
            ├── live/    # hooks que corren SOLO en el medio live
            └── normal/  # hooks que corren en live Y en el sistema instalado
```

`livebuild-profile/chroot/`, `cache/`, `.build/`, `*.iso` y `*.qcow2` son
artefactos de build — se regeneran solos, no van a git (ver `.gitignore`).

## Cómo se construye el ISO

El build corre dentro de un contenedor Podman **privilegiado** (hace falta para
que `live-build` pueda hacer `chroot`, montar `/proc`, `/sys`, etc. — no
funciona en modo rootless). El comando completo, tal cual se usó durante todo
el desarrollo:

```sh
sudo rm -rf livebuild-profile/chroot \
            livebuild-profile/cache \
            livebuild-profile/.build \
            livebuild-profile/*.iso

sudo podman run --rm --privileged \
  -v $(pwd)/livebuild-profile:/build:z \
  docker.io/library/debian:trixie bash -c "
    echo 'Acquire::ForceIPv4 \"true\";' > /etc/apt/apt.conf.d/99force-ipv4
    apt-get update -qq &&
    apt-get install -y -qq live-build >/dev/null 2>&1 &&
    cd /build &&
    lb config \
      --distribution trixie \
      --architecture amd64 \
      --archive-areas 'main contrib non-free non-free-firmware' \
      --binary-image iso-hybrid \
      --apt-recommends true \
      --bootappend-live 'boot=live components quiet splash noautologin' \
      --iso-application 'OweeLinux' \
      --iso-publisher 'OweeLinux <https://oweeme.com>' \
      --iso-volume 'OWEELINUX' &&
    lb build
  "

sudo chown $USER:$USER livebuild-profile/*.iso
```

**Regla de oro: siempre limpiar todo antes de reconstruir.** `lb clean
--chroot` deja estado inconsistente (marcadores de etapas completadas
desincronizados del filesystem real) y produce errores crípticos tipo `chroot:
cannot change root directory`. El `rm -rf` manual de arriba es la única forma
confiable.

Flags de `lb config` que importan y por qué:

| Flag | Por qué |
|---|---|
| `--apt-recommends true` | Sin esto, WiFi/HDMI/batería quedan rotos en hardware real (ver Lecciones aprendidas) |
| `--bootappend-live 'boot=live components ... noautologin'` | Reemplaza (no suma) los parámetros por defecto de live-build — si no incluís `boot=live components` explícito, el medio live no arranca. `noautologin` desactiva el autologin propio de `live-config` para que no compita con el nuestro |
| `--archive-areas 'main contrib non-free non-free-firmware'` | Necesario para firmware de WiFi/GPU y, a futuro, el driver Nvidia |

## Cómo probar

**Live + instalación completa en QEMU** (recrea exactamente lo que hace un
usuario real):

```sh
qemu-img create -f qcow2 test-disk.qcow2 25G

qemu-system-x86_64 -m 4096 -enable-kvm -cpu host \
  -cdrom livebuild-profile/live-image-amd64.hybrid.iso \
  -drive file=test-disk.qcow2,format=qcow2,if=virtio \
  -boot d \
  -device virtio-vga-gl \
  -display gtk,gl=on
```

Instalar normalmente desde el ícono del escritorio, cerrar la ventana, y
arrancar de nuevo **sin** `-cdrom` para probar el sistema ya instalado:

```sh
qemu-system-x86_64 -m 4096 -enable-kvm -cpu host \
  -drive file=test-disk.qcow2,format=qcow2,if=virtio \
  -device virtio-vga-gl \
  -display gtk,gl=on
```

Usar siempre `-device virtio-vga-gl -display gtk,gl=on` — la VGA "std" por
defecto de QEMU tiene soporte DRM/KMS demasiado primitivo y puede confundir
diagnósticos (ver Lecciones aprendidas, caso del login congelado).

**Hardware real:** grabar con KDE ISO Image Writer, jamás con `dd` a mano sin
confirmar el dispositivo dos veces (`lsblk -d -o NAME,SIZE,MODEL,TRAN`).

## Agregar o sacar paquetes

Editar `livebuild-profile/config/package-lists/oweelinux.list.chroot` — una
línea por paquete, `#` para comentarios/secciones. No hace falta nada más,
`lb build` los toma solos en el próximo build.

**Ojo con `apt-recommends true`:** un paquete "chico" puede arrastrar cientos
de MB de recomendados. Antes de asumir que algo pesa poco, medí de verdad
(ver [Medir qué pesa el ISO](#medir-qué-pesa-el-iso-de-verdad) abajo) en vez de
adivinar.

### Excluir recomendados específicos sin romper el build

`livebuild-profile/config/includes.chroot_before_packages/etc/apt/preferences.d/oweelinux-trim.pref`
tiene pines de APT (`Pin-Priority: -1`) para bloquear paquetes puntuales que
solo llegan como *Recommends* (fuentes de escrituras antiguas que nadie usa,
herramientas de desarrollo de LLVM sin uso en runtime, el EULA interactivo de
`ttf-mscorefonts-installer`).

**Antes de pinear algo, probar si es seguro:**

```sh
sudo chroot livebuild-profile/chroot apt-get remove --simulate --auto-remove <paquete>
```

Si la simulación no toca nada crítico, es seguro pinear. Si tira error de "no
installation candidate" al pinear, es que otro paquete lo tiene como *Depends*
duro (no *Recommends*) — pinearlo rompe el build entero. Nos pasó con
`firmware-netronome`/`firmware-marvell-prestera`/`firmware-nvidia-tesla-535-gsp`:
parecían basura de firmware de servidor, pero algo los depende en duro, y
tuvimos que revertir el pin.

### Medir qué pesa el ISO de verdad

Con el chroot de un build reciente todavía en disco (se borra recién al
arrancar el *próximo* build):

```sh
sudo chroot livebuild-profile/chroot dpkg-query -Wf '${Installed-Size}\t${Package}\n' | sort -rn | head -50
sudo chroot livebuild-profile/chroot apt-cache rdepends --installed <paquete>
```

## Sistema de includes: `before_packages` vs `after_packages`

- **`includes.chroot_before_packages/`**: se copian ANTES de que `live-build`
  instale los paquetes de la lista. Usar para: fuentes APT propias (si querés
  que un paquete de tu propio repo se pueda instalar vía `package-lists`, el
  repo tiene que estar acá — si lo ponés en `after_packages`, todavía no
  existe cuando `apt` intenta resolver la lista y falla con "Unable to locate
  package"), pines de APT (`preferences.d`).
- **`includes.chroot_after_packages/`**: se copian DESPUÉS. Usar para todo lo
  que tiene que *sobreescribir* algo que un paquete de Debian ya instaló
  (branding, configs de SDDM/GRUB/Calamares) — así el archivo tuyo gana en vez
  de generar un conflicto de dpkg.

## Hooks

`config/hooks/live/*.hook.chroot` corren solo al construir el **medio live**
(ej.: crear el usuario `liveuser`). `config/hooks/normal/*.hook.chroot` corren
tanto en el live como en lo que termina siendo el sistema instalado (el
squashfs es el mismo para los dos).

Numeración: los hooks corren en orden alfabético/numérico. Los `1000-5999`
son de `live-build` mismo (symlinks al paquete), los `8000-8999` son limpieza
de `live-build`, así que cualquier hook propio que instale algo pesado
(Flatpak, un `.deb` de un repo propio) va después, en el rango `9200+`, para
no interferir con esa limpieza.

**Patrón para instalar algo desde el repo APT propio en un hook** (no se puede
meter directo en `package-lists` de forma confiable — ver Lecciones
aprendidas):

```sh
#!/bin/sh
set -e
apt-get update
apt-get install -y <paquete-del-repo-propio>
```

Ejemplo real: `config/hooks/normal/9220-install-oweeide.hook.chroot`.

## Branding

Cada pieza visual de KDE es un subsistema separado, con su propio formato de
config. Todas están verificadas contra archivos reales de KDE/Debian (nunca
inventadas de memoria) para evitar bugs de sintaxis fantasma.

| Pieza | Dónde vive | Formato |
|---|---|---|
| Splash de arranque (Plymouth) | `includes.chroot_after_packages/usr/share/plymouth/themes/oweelinux/` | `.plymouth` + `.script` |
| Login (SDDM) | `includes.chroot_after_packages/usr/share/sddm/themes/breeze/theme.conf.user` | INI, override de Breeze |
| Splash de sesión (KSplash) | `includes.chroot_after_packages/usr/share/plasma/look-and-feel/org.oweelinux.desktop/` | KPackage `Plasma/LookAndFeel`, QML |
| Wallpaper | `includes.chroot_after_packages/usr/share/wallpapers/OweeLinux/` | KPackage estándar, aplicado por script (ver abajo) |
| Esquema de colores | `includes.chroot_after_packages/usr/share/color-schemes/OweeLinux.colors` | INI KConfig, basado en `BreezeDark.colors` real con los valores cambiados |
| GRUB (sistema instalado) | `includes.chroot_after_packages/boot/grub/themes/oweelinux/` + `etc/default/grub` | `theme.txt` propio de GRUB |
| Instalador (Calamares) | ver sección propia abajo | YAML + QML |
| Identidad del sistema (`/etc/os-release`) | `includes.chroot_after_packages/etc/os-release` + `includes.chroot_after_packages/usr/share/icons/hicolor/*/apps/distributor-logo-oweelinux.png` | `os-release` (formato `KEY=value` de systemd) + icon theme hicolor |

**Wallpaper y esquema de colores no se aplican por archivo de config
estático** — se aplican con un script que corre en el primer login
(`etc/xdg/autostart/oweelinux-first-login.desktop` →
`usr/local/bin/oweelinux-first-login`), usando las herramientas CLI de Plasma
(`plasma-apply-wallpaperimage`, `plasma-apply-colorscheme`). Es más robusto
que tratar de escribir a mano el `plasma-org.kde.plasma.desktop-appletsrc` o
`kdeglobals`, que tienen formato frágil y specific a la versión de Plasma.

**`/etc/os-release` es la identidad que leen las herramientas del sistema**
(KDE "Acerca de este sistema"/kinfocenter, `neofetch`, cualquier script que
chequee la distro) — cambiar el tema visual (Plymouth/SDDM/colores) no toca
esto para nada, son subsistemas totalmente separados. Sin overridearlo, el
sistema se identifica como "Debian GNU/Linux 13" aunque todo el branding
visual esté puesto. Campos clave: `ID=oweelinux` (identificador machine-readable),
`ID_LIKE=debian` (mantiene compatibilidad con scripts que chequean por
distros basadas en Debian), `PRETTY_NAME`/`NAME`/`VERSION*` (lo que se
muestra), `LOGO=distributor-logo-oweelinux` (nombre de ícono, **no** un path —
sigue el icon naming spec de freedesktop, resuelto vía `KOSRelease::logo()`
de KCoreAddons). El ícono correspondiente se instala en el tema `hicolor`
(`usr/share/icons/hicolor/<size>x<size>/apps/distributor-logo-oweelinux.png`,
generado a partir del logo koi de 256×256 ya usado en Calamares) — sin el
ícono en el theme, `LOGO` apunta a un nombre que no resuelve a nada y
kinfocenter cae al ícono genérico.

**Paleta de referencia** (usada en todos los subsistemas de arriba):
- Fondo oscuro base: `#102019` (RGB 16,32,25)
- Acento teal: `#2A9D8F` (RGB 42,157,143)
- Acento coral: `#F06548` (RGB 240,101,72)
- Texto claro: `#EFF0F1` (RGB 239,240,241)

Para armar/tocar un `theme.txt` de GRUB o un `.colors` de Plasma nuevos:
**partir siempre de un archivo real** (`chroot/usr/share/color-schemes/*.colors`,
etc.) y solo cambiar los valores, nunca escribir la estructura de memoria.

## Instalador gráfico (Calamares)

Config en `includes.chroot_after_packages/etc/calamares/`:

- `branding/oweelinux/` — `branding.desc` (YAML) + `show.qml` (slideshow,
  **obligatorio**, aunque parezca opcional — sin la clave `slideshow:` el
  instalador crashea con "key not found").
- `settings.conf` — la secuencia de fases. `branding: oweelinux` selecciona
  nuestro branding en vez del de Debian.
- `modules/*.conf` — config de cada módulo individual.

### El bug de seguridad que encontramos (y por qué el orden de `settings.conf` importa)

`unpackfs` copia el squashfs del live **entero** al disco de destino,
incluyendo el usuario `liveuser` y su autologin. Ni `users` ni
`displaymanager` limpian eso solos:
`displaymanager` (`DMsddm`) **solo** lee/escribe `/etc/sddm.conf` — nunca toca
`/etc/sddm.conf.d/*.conf`, que tiene **más prioridad** que ese archivo. Sin
fix, el sistema instalado queda con autologin sin contraseña.

**Fix** (dos módulos agregados a `settings.conf`, en este orden exacto —
después de `localecfg`, antes de `users`/`displaymanager`):

```yaml
- localecfg
- removeuser      # borra el usuario liveuser (config: modules/removeuser.conf)
- shellprocess    # borra /etc/sddm.conf.d/autologin.conf y /etc/sudoers.d/liveuser
                   # (config: modules/shellprocess.conf)
- users
- displaymanager
```

**Verificado con un ciclo completo real:** live → instalar → reiniciar →
login, confirmando que pide contraseña. No confiar en esto sin repetir esa
prueba después de tocar `settings.conf`.

## Repo APT propio

`packaging/apt-repo/` es la fuente de verdad (herramienta: `reprepro`). Se
sincroniza una copia a `livebuild-profile/config/includes.chroot_before_packages/usr/share/oweelinux/apt-repo/`
para que quede embebida *offline* dentro del ISO — el sistema instalado no
necesita internet para `apt install oweeide` ni para futuros `apt upgrade`
sobre esos paquetes.

**Un clon fresco del repo de git NO trae los `.deb` reales — el build falla
en el hook de oweeide hasta que se repueblan.** `packaging/apt-repo/pool/` y
su copia embebida (`.../apt-repo/pool/`) están en `.gitignore` a propósito
(WPS Office pesa 305MB, por encima del límite de 100MB de GitHub) — lo único
que viaja en git son los metadatos de `reprepro` (`dists/*/Packages`,
`Release`), no los binarios. Sin el `pool/`, `lb build` falla así:

```
E: Failed to fetch file:/usr/share/oweelinux/apt-repo/pool/main/o/oweeme-ide/oweeme-ide_1.2.0_amd64.deb  File not found
E: config/hooks/normal/9220-install-oweeide.hook.chroot failed
```

**Fix, si ya tenés OweeLinux instalado en algún equipo** (el sistema
instalado conserva una copia completa en `/usr/share/oweelinux/apt-repo/pool/`,
puesta ahí por Calamares al copiar el squashfs del live):

```sh
cp -r /usr/share/oweelinux/apt-repo/pool/. packaging/apt-repo/pool/
cp -r /usr/share/oweelinux/apt-repo/pool/. \
  livebuild-profile/config/includes.chroot_before_packages/usr/share/oweelinux/apt-repo/pool/
```

Verificar que los hashes coincidan con lo que ya dice `Packages` antes de
confiar en la copia (`sha256sum` contra el campo `SHA256:` de cada paquete)
— si no coinciden, el `.deb` real hay que conseguirlo de otro lado (el build
output original de oweeide, o bajar WPS Office de nuevo) y volver a
agregarlo con `reprepro includedeb` (ver abajo), no solo copiarlo a mano.

**Agregar una app nueva al repo:**

```sh
cd packaging/apt-repo
reprepro includedeb trixie /ruta/al/paquete.deb

# sincronizar la copia embebida en el ISO
rm -rf ../../livebuild-profile/config/includes.chroot_before_packages/usr/share/oweelinux/apt-repo
cp -r . ../../livebuild-profile/config/includes.chroot_before_packages/usr/share/oweelinux/apt-repo
```

Si el `.deb` no tiene `Section`/`Priority` en su control file (pasó con la
primera build de `oweeide`), reprepro lo rechaza — forzarlo con
`reprepro -S <sección> -P <prioridad> includedeb trixie archivo.deb`.

**Para que se instale por defecto** en vez de quedar solo disponible: agregar
un hook (ver [Hooks](#hooks)), no un paquete en `package-lists` (no funciona,
ver Lecciones aprendidas).

**Repo sin firmar** (`Trusted: yes` en `conf/distributions`) — aceptable
mientras el repo solo se use empaquetado dentro del propio ISO. Si algún día
se publica externamente para que la gente lo agregue a mano a su
`sources.list`, ahí sí hace falta firmarlo con una clave GPG real.

## Apps opcionales post-instalación

Patrón usado para todo lo que es "pesado" o "no todos lo necesitan" (driver
Nvidia, y el launcher de apps recomendadas de abajo): un ícono en el
escritorio (`etc/skel/Desktop/*.desktop`, con el mismo `.desktop` también en
`usr/share/applications/`) que llama a un script en `usr/local/bin/`. Ollama y
bases de datos quedan en esta misma categoría a futuro, sin empaquetar
todavía. (Podman pasó a estar preinstalado en el ISO base — es herramienta de
terminal, no tiene sentido como ícono de instalación con un click.)

**Ejemplo real, driver Nvidia** (`oweelinux-install-nvidia` +
`oweelinux-install-nvidia-worker`): detecta la GPU con `lspci -d 10de:`, si no
hay Nvidia no hace nada, si hay pregunta con `kdialog` y corre la instalación
real con `pkexec` (para pedir la contraseña de forma gráfica, sin depender de
que el usuario abra una terminal).

**Chequeo de Secure Boot antes de instalar:** el módulo `nvidia-kernel-dkms`
se compila sin firmar. Con Secure Boot activado (default de fábrica en varios
laptops OEM) la instalación termina "bien" pero el módulo nunca carga al
reiniciar, sin ningún error visible — justo el tipo de falla silenciosa que
más rompe a un usuario sin experiencia técnica. `oweelinux-install-nvidia`
chequea `mokutil --sb-state` antes de ofrecer instalar; si está activado,
avisa con instrucciones para desactivarlo en la BIOS/UEFI y no continúa
(`mokutil`/`shim-signed` ya estaban en el `package-lists` base por la razón 7
de Lecciones aprendidas, así que la herramienta de detección no hace falta
agregarla). Deliberadamente **no** se automatiza el enrolamiento de MOK
(generar clave, firmar el módulo, guiar por el reinicio a MokManager) —
avisar y dejar que el usuario lo resuelva en la BIOS es más simple y robusto
que un flujo desatendido que puede fallar a mitad de camino.

### Apps recomendadas (`oweelinux-recommended-apps`)

Ícono "Apps recomendadas" en el escritorio: una pantalla con checklist
(`kdialog --checklist`) de apps sugeridas (ofimática, dibujo, video, juegos —
hoy: Geany, Krita, WPS Office, Typora, Inkscape, VLC, Blender, Hedgewars,
Kooha, Obsidian) para que el usuario elija cuáles instalar de una.

**La lista de apps NO está fija por versión del ISO.** El launcher
(`usr/local/bin/oweelinux-recommended-apps`) intenta bajar
`recommended-apps.json` desde
`raw.githubusercontent.com/oweeme/oweelinux/main/.../usr/share/oweelinux/recommended-apps.json`
(el mismo archivo del repo, fetcheado en caliente) con un timeout corto; si
falla (sin internet, GitHub caído) cae a la copia embebida en
`/usr/share/oweelinux/recommended-apps.json`. Agregar/sacar apps de la lista
es editar el JSON en el repo y hacer `git push` — **no** requiere una nueva
versión de OweeLinux, cualquier instalación ya existente la ve la próxima vez
que abre el ícono.

**Tres formas de instalar, según el campo `type` de cada entrada del JSON:**
- `flatpak`: no necesita root. El launcher hace
  `xdg-open appstream://<flatpak_id>`, que abre Discover ya posicionado en la
  página de esa app (Discover registra el manejador de `x-scheme-handler/appstream`,
  confirmado con `xdg-mime query default`) — un click más adentro de Discover
  la instala. Requiere que la app esté en Flathub (remoto ya agregado por
  `9200-flathub-remote.hook.chroot`).
- `apt-debian` / `apt-repo-own`: paquete de los repos de Debian o del repo
  propio de OweeLinux. El launcher junta los IDs seleccionados y llama a
  `pkexec oweelinux-recommended-apps-worker <manifiesto> <ids...>`, que hace
  `apt-get install` de una sola vez (un solo prompt de contraseña aunque se
  elijan varias).
- `apt-thirdparty`: paquete de un repo externo de terceros (ej. Typora) que
  no vive ni en Debian ni en el repo propio. El JSON trae los campos
  `key_url`/`keyring_path`/`repo_line`/`sources_file` completos; el worker
  los usa para armar el repo (mismo patrón que ya usa VSCode/Yandex en un
  sistema instalado: clave en `/etc/apt/keyrings/`, `Signed-By:` en el
  `sources.list.d`) antes de instalar. Agregar una futura app de terceros
  así es 100% editar el JSON, sin tocar el worker.

El worker (`usr/local/bin/oweelinux-recommended-apps-worker`) es el único
componente con privilegios — recibe la ruta al manifiesto ya descargado (no
vuelve a pegarle a la red para el JSON) y las IDs elegidas, y es
completamente genérico: no tiene ningún nombre de app hardcodeado, todo sale
del JSON.

## Lecciones aprendidas (bugs reales y su causa raíz)

Esto es lo más valioso de todo el documento — cada uno de estos costó horas de
diagnóstico real. Si algo se rompe de forma parecida, empezar por acá.

1. **`--bootappend-live 'quiet splash'` sin más rompe el arranque del live.**
   Este flag *reemplaza* los parámetros por defecto de live-build en vez de
   sumarse — sin `boot=live components` explícito, el kernel no encuentra el
   medio live. Siempre: `--bootappend-live 'boot=live components quiet splash ...'`.

2. **`lb clean --chroot` deja estado roto.** Los marcadores de etapa completada
   quedan desincronizados del filesystem real. Solución: siempre `rm -rf
   chroot cache .build *.iso` manual antes de cada build.

3. **Descargas IPv6 fallan en el build.** `Acquire::ForceIPv4 "true";` hace
   falta en **dos** lugares: el `apt.conf.d` del contenedor exterior Y
   `config/apt/apt.conf` de live-build (que aplica *dentro* del chroot de
   build, un contexto de apt completamente separado).

4. **`apt-recommends false` rompe funcionalidad real de hardware**, no solo
   "cosas de más". `wpasupplicant` (WiFi real), `kscreen` (multi-monitor
   HDMI) y otros paquetes clave son *Recommends*, no *Depends*, de sus
   paquetes padre. Decisión final del proyecto: `apt-recommends true` a nivel
   global, y podar caso por caso lo que sobra (ver sección de pines de APT)
   en vez de perseguir gaps de funcionalidad uno por uno.

5. **Autologin duplicado y en conflicto: `live-config` vs el nuestro.**
   `live-config` trae su propio autologin de consola apuntando a un usuario
   llamado literalmente `user` (no `liveuser`, que es como lo llamamos
   nosotros). El choque entre los dos mecanismos competía por el mismo VT/seat
   y dejaba SDDM colgado, sin aceptar ni mouse ni teclado, en el primer
   arranque. Fix: parámetro de arranque `noautologin` (desactiva el mecanismo
   de live-config, deja que actúe solo el nuestro).

6. **El bug más largo de cazar: SDDM renderiza perfecto pero el teclado/mouse
   no responden nunca, en el greeter.** Se investigaron y descartaron, en
   orden: RAM de la VM, VGA "std" vs `virtio-vga-gl` de QEMU (mejoró pero no
   lo resolvió del todo), X11 vs Wayland del greeter, permisos de
   `systemd-logind`/PAM. **Causa real, confirmada leyendo el log real de
   Xorg** (`/var/log/Xorg.0.log` del sistema instalado, montando el disco con
   `qemu-nbd` para leerlo sin depender de que la VM responda a nada):

   ```
   (II) config/udev: Adding input device AT Translated Set 2 keyboard (/dev/input/event0)
   (II) No input driver specified, ignoring this device.
   ```

   Faltaba el paquete `xserver-xorg-input-libinput` — el puente entre Xorg y
   `libinput`. Sin él, Xorg ve los dispositivos por udev perfectamente pero no
   tiene ningún driver para *usarlos*. La sesión Wayland normal nunca mostró
   el problema porque KWin/Wayland usa `libinput` directo contra el kernel,
   sin pasar por este driver específico de Xorg — por eso el autologin
   (que evita el greeter) siempre funcionó, mientras que cualquier momento en
   que el greeter tenía que renderizarse de verdad (primer boot sin
   autologin, o volver al greeter después de un logout) se colgaba.
   También se agregó `kwin-x11` (faltaba por completo — sin él la sesión X11
   de Plasma ni arranca) ya que estábamos forzando el greeter a modo X11
   (`/etc/sddm.conf.d/x11.conf`, `DisplayServer=x11`) por las dudas de
   compatibilidad con QEMU.

   **Técnica de diagnóstico clave que desbloqueó esto:** journal persistente
   (`etc/systemd/journald.conf.d/persistent.conf`, `Storage=persistent` — por
   defecto el journal es volátil y se pierde en cada reinicio) + montar el
   `.qcow2` de prueba desde el host con `qemu-nbd` para leer logs y archivos
   *sin* necesitar que la VM responda a nada:

   ```sh
   sudo modprobe nbd max_part=8
   sudo qemu-nbd --connect=/dev/nbd0 test-disk.qcow2
   sudo mount /dev/nbd0p1 /mnt/owee
   # journalctl --root funciona sobre un filesystem offline:
   journalctl --root=/mnt/owee -b -1 -u sddm --no-pager
   sudo umount /mnt/owee && sudo qemu-nbd --disconnect /dev/nbd0
   ```

7. **Calamares necesita internet para el bootloader si `grub-efi-amd64` (y
   paquetes relacionados: `shim-signed`, `mokutil`, `efibootmgr`, etc.) no
   están en la ISO.** El módulo `bootloader-config` de Calamares instala esos
   paquetes en el momento de instalar si no los encuentra ya presentes — en
   una máquina sin red (algo muy real para el público objetivo de esta
   distro) la instalación completa falla. Se agregaron todos al
   `package-lists` para que ya estén en el squashfs.

8. **`Pin-Priority: -1` puede romper el build si el paquete es *Depends* duro
   de otra cosa, no solo *Recommends*.** Ver sección de pines más arriba —
   probar siempre con `apt-get remove --simulate` antes.

9. **Reloj del sistema mal (batería CMOS débil/muerta) rompe `apt
   update`/`upgrade` y la instalación/arranque de apps Flatpak**, con errores
   de "Verifying signature: Not live until <fecha>". Es un problema real y
   esperable en hardware secundhand/viejo, exactamente el tipo de máquina que
   usan los usuarios objetivo de esta distro. Fix inmediato en la máquina
   afectada: `timedatectl set-ntp true`, o fijar la fecha a mano
   (`date -s "..."` + `hwclock --systohc`) si no hay red todavía. No hay un
   fix a nivel ISO todavía — queda como pendiente evaluar si vale la pena
   forzar algo más agresivo por defecto.

10. **`nvidia-prime` (el comando `prime-select` que existe en Ubuntu/KDE
    Neon) no existe en Debian.** En Debian, el offload de PRIME funciona sin
    una herramienta de "modo" — el driver Nvidia + Intel conviven
    automáticamente, y las apps que necesitan la Nvidia se lanzan con
    variables de entorno (`__NV_PRIME_RENDER_OFFLOAD=1
    __GLX_VENDOR_LIBRARY_NAME=nvidia`) o vía el menú contextual de KDE ("Run
    using Discrete Graphics"). No intentar portar `prime-select` a Debian, no
    hace falta.

11. **`kdialog` nunca estuvo en el `package-lists`, pese a ser dependencia
    real de todos los scripts de `usr/local/bin/` que muestran diálogos
    gráficos** (`oweelinux-install-nvidia`, `oweelinux-recommended-apps`).
    Pasó desapercibido porque nadie había ejecutado esos íconos de punta a
    punta — la validación de Nvidia en hardware real (Dell G3 3579) se hizo
    con `apt install nvidia-driver` directo por terminal, no clickeando el
    ícono del escritorio, así que el `kdialog: not found` (exit code 127)
    nunca salió a la luz hasta probar el ícono en una VM limpia de QEMU.
    Confirmado que faltaba tanto en el ISO como en el propio hardware ya
    instalado. Lección: un flujo que depende de un ícono de escritorio hay
    que probarlo clickeando el ícono, no ejecutando el comando equivalente a
    mano — son caminos de código distintos aunque terminen haciendo lo
    mismo.

## Estado y fases

- ✅ **Fase 1** — Base Debian + KDE mínimo
- ✅ **Fase 2** — Driver Nvidia: script de detección + instalación opcional
  post-instalación (ver [Apps opcionales](#apps-opcionales-post-instalación)),
  **validado en hardware real** (Dell G3 3579, GTX 1050 Pascal, driver
  `nvidia-driver` 550.163.01 de los repos non-free de Debian trixie,
  `nvidia-smi` y KWin Wayland funcionando sobre la GPU). Gap encontrado y
  corregido en esta validación: el instalador no chequeaba Secure Boot antes
  de instalar (ver nota en [Apps opcionales](#apps-opcionales-post-instalación)) —
  en esta máquina funcionó porque Secure Boot estaba desactivado.
- ✅ **Fase 3** — Dev stack (Rust/Go/Ada/Python vía gestores de versión)
- ✅ **Fase 4** — Branding completo (Plymouth, SDDM, KSplash, wallpaper, GRUB,
  esquema de colores)
- ✅ **Fase 5** — `oweeide` empaquetado como `.deb`, preinstalado por defecto
- ✅ **Fase 6** — Repo APT propio (`reprepro`), embebido offline en el ISO

**Validado en hardware real:** HP sin Nvidia (instalación completa, WiFi,
batería, Bluetooth, audio, GRUB con tema) y Dell G3 3579 con GTX 1050 Pascal
(driver Nvidia funcionando de punta a punta, incluyendo el fix de Secure Boot
de esta sección).

**Otros pendientes conocidos, prioridad baja:**
- Firmar el repo APT propio con GPG (solo necesario si se publica afuera del
  ISO)
- Reskinear el menú de arranque isolinux/syslinux del *live* (distinto al
  GRUB del sistema instalado, que ya tiene tema — este es más laborioso por
  ser un sistema de menú diferente y generado dinámicamente)
- Integrar el repo APT propio a la GUI de KDE Discover (hoy funciona por
  `apt install` desde terminal; para aparecer en Discover hace falta generar
  metadata AppStream y un backend PackageKit-apt funcional)
