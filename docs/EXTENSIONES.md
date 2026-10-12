# Extensiones y personalización de OweeLinux

Principio (del autor, 2026-10-12): **un Linux es usable y modificable según su filosofía**. En OweeLinux, cualquiera que sepa
**Python o JavaScript** debe poder cambiar el escritorio y escribir apps **sin compilar** y **sin poder romper el sistema**.
Detalles de lenguajes y memoria: `docs/ESCRITORIO.md` ("¿Qué lenguaje con GTK?").

## Tres niveles, de menos a más poder
| Nivel | Qué es | Lenguajes | Cuesta (memoria) | Estado |
|---|---|---|---|---|
| **1. Widgets de script** | Un ejecutable que imprime una línea JSON; el panel la muestra | **Python, JavaScript (GJS), shell o cualquier otro** | ≈ 0 residente (el script solo vive un instante) | **Prototipo probado** |
| **2. Widgets nativos** | Código dentro del proceso del panel (popovers, ventanas propias) | Python (dentro del panel) | pocos MB | Por diseñar |
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
