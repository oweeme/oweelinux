#!/usr/bin/env bash
# Instala en un rootfs las piezas propias de OweeLinux (herramientas, servicio de salud,
# directorios de /var). Funciona antes o después de mover /etc a /usr/etc.
# Uso: overlay-owee.sh ROOTFS
set -euo pipefail
R=${1:?uso: $0 ROOTFS}; HERE=$(cd "$(dirname "$0")" && pwd)
install -m0755 "$HERE"/owee-{env,id,bootcfg,update,rollback,confirm,health,status} "$R/usr/bin/"
install -m0644 "$HERE/owee-health.service" "$R/usr/lib/systemd/system/"
[ -d "$R/usr/etc" ] && ETC=$R/usr/etc || ETC=$R/etc
mkdir -p "$ETC/systemd/system/basic.target.wants" "$R/usr/lib/tmpfiles.d"
rm -f "$ETC/systemd/system/multi-user.target.wants/owee-health.service"   # versiones antiguas lo colgaban de multi-user.target
ln -sf /usr/lib/systemd/system/owee-health.service "$ETC/systemd/system/basic.target.wants/owee-health.service"
# Espera de estabilidad de owee-health (segundos). En producción 60 (por defecto); las pruebas la acortan
# con OWEE_HEALTH_STABLE=20 al ejecutar este script.
if [ -n "${OWEE_HEALTH_STABLE:-}" ]; then
  mkdir -p "$R/usr/lib/systemd/system/owee-health.service.d"
  printf '[Service]\nEnvironment=OWEE_HEALTH_STABLE=%s\n' "$OWEE_HEALTH_STABLE" > "$R/usr/lib/systemd/system/owee-health.service.d/stable.conf"
fi
# Watchdog: si el sistema se cuelga del todo, systemd deja de avisar al temporizador y la máquina
# se reinicia sola; GRUB (que ya gastó el intento a prueba) vuelve a la versión confirmada.
mkdir -p "$R/usr/lib/systemd/system.conf.d"
printf '[Manager]\nRuntimeWatchdogSec=30s\n' > "$R/usr/lib/systemd/system.conf.d/owee-watchdog.conf"
printf 'd /var/home 0755 root root -\nd /var/roothome 0700 root root -\nd /var/usrlocal 0755 root root -\n' > "$R/usr/lib/tmpfiles.d/owee.conf"
