#!/usr/bin/env bash
# Publica una versión: marca el rootfs con REL, commit en el repo local y copia a un repo
# "archive" (servible por HTTP) con su resumen. Se ejecuta DENTRO del pod.
# Uso: publish.sh ROOTFS DIR_TRABAJO RELEASE [ROTURA]
# ROTURA (solo para probar el rollback automático) publica una versión defectuosa SIN tocar el
# rootfs original (trabaja sobre una copia con enlaces duros):
#   service  = añade un servicio que falla al arrancar (el sistema queda "degraded")
#   initrd   = initramfs corrupto (el arranque falla en el kernel)
set -euo pipefail
ROOTFS=${1:?uso: $0 ROOTFS DIR_TRABAJO RELEASE [ROTURA]}; WORK=${2:?}; REL=${3:?}; BREAK=${4:-}
BRANCH=oweelinux/proto/x86_64
mkdir -p "$WORK"; cd "$WORK"
if [ -n "$BREAK" ]; then
  COPY="$WORK/rootfs-broken"; rm -rf "$COPY"; cp -al "$ROOTFS" "$COPY"; ROOTFS=$COPY; trap 'rm -rf "$COPY"' EXIT
  case $BREAK in
    service)
      printf '[Unit]\nDescription=Servicio roto a proposito (prueba de rollback)\n[Service]\nExecStart=/bin/false\n[Install]\nWantedBy=multi-user.target\n' > "$ROOTFS/usr/lib/systemd/system/owee-broken.service"
      ln -sf /usr/lib/systemd/system/owee-broken.service "$ROOTFS/usr/etc/systemd/system/multi-user.target.wants/owee-broken.service" ;;
    initrd)
      K=$(ls "$ROOTFS/usr/lib/modules"); rm -f "$ROOTFS/usr/lib/modules/$K/initramfs.img"
      head -c 4096 /dev/urandom > "$ROOTFS/usr/lib/modules/$K/initramfs.img" ;;
    *) echo "ROTURA desconocida: $BREAK" >&2; exit 1 ;;
  esac
fi
mkdir -p "$ROOTFS/usr/share/owee"; echo "$REL" > "$ROOTFS/usr/share/owee/release"
[ -d repo ] || ostree init --repo=repo --mode=bare
ostree commit --repo=repo --branch=$BRANCH --tree=dir="$ROOTFS" --no-xattrs \
  --subject="release $REL ($(date -u +%F\ %T))" | tail -1
[ -d pub ] || ostree init --repo=pub --mode=archive
ostree pull-local --repo=pub repo $BRANCH | tail -1
ostree summary --repo=pub -u
echo "publicado release $REL: $(ostree rev-parse --repo=pub $BRANCH)"
