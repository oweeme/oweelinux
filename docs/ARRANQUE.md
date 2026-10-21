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
