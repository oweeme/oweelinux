#!/usr/bin/env bash
# Descarga (o actualiza) el proyecto del idioma Owee (https://github.com/oweeme/owee, del mismo autor) y construye sus paquetes: fonts-owee, fcitx5-owee y owee-locale.
# Se ejecuta DENTRO del pod (necesita red, git, cmake, g++ y libfcitx5core-dev). Resultado: /var/tmp/owee-src (código) y /var/tmp/owee-debs/*.deb
# Uso: build-owee-debs.sh      (si falla, la imagen se construye igual, solo sin el idioma Owee)
set -uo pipefail
SRC=${OWEE_SRC:-/var/tmp/owee-src}; OUT=${OWEE_DEBS:-/var/tmp/owee-debs}
command -v git >/dev/null || { echo "build-owee-debs: falta git" >&2; exit 1; }
dpkg -s libfcitx5core-dev >/dev/null 2>&1 || apt-get install -y -qq libfcitx5core-dev cmake g++ pkg-config >/dev/null 2>&1 || { echo "build-owee-debs: no se pudo instalar libfcitx5core-dev" >&2; exit 1; }
if [ -d "$SRC/.git" ]; then git -C "$SRC" pull -q --ff-only || true; else rm -rf "$SRC"; git clone --depth 1 -q https://github.com/oweeme/owee "$SRC" || exit 1; fi
( cd "$SRC/08_Integracion/linux" && ./build-debs.sh >/dev/null ) || exit 1
rm -rf "$OUT"; mkdir -p "$OUT"; cp "$SRC"/08_Integracion/linux/dist/*.deb "$OUT"/
echo "owee: $(ls "$OUT" | tr '\n' ' ') (commit $(git -C "$SRC" rev-parse --short HEAD))"
