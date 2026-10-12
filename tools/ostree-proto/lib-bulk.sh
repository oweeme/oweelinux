# Genera una "carga" de datos aleatorios dentro de un árbol, para que una actualización de prueba se
# parezca más a una real (muchos archivos pequeños + algunos grandes). Se usa con `source`.
# bulk_payload ARBOL ETIQUETA N_PEQUEÑOS MB_GRANDES N_GRANDES
# Los archivos van en usr/share/owee/bulk/ETIQUETA/ y NO afectan al funcionamiento del sistema.
bulk_payload() {
  local root=$1 tag=$2 small=$3 bigmb=$4 bign=$5 d i
  d="$root/usr/share/owee/bulk/$tag"; mkdir -p "$d"
  for i in $(seq 1 "$small"); do head -c $((1024 + RANDOM % 7168)) /dev/urandom > "$d/f$i"; done
  for i in $(seq 1 "$bign"); do head -c "${bigmb}M" /dev/urandom > "$d/big$i"; done
  chmod 0755 "$root/usr/share/owee/bulk" "$d" 2>/dev/null || true
}
