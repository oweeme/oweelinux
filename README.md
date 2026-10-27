# OweeLinux

Debian 13 **inmutable** (ostree: el sistema es de solo lectura y se actualiza por versiones completas, con vuelta automática a la anterior si algo falla) con un escritorio propio y ligero, **OweeLinux Lite** (labwc + Python y GTK4), pensado para equipos modestos y para quien no quiere tocar la terminal. Proyecto de Hector Martinez (<https://oweeme.com>), licencia GPL-3.0.

> **Estado (26 de octubre de 2026):** se instala y funciona en QEMU (también con Secure Boot). Pendiente de probar en equipos reales (HP con AMD A12 y Dell con NVIDIA). **No hay ISO publicada** (pesa ~1,5 GB): se construye con [`docs/CONSTRUIR.md`](docs/CONSTRUIR.md). Aún no hay servidor de actualizaciones ni clave de publicación ([`docs/ACTUALIZACIONES.md`](docs/ACTUALIZACIONES.md)). El controlador privativo de NVIDIA no se construye todavía (ver abajo).

## Qué trae
- **Escritorio:** panel arriba, abajo o a los lados (delgado), escritorios virtuales, iconos y menú de clic derecho en el escritorio con arrastrar y soltar, lanzador, calendario, calculadora, monitor del sistema, capturadora, ajustes propios, bloqueo y protector de pantalla animados (kois), arranque con el logo animado, inicio de sesión con tema propio.
- **Aplicaciones:** Dolphin, Kate, Okular, Gwenview, Ark, mpv, Falkon, **LibreOffice** (Writer, Calc, Impress, Draw y Math), tienda con Discover y Flathub ya configurado.
- **Desarrollo sin permisos de administrador:** `owee-dev` crea cajas Debian (Podman + distrobox) donde `apt`, `pip`, `cargo`, `npm` y `gcc` funcionan como siempre (`owee-dev init --with python,rust,node,java`).
- **Seguridad:** cortafuegos activo, Centinela (señuelo de red, apagado por defecto), Secure Boot con GRUB y núcleo firmados, AppArmor.
- **Idiomas (22):** español, inglés, portugués, francés, alemán, italiano, ruso, ucraniano, chino, japonés, coreano, árabe, persa, hindi, urdu, indonesio, malayo, polaco, finlandés, sueco y **Owee** (romano y Owee Script, <https://github.com/oweeme/owee>).
- **Pensado para poco consumo:** `earlyoom`, zram, grabadora con límites de memoria, temporales en disco.

## Construir la ISO y probarla (resumen)
Necesitas Linux con Podman, git, QEMU/KVM y ~40 GB libres. Todo está en [`docs/CONSTRUIR.md`](docs/CONSTRUIR.md); en corto:
```bash
git clone https://github.com/oweeme/oweelinux.git && cd oweelinux
tools/devpod/devpod.sh build && tools/devpod/devpod.sh up
podman exec oweelinux-dev bash -c 'cd /work/tools/ostree-proto && ./gen-test-keys.sh'
podman exec -e OWEE_INSTALLER=1 -e OWEE_TEST_USER=0 -e OWEE_DISK_MIB=12000 oweelinux-dev \
  bash -c 'cd /work/tools/ostree-proto && ./build-image-full.sh /var/tmp/imagen && ./make-iso.sh /var/tmp/imagen /var/tmp/OweeLinux.iso'
podman cp oweelinux-dev:/var/tmp/OweeLinux.iso .
tools/usuario/probar-en-qemu.sh OweeLinux.iso --secureboot --nuevo     # instalar en una VM
tools/usuario/probar-en-qemu.sh --disco --secureboot                    # arrancar lo instalado
```
`tools/usuario/` tiene también `write-usb.sh` (grabar la ISO a un USB), `owee-diag.sh` (diagnóstico de lentitud) y un `LEEME.txt` para quien reciba la ISO.

## Estructura del repositorio
| Carpeta | Contenido |
|---|---|
| `desktop/` | el escritorio: `shell/` (panel, Ajustes, iconos del escritorio), `session/` (inicio de sesión, bloqueo, protector, ayudantes), `apps/` (calculadora, calendario, capturadora, monitor), `setup/` (asistente de primer arranque), `sddm/` (tema de inicio de sesión), `theme/`, `wallpapers/`, `i18n/` (catálogos) |
| `tools/ostree-proto/` | construcción de la imagen (ostree), ISO, pruebas en QEMU (`boot-shot.py`) |
| `tools/i18n/` | traducciones y generadores de catálogos (incluido Owee) |
| `tools/devpod/` | contenedor de desarrollo (Debian 13) |
| `tools/usuario/` | guiones para quien prueba la ISO |
| `docs/` | documentación técnica (ver abajo) |
| `livebuild-profile/`, `packaging/` | la primera versión del proyecto (live-build con KDE Plasma): ver [`docs/README-v1-livebuild.md`](docs/README-v1-livebuild.md) |

## Documentación
[`CONSTRUIR`](docs/CONSTRUIR.md) · [`ESCRITORIO`](docs/ESCRITORIO.md) · [`ARRANQUE`](docs/ARRANQUE.md) · [`ACTUALIZACIONES`](docs/ACTUALIZACIONES.md) · [`SEGURIDAD`](docs/SEGURIDAD.md) · [`IDIOMAS`](docs/IDIOMAS.md) · [`EXTENSIONES`](docs/EXTENSIONES.md) y [`CREAR_WIDGETS`](docs/CREAR_WIDGETS.md) (para crear widgets y apps) · [`RECURSOS`](docs/RECURSOS.md) · [`DESARROLLO`](docs/DESARROLLO.md).

## Lo que falta (honesto)
- Probar en el HP y el Dell reales; medir consumo y batería.
- **NVIDIA privativo:** `OWEE_NVIDIA=1` no construye todavía (dkms de nvidia 550 contra el núcleo 6.12 falla). Mientras tanto la imagen usa el controlador libre nouveau.
- Servidor de actualizaciones, clave de publicación y CI.
- Cifrado de disco (LUKS), arrastrar iconos del escritorio a mano, y más pruebas con aplicaciones de terceros.

## Autoría y licencia
Hector Martinez — GPL-3.0 (ver [`LICENSE`](LICENSE)). La capturadora se desarrolla además como proyecto aparte: <https://github.com/oweeme/screencapture>.
