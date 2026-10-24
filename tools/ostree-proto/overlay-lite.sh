#!/usr/bin/env bash
# Instala en un rootfs ya preparado para ostree la sesión "OweeLinux Lite" (prototipo): archivo de sesión, arranque,
# configuración y tema de labwc, Waybar de comparación, el panel en Python y la prueba de lista de ventanas.
# Los enlaces de pywayland se generan AQUÍ (en el pod, que tiene la misma versión que la imagen).
# Uso: overlay-lite.sh ROOTFS [REPO_ROOT]
set -euo pipefail
R=${1:?uso: $0 ROOTFS [REPO_ROOT]}; REPO=${2:-/work}; D=$REPO/desktop
ETC=$R/usr/etc; [ -d "$ETC" ] || { echo "rootfs sin preparar" >&2; exit 1; }
install -Dm0644 "$D/session/owee-lite.desktop" "$R/usr/share/wayland-sessions/owee-lite.desktop"
for f in owee-session owee-lite-start owee-wallpaper owee-apply-display owee-idle owee-desktop owee-store-setup owee-apply-theme owee-layout owee-lock owee-screensaver owee-account-helper owee-avatar-helper owee-firstboot owee-setup-session owee-setup-run owee-locale owee-installer-session owee-installer-run owee-installer-calamares owee-run-labwc owee-apt-shim owee-panel-run owee-firewall owee-centinela owee-centinela-ctl owee-dev; do install -Dm0755 "$D/session/$f" "$R/usr/libexec/owee/$f"; done
for f in owee_panel.py wl_toplevels.py owee_tray.py owee_theme.py owee_config.py owee_i18n.py owee_windows.py owee_overview.py owee_switcher.py owee_desktops.py owee_keys.py owee_koi.py owee_icons.py owee_settings.py $(cd "$D/shell" && ls ajustes/*.py); do install -Dm0755 "$D/shell/$f" "$R/usr/libexec/owee/$f"; done
install -Dm0644 "$D/session/mako/config" "$ETC/xdg/mako/config"; install -Dm0644 "$D/session/labwc/menu.xml" "$ETC/xdg/labwc/menu.xml"; install -Dm0644 "$D/session/labwc/rc.xml" "$ETC/xdg/labwc/rc.xml"; install -Dm0755 "$D/session/labwc/autostart" "$ETC/xdg/labwc/autostart"
# widgets del panel: los del sistema van en /usr/share/owee/widgets (el usuario los sustituye con un archivo del mismo nombre
# en ~/.config/owee/widgets); los ejemplos se dejan aparte para copiarlos y cambiarlos.
for f in "$D"/widgets/sistema/*; do install -Dm0755 "$f" "$R/usr/share/owee/widgets/$(basename "$f")"; done
install -Dm0644 "$D/session/org.oweelinux.accounts.policy" "$R/usr/share/polkit-1/actions/org.oweelinux.accounts.policy"      # Ajustes → Usuarios/Acceso: pkexec pide la clave de administrador
install -Dm0644 "$D/session/org.oweelinux.avatar.policy" "$R/usr/share/polkit-1/actions/org.oweelinux.avatar.policy"      # cambiar la propia foto no pide clave de administrador
mkdir -p "$R/usr/share/owee/avatars"; cp "$D"/theme/avatars/*.png "$R/usr/share/owee/avatars/"
# Primer arranque (docs/EXTENSIONES.md → Primer arranque): sesión propia de SDDM con el asistente, usuario de sistema `owee-setup`, regla polkit y servicio que decide cada arranque
install -Dm0644 "$D/session/labwc-setup/rc.xml" "$R/usr/share/owee/labwc-setup/rc.xml"; install -Dm0644 "$D/session/labwc-setup/autostart" "$R/usr/share/owee/labwc-setup/autostart"
# Fcitx5 por defecto (también para usuarios nuevos): sin icono propio en la bandeja (lo reemplaza el indicador del panel) y sin avisos (el de «Wayland Diagnose» no aplica con labwc)
printf '[Behavior]\nDisabledAddons=notificationitem,notifications\n' | install -Dm0644 /dev/stdin "$ETC/xdg/fcitx5/config"
# Reproductor de vídeo y música por defecto: mpv (ligero; con controles en pantalla al abrirlo desde el lanzador o desde Dolphin), para las grabaciones de la Capturadora y cualquier archivo multimedia
{ echo "[Default Applications]"; for t in video/mp4 video/x-matroska video/webm video/quicktime video/x-msvideo video/mpeg video/ogg video/x-flv video/3gpp audio/mpeg audio/mp4 audio/ogg audio/flac audio/x-wav audio/webm audio/aac audio/opus; do echo "$t=mpv.desktop"; done; echo "application/vnd.debian.binary-package=owee-dev-deb.desktop"; for t in text/plain text/markdown text/x-markdown text/css text/xml application/xml application/json application/x-shellscript text/x-python text/x-script.python text/x-csrc text/x-chdr text/x-c++src text/x-java text/javascript application/javascript text/x-log text/x-makefile text/x-readme text/x-go text/x-rust application/x-yaml text/yaml application/toml; do echo "$t=org.kde.kate.desktop"; done; echo "inode/directory=org.kde.dolphin.desktop"; for t in application/vnd.openxmlformats-officedocument.wordprocessingml.document application/msword application/vnd.oasis.opendocument.text application/rtf; do echo "$t=libreoffice-writer.desktop"; done; for t in application/vnd.openxmlformats-officedocument.spreadsheetml.sheet application/vnd.ms-excel application/vnd.oasis.opendocument.spreadsheet text/csv; do echo "$t=libreoffice-calc.desktop"; done; for t in application/vnd.openxmlformats-officedocument.presentationml.presentation application/vnd.ms-powerpoint application/vnd.oasis.opendocument.presentation; do echo "$t=libreoffice-impress.desktop"; done; for t in x-scheme-handler/http x-scheme-handler/https text/html application/xhtml+xml; do echo "$t=org.kde.falkon.desktop"; done; } | install -Dm0644 /dev/stdin "$ETC/xdg/mimeapps.list"
# Instalador (Calamares): scripts, configuración y marca. Solo se activa en el medio de instalación (marca en /var, ver build.sh); si falta el paquete calamares, no se instala nada.
if [ "${OWEE_INSTALLER:-0}" = 1 ]; then
  install -Dm0755 "$D/installer/owee-install-deploy" "$R/usr/libexec/owee/installer/owee-install-deploy"; install -Dm0755 "$D/installer/owee-install-disk" "$R/usr/libexec/owee/installer/owee-install-disk"
  for f in owee-reinstall owee-install-efi owee-installer-scan owee-installer-sethome owee_install_choice.py; do install -Dm0755 "$D/installer/$f" "$R/usr/libexec/owee/installer/$f"; done
  install -Dm0644 "$D/session/owee-installer.desktop" "$R/usr/share/wayland-sessions/owee-installer.desktop"
  for f in settings.conf; do install -Dm0644 "$D/installer/calamares/$f" "$ETC/calamares/$f"; done          # /etc/calamares: la ubicación normal de Calamares (con -c exigiría su propia carpeta qml/)
  for f in welcome partition finished shellprocess-oweedeploy; do install -Dm0644 "$D/installer/calamares/$f.conf" "$ETC/calamares/modules/$f.conf"; done
  for f in branding.desc show.qml owee-logo.png owee-welcome.png; do install -Dm0644 "$D/installer/calamares/branding/oweelinux/$f" "$ETC/calamares/branding/oweelinux/$f"; done
fi
# Tienda de apps = Discover (KDE) solo con el backend de Flatpak (sin PackageKit/apt: el sistema es inmutable); lanzador propio y el de KDE oculto
install -Dm0644 /dev/stdin "$R/usr/share/applications/owee-store.desktop" <<'EOD'
[Desktop Entry]
Type=Application
Name=Tienda de apps
Name[en]=App store
Comment=Instala y quita aplicaciones (Flathub)
Exec=plasma-discover --backends flatpak-backend %U
Icon=plasmadiscover
Categories=System;PackageManager;
StartupWMClass=org.kde.discover
EOD
# NVIDIA privativo (solo si la imagen se construyó con OWEE_NVIDIA=1): Wayland necesita el modo KMS del módulo
if [ "${OWEE_NVIDIA:-0}" = 1 ]; then printf 'options nvidia-drm modeset=1 fbdev=1\n' | install -Dm0644 /dev/stdin "$ETC/modprobe.d/owee-nvidia.conf"; fi
install -Dm0755 "$D/setup/owee_setup.py" "$R/usr/libexec/owee/setup/owee_setup.py"
install -Dm0644 "$D/session/owee-setup.desktop" "$R/usr/share/wayland-sessions/owee-setup.desktop"
install -Dm0644 "$D/session/owee-setup.sysusers" "$R/usr/lib/sysusers.d/owee-setup.conf"; install -Dm0644 "$D/session/owee-setup.tmpfiles" "$R/usr/lib/tmpfiles.d/owee-setup.conf"
install -Dm0644 "$D/session/49-owee-setup.rules" "$R/usr/share/polkit-1/rules.d/49-owee-setup.rules"
install -Dm0644 "$D/session/owee-firstboot.service" "$R/usr/lib/systemd/system/owee-firstboot.service"
mkdir -p "$R/usr/lib/systemd/system/sysinit.target.wants"; ln -sf ../owee-firstboot.service "$R/usr/lib/systemd/system/sysinit.target.wants/owee-firstboot.service"
for f in "$D"/widgets/ejemplos/*; do install -Dm0755 "$f" "$R/usr/share/owee/widgets-ejemplos/$(basename "$f")"; done
mkdir -p "$R/usr/share/owee/koi"; cp "$D"/theme/koi/*.png "$R/usr/share/owee/koi/"      # kois del bloqueo animado
for v in 3.0 4.0; do printf '[Settings]\ngtk-decoration-layout=appmenu:minimize,maximize,close\n' | install -Dm0644 /dev/stdin "$ETC/xdg/gtk-$v/settings.ini"; done      # botones de minimizar y maximizar en las apps GTK que dibujan su propia barra de título
install -Dm0644 "$D/../docs/CREAR_WIDGETS.md" "$R/usr/share/doc/oweelinux/CREAR_WIDGETS.md"; install -Dm0644 "$D/../docs/EXTENSIONES.md" "$R/usr/share/doc/oweelinux/EXTENSIONES.md"      # guía para crear widgets y apps
python3 "$D/theme/icons/gen_icons.py" "$R/usr/share/icons" >/dev/null; python3 "$D/theme/icons/gen_icons.py" "$R/usr/share/icons" "#17231e" Owee-Light >/dev/null
install -Dm0644 "$D/theme/themerc" "$R/usr/share/themes/Owee/openbox-3/themerc"; install -Dm0644 "$D/theme/themerc-light" "$R/usr/share/themes/Owee-Light/openbox-3/themerc"
install -Dm0644 "$D/waybar/config.jsonc" "$ETC/xdg/waybar/config.jsonc"; install -Dm0644 "$D/waybar/style.css" "$ETC/xdg/waybar/style.css"
# Debian instala waybar.service y mako.service (usuario) y arrancan solos con la sesión gráfica: la sesión Lite
# controla sus piezas ella misma, así que se enmascaran (si no, hay dos paneles y dos demonios de notificaciones).
mkdir -p "$ETC/systemd/user"; for u in waybar.service mako.service; do ln -sfn /dev/null "$ETC/systemd/user/$u"; done
rm -rf "$R/usr/lib/owee/wlgen"; mkdir -p "$R/usr/lib/owee/wlgen"
python3 -m pywayland.scanner -o "$R/usr/lib/owee/wlgen" -i \
  /usr/share/wayland-protocols/staging/ext-foreign-toplevel-list/ext-foreign-toplevel-list-v1.xml 2>&1 | tail -1
# Estado de ventanas (wlr-foreign-toplevel-management): el XML va en el repositorio (Debian no lo trae); necesita wayland.xml y se importa como paquete «wlgen.…»
python3 -m pywayland.scanner -o "$R/usr/lib/owee/wlgen" -i /usr/share/wayland/wayland.xml "$D/shell/protocols/wlr-foreign-toplevel-management-unstable-v1.xml" 2>&1 | tail -1
touch "$R/usr/lib/owee/wlgen/__init__.py"
chroot "$R" localedef -i es_ES -f UTF-8 es_ES.UTF-8 2>/dev/null || echo "(aviso: sin locale es_ES)"   # escribe en /usr/lib/locale (la parte inmutable)
# Calculadora propia (desktop/apps/calculadora) + icono + lanzador
for f in "$D"/apps/calculadora/*.py; do case "$(basename "$f")" in test_*) continue;; esac; install -Dm0755 "$f" "$R/usr/libexec/owee/apps/calculadora/$(basename "$f")"; done      # todos los módulos (owee_calc, calc_engine, calc_owee…)
install -Dm0644 "$R/usr/share/icons/Owee/scalable/actions/owee-calc.svg" "$R/usr/share/icons/hicolor/scalable/apps/owee-calc.svg"
install -Dm0644 /dev/stdin "$R/usr/share/applications/owee-calc.desktop" <<'EOD'
[Desktop Entry]
Type=Application
Name=Calculadora
GenericName=Calculadora
Comment=Calculadora con modo científico e historial
Exec=/usr/libexec/owee/apps/calculadora/owee_calc.py
Icon=owee-calc
Categories=Utility;Calculator;
Keywords=calculadora;suma;matemáticas;
EOD
# Calendario propio (desktop/apps/calendario): vista mensual, eventos y avisos (los lanza el panel)
install -Dm0755 "$D/apps/calendario/owee_calendar.py" "$R/usr/libexec/owee/apps/calendario/owee_calendar.py"
install -Dm0644 "$R/usr/share/icons/Owee/scalable/actions/owee-calendar.svg" "$R/usr/share/icons/hicolor/scalable/apps/owee-calendar.svg"
install -Dm0644 /dev/stdin "$R/usr/share/applications/owee-calendar.desktop" <<'EOD'
[Desktop Entry]
Type=Application
Name=Calendario
GenericName=Calendario
Comment=Calendario con eventos y avisos
Exec=/usr/libexec/owee/apps/calendario/owee_calendar.py
Icon=owee-calendar
Categories=Office;Calendar;
Keywords=calendario;agenda;eventos;fecha;
EOD
# Monitor del sistema propio (procesos, CPU, memoria; «Forzar cierre» para lo que se cuelga). Atajo Ctrl+Mayús+Esc
install -Dm0755 "$D/apps/monitor/owee_monitor.py" "$R/usr/libexec/owee/apps/monitor/owee_monitor.py"
install -Dm0644 /dev/stdin "$R/usr/share/applications/owee-monitor.desktop" <<'EOD'
[Desktop Entry]
Type=Application
Name=Monitor del sistema
GenericName=Monitor del sistema
Comment=Procesos, CPU y memoria; cerrar lo que se cuelga
Exec=/usr/libexec/owee/apps/monitor/owee_monitor.py
Icon=utilities-system-monitor
Categories=System;Monitor;
Keywords=procesos;tareas;memoria;cpu;matar;colgado;monitor;
EOD
# Capturadora propia (reemplaza a Spectacle): capturas con editor, vídeo con audio y cámara, modo presentación
for f in "$D"/apps/capturadora/*.py; do install -Dm0755 "$f" "$R/usr/libexec/owee/apps/capturadora/$(basename "$f")"; done
install -Dm0644 "$R/usr/share/icons/Owee/scalable/actions/owee-capture.svg" "$R/usr/share/icons/hicolor/scalable/apps/owee-capture.svg"
install -Dm0644 /dev/stdin "$R/usr/share/applications/owee-capture.desktop" <<'EOD'
[Desktop Entry]
Type=Application
Name=Capturadora
GenericName=Captura y grabación de pantalla
Comment=Capturas con editor, grabación de vídeo con audio y cámara, modo presentación
Exec=/usr/libexec/owee/apps/capturadora/owee_capture.py
Icon=owee-capture
Categories=Utility;AudioVideo;Recorder;
Keywords=captura;pantalla;grabar;video;screenshot;recorder;
Actions=Shot;Region;Record;Present;
[Desktop Action Shot]
Name=Capturar pantalla completa
Exec=/usr/libexec/owee/apps/capturadora/owee_capture.py --shot full
[Desktop Action Region]
Name=Capturar una zona
Exec=/usr/libexec/owee/apps/capturadora/owee_capture.py --shot region
[Desktop Action Record]
Name=Grabar pantalla
Exec=/usr/libexec/owee/apps/capturadora/owee_capture.py --record full
[Desktop Action Present]
Name=Modo presentación
Exec=/usr/libexec/owee/apps/capturadora/owee_capture.py --present
EOD
# Apps de KDE que OweeLinux reemplaza con las propias: se ocultan del lanzador (siguen instaladas por si otra app las llama)
for f in org.kde.systemsettings.desktop kdesystemsettings.desktop systemsettings.desktop org.kde.kinfocenter.desktop org.kde.kcalc.desktop org.kde.spectacle.desktop org.kde.discover.desktop org.kde.discover.urlhandler.desktop org.kde.discover.notifier.desktop org.kde.discover.flatpak.desktop foot-server.desktop footclient.desktop fcitx5-configtool.desktop fcitx5-wayland-launcher.desktop org.fcitx.Fcitx5.desktop org.fcitx.fcitx5-qt6-gui-wrapper.desktop; do [ -f "$R/usr/share/applications/$f" ] && sed -i '/^NoDisplay=/d; /^\[Desktop Entry\]/a NoDisplay=true' "$R/usr/share/applications/$f"; done
# ---- Idiomas: catálogos de la interfaz, locales del sistema, fuentes y teclados (docs/EXTENSIONES.md → Idiomas)
install -d "$R/usr/share/owee/i18n"; cp "$D"/i18n/*.json "$R/usr/share/owee/i18n/"
for l in es_ES en_US pt_BR fr_FR de_DE it_IT ru_RU uk_UA zh_CN ja_JP ko_KR ar_SA fa_IR hi_IN ur_PK id_ID ms_MY pl_PL fi_FI sv_SE; do chroot "$R" localedef -i "$l" -f UTF-8 "$l.UTF-8" 2>/dev/null || echo "(aviso: sin locale $l)"; done
# Nombres de nuestras apps en cada idioma dentro del lanzador (Name[xx]= en los .desktop), a partir de los mismos catálogos
python3 - "$R" "$D/i18n" <<'PYEOF'
import json, os, sys
R, cat = sys.argv[1], sys.argv[2]
SRC = {"owee-settings.desktop": "Ajustes de OweeLinux", "owee-calc.desktop": "Calculadora", "owee-capture.desktop": "Capturadora", "owee-calendar.desktop": "Calendario"}
WMC = {"owee-settings.desktop": "org.oweelinux.Settings", "owee-calc.desktop": "org.oweelinux.Calculator", "owee-capture.desktop": "org.oweelinux.Capture", "owee-calendar.desktop": "org.oweelinux.Calendar"}       # app_id de la ventana: la barra de ventanas del panel encuentra así el icono
LOC = {lg: lg for lg in ("en", "pt", "fr", "de", "it", "ru", "uk", "ja", "ko", "ar", "fa", "hi", "ur", "id", "ms")}; LOC["zh"] = "zh_CN"
for f, es in SRC.items():
    p = os.path.join(R, "usr/share/applications", f)
    if not os.path.exists(p): continue
    lines = open(p, encoding="utf-8").read().splitlines(); out = []
    for l in lines:
        out.append(l)
        if l.startswith("Name=") and not l.startswith("Name["):
            out += ["StartupWMClass=" + WMC[f], "Name[es]=" + es] + [f"Name[{loc}]=" + json.load(open(os.path.join(cat, lg + ".json"), encoding="utf-8")).get(es, es) for lg, loc in LOC.items()]
    open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")
PYEOF
# Owee: fuentes, teclado (Fcitx5) y locale qow_BO del proyecto del idioma (build-owee-debs.sh); catálogos de interfaz desde su glosario
OWEE_DEBS=${OWEE_DEBS:-/var/tmp/owee-debs}; OWEE_SRC=${OWEE_SRC:-/var/tmp/owee-src}
if ls "$OWEE_DEBS"/*.deb >/dev/null 2>&1; then
  for p in "$OWEE_DEBS"/*.deb; do dpkg-deb -x "$p" "$R"; done
  chroot "$R" localedef -i qow_BO -f UTF-8 qow_BO.UTF-8 2>/dev/null || echo "(aviso: sin locale qow_BO)"
  python3 "$D/../tools/i18n/build_owee_catalog.py" "$OWEE_SRC" "$R/usr/share/owee/i18n" || echo "(aviso: sin catálogos de Owee)"
  # Cifras Owee (owee-numerals): la fuente se instala, pero la regla que las impone a TODO el sistema NO (la activa Ajustes → Idioma solo con «Owee (Owee Script)», por usuario)
  install -Dm0644 "$OWEE_SRC/08_Integracion/linux/fontconfig/60-owee-numerals.conf" "$R/usr/share/owee/fontconfig/60-owee-numerals.conf"
  rm -rf "$R/etc/fonts"; rm -f "$R/usr/etc/fonts/conf.d/60-owee-numerals.conf"      # ostree exige /etc vacío (la configuración va en /usr/etc)
  [ -z "$(ls -A "$R/etc" 2>/dev/null)" ] || echo "(AVISO: /etc no está vacío: $(ls -A "$R/etc"))"
  # Catálogos de Owee para las apps ya instaladas (KDE, GTK…): LANGUAGE=qow:es / qow@owee:qow:es; lo que el glosario no cubre se ve en español
  python3 "$OWEE_SRC/08_Integracion/herramientas/gettext_rellenar.py" --origen "$R/usr/share/locale/es/LC_MESSAGES" --salida "$R/usr/share/locale" | head -2 || echo "(aviso: sin catálogos de apps en Owee)"
else echo "(aviso: sin paquetes de Owee: el idioma Owee no estará disponible)"; fi
# Fondos de pantalla propios (15 paisajes de tecnología, ilusiones y sueños, dibujados con desktop/wallpapers/generar.py): aparecen en Ajustes → Fondo de pantalla
install -d "$R/usr/share/backgrounds/oweelinux"; cp "$D"/wallpapers/fondos/*.jpg "$R/usr/share/backgrounds/oweelinux/"
# Tienda de apps: Bazaar (Flatpak). El servicio la instala en el primer arranque con red; Discover (de KDE) se oculta
install -Dm0644 "$D/session/owee-store.service" "$R/usr/lib/systemd/system/owee-store.service"
mkdir -p "$ETC/systemd/system/multi-user.target.wants"; ln -sf /usr/lib/systemd/system/owee-store.service "$ETC/systemd/system/multi-user.target.wants/owee-store.service"
# Hora por red: sin NTP el reloj de equipos con la pila agotada se queda atrás y Discover/HTTPS fallan con «certificado aún no válido»
mkdir -p "$ETC/systemd/system/sysinit.target.wants"; ln -sf /usr/lib/systemd/system/systemd-timesyncd.service "$ETC/systemd/system/sysinit.target.wants/systemd-timesyncd.service"
# Carpetas personales de siempre (Escritorio, Documentos, Descargas, Música, Imágenes, Vídeos): el gestor de archivos las muestra en su barra lateral
for d in Desktop Documents Downloads Music Pictures Videos; do install -d "$ETC/skel/$d"; done
printf 'XDG_DESKTOP_DIR="$HOME/Desktop"\nXDG_DOCUMENTS_DIR="$HOME/Documents"\nXDG_DOWNLOAD_DIR="$HOME/Downloads"\nXDG_MUSIC_DIR="$HOME/Music"\nXDG_PICTURES_DIR="$HOME/Pictures"\nXDG_VIDEOS_DIR="$HOME/Videos"\n' | install -Dm0644 /dev/stdin "$ETC/skel/.config/user-dirs.dirs"
# apt/apt-get explican cómo instalar en un sistema inmutable (apt de verdad se conserva como .real y sigue funcionando en contenedores y al construir)
install -d "$R/usr/libexec/owee"
for b in apt apt-get; do [ -x "$R/usr/bin/$b" ] && [ ! -e "$R/usr/libexec/owee/$b.real" ] && mv "$R/usr/bin/$b" "$R/usr/libexec/owee/$b.real"; install -Dm0755 "$D/session/owee-apt-shim" "$R/usr/bin/$b"; done
# Brillo de la pantalla (y del teclado): el paquete brightnessctl de Debian NO trae la regla de permisos y /sys/class/backlight/*/brightness solo lo escribe root, así que ni Ajustes ni las teclas Fn podían cambiarlo
install -Dm0644 /dev/stdin "$R/usr/lib/udev/rules.d/90-owee-backlight.rules" <<'EOR'
ACTION=="add", SUBSYSTEM=="backlight", RUN+="/bin/chgrp video /sys/class/backlight/%k/brightness", RUN+="/bin/chmod g+w /sys/class/backlight/%k/brightness"
ACTION=="add", SUBSYSTEM=="leds", KERNEL=="*kbd_backlight*", RUN+="/bin/chgrp video /sys/class/leds/%k/brightness", RUN+="/bin/chmod g+w /sys/class/leds/%k/brightness"
EOR
# Rendimiento y recursos (equipos de 2-4 GB y discos lentos): ajustes conservadores
install -Dm0644 /dev/stdin "$R/usr/lib/sysctl.d/90-owee.conf" <<'EOS'
# zram hace barato el intercambio: se usa antes de tirar la caché de archivos; sin lecturas por adelantado en zram; caché de nombres de archivo más duradera; escrituras a disco más suaves
vm.swappiness = 100
vm.page-cluster = 0
vm.vfs_cache_pressure = 50
vm.dirty_background_ratio = 5
vm.dirty_ratio = 15
vm.watermark_boost_factor = 0
kernel.nmi_watchdog = 0
EOS
install -Dm0644 /dev/stdin "$R/usr/lib/udev/rules.d/60-owee-ioscheduler.rules" <<'EOS'
# planificador de disco según el tipo: HDD con bfq (reparte bien entre apps), SSD y NVMe sin planificador (lo mejor para memorias flash)
ACTION=="add|change", KERNEL=="sd[a-z]*|mmcblk[0-9]*", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="bfq"
ACTION=="add|change", KERNEL=="sd[a-z]*|mmcblk[0-9]*", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="mq-deadline"
ACTION=="add|change", KERNEL=="nvme[0-9]*n[0-9]*", ATTR{queue/scheduler}="none"
EOS
install -Dm0644 /dev/stdin "$R/usr/lib/systemd/system.conf.d/90-owee.conf" <<'EOS'
[Manager]
# un servicio que no responde no debe retrasar el apagado más de 15 s
DefaultTimeoutStopSec=15s
EOS
install -Dm0644 /dev/stdin "$R/usr/lib/systemd/journald.conf.d/90-owee.conf" <<'EOS'
[Journal]
# registros acotados: no llenan un disco pequeño ni la RAM del modo en vivo
SystemMaxUse=150M
RuntimeMaxUse=40M
Compress=yes
EOS
install -Dm0644 /dev/stdin "$ETC/default/zramswap" <<'EOS'
# zram: memoria comprimida como intercambio (50 % de la RAM, comprime ~3:1 con zstd)
ALGO=zstd
PERCENT=50
PRIORITY=100
EOS
install -Dm0644 /dev/stdin "$ETC/default/earlyoom" <<'EOS'
# earlyoom: actúa ANTES de que el equipo se ahogue (a partir de menos del 8 % de memoria disponible; a menos del 4 % ya sin pedir permiso). Con zram hay intercambio de sobra, así que no espera a que se llene (-s 100): cuando se llena ya está todo bloqueado.
# Nunca toca el escritorio, el sonido ni los servicios del sistema (los nombres se comparan truncados a 15 letras); prefiere navegadores, grabadoras y apps pesadas.
EARLYOOM_ARGS="-r 0 -m 8,4 -s 100,100 --avoid '(^|/)(labwc|sddm.*|Xwayland|Xorg|pipewire.*|wireplumber|systemd.*|dbus-daemon|NetworkManager|wpa_supplicant|polkitd|polkit-mate.*|mako|foot|python3|fcitx5|swaybg|swayidle|xdg-.*|flatpak-.*|dconf-service|gvfs.*|kded6|udisksd|upowerd|bluetoothd)$' --prefer '(^|/)(QtWebEngineProc|falkon|chrome|chromium|firefox|firefox-esr|electron|java|code|slack|discord|steam|wf-recorder|ffmpeg|DesktopEditors|editors_helper)$'"
EOS
mkdir -p "$ETC/systemd/system/timers.target.wants"; ln -sf /usr/lib/systemd/system/fstrim.timer "$ETC/systemd/system/timers.target.wants/fstrim.timer"
# Fcitx5 no debe arrancarse solo por D-Bus (lo activaban Ajustes y el panel nada más abrirse, +32 MB): se lanza cuando el usuario activa un método de escritura (Ajustes → Teclado) o ya tiene uno
rm -f "$R/usr/share/dbus-1/services/org.fcitx.Fcitx5.service"
printf '#!/bin/sh\n# El selector «Abrir con…» llama a gnome-software; en OweeLinux la tienda es Discover\nexec plasma-discover "$@"\n' | install -Dm0755 /dev/stdin "$R/usr/bin/gnome-software"
# Un escritorio no necesita esperar a que haya red para arrancar (NetworkManager-wait-online retrasaba el inicio unos 9 s)
mkdir -p "$ETC/systemd/system"; ln -sf /dev/null "$ETC/systemd/system/NetworkManager-wait-online.service"
# Inicio de sesión de OweeLinux (tema SDDM «owee») y bloqueo de pantalla (gtklock): el aspecto se elige en Ajustes → Acceso
T="$R/usr/share/sddm/themes/owee"; mkdir -p "$T"
for f in Main.qml metadata.desktop theme.conf logo.png; do install -m0644 "$D/sddm/owee/$f" "$T/$f"; done
ln -sf /usr/share/wallpapers/OweeLinux/contents/images/1920x1080.jpg "$T/background-default.jpg"          # imagen por defecto: el fondo de OweeLinux
ln -sf /var/lib/owee/login/theme.conf.user "$T/theme.conf.user"                                         # lo que elige el usuario vive en /var (el tema, en /usr, es de solo lectura)
printf '[Theme]\nCurrent=owee\nFacesDir=/var/lib/owee/faces\n' | install -Dm0644 /dev/stdin "$ETC/sddm.conf.d/25-owee-login-theme.conf"
printf 'd /var/lib/owee/login 0755 root root -\nd /var/lib/owee/faces 0755 root root -\n' | install -Dm0644 /dev/stdin "$R/usr/lib/tmpfiles.d/owee-login.conf"
install -Dm0644 "$D/session/gtklock-layout.ui.in" "$R/usr/share/owee/gtklock/layout.ui.in"
# owee-dev: cajas de desarrollo y programas .deb (Podman + distrobox, sin root); un .deb abre el asistente en una terminal
ln -sf /usr/libexec/owee/owee-dev "$R/usr/bin/owee-dev"
install -Dm0644 /dev/stdin "$R/usr/share/applications/owee-dev-deb.desktop" <<'EOD'
[Desktop Entry]
Type=Application
Name=Instalar programa .deb (en una caja)
Comment=Instala un paquete .deb con sus dependencias en la caja «apps», sin tocar el sistema
Exec=foot -e sh -c 'owee-dev deb "$1"; echo; printf "Pulsa Intro para cerrar"; read x' sh %f
Icon=package-x-generic
MimeType=application/vnd.debian.binary-package;
NoDisplay=true
Categories=System;
EOD
# sin LLMNR ni mDNS en el resolutor: no hace falta en un escritorio y deja puertos abiertos
install -Dm0644 /dev/stdin "$R/usr/lib/systemd/resolved.conf.d/90-owee.conf" <<'EOS'
[Resolve]
LLMNR=no
MulticastDNS=no
EOS
# Seguridad: cortafuegos (bloquea lo entrante; activo por defecto), Centinela (señuelo de red pasivo; apagado por defecto) y endurecimiento del kernel
install -Dm0644 "$D/session/owee-firewall.service" "$R/usr/lib/systemd/system/owee-firewall.service"
install -Dm0644 "$D/session/owee-centinela.service" "$R/usr/lib/systemd/system/owee-centinela.service"
install -Dm0644 "$D/session/owee-centinela.sysusers" "$R/usr/lib/sysusers.d/owee-centinela.conf"
ln -sf /usr/lib/systemd/system/owee-firewall.service "$ETC/systemd/system/multi-user.target.wants/owee-firewall.service"
install -Dm0644 /dev/stdin "$R/usr/lib/sysctl.d/91-owee-hardening.conf" <<'EOS'
# Endurecimiento de escritorio: no rompe navegadores, Flatpak ni Podman (se dejan los espacios de nombres de usuario sin restringir)
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.unprivileged_bpf_disabled = 1
net.core.bpf_jit_harden = 2
kernel.kexec_load_disabled = 1
kernel.yama.ptrace_scope = 1
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.protected_fifos = 2
fs.protected_regular = 2
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
EOS
echo "sesión Lite instalada en $R"
install -Dm0644 /dev/stdin "$R/usr/share/applications/owee-settings.desktop" <<'EOD'
[Desktop Entry]
Type=Application
Name=Ajustes de OweeLinux
GenericName=Ajustes
Comment=Apariencia y fondo de pantalla
Exec=/usr/libexec/owee/owee_settings.py
Icon=preferences-system
Categories=Settings;
Keywords=ajustes;tema;fondo;color;apariencia;
EOD
# Índice de aplicaciones (mimeinfo.cache), al final, cuando ya están todos los .desktop: sin él, GIO y los portales no saben qué abre cada tipo de archivo y salía «No hay aplicaciones…»
[ -x "$R/usr/bin/update-desktop-database" ] && chroot "$R" update-desktop-database -q /usr/share/applications || echo "(aviso: sin update-desktop-database; falta desktop-file-utils)"
