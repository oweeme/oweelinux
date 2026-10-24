# El escritorio de OweeLinux ("Lite"): cómo funcionará

Estado: **diseño** (2026-10-12). Nada de esto está implementado; lo marcado *(verificar)* no se ha probado.
Se apoya en `docs/FASES.md` (F6, F7, F-R), `docs/INTERFAZ.md` (dirección visual) y `docs/RESILIENCIA.md`.
Decisión de plataforma: **GTK4 + libadwaita + `gtk4-layer-shell`, con Python (PyGObject)** como lenguaje principal.

## Idea central
Un escritorio se arma con **muchas piezas pequeñas que hablan entre sí**, no con un programa gigante. Lo nuestro es la
**capa de interfaz** (panel, lanzador, ajustes rápidos, cambio de ventanas); el resto se reutiliza. Plasma sigue
instalado como **segunda sesión** (red de seguridad) mientras "Lite" madura.

## Cómo arranca y qué corre
```
SDDM (login con el tema de OweeLinux) ──elige sesión──► "OweeLinux Lite"
        │
        ▼  owee-session (script): pasa el entorno a systemd --user y arranca el compositor
   labwc  (compositor: ventanas, escritorios, botones a la derecha, esquinas)   [C, empaquetado]
        │
        ▼  graphical-session.target  →  servicios de usuario (systemd los vigila y los reinicia si caen)
   siempre activos:
     owee-panel        panel superior (Python/GTK4 + layer-shell)                 [propio]
     owee-notifd       notificaciones (al principio: mako)                        [reutilizado → propio]
     owee-polkit       ventana de autenticación gráfica (lxqt-policykit o similar)[reutilizado]
     owee-idle         inactividad: bloquear, apagar pantalla, suspender (swayidle)[reutilizado]
   bajo demanda (se arrancan al usarlos y se cierran solos; cero RAM cuando no se usan):
     owee-launcher     lanzador con cuadrícula, categorías y buscador             [propio]
     owee-quicksettings red, audio, brillo, perfil de energía, claro/oscuro       [propio]
     owee-switcher     Alt+Tab con miniaturas, y vista general de ventanas        [propio, difícil]
     owee-corners      esquinas activas (ventanas de 1 píxel por esquina)         [propio]
     owee-capture      capturas y grabación                                       [propio, F7]
     owee-settings     ajustes del sistema                                        [propio]
     owee-lock         bloqueo de pantalla (swaylock/gtklock al principio)        [reutilizado]
Servicios que YA existen y no se reescriben: NetworkManager, UPower, logind, BlueZ, PipeWire/WirePlumber,
power-profiles-daemon, xdg-desktop-portal (+wlr/gtk).
```

## Cómo se comunican
- **D-Bus** (con `Gio`, siempre **asíncrono y con tiempo límite**, regla nacida del caso real de Deepin, `docs/FASES.md` F-R): NetworkManager (`gir1.2-nm-1.0`), UPower (`gir1.2-upowerglib-1.0`), audio (`gir1.2-wp-0.5` o `pipewire-pulse`), MPRIS (`gir1.2-playerctl-2.0`), notificaciones, energía, logind.
- **Wayland**: paneles, lanzador y esquinas usan `layer-shell` (`gtk4-layer-shell`). Lo difícil es lo que **no** es una ventana: **lista de ventanas y escritorios** (Alt+Tab, vista general) y **gestión de pantallas**. Existe `python3-pywayland` 0.4.18 en Debian 13, pero **no sé si cubre bien** los protocolos de lista de ventanas y de salidas *(verificar con un prototipo)*. Plan B: un **pequeño puente** en Rust/C ("owee-wlbridge") que habla Wayland y expone la información por D-Bus al resto.

## Configuración y personalización
- Valores de fábrica en `/usr/share/owee/` (dentro de la imagen, inmutable); los del usuario en `~/.config/owee/` (sobreviven a las actualizaciones).
- **Widgets del panel** como archivos Python en `~/.config/owee/widgets/`: quien sepa Python añade o cambia uno. Si un widget falla, el panel lo **desactiva y avisa**, no se cae.
- Estilos desde un archivo de **tokens de diseño** (colores, radios, sombras) → CSS; el modo claro/oscuro sigue al portal `color-scheme`; los cambios se aplican en vivo.
- Teclado, ratón y pantallas: ajustes de `labwc`/`wlr-randr`/`kanshi` *(verificar)*; escalado y varios monitores a probar.

## Reglas de robustez (de `docs/FASES.md` F-R)
1. Ningún componente espera a otro servicio sin tiempo límite.
2. El bloqueo de pantalla depende solo del compositor y de PAM; nunca de red, audio o energía.
3. Cada servicio de usuario con `Restart=on-failure` y, el panel, con *watchdog* de systemd.
4. Una **sesión segura** ("OweeLinux Safe": compositor + terminal) y **Plasma** siempre disponibles en el login.
5. Prueba obligatoria: **inyección de fallos** (matar red/audio/energía con el panel y el bloqueo en marcha; deben seguir respondiendo en < 2 s).

## Por dónde empezar (camino prudente)
| Versión | Contenido | Esfuerzo | Cómo se comprueba |
|---|---|---|---|
| **v0.0 (prototipo de riesgos)** | En la VM: `labwc` + un panel mínimo en Python/GTK4 con `layer-shell` + prueba de `pywayland` para listar ventanas | Bajo | Mide RAM (Pss), tiempo de arranque, si `layer-shell` funciona, si `pywayland` basta. **Decide si Python vale para el panel** |
| v0.1 | Sesión armada con piezas existentes: labwc + **Waybar** + mako + fuzzel + swaylock + swayidle, con la paleta de OweeLinux | Bajo-medio | Captura y pruebas de fallos; ya es un escritorio usable |
| v0.2 | Lanzador propio (cuadrícula + categorías + búsqueda) | Medio | Captura; arranque bajo demanda < 1 s |
| v0.3 | Ajustes rápidos propios (red, audio, brillo, claro/oscuro) | Medio | Inyección de fallos |
| v0.4 | Cambiador de ventanas, vista general y esquinas activas | Alto | Depende del resultado de v0.0 con Wayland |
| v0.5 | Notificaciones y OSD propios; panel propio sustituye a Waybar si v0.0 lo justifica | Medio | Comparación de RAM con Waybar |
| v1 | Ajustes del sistema, captura propia, tema claro/oscuro con tokens, iconos y tipografía propios | Alto | Beta |

## Riesgos
| Riesgo | Por qué importa | Mitigación |
|---|---|---|
| Python en el panel pesa o arranca lento | Es la única pieza propia que corre siempre | v0.0 mide antes de comprometerse; Waybar de respaldo |
| `pywayland` no basta | Sin lista de ventanas no hay Alt+Tab ni vista general | Puente en Rust/C |
| GTK4 con la Nvidia Pascal | Render por GPU en tarjeta antigua | `GSK_RENDERER=cairo` como alternativa; probar en el Dell |
| Es mucho trabajo para una persona | Un escritorio entero son decenas de piezas | Reutilizar lo existente y reemplazar solo donde aporte identidad |
| Menú global y bandeja de apps Qt/KDE | Dependen de protocolos (`StatusNotifierItem`, `dbusmenu`) que hay que implementar | Empezar con la bandeja de Waybar; menú global en v2 (ver `docs/INTERFAZ.md`) |
| Accesibilidad e idiomas | Un escritorio propio hereda la obligación de soportarlos | GTK4 trae AT-SPI; usar `gettext`; español como idioma base |

## Cómo puede mejorarse
- **Medir siempre:** RAM (Pss), latencia de los componentes y tiempo de arranque de cada versión, comparando con Plasma y con Waybar.
- **Probar con las mismas herramientas de la VM** (capturas, serie, inyección de fallos) en CI.
- Si Python resulta pesado: mismo GTK4 con **Rust (`gtk4-rs`)** para el panel y Python solo para widgets y extensiones.

## Resultado del prototipo de riesgos v0.0 (2026-10-12)
Código en `desktop/`; medición con `tools/ostree-proto/lite-spike.py` (capturas en `docs/img/lite/`). VM de 3 GB con gráficos
**por software**, una sola ejecución por variante, a ~1 minuto de entrar a la sesión. `usada` = `free -m`; Pss = memoria
repartida entre los procesos que comparten bibliotecas.
| Sesión | Memoria usada (total) | Procesos propios de la sesión (Pss) |
|---|---|---|
| **Plasma** (referencia) | **910 MB** | plasmashell 243, kwin_x11 117, kded6 60, Xorg 49, ksmserver 45, polkit-kde 33, portal 26, kioworker 10 ≈ 586 MB |
| **Lite + panel en Python/GTK4** | **441 MB** | panel 42 (Rss 56), labwc 22, swaybg 2, mako 1 ≈ 67 MB |
| **Lite + Waybar** | **453 MB** | waybar 27 (Rss 42), labwc 21, portal 15, swaybg 2, mako 1 ≈ 66 MB |
El sistema base (kernel, systemd, NetworkManager, SDDM…) pesa ~375 MB en las tres. **Lite ahorra ~460 MB (≈ 50 %) frente a Plasma**
en esta VM. El panel en Python cuesta **+15 MB** respecto a Waybar (42 frente a 27 MB de Pss), con reloj, red (NetworkManager,
asíncrono) y batería (UPower); la diferencia en el total queda dentro del ruido de medida.

**Respuestas a los riesgos de la tabla anterior:**
| Riesgo | Resultado |
|---|---|
| ¿Python en el panel pesa demasiado? | **No**: 42 MB de Pss con `GSK_RENDERER=cairo`. **Reevaluar** cuando tenga bandeja, volumen y escritorios. |
| ¿`layer-shell` funciona con labwc? | **Sí**, pero con Python exige `LD_PRELOAD` de `libgtk4-layer-shell.so.0` (si no, sale como ventana normal). `owee_panel.py` se relanza solo con la variable. |
| ¿`pywayland` basta para listar ventanas? | **Para listarlas, sí**: con `ext-foreign-toplevel-list-v1` vio Konsole (título y `app_id`) en una sesión limpia. **Para activarlas o cerrarlas, no**: hace falta `wlr-foreign-toplevel-management`, cuyo XML **no está en Debian** (habría que incluirlo en el proyecto). |
| ¿Botones de ventana a la derecha? | **Sí** (tema y `rc.xml` de labwc; ver capturas). |
| ¿Esquinas redondeadas (`cornerRadius`)? | **No se aprecian** en las capturas con labwc 0.8.3; por revisar. |

**Hallazgos de integración (todos arreglados o anotados):**
1. `python3-pywayland` de Debian 13 **no declara** su dependencia `python3-cffi-backend` (sin ella ni importa) y **no trae ningún protocolo**: los enlaces se generan con `python3 -m pywayland.scanner` desde los XML de `wayland-protocols`.
2. **Debian instala `waybar.service` y `mako.service`** (usuario) que arrancan solos con la sesión gráfica: la sesión Lite los enmascara (`overlay-lite.sh`).
3. **`source` no exporta variables**: `owee-session` cargaba `/etc/owee/lite.env` sin exportarlas y `GSK_RENDERER=cairo`/`WLR_RENDERER=pixman` nunca llegaban a los procesos → el panel parecía pesar **152 MB** (GL por software) en vez de 42 MB, y labwc 122 MB en vez de 22 MB. Corregido con `set -a`.
4. En la VM el renderizador GL **por software** de GTK4 cuesta ~87 MB por ventana (127 frente a 40 MB en una ventana mínima). Con GPU real **no se pagaría**: pendiente de medir en hardware, y de elegir el renderizador por defecto.
5. Para comparar sesiones hay que **detener SDDM y el gestor de usuario** de la sesión anterior; si no, `plasmashell` y `waybar.service` siguen vivos y contaminan la medida.

**Límites:** VM con gráficos por software; una sola ejecución; sin CPU ni latencia; el panel real tendrá más funciones; sin Nvidia.

**Decisión provisional:** el panel en Python/GTK4 **pasa** la puerta de memoria y de integración; se mantiene como camino principal con Waybar de respaldo
(`docs/FASES.md`, 4c ✅). Siguiente: v0.1 (sesión usable con piezas existentes), medir de nuevo con bandeja y volumen, y probar en hardware real.

## ¿GTK o Qt en Python? Decisión y presupuesto de memoria (2026-10-12)
Medido en la sesión Lite de la VM (gráficos por software, **una sola ejecución**; scripts en `tools/bench/toolkit/`).
Ventana mínima con una etiqueta, a los 6 s. USS = memoria **privada** del proceso (lo que se libera al cerrarlo).
| Caso | Rss | Pss | USS |
|---|---|---|---|
| GTK4 (PyGObject, `cairo`) solo | 51 | 39 | 36 |
| Qt6 (PySide6) solo | 56 | 45 | 40 |
| GTK4 con Konsole (Qt) abierta | 51 | 39 | 36 |
| Qt6 con Konsole (Qt) abierta (comparte bibliotecas) | 57 | 40 | **31** |
| 2.º GTK4 con otro GTK4 ya cargado (comparte bibliotecas) | 51 | 30 | **20** |
**Lectura:** la memoria **no decide** entre GTK y Qt: ±10 MB. Compartir bibliotecas ayuda al toolkit que ya está cargado
(Qt con apps de KDE: −9 MB; GTK con otro GTK: −16 MB). La mitad del costo es Python y el motor de ventanas, no el toolkit.

**Dónde se va la memoria de la sesión Lite** (Waybar, procesos agrupados por nombre, Pss): waybar 27, labwc 21,
xdg-desktop-portal 15, systemd 13, sddm 11 + sddm-helper 9, NetworkManager 8, wireplumber 6, udisksd 6, pipewire 6, resto < 3 cada
uno. **Todo el espacio de usuario ≈ 150 MB**. El `used` de `free` (428 MB) incluye además kernel (Slab 47, vmalloc 26…) y archivos
mapeados en caché (Mapped 94 MB), que se pueden recuperar: **para comparar sesiones, el Pss de los procesos es la cifra honesta**.

**Decisión:**
1. **Shell (panel, lanzador, OSD, cambiador de ventanas, esquinas): GTK4 + Python.** Es la única combinación con soporte
   de *layer-shell* usable desde Python hoy (`gtk4-layer-shell`, con `LD_PRELOAD`). En Qt, `layer-shell-qt` está en Debian pero es
   C++ y no trae enlaces para Python *(verificar si el plugin de integración basta para un panel anclado)*.
2. **Apps de los usuarios: GTK4/libadwaita o Qt6/PySide6, a elección.** Plantilla oficial de cada una: GTK4 (coherente con el
   shell) y Qt6 (aspecto nativo junto a las apps de KDE). Evitar PyQt6 (GPL/comercial); PySide6 es LGPL.
3. **Las apps de KDE (Dolphin, Kate, Konsole, Okular…) siguen siendo Qt** y conviven con el shell en GTK; medido: no se molestan.
4. Tener GTK en el panel **abarata las apps GTK** (−16 MB cada una al compartir bibliotecas).

**Presupuesto de memoria (objetivos a vigilar en CI, no promesas):** panel ≤ 50 MB de Pss; sesión (compositor, panel, notificaciones,
autenticación, inactividad) ≤ 120 MB; **todo el espacio de usuario de la sesión Lite ≤ 200 MB** (hoy ≈ 150).

**Palancas para gastar menos, de mayor a menor efecto:**
1. No usar Plasma: ≈ −440 MB (medido).
2. Dieta de servicios (F2): SDDM + ayudante (20 MB) → un gestor de entrada Wayland más pequeño; portales y udisks bajo demanda (~20 MB).
3. **Un solo proceso largo** con varios elementos pequeños (calendario, ajustes rápidos como *popovers* del panel) y procesos **a demanda** para lo pesado
   (lanzador con cuadrícula, ajustes, vista general): cada proceso GTK abierto cuesta 20-36 MB mientras vive.
4. Python: importar con pereza, sin sondeos (señales de GIO), medir con `-X importtime`.
5. Panel en Waybar (−15 MB) o compilado (Rust + gtk4-rs): ganancia pequeña, **no es la prioridad**.
6. Renderizador: con GPU real hay que **medir** `ngl` frente a `cairo`; en la VM el GL por software cuesta ~87 MB por ventana.

## ¿Qué lenguaje con GTK? Medición de Python, JavaScript (GJS), Rust y C (2026-10-12)
Una ventana mínima con una etiqueta (GTK4, `cairo`), a los 6 s, en la sesión Lite de la VM (gráficos por software, **una sola
ejecución**). Fuentes en `tools/bench/toolkit/lang/`. JavaScript es **GJS** (el motor de GNOME), **sin Node**.
| Lenguaje | Rss | Pss | USS (privada) | Coste sobre GTK4 puro |
|---|---|---|---|---|
| **C** (referencia: lo que cuesta GTK4 solo) | 27 | 16 | **13** | — |
| **Rust** (`gtk4-rs` 0.9) | 27 | 17 | **13** | ≈ 0 (binario de 477 KB) |
| **JavaScript** (GJS 1.82) | 47 | 36 | **32** | +19 MB |
| **Python** (PyGObject) | 51 | 39 | **36** | +23 MB |
Arranque en la VM: `python3 -c pass` 37 ms; **`import` de GTK4 en Python 869 ms**; `gjs -c 1` 55 ms (sin GTK); C/Rust: inmediato.

**Lectura:**
- **GTK4 en sí cuesta ~13 MB; el lenguaje interpretado añade ~20 MB por proceso.** Rust no añade nada.
- **GJS no ahorra memoria frente a Python** (−4 MB) y no trae el ecosistema de npm: solo tiene sentido si el público prefiere JavaScript.
- Rust ahorraría **~23 MB por proceso siempre activo** (el panel pasaría de ~42 a ~20 MB) y evitaría ~0,8 s de arranque; cuesta **compilar** para cada cambio (la compilación de `gtk4-rs` tardó 4 min 55 s la primera vez) y los usuarios no pueden retocar un widget sin recompilar.
- **El arranque importa para lo que se abre a menudo**: un lanzador en Python tardaría ~0,9 s en abrirse (VM; en hardware real, menos). Debe vivir **dentro del proceso residente del panel** o ser compilado.

**Decisión:**
1. **Ahora: Python + GTK4 para todo.** Es lo que antes se puede usar y lo que más gente sabe modificar. Con 150 MB de espacio de usuario en total el consumo ya es bajo.
2. **Después, solo donde dé resultado y se haya medido en hardware real:** reescribir en **Rust + `gtk4-rs`** lo que está **siempre activo** o se abre muy a menudo (panel, demonio de notificaciones, lanzador). Python/GJS quedan para herramientas a demanda, apps y extensiones de los usuarios.
3. **JavaScript sin Node (GJS): permitido como opción para apps de usuarios** (plantilla), no como lenguaje del shell. **Node/Electron: no.**
4. Si algún día los widgets de usuario deben convivir con un panel en Rust, hará falta un mecanismo de extensiones (p. ej. un lenguaje de *scripting* embebido); **no se ha evaluado**.

## Iconos y menú del escritorio (clic derecho)
- `desktop/shell/owee_icons.py` muestra la carpeta Escritorio (`xdg-user-dir DESKTOP`, o `~/Desktop`) sobre el fondo: una capa de layer-shell **por debajo de las ventanas**, que respeta el panel. Doble clic abre; clic derecho en un hueco da el menú (Nueva carpeta, Nuevo documento, Seleccionar todo, Pegar, Actualizar, Ordenar por, Configuración del escritorio, Abrir en terminal, Configuración de pantalla, Establecer fondo); clic derecho en un icono da Abrir, Copiar, Cortar, Cambiar nombre y Mover a la papelera. El orden elegido se guarda en `~/.config/owee/desktop.json`.
- Se apaga en Ajustes → Fondo de pantalla («Mostrar iconos en el escritorio», clave `desktop_icons`). Sin él, el clic derecho muestra el menú de respaldo de labwc (`session/labwc/menu.xml`).
- `rc.xml` anula el enlace por defecto de labwc que abría el menú con el clic **izquierdo** sobre el fondo.
- Aún no hay arrastrar y soltar dentro del escritorio ni mover los iconos de sitio (se ordenan solos en columnas).
- Ajustes se puede abrir en una página con `OWEE_PAGE=fondo owee_settings.py`.
- Pruebas en la VM: `boot-shot.py` entiende ahora `rclick:x,y` (clic derecho) además de `click`.
- Teclado en el escritorio: flechas para moverse entre iconos, Intro abre, F2 renombra, Supr manda a la papelera, Ctrl+C/X/V/A. Se abre con la aplicación predeterminada de cada tipo (`/etc/xdg/mimeapps.list`: carpetas con Dolphin y texto/código con Kate).
- Barra de tareas: las ventanas de la misma aplicación se agrupan en un solo icono con el número de ventanas; al pulsarlo se abre la lista (clic central en una fila cierra esa ventana). Así el panel no se llena y el reloj no se desplaza.
- `LD_PRELOAD` (capa de paneles) se quita del entorno en cuanto el panel, la Capturadora, el protector y los iconos la han cargado: los programas que lanzan (terminales, cajas de desarrollo…) ya no escriben «cannot be preloaded» en cada comando.
- Las apps GTK con barra de título propia (p. ej. Flutter) reciben minimizar y maximizar: `gtk-decoration-layout` en `/etc/xdg/gtk-{3,4}.0/settings.ini` y en `~/.config/gtk-*/settings.ini`.
