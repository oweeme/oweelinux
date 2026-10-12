#!/usr/bin/env bash
# Crea N versiones mínimas (steps/step1..stepN) derivadas de la release 2: cada una solo cambia
# /usr/share/owee/release (=100+k). Usa "--tree=ref=BASE --tree=dir=OVERLAY", que es instantáneo
# (no recorre los 370 MB). Se ejecuta DENTRO del pod. Uso: publish-steps.sh DIR_TRABAJO [N]
set -euo pipefail
source "$(dirname "$0")/lib-bulk.sh"
W=${1:?uso: $0 DIR_TRABAJO [N]}; N=${2:-40}; cd "$W"
# BASE_REF=rama usa esa rama como base (p. ej. good/new, que ya incluye la última comprobación de salud);
# si no, la release 2 de la rama principal.
if [ -n "${BASE_REF:-}" ]; then BASE=$(ostree rev-parse --repo=repo "$BASE_REF")
else BASE=$(ostree log --repo=repo oweelinux/proto/x86_64 | awk '/^commit/{c=$2} /release 2 /{print c; exit}')
fi
[ -n "$BASE" ] || { echo "no encuentro la release 2 en repo/" >&2; exit 1; }
for k in $(seq 1 "$N"); do
  OVL=$(mktemp -d); mkdir -p "$OVL/usr/share/owee"; echo $((100+k)) > "$OVL/usr/share/owee/release"
  # --tree=dir toma los permisos de las carpetas del overlay (mktemp crea la raíz con 0700 y
  # eso acabó en "/" del commit, rompiendo servicios): se fijan igual que en la imagen.
  # Carga por versión (STEP_SMALL archivos pequeños + STEP_N de STEP_MB MB): amplía la ventana del corte.
  bulk_payload "$OVL" "step$k" "${STEP_SMALL:-400}" "${STEP_MB:-4}" "${STEP_N:-3}"
  chmod 0755 "$OVL" "$OVL/usr" "$OVL/usr/share" "$OVL/usr/share/owee"
  ostree commit --repo=repo --branch="steps/step$k" --tree=ref="$BASE" --tree=dir="$OVL" \
    --no-xattrs --subject="step $k" >/dev/null
  rm -rf "$OVL"
  ostree pull-local --repo="${OUT_PUB:-pub}" repo "steps/step$k" >/dev/null
done
ostree summary --repo="${OUT_PUB:-pub}" -u
echo "publicadas $N versiones step (base release 2 = ${BASE:0:12})"
