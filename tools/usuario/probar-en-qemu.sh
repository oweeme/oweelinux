#!/bin/bash
# Prueba OweeLinux en una ventana de QEMU (UEFI), sin tocar tu equipo.
#   ./probar-en-qemu.sh OweeLinux-XXXX.iso      arranca la ISO (instalar o probar). Crea un disco virtual de 20 GB en ~/oweelinux-vm/disco.img
#   ./probar-en-qemu.sh --disco                 arranca el sistema ya instalado en ese disco (sin la ISO): así ves el arranque con el logo
# Opciones:  --secureboot (Secure Boot activado, como en el HP)   --ram 4096 (MB)   --cpus 2   --nuevo (borra el disco virtual y empieza de cero)
# Necesita: qemu-system-x86_64 y ovmf (sudo apt install qemu-system-x86 ovmf). El disco virtual es un archivo; para borrarlo todo: rm -r ~/oweelinux-vm
set -euo pipefail
ISO=""; DISCO_SOLO=0; SB=0; RAM=4096; CPUS=2; NUEVO=0
while [ $# -gt 0 ]; do case "$1" in
  --disco) DISCO_SOLO=1 ;; --secureboot) SB=1 ;; --nuevo) NUEVO=1 ;; --ram) RAM=${2:?}; shift ;; --cpus) CPUS=${2:?}; shift ;;
  -h|--help) sed -n 2,8p "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) ISO=$1 ;; esac; shift; done
VM=$HOME/oweelinux-vm; mkdir -p "$VM"; DISK=$VM/disco.img
[ "$NUEVO" = 1 ] && rm -f "$DISK" "$VM"/vars-*.fd
[ -e "$DISK" ] || { truncate -s 20G "$DISK"; echo "disco virtual nuevo: $DISK (20 GB, ocupa solo lo que uses)"; }
if [ "$DISCO_SOLO" = 0 ]; then [ -f "$ISO" ] || { echo "Indica la ISO:  $0 OweeLinux-XXXX.iso   (o --disco para arrancar lo instalado)" >&2; exit 1; }; fi
command -v qemu-system-x86_64 >/dev/null || { echo "Falta QEMU: sudo apt install qemu-system-x86 ovmf" >&2; exit 1; }
FW=""; for d in /usr/share/OVMF /usr/share/edk2/ovmf /usr/share/qemu; do [ -f "$d/OVMF_CODE_4M.fd" ] && FW=$d && break; done
[ -n "$FW" ] || { echo "Falta el firmware UEFI: sudo apt install ovmf" >&2; exit 1; }
MSVARS=""; for f in "$FW/OVMF_VARS_4M.ms.fd" "$HOME/.cache/oweelinux/ovmf/OVMF_VARS_4M.ms.fd"; do [ -f "$f" ] && MSVARS=$f && break; done
if [ "$SB" = 1 ]; then [ -n "$MSVARS" ] || { echo "Secure Boot en QEMU necesita una plantilla de variables con las claves de Microsoft (OVMF_VARS_4M.ms.fd); no la encuentro." >&2; exit 1; }
  CODE=$FW/OVMF_CODE_4M.secboot.fd; TPL=$MSVARS; VARS=$VM/vars-sb.fd; MACH="q35,smm=on"; EXTRA="-global driver=cfi.pflash01,property=secure,value=on"
else CODE=$FW/OVMF_CODE_4M.fd; TPL=$FW/OVMF_VARS_4M.fd; VARS=$VM/vars.fd; MACH="q35"; EXTRA=""; fi
[ -f "$CODE" ] && [ -f "$TPL" ] || { echo "No encuentro los archivos de firmware ($CODE). Instala/actualiza: sudo apt install ovmf" >&2; exit 1; }
[ -f "$VARS" ] || cp "$TPL" "$VARS"
ACCEL="-enable-kvm -cpu host"; [ -w /dev/kvm ] || { echo "(sin KVM: irá lento)"; ACCEL="-accel tcg -cpu max"; }
CD=""; [ "$DISCO_SOLO" = 0 ] && CD="-device ich9-ahci,id=ahci -drive if=none,id=cd0,file=$ISO,media=cdrom,readonly=on -device ide-cd,drive=cd0,bus=ahci.0,bootindex=0"
echo "Arrancando OweeLinux en QEMU ($([ "$SB" = 1 ] && echo 'Secure Boot activado' || echo 'sin Secure Boot'), ${RAM} MB). Cierra la ventana para apagar."
# shellcheck disable=SC2086
exec qemu-system-x86_64 -name "OweeLinux" $ACCEL -smp "$CPUS" -m "$RAM" -machine "$MACH" $EXTRA \
  -display "${OWEE_DISPLAY:-gtk}" -device virtio-vga,xres=1280,yres=720 -device qemu-xhci -device usb-tablet -device usb-kbd \
  -drive if=pflash,format=raw,readonly=on,file="$CODE" -drive if=pflash,format=raw,file="$VARS" \
  $CD -drive if=none,id=hd0,file="$DISK",format=raw -device virtio-blk-pci,drive=hd0,bootindex=1 -nic user -audiodev none,id=a0
