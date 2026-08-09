# OweeLinux

Distro propia basada en **Debian 13 (Trixie) + KDE Plasma**, con la marca **oweeme**
(logo koi, paleta teal/coral). Pensada para tres tipos de usuario a la vez:
desarrolladores, oficina, y usuarios sin experiencia técnica (incluye chicos de
~10 años) — todo en el mismo sistema, sin perfiles separados.

Principios del proyecto:

- **Cero telemetría**, en cualquier capa del sistema.
- **Estable antes que bleeding-edge** — Debian stable congelado, sin sorpresas de
  rolling release. Fue una decisión explícita después de abandonar un intento
  previo con Arch + Hyprland/COSMIC (ver `docs/PLAN_OWEELINUX.md`).
- **Liviano pero completo** — no se sacrifica funcionalidad real (WiFi, batería,
  Bluetooth, HDMI, tabletas Wacom) solo por bajar el tamaño del ISO.
- Instalable con clicks (instalador gráfico Calamares), sin necesitar terminal.
- Las apps propias (`oweeide`, y las que vengan después) se instalan y actualizan
  vía `apt`, desde un repo APT propio — nunca hace falta reinstalar el sistema
  para tener la última versión.

## Estado actual

v1 funcional para hardware **sin Nvidia** (validado en un HP real): instalación
gráfica de punta a punta, WiFi/batería/Bluetooth/HDMI/audio funcionando, apps
básicas, IDE propio preinstalado, branding completo (splash, login, GRUB, colores).

Pendiente: validar el driver Nvidia (Fase 2) en hardware real con GPU Nvidia.
Ver el detalle completo de qué falta en
[`docs/MANUAL_MODIFICACIONES.md`](docs/MANUAL_MODIFICACIONES.md#estado-y-fases).

## Descargar

_(pendiente: link una vez publicada la ISO)_

## Instalación rápida

1. Grabar la ISO a un pendrive (recomendado: [KDE ISO Image Writer](https://apps.kde.org/isoimagewriter/)).
2. Arrancar la máquina desde el pendrive.
3. Abrir "Instalar OweeLinux" desde el escritorio y seguir el instalador.
4. Si la máquina tiene GPU Nvidia: después de instalar, correr el ícono
   "Instalar driver Nvidia" del escritorio (detecta el hardware automáticamente).

## Para desarrollar / modificar esta distro

Toda la documentación técnica — estructura del proyecto, cómo reconstruir el
ISO, dónde tocar cada cosa, y los bugs reales que nos encontramos en el camino
(y por qué existen sus fixes) — está en
[`docs/MANUAL_MODIFICACIONES.md`](docs/MANUAL_MODIFICACIONES.md).

## Autoría y licencia

OweeLinux es un proyecto de código abierto creado y mantenido por
**Héctor Martínez**, desarrollador boliviano — [oweeme.com](https://oweeme.com).

Se distribuye bajo los términos de la **GNU General Public License v3.0
(GPLv3)**. Esto significa que cualquiera puede usar, estudiar, modificar y
redistribuir este proyecto libremente, siempre que las obras derivadas se
mantengan bajo la misma licencia y se conserve el aviso de copyright
original — el espíritu del copyleft: el software libre que nace de este
proyecto debe seguir siendo libre. El texto legal completo, sin modificar,
está en [`LICENSE`](LICENSE).

```
OweeLinux — un proyecto de Héctor Martínez (oweeme.com)
Copyright (C) 2026 Héctor Martínez

Este programa es software libre: podés redistribuirlo y/o modificarlo
bajo los términos de la Licencia Pública General de GNU publicada por
la Free Software Foundation, ya sea la versión 3 de la licencia, o
(a tu elección) cualquier versión posterior.
```
