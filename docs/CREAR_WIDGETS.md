# Crea tu propio widget para OweeLinux (guía para aprender Python)

Un **widget** es un programa pequeño que escribe una línea en el panel de arriba: la hora de otro país, la batería, el clima, un contador… Para hacer uno
solo necesitas **un archivo de texto** y **Python** (o JavaScript, o shell). No hay que compilar nada, no se puede romper el sistema, y el cambio se ve **al guardar el archivo**.
Es la forma más rápida de aprender a programar haciendo algo que ves y usas todos los días.

## 1. Tu primer widget (2 minutos)
1. Abre una terminal y crea la carpeta de tus widgets (solo la primera vez):
   ```bash
   mkdir -p ~/.config/owee/widgets
   ```
2. Crea el archivo `~/.config/owee/widgets/hola.py` con este contenido:
   ```python
   #!/usr/bin/env python3
   import json
   print(json.dumps({"text": "Hola 👋"}))
   ```
3. Hazlo ejecutable:
   ```bash
   chmod +x ~/.config/owee/widgets/hola.py
   ```
En unos segundos aparece **Hola 👋** en el panel. Para cambiar el texto, edita el archivo y guarda: el panel lo actualiza solo.

**Cómo funciona:** el panel ejecuta tu programa cada pocos segundos y muestra lo que imprime. Lo que imprime debe ser **una sola línea en formato JSON** con al menos `"text"`.
Pruébalo siempre primero en la terminal: `python3 ~/.config/owee/widgets/hola.py` debe imprimir una línea como `{"text": "Hola 👋"}`.

## 2. Un widget que cambia: la hora en Tokio
```python
#!/usr/bin/env python3
# owee-interval: 10
import json
from datetime import datetime
from zoneinfo import ZoneInfo

ahora = datetime.now(ZoneInfo("Asia/Tokyo"))
print(json.dumps({"text": "🇯🇵 " + ahora.strftime("%H:%M"), "tooltip": "Hora en Tokio"}))
```
- La línea `# owee-interval: 10` dice cada cuántos segundos se ejecuta (por defecto, 5).
- `"tooltip"` es el texto que aparece al dejar el ratón encima.
- **Para practicar:** cambia la ciudad (`America/La_Paz`, `Europe/Madrid`…) o muestra dos ciudades en el mismo widget.

## 3. Colores de aviso: la batería
```python
#!/usr/bin/env python3
# owee-interval: 30
import json, glob

def leer(nombre):
    try: return open(glob.glob("/sys/class/power_supply/BAT*/" + nombre)[0]).read().strip()
    except (IndexError, OSError): return None

nivel, estado = leer("capacity"), leer("status")
if nivel is None: print(json.dumps({"text": ""}))        # sin batería (equipo de escritorio): no se muestra nada
else:
    aviso = "warn" if int(nivel) < 20 and estado != "Charging" else ""
    print(json.dumps({"text": f"🔋 {nivel}%", "tooltip": estado, "class": aviso}))
```
`"class": "warn"` pinta el widget como aviso. Un `try/except` evita que un error rompa el widget: si algo falla, el panel muestra `⚠ nombre` y el motivo en el tooltip.

## 4. Un widget con ventanita y botones
El mismo script puede pedirle al panel que dibuje una **ventanita** al hacer clic. Tu programa no dibuja nada: solo describe lo que quiere, y el panel lo dibuja con el estilo de OweeLinux.
```python
#!/usr/bin/env python3
# owee-interval: 5
import json, os, sys

ARCHIVO = os.path.expanduser("~/.cache/mi-contador")
cuenta = int(open(ARCHIVO).read()) if os.path.exists(ARCHIVO) else 0

if len(sys.argv) > 1 and sys.argv[1] == "sumar":           # el panel nos llama así cuando se pulsa el botón
    cuenta += 1
    open(ARCHIVO, "w").write(str(cuenta))
elif len(sys.argv) > 1 and sys.argv[1] == "borrar":
    cuenta = 0
    open(ARCHIVO, "w").write("0")

yo = os.path.abspath(sys.argv[0])
print(json.dumps({"text": f"🔢 {cuenta}", "popup": {"title": "Contador", "items": [
    {"type": "label", "text": f"Llevas {cuenta} clics"},
    {"type": "button", "text": "Sumar uno", "command": [yo, "sumar"]},
    {"type": "button", "text": "Volver a cero", "command": [yo, "borrar"]}]}}))
```
Tipos de elementos para la ventanita: `label` (texto), `button` (botón), `slider` (deslizante: `min`, `max`, `value`; el valor elegido se añade al final del comando), `calendar` y `separator`.
**La idea importante:** el widget **no se queda ejecutándose**. Cada vez que algo ocurre, el panel vuelve a llamar a tu script con otros argumentos, y tu script guarda lo que necesite en un archivo.

## 5. Reglas y trucos
- **Rápido:** tu script tiene **5 segundos** como máximo; si tarda más, el panel lo corta y muestra `⚠`. Si necesitas algo lento (internet, por ejemplo), guarda el último resultado en un archivo y léelo.
- **Una sola línea** de salida. Para depurar, imprime a `sys.stderr` (no se mezcla con el widget) o mira la terminal.
- **Qué hacer si no aparece:** (1) ¿tiene permiso de ejecución (`chmod +x`)? (2) ¿empieza con `#!/usr/bin/env python3`? (3) ¿funciona en la terminal?
- **Orden:** los widgets aparecen en orden alfabético del nombre del archivo; ponle `10-`, `20-`… al principio para ordenarlos.
- **Cambiar uno del sistema:** si dejas en tu carpeta un archivo con el **mismo nombre** que uno de `/usr/share/owee/widgets/`, gana el tuyo. Para volver al original, borra el tuyo.
- **Esta guía** está en tu equipo: `/usr/share/doc/oweelinux/CREAR_WIDGETS.md`.
- **Ejemplos listos para copiar:** `/usr/share/owee/widgets-ejemplos/` (brillo, calendario, contador en JavaScript, carga del equipo, hora UTC).
- **Seguridad:** un widget es un programa tuyo que corre con tus permisos; solo instala widgets de gente en quien confíes.

## 6. Retos para practicar (de fácil a difícil)
1. Muestra la **fecha** con el día de la semana (`strftime("%A %d")`).
2. Muestra el **uso de memoria** leyendo `/proc/meminfo`.
3. Haz un **temporizador** de 25 minutos (Pomodoro) con botones «Empezar» y «Parar» (guarda la hora de inicio en un archivo).
4. Muestra el **clima** de tu ciudad: descarga con `urllib.request` cada 30 minutos y guarda el resultado en un archivo; el widget solo lo lee.
5. Un widget que **cuente los días** que faltan para tu cumpleaños, con un `calendar` en la ventanita.
6. Una **lista de tareas** con `button`s que marcan cada tarea como hecha.

## 7. ¿Y después? Apps completas
Cuando un widget se te quede corto, el siguiente paso es una **app con ventana propia** en Python + GTK4 que usa el mismo tema, los mismos idiomas y los atajos de OweeLinux.
Hay una plantilla en `tools/owee-app-template/` y el resumen de los tres niveles (widgets, widgets con ventanita, apps) en `docs/EXTENSIONES.md`.
