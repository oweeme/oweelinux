# Arranque de OweeLinux: rápido y con el logo

Objetivo: al encender, sin menús ni texto: el logo del koi sobre fondo verde oscuro y, al terminar, el escritorio. Solo se ve texto si algo falla.

## Cómo está armado
1. **Firmware UEFI → shim → GRUB firmado** (Secure Boot funciona; ver `SEGURIDAD.md`).
2. **GRUB oculto cuando OweeLinux está solo en el equipo** (`set timeout_style=hidden`, `timeout=1`): no se ve menú; si se mantiene **Mayús** o se pulsa **Esc** al encender, aparece (con la opción «modo seguro» si la pantalla saliera negra).
3. **Si hay otro sistema en la partición EFI** (por ejemplo Windows), `owee-bootcfg` añade su entrada (`chainloader`) y el menú se muestra 5 s. Si la partición EFI no está montada cuando se regenera el menú (p. ej. tras una actualización), se conservan las entradas ya existentes.
4. **Plymouth** muestra el logo desde el initramfs: tema propio `desktop/theme/plymouth/oweelinux` (fondo `#102019`, koi que «respira», barra fina de progreso, sin texto). `prepare-rootfs.sh` lo instala **antes** de generar el initramfs con `dracut --add plymouth`.
5. Parámetros del núcleo (en `owee-bootcfg`): `quiet splash loglevel=3 vt.global_cursor_default=0 rd.udev.log_level=3`. `loglevel=3` oculta los avisos de firmware (ACPI) que algunos portátiles, como el HP A12, imprimen y que no son fallos. Si el arranque falla de verdad, `rd.emergency=reboot panic=5` reinicia solo; **Esc** durante el logo muestra el detalle.

## Verificado en una VM (QEMU + OVMF con Secure Boot, 21 oct 2026)
- Instalación y arranque con Secure Boot activado; el menú instalado trae «OweeLinux 1» y «OweeLinux 1 (modo seguro)», con `timeout_style=hidden`.
- Del segundo ~7 al ~13: logo con barra de progreso, sin menú de GRUB ni texto del núcleo; después, el asistente de bienvenida.
- AppArmor activo (se quitó `apparmor-profiles`, cuyo `bin.ping` fallaba en el HP); `NetworkManager-wait-online` enmascarado: el sistema llega al escritorio gráfico en ~4,6 s de espacio de usuario en la VM (en el HP eran ~11,9 s con 8,6 s de esa espera).
- El initramfs pasó a ~105 MB: Plymouth incluye los controladores gráficos y su firmware (626 archivos de `amdgpu`).

## Sin verificar / pendiente
- **Esc al encender para mostrar el menú oculto:** en la VM no se pudo comprobar (el teclado virtual manda una pulsación, no repeticiones). En un equipo real mantener Esc debería funcionar; probar en el HP.
- **Hueco negro de ~3 s** entre el logo y el escritorio (Plymouth termina, SDDM arranca la sesión de labwc y hasta que dibuja el primer cuadro no hay imagen). Probados sin efecto: `plymouth quit --retain-splash` y SDDM en modo Wayland. Opciones a estudiar: sustituir SDDM por un gestor de autologin sin servidor X, o que labwc pinte el fondo verde antes que nada. En hardware real puede ser distinto.
- Varios monitores y pantallas de resolución muy alta: el tema escala el logo al 22 % del alto, sin probar fuera de 1280×720.

## Qué NO hace (todavía)
- **No es un arranque sin cargador.** Con Secure Boot hace falta el encadenado shim → GRUB; arrancar el núcleo directamente desde el firmware (como Windows o macOS) exigiría un núcleo firmado por una clave que el firmware conozca (imagen UKI + systemd-boot firmado, o claves propias en el firmware). Se deja como mejora futura.
- El **medio en vivo** (ISO) sigue sin Plymouth: su menú es visible porque ahí se elige entre instalar y probar.

## Probar
`~/oweelinux-dist/probar-en-qemu.sh ISO` (instalar) y luego `probar-en-qemu.sh --disco` (arrancar lo instalado, para ver el logo). Con `--secureboot` se prueba con Secure Boot activado.

## Bloqueo de pantalla e inicio de sesión (aspecto configurable)
- **Bloqueo** (`desktop/session/owee-lock`): usa **gtklock** (verifica con PAM) con un diseño propio: reloj, fecha, tu nombre y foto, campo de contraseña **siempre visible** y la indicación «Escribe tu contraseña y pulsa Intro» (antes el campo estaba oculto hasta pulsar una tecla y no se sabía qué hacer). Si gtklock faltara, vuelve a swaylock.
- **Inicio de sesión** (`desktop/sddm/owee`, tema de SDDM hecho en QML, sin dependencias extra): reloj, fecha, usuario, contraseña, apagar/reiniciar/reposo. Formulario a la **izquierda, centro o derecha**; **imagen de fondo completa** o **imagen en un lado** con un panel liso para el formulario; imagen del escritorio, otra imagen o solo color; desenfoque opcional.
- **Dónde se elige:** Ajustes → Acceso → «Aspecto del acceso». El bloqueo cambia al instante; el inicio de sesión es del sistema y se aplica con «Aplicar al inicio de sesión» (pide la clave de administrador). «Ver el inicio de sesión» lo muestra en una ventana de prueba.
- **Cómo funciona:** `owee-account-helper logintheme …` (polkit, ya existente) valida todo, reduce/desenfoca la imagen **con los permisos del usuario que llama** (no root) y escribe `/var/lib/owee/login/theme.conf.user`, que el tema (en `/usr`, de solo lectura) enlaza. «Usar el aspecto de OweeLinux» apagado = tema estándar (Breeze).
- **Si el login no se viera** (un tema roto dejaría el greeter en negro): Ctrl+Alt+F3, entrar y ejecutar `sudo rm -f /etc/sddm.conf.d/25-owee-login-theme.conf && sudo systemctl restart sddm` para volver al tema estándar.

## Kois animados (arranque, protector de pantalla y bloqueo)
- **Arranque (Plymouth):** `desktop/theme/plymouth/oweelinux/oweelinux.script` hace nadar tres kois alrededor del logo (imágenes `koiN_M.png`, giradas en cada cuadro; la cola tiene tres posiciones). Los sprites son cuadrados (240×240) para que al girar no se recorten. Comprobado arrancando el disco con `boot-shot.py` y `BOOT_KERNEL` (arranque directo con el parámetro `splash`, que el disco de pruebas no lleva; sin `splash` Plymouth no se muestra).
- **Protector de pantalla:** `desktop/session/owee-screensaver` (GTK4 + layer-shell, capa superior sin foco; dibuja con `shell/owee_koi.py`, 20 imágenes por segundo). Lo lanza `owee-idle` (swayidle) tras el tiempo de Ajustes → Energía (5 min por defecto; 0 = nunca) y se cierra con cualquier actividad; `owee-lock` lo cierra antes de bloquear. El patrón de `pkill` es exacto porque la línea de comandos de swayidle también contiene el nombre.
- **Bloqueo animado:** `owee-lock` añade al CSS de gtklock una animación de `background-position` con cinco kois (`/usr/share/owee/koi/*.png`) sobre la imagen de fondo; se apaga en Ajustes → Acceso («Bloqueo animado»). Es CSS puro: el bloqueo no ejecuta código propio más allá de gtklock.
- **Asistente de primer arranque:** la página de progreso usa el mismo estanque (`KoiPond`).
- **Grabaciones cortadas de golpe:** `core.leftovers()` / `recover_orphans()` guardan el vídeo que quedó en `~/.cache/owee/rec` cuando la Capturadora muere (p. ej. por falta de memoria); se ejecuta al pulsar «Detener» sin grabación propia y al abrir la Capturadora.
