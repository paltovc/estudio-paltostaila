# Receta de miniatura: mide una o varias miniaturas que funcionan (paleta, brillo, contraste, saturación,
# dónde está el peso visual y cuánto ocupa el texto grande) y arma una hoja para comparar. Con esa hoja,
# el director de arte escribe la receta (references/receta-miniatura.md): reglas + prompt adaptado al personaje
# y al canal propios. Nunca se copia la miniatura ni sus personajes o logos.
#   python receta_miniatura.py "mini1.jpg" "mini2.jpg" ... [--salida "C:\carpeta"] [--nuestra "mia.png"]
import colorsys, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat


def fuente(t):
    for n in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(n, t)
        except OSError:
            continue
    return ImageFont.load_default()


def medir(ruta):
    im = Image.open(ruta).convert("RGB")
    chica = im.resize((320, 180))
    pal = chica.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
    cuentas = sorted(pal.getcolors(), reverse=True)
    rgb = pal.getpalette()[:18]
    paleta = []
    for n, k in cuentas:
        r, g, b = rgb[k * 3:k * 3 + 3]
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        paleta.append({"hex": f"#{r:02X}{g:02X}{b:02X}", "parte": round(n / (320 * 180), 2), "saturacion": round(s, 2), "luz": round(l, 2)})
    gris = chica.convert("L")
    st = ImageStat.Stat(gris)
    hsv = chica.convert("HSV")
    sat = ImageStat.Stat(hsv.split()[1]).mean[0] / 255
    bordes = gris.filter(ImageFilter.FIND_EDGES)
    px = bordes.load()
    tot = sx = sy = 0
    celdas = [[0] * 3 for _ in range(3)]
    for y in range(180):
        for x in range(320):
            v = px[x, y]
            tot += v; sx += v * x; sy += v * y
            celdas[min(2, y // 60)][min(2, x * 3 // 320)] += v
    cx, cy = (sx / tot / 320, sy / tot / 180) if tot else (0.5, 0.5)
    # texto grande: zonas muy contrastadas de tamaño medio (aproximado; confirmar mirando)
    alto_c = gris.point(lambda v: 255 if v > 225 or v < 30 else 0).filter(ImageFilter.MaxFilter(5))
    texto = ImageStat.Stat(alto_c).mean[0] / 255
    return {"archivo": str(ruta), "ancho": im.width, "alto": im.height, "paleta": paleta,
            "brillo": round(st.mean[0] / 255, 2), "contraste": round(st.stddev[0] / 128, 2), "saturacion": round(sat, 2),
            "peso_visual": {"x": round(cx, 2), "y": round(cy, 2)},
            "tercio_con_mas_detalle": ["arriba", "medio", "abajo"][max(range(3), key=lambda r: sum(celdas[r]))] + "-" +
                                      ["izquierda", "centro", "derecha"][max(range(3), key=lambda c: sum(celdas[r][c] for r in range(3)))],
            "zona_muy_contrastada": round(texto, 2)}


def hoja(medidas, destino):
    W, fila = 1600, 300
    img = Image.new("RGB", (W, fila * len(medidas) + 10), (24, 24, 24))
    d = ImageDraw.Draw(img)
    f, fc = fuente(22), fuente(17)
    for i, m in enumerate(medidas):
        y = i * fila + 10
        mini = Image.open(m["archivo"]).convert("RGB").resize((480, 270))
        dm = ImageDraw.Draw(mini)
        for k in (1, 2):          # tercios
            dm.line([(160 * k, 0), (160 * k, 270)], fill=(255, 255, 255), width=1)
            dm.line([(0, 90 * k), (480, 90 * k)], fill=(255, 255, 255), width=1)
        px_, py_ = m["peso_visual"]["x"] * 480, m["peso_visual"]["y"] * 270
        dm.ellipse([px_ - 10, py_ - 10, px_ + 10, py_ + 10], outline=(255, 210, 63), width=3)
        img.paste(mini, (10, y))
        d.text((510, y), Path(m["archivo"]).name[:60], fill=(255, 255, 255), font=f)
        d.text((510, y + 36), f"brillo {m['brillo']}   contraste {m['contraste']}   saturación {m['saturacion']}   "
                              f"detalle: {m['tercio_con_mas_detalle']}   zona muy contrastada {int(m['zona_muy_contrastada'] * 100)} %",
               fill=(200, 200, 200), font=fc)
        x = 510
        for c in m["paleta"]:
            ancho = max(40, int(c["parte"] * 1000))
            d.rectangle([x, y + 80, x + ancho, y + 200], fill=c["hex"])
            d.text((x + 4, y + 206), c["hex"], fill=(220, 220, 220), font=fc)
            d.text((x + 4, y + 228), f"{int(c['parte'] * 100)} %", fill=(150, 150, 150), font=fc)
            x += ancho + 8
    img.save(destino, quality=90)


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit("uso: python receta_miniatura.py mini1.jpg [mini2.jpg ...] [--nuestra mia.png] [--salida carpeta]")
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    rutas = [x for x in a if not x.startswith("--") and x not in (opt("--salida"), opt("--nuestra"))]
    if opt("--nuestra"):
        rutas.append(opt("--nuestra"))
    salida = Path(opt("--salida") or Path(rutas[0]).parent / "receta_miniatura")
    salida.mkdir(parents=True, exist_ok=True)
    medidas = [medir(r) for r in rutas]
    (salida / "medidas.json").write_text(json.dumps(medidas, ensure_ascii=False, indent=1), encoding="utf-8")
    hoja(medidas, salida / "hoja_miniaturas.jpg")
    for m in medidas:
        print(f"{Path(m['archivo']).name}: brillo {m['brillo']}, contraste {m['contraste']}, saturación {m['saturacion']}, "
              f"colores {' '.join(c['hex'] for c in m['paleta'][:4])}, detalle {m['tercio_con_mas_detalle']}")
    print("LISTO", salida, "(hoja_miniaturas.jpg + medidas.json). Siguiente: escribir la receta con references/receta-miniatura.md")


if __name__ == "__main__":
    main()
