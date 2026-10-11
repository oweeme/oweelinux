# Prototipo ostree (F3a, F3b) — resultado

Fecha: 2026-10-11. **Estado: F3a y F3b superadas.** Un Debian 13 mínimo arranca desde un
despliegue ostree en QEMU/KVM con UEFI, con `/usr` de solo lectura.

## Qué se probó (`tools/ostree-proto/boot-test.sh`, 4/4 pasa)
- UEFI (OVMF) → GRUB → kernel 6.12.107 → initramfs (dracut + `ostree-prepare-root`) → systemd.
- `/usr` montado `ro`; `touch /usr/x` falla ("Read-only file system").
- `/var` escribible; `/home` es enlace a `var/home`.
- `ostree admin status` muestra el despliegue activo.

## Cómo se reproduce (dentro del pod)
```bash
mmdebstrap --mode=root --variant=minbase \
  --include=systemd-sysv,linux-image-amd64,ostree,dbus trixie ROOTFS http://deb.debian.org/debian
# instalar en ROOTFS (chroot): ostree-boot dracut-core kmod
tools/ostree-proto/prepare-rootfs.sh ROOTFS      # estructura ostree, kernel+initramfs en /usr/lib/modules
tools/ostree-proto/build.sh ROOTFS /var/tmp/ostree-proto   # commit + despliegue + disco UEFI
# en el host:
tools/ostree-proto/boot-test.sh disk.img
```

## Hallazgos
1. **Debian 13 sí trae el arranque de ostree** (`ostree-boot`: módulo dracut, `ostree-prepare-root`, units y GRUB). Requiere initramfs hecho con **dracut**, no `initramfs-tools`.
2. **El árbol necesita `/sysroot` y el enlace `/ostree -> sysroot/ostree`.** Sin ellos `ostree-prepare-root` falla con "failed to MS_MOVE '/sysroot'". Ya lo hace `prepare-rootfs.sh`.
3. **El QEMU de Deepin no trae ROMs** (`linuxboot_dma.bin`, `kvmvapic.bin`): no sirve `-kernel` directo. Se usa OVMF + GRUB, que además es el camino real.
4. **ESP FAT32 pequeña:** con pocos clusters OVMF no la reconoce; se fuerza `-s 1` (clusters de 512 B).
5. **El rootfs tardó ~2,5 horas por la red**, no por CPU. Hace falta una caché de paquetes (apt-cacher-ng o volumen) antes de F1.
6. Todo se crea **sin montar nada ni privilegios** (`mke2fs -d`, `mcopy`, `sfdisk`), así que cabe en el pod rootless y en CI.

## Limitaciones conocidas del prototipo (no es la imagen final)
- Sin entorno gráfico, sin Nvidia, sin Secure Boot, sin Calamares.
- `grub.cfg` escrito a mano a partir de la entrada BLS (la integración real de GRUB con ostree está por hacer).
- `/root` no existe (falta el `tmpfiles` de `var/roothome`); login automático en consola serie solo para pruebas.
- El `/var` del commit se vació y la base de dpkg se guardó en `/usr/share/owee/dpkg-db`; falta definir cómo se construye la imagen real.
- `--no-xattrs` en el commit (por el contenedor rootless): hay que revisar si afecta a capabilities y SELinux/AppArmor.

## F3b — ciclo de actualización por red (`tools/ostree-proto/update-test.sh`, 4/4 pasa)
Flujo: `publish.sh` crea un repo ostree "archive" servible por HTTP → el sistema (release 1)
ejecuta `owee-update` → descarga la release 2 desde `http://10.0.2.2:8000/pub` (el host,
vía red de QEMU) → reinicia → arranca en la release 2 y conserva la 1.
- `ostree admin status` tras reiniciar: release 2 activa (`*`), release 1 marcada `(rollback)`.
- Publicar la release 2 (cambia un solo archivo) importó solo **5 objetos de metadatos y 1 de contenido**: ostree deduplica por contenido, así que actualizar poco cuesta poco.

### Hallazgos de F3b
1. **El menú de arranque no puede ser fijo.** ostree alterna `boot.0` / `boot.1` en cada cambio de despliegues; un `grub.cfg` escrito a mano dejó el sistema en el modo de emergencia tras reiniciar ("Couldn't find specified OSTree root"). Solución del prototipo: `owee-bootcfg` regenera `/boot/owee/grub.cfg` desde las entradas BLS y `owee-update` lo ejecuta tras cada `upgrade`. La integración definitiva (hook de ostree/GRUB, o systemd-boot) queda por decidir.
2. **El remoto de actualizaciones se define una sola vez** (en `/etc/ostree/remotes.d/`, dentro de la imagen). Definirlo también en el repo del sysroot da "Multiple specifications found for remote".
3. **`ostree pull-local` no admite `rama@commit`**: para instalar una versión concreta se trae el commit y se crea la ref a mano (`build.sh DIR COMMIT`).
4. **Seguridad:** el prototipo no firma commits (`gpg-verify=false`) y usa HTTP. **Antes de cualquier uso real hace falta firma y HTTPS.**
5. **Nota de método:** un fallo de la primera prueba (parecía error de actualización) era del montaje (el disco ya estaba en la release 2). Las pruebas deben fijar la versión de partida.

## Pendiente (siguientes sub-fases)
- F3c rollback: manual (elegir la versión anterior en GRUB / `ostree admin`) y **automático** (comprobación de salud tras arrancar la versión nueva).
- F3d corte de energía repetido durante `pull` y durante el cambio de despliegue.
