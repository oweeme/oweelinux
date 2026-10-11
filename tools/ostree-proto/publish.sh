#!/usr/bin/env bash
# Publica una versión: marca el rootfs con REL, commit en el repo local y copia a un repo
# "archive" (servible por HTTP) con su resumen. Se ejecuta DENTRO del pod.
# Uso: publish.sh ROOTFS DIR_TRABAJO RELEASE
set -euo pipefail
ROOTFS=${1:?uso: $0 ROOTFS DIR_TRABAJO RELEASE}; WORK=${2:?}; REL=${3:?}
BRANCH=oweelinux/proto/x86_64
mkdir -p "$WORK"; cd "$WORK"
mkdir -p "$ROOTFS/usr/share/owee"; echo "$REL" > "$ROOTFS/usr/share/owee/release"
[ -d repo ] || ostree init --repo=repo --mode=bare
ostree commit --repo=repo --branch=$BRANCH --tree=dir="$ROOTFS" --no-xattrs \
  --subject="release $REL ($(date -u +%F\ %T))" | tail -1
[ -d pub ] || ostree init --repo=pub --mode=archive
ostree pull-local --repo=pub repo $BRANCH | tail -1
ostree summary --repo=pub -u
echo "publicado release $REL: $(ostree rev-parse --repo=pub $BRANCH)"
