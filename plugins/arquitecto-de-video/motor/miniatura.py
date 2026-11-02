# Miniaturas 1280x720: texto corto (maximo 3 palabras) sobre una imagen del video.
# En proyecto.json: "miniaturas": [{"imagen": "Imagen_010.jpeg", "lineas": ["¿SOLO PARA", "RICOS?"], "lado": "derecha"}]
#   python miniatura.py "C:\ruta\video"
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from estudio import Proyecto

pr = Proyecto()
CANDIDATAS = [r"C:\Windows\Fonts\ariblk.ttf", r"C:\Windows\Fonts\arialbd.ttf",
              "/System/Library/Fonts/Supplemental/Arial Black.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
FUENTE = next((f for f in CANDIDATAS if os.path.exists(f)), None)
VERDE, BLANCO, OSCURO = (106, 209, 91), (255, 255, 255), (10, 22, 45)


def hacer(m, n):
    im = Image.open(pr.imagenes / m["imagen"]).convert("RGB")
    im = im.resize((1280, round(1280 * im.height / im.width)))
    if im.height < 720:
        im = im.resize((round(720 * im.width / im.height), 720))
    x0, y0 = (im.width - 1280) // 2, (im.height - 720) // 2
    im = ImageEnhance.Contrast(im.crop((x0, y0, x0 + 1280, y0 + 720))).enhance(1.12)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FUENTE, 104) if FUENTE else ImageFont.load_default()
    y = 70
    for i, t in enumerate(m["lineas"]):
        w = d.textlength(t, font=f)
        x = 1280 - w - 50 if m.get("lado", "derecha") == "derecha" else 50
        d.text((x, y), t, font=f, fill=VERDE if i == len(m["lineas"]) - 1 else BLANCO, stroke_width=12, stroke_fill=OSCURO)
        y += 122
    pr.publicar.mkdir(parents=True, exist_ok=True)
    ruta = pr.publicar / f"Miniatura_{pr.base_nombre}_{n}.jpg"
    im.save(ruta, quality=92)
    print(ruta)


for n, m in enumerate(pr["miniaturas"], 1):
    hacer(m, n)
if not pr["miniaturas"]:
    print("no hay miniaturas definidas en proyecto.json")
