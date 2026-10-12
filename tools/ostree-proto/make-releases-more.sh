#!/usr/bin/env bash
# Amplía un repo que YA tiene la release 1 publicada y su disco construido (p. ej. la imagen Plasma):
#   release 2 (buena, con carga realista)           -> pub-ab/
#   release 3 (servicio roto, con carga realista)   -> pub-abc/
#   N versiones "step" (con carga)                  -> pub-steps/
# Se ejecuta DENTRO del pod. Uso: make-releases-more.sh ROOTFS DIR_TRABAJO [N_STEPS]
set -euo pipefail
ROOTFS=${1:?uso: $0 ROOTFS DIR_TRABAJO [N_STEPS]}; W=${2:?}; N=${3:-40}; HERE=$(cd "$(dirname "$0")" && pwd)
rm -rf "$W/pub-ab" "$W/pub-abc" "$W/pub-steps"
BULK=1 "$HERE/publish.sh" "$ROOTFS" "$W" 2 | tail -1;          cp -a "$W/pub" "$W/pub-ab"
BULK=1 "$HERE/publish.sh" "$ROOTFS" "$W" 3 service | tail -1;  cp -a "$W/pub" "$W/pub-abc"
"$HERE/publish-steps.sh" "$W" "$N" | tail -1;                  cp -a "$W/pub" "$W/pub-steps"
du -sh "$W"/pub-ab "$W"/pub-abc "$W"/pub-steps
