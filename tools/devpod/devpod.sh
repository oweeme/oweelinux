#!/usr/bin/env bash
# Gestiona el pod de desarrollo "oweelinux" (Podman rootless).
#   ./devpod.sh build    construye la imagen (descarga debian:trixie la 1ª vez)
#   ./devpod.sh up       crea el pod (si falta) y arranca el contenedor "dev"
#   ./devpod.sh shell    abre una shell dentro del contenedor
#   ./devpod.sh down     detiene y elimina contenedor y pod (el repo no se toca)
set -euo pipefail

POD=oweelinux
CTR=oweelinux-dev
IMG=localhost/oweelinux-dev:trixie
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

case "${1:-}" in
  build)
    podman build -t "$IMG" -f "$REPO/tools/devpod/Containerfile" "$REPO/tools/devpod"
    ;;
  up)
    podman pod exists "$POD" || podman pod create --name "$POD" --label project=oweelinux
    podman container exists "$CTR" || podman run -d --name "$CTR" --pod "$POD" \
        -v "$REPO":/work:Z \
        -v oweelinux-cache:/var/cache/apt \
        "$IMG"
    podman pod start "$POD" >/dev/null
    podman pod ps --filter name="$POD"
    ;;
  shell)
    exec podman exec -it -w /work "$CTR" bash
    ;;
  down)
    podman pod rm -f "$POD"
    ;;
  *)
    sed -n '2,7p' "${BASH_SOURCE[0]}"; exit 1
    ;;
esac
