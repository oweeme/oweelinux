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
# Instalador (Calamares y herramientas de disco): solo con OWEE_INSTALLER=1
[ "${OWEE_INSTALLER:-0}" = 1 ] && INCLUDE="$INCLUDE,$(grep -v -e '^#' -e '^$' "$HERE/packages-installer.txt" | paste -sd, -)"
rm -rf "$OUT"
# ESTADO (2026-10-25): OWEE_NVIDIA=1 NO construye todavía: dkms compila nvidia-current 550.163.01 contra el núcleo 6.12.107 y falla en la prueba «macros.h» de conftest (errores «missing binary operator before token "("» al leer cabeceras del núcleo); reproducido en un chroot mmdebstrap con gcc-14 y non-free-firmware. Sin resolver; probar en una máquina real (Dell G3, GTX 1050 Mobile) o con otra versión del controlador.
# Controlador privativo de NVIDIA (OWEE_NVIDIA=1): hace falta el componente non-free (y contrib para dkms); el módulo se compila AL CONSTRUIR la imagen (en el sistema instalado /usr es de solo lectura: no hay dkms en marcha)
COMPONENTS="main non-free-firmware"
if [ "${OWEE_NVIDIA:-0}" = 1 ]; then COMPONENTS="main contrib non-free non-free-firmware"; INCLUDE="$INCLUDE,$(grep -v -e '^#' -e '^$' "$HERE/packages-nvidia.txt" | paste -sd, -)"; fi
mmdebstrap --mode=root --variant=minbase --components="$COMPONENTS" \
  --aptopt='Acquire::http::Proxy "http://127.0.0.1:3142"' \
  --aptopt='Acquire::Retries "8"' --aptopt='Acquire::http::Timeout "60"' \
  --include="$INCLUDE" trixie "$OUT" http://deb.debian.org/debian
echo "rootfs listo: $OUT ($(du -sh "$OUT" | cut -f1))"
