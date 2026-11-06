# Qué partes de la imagen no hay que tapar (para que la capa viva no ponga tarjetas ni textos encima):
#   - caras reales (OpenCV) y cabezas de personaje dibujado (círculos blancos grandes con contorno, como el del canal)
#   - globos y nubes blancas grandes (suelen llevar el texto de la imagen)
#   - texto escrito en la imagen (RapidOCR, si está instalado)
# Se mira el video ya armado (tmp/solo_video.mp4) en el inicio, la mitad y el final de cada elemento.
#   python caras.py "<video>" 12.5     -> <video>_caras_12.5.jpg con lo que encontró marcado (para revisar)
import io, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

try:
    from estudio import FFMPEG
except Exception:
    FFMPEG = "ffmpeg"

PESO_CARA, PESO_GLOBO, PESO_TEXTO = 10.0, 4.0, 3.0
ANCHO = 640


def cuadro(video, t):
    r = subprocess.run([str(FFMPEG), "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(video), "-frames:v", "1",
                        "-vf", f"scale={ANCHO}:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    if r.returncode or not r.stdout:
        return None
    return Image.open(io.BytesIO(r.stdout)).convert("RGB")


def detectar(im, con_texto=True):
    """Lista de ((x0, y0, x1, y1) en fracción del cuadro, peso, tipo)."""
    import cv2
    a = np.array(im)
    h, w = a.shape[:2]
    out = []
    # 1) caras reales
    ruta = Path(getattr(cv2, "data", None).haarcascades if hasattr(cv2, "data") else "") / "haarcascade_frontalface_default.xml"
    if ruta.exists():
        cas = cv2.CascadeClassifier(str(ruta))
        if not cas.empty():
            gris = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
            for (x, y, fw, fh) in cas.detectMultiScale(gris, 1.1, 5, minSize=(int(h * 0.06), int(h * 0.06))):
                out.append((((x - fw * 0.2) / w, (y - fh * 0.3) / h, (x + fw * 1.2) / w, (y + fh * 1.2) / h), PESO_CARA, "cara"))
    # 2) cabezas dibujadas y globos: manchas blancas grandes
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    blanco = ((hsv[:, :, 2] > 205) & (hsv[:, :, 1] < 45)).astype(np.uint8) * 255
    blanco = cv2.morphologyEx(blanco, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cont, _ = cv2.findContours(blanco, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in cont:
        area = cv2.contourArea(cnt)
        frac = area / (w * h)
        if frac < 0.004 or frac > 0.22:          # muy chico (detalle) o enorme (fondo claro)
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        per = cv2.arcLength(cnt, True) or 1
        # ojos: 1 a 4 manchas oscuras medianas dentro de la mancha blanca (un globo con texto tiene muchas y chicas)
        sub = a[y:y + bh, x:x + bw]
        dentro = np.zeros((bh, bw), np.uint8)
        cv2.drawContours(dentro, [cnt - [x, y]], -1, 255, -1)
        oscuro = ((cv2.cvtColor(sub, cv2.COLOR_RGB2GRAY) < 70) & (dentro > 0)).astype(np.uint8)
        k, _, est, _ = cv2.connectedComponentsWithStats(oscuro)
        medianas = [e for e in est[1:] if 0.002 * area < e[4] < 0.08 * area]
        chicas = [e for e in est[1:] if e[4] <= 0.002 * area]
        con_ojos = 1 <= len(medianas) <= 4 and len(chicas) < 12
        circ = 4 * math.pi * area / per ** 2
        proporcion = bw / max(bh, 1)
        lleno = area / max(bw * bh, 1)
        # cabeza redonda (los ojos y la boca bajan la redondez medida: se acepta también lo casi cuadrado y bien lleno)
        if (circ > 0.62 and 0.65 < proporcion < 1.5 and lleno > 0.65) or (0.72 < proporcion < 1.38 and lleno > 0.6 and circ > 0.35) \
                or (con_ojos and lleno > 0.45):
            m = 0.18
            out.append((((x - bw * m) / w, (y - bh * m) / h, (x + bw * (1 + m)) / w, (y + bh * (1 + m)) / h), PESO_CARA, "cabeza"))
        elif frac > 0.01:                                                   # globo, nube, cartel blanco
            out.append(((x / w, y / h, (x + bw) / w, (y + bh) / h), PESO_GLOBO, "globo"))
    # 3) texto de la imagen
    if con_texto:
        try:
            from rapidocr_onnxruntime import RapidOCR
            global _ocr
            try:
                _ocr
            except NameError:
                _ocr = RapidOCR()
            res, _ = _ocr(a)
            for caja, txt, conf in res or []:
                if float(conf) < 0.6 or len(txt.strip()) < 2:
                    continue
                xs, ys = [p[0] for p in caja], [p[1] for p in caja]
                out.append((((min(xs) - 4) / w, (min(ys) - 4) / h, (max(xs) + 4) / w, (max(ys) + 4) / h), PESO_TEXTO, "texto"))
        except ImportError:
            pass
    return out


class Mapa:
    """Regiones a no tapar a lo largo del video, en píxeles del video final (W x H)."""
    def __init__(self, video, W, H, con_texto=True):
        self.video, self.W, self.H, self.con_texto = Path(video), W, H, con_texto
        self.cache = {}

    def en(self, t):
        k = round(t, 1)
        if k not in self.cache:
            im = cuadro(self.video, k)
            self.cache[k] = [] if im is None else [((x0 * self.W, y0 * self.H, x1 * self.W, y1 * self.H), p, tipo)
                                                   for (x0, y0, x1, y1), p, tipo in detectar(im, self.con_texto)]
        return self.cache[k]

    def regiones(self, a, b):
        ts = [a + 0.25, (a + b) / 2, max(a + 0.3, b - 0.3)] if b - a > 1 else [(a + b) / 2]
        out = []
        for t in ts:
            out += self.en(t)
        return out


def cruce(c, r):
    w = min(c[2], r[2]) - max(c[0], r[0])
    h = min(c[3], r[3]) - max(c[1], r[1])
    return max(0.0, w) * max(0.0, h)


def castigo(caja, regiones):
    area = max(1.0, (caja[2] - caja[0]) * (caja[3] - caja[1]))
    return sum(p * cruce(caja, r) / area for r, p, _ in regiones)


def main():
    video, t = Path(sys.argv[1]), float(sys.argv[2])
    im = cuadro(video, t)
    if im is None:
        sys.exit("No pude sacar ese cuadro")
    d = ImageDraw.Draw(im)
    colores = {"cara": (255, 0, 80), "cabeza": (255, 0, 80), "globo": (255, 200, 0), "texto": (0, 200, 255)}
    for (x0, y0, x1, y1), p, tipo in detectar(im):
        d.rectangle([x0 * im.width, y0 * im.height, x1 * im.width, y1 * im.height], outline=colores[tipo], width=3)
        d.text((x0 * im.width + 3, y0 * im.height + 2), tipo, fill=colores[tipo])
    sal = video.with_name(f"{video.stem}_caras_{t}.jpg")
    im.save(sal, quality=88)
    print("LISTO", sal)


if __name__ == "__main__":
    main()
