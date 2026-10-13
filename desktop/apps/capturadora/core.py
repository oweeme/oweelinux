"""Capturadora de OweeLinux — núcleo sin interfaz: capturas con grim/slurp y grabación de vídeo con wf-recorder + audio con pw-record (se mezcla con ffmpeg).
Todas las órdenes son procesos externos con tiempo límite; ninguna se espera en el hilo de la interfaz (el llamador usa `run_async`)."""
import datetime, json, os, shutil, signal, subprocess, threading, time
from owee_i18n import _
HOME = os.path.expanduser("~")
def _dir(kind, fallback):
    """Carpeta estándar del usuario (XDG): Pictures/Videos si no hay otra configurada (no depende del idioma de la interfaz)."""
    from gi.repository import GLib
    return GLib.get_user_special_dir(kind) or os.path.join(HOME, fallback)
def dirs():
    from gi.repository import GLib
    return (os.path.join(_dir(GLib.UserDirectory.DIRECTORY_PICTURES, "Pictures"), "Screenshots"), os.path.join(_dir(GLib.UserDirectory.DIRECTORY_VIDEOS, "Videos"), "Screen Recordings"))
DIR_IMG, DIR_VID = dirs()
CFG = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "owee", "capture.json")
DEFAULTS = {"timer": 0, "cursor": False, "clipboard": True, "fps": 30, "audio_system": True, "audio_mic": False, "camera": False, "quality": "media"}

def load_cfg():
    try: d = json.load(open(CFG))
    except (OSError, ValueError): d = {}
    return {**DEFAULTS, **{k: v for k, v in d.items() if k in DEFAULTS}}

def save_cfg(d):
    os.makedirs(os.path.dirname(CFG), exist_ok=True); tmp = CFG + ".tmp"; open(tmp, "w").write(json.dumps(d, indent=1)); os.replace(tmp, CFG)

def stamp(): return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
def have(p): return shutil.which(p) is not None

def select_region():
    """Deja elegir una zona con el ratón (slurp). Devuelve 'x,y WxH' o None si se cancela (Esc)."""
    if not have("slurp"): return None
    r = subprocess.run(["slurp", "-d", "-b", "#10201966", "-c", "#2A9D8Fff", "-s", "#2A9D8F33", "-w", "2"], capture_output=True, text=True, timeout=120)
    g = r.stdout.strip()
    return g if r.returncode == 0 and g else None

def shot(geometry=None, cursor=False, path=None):
    """Hace una captura (toda la pantalla o `geometry`). Devuelve la ruta del PNG o lanza RuntimeError con un mensaje legible."""
    if not have("grim"): raise RuntimeError(_("Falta «grim» (captura de pantalla de Wayland)."))
    os.makedirs(DIR_IMG, exist_ok=True); path = path or os.path.join(DIR_IMG, f"captura-{stamp()}.png")
    cmd = ["grim"] + (["-c"] if cursor else []) + (["-g", geometry] if geometry else []) + [path]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or not os.path.exists(path): raise RuntimeError(_("No se pudo capturar la pantalla: ") + (r.stderr.strip() or _("error desconocido")))
    return path

def copy_image(path):
    if not have("wl-copy"): return False
    with open(path, "rb") as f: subprocess.run(["wl-copy", "--type", "image/png"], stdin=f, timeout=10)
    return True

def audio_sources():
    """(sistema_monitor, micrófono) disponibles según wpctl; None si no hay. Se usan los nombres «@DEFAULT_...@» de PipeWire."""
    if not have("wpctl"): return None, None
    def ok(t):
        try: return subprocess.run(["wpctl", "inspect", t], capture_output=True, timeout=3).returncode == 0
        except Exception: return False
    return ("@DEFAULT_AUDIO_SINK@" if ok("@DEFAULT_AUDIO_SINK@") else None), ("@DEFAULT_AUDIO_SOURCE@" if ok("@DEFAULT_AUDIO_SOURCE@") else None)

class Recorder:
    """Grabación de pantalla. start() lanza wf-recorder (vídeo) y, si se pide, pw-record por cada fuente de audio; stop() cierra con SIGINT (así los archivos quedan válidos),
    mezcla el audio con ffmpeg y deja un MP4 en ~/Videos/Screen Recordings. Un fallo en una fuente de audio no estropea el vídeo."""
    def __init__(self): self.procs = []; self.tmp = None; self.out = None; self.t0 = 0; self.running = False

    def start(self, geometry=None, fps=30, system=False, mic=False):
        if not have("wf-recorder"): raise RuntimeError(_("Falta «wf-recorder» (grabación de pantalla)."))
        os.makedirs(DIR_VID, exist_ok=True); self.out = os.path.join(DIR_VID, f"grabacion-{stamp()}.mp4"); self.tmp = os.path.join("/tmp", f"owee-rec-{os.getpid()}-{stamp()}")
        os.makedirs(self.tmp, exist_ok=True); self.audio = []
        v = ["wf-recorder", "-f", os.path.join(self.tmp, "video.mkv"), "-r", str(fps), "-c", "libx264", "-p", "preset=veryfast", "-p", "crf=24", "-p", "pix_fmt=yuv420p"] + (["-g", geometry] if geometry else [])   # el puntero se graba por defecto
        self.procs = [subprocess.Popen(v, stdout=subprocess.DEVNULL, stderr=open(os.path.join(self.tmp, "wf.log"), "w"), start_new_session=True)]
        sys_t, mic_t = audio_sources()
        if system and sys_t:
            self.audio.append(self._pw("sistema", sys_t, True))
        if mic and mic_t:
            self.audio.append(self._pw("mic", mic_t, False))
        self.t0 = time.time(); self.running = True
        time.sleep(0.6)
        if self.procs[0].poll() is not None:
            err = open(os.path.join(self.tmp, "wf.log")).read().strip()[-300:]; self.cleanup(); raise RuntimeError(_("No arrancó la grabación: ") + (err or _("wf-recorder terminó al instante")))

    def _pw(self, name, target, monitor):
        f = os.path.join(self.tmp, name + ".wav")
        cmd = ["pw-record", "--target", target, "--rate", "48000", "--channels", "2"] + (["-P", "{ stream.capture.sink=true }"] if monitor else []) + [f]
        return (name, f, subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True))

    def elapsed(self): return int(time.time() - self.t0) if self.running else 0

    def stop(self):
        """Termina y devuelve la ruta del MP4 (o lanza RuntimeError). Bloquea unos segundos: llamar desde un hilo."""
        if not self.running: raise RuntimeError(_("No hay una grabación en curso."))
        self.running = False
        for _n, _f, p in self.audio: self._term(p)
        self._term(self.procs[0]); video = os.path.join(self.tmp, "video.mkv")
        if not os.path.exists(video) or os.path.getsize(video) < 1000: err = open(os.path.join(self.tmp, "wf.log")).read().strip()[-200:]; self.cleanup(); raise RuntimeError(_("La grabación quedó vacía. ") + err)
        wavs = [f for _n, f, _p in self.audio if os.path.exists(f) and os.path.getsize(f) > 2000]
        if wavs and have("ffmpeg"):
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", video] + sum([["-i", w] for w in wavs], [])
            cmd += (["-filter_complex", f"{''.join(f'[{i + 1}:a]' for i in range(len(wavs)))}amix=inputs={len(wavs)}:normalize=0[a]", "-map", "0:v", "-map", "[a]"] if len(wavs) > 1 else ["-map", "0:v", "-map", "1:a"])
            cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", self.out]
        elif have("ffmpeg"): cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-c:v", "copy", self.out]
        else: shutil.copy(video, self.out.replace(".mp4", ".mkv")); self.out = self.out.replace(".mp4", ".mkv"); cmd = None
        if cmd:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode != 0 or not os.path.exists(self.out): shutil.copy(video, self.out.replace(".mp4", ".mkv")); self.out = self.out.replace(".mp4", ".mkv")   # al menos el vídeo no se pierde
        out = self.out; self.cleanup(); return out

    def _term(self, p):
        try:
            os.killpg(p.pid, signal.SIGINT); p.wait(timeout=8)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try: os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError: pass

    def cleanup(self):
        self.running = False
        for _n, _f, p in self.audio:
            if p.poll() is None: self._term(p)
        for p in self.procs:
            if p.poll() is None: self._term(p)
        if self.tmp: shutil.rmtree(self.tmp, ignore_errors=True)

def run_async(fn, done, *a):
    """Ejecuta fn(*a) en un hilo y llama a done(resultado, error) en el hilo de la interfaz (GLib.idle_add)."""
    from gi.repository import GLib
    def work():
        try: r, e = fn(*a), None
        except Exception as ex: r, e = None, str(ex)
        GLib.idle_add(lambda: (done(r, e), False)[1])
    threading.Thread(target=work, daemon=True).start()
