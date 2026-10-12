#!/usr/bin/env bash
# Abre la imagen de OweeLinux en una ventana de QEMU para VER el escritorio funcionando. Se ejecuta en el HOST.
# Uso: run-vm.sh DISCO.img [MiB_RAM] [CPUs]
# - El disco se abre con -snapshot: nada de lo que hagas dentro se guarda (se descarta al cerrar la ventana).
# - Usuario de prueba "oweeuser" (sin contraseña) con inicio de sesión automático.
# - Ratón: se captura al hacer clic en la ventana; para soltarlo, Ctrl+Alt+G. Cerrar la ventana apaga la VM.
# - Gráficos por software (sin GPU en la VM): irá más lento que en un equipo real.
# - SIN PROBAR: en la máquina de desarrollo actual el QEMU no trae los módulos de ventana (ui-gtk/sdl;
#   `qemu-system-x86_64 -display help` solo lista "none"), así que este script necesita un QEMU con GTK o SDL.
#   Alternativas: `tour.py` (capturas de pantalla) o un visor VNC con `-vnc`.
set -euo pipefail
DISK=${1:?uso: $0 DISCO.img [MiB_RAM] [CPUs]}; MEM=${2:-3072}; CPUS=${3:-2}
TMP=$HOME/.cache/oweelinux/tmp; mkdir -p "$TMP"; export TMPDIR=$TMP   # el overlay de -snapshot va al disco, no a la RAM
VARS=$(mktemp "$TMP/vars.XXXXXX"); cp /usr/share/OVMF/OVMF_VARS_4M.fd "$VARS"; trap 'rm -f "$VARS"' EXIT
exec qemu-system-x86_64 -name "OweeLinux (VM sin guardar cambios)" -enable-kvm -cpu host -smp "$CPUS" -m "$MEM" -machine q35 \
  -snapshot -display gtk,zoom-to-fit=off -device virtio-vga,xres=1280,yres=720 -device qemu-xhci -device usb-tablet -device usb-kbd \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file="$VARS" \
  -drive file="$DISK",format=raw,if=virtio -nic user
