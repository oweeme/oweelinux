#!/usr/bin/env bash
# Construye el rootfs de la imagen real (Debian 13 + Plasma) con mmdebstrap.
# Se ejecuta DENTRO del pod. Usa apt-cacher-ng (127.0.0.1:3142) para no repetir descargas:
# con una red lenta es la diferencia entre horas y minutos al reconstruir.
# Uso: build-rootfs-plasma.sh DIR_ROOTFS
set -euo pipefail
OUT=${1:?uso: $0 DIR_ROOTFS}; HERE=$(cd "$(dirname "$0")" && pwd)
pgrep -x apt-cacher-ng >/dev/null || { mkdir -p /run/apt-cacher-ng; chown apt-cacher-ng /run/apt-cacher-ng 2>/dev/null || true
  /usr/sbin/apt-cacher-ng -c /etc/apt-cacher-ng ForeGround=0 PidFile=/run/apt-cacher-ng/pid SocketPath=/run/apt-cacher-ng/socket >/dev/null 2>&1; sleep 2; }
INCLUDE=$(grep -v -e '^#' -e '^$' "$HERE/packages-plasma.txt" | paste -sd, -)
rm -rf "$OUT"
mmdebstrap --mode=root --variant=minbase \
  --aptopt='Acquire::http::Proxy "http://127.0.0.1:3142"' \
  --include="$INCLUDE" trixie "$OUT" http://deb.debian.org/debian
echo "rootfs listo: $OUT ($(du -sh "$OUT" | cut -f1))"
