#!/usr/bin/env bash
# Prueba el INSTALADOR en una ventana de QEMU: arranca la imagen de instalación y le añade un segundo disco VACÍO donde se instala (se crea si no existe).
# El disco de instalación no guarda nada (-snapshot); el disco destino SÍ se guarda, para poder arrancarlo después con run-vm.sh.
# Uso: run-install-vm.sh IMAGEN_INSTALACION.img [DESTINO.img] [MiB_RAM] [CPUs]      (destino por defecto: ~/.cache/oweelinux/vm/destino.img, 10 GB)
set -euo pipefail
DISK=${1:?uso: $0 IMAGEN_INSTALACION.img [DESTINO.img] [MiB_RAM] [CPUs]}; DEST=${2:-$HOME/.cache/oweelinux/vm/destino.img}; MEM=${3:-3072}; CPUS=${4:-2}
[ -e "$DEST" ] || { mkdir -p "$(dirname "$DEST")"; truncate -s 10G "$DEST"; echo "disco destino nuevo: $DEST (10 GB, vacío)"; }
TMP=$HOME/.cache/oweelinux/tmp; mkdir -p "$TMP"; export TMPDIR=$TMP
VARS=$(mktemp "$TMP/vars.XXXXXX"); cp /usr/share/OVMF/OVMF_VARS_4M.fd "$VARS"; trap 'rm -f "$VARS"' EXIT
exec qemu-system-x86_64 -name "OweeLinux instalador" -enable-kvm -cpu host -smp "$CPUS" -m "$MEM" -machine q35 \
  -snapshot -display gtk,zoom-to-fit=off -device virtio-vga,xres=1280,yres=720 -device qemu-xhci -device usb-tablet -device usb-kbd \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file="$VARS" \
  -drive file="$DISK",format=raw,if=virtio -drive file="$DEST",format=raw,if=virtio,snapshot=off -nic user
