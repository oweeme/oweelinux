#!/usr/bin/env bash
# Prepara un rootfs Debian (mmdebstrap) para ser commiteado en ostree.
# Se ejecuta DENTRO del pod. Uso: prepare-rootfs.sh /ruta/al/rootfs
# Requiere en el rootfs: ostree-boot, dracut-core, linux-image-*.
set -euo pipefail
R=${1:?uso: $0 ROOTFS}
KVER=$(ls "$R/usr/lib/modules" | head -1)
echo "kernel: $KVER"

# 1. Kernel + initramfs (hecho con dracut, que es lo que ostree-boot espera)
#    dentro de /usr/lib/modules/<kver>/, no en /boot.
mkdir -p "$R/proc" "$R/sys" "$R/dev"
install -m0644 "$R/boot/vmlinuz-$KVER" "$R/usr/lib/modules/$KVER/vmlinuz"
chroot "$R" dracut --force --no-hostonly --add ostree --kver "$KVER" \
    "/usr/lib/modules/$KVER/initramfs.img"
rm -rf "$R"/boot/* "$R"/var/lib/initramfs-tools

# 2. /var no va en el commit: se guarda la base de dpkg como registro y se vacía.
mkdir -p "$R/usr/share/owee"
[ -d "$R/var/lib/dpkg" ] && mv "$R/var/lib/dpkg" "$R/usr/share/owee/dpkg-db"
rm -rf "$R"/var/* "$R"/tmp/* "$R"/run/*

# 3. Enlaces estándar de ostree: lo escribible vive bajo /var.
for d in home:var/home root:var/roothome opt:var/opt srv:var/srv mnt:var/mnt; do
  n=${d%%:*}; t=${d#*:}
  rm -rf "${R:?}/$n"; ln -s "$t" "$R/$n"
done
rm -rf "$R/usr/local"; ln -s ../var/usrlocal "$R/usr/local"
rm -rf "$R/media"; ln -s run/media "$R/media"

# 3b. ostree mueve el sysroot real a /sysroot de la raíz nueva: debe existir en el árbol.
mkdir -p "$R/sysroot"; rm -rf "$R/ostree"; ln -s sysroot/ostree "$R/ostree"
rm -f "$R"/vmlinuz "$R"/vmlinuz.old "$R"/initrd.img "$R"/initrd.img.old   # enlaces heredados de Debian a /boot

# 4. Configuración mínima de prueba (imagen desechable, NO es la de producción)
: > "$R/etc/machine-id"
echo oweelinux-proto > "$R/etc/hostname"
mkdir -p "$R/etc/systemd/system/serial-getty@ttyS0.service.d"
cat > "$R/etc/systemd/system/serial-getty@ttyS0.service.d/autologin.conf" <<'EOC'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
EOC
rm -f "$R/etc/resolv.conf"; ln -s ../run/systemd/resolve/stub-resolv.conf "$R/etc/resolv.conf"

# 4b. Red por DHCP (systemd-networkd) y remoto de actualizaciones (SOLO prototipo:
#     sin firma GPG y por HTTP; en producción habrá firma y HTTPS).
mkdir -p "$R/etc/systemd/network" "$R/etc/ostree/remotes.d" "$R/etc/systemd/system/multi-user.target.wants"
printf '[Match]\nName=en*\n\n[Network]\nDHCP=yes\n' > "$R/etc/systemd/network/20-dhcp.network"
ln -sf /usr/lib/systemd/system/systemd-networkd.service \
   "$R/etc/systemd/system/multi-user.target.wants/systemd-networkd.service"
printf '[remote "owee"]\nurl=http://10.0.2.2:8000/pub\ngpg-verify=false\n' > "$R/etc/ostree/remotes.d/owee.conf"

# 4c. Herramientas del proyecto: generador del menú de arranque y actualizador.
HERE=$(cd "$(dirname "$0")" && pwd)
install -m0755 "$HERE/owee-bootcfg" "$HERE/owee-update" "$R/usr/bin/"

# 5. ostree espera la configuración en /usr/etc (el /etc de fábrica).
rm -rf "$R/usr/etc"; mv "$R/etc" "$R/usr/etc"; mkdir "$R/etc"
echo "rootfs listo para ostree commit"
