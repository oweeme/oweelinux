#!/usr/bin/env bash
# Reconstruye la imagen COMPLETA de pruebas: Debian 13 + Plasma + firmware + branding B1 + firma de actualizaciones.
# Se ejecuta DENTRO del pod (usa la caché apt-cacher-ng y las claves de prueba de gen-test-keys.sh).
# Resultado en DIR_TRABAJO: rootfs/, repo/ y pub/ (release 1 FIRMADA) y disk.img.
# Uso: build-image-full.sh DIR_TRABAJO
set -euo pipefail
W=${1:?uso: $0 DIR_TRABAJO}; HERE=$(cd "$(dirname "$0")" && pwd); R=$W/rootfs
export OWEE_GNUPGHOME=${OWEE_GNUPGHOME:-/var/tmp/owee-gnupg}
export OWEE_SIGN_KEY=$(gpg --homedir "$OWEE_GNUPGHOME" --list-keys --with-colons "OweeLinux TEST signing key A" | awk -F: '/^fpr/{print $10; exit}')
[ -n "$OWEE_SIGN_KEY" ] || { echo "faltan las claves de prueba: ejecuta gen-test-keys.sh" >&2; exit 1; }
mkdir -p "$W"
date +%T | sed 's/^/[inicio] /'
"$HERE/build-rootfs-plasma.sh" "$R"; date +%T | sed 's/^/[rootfs] /'
OWEE_TEST_USER=1 OWEE_HEALTH_STABLE=20 "$HERE/prepare-rootfs.sh" "$R" >/dev/null
"$HERE/overlay-branding.sh" "$R" /work
[ -x "$HERE/overlay-lite.sh" ] && "$HERE/overlay-lite.sh" "$R" /work
rm -rf "$W/repo" "$W/pub" "$W/sysroot" "$W/disk.img"
"$HERE/publish.sh" "$R" "$W" 1 | tail -1; date +%T | sed 's/^/[publicado] /'
DISK_MIB=6200 "$HERE/build.sh" "$W" 2>&1 | grep -v -i "block count" | tail -2
date +%T | sed 's/^/[disco] /'
echo "imagen completa lista: $W/disk.img"
