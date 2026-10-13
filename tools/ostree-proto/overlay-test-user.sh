#!/usr/bin/env bash
# SOLO PARA PRUEBAS EN VM (nunca para una imagen real): crea el usuario "oweeuser" SIN contraseña y
# configura SDDM para entrar solo a una sesión de Plasma (X11). Se usa antes de mover /etc a /usr/etc.
# Sesión de inicio automático: OWEE_TEST_SESSION (por defecto plasmax11.desktop; owee-lite.desktop para ver el escritorio Lite).
# Uso: overlay-test-user.sh ROOTFS
set -euo pipefail
R=${1:?uso: $0 ROOTFS}
chroot "$R" id oweeuser >/dev/null 2>&1 || chroot "$R" useradd -M -d /home/oweeuser -u 1000 -s /bin/bash -G audio,video,netdev,plugdev oweeuser
chroot "$R" passwd -d oweeuser >/dev/null
mkdir -p "$R/etc/sddm.conf.d" "$R/usr/lib/tmpfiles.d"
printf '[Autologin]\nUser=oweeuser\nSession=%s\n\n[General]\nDisplayServer=x11\n' "${OWEE_TEST_SESSION:-plasmax11.desktop}" > "$R/etc/sddm.conf.d/10-owee-test.conf"
# SOLO PRUEBAS: el usuario de prueba (sin contraseña) puede hacer tareas de administrador por polkit (zona horaria, owee-update desde Ajustes...); una imagen real NO lleva esto
mkdir -p "$R/etc/polkit-1/rules.d"; printf 'polkit.addRule(function (action, subject) { if (subject.user == "oweeuser") return polkit.Result.YES; });\n' > "$R/etc/polkit-1/rules.d/49-owee-test.rules"
# /home es /var/home y /var nace vacío: el directorio personal se crea al arrancar.
printf 'd /var/home 0755 root root -\nd /var/home/oweeuser 0700 oweeuser oweeuser -\n' > "$R/usr/lib/tmpfiles.d/owee-test-user.conf"
echo "overlay-test-user: usuario oweeuser sin contraseña + autologin SDDM (SOLO PRUEBAS)"
