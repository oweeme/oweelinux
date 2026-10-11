#!/usr/bin/env bash
# Prueba de arranque automática (F1/F3a): arranca el disco en QEMU+KVM+OVMF, entra por la
# consola serie y comprueba que /usr es de solo lectura, /var escribible y ostree activo.
# Se ejecuta en el HOST. Uso: boot-test.sh DISCO.img [LOG]
# Requiere: qemu-system-x86_64 con /dev/kvm y OVMF (/usr/share/OVMF/OVMF_CODE_4M.fd).
# El disco se abre con -snapshot: la prueba nunca modifica la imagen.
set -euo pipefail
DISK=${1:?uso: $0 DISCO.img [LOG]}; LOG=${2:-$(mktemp)}
VARS=$(mktemp); cp /usr/share/OVMF/OVMF_VARS_4M.fd "$VARS"; trap 'rm -f "$VARS"' EXIT

(sleep "${BOOT_WAIT:-50}"
 printf 'echo MARK_KVER=$(uname -r)\r'; sleep 1
 printf 'echo MARK_USR_OPTS=$(findmnt -n -o OPTIONS /usr)\r'; sleep 1
 printf 'touch /usr/x 2>/dev/null; echo MARK_USR_TOUCH_RC=$?\r'; sleep 1
 printf 'touch /var/ok; echo MARK_VAR_TOUCH_RC=$?\r'; sleep 1
 printf 'echo MARK_OSTREE=$(ostree admin status | grep -c "^\\*")\r'; sleep 2
 printf 'poweroff\r'; sleep 10) |
timeout 150 qemu-system-x86_64 -enable-kvm -cpu host -m 1536 -nographic -no-reboot -snapshot \
  -machine q35 \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file="$VARS" \
  -drive file="$DISK",format=raw,if=virtio > "$LOG" 2>&1 || true

val() { sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g' "$LOG" | tr -d '\r' | grep -a "^$1=" | tail -1 | cut -d= -f2-; }
fail=0
check() { # nombre, valor_obtenido, condición
  if [ "$3" = ok ]; then echo "PASA   $1 ($2)"; else echo "FALLA  $1 ($2)"; fail=1; fi; }
usr_opts=$(val MARK_USR_OPTS); usr_rc=$(val MARK_USR_TOUCH_RC); var_rc=$(val MARK_VAR_TOUCH_RC); os=$(val MARK_OSTREE)
check "/usr montado solo lectura" "$usr_opts" "$([[ $usr_opts == ro* ]] && echo ok || echo no)"
check "escribir en /usr es rechazado" "rc=$usr_rc" "$([ "$usr_rc" = 1 ] && echo ok || echo no)"
check "/var es escribible" "rc=$var_rc" "$([ "$var_rc" = 0 ] && echo ok || echo no)"
check "despliegue ostree activo" "$os" "$([ "$os" = 1 ] && echo ok || echo no)"
echo "kernel: $(val MARK_KVER)  |  log: $LOG"
exit $fail
