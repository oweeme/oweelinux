# devpod

Pod de Podman (rootless) para trabajar en OweeLinux con las mismas versiones
que la distro (Debian 13). El repo se monta en `/work`.

```bash
tools/devpod/devpod.sh build   # 1ª vez: descarga debian:trixie y construye la imagen
tools/devpod/devpod.sh up
tools/devpod/devpod.sh shell
```

Límites conocidos:
- **`lb build` (live-build) necesita privilegios** (chroot, montajes). En rootless suele fallar; usar `sudo podman run --privileged ...` o una VM.
- **No hay sesión gráfica** en el contenedor: probar la ISO con QEMU.
