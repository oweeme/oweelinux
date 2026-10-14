# Idiomas de OweeLinux

Todo el escritorio Lite se puede usar en **17 idiomas más Owee** (romano y Owee Script): español, inglés, portugués, francés, alemán, italiano, ruso, ucraniano, chino (simplificado), japonés, coreano,
árabe, persa, hindi, urdu, indonesio y malayo. **Interfaz, teclado y métodos de escritura salen de la misma tabla** (`owee_i18n.LANGS` y `LANG_INFO`), así que lo que puedes escribir también lo puedes
elegir como idioma y al revés: `tools/i18n/consistency.py` falla si una distribución de Teclado no tiene idioma, si un idioma no tiene catálogo o locale, o si un método no encaja con su idioma.
Se cambia en **Ajustes → Idioma**; el panel y Ajustes se reinician solos, y las apps abiertas cambian al volver a abrirlas.

## Tabla única de idiomas
`desktop/shell/owee_i18n.py` → `LANGS` (código, nombre propio, locale) y `LANG_INFO` (distribución(es) de teclado, método de escritura, derecha-a-izquierda). Al elegir un idioma se aplican **a la vez**:
locale (`LANG`/`LANGUAGE`), distribución de teclado, método de escritura (chino → pinyin, japonés → Mozc, coreano → Hangul, Owee → teclado Owee) y la cifra de Owee Script.
| Idioma | Teclado (activo primero) | Método | Escritura |
|---|---|---|---|
| es, en, pt, fr, de, it | latam, us, br, fr, de, it | – | izq.→der. |
| ru, uk | US + ru / ua (queda activa la propia) | – | cirílico |
| zh, ja, ko | us, jp, us | pinyin, Mozc, Hangul | CJK |
| ar, fa, ur | US + ara / ir / pk (queda activa la propia) | – | **derecha→izquierda** |
| hi | US + in (InScript; también «Bolnagri» fonético) | – | devanagari |
| id, ms | us; ms: US + `my` (jawi) | – | latino (jawi) |
| qow, qow@owee | us | Owee | romano / Owee Script |

**Teclado: una distribución activa, hasta dos elegidas.** labwc usa UNA a la vez (`XKB_DEFAULT_LAYOUT`); `Super + Mayús + Espacio` (o el indicador del panel) pasa a la siguiente con `owee-layout`
(`desktop/shell/owee_keys.py`: guarda `layouts` y `layout_idx` en `settings.json`, reescribe `~/.config/labwc/environment` y recarga labwc). Así el indicador del panel (US, AR, RU, 拼, あ, 한, Ow…)
dice siempre la verdad. Verificado en VM: escribir «شس» con `ara` y «ав» con `ru` tras cambiar la distribución con Fcitx5 en marcha.

## Cómo funciona
| Pieza | Dónde | Qué hace |
|---|---|---|
| `_("texto en español")` | `desktop/shell/owee_i18n.py` | devuelve el texto en el idioma elegido; marcadores `{0}`, `{1}`…; si falta una traducción se ve el español (nunca falla) |
| Catálogos | `desktop/i18n/<código>.json` → `/usr/share/owee/i18n/` | `{"español": "traducción"}`; el idioma se lee **una vez** al arrancar cada programa |
| Idioma elegido | `~/.config/owee/settings.json` (`lang`) | lo leen panel, Ajustes, Calculadora y Capturadora; `owee-session` lo usa para fijar `LANG` en la sesión siguiente |
| Programas ajenos (KDE, GTK…) | `LANG`/`LANGUAGE` en `~/.config/labwc/environment` y `~/.config/plasma-localerc` | los que se abran después salen en ese idioma (si traen traducción) |
| Locales del sistema | `localedef` en `overlay-lite.sh` (las 17 de la tabla + qow_BO) | calendarios, nombres de mes, diálogos de GTK |
| Fuentes | `fonts-noto-cjk`, `fonts-noto-core`, `fonts-owee` | chino, japonés, coreano, cirílico, árabe/persa/urdu (Naskh), devanagari y Owee Script |
| Escribir | Fcitx5 (`fcitx5-chinese-addons`, `fcitx5-mozc`, `fcitx5-hangul`, `fcitx5-owee`) | perfil en `~/.config/fcitx5/profile`; **Ctrl + Espacio** cambia de método; al elegir un idioma se activa su método |

## Owee
Se toma del proyecto del idioma (<https://github.com/oweeme/owee>, del mismo autor, MIT/CC BY-SA/OFL): `tools/ostree-proto/build-owee-debs.sh` (en el pod) descarga el repositorio y construye
`fonts-owee`, `fcitx5-owee` y `owee-locale`; `tools/i18n/build_owee_catalog.py` genera `qow.json` y `qow@owee.json` para **todos** los textos de la interfaz, con este orden de prioridad:
1. **Glosario del autor** (`ui_glosario.tsv`, coincidencia entera): palabra **oficial** (hoy 58 textos).
2. **Propuesta** (`tools/i18n/owee/p*.py`, 398 textos): frases armadas **solo con raíces del léxico** (`lexico.tsv`, `lexico_ciencias.tsv`) y la Gramática 1.1; el constructor las **valida** (fonología V/CV sin `i` y
   cada raíz en el léxico) y descarta las que no pasen. **Ninguna está aprobada por el autor del idioma**: son el flujo PROPUESTA → VERIFICADA → APROBADA del proyecto, y los nombres de programas van entre «comillas» (§14).
3. Si no hay ninguna, se ve el español.
**Revisión:** `docs/owee-propuestas.tsv` (es, en, owee, origen) se regenera en cada construcción; el autor corrige o aprueba y lo aprobado pasa a `ui_glosario.tsv`. Convenciones usadas en las propuestas:
«X no mora» = «falta X», «X no pe kera» = «no se encontró X», hora = `tera-kedo`, minuto = `tera-kedo-po`, segundo = `tera-kedo-po-po`, días y meses como ordinales (`be-pose loda-kelo` = lunes).

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

## Añadir o corregir un idioma
1. `owee_i18n.LANGS` (código, nombre propio, locale) y `LANG_INFO` (teclado, método, derecha-a-izquierda); si hace falta una distribución nueva, añádela a `LAYOUTS` en `ajustes/teclado.py`; `overlay-lite.sh`: el locale en la lista de `localedef`.
2. Traducciones: `tools/i18n/tr/t*.py` (idiomas históricos, índice → tupla) o `tools/i18n/tr9/a*.py` (idiomas nuevos); el orden de idiomas está en `tools/i18n/build_catalogs.py`, que se ejecuta con `python3 tools/i18n/build_catalogs.py`.
3. Textos nuevos en el código: escríbelos en español dentro de `_()`; `python3 tools/i18n/extract_keys.py` añade las claves nuevas a `keys.json` (las existentes conservan su índice) y `build_catalogs.py` avisa de lo que falta.
4. Comprobaciones: `tools/i18n/consistency.py` (sin GTK) y `tools/i18n/smoke.py` (construye todas las páginas en cada idioma).

## Verificado en VM
`tools/ostree-proto/idiomas-test.py` y `lang-image-test.py` (cambio de idioma en la imagen completa; escribir «nihao» → 你好, «nihongo» → 日本語, «kuma» → dos glifos Owee). Teclados ara y ru en uso real (ver arriba).
**No verificado todavía:** corrección de las traducciones a it, uk, ko, ar, fa, hi, ur, id y ms (hechas sin hablante nativo: **conviene que las revise gente de cada idioma**), Mozc/Hangul en uso real, apps de KDE traducidas,
SDDM en otro idioma, ajuste fino de la interfaz de derecha a izquierda (GTK invierte los cuadros solo; falta revisar el panel y los textos mixtos) y que las propuestas de Owee sean buen Owee (las revisa el autor).
