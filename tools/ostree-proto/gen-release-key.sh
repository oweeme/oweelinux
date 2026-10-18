#!/usr/bin/env bash
# Genera la clave REAL con la que se firman las actualizaciones de OweeLinux. Ejecútalo en TU máquina (no en el pod de construcción), con una contraseña larga.
# La clave privada se queda en tu llavero de GnuPG: guarda una copia CIFRADA fuera de línea (USB en un cajón) y NUNCA la subas al repositorio ni a un servidor de construcción.
# Exporta solo la clave pública a tools/ostree-proto/keys/oweelinux.gpg (la que la imagen considera de confianza). Uso: gen-release-key.sh
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); NAME="OweeLinux release signing key"
gpg --list-keys "$NAME" >/dev/null 2>&1 && { echo "Ya existe una clave «$NAME». Si quieres rotarla, revoca la anterior primero (docs/ACTUALIZACIONES.md)."; exit 1; }
gpg --quick-generate-key "$NAME" ed25519 sign 3y        # te pedirá la contraseña; caduca a los 3 años (renovable)
mkdir -p "$HERE/keys"; gpg --export "$NAME" > "$HERE/keys/oweelinux.gpg"
FPR=$(gpg --list-keys --with-colons "$NAME" | awk -F: '/^fpr/{print $10; exit}')
echo "Clave creada. Huella (publícala en tu web para que cualquiera pueda comprobarla): $FPR"
echo "Pública exportada en: $HERE/keys/oweelinux.gpg   (se incluye en la imagen al construir)"
echo "Copia de seguridad de la PRIVADA (cifrada): gpg --export-secret-keys --armor '$FPR' > oweelinux-privada.asc   → guárdala fuera de línea y bórrala del disco."
