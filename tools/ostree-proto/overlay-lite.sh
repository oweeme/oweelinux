#!/usr/bin/env bash
# Instala en un rootfs ya preparado para ostree la sesión "OweeLinux Lite" (prototipo): archivo de sesión, arranque,
# configuración y tema de labwc, Waybar de comparación, el panel en Python y la prueba de lista de ventanas.
# Los enlaces de pywayland se generan AQUÍ (en el pod, que tiene la misma versión que la imagen).
# Uso: overlay-lite.sh ROOTFS [REPO_ROOT]
set -euo pipefail
R=${1:?uso: $0 ROOTFS [REPO_ROOT]}; REPO=${2:-/work}; D=$REPO/desktop
ETC=$R/usr/etc; [ -d "$ETC" ] || { echo "rootfs sin preparar" >&2; exit 1; }
install -Dm0644 "$D/session/owee-lite.desktop" "$R/usr/share/wayland-sessions/owee-lite.desktop"
for f in owee-session owee-lite-start; do install -Dm0755 "$D/session/$f" "$R/usr/libexec/owee/$f"; done
for f in owee_panel.py wl_toplevels.py; do install -Dm0755 "$D/shell/$f" "$R/usr/libexec/owee/$f"; done
install -Dm0644 "$D/session/labwc/rc.xml" "$ETC/xdg/labwc/rc.xml"; install -Dm0755 "$D/session/labwc/autostart" "$ETC/xdg/labwc/autostart"
# widgets del panel: los del sistema van en /usr/share/owee/widgets (el usuario los sustituye con un archivo del mismo nombre
# en ~/.config/owee/widgets); los ejemplos se dejan aparte para copiarlos y cambiarlos.
for f in "$D"/widgets/sistema/*; do install -Dm0755 "$f" "$R/usr/share/owee/widgets/$(basename "$f")"; done
for f in "$D"/widgets/ejemplos/*; do install -Dm0755 "$f" "$R/usr/share/owee/widgets-ejemplos/$(basename "$f")"; done
install -Dm0644 "$D/theme/themerc" "$R/usr/share/themes/Owee/openbox-3/themerc"
install -Dm0644 "$D/waybar/config.jsonc" "$ETC/xdg/waybar/config.jsonc"; install -Dm0644 "$D/waybar/style.css" "$ETC/xdg/waybar/style.css"
# Debian instala waybar.service y mako.service (usuario) y arrancan solos con la sesión gráfica: la sesión Lite
# controla sus piezas ella misma, así que se enmascaran (si no, hay dos paneles y dos demonios de notificaciones).
mkdir -p "$ETC/systemd/user"; for u in waybar.service mako.service; do ln -sfn /dev/null "$ETC/systemd/user/$u"; done
rm -rf "$R/usr/lib/owee/wlgen"; mkdir -p "$R/usr/lib/owee/wlgen"
python3 -m pywayland.scanner -o "$R/usr/lib/owee/wlgen" -i \
  /usr/share/wayland-protocols/staging/ext-foreign-toplevel-list/ext-foreign-toplevel-list-v1.xml 2>&1 | tail -1
echo "sesión Lite instalada en $R"
