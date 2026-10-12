#!/usr/bin/env bash
# Prueba de rollback (F3c). Una sola sesión de QEMU con varios reinicios:
#   B1 release 1 (confirmada) -> crea un archivo en /home -> owee-update a la 2 (a prueba) -> reinicia
#   B2 release 2: owee-health la confirma sola          -> rollback MANUAL -> reinicia
#   B3 release 1 otra vez, /home intacto                -> owee-update a la 3 (rota) -> reinicia
#   B4 release 3: servicio roto, owee-health la RECHAZA y reinicia solo
#   B5 vuelta AUTOMÁTICA a la release 1, /home intacto
# Se ejecuta en el HOST. Uso: rollback-test.sh DISCO.img DIR_PUB_AB DIR_PUB_ABC [LOG]
# (pub-ab = releases 1-2, pub-abc = 1-3). Disco con -snapshot: la prueba no lo modifica.
set -euo pipefail
DISK=${1:?uso: $0 DISCO.img PUB_AB PUB_ABC [LOG]}; AB=$(readlink -f "${2:?}"); ABC=$(readlink -f "${3:?}"); LOG=${4:-$(mktemp)}
VARS=$(mktemp); cp /usr/share/OVMF/OVMF_VARS_4M.fd "$VARS"
STAGE=$(mktemp -d); ln -s "$AB" "$STAGE/pub"
python3 -m http.server 8000 --bind 127.0.0.1 --directory "$STAGE" >/dev/null 2>&1 & HTTP=$!
trap 'kill $HTTP 2>/dev/null || true; rm -rf "$VARS" "$STAGE"' EXIT
BW=${BOOT_WAIT:-50}; HW=${HEALTH_WAIT:-30}
say() { printf '%s\r' "$1"; sleep "${2:-1}"; }
st() { say "echo MARK_$1=\$(owee-status | tr '\\n' ' ')" 1; }

(sleep "$BW"
 st B1_STATUS
 say 'echo hola-usuario > /home/dato.txt; sync' 1
 say "OWEE_REF=${REF_GOOD:-} "'owee-update 2>&1 | tail -2; echo MARK_B1_UPDATE_RC=${PIPESTATUS[0]}' "${UPDATE_WAIT:-45}"
 say 'echo MARK_B1_TRIAL=$(owee-env /boot/owee/grubenv get trial)' 1
 say 'systemctl reboot' $((BW+HW))
 st B2_STATUS
 say 'owee-rollback 2>&1 | tail -1; echo MARK_B2_ROLLBACK_RC=${PIPESTATUS[0]}' 5
 say 'systemctl reboot' $((BW+HW))
 st B3_STATUS
 say 'echo MARK_B3_DATO=$(cat /home/dato.txt)' 1
 ln -sfn "$ABC" "$STAGE/pub"
 say "OWEE_REF=${REF_BAD:-} "'owee-update 2>&1 | tail -2; echo MARK_B3_UPDATE_RC=${PIPESTATUS[0]}' "${UPDATE_WAIT:-45}"
 say 'echo MARK_B3_TRIAL=$(owee-env /boot/owee/grubenv get trial)' 1
 say 'systemctl reboot' $((BW+90+BW))
 st B5_STATUS
 say 'echo MARK_B5_DATO=$(cat /home/dato.txt)' 1
 say 'echo MARK_B5_HEALTH_RECHAZOS=$(grep -c "rechazada" /var/lib/owee/health.log)' 1
 say 'echo MARK_B5_BROKEN_UNIT=$(ls /usr/lib/systemd/system/owee-broken.service 2>&1 | grep -c "No such")' 1
 say 'poweroff' 10) |
timeout 1500 qemu-system-x86_64 -enable-kvm -cpu host -smp "${QEMU_SMP:-1}" -m "${QEMU_MEM:-1536}" -nographic -snapshot \
  -machine q35 -nic user \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file="$VARS" \
  -drive file="$DISK",format=raw,if=virtio > "$LOG" 2>&1 || true

val() { sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g' "$LOG" | tr -d '\r' | grep -a "^$1=" | tail -1 | cut -d= -f2- || true; }
kv() { echo "$1" | tr ' ' '\n' | sed -n "s/^$2=//p"; }   # kv "a=1 b=2" b -> 2
fail=0
chk() { if [ "$3" = ok ]; then echo "PASA   $1 ($2)"; else echo "FALLA  $1 ($2)"; fail=1; fi; }
ok() { [ "$1" = "$2" ] && echo ok || echo no; }
S1=$(val MARK_B1_STATUS); S2=$(val MARK_B2_STATUS); S3=$(val MARK_B3_STATUS); S5=$(val MARK_B5_STATUS)
r1=$(kv "$S1" release); r2=$(kv "$S2" release); r3=$(kv "$S3" release); r5=$(kv "$S5" release)
chk "B1 arranca en release 1 confirmada"            "$S1" "$([ "$r1" = 1 ] && [ "$(kv "$S1" booted)" = "$(kv "$S1" confirmed)" ] && echo ok || echo no)"
chk "update a la 2 deja prueba pendiente (trial=1)" "trial=$(val MARK_B1_TRIAL)" "$(ok "$(val MARK_B1_TRIAL)" 1)"
chk "B2 arranca en release 2"                       "release=$r2" "$(ok "$r2" 2)"
chk "B2 la release 2 se confirma sola (salud ok)"   "$S2" "$([ "$(kv "$S2" booted)" = "$(kv "$S2" confirmed)" ] && [ "$(kv "$S2" trial)" = 0 ] && echo ok || echo no)"
chk "rollback manual termina bien"                  "rc=$(val MARK_B2_ROLLBACK_RC)" "$(ok "$(val MARK_B2_ROLLBACK_RC)" 0)"
chk "B3 tras rollback manual: release 1"            "release=$r3" "$(ok "$r3" 1)"
chk "B3 /home conserva el archivo del usuario"      "$(val MARK_B3_DATO)" "$(ok "$(val MARK_B3_DATO)" hola-usuario)"
chk "update a la 3 (rota) deja prueba pendiente"    "trial=$(val MARK_B3_TRIAL)" "$(ok "$(val MARK_B3_TRIAL)" 1)"
chk "B5 rollback AUTOMÁTICO: vuelve a la release 1" "release=$r5" "$(ok "$r5" 1)"
chk "B5 la versión en uso es la confirmada"         "$S5" "$([ "$(kv "$S5" booted)" = "$(kv "$S5" confirmed)" ] && echo ok || echo no)"
chk "B5 /home conserva el archivo del usuario"      "$(val MARK_B5_DATO)" "$(ok "$(val MARK_B5_DATO)" hola-usuario)"
rech=$(val MARK_B5_HEALTH_RECHAZOS)
chk "la release 3 llegó a arrancar y fue rechazada" "rechazos=$rech" "$([ "${rech:-0}" -ge 1 ] && echo ok || echo no)"
echo "log: $LOG"; exit $fail
