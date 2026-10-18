# Recursos y rendimiento de OweeLinux

Objetivo: que el sistema funcione bien con 2–4 GB de RAM y discos lentos, sin sobrecargar el equipo y sin romper nada. Todo es conservador y medido en la VM (3 GB).

## Qué se hace (y dónde)
| Ajuste | Efecto | Dónde |
|---|---|---|
| Agente de contraseñas `mate-polkit` (GTK3) en vez del de KDE | ~21 MB en vez de ~179 MB de RAM | `packages-plasma.txt`, `session/owee-lite-start` |
| `fcitx5` solo si hay un método de escritura activo (y sin activación por D-Bus) | −32 MB | `session/owee-lite-start`, `overlay-lite.sh` |
| Reloj del panel y controles de grabación sin sondeo por segundo | 1 despertar por minuto en reposo | `shell/owee_panel.py` |
| `earlyoom` | cierra la app más pesada antes de que el equipo se congele por falta de memoria; protege el escritorio | `overlay-lite.sh` (`/etc/default/earlyoom`) |
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
