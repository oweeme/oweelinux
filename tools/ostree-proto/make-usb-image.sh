#!/usr/bin/env bash
# Prepara la IMAGEN DE INSTALACIÓN PARA USB: toma el disk.img de una construcción con OWEE_INSTALLER=1, lo comprime (xz) y escribe la suma de comprobación y las instrucciones.
# Se ejecuta en el HOST. Uso: make-usb-image.sh DISK.img [DESTINO]      (DESTINO por defecto: ~/oweelinux-dist)
set -euo pipefail
IMG=${1:?uso: $0 DISK.img [DESTINO]}; OUT=${2:-$HOME/oweelinux-dist}; N=OweeLinux-instalador-$(date +%Y%m%d)
mkdir -p "$OUT"; echo "comprimiendo (unos minutos)…"
xz -T0 -6 -c "$IMG" > "$OUT/$N.img.xz"; (cd "$OUT" && sha256sum "$N.img.xz" > "$N.img.xz.sha256")
cat > "$OUT/LEEME-$N.txt" <<TXT
OweeLinux — imagen de instalación para USB  ($N)

QUÉ ES   Un USB que arranca directo al instalador de OweeLinux (UEFI). NO es una ISO en vivo: no hay modo de prueba sin instalar.
REQUISITOS  Equipo con UEFI y Secure Boot DESACTIVADO (en la BIOS). USB de 8 GB o más (se borra por completo; la imagen ocupa unos 5 GB descomprimida). Mínimo 2 GB de RAM y 20 GB de disco.

1) Comprobar la descarga:   sha256sum -c $N.img.xz.sha256
2) Averiguar cuál es el USB:  lsblk -o NAME,SIZE,MODEL,TRAN      (el USB muestra TRAN=usb; EQUIVOCARSE DE DISCO BORRA LOS DATOS DEL OTRO DISCO)
3) Grabarlo con el script de seguridad (cambia sdX por el USB, sin número; solo graba en USB, sin nada montado y con espacio suficiente):
     ./write-usb.sh /dev/sdX $N.img.xz
   (no copies «sdX» tal cual: es un ejemplo; si el nombre no existe, el script se niega)
4) Arrancar el equipo desde el USB (tecla F12 / F9 / Esc al encender, según la marca) y elegir «UEFI: …USB…».
5) En el instalador: si ya hay un OweeLinux, ofrece reinstalar conservando tus archivos; si no, puedes elegir una partición existente como /home (sin formatear) y después el disco donde instalar (se BORRA por completo).
6) Al reiniciar, quita el USB: el asistente de primer arranque crea tu usuario.

Si algo falla (pantalla negra, no arranca, el disco no aparece), anota el modelo del equipo y qué viste: sirve para corregirlo.
TXT
cp "$(dirname "$0")/write-usb.sh" "$OUT/"; ls -la "$OUT"
