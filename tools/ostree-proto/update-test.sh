#!/usr/bin/env bash
# Prueba de actualización (F3b): el sistema (release 1) descarga la release 2 por HTTP,
# reinicia y debe quedar en la 2 conservando la 1 como respaldo. Se ejecuta en el HOST.
# Uso: update-test.sh DISCO.img DIR_PUB [LOG]     (DIR_PUB = repo "archive" con la release 2)
# El disco se abre con -snapshot: nunca se modifica. El servidor HTTP escucha solo en 127.0.0.1:8000.
set -euo pipefail
DISK=${1:?uso: $0 DISCO.img DIR_PUB [LOG]}; PUB=${2:?}; LOG=${3:-$(mktemp)}
VARS=$(mktemp); cp /usr/share/OVMF/OVMF_VARS_4M.fd "$VARS"
STAGE=$(mktemp -d); ln -s "$(readlink -f "$PUB")" "$STAGE/pub"
python3 -m http.server 8000 --bind 127.0.0.1 --directory "$STAGE" >/dev/null 2>&1 & HTTP=$!
trap 'kill $HTTP 2>/dev/null || true; rm -rf "$VARS" "$STAGE"' EXIT

say() { printf '%s\r' "$1"; sleep "${2:-1}"; }
(sleep "${BOOT_WAIT:-50}"
 say 'echo MARK_REL_BEFORE=$(cat /usr/share/owee/release)'
 say 'echo MARK_DEPLOYS_BEFORE=$(ostree admin status | grep -c "ostree/\|oweelinux ")'
 say 'owee-update 2>&1 | tail -4; echo MARK_UPGRADE_RC=${PIPESTATUS[0]}' 45
 say 'echo MARK_STAGED=$(ostree admin status | grep -c -i "staged")'
 say 'systemctl reboot' "${BOOT_WAIT:-50}"
 say 'echo MARK_REL_AFTER=$(cat /usr/share/owee/release)'
 say 'echo MARK_DEPLOYS_AFTER=$(ostree admin status | grep -c "^[* ] oweelinux")'
 say 'echo MARK_BOOTED_FIRST=$(ostree admin status | sed -n 1p | grep -c "^\\*")'
 say 'ostree admin status' 2
 say 'poweroff' 10) |
timeout 400 qemu-system-x86_64 -enable-kvm -cpu host -m 1536 -nographic -snapshot \
  -machine q35 -nic user \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file="$VARS" \
  -drive file="$DISK",format=raw,if=virtio > "$LOG" 2>&1 || true

val() { sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g' "$LOG" | tr -d '\r' | grep -a "^$1=" | tail -1 | cut -d= -f2-; }
fail=0
chk() { if [ "$3" = ok ]; then echo "PASA   $1 ($2)"; else echo "FALLA  $1 ($2)"; fail=1; fi; }
b=$(val MARK_REL_BEFORE); a=$(val MARK_REL_AFTER); rc=$(val MARK_UPGRADE_RC); d=$(val MARK_DEPLOYS_AFTER)
chk "arranca en release 1"             "$b"     "$([ "$b" = 1 ] && echo ok || echo no)"
chk "ostree upgrade termina sin error" "rc=$rc" "$([ "$rc" = 0 ] && echo ok || echo no)"
chk "tras reiniciar queda en release 2" "$a"    "$([ "$a" = 2 ] && echo ok || echo no)"
chk "se conserva el despliegue anterior" "$d despliegues" "$([ "${d:-0}" -ge 2 ] && echo ok || echo no)"
echo "log: $LOG"; exit $fail
