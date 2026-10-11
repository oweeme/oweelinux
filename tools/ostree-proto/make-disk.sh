#!/usr/bin/env bash
# Convierte un sysroot de ostree en un disco GPT arrancable por UEFI:
#   p1 = ESP (FAT, GRUB)   p2 = raíz ext4 (etiqueta oweeroot, con /boot dentro)
# Se ejecuta DENTRO del pod, sin montar nada (mke2fs -d / mcopy).
# Uso: make-disk.sh SYSROOT DISCO.img [TAMAÑO_MiB]
set -euo pipefail
SYSROOT=${1:?uso: $0 SYSROOT DISCO.img [MiB]}; IMG=${2:?}; SIZE=${3:-2300}
ESP_MIB=128
OFF_ESP=$((1*1024*1024)); OFF_ROOT=$(( (1+ESP_MIB)*1024*1024 ))
ROOT_BYTES=$(( (SIZE-1-ESP_MIB)*1024*1024 - 1024*1024 ))   # deja 1 MiB final para la GPT de respaldo

# El menú real lo genera owee-bootcfg desde las entradas BLS de ostree (ver ese script).
HERE=$(cd "$(dirname "$0")" && pwd)
PATH="$HERE:$PATH" owee-bootcfg "$SYSROOT/boot"

W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
cat > "$W/grub.cfg" <<EOC
search --no-floppy --label oweeroot --set=root
configfile /boot/owee/grub.cfg
EOC
grub-mkstandalone -O x86_64-efi -o "$W/BOOTX64.EFI" \
  --modules="part_gpt ext2 search search_label linux normal echo gzio" \
  "boot/grub/grub.cfg=$W/grub.cfg" 2>/dev/null

truncate -s "${SIZE}M" "$IMG"
sfdisk -q "$IMG" <<EOS
label: gpt
start=2048, size=$((ESP_MIB*2048)), type=C12A7328-F81F-11D2-BA4B-00A0C93EC93B
type=4F68BCE3-E8CD-4DB1-96E7-FBCAF984B709
EOS
mkfs.vfat -F32 -s 1 --offset $((OFF_ESP/512)) "$IMG" $((ESP_MIB*1024)) >/dev/null
mmd   -i "$IMG@@$OFF_ESP" ::/EFI ::/EFI/BOOT
mcopy -i "$IMG@@$OFF_ESP" "$W/BOOTX64.EFI" ::/EFI/BOOT/BOOTX64.EFI
mke2fs -q -F -t ext4 -L oweeroot -d "$SYSROOT" -E offset=$OFF_ROOT "$IMG" $((ROOT_BYTES/1024))k
echo "disco listo: $IMG"
