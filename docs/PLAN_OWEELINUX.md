# OweeLinux — Plan de arquitectura (v2: base Debian)

> Reemplaza el plan anterior basado en Arch Linux + Hyprland/COSMIC. Motivo del
> cambio: Arch rolling-release generó demasiada fricción real (Nvidia cortó
> soporte a Pascal en la rama 590+, COSMIC tiene bugs abiertos de gráficos
> híbridos y no existe empaquetado viable en Debian, el ecosistema Hyprland
> cambia muy rápido). El objetivo pasó de "entorno dev de vanguardia" a
> "sistema estable, práctico, que no se rompa solo" — Debian estable + KDE
> Plasma encajan mejor con eso.

## 1. Identidad del proyecto

| Campo | Decisión |
|---|---|
| Nombre | OweeLinux |
| Marca | oweeme |
| Logo | Círculo teal con koi crema/naranja, acentos rojo coral (`oweeme-koi.png`) |
| Público objetivo | Desarrolladores, oficina, y usuarios sin experiencia técnica (incluye niños ~10 años) |
| Valor diferencial | Estable, liviano, práctico, sin telemetría, listo para desarrollo |
| Filosofía | Estabilidad > bleeding edge. FOSS por defecto (excepción documentada: driver NVIDIA propietario cuando el hardware lo requiera) |

## 2. Base técnica

- **Distro base:** Debian 13 (Trixie), rama **stable** — ciclo de updates fijo, sin sorpresas de rolling release
- **Herramienta de build de ISO:** `live-build` (el equivalente de `archiso` para Debian)
- **Escritorio:** KDE Plasma, instalado **mínimo/curado** (no el meta-paquete `kde-full`) — panel, menú, Dolphin, Konsole, Kate, configuración del sistema. Sin Akonadi/Kontact, sin juegos/apps educativas de relleno
- **Kernel:** el de Debian stable; se evalúa sumar `backports` para hardware de ~2 años si el kernel base no lo reconoce bien
- **Firmware no libre:** incluido desde la ISO (Debian 12+ ya lo trae de forma oficial, no es un paso manual)
- **Driver GPU:** a definir en Fase 2 con hardware real — si es necesario Nvidia propietario, evaluar la rama que corresponda al hardware (ver nota Pascal/580.xx del plan anterior, a revalidar en el mundo Debian)

### Hardware objetivo confirmado
Dell G3 3579 — Intel i5-8300H, 16GB RAM, gráficos híbridos Intel UHD 630 + NVIDIA GTX 1050 (Pascal). Segunda máquina similar disponible para pruebas. Debe instalar y andar razonablemente tanto en equipos de ~10 años como de ~2 años.

## 3. Modelo de actualizaciones

Debian estable ya resuelve esto de fábrica, sin necesidad de inventar un modelo propio tipo SteamOS:

- Paquetes congelados durante todo el ciclo de vida de la versión (solo parches de seguridad)
- El usuario actualiza tranquilo con `apt upgrade` sin miedo a que algo se rompa
- Salto de versión mayor de OweeLinux solo cuando Debian publique su siguiente release estable
- Excepción deliberada: los lenguajes de desarrollo (ver sección 6) usan gestores de versión propios (`rustup`, `nvm`, `pyenv`) en vez de los paquetes congelados de Debian, para no quedarse atrás en las herramientas de trabajo diario

## 4. Sin telemetría

- Debian en sí no tiene telemetría por diseño (no se instala `popularity-contest`)
- KDE: `KUserFeedback` forzado a desactivado por config explícita (no confiar en el default)
- Firefox: `policies.json` a nivel sistema desactivando telemetría, estudios, Pocket, crash reporter, mensajería de "recomendaciones"

## 5. Bajo consumo de recursos

KDE tiene fama de "pesado" por el meta-paquete completo, no por el escritorio en sí:

- Paquete curado a mano (sin Akonadi/Kontact/juegos)
- **Baloo (indexador de archivos) desactivado por defecto** — el mayor consumidor de fondo en hardware viejo con disco mecánico
- `zram` en vez de swap en disco (compresión en RAM)
- Sin daemons de fondo innecesarios

## 6. Paquete "dev-ready" preinstalado

Lo que realmente está en el ISO hoy (verificado contra
`livebuild-profile/config/package-lists/oweelinux.list.chroot`):

- **Toolchains:** Python3, Rust (`rustup`), Go, Ada (`gnat`)
- **Gestores de versión:** `rustup`, `pyenv` — en vez de depender de los
  paquetes congelados de Debian
- **Contenedores:** Podman
- **Android:** `adb` + `fastboot`
- **Terminal moderna:** `ripgrep`, `fzf`, `bat`, `starship`, zsh
- **Explorador de archivos:** Dolphin (nativo de KDE, sin agregar nada aparte)
- **Captura de pantalla:** Spectacle (nativo de KDE, sin problemas de
  compatibilidad de portal como tuvimos con Kooha)

**IDE propio:** [oweecode](https://github.com/oweeme/oweecode) (antes
"oweecode", Tauri/Rust) — no viene preinstalado ni empaquetado en el ISO;
se instala aparte desde
[GitHub Releases](https://github.com/oweeme/oweecode/releases).

Editor gráfico, bases de datos, IA local, grabación de video y suite de
oficina quedaron descartados de esta fase por no estar realmente
instalados — si se retoman, van en la sección 12 como pendiente por decidir,
no acá.

## 7. Branding

- Logo koi en: splash de arranque (Plymouth, reutilizable tal cual del trabajo ya hecho), pantalla de login (tema SDDM), splash de sesión de Plasma, wallpaper
- Tema global de Plasma con los colores teal/coral de la marca
- Íconos Papirus con carpetas en teal (mismo mecanismo que ya funcionó, DE-agnóstico)
- Esquema de color de Konsole a juego

## 8. Distribución de apps propias

Decisión deliberada: **las apps propias no van en el ISO**, para no inflar el
tamaño de la descarga. Cada una se instala aparte, por el canal que le quede
mejor:

- **oweecode**: `.deb` publicado directo en
  [GitHub Releases](https://github.com/oweeme/oweecode/releases) del propio
  repo de la app.
- Alternativa disponible si hiciera falta (ej. para que quede instalable vía
  `apt upgrade` sin bajar un `.deb` a mano): empaquetar y subir al repo APT
  propio, igual que ya se hace con WPS Office.

## 9. Repo APT propio

- Herramienta: `reprepro`
- Contenido hoy: WPS Office (redistribuido)
- Se agrega como una entrada más en `sources.list.d`, se comporta como un repo oficial más

## 10. Pipeline de build de la ISO (live-build)

1. Configurar `live-build` con la base Debian 13 + KDE mínimo
2. Curar la lista de paquetes (sección 6), sin meta-paquetes pesados
3. Configurar `airootfs`-equivalente de `live-build` con:
   - Branding (splash, wallpaper, tema, SDDM)
   - Dotfiles de terminal
   - Config de KDE sin telemetría, sin Baloo
4. Generar la ISO
5. Probar en VM antes de hardware real

## 11. Roadmap por fases

- **Fase 1 — Base funcional:** Debian + KDE mínimo booteando en VM
- **Fase 2 — Drivers:** Nvidia (si corresponde) + PRIME en el hardware real (Dell G3 3579)
- **Fase 3 — Dev stack:** toolchains y terminal configurada
- **Fase 4 — Branding:** logo, splash, tema, sin telemetría confirmado
- **Fase 5 — App propia:** oweecode empaquetado como `.deb`, distribuido
  aparte del ISO vía GitHub Releases
- **Fase 6 — Repo propio:** repo APT propio para apps redistribuidas
  (WPS Office) y futuras apps propias que lo necesiten

## 12. Pendiente por decidir

- Paquete exacto de VSCode en Debian (oficial vs repo de terceros)
- Suite de oficina definitiva
- Nombre del repo APT propio (si aplica)
- Si hace falta el kernel de `backports` para el hardware de ~2 años

## 13. Ideas futuras (no comprometidas)

- **Memoria persistente para oweecode**: evaluar `TencentCloud/TencentDB-Agent-Memory`
  (github.com/TencentCloud/TencentDB-Agent-Memory) como posible backend para que
  oweecode tenga memoria entre sesiones de código (chat memory, skills, wiki,
  code-graph). Es una stack de servicios Node.js/Docker que depende de una API de
  LLM externa — no es liviano, no es un simple "agregar paquete". Antes de integrar,
  verificar que no mande nada a servidores de Tencent por defecto (choca con la
  regla de cero telemetría del proyecto si no se confirma). No aplica a la distro
  en sí, solo como posible feature de oweecode a futuro.
