# Gráficos animados propios con los colores y letras del canal (como los gráficos animados de Canva, hechos de cero):
#   barras que crecen, línea que se dibuja (interés compuesto), torta o dona que se llena y número que cuenta.
#
# En un video narrado, en proyecto.json:
#   "graficos": [
#     {"escena": 12, "tipo": "barras", "titulo": "Lo que cobra cada AFP", "etiquetas": ["Uno", "Dos", "Tres"],
#      "valores": [0.46, 1.16, 1.45], "sufijo": "%", "decimales": 2, "destacar": 0},
#     {"escena": 18, "tipo": "linea", "titulo": "$100.000 al mes durante 30 años", "x": [0, 10, 20, 30],
#      "series": [{"nombre": "Con interés", "valores": [0, 20.7, 76.6, 226]}, {"nombre": "Sin interés", "valores": [0, 12, 24, 36]}],
#      "prefijo": "$", "sufijo": " M", "empieza_en": "si lo dejas crecer"},
#     {"escena": 22, "tipo": "torta", "titulo": "Regla 50/30/20", "partes": [{"nombre": "Necesidades", "valor": 50},
#      {"nombre": "Gustos", "valor": 30}, {"nombre": "Ahorro", "valor": 20}], "dona": true, "sufijo": "%"},
#     {"escena": 30, "tipo": "contador", "hasta": 226000000, "prefijo": "$", "texto": "en 30 años"} ]
#   python graficos.py "<proyecto>"            -> 04_CLIPS_FLOW\escena_NNN.mp4 (armar.py los inserta como un clip)
#   "empieza_en": la animación arranca cuando la voz dice esa frase (dentro de la escena); si no, al empezar la escena.
#
# Suelto, sin proyecto:
#   python graficos.py --spec grafico.json --salida g.mp4 [--dur 6] [--vertical] [--canal finanzas]
import json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

try:
    from estudio import FFMPEG
except Exception:
    FFMPEG = "ffmpeg"
from diseno import marca, color, fuente

SS = 2            # se dibuja al doble y se achica: bordes suaves


def suave(x):     # entrada rápida, frenada suave
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def numero(v, g):
    dec = g.get("decimales", 0 if abs(v) >= 100 or float(v).is_integer() else 1)
    s = f"{abs(v):,.{dec}f}".replace(",", "§").replace(".", ",").replace("§", ".")    # formato chileno 1.234,5
    return f"{'-' if v < 0 else ''}{g.get('prefijo', '')}{s}{g.get('sufijo', '')}"


def paleta(mk):
    # el rojo de "alerta" va al final: se usa para lo malo (comisiones, deudas) y se pide con "color"
    return [color("acento", mk), color("acento2", mk), (120, 170, 255, 255), (255, 140, 200, 255), color("texto", mk), color("alerta", mk)]


def lienzo(W, H, mk, g):
    im = Image.new("RGBA", (W, H), color("fondo", mk))
    if "fondo2" in mk["colores"]:              # degradado suave del fondo al fondo2
        c1, c2 = color("fondo", mk), color("fondo2", mk)
        d = ImageDraw.Draw(im)
        for y in range(0, H, 2):
            k = (y / H) ** 1.5
            d.rectangle([0, y, W, y + 2], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3)) + (255,))
    d = ImageDraw.Draw(im)
    if g.get("titulo"):
        f = fuente("titulo", H * 0.075, mk)
        b = d.textbbox((0, 0), g["titulo"], font=f)
        d.text(((W - (b[2] - b[0])) / 2, H * 0.06), g["titulo"], font=f, fill=color("texto", mk),
               stroke_width=int(H * 0.004), stroke_fill=color("borde", mk))
    return im, d


def barras(g, p, W, H, mk):
    im, d = lienzo(W, H, mk, g)
    vals, ets = g["valores"], g.get("etiquetas", [""] * len(g["valores"]))
    n, vmax = len(vals), max(max(vals), 1e-9)
    x0, x1, base, alto = W * 0.10, W * 0.90, H * 0.84, H * 0.56
    hueco = (x1 - x0) / n
    ancho = hueco * 0.62
    fv, fe = fuente("titulo", H * 0.055, mk), fuente("texto", H * 0.042, mk)
    d.line([x0 - W * 0.02, base, x1 + W * 0.02, base], fill=color("texto", mk, 150), width=int(H * 0.004))
    for i, (v, e) in enumerate(zip(vals, ets)):
        k = suave((p - i * 0.12) / 0.7)                       # una barra detrás de otra
        h = alto * v / vmax * k
        cx = x0 + hueco * (i + 0.5)
        col = color("acento", mk) if g.get("destacar") in (None, i) else color("acento2", mk)
        if h > 2:
            d.rounded_rectangle([cx - ancho / 2, base - h, cx + ancho / 2, base], radius=int(ancho * 0.12), fill=col)
        t = numero(v * k, g)
        b = d.textbbox((0, 0), t, font=fv)
        d.text((cx - (b[2] - b[0]) / 2, base - h - H * 0.075), t, font=fv, fill=color("texto", mk),
               stroke_width=int(H * 0.003), stroke_fill=color("borde", mk))
        b = d.textbbox((0, 0), e, font=fe)
        d.text((cx - (b[2] - b[0]) / 2, base + H * 0.02), e, font=fe, fill=color("texto", mk, int(255 * min(1, p * 3))))
    return im


def linea(g, p, W, H, mk):
    im, d = lienzo(W, H, mk, g)
    xs, series = g["x"], g["series"]
    vmax = max(max(s["valores"]) for s in series) or 1
    vmin = min(0, min(min(s["valores"]) for s in series))
    x0, x1, y0, y1 = W * 0.12, W * 0.86, H * 0.86, H * 0.24
    px = lambda i: x0 + (x1 - x0) * i / (len(xs) - 1)
    py = lambda v: y0 - (y0 - y1) * (v - vmin) / (vmax - vmin)
    fe, fv = fuente("texto", H * 0.038, mk), fuente("titulo", H * 0.05, mk)
    gris = color("texto", mk, 70)
    for k in range(5):
        y = y0 - (y0 - y1) * k / 4
        d.line([x0, y, x1, y], fill=gris, width=max(1, int(H * 0.002)))
    for i, x in enumerate(xs):
        t = str(x)
        b = d.textbbox((0, 0), t, font=fe)
        d.text((px(i) - (b[2] - b[0]) / 2, y0 + H * 0.02), t, font=fe, fill=color("texto", mk, 200))
    avance = suave(p / 0.8) * (len(xs) - 1)                   # hasta qué punto del eje x va dibujada
    pal = paleta(mk)
    for si, s in enumerate(series):
        col = tuple(s["color"]) + (255,) if "color" in s else pal[si % len(pal)]
        pts = []
        for i in range(len(xs)):
            if i <= avance:
                pts.append((px(i), py(s["valores"][i])))
            else:
                f = avance - math.floor(avance)
                a = s["valores"][i - 1]
                pts.append((px(i - 1) + (px(i) - px(i - 1)) * f, py(a + (s["valores"][i] - a) * f)))
                break
        if len(pts) > 1:
            d.line(pts, fill=col, width=int(H * 0.012), joint="curve")
        xe, ye = pts[-1]
        r = H * 0.014
        d.ellipse([xe - r, ye - r, xe + r, ye + r], fill=col)
        v = s["valores"][-1] if p >= 0.8 else (vmin + (y0 - ye) / (y0 - y1) * (vmax - vmin))
        t = numero(v, g)
        d.text((xe + H * 0.02, ye - H * 0.06), t, font=fv, fill=col, stroke_width=int(H * 0.003), stroke_fill=color("borde", mk))
        if s.get("nombre"):
            ly = H * 0.17 + si * H * 0.055
            d.rounded_rectangle([W * 0.12, ly, W * 0.12 + H * 0.04, ly + H * 0.04], radius=int(H * 0.008), fill=col)
            d.text((W * 0.12 + H * 0.06, ly - H * 0.005), s["nombre"], font=fe, fill=color("texto", mk))
    return im


def torta(g, p, W, H, mk):
    im, d = lienzo(W, H, mk, g)
    partes = g["partes"]
    total = sum(x["valor"] for x in partes) or 1
    cx, cy, r = W * 0.36, H * 0.57, H * 0.30
    pal = paleta(mk)
    k = suave(p / 0.75)
    ang = -90.0
    fe, fv = fuente("texto", H * 0.045, mk), fuente("titulo", H * 0.06, mk)
    for i, x in enumerate(partes):
        barrido = 360 * x["valor"] / total * k
        col = tuple(x["color"]) + (255,) if "color" in x else pal[i % len(pal)]
        if barrido > 0.3:
            d.pieslice([cx - r, cy - r, cx + r, cy + r], ang, ang + barrido, fill=col)
        ang += barrido
        ly = H * 0.32 + i * H * 0.11
        a = int(255 * suave((p - 0.15 - i * 0.1) / 0.3))
        d.rounded_rectangle([W * 0.66, ly, W * 0.66 + H * 0.05, ly + H * 0.05], radius=int(H * 0.01), fill=col[:3] + (a,))
        d.text((W * 0.66 + H * 0.075, ly - H * 0.008), f"{x['nombre']}  {numero(x['valor'], g)}", font=fe,
               fill=color("texto", mk, a))
    if g.get("dona", True):
        ri = r * 0.55
        d.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=color("fondo", mk))
        if g.get("centro"):
            b = d.textbbox((0, 0), g["centro"], font=fv)
            d.text((cx - (b[2] - b[0]) / 2, cy - (b[3] - b[1]) / 2 - b[1]), g["centro"], font=fv, fill=color("texto", mk))
    return im


def contador(g, p, W, H, mk):
    im, d = lienzo(W, H, mk, dict(g, titulo=g.get("titulo")))
    v = g.get("desde", 0) + (g["hasta"] - g.get("desde", 0)) * suave(p / 0.7)
    t = numero(v, g)
    tam = H * 0.22
    f = fuente("titulo", tam, mk)
    while d.textbbox((0, 0), t, font=f)[2] > W * 0.9 and tam > 20:
        tam *= 0.93
        f = fuente("titulo", tam, mk)
    b = d.textbbox((0, 0), numero(g["hasta"], g), font=f)               # centrado según el número final: no baila
    x = (W - (b[2] - b[0])) / 2
    esc = 1 + 0.06 * max(0, 1 - abs(p - 0.72) / 0.06)                   # pequeño golpe al llegar
    capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(capa).text((x, H * 0.36), t, font=f, fill=color("acento", mk), stroke_width=int(H * 0.008),
                              stroke_fill=color("borde", mk))
    if esc > 1:
        capa = capa.resize((int(W * esc), int(H * esc)), Image.LANCZOS).crop(
            (int(W * (esc - 1) / 2), int(H * (esc - 1) / 2), int(W * (esc - 1) / 2) + W, int(H * (esc - 1) / 2) + H))
    im.alpha_composite(capa)
    if g.get("texto"):
        fe = fuente("texto", H * 0.07, mk)
        b = d.textbbox((0, 0), g["texto"], font=fe)
        ImageDraw.Draw(im).text(((W - (b[2] - b[0])) / 2, H * 0.68), g["texto"], font=fe,
                                fill=color("texto", mk, int(255 * suave((p - 0.5) / 0.3))))
    return im


TIPOS = {"barras": barras, "linea": linea, "torta": torta, "dona": torta, "contador": contador}


def render(g, dur, sal, W=1920, H=1080, fps=30, canal=None, retraso=0.0):
    mk = marca(canal or g.get("canal"))
    dibujar = TIPOS[g["tipo"]]
    n = max(1, round(dur * fps))
    anim = g.get("duracion_animacion", min(3.0, max(1.2, dur - retraso - 0.8)))
    proc = subprocess.Popen([str(FFMPEG), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                             "-pix_fmt", "yuv420p", str(sal)], stdin=subprocess.PIPE)
    ultimo, clave = None, None
    for i in range(n):
        t = i / fps
        p = max(0.0, (t - retraso) / anim) if t >= retraso else 0.0
        p = min(p, 1.0)
        if clave != round(p, 4) or ultimo is None:          # cuando ya terminó, se repite el cuadro (rápido)
            im = dibujar(g, p, W * SS, H * SS, mk).convert("RGB").resize((W, H), Image.LANCZOS)
            ultimo, clave = im.tobytes(), round(p, 4)
        proc.stdin.write(ultimo)
    proc.stdin.close()
    if proc.wait():
        raise SystemExit("ffmpeg falló al escribir " + str(sal))
    return sal


def main():
    a = sys.argv[1:]
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if "--spec" in a:
        g = json.loads(Path(op("--spec")).read_text(encoding="utf-8-sig"))
        W, H = (1080, 1920) if "--vertical" in a else (1920, 1080)
        s = render(g, float(op("--dur", 6)), op("--salida", "grafico.mp4"), W, H, 30, op("--canal"))
        print("LISTO", s)
        return
    from estudio import Proyecto, palabras, buscar
    pr = Proyecto()
    esc = {r["n"]: r for r in pr.escenas()}
    pals = None
    pr.clips.mkdir(parents=True, exist_ok=True)
    canal = pr.cfg.get("canal")
    for g in pr.cfg.get("graficos", []):
        r = esc.get(int(g["escena"]))
        if not r:
            print(f"AVISO escena {g['escena']} no existe en la receta"); continue
        sal = pr.clips / f"escena_{r['n']:03d}.mp4"
        marca = sal.with_suffix(".graficos.json")             # constancia de que el clip lo hizo graficos.py (con su hash)
        propio = False
        if sal.exists() and marca.exists():
            import hashlib
            try:
                propio = json.loads(marca.read_text(encoding="utf-8")).get("sha256") == hashlib.sha256(sal.read_bytes()).hexdigest()
            except (ValueError, OSError):
                propio = False
        if sal.exists() and ("--rehacer" not in a or not propio):
            print(f"escena {r['n']}: ya hay un clip ({sal.name}); no lo piso. "
                  + ("Usa --rehacer para reemplazar uno hecho por graficos.py" if propio else "No lo hizo graficos.py o cambió desde entonces (puede ser de Flow): no se reemplaza"))
            continue
        retraso = 0.0
        if g.get("empieza_en"):
            pals = pals or palabras(pr)[1]
            try:
                retraso = max(0.0, buscar(pals, g["empieza_en"]) - r["t0"])
            except ValueError:
                print(f"AVISO escena {r['n']}: no encontré la frase «{g['empieza_en']}»; parte al inicio")
        dur = r["t1"] - r["t0"] + 1.0                                   # margen para las transiciones
        render(g, dur, sal, pr.ancho, pr.alto, pr.fps, canal, retraso)
        import hashlib
        marca.write_text(json.dumps({"sha256": hashlib.sha256(sal.read_bytes()).hexdigest(), "grafico": g}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"escena {r['n']}: {g['tipo']} {dur:.1f} s -> {sal.name}", flush=True)
    print("LISTO", flush=True)


if __name__ == "__main__":
    main()
