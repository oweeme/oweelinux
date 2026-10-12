#!/usr/bin/env bash
# Fase B1 del branding: traslada la identidad de OweeLinux a un rootfs de ostree (ya preparado: /etc está en /usr/etc).
# Idempotente. Se ejecuta DENTRO del pod. Uso: overlay-branding.sh ROOTFS [REPO_ROOT]
set -euo pipefail
R=${1:?uso: $0 ROOTFS [REPO_ROOT]}; REPO=${2:-/work}
SRC=$REPO/livebuild-profile/config/includes.chroot_after_packages
[ -d "$SRC" ] || { echo "no encuentro $SRC" >&2; exit 1; }
ETC=$R/usr/etc; [ -d "$ETC" ] || { echo "el rootfs no está preparado para ostree (falta usr/etc)" >&2; exit 1; }

# 1. Identidad. En la imagen /etc/os-release es un enlace a ../usr/lib/os-release: se escribe el archivo real.
install -m0644 "$SRC/etc/os-release" "$R/usr/lib/os-release"
[ -L "$ETC/os-release" ] || { rm -f "$ETC/os-release"; ln -s ../usr/lib/os-release "$ETC/os-release"; }
for d in "$SRC"/usr/share/icons/hicolor/*/apps; do
  sz=$(basename "$(dirname "$d")"); mkdir -p "$R/usr/share/icons/hicolor/$sz/apps"
  install -m0644 "$d/distributor-logo-oweelinux.png" "$R/usr/share/icons/hicolor/$sz/apps/"
done

# 2. Fondos, colores, aspecto de Plasma, fondo de SDDM
for w in "$SRC"/usr/share/wallpapers/*; do rm -rf "$R/usr/share/wallpapers/$(basename "$w")"; cp -a "$w" "$R/usr/share/wallpapers/"; done
mkdir -p "$R/usr/share/backgrounds/oweelinux"; cp -a "$SRC/usr/share/backgrounds/oweelinux/." "$R/usr/share/backgrounds/oweelinux/"
install -m0644 "$SRC/usr/share/color-schemes/OweeLinux.colors" "$R/usr/share/color-schemes/OweeLinux.colors"
rm -rf "$R/usr/share/plasma/look-and-feel/org.oweelinux.desktop"; cp -a "$SRC/usr/share/plasma/look-and-feel/org.oweelinux.desktop" "$R/usr/share/plasma/look-and-feel/"
mkdir -p "$R/usr/share/sddm/themes/breeze"; install -m0644 "$SRC/usr/share/sddm/themes/breeze/theme.conf.user" "$R/usr/share/sddm/themes/breeze/theme.conf.user"
mkdir -p "$ETC/sddm.conf.d"; install -m0644 "$SRC/etc/sddm.conf.d/theme.conf" "$ETC/sddm.conf.d/20-owee-theme.conf"

# 3. Ajustes por defecto para TODOS los usuarios (/etc/xdg, no /etc/skel)
mkdir -p "$ETC/xdg"; install -m0644 "$SRC/etc/skel/.config/kdeglobals" "$ETC/xdg/kdeglobals"; install -m0644 "$SRC/etc/skel/.config/ksplashrc" "$ETC/xdg/ksplashrc"
install -m0644 "$SRC/etc/skel/.config/baloofilerc" "$ETC/xdg/baloofilerc"

# 4. Script de primer inicio (aplica fondo y colores con las herramientas de Plasma)
mkdir -p "$R/usr/libexec/oweelinux" "$ETC/xdg/autostart"
install -m0755 "$SRC/usr/local/bin/oweelinux-first-login" "$R/usr/libexec/oweelinux/oweelinux-first-login"
sed 's#/usr/local/bin/oweelinux-first-login#/usr/libexec/oweelinux/oweelinux-first-login#g' "$SRC/etc/xdg/autostart/oweelinux-first-login.desktop" > "$ETC/xdg/autostart/oweelinux-first-login.desktop"
echo "branding B1 aplicado a $R"
