#!/usr/bin/env bash
# Prepara todo lo que necesitan las pruebas F3b/F3c, DENTRO del pod:
#   - release 1 -> disco de arranque (disk.img)
#   - release 2 (buena)               -> pub-ab/   (repo servible)
#   - release 3 (servicio roto)       -> pub-abc/  (repo servible, contiene 1, 2 y 3)
#   - N versiones step (rama steps/)   -> pub-steps/ (para la prueba de corte de energía)
# Uso: make-releases.sh ROOTFS DIR_TRABAJO
set -euo pipefail
ROOTFS=${1:?uso: $0 ROOTFS DIR_TRABAJO}; W=${2:?}; HERE=$(cd "$(dirname "$0")" && pwd)
"$HERE/overlay-owee.sh" "$ROOTFS"
rm -rf "$W/repo" "$W/pub" "$W/pub-ab" "$W/pub-abc" "$W/pub-steps"
"$HERE/publish.sh" "$ROOTFS" "$W" 1 | tail -1
"$HERE/build.sh" "$W" 2>&1 | grep -v -i "block count" | tail -1
"$HERE/publish.sh" "$ROOTFS" "$W" 2 | tail -1;            cp -a "$W/pub" "$W/pub-ab"
"$HERE/publish.sh" "$ROOTFS" "$W" 3 service | tail -1;    cp -a "$W/pub" "$W/pub-abc"
"$HERE/publish-steps.sh" "$W" "${STEPS:-40}" | tail -1;  cp -a "$W/pub" "$W/pub-steps"
