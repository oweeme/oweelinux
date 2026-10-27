#!/bin/bash
# owee-diag.sh — recoge información para diagnosticar lentitud o reinicios en OweeLinux.
# SOLO LEE: no cambia nada en el sistema. Guarda el resultado en ~/owee-diag-FECHA.txt (revísalo antes de compartirlo: lleva tu nombre de usuario y el nombre del equipo).
# Úsalo MIENTRAS el equipo esté lento (con las aplicaciones abiertas) y, si hubo un reinicio raro, justo después de arrancar.
OUT="$HOME/owee-diag-$(date +%Y%m%d-%H%M).txt"
s() { printf '\n===== %s =====\n' "$1" >> "$OUT"; }
r() { s "$*"; timeout 20 "$@" >> "$OUT" 2>&1 || echo "(falló o no existe: $*)" >> "$OUT"; }
sh_() { s "$1"; timeout 20 sh -c "$1" >> "$OUT" 2>&1 || echo "(falló)" >> "$OUT"; }
: > "$OUT"
echo "OweeLinux diagnóstico — $(date)" >> "$OUT"
r uname -a
sh_ 'cat /etc/os-release | head -3; cat /proc/cmdline'
sh_ 'ostree admin status 2>/dev/null | head -8'
r uptime
r free -m
sh_ 'cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io 2>/dev/null'
sh_ 'swapon --show; zramctl 2>/dev/null'
sh_ 'ps -eo pid,user,pcpu,pmem,rss,etime,args --sort=-pcpu | head -25 | cut -c1-170'
sh_ 'ps -eo pid,user,pcpu,pmem,rss,etime,args --sort=-rss | head -20 | cut -c1-170'
sh_ 'top -b -n 1 -w 170 | head -15'
sh_ 'iostat -x 1 2 2>/dev/null | tail -12 || cat /proc/diskstats | head -5'
sh_ 'cat /sys/block/*/queue/scheduler 2>/dev/null | head -5; for d in /sys/block/sd* /sys/block/nvme*; do [ -e "$d" ] && echo "$d rot=$(cat $d/queue/rotational)"; done'
s "CPU: gobernador, frecuencia, temperatura"
for c in /sys/devices/system/cpu/cpu[0-9]*/cpufreq; do echo "$c $(cat $c/scaling_driver 2>/dev/null) $(cat $c/scaling_governor 2>/dev/null) cur=$(cat $c/scaling_cur_freq 2>/dev/null) max=$(cat $c/scaling_max_freq 2>/dev/null)" >> "$OUT"; done
for t in /sys/class/thermal/thermal_zone*; do echo "$(cat $t/type 2>/dev/null) $(( $(cat $t/temp 2>/dev/null || echo 0) / 1000 ))C" >> "$OUT"; done
sh_ 'grep -E "MHz|model name" /proc/cpuinfo | head -8'
sh_ 'for b in /sys/class/power_supply/*; do echo "$b: $(cat $b/status 2>/dev/null) $(cat $b/capacity 2>/dev/null)%"; done'
s "Gráficos"
sh_ 'ls /sys/class/drm | head; lsmod | grep -E "amdgpu|radeon|i915|nouveau|nvidia" | head'
sh_ 'journalctl -b -k --no-pager 2>/dev/null | grep -iE "amdgpu|drm|firmware|gpu" | tail -25 | cut -c1-200'
sh_ 'env | grep -E "WLR_|WAYLAND|XDG_SESSION|LD_PRELOAD|GDK_|QT_" | sort'
sh_ 'ps -eo args | grep -E "labwc|owee_panel|baloo|kactivit|plasma|kded|akonadi|tracker" | grep -v grep | cut -c1-140'
s "Registro del sistema: ¿se conserva entre reinicios?"
sh_ 'ls -ld /var/log/journal 2>/dev/null || echo "NO hay /var/log/journal: el registro se pierde al reiniciar"; journalctl --list-boots 2>/dev/null | tail -6; journalctl --disk-usage 2>/dev/null'
s "ARRANQUE ANTERIOR (errores graves; si dice 'no persistent journal' el registro no sobrevivió)"
sh_ 'journalctl -b -1 -p 3 --no-pager 2>&1 | tail -60 | cut -c1-220'
sh_ 'journalctl -b -1 --no-pager 2>&1 | tail -40 | cut -c1-220'
s "ARRANQUE ACTUAL: errores"
sh_ 'journalctl -b -p 3 --no-pager 2>&1 | tail -60 | cut -c1-220'
sh_ 'journalctl -b --no-pager 2>&1 | grep -iE "oom|out of memory|earlyoom|killed process|segfault|labwc|core dump|thermal|throttl|hung task|blocked for" | tail -30 | cut -c1-220'
sh_ 'coredumpctl list --no-pager 2>/dev/null | tail -10 || echo "(sin coredumps o coredumpctl no existe)"'
sh_ 'systemctl --failed --no-pager 2>&1 | head -15'
sh_ 'systemd-analyze 2>&1; systemd-analyze blame 2>&1 | head -15'
sh_ 'systemctl status earlyoom --no-pager 2>&1 | head -8; journalctl -u earlyoom -b --no-pager 2>/dev/null | tail -8 | cut -c1-200'
sh_ 'dmesg 2>/dev/null | tail -30 | cut -c1-200 || echo "(dmesg requiere permisos; el registro del núcleo está arriba)"'
s "MEMORIA en detalle (quién ocupa lo «compartido» y lo que no son procesos)"
sh_ 'grep -E "^(MemTotal|MemAvailable|Cached|Shmem|AnonPages|Mapped|Slab|SReclaimable|SUnreclaim|KernelStack|PageTables|Unevictable|Mlocked|Percpu|VmallocUsed|Zswap|SwapTotal|SwapFree):" /proc/meminfo'
sh_ 'cat /proc/swaps; for z in /sys/block/zram*; do echo "$z disksize=$(cat $z/disksize) mm_stat(orig comprim usado ...)=$(cat $z/mm_stat)"; done'
sh_ 'df -h /tmp /dev/shm /run/user/$(id -u) 2>/dev/null; du -sh /tmp/owee-rec-* /dev/shm/* 2>/dev/null | sort -h | tail -8'
sh_ 'echo "memfd abiertos (todos los procesos que puedo ver): $(ls -l /proc/[0-9]*/fd 2>/dev/null | grep -c memfd)"'
s "Procesos con más memoria COMPARTIDA (RssShmem) y ANÓNIMA (RssAnon), en MB"
sh_ 'for d in /proc/[0-9]*; do awk -v p="${d#/proc/}" "/^Name:/{n=\$2} /^RssShmem:/{s=\$2} /^RssAnon:/{a=\$2} END{if(s+a>0) printf \"%d %d %d %s\n\", s/1024, a/1024, p, n}" $d/status 2>/dev/null; done | sort -rn | head -15 | awk "BEGIN{print \"shmem_MB anon_MB pid nombre\"}{print}"'
sh_ 'for d in /proc/[0-9]*; do awk -v p="${d#/proc/}" "/^Name:/{n=\$2} /^RssAnon:/{a=\$2} END{if(a>0) printf \"%d %s %s\n\", a/1024, p, n}" $d/status 2>/dev/null; done | sort -rn | head -10 | awk "BEGIN{print \"anon_MB pid nombre\"}{print}"'
s "Memoria de la GPU (en este equipo comparte la RAM)"
sh_ 'for c in /sys/class/drm/card*/device; do [ -f $c/mem_info_gtt_used ] && echo "$c: GTT usado=$(( $(cat $c/mem_info_gtt_used) / 1048576 ))MB de $(( $(cat $c/mem_info_gtt_total) / 1048576 ))MB · VRAM usada=$(( $(cat $c/mem_info_vram_used) / 1048576 ))MB de $(( $(cat $c/mem_info_vram_total) / 1048576 ))MB"; done'
sh_ 'for d in /proc/[0-9]*; do g=0; for f in $d/fdinfo/*; do v=$(sed -n "s/^drm-memory-gtt:[[:space:]]*\([0-9]*\).*/\1/p" $f 2>/dev/null | head -1); [ -n "$v" ] && g=$((g + v)); done; [ "$g" -gt 0 ] && echo "$((g / 1024)) MB-GTT pid=${d#/proc/} $(cat $d/comm 2>/dev/null)"; done 2>/dev/null | sort -rn | head -10'
sh_ 'P=$(pgrep -x labwc | head -1); [ -n "$P" ] && tr "\0" "\n" < /proc/$P/environ 2>/dev/null | grep -E "^(WLR_|GSK_|LIBVA|MESA)" ; ls -l /dev/dri 2>/dev/null'
s "Crecimiento en 15 s (si Shmem sube, anota cuánto)"
sh_ 'for i in 1 2 3; do date +%T; grep -E "^(MemAvailable|Shmem|AnonPages):" /proc/meminfo | tr "\n" " "; echo; sleep 5; done'
s "Ratón / touchpad"
sh_ 'grep -E "^N: Name|^H: Handlers" /proc/bus/input/devices | paste - - | grep -iE "mouse|touchpad|synaptics|elan|pointer" | cut -c1-200'
sh_ 'libinput list-devices 2>/dev/null | grep -E "Device:|Capabilities|Accel|Tap" | head -24'
s "Procesos de Owee"
sh_ 'ps -eo pid,pcpu,rss,args | grep -E "owee|foot|ffmpeg|wf-recorder|capturadora|cámara|camera" | grep -v grep | cut -c1-170'
echo >> "$OUT"; echo "Listo. Archivo: $OUT"
echo "Listo: $OUT ($(wc -c < "$OUT") bytes). Revísalo y llévalo al otro ordenador."
