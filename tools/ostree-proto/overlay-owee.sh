#!/usr/bin/env bash
# Instala en un rootfs las piezas propias de OweeLinux (herramientas, servicio de salud,
# directorios de /var). Funciona antes o después de mover /etc a /usr/etc.
# Uso: overlay-owee.sh ROOTFS
set -euo pipefail
R=${1:?uso: $0 ROOTFS}; HERE=$(cd "$(dirname "$0")" && pwd)
install -m0755 "$HERE"/owee-{env,id,bootcfg,update,rollback,confirm,health,status} "$R/usr/bin/"
install -m0644 "$HERE/owee-health.service" "$R/usr/lib/systemd/system/"
[ -d "$R/usr/etc" ] && ETC=$R/usr/etc || ETC=$R/etc
mkdir -p "$ETC/systemd/system/multi-user.target.wants" "$R/usr/lib/tmpfiles.d"
ln -sf /usr/lib/systemd/system/owee-health.service "$ETC/systemd/system/multi-user.target.wants/owee-health.service"
printf 'd /var/home 0755 root root -\nd /var/roothome 0700 root root -\nd /var/usrlocal 0755 root root -\n' > "$R/usr/lib/tmpfiles.d/owee.conf"
