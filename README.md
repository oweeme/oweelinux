# OweeLinux

Distro propia basada en **Debian 13 (Trixie) + KDE Plasma**, con la marca **oweeme**
(logo koi, paleta teal/coral). Pensada para tres tipos de usuario a la vez:
desarrolladores, oficina, y usuarios sin experiencia técnica (incluye chicos de
~10 años) — todo en el mismo sistema, sin perfiles separados.

Principios del proyecto:

- **Cero telemetría**, en cualquier capa del sistema.
- **Estable antes que bleeding-edge** — Debian stable congelado, sin sorpresas de
  rolling release. Fue una decisión explícita después de abandonar un intento
  previo con Arch + Hyprland/COSMIC (ver `docs/PLAN_OWEELINUX.md`).
- **Liviano pero completo** — no se sacrifica funcionalidad real (WiFi, batería,
  Bluetooth, HDMI, tabletas Wacom) solo por bajar el tamaño del ISO.
- Instalable con clicks (instalador gráfico Calamares), sin necesitar terminal.
- Las apps propias se instalan y actualizan vía `apt`, desde un repo APT propio —
  nunca hace falta reinstalar el sistema para tener la última versión.

## Qué trae OweeLinux hoy

### Escritorio

- KDE Plasma 6, instalado **mínimo y curado** (no el meta-paquete `kde-full`).
- Look-and-feel propio (`org.oweelinux.desktop`): panel único arriba, sin barra
  de tareas abajo, reloj centrado.
- Esquema de color propio (teal + coral, basado en el logo del koi), aplicado
  en toda la interfaz — ventanas, diálogos, panel — no solo el wallpaper.
- **6 wallpapers de koi** a elegir desde Configuración del Sistema, todos
  ilustración vectorial propia: Solo, Duo, Pond, Sunset, Night, Dawn — además
  del wallpaper foto que viene por defecto.
- Splash de arranque (Plymouth), splash de sesión (KSplash), login (SDDM) y
  GRUB, todos con el mismo branding.

### Instalación

- Instalador gráfico Calamares, sin terminal.
- Particionado automático pensado para que los archivos del usuario sobrevivan
  a una reinstalación: `/` (40GB) y `/home` separados, más un swap chico en
  disco como colchón sobre zram.
- Filesystem del instalador limitado a lo que el ISO puede formatear de
  verdad (ext4, btrfs) — no se ofrecen opciones que fallarían a mitad de
  instalación.
- Driver Nvidia opcional post-instalación (ícono "Instalar driver Nvidia"),
  con chequeo de Secure Boot antes de instalar.

### Stack de desarrollo preinstalado

Python 3, Rust (`rustup`), Go, Ada (`gnat`), Podman, `git`, `curl`, `adb` +
`fastboot`, y una terminal moderna lista para usar: `ripgrep`, `fzf`, `bat`,
`starship`, `zsh`.

### Apps para todo el mundo (sin terminal)

Dolphin, Konsole, Kate, Gwenview, Ark, Okular, KCalc, Falkon, Spectacle — más
KDE Discover (con Flatpak) para instalar lo que falte.

**Apps recomendadas**: un ícono en el escritorio abre un checklist gráfico de
apps opcionales (Krita, WPS Office, Inkscape, VLC, Blender, Hedgewars, Kooha,
Obsidian) — se instalan con un click, cada una desde la fuente que le
corresponde (apt propio, Debian, Flatpak, o terceros). La lista se actualiza
sin necesidad de una ISO nueva, editando un manifiesto JSON en este repo.

### Bajo consumo de recursos

- `zram` (50% de la RAM, compresión lz4) en vez de depender solo de swap en
  disco.
- Baloo (indexador de archivos) instalado pero con indexado desactivado por
  defecto.
- Sin Akonadi, Kontact, ni juegos/apps de relleno.

### Apps propias

Las apps propias **no vienen incluidas en el ISO** — se instalan aparte, para
no inflar el tamaño de la descarga.

- **[oweecode](https://github.com/oweeme/oweecode)**: IDE propio (Tauri/Rust).
  Se instala desde [GitHub Releases](https://github.com/oweeme/oweecode/releases),
  no viene preinstalado ni en "Apps recomendadas".
- Repo APT propio (`reprepro`), embebido offline en el ISO — hoy distribuye
  WPS Office; funciona sin conexión desde el primer arranque.

## Estado actual

**v1 validada de punta a punta en hardware real**, incluyendo instalación
gráfica completa con el particionado root+home+swap:

- ✅ Hardware sin Nvidia (HP): WiFi, batería, Bluetooth, HDMI, audio.
- ✅ Hardware con Nvidia (Dell G3 3579, GTX 1050 Pascal): driver instalado y
  funcionando sobre Wayland, con chequeo de Secure Boot.
- ✅ Instalación gráfica completa probada en hardware real (no solo VM),
  incluyendo el nuevo esquema de particiones.

Ver el detalle completo — incluyendo los bugs reales que se encontraron y
resolvieron en el camino — en
[`docs/MANUAL_MODIFICACIONES.md`](docs/MANUAL_MODIFICACIONES.md#estado-y-fases).

## Descargar

**[live-image-amd64.hybrid.iso](http://oweeme.com/iso/live-image-amd64.hybrid.iso)**

Canal de YouTube: [@oweeme](https://www.youtube.com/@oweeme) — todavía sin
videos, pero ahí van a subirse a medida que el autor trabaje con OweeLinux.

## Instalación rápida

1. Grabar la ISO a un pendrive (recomendado: [KDE ISO Image Writer](https://apps.kde.org/isoimagewriter/)).
2. Arrancar la máquina desde el pendrive.
3. Abrir "Instalar OweeLinux" desde el escritorio y seguir el instalador. En
   el paso de particiones, elegir **"Erase disk"** con **"Format"** (no
   "Keep") para que se cree el esquema root+home+swap.
4. Si la máquina tiene GPU Nvidia: después de instalar, correr el ícono
   "Instalar driver Nvidia" del escritorio (detecta el hardware
   automáticamente).

## Para desarrollar / modificar esta distro

Toda la documentación técnica — estructura del proyecto, cómo reconstruir el
ISO, dónde tocar cada cosa, y los bugs reales que nos encontramos en el camino
(y por qué existen sus fixes) — está en
[`docs/MANUAL_MODIFICACIONES.md`](docs/MANUAL_MODIFICACIONES.md).

## Autoría y licencia

OweeLinux es un proyecto de código abierto creado y mantenido por
**Héctor Martínez**, desarrollador boliviano — [oweeme.com](https://oweeme.com).

Se distribuye bajo los términos de la **GNU General Public License v3.0
(GPLv3)**. Esto significa que cualquiera puede usar, estudiar, modificar y
redistribuir este proyecto libremente, siempre que las obras derivadas se
mantengan bajo la misma licencia y se conserve el aviso de copyright
original — el espíritu del copyleft: el software libre que nace de este
proyecto debe seguir siendo libre. El texto legal completo, sin modificar,
está en [`LICENSE`](LICENSE).

```
OweeLinux — un proyecto de Héctor Martínez (oweeme.com)
Copyright (C) 2026 Héctor Martínez

Este programa es software libre: podés redistribuirlo y/o modificarlo
bajo los términos de la Licencia Pública General de GNU publicada por
la Free Software Foundation, ya sea la versión 3 de la licencia, o
(a tu elección) cualquier versión posterior.
```
