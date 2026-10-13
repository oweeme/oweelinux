# Idiomas de OweeLinux

Todo el escritorio Lite se puede usar en **español, inglés, portugués, francés, alemán, ruso, chino (simplificado), japonés y Owee** (en romano y en Owee Script), y se puede **escribir**
en chino (pinyin), japonés (Mozc), coreano (Hangul) y Owee. Se cambia en **Ajustes → Idioma**; el panel y Ajustes se reinician solos, y las apps abiertas cambian al volver a abrirlas.

## Cómo funciona
| Pieza | Dónde | Qué hace |
|---|---|---|
| `_("texto en español")` | `desktop/shell/owee_i18n.py` | devuelve el texto en el idioma elegido; marcadores `{0}`, `{1}`…; si falta una traducción se ve el español (nunca falla) |
| Catálogos | `desktop/i18n/<código>.json` → `/usr/share/owee/i18n/` | `{"español": "traducción"}`; el idioma se lee **una vez** al arrancar cada programa |
| Idioma elegido | `~/.config/owee/settings.json` (`lang`) | lo leen panel, Ajustes, Calculadora y Capturadora; `owee-session` lo usa para fijar `LANG` en la sesión siguiente |
| Programas ajenos (KDE, GTK…) | `LANG`/`LANGUAGE` en `~/.config/labwc/environment` y `~/.config/plasma-localerc` | los que se abran después salen en ese idioma (si traen traducción) |
| Locales del sistema | `localedef` en `overlay-lite.sh` (es_ES, en_US, pt_BR, fr_FR, de_DE, ru_RU, zh_CN, ja_JP, qow_BO) | calendarios, nombres de mes, diálogos de GTK |
| Fuentes | `fonts-noto-cjk`, `fonts-noto-core`, `fonts-owee` | chino, japonés, cirílico y Owee Script |
| Escribir | Fcitx5 (`fcitx5-chinese-addons`, `fcitx5-mozc`, `fcitx5-hangul`, `fcitx5-owee`) | perfil en `~/.config/fcitx5/profile`; **Ctrl + Espacio** cambia de método; al elegir un idioma se activa su método |

## Owee
Se toma del proyecto del idioma (<https://github.com/oweeme/owee>, del mismo autor, MIT/CC BY-SA/OFL): `tools/ostree-proto/build-owee-debs.sh` (en el pod) descarga el repositorio y construye
`fonts-owee`, `fcitx5-owee` y `owee-locale`; `tools/i18n/build_owee_catalog.py` genera `qow.json` y `qow@owee.json` a partir de su **glosario de interfaz** (`ui_glosario.tsv`).
Una cadena solo se traduce si coincide **entera** con el glosario: hoy 27 de 351; el resto se ve en español. No se inventa vocabulario: para ampliar Owee hay que aprobar términos en el proyecto del idioma.

## Escribir en Owee (como el pinyin en chino)
Con un idioma que tiene método de escritura (chino, japonés, Owee) Ajustes activa el método **desde el principio** (`ActiveByDefault` de Fcitx5): se escribe en romano y se ve en Owee Script, sin pulsar Ctrl + Espacio
(Ctrl + Espacio sigue alternando con el teclado normal). Las apps GTK y Qt usan el protocolo nativo de Wayland, así que **no** se fijan `GTK_IM_MODULE` ni `QT_IM_MODULE` (con ellas Fcitx5 muestra «Wayland Diagnose»).
Fcitx5 no relee su perfil en marcha: Ajustes le pide salir, espera, escribe el perfil y lo vuelve a lanzar. **Teclado → Métodos de escritura** activa o quita cada método y el modo «activo desde el principio».

## Calculadora y cifras en Owee
Con el idioma **Owee** la Calculadora usa la disposición del proyecto del idioma (7 8 9 arriba) con el nombre bajo cada tecla (cho, be, du, ga, fo, sa, ku, mu, na, she; faku, kebu, dopo, dapa, se, doto) y una **lectura en voz alta**
del número o la operación («ga tanu ga» = 33); con «Owee (Owee Script)» las cifras salen en glifos. `calc_owee.py` es un port de `calculadora.js` del proyecto del idioma (comprobado igual en 226 números).
Con «Owee (Owee Script)» Ajustes también activa por usuario la regla de **cifras Owee** (fuente `owee-numerals`, `~/.config/fontconfig/conf.d/60-owee-numerals.conf`): reloj, calendario y apps muestran sus números en Owee; en cualquier otro idioma se quita.

## Apps ajenas en Owee
`gettext_rellenar.py` (del proyecto del idioma) genera, al construir la imagen, catálogos `qow` y `qow@owee` para las apps instaladas a partir del glosario (`/usr/share/locale/qow*/`): con el idioma Owee las apps de KDE/GTK muestran en Owee lo que el glosario cubre y el resto en español.
**Glosario:** `docs/glosario-owee-pendiente.tsv` lista las etiquetas de la interfaz de OweeLinux que aún no tienen palabra en Owee (columnas en, es, owee); al aprobarlas en `ui_glosario.tsv` del proyecto del idioma, aparecen en la siguiente construcción.

## Añadir o corregir un idioma
1. `owee_i18n.LANGS`: añade `(código, nombre en su idioma, locale)`; `overlay-lite.sh`: añade el locale a la lista de `localedef`; `owee-session`: una línea en el `case`.
2. Traducciones: `tools/i18n/tr/t*.py` (una tupla por texto; el orden de idiomas está en `tools/i18n/build_catalogs.py`) y `python3 tools/i18n/build_catalogs.py`.
3. Textos nuevos en el código: escríbelos en español dentro de `_()`; `tools/i18n/wrap_strings.py archivo.py` envuelve los de un archivo nuevo; añade la clave a `tools/i18n/keys.json` y su traducción.
4. Comprobación: `tools/i18n/smoke.py` (construye todas las páginas en los 10 idiomas y cuenta lo que falta por traducir).

## Verificado en VM
`tools/ostree-proto/idiomas-test.py` (cambio a English, 14 páginas × 10 idiomas sin errores) y `lang-image-test.py` (imagen completa: locales, fuentes, cambio a japonés, chino, ruso, Owee y Owee Script,
y escribir «nihao» → 你好, «nihongo» → 日本語, «kuma» → dos glifos Owee). **No verificado:** coreano, teclado ruso en uso real, apps de KDE traducidas, pantalla de inicio de sesión (SDDM) en otro idioma,
y ningún idioma más allá de los diez (árabe y hebreo necesitan escritura de derecha a izquierda, aún sin revisar).
