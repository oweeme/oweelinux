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

## Imagen de instalación (Calamares) y primer arranque
```bash
# sistema «real» (sin usuario de pruebas): al arrancar pide crear tu cuenta
podman exec -e OWEE_TEST_USER=0 -e OWEE_DISK_MIB=12000 oweelinux-dev bash -c 'cd /work/tools/ostree-proto && ./build-image-full.sh /var/tmp/imagen'
# imagen de INSTALACIÓN: arranca al instalador (Calamares); instala el sistema en otro disco
podman exec -e OWEE_INSTALLER=1 -e OWEE_TEST_USER=0 -e OWEE_DISK_MIB=12000 oweelinux-dev bash -c 'cd /work/tools/ostree-proto && ./build-image-full.sh /var/tmp/imagen'
# probar el instalador en una VM con un segundo disco vacío (la VM no guarda nada del primero)
truncate -s 10G target.img && qemu-system-x86_64 -enable-kvm -cpu host -m 3072 -machine q35 -snapshot -display gtk -device virtio-vga \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file=vars.fd \
  -drive file=imagen.img,format=raw,if=virtio -drive file=target.img,format=raw,if=virtio,snapshot=off
tools/ostree-proto/boot-shot.py target.img captura 60 120     # arranca el disco instalado como un equipo real y guarda capturas
```

## Solo los paquetes de Owee (fuentes, teclado, locale, cifras) en una Debian/Ubuntu/Deepin ya instalada
Se instalan con `apt` desde los `.deb` que construye `tools/ostree-proto/build-owee-debs.sh` (dentro del pod → `/var/tmp/owee-debs/`) o, sin pod, con `08_Integracion/linux/build-debs.sh` del repositorio de Owee.
Comprobado: instalan y se quitan sin errores en un Debian 13 limpio.
