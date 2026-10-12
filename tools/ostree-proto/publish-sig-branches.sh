#!/usr/bin/env bash
# Crea ramas de prueba para la verificación de firmas (derivadas de la release 1 ya publicada):
#   sig/good       firmada con la clave A (de confianza)         -> debe aceptarse
#   sig/unsigned   sin firma                                      -> debe rechazarse
#   sig/wrongkey   firmada con la clave B (ajena)                 -> debe rechazarse
#   sig/tampered   firmada con A, pero con un objeto CORROMPIDO EN EL MEDIO -> debe rechazarse (la suma de verificación no coincide)
# SIG_ONLY=nombre crea solo esa rama.
# Se ejecuta DENTRO del pod. Uso: publish-sig-branches.sh DIR_TRABAJO [RAMA_BASE]
set -euo pipefail
W=${1:?uso: $0 DIR_TRABAJO [RAMA_BASE]}; BASE_REF=${2:-oweelinux/proto/x86_64}
G=${OWEE_GNUPGHOME:-/var/tmp/owee-gnupg}
fpr() { gpg --homedir "$G" --list-keys --with-colons "$1" | awk -F: '/^fpr/{print $10; exit}'; }
A=$(fpr "OweeLinux TEST signing key A"); B=$(fpr "OweeLinux TEST untrusted key B")
BASE=$(ostree rev-parse --repo="$W/repo" "$BASE_REF")
mk() {  # nombre marcador clave|none
  local name=$1 marker=$2 key=$3 ovl sign=(); ovl=$(mktemp -d)
  mkdir -p "$ovl/usr/share/owee"; echo "$marker" > "$ovl/usr/share/owee/release"
  [ "$name" != tampered ] || head -c 200000 /dev/urandom > "$ovl/usr/share/owee/payload"   # objeto grande y exclusivo para corromperlo
   chmod 0755 "$ovl" "$ovl/usr" "$ovl/usr/share" "$ovl/usr/share/owee"
  [ "$key" = none ] || sign=(--gpg-sign="$key" --gpg-homedir="$G")
  ostree commit --repo="$W/repo" --branch="sig/$name" --tree=ref="$BASE" --tree=dir="$ovl" --no-xattrs "${sign[@]}" --subject="prueba de firma: $name" >/dev/null
  rm -rf "$ovl"; ostree pull-local --repo="$W/pub" "$W/repo" "sig/$name" >/dev/null
}
want() { [ -z "${SIG_ONLY:-}" ] || [ "$SIG_ONLY" = "$1" ]; }
want good && mk good 502 "$A"; want unsigned && mk unsigned 503 none; want wrongkey && mk wrongkey 504 "$B"; want tampered && mk tampered 505 "$A"; want good2 && mk good2 506 "$A"
ostree summary --repo="$W/pub" -u
# corromper EN EL MEDIO el objeto grande de la rama "tampered" (añadir bytes al final de un flujo comprimido no se nota)
if want tampered; then
  ck=$(ostree ls --repo="$W/pub" -C sig/tampered /usr/share/owee/payload | awk '{print $5}')
  obj="$W/pub/objects/${ck:0:2}/${ck:2}.filez"; [ -f "$obj" ] || { echo "no encuentro el objeto $obj" >&2; exit 1; }
  printf '\377\377\377\377\377\377\377\377\377\377\377\377' | dd of="$obj" bs=1 seek=4000 conv=notrunc 2>/dev/null
  echo "objeto corrompido en el medio: ${ck:0:12}... ($(stat -c %s "$obj") bytes)"
fi
