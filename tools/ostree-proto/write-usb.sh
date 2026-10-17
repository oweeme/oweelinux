#!/usr/bin/env bash
# Graba la imagen de instalación en un USB CON COMPROBACIONES (evita borrar el disco equivocado): exige un dispositivo de bloques real, conectado por USB, sin nada montado,
# con espacio suficiente, y pide escribir su nombre para confirmar. Uso: write-usb.sh /dev/sdX OweeLinux-instalador-AAAAMMDD.img.xz     (cambia sdX por el USB; ver `lsblk -o NAME,SIZE,MODEL,TRAN`)
set -euo pipefail
DEV=${1:-}; IMG=${2:-}
[ -n "$DEV" ] && [ -n "$IMG" ] || { echo "uso: $0 /dev/sdX imagen.img.xz   (mira cuál es tu USB con: lsblk -o NAME,SIZE,MODEL,TRAN)" >&2; exit 2; }
[ -b "$DEV" ] || { echo "ERROR: $DEV no existe o no es un disco. Cambia «sdX» por el nombre real de tu USB (sin número al final)." >&2; exit 1; }
[ -f "$IMG" ] || { echo "ERROR: no encuentro $IMG" >&2; exit 1; }
NAME=$(basename "$DEV"); [ "$(lsblk -dno TYPE "$DEV")" = disk ] || { echo "ERROR: $DEV es una partición; usa el disco entero (sin número al final)." >&2; exit 1; }
TRAN=$(lsblk -dno TRAN "$DEV"); [ "$TRAN" = usb ] || { echo "ERROR: $DEV no es un USB (transporte: ${TRAN:-desconocido}). Por seguridad solo se graba en USB." >&2; exit 1; }
[ "$(lsblk -no MOUNTPOINTS "$DEV" | tr -d '[:space:]')" = "" ] || { echo "ERROR: $DEV tiene algo montado; desmóntalo primero (o elige otro)." >&2; exit 1; }
NEED=$(xz --robot -l "$IMG" | awk '$1=="totals"{print $5}'); HAVE=$(blockdev --getsize64 "$DEV")
[ "$HAVE" -ge "$NEED" ] || { echo "ERROR: $DEV es demasiado pequeño: tiene $((HAVE/1000000)) MB y la imagen necesita $((NEED/1000000)) MB." >&2; exit 1; }
echo "Se BORRARÁ TODO en $DEV ($(lsblk -dno SIZE,MODEL "$DEV")):"; lsblk "$DEV"
printf 'Escribe «%s» para continuar: ' "$NAME"; read -r a; [ "$a" = "$NAME" ] || { echo "cancelado"; exit 1; }
xz -dc "$IMG" | sudo dd of="$DEV" bs=4M status=progress conv=fsync && sync && echo "Listo. Ya puedes quitar el USB y arrancar desde él."
