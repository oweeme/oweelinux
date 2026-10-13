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

## Ajustes de OweeLinux (probado, v0.1)
App propia `owee_settings.py` (Python + GTK4, sin libadwaita) con **Apariencia** (modo claro/oscuro y 6 colores de acento) y **Fondo de pantalla** (miniaturas de las carpetas
de fondos + «Elegir otra imagen…»). Escribe `~/.config/owee/settings.json` (se puede editar a mano; si falta o está dañado se usan los valores de fábrica).
- El **panel vigila ese archivo** y cambia al instante (colores, texto sobre el acento claro/oscuro, y el tema de iconos `Owee` ↔ `Owee-Light`), sin reiniciar.
- El fondo lo cambia `owee-wallpaper` (reinicia `swaybg`); al iniciar sesión se usa el elegido.
- Apps GTK: `gtk-application-prefer-dark-theme` en `~/.config/gtk-{3,4}.0/settings.ini`; apps Qt/KDE: esquema Breeze/BreezeDark con `kwriteconfig` si existe (tomado al abrir la app de nuevo; **este último paso no está probado**).
- Pendiente: color de acento en apps ajenas, tema de las ventanas de labwc (hoy fijo), tipografía propia, apariencia automática por hora, más ajustes (pantalla, teclado, red).
Prueba: `tools/ostree-proto/settings-test.py` (clics reales en la VM: modo, acento, fondo; capturas `ajustes-*.png`).

## Lista de WiFi (probada con `nmcli` simulado)
El widget de red muestra las 8 redes más fuertes (una por nombre), marca la conectada, las guardadas y las que piden clave. Conectar se lanza **aparte** (tarda más que el límite de 5 s del panel).
Nuevo tipo de elemento de ventanita: `{"type":"entry","password":true,"command":[...]}` (al pulsar Intro se llama al comando con el texto como último argumento).
Prueba: `tools/ostree-proto/wifi-test.py` con `mock-nmcli` (la VM no tiene WiFi): clic en red abierta, red guardada, red con clave y apagar WiFi; **no está probado con una tarjeta WiFi real**.

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
