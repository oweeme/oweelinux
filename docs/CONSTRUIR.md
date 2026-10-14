# Construir y probar OweeLinux en otra computadora

Necesitas Linux con **Podman** (sin root), **git**, **QEMU con KVM** (`qemu-system-x86`, `qemu-system-gui` para ver la ventana, `ovmf`), unos **40 GB libres** y buena conexión (la primera construcción baja ~2 GB de paquetes).
Nada de esto se ha probado todavía desde cero en otra máquina: si algo falla, el mensaje te dirá qué falta; ábrenos un issue.

```bash
git clone https://github.com/oweeme/oweelinux.git && cd oweelinux
tools/devpod/devpod.sh build && tools/devpod/devpod.sh up            # pod de desarrollo (Debian 13) con el repo en /work
podman exec oweelinux-dev bash -c 'cd /work/tools/ostree-proto && ./gen-test-keys.sh'      # claves de PRUEBA para firmar actualizaciones (una vez)
podman exec -e OWEE_TEST_SESSION=owee-lite.desktop -e OWEE_DISK_MIB=12000 oweelinux-dev bash -c 'cd /work/tools/ostree-proto && ./build-image-full.sh /var/tmp/imagen'   # ~25 min
podman cp oweelinux-dev:/var/tmp/imagen/disk.img ~/oweelinux-disk.img
tools/ostree-proto/run-vm.sh ~/oweelinux-disk.img                      # ventana de QEMU; nada de lo que hagas se guarda
```

- La imagen resultante entra **sola** al escritorio Lite como `oweeuser` (sin contraseña: solo para pruebas; una imagen real no lleva `OWEE_TEST_SESSION` ni el usuario de prueba).
- Cada construcción descarga la última versión del proyecto del idioma Owee (<https://github.com/oweeme/owee>), construye sus paquetes `.deb` y genera los catálogos de traducción con tu glosario.
- La imagen usa ~6 GB; con la tienda de apps (Flatpak) hace falta el disco de 12 GB (`OWEE_DISK_MIB=12000`).
- Para ver el escritorio **sin construir**: `docs/ESCRITORIO.md` explica cómo probar el panel y las apps en una sesión Wayland existente (desarrollo).
- Borra la imagen anterior antes de construir otra: cada una ocupa 6–12 GB (`rm ~/oweelinux-disk.img; podman exec oweelinux-dev rm -rf /var/tmp/imagen`).

## Solo los paquetes de Owee (fuentes, teclado, locale, cifras) en una Debian/Ubuntu/Deepin ya instalada
Se instalan con `apt` desde los `.deb` que construye `tools/ostree-proto/build-owee-debs.sh` (dentro del pod → `/var/tmp/owee-debs/`) o, sin pod, con `08_Integracion/linux/build-debs.sh` del repositorio de Owee.
Comprobado: instalan y se quitan sin errores en un Debian 13 limpio.
