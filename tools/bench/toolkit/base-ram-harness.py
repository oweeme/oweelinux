import importlib.util, os, shutil, sys, time
spec = importlib.util.spec_from_file_location("gui", "/home/oweeme/Dev/oweelinux/tools/ostree-proto/gui-boot-test.py")
gui = importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)
W = "/home/oweeme/.cache/oweelinux/vm/litediag"; os.makedirs(W, exist_ok=True); os.chdir(W)
for f in ("ser.sock", "mon.sock"):
    if os.path.exists(f): os.unlink(f)
shutil.copyfile(gui.VARS_SRC, "vars.fd"); open("c.log", "wb").close(); os.environ["QEMU_MEM"] = "3072"
vm = gui.Vm("/home/oweeme/.cache/oweelinux/vm/lite-disk.img", W + "/vars.fd", W + "/c.log")
def sh(c, k, t=90): return vm.run(f"echo MARK_{k}=$({c} | tr '\\n' '|')", k, t)
try:
    assert vm.wait(gui.PROMPT, 240); time.sleep(8)
    vm.run("systemctl stop sddm; loginctl terminate-user oweeuser; systemctl stop user@1000.service; sleep 3; pkill -9 -u oweeuser; sleep 1; echo MARK_ST=ok", "ST", 90)
    vm.run("mkdir -p /etc/owee /etc/systemd/user; ln -sfn /dev/null /etc/systemd/user/waybar.service; ln -sfn /dev/null /etc/systemd/user/mako.service; printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/environment; printf 'PANEL=waybar\\n' > /etc/owee/panel.conf; printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 60)
    time.sleep(60)
    print("free:", sh("free -m | awk '/Mem:/{print \"total=\"$2\" usada=\"$3\" libre=\"$4\" compartida=\"$5\" cache=\"$6}'", "A"))
    print("kernel (meminfo):", sh("awk '/^(Slab|SUnreclaim|KernelStack|PageTables|Shmem|AnonPages|Mapped|Percpu|VmallocUsed):/{printf \"%s=%dMB \", $1, $2/1024}' /proc/meminfo", "B"))
    print("top 16 procesos por Pss (agrupados por nombre):")
    print(sh("for p in /proc/[0-9]*; do n=$(cat $p/comm 2>/dev/null); a=$(awk '/^Pss:/{print $2}' $p/smaps_rollup 2>/dev/null); [ -n \"$a\" ] && echo \"$n $a\"; done | awk '{s[$1]+=$2; c[$1]++} END{for(k in s) printf \"%6d MB  %s (x%d)\\n\", s[k]/1024, k, c[k]}' | sort -rn | head -16", "C", 120))
finally:
    vm.kill()
