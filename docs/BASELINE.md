# Línea base (F0)

Medida el 2026-10-10. **Referencia: Deepin 25 en esta máquina, no OweeLinux.**
Sirve para fijar metas realistas y como punto de comparación. No hay medición del
Dell G3 con Nvidia todavía (ver "Pendiente").

## Hardware

| | |
|---|---|
| Equipo | Lenovo 20KNS13D00 |
| CPU | Intel Core i5-7200U (2 núcleos / 4 hilos) |
| GPU | Intel HD Graphics 620 (sin Nvidia) |
| RAM | 16 GB |
| Discos | SSD SATA Samsung MZ7LN256 (sda) + SSD NVMe 256 GB (raíz) |
| SO | Deepin 25, kernel 6.18.48, sesión **X11**, LightDM |
| Estado | Con navegador y otras apps abiertas (**no** es un escritorio en reposo limpio) |

## Arranque (`systemd-analyze`)

| Etapa | Tiempo |
|---|---|
| Firmware | 4,4 s |
| Loader (bootloader) | **9,8 s** |
| Kernel | 2,9 s |
| Userspace hasta `graphical.target` | 9,7 s |
| **Total** | **26,8 s** |

Cadena crítica de userspace: `plymouth-quit-wait.service` (7,5 s) retrasa
`graphical.target`. Servicios más lentos: `NetworkManager-wait-online` 6,8 s,
`apt-daily` 6,7 s, `lightdm` 6,5 s, `apt-daily-upgrade` 2,2 s.

### Corrección importante
Se había supuesto que los 9,8 s del *loader* eran el menú de GRUB esperando.
**Es falso en esta máquina**: `GRUB_TIMEOUT=1`. La causa real no está identificada
(hipótesis: carga del kernel/initramfs, firmware o gestor de arranque). Se investiga
en F2 antes de tocar nada.

## Memoria (con la sesión cargada y muchas apps abiertas)

Total 15,9 GB; usados 5,3 GB; el resto es caché de disco.
Procesos de escritorio de Deepin, RSS aproximado: `dde-shell` 433 MB,
`dde-file-manager` 221 MB (+112 MB del diálogo), `kwin_x11` 175 MB, `Xorg` 115 MB,
`dde-lock` 128 MB, `trayplugin-load` 191 MB, `service-manager` 262 MB.
**No es una cifra de "RAM en reposo"**: hay que repetirla tras un arranque limpio sin otras apps.

## Tiempo hasta la primera ventana (caliente, 3 repeticiones)

Herramienta: `tools/bench/first-window.sh` (X11 + `xdotool`, filtra por PID).

| App | Resultado | Fiabilidad |
|---|---|---|
| GIMP (`/opt/apps/org.gimp`, formato de Deepin) | 975 – 1077 ms | Probablemente mide la **pantalla de carga** (splash), no la ventana principal |
| LibreOffice Writer | no medible | Su ventana no se asocia al PID lanzado (sin resultado válido) |

Limitaciones: solo en caliente (el frío exige `drop_caches` con root); la primera
medición incluía ventanas ajenas y se descartó.

## Pendiente de F0
- [ ] Repetir tras un **arranque limpio** (RAM en reposo real).
- [ ] Medición en frío: `sync; echo 3 | sudo tee /proc/sys/vm/drop_caches` antes de cada prueba.
- [ ] Distinguir splash y ventana principal (p. ej. por clase de ventana o tamaño).
- [ ] Medir el **Dell G3 con Nvidia** y la HP (las máquinas objetivo del proyecto).
- [ ] Identificar la causa del *loader* de 9,8 s.
