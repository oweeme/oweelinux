#!/usr/bin/env bash
# Instala en un rootfs ya preparado para ostree la sesión "OweeLinux Lite" (prototipo): archivo de sesión, arranque,
# configuración y tema de labwc, Waybar de comparación, el panel en Python y la prueba de lista de ventanas.
# Los enlaces de pywayland se generan AQUÍ (en el pod, que tiene la misma versión que la imagen).
# Uso: overlay-lite.sh ROOTFS [REPO_ROOT]
set -euo pipefail
R=${1:?uso: $0 ROOTFS [REPO_ROOT]}; REPO=${2:-/work}; D=$REPO/desktop
ETC=$R/usr/etc; [ -d "$ETC" ] || { echo "rootfs sin preparar" >&2; exit 1; }
install -Dm0644 "$D/session/owee-lite.desktop" "$R/usr/share/wayland-sessions/owee-lite.desktop"
for f in owee-session owee-lite-start owee-wallpaper owee-apply-display owee-idle owee-desktop owee-store-setup owee-apply-theme owee-layout owee-lock owee-account-helper owee-firstboot owee-setup-session owee-setup-run owee-locale owee-installer-session owee-installer-run; do install -Dm0755 "$D/session/$f" "$R/usr/libexec/owee/$f"; done
for f in owee_panel.py wl_toplevels.py owee_tray.py owee_theme.py owee_config.py owee_i18n.py owee_windows.py owee_desktops.py owee_keys.py owee_settings.py $(cd "$D/shell" && ls ajustes/*.py); do install -Dm0755 "$D/shell/$f" "$R/usr/libexec/owee/$f"; done
install -Dm0644 "$D/session/mako/config" "$ETC/xdg/mako/config"; install -Dm0644 "$D/session/labwc/menu.xml" "$ETC/xdg/labwc/menu.xml"; install -Dm0644 "$D/session/labwc/rc.xml" "$ETC/xdg/labwc/rc.xml"; install -Dm0755 "$D/session/labwc/autostart" "$ETC/xdg/labwc/autostart"
# widgets del panel: los del sistema van en /usr/share/owee/widgets (el usuario los sustituye con un archivo del mismo nombre
# en ~/.config/owee/widgets); los ejemplos se dejan aparte para copiarlos y cambiarlos.
for f in "$D"/widgets/sistema/*; do install -Dm0755 "$f" "$R/usr/share/owee/widgets/$(basename "$f")"; done
install -Dm0644 "$D/session/org.oweelinux.accounts.policy" "$R/usr/share/polkit-1/actions/org.oweelinux.accounts.policy"      # Ajustes → Usuarios/Acceso: pkexec pide la clave de administrador
# Primer arranque (docs/EXTENSIONES.md → Primer arranque): sesión propia de SDDM con el asistente, usuario de sistema `owee-setup`, regla polkit y servicio que decide cada arranque
install -Dm0644 "$D/session/labwc-setup/rc.xml" "$R/usr/share/owee/labwc-setup/rc.xml"; install -Dm0644 "$D/session/labwc-setup/autostart" "$R/usr/share/owee/labwc-setup/autostart"
# Fcitx5 por defecto (también para usuarios nuevos): sin icono propio en la bandeja (lo reemplaza el indicador del panel) y sin avisos (el de «Wayland Diagnose» no aplica con labwc)
printf '[Behavior]\nDisabledAddons=notificationitem,notifications\n' | install -Dm0644 /dev/stdin "$ETC/xdg/fcitx5/config"
# Reproductor de vídeo y música por defecto: mpv (ligero; con controles en pantalla al abrirlo desde el lanzador o desde Dolphin), para las grabaciones de la Capturadora y cualquier archivo multimedia
{ echo "[Default Applications]"; for t in video/mp4 video/x-matroska video/webm video/quicktime video/x-msvideo video/mpeg video/ogg video/x-flv video/3gpp audio/mpeg audio/mp4 audio/ogg audio/flac audio/x-wav audio/webm audio/aac audio/opus; do echo "$t=mpv.desktop"; done; } | install -Dm0644 /dev/stdin "$ETC/xdg/mimeapps.list"
# Instalador (Calamares): scripts, configuración y marca. Solo se activa en el medio de instalación (marca en /var, ver build.sh); si falta el paquete calamares, no se instala nada.
if [ "${OWEE_INSTALLER:-0}" = 1 ]; then
  install -Dm0755 "$D/installer/owee-install-deploy" "$R/usr/libexec/owee/installer/owee-install-deploy"; install -Dm0755 "$D/installer/owee-install-disk" "$R/usr/libexec/owee/installer/owee-install-disk"
  install -Dm0644 "$D/session/owee-installer.desktop" "$R/usr/share/wayland-sessions/owee-installer.desktop"
  for f in settings.conf welcome.conf partition.conf shellprocess-oweedeploy.conf finished.conf; do install -Dm0644 "$D/installer/calamares/$f" "$R/usr/share/owee/calamares/$f"; done
  mkdir -p "$R/usr/share/owee/calamares/modules"; for f in welcome partition finished; do cp "$D/installer/calamares/$f.conf" "$R/usr/share/owee/calamares/modules/$f.conf"; done; cp "$D/installer/calamares/shellprocess-oweedeploy.conf" "$R/usr/share/owee/calamares/modules/"
  for f in branding.desc show.qml owee-logo.png; do install -Dm0644 "$D/installer/calamares/branding/oweelinux/$f" "$R/usr/share/owee/calamares/branding/oweelinux/$f"; done
fi
install -Dm0755 "$D/setup/owee_setup.py" "$R/usr/libexec/owee/setup/owee_setup.py"
install -Dm0644 "$D/session/owee-setup.desktop" "$R/usr/share/wayland-sessions/owee-setup.desktop"
install -Dm0644 "$D/session/owee-setup.sysusers" "$R/usr/lib/sysusers.d/owee-setup.conf"; install -Dm0644 "$D/session/owee-setup.tmpfiles" "$R/usr/lib/tmpfiles.d/owee-setup.conf"
install -Dm0644 "$D/session/49-owee-setup.rules" "$R/usr/share/polkit-1/rules.d/49-owee-setup.rules"
install -Dm0644 "$D/session/owee-firstboot.service" "$R/usr/lib/systemd/system/owee-firstboot.service"
mkdir -p "$R/usr/lib/systemd/system/sysinit.target.wants"; ln -sf ../owee-firstboot.service "$R/usr/lib/systemd/system/sysinit.target.wants/owee-firstboot.service"
for f in "$D"/widgets/ejemplos/*; do install -Dm0755 "$f" "$R/usr/share/owee/widgets-ejemplos/$(basename "$f")"; done
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
for f in org.kde.systemsettings.desktop kdesystemsettings.desktop systemsettings.desktop org.kde.kinfocenter.desktop org.kde.kcalc.desktop org.kde.spectacle.desktop org.kde.discover.desktop org.kde.discover.urlhandler.desktop org.kde.discover.notifier.desktop org.kde.discover.flatpak.desktop fcitx5-configtool.desktop fcitx5-wayland-launcher.desktop org.fcitx.Fcitx5.desktop org.fcitx.fcitx5-qt6-gui-wrapper.desktop; do [ -f "$R/usr/share/applications/$f" ] && sed -i '/^NoDisplay=/d; /^\[Desktop Entry\]/a NoDisplay=true' "$R/usr/share/applications/$f"; done
# ---- Idiomas: catálogos de la interfaz, locales del sistema, fuentes y teclados (docs/EXTENSIONES.md → Idiomas)
install -d "$R/usr/share/owee/i18n"; cp "$D"/i18n/*.json "$R/usr/share/owee/i18n/"
for l in es_ES en_US pt_BR fr_FR de_DE it_IT ru_RU uk_UA zh_CN ja_JP ko_KR ar_SA fa_IR hi_IN ur_PK id_ID ms_MY; do chroot "$R" localedef -i "$l" -f UTF-8 "$l.UTF-8" 2>/dev/null || echo "(aviso: sin locale $l)"; done
# Nombres de nuestras apps en cada idioma dentro del lanzador (Name[xx]= en los .desktop), a partir de los mismos catálogos
python3 - "$R" "$D/i18n" <<'PYEOF'
import json, os, sys
R, cat = sys.argv[1], sys.argv[2]
SRC = {"owee-settings.desktop": "Ajustes de OweeLinux", "owee-calc.desktop": "Calculadora", "owee-capture.desktop": "Capturadora"}
WMC = {"owee-settings.desktop": "org.oweelinux.Settings", "owee-calc.desktop": "org.oweelinux.Calculator", "owee-capture.desktop": "org.oweelinux.Capture"}       # app_id de la ventana: la barra de ventanas del panel encuentra así el icono
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
