# Seguridad de OweeLinux

## Qué trae por defecto
| Capa | Estado | Dónde |
|---|---|---|
| Sistema inmutable (`/usr` de solo lectura) con vuelta atrás automática | activo | ostree |
| Cortafuegos (nftables): bloquea lo entrante, salvo lo que el usuario abra; saliente y reenvío sin tocar | activo | `session/owee-firewall`, Ajustes → Seguridad |
| Endurecimiento del kernel (`kptr_restrict`, `dmesg_restrict`, BPF sin privilegios, `ptrace_scope`, redirecciones ICMP…) | activo | `/usr/lib/sysctl.d/91-owee-hardening.conf` |
| Secure Boot: shim (Microsoft) → GRUB firmado de Debian → núcleo firmado de Debian | activo en la ISO y en la instalación | `make-iso.sh`, `installer/owee-install-efi` |
| Actualizaciones: HTTPS + firma GPG **obligatoria**, sin clave instalada = rechaza todo (falla cerrado) | activo | `prepare-rootfs.sh`, `docs/ACTUALIZACIONES.md` |
| AppArmor con perfiles base (modo aviso) | activo, base para afinar | paquetes `apparmor`, `apparmor-profiles` |
| Consola serie de depuración (root sin clave) | solo con `owee.debug` en la línea de arranque | `prepare-rootfs.sh` |
| Centinela (señuelo de red pasivo) | **apagado**; se activa en Ajustes → Seguridad | `session/owee-centinela` |

## Centinela (honeypot pasivo)
Escucha en puertos que nadie legítimo usa (23, 445, 3389, 5900, 2222 por defecto; el 22 se deja libre para quien instale un servidor SSH, y se respeta cualquier puerto ya ocupado). Acepta la conexión, lee como mucho 128 bytes, la cierra y la anota. **No hay ningún servicio detrás y no ejecuta ni responde nada de lo recibido.** Dos puertos distintos (o tres intentos) desde una misma dirección en 10 minutos = escaneo: aviso en el panel y, si está activado, bloqueo de esa dirección una hora (nunca bloquea la puerta de enlace). Corre como usuario propio sin privilegios, con solo `CAP_NET_BIND_SERVICE` y `CAP_NET_ADMIN`, y muy acotado por systemd (`ProtectSystem=strict`, filtro de llamadas, 64 MB).

Qué NO es: no atrapa a un atacante que ya esté dentro ni sustituye a un cortafuegos; sirve para enterarte de que alguien te escanea (típico en wifis públicas) y para cortarlo. Si activas un servicio real en uno de esos puertos, Centinela lo respeta (no puede abrir el puerto) y el cortafuegos sigue mandando.

## Todavía NO está
- Cifrado de disco en el instalador (requiere partición `/boot` aparte y `rd.luks` en el initramfs; el GRUB firmado ya trae `cryptodisk`).
- Arranque verificado completo (el initramfs no está firmado, como en Debian). Camino: UKI firmada + TPM.
- Perfiles de AppArmor propios para el navegador.
- Reconstrucción automática y periódica de la imagen (CI).
