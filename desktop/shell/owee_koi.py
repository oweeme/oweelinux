"""Kois nadando en círculos sobre ondas suaves, dibujados con cairo (sin imágenes). Lo usan el asistente de primer arranque (estanque pequeño) y el protector de pantalla (pantalla completa).
Se anima con el reloj de la ventana; si `fps` > 0 se limita a ese ritmo para gastar poco en equipos modestos."""
import math, time
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

class KoiPond(Gtk.DrawingArea):
    """Tres kois nadando en círculos sobre ondas suaves, dibujados con cairo (sin imágenes): se ven mientras el equipo se prepara. Se anima solo mientras la ventana está visible."""
    KOIS = [((0.99, 0.92, 0.68), (0.95, 0.34, 0.23), 0.0, 170, 62, 0.55), ((0.96, 0.95, 0.92), (0.25, 0.22, 0.20), 2.1, 150, 50, -0.45), ((0.97, 0.62, 0.30), (0.99, 0.92, 0.68), 4.2, 100, 40, 0.70)]
    def __init__(self):
        super().__init__(content_width=520, content_height=150); self.set_draw_func(self.draw); self.t0 = time.time(); self.add_tick_callback(lambda *_a: (self.queue_draw(), True)[1])

    @staticmethod
    def koi(cr, x, y, ang, wag, body, spot):
        cr.save(); cr.translate(x, y); cr.rotate(ang)
        cr.set_source_rgb(*body); cr.move_to(-24, 0); cr.curve_to(-38, -8 + wag * 5, -50, -16 + wag * 11, -60, -13 + wag * 15); cr.curve_to(-52, -2 + wag * 8, -52, 2 + wag * 8, -60, 13 + wag * 15)   # cola
        cr.curve_to(-50, 16 + wag * 11, -38, 8 + wag * 5, -24, 0); cr.fill()
        for sgn in (-1, 1):                                                                                                                              # aletas
            cr.save(); cr.translate(8, sgn * 11); cr.rotate(sgn * (0.5 + wag * 0.25)); cr.scale(1, 0.45); cr.arc(0, 0, 10, 0, 2 * math.pi); cr.restore(); cr.set_source_rgb(*body); cr.fill()
        cr.save(); cr.scale(1, 0.42); cr.arc(0, 0, 32, 0, 2 * math.pi); cr.restore(); cr.set_source_rgb(*body); cr.fill()                                  # cuerpo
        cr.set_source_rgb(*spot)
        for dx, dy, r in ((-6, -3, 6), (8, 4, 5), (-16, 3, 4)): cr.arc(dx, dy, r, 0, 2 * math.pi); cr.fill()                                           # manchas
        cr.set_source_rgb(0.12, 0.10, 0.09); cr.arc(22, -4, 1.8, 0, 2 * math.pi); cr.arc(22, 4, 1.8, 0, 2 * math.pi); cr.fill()                          # ojos
        cr.restore()

    def draw(self, area, cr, w, h):
        t = time.time() - self.t0
        for k in range(3):                                                                                                                               # ondas
            cr.set_source_rgba(0.16, 0.62, 0.56, 0.12 * (1 - ((t * 20 + k * 50) % 150) / 150)); cr.set_line_width(2); cr.arc(w / 2, h / 2, 20 + (t * 20 + k * 50) % 150, 0, 2 * math.pi); cr.stroke()
        for i, (body, spot, phase, rx, ry, speed) in enumerate(self.KOIS):
            a = t * speed + phase; x = w / 2 + rx * math.cos(a); y = h / 2 + ry * math.sin(a)
            ang = math.atan2(ry * math.cos(a) * (1 if speed > 0 else -1), -rx * math.sin(a) * (1 if speed > 0 else -1))
            self.koi(cr, x, y, ang, math.sin(t * 6 + i * 2), body, spot)


class KoiScreen(Gtk.DrawingArea):
    """Protector de pantalla: varios kois grandes recorriendo toda la pantalla sobre el verde oscuro del escritorio, con ondas que nacen y se apagan. 20 imágenes por segundo (suficiente para
    un movimiento lento y barato para la CPU)."""
    BG = (0.0627, 0.1255, 0.0980)
    # (cuerpo, manchas, fase, radio x (fracción del ancho), radio y (fracción del alto), velocidad, centro x, centro y, tamaño)
    FISH = [(KoiPond.KOIS[0][0], KoiPond.KOIS[0][1], 0.0, 0.33, 0.30, 0.13, 0.50, 0.50, 2.4), (KoiPond.KOIS[1][0], KoiPond.KOIS[1][1], 2.0, 0.26, 0.33, -0.11, 0.45, 0.55, 2.0),
            (KoiPond.KOIS[2][0], KoiPond.KOIS[2][1], 4.1, 0.30, 0.22, 0.16, 0.58, 0.42, 1.7), (KoiPond.KOIS[0][0], KoiPond.KOIS[1][1], 1.2, 0.18, 0.20, -0.18, 0.28, 0.65, 1.5),
            (KoiPond.KOIS[1][0], KoiPond.KOIS[0][1], 3.3, 0.20, 0.18, 0.15, 0.72, 0.60, 1.3), (KoiPond.KOIS[2][0], KoiPond.KOIS[0][1], 5.2, 0.22, 0.26, -0.14, 0.32, 0.33, 1.8)]
    def __init__(self, fps=20):
        super().__init__(hexpand=True, vexpand=True); self.set_draw_func(self.draw); self.t0 = time.time(); GLib.timeout_add(int(1000 / fps), lambda: (self.queue_draw(), True)[1])

    def draw(self, area, cr, w, h):
        t = time.time() - self.t0
        cr.set_source_rgb(*self.BG); cr.paint()
        for k in range(5):                                                                                                                               # ondas que se agrandan y se apagan
            ph = (t * 0.11 + k * 0.2) % 1.0; cx = w * (0.2 + 0.6 * ((k * 0.37) % 1.0)); cy = h * (0.2 + 0.6 * ((k * 0.61 + 0.3) % 1.0))
            cr.set_source_rgba(0.16, 0.62, 0.56, 0.16 * (1 - ph)); cr.set_line_width(2); cr.arc(cx, cy, 10 + ph * min(w, h) * 0.22, 0, 2 * math.pi); cr.stroke()
        for i, (body, spot, phase, rx, ry, speed, cx, cy, size) in enumerate(self.FISH):
            a = t * speed + phase; x = w * cx + w * rx * math.cos(a); y = h * cy + h * ry * math.sin(a)
            sgn = 1 if speed > 0 else -1; ang = math.atan2(h * ry * math.cos(a) * sgn, -w * rx * math.sin(a) * sgn)
            cr.save(); cr.translate(x, y); cr.scale(size, size); KoiPond.koi(cr, 0, 0, ang, math.sin(t * 5 + i * 2), body, spot); cr.restore()
