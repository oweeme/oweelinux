# Publicar actualizaciones de OweeLinux

Las imágenes de producción **no traen ningún servidor ni clave de confianza de prueba**: `/etc/ostree/remotes.d/owee.conf` apunta a una URL HTTPS y exige firma (`gpg-verify=true`). Hasta instalar la clave pública real, cualquier actualización se rechaza (falla cerrado), que es lo seguro.

## Una sola vez
1. **Clave de publicación** (en TU máquina, con contraseña larga): `tools/ostree-proto/gen-release-key.sh`. Guarda una copia cifrada fuera de línea; nunca la subas a un repositorio ni a un servidor de construcción. Publica la huella en tu web.
2. **Servidor**: cualquier alojamiento estático con HTTPS (el repositorio ostree son archivos). Ejemplo: GitHub Pages o un VPS con nginx.
3. **Construir con la URL y la clave**: `OWEE_UPDATE_URL=https://TU-DOMINIO/ostree ./build-image-full.sh …` (la clave `keys/oweelinux.gpg` se incluye sola si existe).

## Cada versión
`ostree commit --gpg-sign=<HUELLA> …`, `ostree summary --update --gpg-sign=<HUELLA>` y subir el repositorio al servidor. Las imágenes instaladas verifican la firma antes de aceptar nada.

## Pruebas locales
`OWEE_DEV_REMOTE=1` al construir deja el servidor local de QEMU (`10.0.2.2`, sin firma) que usan `update-test.sh`, `rollback-test.sh` y `powerloss-test.py`.

## Rotar la clave
Revoca la anterior (`gpg --gen-revoke`), genera otra y publícala **por un canal ya confiable** (una actualización firmada con la clave vieja que instale la nueva en `/usr/share/ostree/trusted.gpg.d/`) antes de retirar la vieja.
