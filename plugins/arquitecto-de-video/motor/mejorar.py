# Mejorar resolución (como "Mejorar calidad / Upscale" de CapCut y Canva).
#   python mejorar.py imagen "<imagen o carpeta>" [--escala 2|4] [--metodo ia|clasico] [--salida carpeta]
#   python mejorar.py video "<video.mp4>" [--escala 2] [--alto 2160]      (clásico: escalado fino + limpieza + nitidez)
#   python mejorar.py instalar-modelo      baja Real-ESRGAN x2 y x4 en ONNX (licencia BSD-3, uso comercial permitido;
#                                          pesos oficiales de xinntao exportados por SceneWorks en Hugging Face, ~65 MB c/u)
# IA: inventa detalle fino de forma creíble (bordes, texturas); en caras o letras chicas revisar que no deforme nada.
# Clásico: no inventa nada, solo agranda bien; es instantáneo. Sin el modelo instalado, se usa el clásico.
# En el PC sin tarjeta gráfica una imagen 1280x720 -> x2 tarda del orden de un minuto con IA.
# Nunca reemplaza el original: <nombre>_x2.png al lado (o en --salida).
import subprocess, sys, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

try:
    from estudio import FFMPEG
except Exception:
    FFMPEG = "ffmpeg"

MODELOS = Path.home() / "EstudioPaltostaila" / "modelos"
URL = "https://huggingface.co/SceneWorks/real-esrgan-onnx/resolve/main/real_esrgan_x{}.onnx"
EXT = {".png", ".jpg", ".jpeg", ".webp"}
_ses = {}


def sesion(escala):
    p = MODELOS / f"real_esrgan_x{escala}.onnx"
    if not p.exists():
        return None
    if escala not in _ses:
        import onnxruntime as ort
        _ses[escala] = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
    return _ses[escala]


def ia(im, escala, tile=256, pad=16):
    s = sesion(escala)
    a = np.array(im.convert("RGB")).astype(np.float32) / 255
    H, W, _ = a.shape
    out = np.zeros((H * escala, W * escala, 3), np.float32)
    nombre = s.get_inputs()[0].name
    for y in range(0, H, tile):
        for x in range(0, W, tile):
            y0, x0 = max(0, y - pad), max(0, x - pad)
            y1, x1 = min(H, y + tile + pad), min(W, x + tile + pad)
            r = s.run(None, {nombre: a[y0:y1, x0:x1].transpose(2, 0, 1)[None]})[0][0].transpose(1, 2, 0)
            oy, ox = (y - y0) * escala, (x - x0) * escala
            h, w = min(tile, H - y) * escala, min(tile, W - x) * escala
            out[y * escala:y * escala + h, x * escala:x * escala + w] = r[oy:oy + h, ox:ox + w]
    return Image.fromarray((np.clip(out, 0, 1) * 255).round().astype(np.uint8))


def clasico(im, escala):
    g = im.convert("RGB").resize((im.width * escala, im.height * escala), Image.LANCZOS)
    return g.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))


def imagen(ruta, escala=2, metodo="ia", salida=None):
    rutas = sorted(q for q in Path(ruta).iterdir() if q.suffix.lower() in EXT) if Path(ruta).is_dir() else [Path(ruta)]
    usar_ia = metodo == "ia" and sesion(escala) is not None
    if metodo == "ia" and not usar_ia:
        print("AVISO no está el modelo de IA (python mejorar.py instalar-modelo); uso el método clásico", flush=True)
    for r in rutas:
        im = Image.open(r)
        alfa = im.split()[3] if im.mode == "RGBA" else None
        g = ia(im, escala) if usar_ia else clasico(im, escala)
        if alfa is not None:
            g.putalpha(alfa.resize(g.size, Image.LANCZOS))
        carpeta = Path(salida) if salida else r.parent
        carpeta.mkdir(parents=True, exist_ok=True)
        sal = carpeta / f"{r.stem}_x{escala}.png"
        n = 2
        while sal.exists():
            sal = carpeta / f"{r.stem}_x{escala}_{n}.png"
            n += 1
        g.save(sal)
        print(f"{r.name} {im.width}x{im.height} -> {sal.name} {g.width}x{g.height} ({'IA' if usar_ia else 'clásico'})", flush=True)


def video(ruta, escala=2, alto=None):
    ruta = Path(ruta)
    esc = f"scale=-2:{alto}:flags=lanczos" if alto else f"scale=iw*{escala}:ih*{escala}:flags=lanczos"
    from estudio import destino
    sal = destino(ruta.with_name(f"{ruta.stem}_{'%dp' % alto if alto else 'x%d' % escala}.mp4"), ruta)
    r = subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", str(ruta), "-vf", f"hqdn3d=1.5:1.5:4:4,{esc},unsharp=5:5:0.8:3:3:0.3",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy",
                        "-movflags", "+faststart", str(sal)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-1000:])
    print("listo:", sal)


def instalar():
    MODELOS.mkdir(parents=True, exist_ok=True)
    for e in (2, 4):
        p = MODELOS / f"real_esrgan_x{e}.onnx"
        if p.exists():
            print("ya está:", p)
            continue
        print("bajando", URL.format(e), flush=True)
        tmp = p.with_suffix(".parcial")
        urllib.request.urlretrieve(URL.format(e), tmp)
        tmp.rename(p)
        print("listo:", p, f"{p.stat().st_size / 1e6:.0f} MB", flush=True)


def main():
    a = sys.argv[1:]
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a:
        sys.exit("Uso: ver el encabezado de mejorar.py")
    if a[0] == "instalar-modelo":
        instalar()
    elif a[0] == "imagen":
        imagen(a[1], int(op("--escala", 2)), op("--metodo", "ia"), op("--salida"))
    elif a[0] == "video":
        video(a[1], int(op("--escala", 2)), int(op("--alto")) if op("--alto") else None)
    print("LISTO", flush=True)


if __name__ == "__main__":
    main()
