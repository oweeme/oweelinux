# Desarrollo en OweeLinux: cajas con `owee-dev`

El sistema es de solo lectura, así que los lenguajes y herramientas viven en **cajas** (contenedores Debian con Podman y distrobox, sin permisos de administrador). Dentro de una caja `apt update / upgrade / install` funcionan como en cualquier Debian, y tu carpeta personal se comparte con el sistema.

```
owee-dev init --with python,go,rust,php,java,ada,node   # crea la caja «dev» con esos lenguajes
owee-dev enter                                          # terminal dentro de la caja
owee-dev deb programa.deb                               # instala un .deb (Chrome, Yandex…) en la caja «apps» y lo añade al menú
owee-dev remove paquete                                 # lo quita
owee-dev update                                         # apt upgrade en todas las cajas
owee-dev check                                          # comprueba que Podman puede funcionar
```

Hacer doble clic en un `.deb` abre el mismo asistente. Las descargas reintentan solas si la red falla.

## Verificado y límites
- Probado en una VM sobre el sistema **instalado**: `check`, creación de la caja, PHP 8.4 dentro de ella, carpeta personal compartida y lanzador en el menú.
- **En la sesión «Probar» (en vivo) Podman no funciona**: el disco es una capa en memoria y Podman no puede guardar imágenes ahí. Instala el sistema para usarlo.
- Cada usuario necesita rangos `subuid/subgid`; el asistente de cuentas de OweeLinux los crea (verificado).
- Sin verificar aún: apps gráficas desde cajas, `distrobox-export` en el menú con varias apps, Chrome/Yandex dentro de una caja, Go/Rust/Java/Ada (mismo mecanismo, no probados uno a uno).
