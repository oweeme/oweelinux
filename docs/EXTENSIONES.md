# Extensiones y personalización de OweeLinux

Principio (del autor, 2026-10-12): **un Linux es usable y modificable según su filosofía**. En OweeLinux, cualquiera que sepa
**Python o JavaScript** debe poder cambiar el escritorio y escribir apps **sin compilar** y **sin poder romper el sistema**.
Detalles de lenguajes y memoria: `docs/ESCRITORIO.md` ("¿Qué lenguaje con GTK?").

## Tres niveles, de menos a más poder
| Nivel | Qué es | Lenguajes | Cuesta (memoria) | Estado |
|---|---|---|---|---|
| **1. Widgets de script** | Un ejecutable que imprime una línea JSON; el panel la muestra | **Python, JavaScript (GJS), shell o cualquier otro** | ≈ 0 residente (el script solo vive un instante) | **Prototipo probado** |
| **2. Widgets con clic y ventanita** | El mismo script, pero su JSON pide un clic y/o una ventanita que el **panel dibuja** | Python, JavaScript, shell… | ≈ 0 residente | **Prototipo probado** |
| **2b. Widgets nativos** | Código propio dentro del proceso del panel (ventanas a medida) | Python (dentro del panel) | pocos MB | Por diseñar |
| **3. Apps** | Programas completos, con `.kapp`/`owee-app` y permisos | Python+GTK4, JavaScript+GJS, Python+Qt6, Rust… | 20-40 MB por app abierta | Plantilla Python en `tools/owee-app-template/` |

## Nivel 1: widgets de script (probado)
**Contrato:** un archivo ejecutable (con su `#!`) en `/usr/share/owee/widgets/` (de fábrica) o `~/.config/owee/widgets/` (del usuario).
Imprime **una línea JSON** por la salida estándar: `{"text": "...", "tooltip": "...", "class": "warn"}` (solo `text` es obligatorio).
Un comentario `owee-interval: N` fija cada cuántos segundos se ejecuta (5 por defecto).
```python
#!/usr/bin/env python3            # Python
# owee-interval: 5
import json; print(json.dumps({"text": "hola"}))
```
```javascript
#!/usr/bin/env gjs                // JavaScript, sin Node
// owee-interval: 10
print(JSON.stringify({ text: 'hola' }));
```
Ejemplos: `desktop/widgets/load.py` (Python) y `desktop/widgets/utc.js` (JavaScript).

**Garantías (comprobadas en la VM, `tools/ostree-proto/widgets-test.py`):**
- Se ejecutan de forma **asíncrona**: el panel nunca espera a un widget.
- Límite de **5 s** (`timeout` mata el script y sus hijos); un widget colgado muestra `⚠ nombre` y el panel sigue.
- Un widget que imprime algo que no es JSON o que falla muestra `⚠ nombre` con el motivo en el tooltip.
- **Memoria del panel con 4 widgets (2 buenos, 1 roto, 1 colgado): 40 MB de Pss**, igual que sin widgets.
- Cambiar un widget = **editar el archivo**; sin compilar y sin reiniciar el panel.
Limitaciones conocidas: hoy un widget no puede abrir ventanas ni recibir clics; el JSON no admite iconos; el panel ejecuta los
widgets con los permisos del usuario (un widget es código del usuario, **no está aislado**): la seguridad por permisos llega con el nivel 3.

## Nivel 2: clic y ventanitas (probado)
El script añade campos a su JSON; **el panel dibuja la interfaz** (así no cuesta memoria ni exige cargar un toolkit en el script):
```json
{"text": "brillo 50%",
 "on_click": ["gjs", "/ruta/script.js", "inc"],               // se ejecuta al hacer clic y el widget se actualiza
 "popup": {"title": "Brillo", "items": [                      // ventanita que se abre al hacer clic
    {"type": "label",     "text": "..."},
    {"type": "button",    "text": "Poner al 50 %", "command": ["/ruta/script.py", "set", "50"]},
    {"type": "slider",    "min": 0, "max": 100, "value": 50, "command": ["/ruta/script.py", "set"]},   // el valor se añade al final
    {"type": "calendar"}, {"type": "separator"} ]}}
```
Cuando el usuario actúa, el panel vuelve a llamar al script con los argumentos del `command`; el script hace el trabajo y el panel se actualiza.
Los deslizadores esperan 250 ms antes de llamar (no lanzan un proceso por cada píxel). El estilo de las ventanitas es el de OweeLinux.
Ejemplos: `counter.js` (**JavaScript**, cuenta clics), `brillo.py` (**Python**, deslizante) y `calendario.py` (**Python**, calendario).

**Comprobado en la VM** (`tools/ostree-proto/interaction-test.py`, ratón y teclado virtuales de QEMU, capturas en `docs/img/lite/interaccion-*.png`):
| Prueba | Resultado |
|---|---|
| (A) 3 clics sobre un widget de **JavaScript** | el archivo de estado vale 3 y el panel muestra `clics 3` |
| (B) clic sobre un widget de **Python**: la ventanita se abre y el deslizante responde al teclado | el valor cambió (50 → 53; de 10 pulsaciones se aplicaron 3: **no se investigó por qué**) |
| (C) clic sobre el calendario | se abre el calendario del mes (captura) |
| El panel sigue vivo y su memoria | sí; 40 MB de Pss con 5 widgets |
**Límites:** la prueba (B) comprueba que el control responde, no una cifra exacta; los widgets no pueden abrir ventanas propias (eso sería el nivel 2b);
no hay iconos ni menús contextuales; **el estilo del resaltado costó dos intentos** porque `Gtk.MenuButton` tiene un nodo interno (`menubutton > button`).
Para que la ventanita reciba teclado, el panel usa `keyboard-interactivity: on-demand` de `layer-shell`.

## Widgets del sistema (probado)
Vienen con la imagen en `/usr/share/owee/widgets/` y son **widgets de script normales**: se leen, se copian y se cambian igual que los de ejemplo
(los de demostración están en `widgets-ejemplos/`). Para modificar uno basta copiarlo a `~/.config/owee/widgets/` con el **mismo nombre**: el del usuario gana.
| Widget | Fuente | Clic |
|---|---|---|
| `10-red.py` | NetworkManager (`nmcli`) | datos de la conexión, interruptor WiFi y **lista de redes** (abiertas y guardadas con un clic; con clave: campo de contraseña + Intro) |
| `20-volumen.py` | WirePlumber (`wpctl`) | deslizante de volumen y botón silenciar; sin audio se oculta |
| `30-bateria.py` | `/sys/class/power_supply` | porcentaje y estado; sin batería se oculta |
- `{"hidden": true}` en la salida oculta el widget (equipo sin batería o sin audio).
- Prueba: `tools/ostree-proto/system-widgets-test.py` (VM, ratón y teclado virtuales). El `wpctl` es **simulado** (`mock-wpctl`) porque en la VM el WirePlumber real
  acepta `set-volume` pero no cambia una salida virtual; la lectura con el real se validó en un equipo físico. La batería se simula con `OWEE_POWER_SUPPLY_DIR`.
- Dos errores que encontró la prueba: el refresco de 3 s **cerraba la ventanita abierta** (arreglado: no se reasigna el popover si ya tiene uno), y el mock escribía su
  archivo como root sin permiso para el usuario (fallo de la prueba, no del widget). Memoria del panel con los tres widgets: 40 MB Pss.

## Lanzador de aplicaciones (probado)
El botón «OweeLinux» del panel abre una ventanita con búsqueda y la lista de apps instaladas (archivos `.desktop`, ordenadas por nombre, con icono).
Escribir filtra (nombre, nombre genérico y palabras clave), **Intro lanza la primera coincidencia**, clic lanza la elegida, Esc cierra.
La lista se construye al abrir por primera vez, no al arrancar: no cuesta memoria si no se usa. Panel con el lanzador: 39 MB Pss.
Prueba: `tools/ostree-proto/launcher-test.py` (ratón y teclado virtuales; captura en `docs/img/lite/lanzador-busqueda.png`).

## Bandeja de apps (probado)
El panel es el anfitrión del protocolo **StatusNotifierItem** (el que usan Qt/KDE, Electron, Telegram...): es dueño de `org.kde.StatusNotifierWatcher` y dibuja
el icono de cada app (por nombre del tema o por `IconPixmap`). Clic izquierdo → `Activate`, clic derecho → `ContextMenu` (el menú lo dibuja la propia app);
si la app muere, el icono desaparece solo; todas las llamadas D-Bus son asíncronas con 2 s de límite. Si la bandeja falla, el panel sigue sin ella.
Pendiente: dibujar el menú `com.canonical.dbusmenu` y los iconos propios de OweeLinux. Prueba: `tools/ostree-proto/tray-test.py` con la app falsa `mock-sni.py`
(6/6: aparece, Activate, ContextMenu, desaparece; panel 40 MB Pss). Código: `desktop/shell/owee_tray.py`.

## Iconos propios y menú de sesión (probado)
Tema de iconos **Owee** (línea redondeada, dibujos originales) generado por `desktop/theme/icons/gen_icons.py` (se instala en `/usr/share/icons/Owee`;
el color del trazo es un parámetro, así que el modo claro es otra pasada del generador). Los widgets piden iconos con `"icon": "owee-volume-high"` en su JSON;
el panel solo muestra el número junto al icono. El botón de sesión (a la derecha) ofrece Bloquear, Cerrar sesión, Reiniciar y Apagar; los dos últimos piden un segundo clic.
Lección: la imagen **no traía el cargador de SVG** (`librsvg2-common`), así que ningún icono SVG se dibujaba (tampoco los de KDE); ahora está en `packages-plasma.txt`.
Prueba: `tools/ostree-proto/image-lite-test.py` sobre la imagen completa (capturas `imagen-sesion*.png`). El panel sube a ~47 MB Pss con los iconos.

## Ajustes de OweeLinux (v0.2, probado en VM)
Central de configuración propia (reemplaza a «Preferencias del sistema» de KDE, que en Lite funcionaba a medias): `desktop/shell/owee_settings.py` + un módulo por página en `desktop/shell/ajustes/`
(contrato en `ajustes/base.py`; si una página falla al cargar, las demás siguen). Todo se aplica **con herramientas del sistema, sin bloquear la ventana** (órdenes asíncronas con tiempo límite) y se puede buscar por texto.
| Página | Qué controla | Cómo |
|---|---|---|
| Apariencia | modo claro/oscuro, 6 acentos | `settings.json` (el panel cambia al instante); GTK `settings.ini`; Qt/KDE: esquema Breeze copiado a `kdeglobals` (las apps abiertas después lo toman) |
| Fondo de pantalla | miniaturas + «Elegir otra imagen…» | `owee-wallpaper` (swaybg) |
| Pantalla | resolución, escala, rotación, brillo | `wlr-randr` con **confirmación de 10 s y vuelta atrás automática**; guardado en `display.json` y aplicado al iniciar sesión (`owee-apply-display`); `brightnessctl` |
| Sonido | salida/entrada por defecto, volumen, silencio | `wpctl` |
| Teclado | distribución (hasta 2, Alt+Mayús), repetición | `~/.config/labwc/environment` + `labwc --reconfigure` (instantáneo) |
| Ratón y touchpad | velocidad, aceleración, desplazamiento natural, tocar para clic, zurdos | `<libinput>` del `rc.xml` de usuario (parte de una copia del de sistema, conserva comentarios y atajos) |
| Energía | perfil de rendimiento, bloqueo y suspensión por inactividad | `powerprofilesctl`; `power.json` → `owee-idle` (swayidle) |
| Fecha y hora | reloj del panel (24/12 h, segundos, fecha), zona horaria | `settings.json`; `timedatectl` (pide permisos) |
| Aplicaciones | app por defecto de cada tipo de archivo | Gio (`mimeapps.list`) |
| Atajos de teclado | lista de atajos activos | solo lectura (se edita `rc.xml`) |
| Actualizaciones | versión, estado «a prueba/estable», instalar y volver atrás | `owee-status`, `pkexec owee-update/owee-rollback` |
| Acerca de | versión, equipo, memoria, kernel | `/proc`, `os-release` |
Pruebas con clics reales: `tools/ostree-proto/ajustes-test.py` (13 comprobaciones: volumen, silencio, cambio de salida, teclado latam, desplazamiento natural, bloqueo a 1 min con swayidle,
escala 150 % aplicada, **vuelta atrás automática**, y «Mantener» guardado). Capturas en `docs/img/lite/aj/`.
**No probado / pendiente:** instalar actualizaciones y volver atrás desde la app (necesitan polkit: se arranca un agente de contraseña, falta la política y probarlo), zona horaria (polkit),
brillo (la VM no tiene luz regulable), suspensión, Bluetooth, WiFi/red como página propia (hoy desde el widget del panel), usuarios y cuentas, impresoras, inicio automático de apps, tipografía.

## Lista de WiFi (probada con `nmcli` simulado)
El widget de red muestra las 8 redes más fuertes (una por nombre), marca la conectada, las guardadas y las que piden clave. Conectar se lanza **aparte** (tarda más que el límite de 5 s del panel).
Nuevo tipo de elemento de ventanita: `{"type":"entry","password":true,"command":[...]}` (al pulsar Intro se llama al comando con el texto como último argumento).
Prueba: `tools/ostree-proto/wifi-test.py` con `mock-nmcli` (la VM no tiene WiFi): clic en red abierta, red guardada, red con clave y apagar WiFi; **no está probado con una tarjeta WiFi real**.

## Apps propias del escritorio (probadas en VM)
**Calculadora** (`desktop/apps/calculadora`): motor sin `eval` con decimales exactos (40 pruebas en `test_engine.py`), interfaz compacta, historial, modo científico, sigue claro/oscuro y acento.
**Capturadora** (`desktop/apps/capturadora`, reemplaza a Spectacle): `core.py` (grim, slurp, wf-recorder, pw-record, ffmpeg), `editor.py` (lápiz, resaltador, flecha, rectángulo, elipse, texto, números, pixelar, deshacer),
`overlay.py` (modo presentación: dibujo, halo del puntero, ondas al clic; **captura el ratón mientras está activo**), `camera.py` (burbuja redonda con GStreamer; OWEE_CAM_TEST=1 usa imagen de prueba).
Atajos: Impr. Pant. (pantalla), Mayús+Impr. Pant. (zona), Ctrl+Impr. Pant. (ventana de la app), Super+Alt+R / +Mayús (grabar pantalla/zona; repetir = parar), Super+Alt+P (presentación), Super+Alt+C (cámara).
Probado con clics reales: captura, editor (dibujar, guardar, copiar), presentación, grabación MP4 h264 de 6 s con la burbuja de cámara de prueba (`capture-test.py`).
**No probado:** audio del sistema/micrófono (la VM no tiene audio), cámara real, grabar zona, temporizador; la barra de grabación aparece en el vídeo si se graba la pantalla completa; falta captura de una ventana suelta
(labwc no expone captura por ventana todavía) y pausa de grabación.
**Escritorios virtuales:** puntos en el panel, Super+N, Super+Mayús+N, Ctrl+Alt+←/→, rueda sobre el fondo y esquinas activas (Ajustes → Escritorios); la «vista general» es el menú de ventanas de labwc (Super+Tab), sin miniaturas.

## Temas de apariencia (probado en VM)
Siete temas en `owee_config.THEMES` (Koi, Claro, Pizarra, Niebla, Crepúsculo, Arena, Medianoche): fondos suaves (nunca negro ni blanco puro), texto con contraste 11–15:1, cada uno con su acento (se puede cambiar).
Al elegir uno, Ajustes → Apariencia escribe **todo** a partir de la misma paleta: el panel (instantáneo), `kdeglobals` (Qt/KDE: ventana, vistas, botones, selección, tooltips), `gtk.css` de GTK3/4 y libadwaita
(`@define-color`), el tema de barras de título de labwc (`Owee-Tema`) y `gsettings color-scheme`. Las apps propias (Ajustes, Calculadora, Capturadora) usan la paleta directamente.
Probado con Dolphin (tema Arena) y los siete temas en Ajustes. No probado: LibreOffice, Firefox y apps con tema propio.
Capturadora: la ventana principal se cierra y se vuelve a crear tras capturar/grabar (si solo se oculta o minimiza, labwc la vuelve a mostrar sin barra de título).

## Panel: indicador de teclado, modo compacto y fondos (probado en VM)
- **Indicador del teclado** (`InputIndicator` en `owee_panel.py`): muestra con qué escribes (US, ES, 拼, あ, 한, Ow) y su menú deja elegir entre el teclado normal y los métodos activados (pinyin, Mozc, Hangul, Owee):
  `fcitx5-remote -s <método>`. Reemplaza al icono de Fcitx5 de la bandeja (que se oculta). Fcitx5 solo informa del método de la ventana enfocada: sin ventana enfocada se muestra el último conocido.
  Flujo probado en Kate: Owee → glifos, US → texto normal, pinyin → 你好, cambiando desde el panel.
- **Panel compacto** (`owee_windows.py`, protocolo `wlr-foreign-toplevel-management` v3, XML transcrito en `desktop/shell/protocols/`): con la ventana ACTIVA maximizada o a pantalla completa, el panel se pega a los
  bordes, sin margen ni esquinas (como la barra de menús de macOS) y vuelve a flotar al restaurar. Si faltan los enlaces de pywayland, el panel se queda flotante sin romperse.
- **Fondos con presentación** (`session/owee-wallpaper --daemon`): modo «Una imagen fija» o «Presentación» (cada 1 min…1 día, aleatoria u ordenada, con TODAS las imágenes o solo las elegidas); Ajustes → Fondo de pantalla solo guarda
  en `settings.json` y el demonio lo aplica al instante, sin parpadeo. 25 fondos propios en `desktop/wallpapers/fondos/`: 15 paisajes (`generar.py`) y **10 de carpas** hechas con la carpa del logo, con otros colores, cantidades (de 1 a 12) y tamaños (`generar_koi.py`); sin fotos de terceros.
- **Lanzador**: la lista de apps se reconstruye cuando se instala una (p. ej. Bazaar al terminar su instalación en el primer arranque).

## Bluetooth, Usuarios y Acceso (Ajustes, probado en VM con simuladores / el ayudante como root)
- **Bluetooth** (`ajustes/bluetooth.py`, BlueZ con `bluetoothctl`): encender/apagar, lista de dispositivos (conectado / emparejado / disponible), conectar, desconectar, olvidar, buscar y emparejar. Todo asíncrono y con límite de
  tiempo; sin adaptador lo dice y no hace nada. **Widget del panel** `40-bluetooth.py` (oculto sin adaptador; clic: encender/apagar y conectar dispositivos ya emparejados). Probado con `tools/ostree-proto/mock-bluetoothctl`;
  **sin hardware Bluetooth real no se pudo probar** el emparejamiento, el audio (`libspa-0.2-bluetooth`) ni los dispositivos con PIN.
- **Usuarios** (`ajustes/usuarios.py`): lista de cuentas (UID 1000–59999), crear, cambiar contraseña, hacer administrador, eliminar con sus archivos (pide escribir el nombre). Todo lo que cambia cuentas pasa por
  `/usr/libexec/owee/owee-account-helper` con `pkexec` (política `org.oweelinux.accounts`, `auth_admin_keep`): solo órdenes cerradas, nombres validados, **contraseñas por la entrada estándar (nunca en argumentos)**, no toca
  cuentas de sistema, no borra al que lo invoca ni deja el equipo sin administradores (grupo `sudo`). El ayudante se probó como root en la VM (crear, clave, administrador sí/no, errores); **el camino con `pkexec` y la ventana de
  contraseña se verifica con la imagen nueva** (la anterior no traía `pkexec`).
- **Acceso** (`ajustes/acceso.py`): pantalla de bloqueo con los **colores del tema** y, si quieres, el fondo de pantalla (`session/owee-lock` sobre `swaylock`; lo usan Super + L, el menú de apagado, la inactividad y suspender) y
  el **inicio de sesión de SDDM**: entrar sin contraseña con un usuario y una sesión (`/etc/sddm.conf.d/30-owee-autologin.conf`, vía el ayudante). El tiempo de bloqueo sigue en Energía. Probado: bloquear y desbloquear en la VM.
- **Cuentas en línea** (Google, Nextcloud…) **no** se incluyen: pesan (KDE las trae con KAccounts) y no son necesarias para un escritorio ligero; se pueden usar desde el navegador o las apps.

## Teclado en uso: distribuciones, indicador y `owee-layout` (probado en VM)
Ver `docs/IDIOMAS.md`: tabla única de idiomas, teclados árabe/persa/hindi/urdu/indonesio/malayo, `Super + Mayús + Espacio`, indicador del panel con la distribución activa.

## Qué hace falta para que los dos lenguajes sean de primera
- **JavaScript sin Node** = **GJS** (`gjs` 1.82 en Debian 13): se añade a la imagen (~11 MB de descarga). Ya está en `packages-plasma.txt`.
- Una **biblioteca pequeña `owee`** con la misma API en Python y en JavaScript (notificar, leer ajustes, D-Bus, tema) para que
  un script de un lenguaje y el del otro se escriban igual. *Por diseñar.*
- **Plantillas** de app en Python+GTK4, JavaScript+GJS y Python+Qt6 (aspecto nativo junto a las apps de KDE).
- Documentación de una página por nivel y ejemplos "copiar y cambiar".

## Reglas para no romper el sistema
1. El **núcleo es inmutable**: las extensiones viven en `~/.config/owee/` y en `/usr/share/owee/` (solo lectura), nunca modifican el sistema.
2. Nada espera a otra cosa sin tiempo límite (regla de `docs/FASES.md`, F-R).
3. Un fallo se muestra y se aísla; **nunca** tumba el panel ni la sesión.
4. Hay una **sesión segura** y Plasma en el login para recuperarse de una extensión mala.
