# Recursos y rendimiento de OweeLinux

Objetivo: que el sistema funcione bien con 2–4 GB de RAM y discos lentos, sin sobrecargar el equipo y sin romper nada. Todo es conservador y medido en la VM (3 GB).

## Qué se hace (y dónde)
| Ajuste | Efecto | Dónde |
|---|---|---|
| Agente de contraseñas `mate-polkit` (GTK3) en vez del de KDE | ~21 MB en vez de ~179 MB de RAM | `packages-plasma.txt`, `session/owee-lite-start` |
| `fcitx5` solo si hay un método de escritura activo (y sin activación por D-Bus) | −32 MB | `session/owee-lite-start`, `overlay-lite.sh` |
| Reloj del panel y controles de grabación sin sondeo por segundo | 1 despertar por minuto en reposo | `shell/owee_panel.py` |
| `earlyoom` | actúa con menos del 8 % de memoria disponible (sin esperar a que se llene el zram: entonces ya está todo bloqueado); cierra navegadores, grabadoras y apps pesadas; nunca el escritorio, el sonido ni los servicios | `overlay-lite.sh` (`/etc/default/earlyoom`) |
| Grabadora de pantalla | temporales en disco (no en `/tmp`, que es RAM), límites de memoria holgados (45 % / 60 % de la RAM) con `systemd-run --user --scope`, cierre paciente de `wf-recorder`, cámara que se apaga al parar y reducción del archivo en segundo plano (Original / Equilibrada / Ligera) | `apps/capturadora/core.py` |
| zram con zstd (50 % de la RAM) + sysctl (`vm.swappiness=100`, `page-cluster=0`, `vfs_cache_pressure=50`, escritura a disco más suave) | más margen con poca RAM | `overlay-lite.sh` |
| Planificador de disco por tipo (HDD→bfq, SSD→mq-deadline, NVMe→none) | fluidez en HDD, menos sobrecarga en SSD | regla udev `60-owee-ioscheduler.rules` |
| `DefaultTimeoutStopSec=15s`, registros acotados (150 MB / 40 MB en RAM) | apagado rápido, disco pequeño | `overlay-lite.sh` |
| `thermald`, `fstrim.timer` | temperatura (Intel) y salud del SSD | paquetes / `overlay-lite.sh` |
| Regla de brillo (`90-owee-backlight.rules`) | el grupo `video` puede cambiar el brillo (el paquete de Debian no la trae) | `overlay-lite.sh` |

## Medidas (VM de 3 GB, escritorio en reposo)
- Antes: 622 MB usados; `polkit-kde-auth` 179 MB. Después: 531 MB; `polkit-mate` 21 MB.
- Prueba de `earlyoom`: un proceso que devoraba memoria fue cerrado con la memoria libre al 1,6 %; el escritorio siguió vivo.

## Sin verificar
Hardware real (brillo, térmico, planificador de disco), equipos de 2 GB, batería. El ahorro de despertares del reloj no se midió con un medidor de energía.

## Grabadora: medidas y límites (20 oct 2026, HP con AMD A12-9700P, 15 GB)
- Con grabación + varias apps, la memoria llegó a 15 GB usados, 5-6 GB «compartidos» y el zram lleno; `kswapd0` al 100 % y el compositor expulsado al intercambio (labwc 196 → 34 MB residentes). El equipo se congeló y se reinició.
- **No era el archivo de vídeo en `/tmp`** (117 MB en ese momento): el origen de los GB compartidos sigue sin identificar. `owee-diag.sh` mide ahora la memoria compartida por proceso y la memoria gráfica (GTT) para señalarlo.
- No se reprodujo en una VM (software de render): `wf-recorder` se mantuvo en ~110 MB.
- Reducción de tamaño (prueba con vídeo sintético de 60 s, no con pantalla real): 19,0 MB → 7,5 MB (Equilibrada, 720p) y 4,5 MB (Ligera, 720p a 20 fps).
