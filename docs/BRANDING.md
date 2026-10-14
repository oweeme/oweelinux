# Branding de OweeLinux en la imagen ostree

Estado: **plan** (2026-10-12). La identidad visual de OweeLinux existe hoy solo en el perfil antiguo
(`livebuild-profile/config/includes.chroot_after_packages/`) y **no está en la imagen ostree**, que es Plasma de
fábrica. Este plan la traslada por fases, con una comprobación visual en cada una.

Fuente: ver también `docs/MANUAL_MODIFICACIONES.md` (sección de branding) y `docs/INTERFAZ.md` (el diseño nuevo
—barra flotante, claro/oscuro, iconos propios— reemplazará esta identidad más adelante; esto es **paridad** con la
distro anterior, para no perder nada al pasar a ostree).

## Qué hay que trasladar
| Pieza | Origen en el perfil antiguo | Destino en la imagen ostree |
|---|---|---|
| Identidad del sistema | `etc/os-release` + logos `hicolor/*/apps/distributor-logo-oweelinux.png` | `/usr/lib/os-release` (en la imagen `/etc/os-release` es un enlace a él) + iconos en `/usr/share/icons/hicolor` |
| Fondos | `usr/share/wallpapers/OweeLinux*` (1 foto + 6 koi) | `/usr/share/wallpapers/` |
| Esquema de color | `usr/share/color-schemes/OweeLinux.colors` | `/usr/share/color-schemes/` |
| Aspecto de Plasma (panel único arriba, reloj centrado, splash) | `usr/share/plasma/look-and-feel/org.oweelinux.desktop` | `/usr/share/plasma/look-and-feel/` |
| Ajustes por defecto | `etc/skel/.config/{kdeglobals,ksplashrc}` | **`/etc/xdg/`** (valen para cualquier usuario, también los creados después; `skel` solo se copia si el usuario se crea con `useradd -m`) |
| Aplicar fondo y colores al primer inicio | `usr/local/bin/oweelinux-first-login` | `/usr/libexec/oweelinux/` (en la imagen `/usr/local` es un enlace a `/var/usrlocal`, que nace vacío) |
| Login (SDDM) | `usr/share/sddm/themes/breeze/theme.conf.user` | igual |
| Arranque (Plymouth) | `usr/share/plymouth/themes/oweelinux`, `etc/plymouth/plymouthd.conf` | requiere paquete `plymouth` y su módulo en el initramfs (dracut) |
| GRUB | `boot/grub/themes/oweelinux` | **no encaja tal cual**: el GRUB de la imagen es un binario EFI con la configuración embebida |
| Accesos "Instalar driver Nvidia" / "Apps recomendadas" | `usr/local/bin/oweelinux-*`, `.desktop` | **no se trasladan**: usan `apt`, que el sistema inmutable no usa (Nvidia irá en la imagen; las apps, por Flatpak: F4) |
| Instalador (Calamares) | `etc/calamares/branding/` | queda para el instalador nuevo (M2) |

Paleta (del manual): fondo `#102019`, acento teal `#2A9D8F`, acento coral `#F06548`, texto `#EFF0F1`.

## Fases
**B0 — Inventario y decisiones** ✅ (este documento).

**B1 — Identidad base de Plasma** ✅ *(hecha y comprobada 2026-10-12)* (visible, bajo riesgo): `os-release` + logos, fondos, esquema de color,
*look-and-feel* con el panel arriba, ajustes por defecto en `/etc/xdg`, script de primer inicio y tema de SDDM.
- *Cambios respecto al perfil antiguo:* ajustes en `/etc/xdg` en vez de `skel`; el script sale de `/usr/local`.
- *Comprobación:* `os-release` correcto; capturas del escritorio, del menú y de la pantalla de login **antes y después**;
  `kreadconfig6` confirma el esquema de color y el paquete de aspecto.

**B2 — Arranque**: Plymouth (instalar `plymouth` + módulo de dracut; el *initramfs* cambia, así que hay que repetir
`boot-test.sh`) y GRUB (decidir: tema con módulos gráficos embebidos o dejarlo minimalista).
- *Comprobación:* captura del menú de GRUB y del splash durante el arranque; las pruebas de arranque, actualización y
  rollback siguen pasando.

**B3 — Pulido**: logo en "Acerca de este sistema", iconos de escritorio útiles (sin `apt`), nombre del equipo,
fondos alternativos seleccionables, coherencia con el modo claro/oscuro.

**B4 — Identidad propia (diseño nuevo)**: variantes clara/oscura con *tokens* de diseño, iconos y tipografía propios,
barra flotante (`docs/INTERFAZ.md`, F6/F7). Sustituye lo trasladado en B1.

**B5 — Instalador**: se hace con el instalador nuevo (M2).

## Riesgos
- El `autologin` de SDDM de las imágenes de prueba **no debe** llegar a una imagen real.
- Cambiar el *initramfs* (Plymouth) exige repetir las pruebas de arranque, actualización y rollback.
- `look-and-feel` aplica el panel solo a usuarios **sin configuración previa** de Plasma.
- Los 6 fondos de koi son ilustraciones propias del autor (SVG); las fotos de `docs/wallpaper` son de terceros (Unsplash, licencia que permite redistribuirlas como fondos; ver `docs/CREDITOS.md`).

## Resultado de B1 (2026-10-12)
Imagen ostree con el branding (`tools/ostree-proto/overlay-branding.sh`, script `brand-shots.py` para las capturas).
Capturas de **antes y después** en `docs/img/branding/`:
| | Antes (Plasma de fábrica) | Después (B1) |
|---|---|---|
| `os-release` | Debian GNU/Linux 13 (trixie) | **OweeLinux 1 (Debian 13, Trixie)** |
| Esquema de color (`kreadconfig6`) | sin configurar | **OweeLinux** |
| Aspecto de Plasma | sin configurar | **org.oweelinux.desktop** |
| Iconos | sin configurar | breeze-dark |
| Escritorio | fondo morado, panel abajo, tema claro | **foto de koi, panel fino arriba con reloj centrado, tema oscuro teal** |
| Login | fondo morado | **fondo de koi desenfocado** |
Imágenes: `antes-{escritorio,menu,login}.png`, `despues-{escritorio,menu,login}.png`.

Comprobaciones: la imagen con branding sigue arrancando como sistema inmutable (`boot-test.sh`, ver abajo).
No se tocó el initramfs ni el kernel, así que no se repitieron las pruebas de actualización, rollback y corte de energía.

**Hallazgos del método:**
- Para capturar el login **no** sirve `loginctl terminate-user`: el ayudante de SDDM se cae ("Process crashed") y queda sin pantalla. Se quita el autologin en la VM y se reinicia SDDM.
- Los accesos del escritorio y las apps recomendadas del perfil antiguo no se trasladaron (usan `apt`).
- El fondo por defecto es una foto de koi; licencia de Unsplash (permite uso y redistribución; ver `docs/CREDITOS.md`).
- **Pendiente:** B2 (Plymouth y GRUB), B3 (pulido), B4 (identidad nueva).
