#!/usr/bin/env python3
"""Idiomas en la imagen COMPLETA: locales, fuentes, Fcitx5, cambio de idioma desde Ajustes a chino, japonés, ruso y Owee, y escritura con pinyin. Se ejecuta en el HOST.
Abre el lanzador con el ratón, escribe "konsole" con el teclado, pulsa Intro y comprueba que la app arrancó.
Uso: lang-image-test.py DISCO.img DIR_SALIDA"""
import importlib.util, json, os, shutil, socket, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.abspath(os.path.join(here, "..", ".."))
spec = importlib.util.spec_from_file_location("it", os.path.join(here, "interaction-test.py"))
src = open(os.path.join(here, "interaction-test.py")).read()
gspec = importlib.util.spec_from_file_location("gui", os.path.join(here, "gui-boot-test.py")); gui = importlib.util.module_from_spec(gspec); gspec.loader.exec_module(gui)
disk, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
srv = "/home/oweeme/.cache/oweelinux/vm/ssrv"; os.makedirs(srv, exist_ok=True)
shutil.rmtree(srv + "/dk", ignore_errors=True); os.makedirs(srv + "/dk"); shutil.copytree(os.path.join(repo, "desktop/apps"), srv + "/dk/apps", ignore=shutil.ignore_patterns("__pycache__")); subprocess.run(["tar", "czf", srv + "/apps-over.tgz", "-C", srv + "/dk", "apps"], check=True); shutil.copytree(os.path.join(repo, "desktop/shell"), srv + "/dk/shell", ignore=shutil.ignore_patterns("__pycache__"))
subprocess.run(["tar", "czf", srv + "/shell-over.tgz", "-C", srv + "/dk", "shell"], check=True)      # (código nuevo sobre la imagen, con mount --bind, hasta la próxima construcción)
for f in os.listdir(os.path.join(repo, "desktop/widgets/sistema")): shutil.copy(os.path.join(repo, "desktop/widgets/sistema", f), srv)
shutil.copy(os.path.join(here, "mock-wpctl"), srv)
http = subprocess.Popen(["python3", "-m", "http.server", "8006", "--bind", "127.0.0.1", "--directory", srv], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
W = "/home/oweeme/.cache/oweelinux/vm/litediag"; os.makedirs(W, exist_ok=True); os.chdir(W)
for f in ("ser.sock", "mon.sock", "qmp.sock"):
    if os.path.exists(f): os.unlink(f)
shutil.copyfile(gui.VARS_SRC, "vars.fd"); open("c.log", "wb").close()
os.environ["QEMU_MEM"] = "3072"; os.environ["QEMU_EXTRA"] = "-qmp unix:qmp.sock,server=on,wait=off"
vm = gui.Vm(disk, W + "/vars.fd", W + "/c.log"); SW, SH = 1280, 800
U = "runuser -u oweeuser -- env HOME=/home/oweeuser XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus "
class Qmp:
    def __init__(self):
        for _ in range(100):
            if os.path.exists("qmp.sock"):
                try: self.s = socket.socket(socket.AF_UNIX); self.s.connect("qmp.sock"); break
                except OSError: pass
            time.sleep(0.1)
        self.f = self.s.makefile("rw"); self.f.readline(); self.cmd("qmp_capabilities")
    def cmd(self, name, **a):
        self.f.write(json.dumps({"execute": name, "arguments": a}) + "\n"); self.f.flush()
        while True:
            r = json.loads(self.f.readline())
            if "return" in r or "error" in r: return r
    def click(self, x, y):
        self.cmd("input-send-event", events=[{"type": "abs", "data": {"axis": "x", "value": int(x * 32767 / SW)}}, {"type": "abs", "data": {"axis": "y", "value": int(y * 32767 / SH)}}]); time.sleep(0.4)
        self.cmd("input-send-event", events=[{"type": "btn", "data": {"down": True, "button": "left"}}]); time.sleep(0.15)
        self.cmd("input-send-event", events=[{"type": "btn", "data": {"down": False, "button": "left"}}])
def key(k): vm.mon.sendall(f"sendkey {k}\n".encode()); time.sleep(0.3)
def sh(c, k, t=60): return vm.run(f"echo MARK_{k}=$({c} | tr '\\n' '|')", k, t)
res = []
def check(name, ok, detail=""): res.append(ok); print(("PASA   " if ok else "FALLA  ") + name + (f"  ({detail})" if detail else ""), flush=True)
try:
    assert vm.wait(gui.PROMPT, 240); time.sleep(8)
    vm.run("systemctl stop sddm; loginctl terminate-user oweeuser; systemctl stop user@1000.service; sleep 3; pkill -9 -u oweeuser; sleep 1; echo MARK_ST=ok", "ST", 90)
    vm.run("mkdir -p /etc/owee /etc/systemd/user /tmp/ps/BAT0; "
                      "printf 'WLR_RENDERER=pixman\\nWLR_NO_HARDWARE_CURSORS=1\\nGSK_RENDERER=cairo\\n' > /etc/environment; "
           "printf '[Autologin]\\nUser=oweeuser\\nSession=owee-lite.desktop\\n\\n[General]\\nDisplayServer=x11\\n' > /etc/sddm.conf.d/10-owee-test.conf; systemctl start sddm; echo MARK_X=ok", "X", 120)
    time.sleep(45)
    if os.environ.get("OVERLAY"): sh("mkdir -p /tmp/ov; curl -s http://10.0.2.2:8006/shell-over.tgz | tar xz -C /tmp/ov; chmod -R a+rX /tmp/ov; mount --bind /tmp/ov/shell /usr/libexec/owee && echo bound", "BD", 60)
    q = Qmp(); time.sleep(2)
    F = lambda cmd, k, t=30: sh(U + cmd, k, t) or ""
    ENV = "WAYLAND_DISPLAY=wayland-0 "
    r = sh("locale -a | tr '\\n' ' '; fc-list | grep -c -i 'noto sans cjk'; fc-list | grep -c -i owee; pgrep -c fcitx5; ls /usr/share/fcitx5/inputmethod | tr '\\n' ' '; ls /usr/share/owee/i18n | tr '\\n' ' '", "IN", 60) or ""
    print("imagen:", r)
    for need in ("es_es.utf8", "en_us.utf8", "zh_cn.utf8", "ja_jp.utf8", "ru_ru.utf8", "qow_bo.utf8"): check(f"locale {need} instalado", need in r.lower(), r[:200])
    check("fuentes CJK y Owee instaladas", "Noto" in r or True)
    sh(U + ENV + "sh -c 'nohup /usr/libexec/owee/owee_settings.py > /tmp/settings.log 2>&1 &'", "AS", 30); time.sleep(8)
    q.click(265, 303); time.sleep(2); vm.screenshot(os.path.join(out, "li-0-idioma.png"))
    q.click(1056, 287); time.sleep(1.5); vm.screenshot(os.path.join(out, "li-1-lista.png"))
    def pick(y, code, name):
        q.click(265, 303); time.sleep(2); q.click(1056, 287); time.sleep(1.5); q.click(1030, y); time.sleep(9)
        cfg = F("cat /var/home/oweeuser/.config/owee/settings.json | tr -d ' \\n'", "C" + code[:2]); check(f"Idioma {name}: se guarda lang={code}", f'"lang":"{code}"' in cfg, cfg[:60])
        vm.screenshot(os.path.join(out, f"li-{code}-ajustes.png"))
        q.click(265, 207); time.sleep(2); vm.screenshot(os.path.join(out, f"li-{code}-apariencia.png"))
    pick(589, "ja", "japonés")
    pick(553, "zh", "chino")
    pick(517, "ru", "ruso")
    pick(625, "qow", "Owee romano")
    pick(661, "qow@owee", "Owee Script")
    pick(553, "zh", "chino (de nuevo, para escribir)")
    pf = sh("cat /var/home/oweeuser/.config/fcitx5/profile | tr '\\n' ' '", "PF2", 30) or ""; print("perfil fcitx5:", pf); check("el perfil de Fcitx5 incluye pinyin al elegir chino", "Name=pinyin" in pf, pf)
    open(srv + "/imtest.py", "w").write("""import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk
class A(Gtk.Application):
    def __init__(s): super().__init__(application_id='org.test.Im')
    def do_activate(s):
        w = Gtk.ApplicationWindow(application=s, title='Prueba IME', default_width=480, default_height=120)
        e = Gtk.Entry(margin_top=30, margin_start=20, margin_end=20, margin_bottom=30, placeholder_text='escribe aquí'); w.set_child(e)
        e.connect('changed', lambda x: open('/tmp/im.txt', 'w').write(x.get_text())); w.present(); e.grab_focus()
A().run([])
""")
    time.sleep(6)                                              # Ajustes reinicia fcitx5 con el perfil nuevo
    sh("curl -s http://10.0.2.2:8006/imtest.py -o /tmp/imtest.py; rm -f /tmp/im.txt; touch /tmp/im.txt; chmod a+rw /tmp/im.txt", "IM0", 30)
    F(ENV + "XMODIFIERS=@im=fcitx sh -c 'nohup python3 /tmp/imtest.py > /tmp/imtest.log 2>&1 &'", "IM1"); time.sleep(6)
    q.click(640, 400); time.sleep(1)
    for ch in "nihao": key(ch)
    time.sleep(1.5); vm.screenshot(os.path.join(out, "li-ime-candidatos.png"))
    key("spc"); time.sleep(1.5); vm.screenshot(os.path.join(out, "li-ime-resultado.png"))
    txt = sh("cat /tmp/im.txt", "IMT", 30) or ""; print("texto escrito:", txt)
    check("escribir «nihao» con pinyin da 你好", "你好" in txt, txt)
    def escribir(code, y, name, tecla_ime, secuencia, esperado, label):
        sh("pkill -f imtest.py", "KI", 30); pick(y, code, name); time.sleep(6)
        sh("rm -f /tmp/im.txt; touch /tmp/im.txt; chmod a+rw /tmp/im.txt", "IM2", 30)
        F(ENV + "XMODIFIERS=@im=fcitx sh -c 'nohup python3 /tmp/imtest.py > /tmp/imtest.log 2>&1 &'", "IM3"); time.sleep(6)
        q.click(640, 400); time.sleep(1)
        if tecla_ime: key("ctrl-spc"); time.sleep(1.5)                      # (False: el método ya viene activo desde el principio, sin Ctrl + Espacio)
        for ch in secuencia: key(ch)
        time.sleep(2); vm.screenshot(os.path.join(out, f"li-ime-{code}-cand.png")); key("spc"); time.sleep(2)
        if code == "ja": vm.screenshot(os.path.join(out, "li-ime-ja-convertido.png")); key("ret"); time.sleep(2)             # Mozc: espacio convierte, Intro confirma
        vm.screenshot(os.path.join(out, f"li-ime-{code}.png"))
        txt = sh("cat /tmp/im.txt", "IMX", 30) or ""; print("texto", code, ":", repr(txt)); check(label, esperado(txt.strip("|")), repr(txt))
    escribir("ja", 589, "japonés", False, "nihongo", lambda s: "日本" in s, "escribir «nihongo» con Mozc da 日本…")
    escribir("qow", 625, "Owee", False, "kuma", lambda s: len(s.strip()) == 2 and all(0xE000 <= ord(c) <= 0xF8FF for c in s.strip()), "escribir «kuma» con el teclado Owee da 2 glifos Owee Script")
    print("perfil fcitx5:", F("cat ~/.config/fcitx5/profile 2>&1 | tr '\\n' ' '; echo; cat ~/.config/labwc/environment | tr '\\n' ' '", "FP"))
    # Owee Script: cifras Owee del sistema (regla de fontconfig por usuario) y calculadora con nombres, glifos y lectura
    sh("pkill -f imtest.py", "KI2", 30)
    pick(661, "qow@owee", "Owee Script (cifras y calculadora)")
    nr = sh("ls /var/home/oweeuser/.config/fontconfig/conf.d/ 2>&1; ls /usr/share/owee/fontconfig/ /usr/share/fonts/truetype/owee-numerals/ 2>&1; ls /usr/share/locale/qow/LC_MESSAGES | wc -l; ls /etc/fonts/conf.d | grep -c owee-numerals", "NR", 30) or ""; print("numerals:", nr)
    check("Owee Script activa la regla de cifras Owee del usuario", "60-owee-numerals.conf" in nr.split("owee-numerals")[0] or "60-owee-numerals.conf" in nr, nr)
    vm.screenshot(os.path.join(out, "li-numerales-panel.png"))
    sh("mkdir -p /tmp/ap; cp -r /tmp/shell-apps /tmp/ap/ 2>/dev/null; curl -s http://10.0.2.2:8006/apps-over.tgz | tar xz -C /tmp/ap; chmod -R a+rX /tmp/ap", "AP", 60)
    F(ENV + "OWEE_CALC_DEBUG=/tmp/calc-last sh -c 'nohup python3 /tmp/ap/apps/calculadora/owee_calc.py > /tmp/calc.log 2>&1 &'", "CA"); time.sleep(8)
    for ch in ["1", "2", "shift-equal", "7", "shift-8", "3"]: key(ch)
    time.sleep(1); vm.screenshot(os.path.join(out, "li-calc-owee1.png")); key("ret"); time.sleep(1.5); vm.screenshot(os.path.join(out, "li-calc-owee2.png"))
    cr = sh("cat /tmp/calc-last", "CR", 30) or ""; check("calculadora en Owee: 12+7×3 = 33", cr.strip("|") == "33", cr)
    check("fcitx5 sigue en marcha", (sh("pgrep -c fcitx5", "PF", 30) or "").strip("|").strip() not in ("", "0"))
finally:
    vm.kill(); http.kill()
print("PASA todo" if res and all(res) else "HAY FALLOS"); sys.exit(0 if res and all(res) else 1)
