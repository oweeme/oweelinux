#!/usr/bin/env bash
# Descarga (o actualiza) el proyecto del idioma Owee (https://github.com/oweeme/owee, del mismo autor) y construye sus paquetes: fonts-owee, fcitx5-owee y owee-locale.
# Se ejecuta DENTRO del pod (necesita red, git, cmake, g++ y libfcitx5core-dev). Resultado: /var/tmp/owee-src (código) y /var/tmp/owee-debs/*.deb
# Uso: build-owee-debs.sh      (si falla, la imagen se construye igual, solo sin el idioma Owee)
set -uo pipefail
SRC=${OWEE_SRC:-/var/tmp/owee-src}; OUT=${OWEE_DEBS:-/var/tmp/owee-debs}
# Versión del proyecto del idioma que se usa: FIJA (los glifos finales, fuentes 3.4); OWEE_REF=main usa lo último, OWEE_REF=otra-etiqueta otra versión
OWEE_REF=${OWEE_REF-e7fe5d8a42d866e45ef8c4487ea77112a47a7483}
command -v git >/dev/null || { echo "build-owee-debs: falta git" >&2; exit 1; }
dpkg -s libfcitx5core-dev >/dev/null 2>&1 || apt-get install -y -qq libfcitx5core-dev cmake g++ pkg-config >/dev/null 2>&1 || { echo "build-owee-debs: no se pudo instalar libfcitx5core-dev" >&2; exit 1; }
# El clon es desechable: la construcción reescribe archivos versionados (paquetes/*.deb) y eso impediría el siguiente `git pull`; se descartan los cambios locales antes.
# OWEE_REF fija una etiqueta, rama o commit del proyecto del idioma (para construir SIEMPRE los mismos glifos); sin él se usa lo último de la rama principal.
if [ -d "$SRC/.git" ]; then git -C "$SRC" reset -q --hard && git -C "$SRC" clean -fdq 08_Integracion/linux 2>/dev/null; git -C "$SRC" fetch -q --tags --prune || true
else rm -rf "$SRC"; git clone -q https://github.com/oweeme/owee "$SRC" || exit 1; fi
if [ -n "${OWEE_REF:-}" ]; then git -C "$SRC" checkout -q "$OWEE_REF" || { echo "build-owee-debs: no existe OWEE_REF=$OWEE_REF" >&2; exit 1; }
else git -C "$SRC" checkout -q "$(git -C "$SRC" symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || echo main)" 2>/dev/null; git -C "$SRC" pull -q --ff-only || true; fi
( cd "$SRC/08_Integracion/linux" && ./build-debs.sh >/dev/null ) || exit 1
# El proyecto cambió el destino de los paquetes de dist/ a paquetes/: se usa el que se acaba de generar, nunca uno viejo
L=$SRC/08_Integracion/linux; D=$L/paquetes; [ -n "$(find "$L/paquetes" -name '*.deb' -newer "$L/build-debs.sh" 2>/dev/null)" ] || D=$L/dist
rm -rf "$OUT"; mkdir -p "$OUT"; find "$D" -name '*.deb' -mmin -30 -exec cp {} "$OUT"/ \;
[ -n "$(ls "$OUT"/*.deb 2>/dev/null)" ] || { echo "build-owee-debs: no se generó ningún paquete en $D" >&2; exit 1; }
echo "owee: $(ls "$OUT" | tr '\n' ' ') (commit $(git -C "$SRC" rev-parse --short HEAD))"
