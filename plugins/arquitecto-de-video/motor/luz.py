# Iluminación automática para una persona hablando a cámara (0.15). Mide cada toma en varios cuadros (exposición general
# y por zonas, la cara si se ve, y el balance de blancos en lo que debería ser gris) y propone una corrección suave:
# exposición (gamma), balance de blancos neutro, un poco de contraste si la toma está plana y un "realce de cara"
# (la zona de la cara queda con algo más de luz que el resto, con borde difuso). No inventa luz: corrige con medida.
# Orden dentro del color del estudio:  HDR->SDR (color.py)  ->  luz (este archivo)  ->  LUT / look (color.py).
# Nunca toca los originales: solo devuelve un filtro de ffmpeg y hojas de muestra con nombre nuevo.
#
#   python luz.py muestras "<salida>" "toma.mp4@12.5" "foto.jpg" ... [--look natural] [--realce 0.15] [--balance auto|no]
#                                      [--alto 720]      hoja ORIGINAL | SOLO LOOK | LUZ + LOOK, con lo medido
#   python luz.py medir "<toma.mp4>"                     imprime lo medido y la corrección propuesta (no escribe nada)
#   (desde otro script)  import luz; filtro, informe = luz.para_toma(ruta, {"auto": True, "realce_cara": 0.15})
#
# En proyecto.json (lo aplica grabado.py armar, toma por toma):
#   "grabado": {"luz": {"auto": true, "realce_cara": 0.15, "balance": "auto"}}
#   balance: "auto" (neutro, medido), false o "no" (no se toca) o [r, g, b] (ganancias a mano, 1.0 = igual).
#   Opcionales: "fuerza" (1.0; 0.5 = la mitad de la corrección), "cuadros" (5 cuadros medidos por toma),
#               "exposicion": false (no tocar la exposición), "contraste": false.
import io, json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    from estudio import FFMPEG, FFPROBE
except Exception:
    FFMPEG, FFPROBE = "ffmpeg", "ffprobe"
from color import cadena, hdr_sdr, fotograma

DEF = {"auto": True, "realce_cara": 0.15, "balance": "auto", "fuerza": 1.0, "cuadros": 5, "exposicion": True, "contraste": True}
FOTO = (".jpg", ".jpeg", ".png", ".webp")
BANDA = (0.38, 0.55)        # luminancia (0 a 1) que se considera bien expuesta: dentro de la banda no se toca
ANCHO = 384                 # las medidas se hacen sobre cuadros chicos


def _dur(ruta):
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _cuadro(ruta, t, sdr):
    """Un cuadro chico ya pasado a SDR (lo que de verdad va a recibir la corrección), como imagen RGB; None si falla."""
    desde = ["-ss", f"{max(0.0, t):.3f}"] if t is not None else []
    cmd = [str(FFMPEG), "-v", "error", *desde, "-i", str(ruta), "-frames:v", "1",
           "-vf", (sdr + "," if sdr else "") + f"scale={ANCHO}:-2", "-f", "image2pipe", "-vcodec", "png", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode or not r.stdout:
        return None
    return Image.open(io.BytesIO(r.stdout)).convert("RGB")


def medir(ruta, n=5, desde=None, hasta=None):
    """Mide una toma (o una foto) en n cuadros repartidos entre `desde` y `hasta` (segundos; por defecto toda la toma).
    Devuelve un diccionario con medianas entre cuadros:
      y_med, y_p05, y_p95   luminancia general (0 a 1): mediana y extremos
      zonas                 luminancia media en una grilla de 3x3 (fila por fila)
      cara                  {"cx", "cy", "ancho", "alto", "y"} en fracción del cuadro y su luminancia, o None
      cara_vista            en qué parte de los cuadros se encontró una cara (0 a 1)
      neutro                (r, g, b) medio de lo casi gris fuera de la cara, o None si casi no hay gris en la toma
      cuadros, hdr          cuántos cuadros se midieron y si la toma venía en HDR"""
    ruta = Path(ruta)
    sdr = hdr_sdr(ruta)
    if ruta.suffix.lower() in FOTO:
        tiempos = [None]
    else:
        d = _dur(ruta)
        a = 0.0 if desde is None else max(0.0, float(desde))
        b = d if hasta is None else min(d or float(hasta), float(hasta))
        if b <= a:
            a, b = 0.0, d
        n = max(1, int(n))
        tiempos = [a + (b - a) * (k + 0.5) / n for k in range(n)]
    try:
        import caras as _caras
    except Exception:
        _caras = None                      # sin OpenCV o numpy: se mide igual, sin ponderar por la cara
    ys, p05, p95, zonas, caras_, neutros = [], [], [], [], [], []
    for t in tiempos:
        im = _cuadro(ruta, t, sdr)
        if im is None:
            continue
        a_ = np.asarray(im, dtype=np.float32) / 255.0
        Y = 0.2126 * a_[:, :, 0] + 0.7152 * a_[:, :, 1] + 0.0722 * a_[:, :, 2]
        h, w = Y.shape
        ys.append(float(np.median(Y))); p05.append(float(np.percentile(Y, 5))); p95.append(float(np.percentile(Y, 95)))
        zonas.append([float(Y[i * h // 3:(i + 1) * h // 3, j * w // 3:(j + 1) * w // 3].mean()) for i in range(3) for j in range(3)])
        fuera = np.ones((h, w), bool)
        c = _caras.cara_principal(im) if _caras else None
        if c:
            cx, cy, fw, fh = c
            x0, x1 = int((cx - fw * 0.35) * w), int((cx + fw * 0.35) * w)      # el centro de la cara: sin pelo ni fondo
            y0, y1 = int((cy - fh * 0.35) * h), int((cy + fh * 0.35) * h)
            zona = Y[max(0, y0):max(1, y1), max(0, x0):max(1, x1)]
            if zona.size:
                caras_.append((cx, cy, fw, fh, float(zona.mean())))
            fuera[max(0, int((cy - fh * 0.9) * h)):int((cy + fh * 0.9) * h), max(0, int((cx - fw * 0.8) * w)):int((cx + fw * 0.8) * w)] = False
        mx, mn = a_.max(axis=2), a_.min(axis=2)
        sat = (mx - mn) / np.maximum(mx, 1e-3)
        gris = (sat < 0.18) & (Y > 0.25) & (Y < 0.92) & fuera                # casi gris, ni sombra ni quemado, fuera de la piel
        if gris.mean() >= 0.03:
            neutros.append([float(a_[:, :, k][gris].mean()) for k in range(3)])
    if not ys:
        return None
    med = lambda v: float(np.median(np.asarray(v), axis=0)) if np.ndim(v) == 1 else [float(x) for x in np.median(np.asarray(v), axis=0)]
    cara = None
    if caras_ and len(caras_) * 2 >= len(ys):          # la cara tiene que verse al menos en la mitad de los cuadros
        m = med(caras_)
        cara = {"cx": round(m[0], 4), "cy": round(m[1], 4), "ancho": round(m[2], 4), "alto": round(m[3], 4), "y": round(m[4], 4)}
    return {"y_med": round(med(ys), 4), "y_p05": round(med(p05), 4), "y_p95": round(med(p95), 4),
            "zonas": [round(x, 3) for x in med(zonas)], "cara": cara, "cara_vista": round(len(caras_) / len(ys), 2),
            "neutro": [round(x, 4) for x in med(neutros)] if len(neutros) * 2 >= len(ys) else None,
            "cuadros": len(ys), "hdr": bool(sdr)}


def proponer(m, cfg=None):
    """De lo medido a una corrección: {"gamma", "contraste", "balance": (r, g, b) o None, "realce": {...} o None, "avisos"}.
    Todo con tope: es una corrección suave, no un cambio de estilo (el estilo lo pone el look de color.py)."""
    cfg = {**DEF, **(cfg or {})}
    fuerza = max(0.0, min(1.5, float(cfg.get("fuerza", 1.0))))
    avisos, gamma, contraste, balance, realce = [], 1.0, 1.0, None, None
    cara = m.get("cara")
    # 1) exposición: mitad lo general y mitad la cara (si se ve). Solo se corrige si queda fuera de la banda, y hasta
    #    el borde de la banda: no se lleva todas las caras al mismo valor (cada tono de piel se respeta).
    if cfg.get("exposicion", True):
        ref = m["y_med"] if not cara else 0.5 * m["y_med"] + 0.5 * cara["y"]
        ref = min(max(ref, 0.02), 0.98)
        objetivo = min(max(ref, BANDA[0]), BANDA[1])
        if abs(objetivo - ref) > 0.015:
            g = math.log(ref) / math.log(objetivo)          # eq de ffmpeg: salida = entrada ^ (1 / gamma)
            g = min(max(g, 0.80), 1.40)
            gamma = 1 + (g - 1) * fuerza
            if g in (0.80, 1.40):
                avisos.append("la toma está muy " + ("oscura" if g > 1 else "clara") + ": se corrige hasta el tope; conviene mejorar la luz al grabar")
    # 2) contraste suave si la toma está plana (poca distancia entre lo oscuro y lo claro)
    if cfg.get("contraste", True):
        rango = m["y_p95"] - m["y_p05"]
        if rango < 0.50:
            contraste = 1 + min(0.12, (0.50 - rango) * 0.4) * fuerza
    # 3) balance de blancos: lo casi gris de la toma debería ser gris
    b = cfg.get("balance", "auto")
    if isinstance(b, (list, tuple)) and len(b) == 3:
        balance = tuple(float(x) for x in b)
    elif b in ("auto", True):
        if m.get("neutro"):
            r, g_, bl = (max(x, 0.02) for x in m["neutro"])
            gr = min(max(1 + (g_ / r - 1) * 0.7 * fuerza, 0.88), 1.12)       # al 70 %: neutro sin enfriar la piel
            gb = min(max(1 + (g_ / bl - 1) * 0.7 * fuerza, 0.88), 1.12)
            k = 0.2126 * gr + 0.7152 + 0.0722 * gb                           # sin cambiar el brillo general
            gr, gg, gb = gr / k, 1 / k, gb / k
            if max(abs(gr - 1), abs(gg - 1), abs(gb - 1)) >= 0.01:
                balance = (gr, gg, gb)
        else:
            avisos.append("casi no hay zonas grises en la toma: el balance de blancos no se toca")
    # 4) realce de cara: el resto de la imagen baja un poco hacia los bordes (centro en la cara, borde difuso) y todo
    #    sube lo justo para que la cara gane luz y el promedio no cambie
    r_c = max(0.0, min(0.35, float(cfg.get("realce_cara") or 0)))
    if r_c > 0:
        if cara:
            realce = {"x": cara["cx"], "y": cara["cy"], "fuerza": round(r_c, 3), "angulo": round(math.acos((1 - r_c) ** 0.25), 4)}
            gamma *= 1 + 0.5 * r_c
        else:
            avisos.append("no se encontró una cara estable: sin realce de cara")
    return {"gamma": round(gamma, 3), "contraste": round(contraste, 3),
            "balance": tuple(round(x, 3) for x in balance) if balance else None, "realce": realce, "avisos": avisos}


def filtro(c):
    """La corrección como filtro de ffmpeg ("" si no hay nada que corregir)."""
    partes = []
    if c.get("balance"):
        r, g, b = c["balance"]
        partes.append(f"colorchannelmixer=rr={r:.3f}:gg={g:.3f}:bb={b:.3f}")
    if abs(c.get("gamma", 1) - 1) >= 0.005 or abs(c.get("contraste", 1) - 1) >= 0.005:
        partes.append(f"eq=gamma={c.get('gamma', 1):.3f}:contrast={c.get('contraste', 1):.3f}")
    if c.get("realce"):
        e = c["realce"]
        partes.append(f"vignette=angle={e['angulo']:.4f}:x0=w*{e['x']:.4f}:y0=h*{e['y']:.4f}")
    return ",".join(partes)


def para_toma(ruta, cfg=None, desde=None, hasta=None):
    """Mide la toma y devuelve (filtro, informe). El filtro se pasa a color.cadena(ruta, look, luz=filtro).
    informe: {"medida", "correccion", "filtro", "resumen"}; si no se pudo medir, filtro "" y el motivo en "resumen"."""
    cfg = {**DEF, **(cfg or {})}
    m = medir(ruta, cfg.get("cuadros", 5), desde, hasta)
    if m is None:
        return "", {"medida": None, "correccion": None, "filtro": "", "resumen": "no se pudo medir (se deja sin corrección de luz)"}
    c = proponer(m, cfg)
    f = filtro(c)
    cara = m["cara"]
    res = (f"luz {m['y_med']:.2f}" + (f", cara {cara['y']:.2f}" if cara else ", sin cara") +
           f" -> gamma {c['gamma']:.2f}, contraste {c['contraste']:.2f}, balance " +
           ("/".join(f"{x:.2f}" for x in c["balance"]) if c["balance"] else "igual") +
           (f", realce de cara {c['realce']['fuerza']:.2f}" if c["realce"] else "") +
           ("".join(f"  [{a}]" for a in c["avisos"])))
    return f, {"medida": m, "correccion": c, "filtro": f, "resumen": res}


def muestras():
    args = sys.argv[2:]
    op = lambda k, d=None: args[args.index(k) + 1] if k in args else d
    look, alto = op("--look", "natural"), int(op("--alto", 720))
    cfg = {"auto": True, "realce_cara": float(op("--realce", DEF["realce_cara"])),
           "balance": False if op("--balance", "auto") in ("no", "false") else "auto"}
    salida = Path(args[0]); salida.mkdir(parents=True, exist_ok=True)
    valores = {op(k) for k in ("--look", "--alto", "--realce", "--balance")}
    pedidos = [a for a in args[1:] if not a.startswith("--") and a not in valores]
    try:
        fuente = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        fuente = ImageFont.load_default()
    import atexit, shutil, tempfile
    tmp = Path(tempfile.mkdtemp(prefix="luz_muestras_"))        # cuadros sueltos: carpeta temporal propia
    atexit.register(shutil.rmtree, tmp, True)
    for i, p in enumerate(pedidos, 1):
        ruta, _, t = p.rpartition("@") if "@" in p else (p, "", "")
        ruta = Path(ruta); t = float(t) if t else None
        fl, inf = para_toma(ruta, cfg)
        paneles = [("ORIGINAL", fotograma(ruta, t, "", tmp / f"a{i}.jpg", alto)),
                   (f"SOLO LOOK {look} (como hoy)", fotograma(ruta, t, cadena(ruta, look), tmp / f"b{i}.jpg", alto)),
                   (f"LUZ + LOOK {look}", fotograma(ruta, t, cadena(ruta, look, luz=fl), tmp / f"c{i}.jpg", alto))]
        ancho = sum(im.width for _, im in paneles) + 10 * (len(paneles) + 1)
        hoja = Image.new("RGB", (ancho, alto + 84), (20, 20, 24))
        d, x = ImageDraw.Draw(hoja), 10
        for titulo, im in paneles:
            hoja.paste(im, (x, 40))
            d.text((x + 4, 8), titulo, fill=(255, 200, 110) if titulo.startswith("LUZ") else (230, 230, 230), font=fuente)
            x += im.width + 10
        d.text((14, alto + 48), f"{ruta.name}" + (f" @ {t:.1f}s" if t is not None else "") + f"   {inf['resumen']}"[:220], fill=(200, 200, 200), font=fuente)
        sal, k = salida / f"luz_{look}_{i:02d}.jpg", 2
        while sal.exists():                               # nunca encima de una hoja anterior
            sal = salida / f"luz_{look}_{i:02d}_{k}.jpg"; k += 1
        hoja.save(sal, quality=88)
        print("ok", sal, "|", inf["resumen"], flush=True)
    shutil.rmtree(tmp, ignore_errors=True)                # solo la carpeta temporal de arriba


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "muestras":
        muestras()
    elif len(sys.argv) > 2 and sys.argv[1] == "medir":
        _f, _inf = para_toma(sys.argv[2])
        print(json.dumps(_inf, ensure_ascii=False, indent=1))
    else:
        sys.exit('Uso: python luz.py muestras "<salida>" "toma.mp4@12.5" [--look natural] [--realce 0.15] [--balance auto|no]\n'
                 '     python luz.py medir "<toma.mp4>"')
