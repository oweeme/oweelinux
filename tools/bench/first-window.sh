#!/usr/bin/env bash
# Mide el tiempo hasta que una app muestra su primera ventana (sesión X11).
# Uso: first-window.sh [-n REPETICIONES] [-t TIMEOUT_S] -- comando [args...]
# Ejemplo: first-window.sh -n 5 -- gimp
# Requiere: xdotool. Lanza el comando en su propio grupo de procesos y lo mata
# al terminar cada repetición. NO usar con apps que ya estén abiertas
# (instancia única): la medición no sería válida.
# Esto mide "caliente" (caché de disco ya cargada). Para "frío", antes de
# cada medición se necesita: sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
set -euo pipefail

N=3; TIMEOUT=40
while getopts "n:t:" o; do case $o in n) N=$OPTARG;; t) TIMEOUT=$OPTARG;; *) exit 1;; esac; done
shift $((OPTIND-1)); [ "${1:-}" = "--" ] && shift
[ $# -ge 1 ] || { sed -n 2,7p "$0"; exit 1; }
command -v xdotool >/dev/null || { echo "falta xdotool" >&2; exit 1; }

# Ventanas visibles que pertenecen al grupo de procesos lanzado ($1 = pgid).
# Se filtra por PID para no confundir ventanas de otros programas (avisos, popups).
group_wins() {
  local p
  for p in $(pgrep -g "$1" 2>/dev/null); do
    xdotool search --onlyvisible --pid "$p" 2>/dev/null
  done | sort -u
}

for i in $(seq 1 "$N"); do
  t0=$(date +%s%N)
  setsid "$@" >/dev/null 2>&1 &
  pid=$!
  found=""
  while :; do
    now=$(date +%s%N)
    if [ $(( (now - t0) / 1000000000 )) -ge "$TIMEOUT" ]; then break; fi
    new=$(group_wins "$pid" | head -1 || true)
    if [ -n "$new" ]; then found=$(( (now - t0) / 1000000 )); break; fi
    sleep 0.02
  done
  kill -- -"$pid" 2>/dev/null || true
  sleep 1.5
  if [ -n "$found" ]; then echo "$* run $i: ${found} ms"; else echo "$* run $i: sin ventana en ${TIMEOUT}s"; fi
done
