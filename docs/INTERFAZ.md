# Interfaz de OweeLinux — dirección y viabilidad

Estado: **ideas** (2026-10-11). Nada de esto está implementado. La columna "Estado" dice qué se
comprobó y qué hay que verificar; lo marcado *(verificar)* viene de memoria o de documentación y
no se ha probado en esta máquina.

## Dirección visual deseada
- Aspecto limpio tipo macOS, **sin dock**, con una barra superior y menú de aplicación arriba.
- Botones de ventana (cerrar / maximizar / minimizar) **a la derecha**.
- Control de ventanas y de escritorios virtuales cómodo (ajuste a bordes, escritorios, vista general).
- Inspiración, no copia: no se usan iconos, fondos, tipografías ni nombres propiedad de Apple.

## Viabilidad por elemento (labwc + shell en Python/GTK4)

| Elemento | Estado | Cómo |
|---|---|---|
| Botones a la derecha (ventanas del compositor) | Viable *(verificar)* | `labwc` permite configurar la disposición de la barra de título (`<titlebar><layout>`) |
| Botones a la derecha (apps GTK/libadwaita) | Viable | Ajuste `gtk-decoration-layout` (`:minimize,maximize,close`) |
| Botones a la derecha (apps Qt/KDE) | Viable *(verificar)* | Ajuste del tema/estilo de Qt; hay que probarlo con Dolphin y Kate |
| Esquinas redondeadas y sombras | Probable *(verificar en labwc 0.8.3)* | Opciones del tema del compositor |
| Desenfoque / transparencia tipo vidrio | **No** con labwc | wlroots no hace efectos; exigiría otro compositor |
| Escritorios virtuales | Viable | Soportado por `labwc` |
| Ajuste a bordes / mosaico simple | Viable | Acciones de `labwc` |
| Vista general de ventanas (tipo Mission Control) | A construir | App propia en Python con los protocolos de lista de ventanas y captura de Wayland |
| Cambiar entre apps sin dock | Viable | Alt-Tab + lista de ventanas en la barra superior + lanzador (`fuzzel`) |
| **Menú global "universal"** | **Parcial** (ver abajo) | |

## Menú global: no es universal, y conviene saberlo
En macOS cada app entrega su menú al sistema. En Linux **no existe un estándar que todas las
apps cumplan**:
- Apps **GTK3**: sí, con `appmenu-gtk3-module`. Apps **Qt5**: sí, con `libdbusmenu-qt5`.
  Apps **KDE/Qt6**: probable mediante el registro `com.canonical.AppMenu.Registrar` *(verificar)*.
- Apps **GTK4/libadwaita** (la plataforma que recomendamos para el shell): **no**; su diseño
  es una barra de cabecera con un menú propio, y no hay módulo de menú global.
- En Debian 13 existen `vala-panel-appmenu`, `appmenu-gtk3-module`, `appmenu-registrar` y
  `libdbusmenu-qt5` (**no** hay `libdbusmenu-qt6`).

Propuesta por etapas:
1. **v1:** la barra superior muestra el nombre de la app activa; cada app conserva su menú.
2. **v2:** menú global para las apps que lo exportan (GTK3, Qt5, KDE) y, para las demás, un botón de menú de aplicación como alternativa.
3. **Apps propias (`owee-app`):** una pequeña biblioteca que exporte el menú por D-Bus para que el shell lo muestre *(verificar que `Gtk.Application` en GTK4 exporta `org.gtk.Menus` sin necesitar el escritorio)*.

## Lenguajes y distribución: "sin limitaciones"
La imagen es inmutable, así que **las herramientas de desarrollo viven en el directorio del
usuario o en cajas** (distrobox/Podman), no en el sistema. Plan de la matriz de pruebas (F4): para
cada lenguaje, un "hola mundo" que se compile, se ejecute y, si es gráfico, abra una ventana.

| Lenguaje | Dónde vive la herramienta | Apps gráficas | Pendiente de probar |
|---|---|---|---|
| Python | Sistema + `uv`/venv por proyecto | GTK4 (recomendado), Qt (`python3-pyside6`), Tk (`python3-tk`) | Todos están en Debian 13 |
| Rust | `rustup` en `$HOME` | GTK4-rs, Tauri, Qt | Cabeceras de desarrollo en la caja |
| Go | Tarball en `$HOME` o caja | GTK/Qt/Fyne | Idem |
| JavaScript / TypeScript / Vue | `nvm`/`fnm` en `$HOME` | GJS (GTK), Tauri, web | Idem |
| PHP | Caja (Debian/Fedora) | Servidor web local | Idem |
| Ada | `gnat` o Alire en caja | GtkAda | Idem |
| Dart / Flutter | SDK en `$HOME` | Flutter para Linux usa **GTK3**: la imagen debe traer las librerías GTK3 | Idem |
| C / C++ | Compilador en caja | GTK/Qt | Idem |

Instaladores de las apps (cada usuario elige): **Flatpak** (principal), **AppImage** (hay
`libfuse2t64` y `fuse3` en Debian 13; se añadiría `libfuse2t64` a la imagen), binarios portables,
o ejecutar desde la caja de desarrollo. El requisito común es que **funcione en OweeLinux**: que
sus librerías estén en la imagen o vayan incluidas en el paquete.

## oweecode (Rust / Tauri)
- **No hace falta reescribirlo en Python.** Un IDE necesita rendimiento y Rust es adecuado.
- Tauri depende de WebKitGTK (`libwebkit2gtk-4.1-0` existe en Debian 13): se distribuye como Flatpak (el runtime de GNOME lo incluye) o se instala desde sus *releases*, como hoy.
- Python tiene más sentido como **lenguaje de extensiones** de oweecode (que los usuarios lo personalicen) que como reemplazo.
- Pendiente: comprobar que arranca en la imagen real y medir su tiempo hasta la primera ventana.

## Inspiración: qué tomar de cada sistema (ideas, sin priorizar)
Dirección acordada: un equilibrio entre **elementary OS** (sencillez y guías de diseño claras),
**macOS** (menú superior, búsqueda, vista de ventanas) y **Deepin** (pulido visual y centro de
control), con la flexibilidad de **KDE**. Iconos y tipografía **propios**.

| Idea | Origen | Cómo encaja en OweeLinux |
|---|---|---|
| Guía de diseño para las apps (espaciado, botones, menús) | elementary (HIG) | `owee-app` con una guía propia y plantillas que la cumplen |
| Búsqueda universal de apps, archivos y cálculos | macOS (Spotlight), KDE (KRunner) | Lanzador (`fuzzel` al principio) con extensiones en Python |
| Vista general de ventanas y escritorios | macOS (Mission Control), elementary | App propia sobre los protocolos de Wayland (ver tabla anterior) |
| Centro de control único | Deepin | App de ajustes en Python/GTK4 que abre los ajustes de red, energía, pantalla, actualizaciones |
| Volver atrás en el tiempo | macOS (Time Machine), Deepin (instantáneas) | **Ya existe para el sistema** (ostree + rollback); falta lo mismo para `/home` |
| Vista previa rápida de archivos | macOS (Quick Look) | Pieza opcional, más adelante |
| Captura y grabación de pantalla | macOS, Deepin | `owee-capture` (ver F7) |
| Tienda de apps cuidada | elementary (AppCenter), Deepin | Flatpak con una lista curada (el manifiesto de "Apps recomendadas" ya existe) |

### Iconos y tipografía propios
- **Iconos:** un tema siguiendo el estándar freedesktop (SVG + `index.theme`). Es mucho trabajo si se hace completo, así que el tema **hereda** de otro (`Inherits=`) y solo sustituye los iconos que ya estén dibujados; los demás se ven con el tema base en vez de quedar vacíos. Empezar por los del sistema (carpetas, archivos, ajustes, red, batería) y los de las apps propias.
- **Tipografía:** diseñar una fuente completa es un proyecto en sí mismo. Camino práctico: empezar con una fuente de licencia libre (OFL) y dejar la propia como proyecto posterior. Si algún día se deriva una fuente OFL, la licencia suele exigir cambiarle el nombre.
- Todo bajo licencia libre compatible con GPLv3 (iconos y fuentes se suelen licenciar aparte, p. ej. CC-BY-SA y OFL).

## Referencia visual 1: tema de KDE en pling.com (imágenes aportadas por el autor)
Qué se vio (las tres imágenes se recibieron después directamente del autor; ver también la sección siguiente):
- Tema oscuro, ventanas **semitransparentes con esquinas redondeadas**, fondo ilustrado grande.
- Barra superior **flotante** (con los extremos redondeados), logo a la izquierda, **fecha y hora centradas**, bandeja a la derecha (notificaciones, volumen, desplegable).
- En `plasma1.jpg`, menús de aplicación arriba (tipo menú global) y un **lanzador a pantalla parcial**: cuadrícula de apps, lista de categorías a un lado y buscador.
- Botones de ventana como **círculos de colores a la derecha**.
- Terminal con prompt de colores y carpetas de colores pastel en el gestor de archivos.
Decisión del autor: tomar esta estética **sin dock**, con el Alt+Tab de KDE (elegir ventana) y **esquinas activas** para ver ventanas y escritorios.

| Elemento | Viabilidad con labwc + Python/GTK4 |
|---|---|
| Barra flotante redondeada, reloj centrado, bandeja | Viable: capa `layer-shell` con márgenes y CSS (o Waybar con CSS) |
| Lanzador con cuadrícula, categorías y buscador | Viable: app propia en Python/GTK4 (`fuzzel` solo da una lista) |
| Ventanas semitransparentes con esquinas redondeadas | Transparencia: viable en apps que la soporten. Esquinas: *(verificar labwc 0.8.3)*. **Sin desenfoque** |
| Botones de ventana redondos de colores a la derecha | Probable: tema de `labwc` con botones propios *(verificar)* |
| Alt+Tab con elección de ventana (miniaturas como KDE) | *(verificar)* el conmutador de `labwc` puede mostrar iconos; miniaturas exigirían uno propio (protocolos de lista de ventanas y captura de Wayland, y gestionar la tecla Alt) |
| **Esquinas activas** | `labwc` no las trae. Se pueden hacer con ventanitas de 1 píxel en cada esquina (`layer-shell`) que disparen la acción al entrar el puntero *(verificar; ojo con pantalla completa)* |
| Vista general de ventanas y escritorios | App propia (ver tabla anterior) |
| Menú global en la barra | Solo apps que lo exporten (ver sección del menú global) |

Nota de licencia: son obras de otro autor. Se toman como **inspiración**; si algún día se reutiliza algo (iconos, fondos, colores exactos), hay que revisar su licencia en pling antes.

## Referencia visual 2: las tres capturas completas y el modo claro/oscuro
Las tres imágenes muestran el mismo tema: (1) escritorio con barra flotante y widgets, (2) variante
oscura con menú global, lanzador y barra de medios, (3) comparación **claro / oscuro** partida en
diagonal (la diagonal es solo la comparación, no una función).

Rasgos de estilo que se toman como inspiración (con paleta e iconos propios):
- Ventanas oscuras **azul marino** con esquinas redondeadas (~10 px) y sombra suave.
- **Botones de ventana redondos y de colores a la derecha** (verde azulado, violeta, rosa).
- Acentos **pastel** (carpetas, selección).
- Barra superior flotante; lanzador en panel con cuadrícula, categorías, buscador y botones de energía.
- Variante clara: superficies azul muy pálido/blanco, **la terminal sigue oscura** en ambas.
- Extras de la referencia: widgets de música con visualizador y reproductor, y un dock inferior (**este último no se usa**).

### Cómo se ve OweeLinux con identidad propia
La referencia aporta la **estructura** (barra flotante, ventanas redondeadas, botones de color a la
derecha, lanzador con cuadrícula). El **color** sale del propio koi: verde azulado (teal), coral y
crema, que ya existen en el esquema `OweeLinux.colors` del repositorio. Botones de ventana
propuestos: teal, ámbar/crema y coral.

### Modo claro y oscuro: una sola fuente de verdad
Para que cambiar entre claro/oscuro (y de acento) sea barato y todo quede coherente, la idea es un
archivo de **tokens de diseño** (colores, radios, sombras, tipografía) del que se **generan**:

| Destino | Qué se genera |
|---|---|
| Apps GTK4/libadwaita | Colores con nombre en `~/.config/gtk-4.0/gtk.css` y el ajuste `color-scheme` |
| Apps Qt/KDE | Esquema de color (`.colors`), como el que ya existe |
| Compositor (`labwc`) | Tema de ventanas (colores, botones, esquinas) |
| Shell propio | Hoja de estilos del panel, lanzador y ajustes rápidos |
| Terminal | Esquema de colores (Konsole, y el prompt de `starship`) |
| Fondos de pantalla | Pareja clara/oscura de cada fondo |

El selector claro/oscuro/automático (por hora del día) viviría en los ajustes rápidos. Los portales
(`org.freedesktop.appearance`) permiten que las apps modernas sigan el cambio **sin reiniciarse**;
las que no lo soporten se verán con su tema anterior hasta reabrirse *(verificar con Qt/KDE)*.

### Advertencias de viabilidad
- **Sin desenfoque** (labwc): la referencia usa transparencia con desenfoque; sin él, los paneles translúcidos se ven sucios. El diseño debe apoyarse en **superficies casi opacas** con sombra.
- **Esquinas redondeadas en apps Qt**: salen del compositor o de un estilo (p. ej. Kvantum); *(verificar con labwc 0.8.3)*.
- Los **widgets de escritorio** (visualizador, reproductor) son opcionales y cuestan RAM: nacerían como piezas separadas, de activación perezosa (MPRIS por D-Bus + `cava`).
- Un prompt de terminal como el de la imagen necesita símbolos de una fuente "Nerd Font" (licencia OFL, pero añade peso a la imagen).
