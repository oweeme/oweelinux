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
