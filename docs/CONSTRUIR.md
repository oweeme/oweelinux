# Construir y probar OweeLinux en otra computadora

Necesitas Linux con **Podman** (sin root), **git**, **QEMU con KVM** (`qemu-system-x86`, `qemu-system-gui` para ver la ventana, `ovmf`), unos **40 GB libres** y buena conexión (la primera construcción baja ~2 GB de paquetes).
Nada de esto se ha probado todavía desde cero en otra máquina: si algo falla, el mensaje te dirá qué falta; ábrenos un issue.

## Construir la ISO de instalación (el procedimiento actual)
```bash
git clone https://github.com/oweeme/oweelinux.git && cd oweelinux
tools/devpod/devpod.sh build && tools/devpod/devpod.sh up
podman exec oweelinux-dev bash -c 'cd /work/tools/ostree-proto && ./gen-test-keys.sh'          # una vez: claves de PRUEBA para firmar
podman exec -e OWEE_INSTALLER=1 -e OWEE_TEST_USER=0 -e OWEE_DISK_MIB=12000 oweelinux-dev \
  bash -c 'cd /work/tools/ostree-proto && ./build-image-full.sh /var/tmp/imagen && ./make-iso.sh /var/tmp/imagen /var/tmp/OweeLinux.iso'
podman cp oweelinux-dev:/var/tmp/OweeLinux.iso .
sha256sum OweeLinux.iso > OweeLinux.iso.sha256
```
- Tarda ~25–35 min (la última fase, la compresión de la ISO, ~10–15 min; `ISO_COMP=zstd` la acelera para pruebas a costa de tamaño). La ISO pesa ~1,5 GB. **No se sube a GitHub** (ver `.gitignore`).
- La imagen se construye con la versión del proyecto del idioma Owee fijada en `tools/ostree-proto/build-owee-debs.sh` (`OWEE_REF`); para cambiarla, edita ese commit y regenera los catálogos con `tools/i18n/build_owee_catalog.py RUTA_DEL_REPO_OWEE`.
- Probar en una VM: `tools/usuario/probar-en-qemu.sh OweeLinux.iso --secureboot --nuevo` (instala) y luego `tools/usuario/probar-en-qemu.sh --disco --secureboot` (arranca lo instalado). Grabar a un USB: `tools/usuario/write-usb.sh OweeLinux.iso /dev/sdX`.
- Pruebas de interfaz sin ratón ni pantalla: `tools/ostree-proto/boot-shot.py DISCO_O_ISO prefijo 60 120` guarda capturas y entiende acciones (`BOOT_DO="40:click:x,y;45:rclick:x,y;50:type:texto;55:key:ret;60:drag:x1,y1,x2,y2"`). Para una ISO con consola serie de depuración, edita su `grub.cfg` con `xorriso` añadiendo `console=ttyS0 owee.debug` a la entrada «Probar».

### Problemas conocidos al construir
- **El contenedor se queda sin procesos** («fork: retry: Resource temporarily unavailable»): se acumulan procesos zombi del contenedor. Solución: `podman restart oweelinux-dev` (los archivos de `/var/tmp` se conservan). Evita lanzar muchos `podman exec` de espera en bucle.
- **`build-image-full.sh` se queda colgado después de «publicado»:** detenlo (`pkill -f build-image-full`) y ejecuta a mano `./make-iso.sh /var/tmp/imagen /var/tmp/OweeLinux.iso`; la imagen ya estaba completa.
- **Si faltan los paquetes del idioma Owee** (aviso «sin los paquetes del idioma Owee»), la imagen se construye igual pero sin fuentes ni teclado Owee; ejecuta `./build-owee-debs.sh` dentro del contenedor y reconstruye.
- **Controlador privativo de NVIDIA:** `OWEE_NVIDIA=1` no construye todavía (dkms de nvidia 550 contra el núcleo 6.12.107 falla en la prueba «macros.h»). La imagen usa nouveau.
- Borra lo anterior antes de otra construcción: cada imagen ocupa 6–14 GB en `/var/tmp` del contenedor.

## Imagen de pruebas con usuario automático (la forma antigua, sigue funcionando)
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
