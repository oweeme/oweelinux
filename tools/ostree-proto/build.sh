#!/usr/bin/env bash
# Instala la última versión publicada (pub/) en un sysroot y crea el disco UEFI.
# El despliegue queda ligado al remoto "owee" (definido por la imagen en /etc/ostree/remotes.d).
# Se ejecuta DENTRO del pod. Uso: build.sh DIR_TRABAJO [COMMIT]   (antes: publish.sh ...)
# Con COMMIT se instala esa versión concreta (útil para probar actualizaciones desde una anterior).
set -euo pipefail
WORK=${1:?uso: $0 DIR_TRABAJO [COMMIT]}; REV=${2:-}
HERE=$(cd "$(dirname "$0")" && pwd)
BRANCH=oweelinux/proto/x86_64
cd "$WORK"
rm -rf sysroot; mkdir sysroot
ostree admin init-fs --modern sysroot
ostree admin os-init --sysroot=sysroot oweelinux
R=sysroot/ostree/repo
if [ -n "$REV" ]; then   # pull-local no admite rama@commit: se trae el commit y se crea la ref a mano
  ostree pull-local --repo=$R pub --remote=owee "$REV" | tail -1
  ostree refs --repo=$R --create=owee:$BRANCH "$REV"
else
  ostree pull-local --repo=$R pub --remote=owee $BRANCH | tail -1
fi
ostree admin deploy --sysroot=sysroot --os=oweelinux \
  --karg="root=LABEL=oweeroot rw console=ttyS0 quiet" owee:$BRANCH
"$HERE/make-disk.sh" sysroot disk.img "${DISK_MIB:-2300}"
