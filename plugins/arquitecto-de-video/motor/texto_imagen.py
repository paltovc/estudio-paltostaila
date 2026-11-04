# Traducir (o borrar) el texto que viene escrito dentro de una imagen, con herramientas propias y gratuitas:
#   1) leer el texto (OCR, RapidOCR, Apache-2.0)   2) borrarlo rellenando el fondo (LaMa, Apache-2.0; o el
#   relleno simple de OpenCV si el modelo no está)   3) escribir el texto nuevo con la letra del canal.
# Nunca toca la imagen original: escribe <nombre>_es.png (o el sufijo que se pida) al lado o en --salida.
#
#   python texto_imagen.py detectar "<imagen o carpeta>"
#        -> _textos\<nombre>.json (cada línea con su texto, caja y "nuevo": "") y _textos\<nombre>_cajas.jpg
#   (Claude o la persona llena "nuevo" con la traducción; "" = dejar igual, "-" = solo borrar)
#   python texto_imagen.py reemplazar "<imagen o carpeta>" [--sufijo _es] [--salida carpeta] [--metodo lama|simple]
#        [--canal finanzas] [--fuente titulo]
#   python texto_imagen.py instalar-modelo     baja LaMa (lama_fp32.onnx, ~200 MB, Apache-2.0) desde Hugging Face
#
# Uso responsable: solo en imágenes propias o con derechos. No sirve para quitar marcas de agua ni firmas de otros.
import json, sys, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ESTUDIO = Path.home() / "EstudioPaltostaila"
MODELO = ESTUDIO / "modelos" / "lama_fp32.onnx"
URL_MODELO = "https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx"
EXT = {".png", ".jpg", ".jpeg", ".webp"}
_ocr = _lama = None


def imagenes(ruta):
    p = Path(ruta)
    if p.is_dir():
        return sorted(q for q in p.iterdir() if q.suffix.lower() in EXT and not q.stem.endswith(("_es", "_cajas")))
    return [p]


def ocr():
    global _ocr
    if _ocr is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            sys.exit("Falta el lector de texto: python -m pip install rapidocr_onnxruntime")
        _ocr = RapidOCR()
    return _ocr


def detectar(img_path):
    im = Image.open(img_path).convert("RGB")
    res, _ = ocr()(np.array(im))
    trozos = []
    for caja, texto, conf in res or []:
        xs, ys = [p[0] for p in caja], [p[1] for p in caja]
        trozos.append([int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)), texto, float(conf)])
    trozos.sort(key=lambda t: (t[1], t[0]))
    unidos = []                     # el lector a veces parte una línea en palabras: se juntan las de la misma altura
    for t in trozos:
        for u in unidos:
            h = min(t[3] - t[1], u[3] - u[1])
            cruce = min(t[3], u[3]) - max(t[1], u[1])
            if h > 0 and cruce > 0.6 * h and 0 <= t[0] - u[2] < 1.2 * h:
                u[2], u[1], u[3] = t[2], min(u[1], t[1]), max(u[3], t[3])
                u[4], u[5] = u[4] + " " + t[4], min(u[5], t[5])
                break
        else:
            unidos.append(list(t))
    lineas = [{"id": i, "texto": u[4], "nuevo": "", "confianza": round(u[5], 2), "caja": u[:4]}
              for i, u in enumerate(unidos, 1)]
    d = img_path.parent / "_textos"
    d.mkdir(exist_ok=True)
    (d / f"{img_path.stem}.json").write_text(json.dumps({"imagen": img_path.name, "lineas": lineas}, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
    vista = im.copy()
    dr = ImageDraw.Draw(vista)
    for l in lineas:
        dr.rectangle(l["caja"], outline=(255, 0, 80), width=3)
        dr.text((l["caja"][0] + 2, max(0, l["caja"][1] - 14)), str(l["id"]), fill=(255, 0, 80))
    vista.thumbnail((1600, 1600))
    vista.save(d / f"{img_path.stem}_cajas.jpg", quality=85)
    return lineas


def lama():
    global _lama
    if _lama is None and MODELO.exists():
        import onnxruntime as ort
        _lama = ort.InferenceSession(str(MODELO), providers=["CPUExecutionProvider"])
    return _lama


def borrar(im, mascara, metodo="lama"):
    """im RGB PIL, mascara L (255 = borrar). Rellena por trozos alrededor de cada mancha."""
    a = np.array(im)
    m = np.array(mascara) > 127
    if not m.any():
        return im
    import cv2
    sesion = lama() if metodo == "lama" else None
    if sesion is None:
        out = cv2.inpaint(a[:, :, ::-1].copy(), m.astype(np.uint8) * 255, 7, cv2.INPAINT_TELEA)[:, :, ::-1]
        return Image.fromarray(out)
    n, etiquetas, stats, _ = cv2.connectedComponentsWithStats(cv2.dilate(m.astype(np.uint8), np.ones((25, 25), np.uint8)))
    H, W = m.shape
    for k in range(1, n):
        x, y, w, h = stats[k][:4]
        lado = int(max(w, h) * 1.6) + 32
        cx, cy = x + w // 2, y + h // 2
        x0, y0 = max(0, cx - lado // 2), max(0, cy - lado // 2)
        x1, y1 = min(W, x0 + lado), min(H, y0 + lado)
        trozo, tm = a[y0:y1, x0:x1], m[y0:y1, x0:x1] & (etiquetas[y0:y1, x0:x1] == k)
        ti = np.array(Image.fromarray(trozo).resize((512, 512), Image.LANCZOS)).astype(np.float32) / 255
        mm = (np.array(Image.fromarray(tm.astype(np.uint8) * 255).resize((512, 512), Image.NEAREST)) > 127).astype(np.float32)
        entradas = sesion.get_inputs()
        res = sesion.run(None, {entradas[0].name: ti.transpose(2, 0, 1)[None], entradas[1].name: mm[None, None]})[0][0]
        res = res.transpose(1, 2, 0)
        if res.max() <= 1.5:
            res = res * 255
        res = np.array(Image.fromarray(np.clip(res, 0, 255).astype(np.uint8)).resize((x1 - x0, y1 - y0), Image.LANCZOS))
        a[y0:y1, x0:x1][tm] = res[tm]
    return Image.fromarray(a)


def colores_texto(im, caja):
    """(color de las letras, color del contorno o None) dentro de la caja.
    Fondo = mediana del borde de la caja; letras = lo que se aleja del fondo; el contorno es el anillo exterior de las
    letras (se separa con una erosión) cuando su color es claramente otro."""
    import cv2
    x0, y0, x1, y1 = caja
    p = max(3, (y1 - y0) // 4)                 # el lector suele cortar el contorno: se mira un poco más grande
    x0, y0, x1, y1 = max(0, x0 - p), max(0, y0 - p), min(im.width, x1 + p), min(im.height, y1 + p)
    a = np.array(im.crop((x0, y0, x1, y1)).convert("RGB")).astype(np.int32)
    if a.shape[0] < 6 or a.shape[1] < 6:
        return (255, 255, 255), None
    borde = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    fondo = np.median(borde, axis=0)
    dist = np.sqrt(((a - fondo) ** 2).sum(axis=2))
    letras = (dist > 60).astype(np.uint8)
    if letras.sum() < 20:
        return tuple(int(v) for v in a.reshape(-1, 3).mean(0)), None
    r = max(1, (caja[3] - caja[1]) // 22)
    interior = cv2.erode(letras, np.ones((2 * r + 1, 2 * r + 1), np.uint8)).astype(bool)
    anillo = letras.astype(bool) & ~interior
    if interior.sum() < 10:
        return tuple(int(v) for v in np.median(a[letras.astype(bool)], axis=0)), None
    letra = np.median(a[interior], axis=0)
    aro = np.median(a[anillo], axis=0) if anillo.sum() > 10 else letra
    d = lambda p, q: float(np.sqrt(((p - q) ** 2).sum()))
    contorno = tuple(int(v) for v in aro) if d(aro, letra) > 90 and d(aro, fondo) > 60 else None
    return tuple(int(v) for v in letra), contorno


def fuente_para(texto, ancho, alto, nombre_fuente, mk):
    from diseno import fuente
    tam = max(8, int(alto * 1.05))
    while tam > 8:
        f = fuente(nombre_fuente, tam, mk)
        b = f.getbbox(texto)
        if b[2] - b[0] <= ancho * 1.04 and b[3] - b[1] <= alto * 1.15:
            return f
        tam -= 1
    return fuente(nombre_fuente, 8, mk)


def reemplazar(img_path, sufijo="_es", salida=None, metodo="lama", canal=None, nombre_fuente="titulo"):
    from diseno import marca
    js = img_path.parent / "_textos" / f"{img_path.stem}.json"
    if not js.exists():
        detectar(img_path)
        print(f"  {img_path.name}: no había textos detectados; los detecté en {js}. Llena \"nuevo\" y vuelve a correr.")
        return None
    datos = json.loads(js.read_text(encoding="utf-8"))
    im = Image.open(img_path).convert("RGB")
    cambiar = [l for l in datos["lineas"] if l.get("nuevo")]
    if not cambiar:
        print(f"  {img_path.name}: ninguna línea con \"nuevo\"; no se hizo nada")
        return None
    colores = {l["id"]: colores_texto(im, l["caja"]) for l in cambiar}
    mascara = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(mascara)
    for l in cambiar:
        x0, y0, x1, y1 = l["caja"]
        pad = max(3, (y1 - y0) // 6)
        d.rectangle([x0 - pad, y0 - pad, x1 + pad, y1 + pad], fill=255)
    limpia = borrar(im, mascara, metodo)
    mk = marca(canal)
    dr = ImageDraw.Draw(limpia)
    for l in cambiar:
        if l["nuevo"].strip() == "-":
            continue
        x0, y0, x1, y1 = l["caja"]
        letra, fondo = colores[l["id"]]
        f = fuente_para(l["nuevo"], x1 - x0, y1 - y0, l.get("fuente", nombre_fuente), mk)
        b = f.getbbox(l["nuevo"])
        tx = x0 + ((x1 - x0) - (b[2] - b[0])) // 2 - b[0]
        ty = y0 + ((y1 - y0) - (b[3] - b[1])) // 2 - b[1]
        if fondo is None and l.get("borde") is True:       # se pidió contorno aunque el original no tenía
            lum = 0.299 * letra[0] + 0.587 * letra[1] + 0.114 * letra[2]
            fondo = (0, 0, 0) if lum > 128 else (255, 255, 255)
        borde = max(1, (y1 - y0) // 14) if fondo is not None and l.get("borde", True) else 0
        dr.text((tx, ty), l["nuevo"], font=f, fill=tuple(l.get("color", letra)), stroke_width=borde, stroke_fill=fondo)
    carpeta = Path(salida) if salida else img_path.parent
    carpeta.mkdir(parents=True, exist_ok=True)
    sal = carpeta / f"{img_path.stem}{sufijo}.png"
    n = 2
    while sal.exists():                                       # nunca se sobrescribe una versión
        sal = carpeta / f"{img_path.stem}{sufijo}_{n}.png"
        n += 1
    limpia.save(sal)
    return sal


def instalar_modelo():
    if MODELO.exists():
        print("Ya está:", MODELO)
        return
    MODELO.parent.mkdir(parents=True, exist_ok=True)
    print("Bajando LaMa (Apache-2.0) desde", URL_MODELO, "(~200 MB)...", flush=True)
    tmp = MODELO.with_suffix(".parcial")
    urllib.request.urlretrieve(URL_MODELO, tmp)
    tmp.rename(MODELO)
    print("Listo:", MODELO, f"{MODELO.stat().st_size / 1e6:.0f} MB")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__ or "ver encabezado del archivo")
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a[0] == "instalar-modelo":
        return instalar_modelo()
    for img in imagenes(a[1]):
        if a[0] == "detectar":
            ls = detectar(img)
            print(f"{img.name}: {len(ls)} líneas de texto")
            for l in ls:
                print(f"   {l['id']:>2}. {l['texto']}  ({l['confianza']})")
        elif a[0] == "reemplazar":
            s = reemplazar(img, op("--sufijo", "_es"), op("--salida"), op("--metodo", "lama"), op("--canal"), op("--fuente", "titulo"))
            if s:
                print(f"{img.name} -> {s}  (borrado con {'LaMa' if lama() and op('--metodo', 'lama') == 'lama' else 'relleno simple'})")
    print("LISTO", flush=True)


if __name__ == "__main__":
    main()
