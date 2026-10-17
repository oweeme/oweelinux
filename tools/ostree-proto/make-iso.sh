#!/usr/bin/env bash
# Crea la ISO de OweeLinux (arranque UEFI, híbrida: sirve en DVD virtual y en USB con dd) a partir de una construcción con OWEE_INSTALLER=1 (DIR = su directorio de trabajo, con rootfs/ y sysroot/).
# La ISO contiene: núcleo + initramfs de dracut (con los módulos `ostree` y `dmsquash-live`), y LiveOS/squashfs.img (xz) con una imagen ext4 del sysroot de ostree (repositorio + despliegue).
# Al arrancar, dracut monta esa imagen de solo lectura con una capa de escritura en RAM y ostree entra en el despliegue como en un disco normal. Menú: «Instalar» (instalador) y «Probar» (escritorio sin instalar).
# Se ejecuta DENTRO del pod. Uso: make-iso.sh DIR [SALIDA.iso]       ISO_COMP=zstd para pruebas rápidas (más grande); por defecto xz.
set -euo pipefail
W=${1:?uso: $0 DIR_TRABAJO [SALIDA.iso]}; OUT=${2:-$W/OweeLinux.iso}; R=$W/rootfs; S=$W/sysroot
[ -d "$R/usr/lib/modules" ] && [ -d "$S/ostree/repo" ] || { echo "faltan $R o $S: ¿es una construcción con OWEE_INSTALLER=1?" >&2; exit 1; }
KVER=$(ls "$R/usr/lib/modules" | head -1); T=$(mktemp -d "$W/iso.XXXXXX"); trap 'rm -rf "$T"' EXIT; mkdir -p "$T/iso/LiveOS" "$T/iso/boot/grub" "$T/sq/LiveOS"
log() { echo "[iso] $*"; }
log "initramfs en vivo (dracut: ostree + dmsquash-live) para $KVER"
chroot "$R" sh -c 'command -v dracut >/dev/null && ls /usr/lib/dracut/modules.d | grep -q dmsquash-live' || { log "instalando dracut-live en el rootfs de trabajo"; chroot "$R" sh -c 'apt-get -o Acquire::http::Proxy="http://127.0.0.1:3142" install -y --no-install-recommends dracut-live dmsetup >/dev/null'; }
mkdir -p "$R/proc" "$R/sys" "$R/dev"
chroot "$R" dracut --force --no-hostonly --add "ostree dmsquash-live" --omit "plymouth nfs iscsi" --compress zstd --kver "$KVER" /tmp/live-initramfs.img
cp "$R/tmp/live-initramfs.img" "$T/iso/boot/initramfs.img"; rm -f "$R/tmp/live-initramfs.img"; install -m0644 "$R/usr/lib/modules/$KVER/vmlinuz" "$T/iso/boot/vmlinuz"
log "imagen del sistema (ext4 con el sysroot de ostree)"
MB=$(( $(du -sm "$S" | cut -f1) * 112 / 100 + 64 ))
mke2fs -q -F -t ext4 -m 0 -L OWEEROOT -d "$S" "$T/sq/LiveOS/rootfs.img" "${MB}M"
log "squashfs (${ISO_COMP:-xz})"
if [ "${ISO_COMP:-xz}" = zstd ]; then COMP="-comp zstd -Xcompression-level 6 -b 256K"; else COMP="-comp xz -Xbcj x86 -b 1M -Xdict-size 100%"; fi
mksquashfs "$T/sq" "$T/iso/LiveOS/squashfs.img" $COMP -noappend -quiet
OSTREE=$(sed -n 's/^options //p' "$S"/boot/loader/entries/*.conf | head -1 | tr ' ' '\n' | grep '^ostree=' | head -1)
[ -n "$OSTREE" ] || { echo "no encuentro ostree= en las entradas de arranque" >&2; exit 1; }
BASE="root=live:LABEL=OWEELIVE rd.live.image rd.live.overlay.overlayfs=1 rd.live.overlay.size=1536 $OSTREE rw quiet loglevel=3 rd.shell=0 rd.emergency=reboot panic=10"
cat > "$T/iso/boot/grub/grub.cfg" <<EOC
set timeout=4
set default=0
menuentry 'Instalar OweeLinux' --id install { linux /boot/vmlinuz $BASE; initrd /boot/initramfs.img; }
menuentry 'Probar OweeLinux (sin instalar)' --id try { linux /boot/vmlinuz $BASE owee.mode=try; initrd /boot/initramfs.img; }
menuentry 'Instalar OweeLinux (modo seguro: sin aceleración gráfica)' --id safe { linux /boot/vmlinuz $BASE nomodeset; initrd /boot/initramfs.img; }
EOC
log "imagen de arranque UEFI"
printf 'search --no-floppy --label OWEELIVE --set=root\nconfigfile /boot/grub/grub.cfg\n' > "$T/early.cfg"
grub-mkstandalone -O x86_64-efi -o "$T/BOOTX64.EFI" --modules="part_gpt part_msdos fat iso9660 search search_label linux normal echo configfile gzio all_video" "boot/grub/grub.cfg=$T/early.cfg" 2>/dev/null
dd if=/dev/zero of="$T/iso/boot/grub/efi.img" bs=1M count=8 status=none; mkfs.vfat -F12 "$T/iso/boot/grub/efi.img" >/dev/null
mmd -i "$T/iso/boot/grub/efi.img" ::/EFI ::/EFI/BOOT; mcopy -i "$T/iso/boot/grub/efi.img" "$T/BOOTX64.EFI" ::/EFI/BOOT/BOOTX64.EFI
log "ISO"
xorriso -as mkisofs -iso-level 3 -full-iso9660-filenames -volid OWEELIVE -appid "OweeLinux" -eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot \
  -isohybrid-gpt-basdat -append_partition 2 0xef "$T/iso/boot/grub/efi.img" -o "$OUT" "$T/iso" 2>&1 | tail -2
ls -la "$OUT"; log "listo: $OUT ($(du -h "$OUT" | cut -f1))"
