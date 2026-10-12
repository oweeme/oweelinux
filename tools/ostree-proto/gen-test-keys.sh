#!/usr/bin/env bash
# CLAVES DE PRUEBA para verificar la firma de las actualizaciones. Se ejecuta DENTRO del pod.
# Crea dos claves sin contraseña en un directorio de GnuPG que NO está en el repositorio:
#   A = la "clave de OweeLinux" que la imagen de prueba considera de confianza
#   B = una clave ajena (para comprobar que se rechaza)
# Exporta SOLO la clave pública de A a tools/ostree-proto/keys/owee-test.gpg (formato binario, el que lee ostree).
# ⚠ La clave real de producción debe generarla el autor, con contraseña, y vivir fuera de línea. No usar estas.
# Uso: gen-test-keys.sh [DIR_GNUPG]   (por defecto /var/tmp/owee-gnupg)
set -euo pipefail
G=${1:-/var/tmp/owee-gnupg}; HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$G"; chmod 700 "$G"
for k in "OweeLinux TEST signing key A" "OweeLinux TEST untrusted key B"; do
  gpg --homedir "$G" --list-keys "$k" >/dev/null 2>&1 || \
    gpg --homedir "$G" --batch --pinentry-mode loopback --passphrase '' --quick-generate-key "$k" ed25519 sign never 2>/dev/null
done
mkdir -p "$HERE/keys"
gpg --homedir "$G" --export "OweeLinux TEST signing key A" > "$HERE/keys/owee-test.gpg"
echo "A=$(gpg --homedir "$G" --list-keys --with-colons "OweeLinux TEST signing key A" | awk -F: '/^fpr/{print $10; exit}')"
echo "B=$(gpg --homedir "$G" --list-keys --with-colons "OweeLinux TEST untrusted key B" | awk -F: '/^fpr/{print $10; exit}')"
