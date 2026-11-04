# Seguimiento de movimiento (como "Tracking" de CapCut): un texto, círculo o flecha que sigue a una persona u objeto.
#   python seguimiento.py "<video>" "<salida.mp4>" --desde 3.0 --hasta 9.5 --caja 820,300,180,420
#        [--texto "Ava"] [--marca circulo|flecha|texto] [--lado arriba|abajo|izq|der] [--color acento] [--canal bachata]
#   --caja x,y,ancho,alto: dónde está lo que se sigue en el segundo --desde (en píxeles del video).
#        Para elegirla: python seguimiento.py "<video>" --cuadro 3.0   -> saca ese cuadro con una cuadrícula numerada.
#   Deja también <salida>_recorrido.json (posición cada cuadro) y <salida>_control.jpg (dónde lo vio cada 0,5 s).
# Funciona bien con una persona u objeto claro; si alguien se cruza delante o sale del cuadro, el seguimiento se
# congela donde lo vio por última vez (y lo avisa con el segundo). Todo es local: OpenCV + ffmpeg.
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

try:
    from estudio import FFMPEG
except Exception:
    FFMPEG = "ffmpeg"


def rastreador():
    import cv2
    for nombre in ("TrackerCSRT_create", "TrackerKCF_create", "TrackerMIL_create"):
        for mod in (cv2, getattr(cv2, "legacy", None)):
            if mod is not None and hasattr(mod, nombre):
                return getattr(mod, nombre)(), nombre.replace("Tracker", "").replace("_create", "")
    sys.exit("Este OpenCV no trae rastreadores; python -m pip install opencv-contrib-python-headless")


def cuadro(video, t, salida):
    import cv2
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, f = cap.read()
    if not ok:
        sys.exit("No pude leer ese segundo del video")
    im = Image.fromarray(f[:, :, ::-1])
    d = ImageDraw.Draw(im)
    paso = 100
    for x in range(0, im.width, paso):
        d.line([x, 0, x, im.height], fill=(255, 255, 0), width=1)
        d.text((x + 3, 3), str(x), fill=(255, 255, 0))
    for y in range(0, im.height, paso):
        d.line([0, y, im.width, y], fill=(255, 255, 0), width=1)
        d.text((3, y + 3), str(y), fill=(255, 255, 0))
    im.save(salida, quality=88)
    return salida


def seguir(video, desde, hasta, caja):
    import cv2
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, round(desde * fps))
    ok, f = cap.read()
    if not ok:
        sys.exit("No pude leer el video en --desde")
    tr, tipo = rastreador()
    tr.init(f, tuple(int(v) for v in caja))
    pts, perdidos, ultimo = [], [], None
    n = round((hasta - desde) * fps)
    x, y, w, h = caja
    pts.append((desde, x + w / 2, y + h / 2, w, h))
    muestras = [(0.0, f.copy(), tuple(caja))]
    for i in range(1, n):
        ok, f = cap.read()
        if not ok:
            break
        bien, b = tr.update(f)
        t = desde + i / fps
        if bien:
            x, y, w, h = b
            ultimo = (x, y, w, h)
        else:
            perdidos.append(round(t, 2))
            x, y, w, h = ultimo or caja
        pts.append((t, x + w / 2, y + h / 2, w, h))
        if i % round(fps / 2) == 0 and len(muestras) < 24:
            muestras.append((t - desde, f.copy(), (x, y, w, h)))
    # suavizado (media móvil de 7 cuadros): sin temblor
    k = 3
    lisos = []
    for i, p in enumerate(pts):
        v = pts[max(0, i - k): i + k + 1]
        lisos.append((p[0], sum(q[1] for q in v) / len(v), sum(q[2] for q in v) / len(v), p[3], p[4]))
    return lisos, perdidos, tipo, muestras, fps


def pegatina(marca, texto, col, alto_obj, canal):
    from diseno import marca as mk_, color, fuente
    mk = mk_(canal)
    c = color(col, mk)
    borde = color("borde", mk)
    if marca == "circulo":
        lado = int(alto_obj * 1.15)
        im = Image.new("RGBA", (lado * 4, lado * 4), (0, 0, 0, 0))
        g = max(8, lado // 12) * 4
        ImageDraw.Draw(im).ellipse([g, g, lado * 4 - g, lado * 4 - g], outline=c, width=g)
        return im.resize((lado, lado), Image.LANCZOS)
    if marca == "flecha":
        L = max(60, int(alto_obj * 0.35))
        im = Image.new("RGBA", (L * 4, L * 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.polygon([(L * 2, L * 4 - 8), (L * 0.6, L * 2.2), (L * 1.5, L * 2.2), (L * 1.5, 8), (L * 2.5, 8), (L * 2.5, L * 2.2),
                   (L * 3.4, L * 2.2)], fill=c, outline=borde, width=12)
        return im.resize((L, L), Image.LANCZOS)
    f = fuente("titulo", max(28, int(alto_obj * 0.13)), mk)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    b = d0.textbbox((0, 0), texto, font=f, stroke_width=4)
    im = Image.new("RGBA", (b[2] - b[0] + 40, b[3] - b[1] + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 3, fill=borde[:3] + (190,))
    d.text((20 - b[0], 15 - b[1]), texto, font=f, fill=c, stroke_width=2, stroke_fill=borde)
    return im


def main():
    a = sys.argv[1:]
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if "--cuadro" in a:
        s = cuadro(a[0], float(op("--cuadro")), str(Path(a[0]).with_name(Path(a[0]).stem + f"_cuadro_{op('--cuadro')}s.jpg")))
        print("LISTO", s)
        return
    video, sal = Path(a[0]), Path(a[1])
    desde, hasta = float(op("--desde", 0)), float(op("--hasta", 5))
    caja = [float(v) for v in op("--caja").split(",")]
    marca = op("--marca", "texto" if op("--texto") else "circulo")
    lisos, perdidos, tipo, muestras, fps = seguir(video, desde, hasta, caja)
    if perdidos:
        print(f"AVISO lo perdí de vista {len(perdidos)} cuadros (desde {perdidos[0]} s); ahí queda quieto. Revisa el control.")
    st = pegatina(marca, op("--texto", ""), op("--color", "acento"), caja[3], op("--canal"))
    png = sal.with_name(sal.stem + "_marca.png")
    st.save(png)
    lado = op("--lado", "arriba")
    cmds = []
    for t, cx, cy, w, h in lisos:
        if marca == "circulo":
            x, y = cx - st.width / 2, cy - st.height / 2
        elif lado == "arriba":
            x, y = cx - st.width / 2, cy - h / 2 - st.height - 10
        elif lado == "abajo":
            x, y = cx - st.width / 2, cy + h / 2 + 10
        elif lado == "izq":
            x, y = cx - w / 2 - st.width - 10, cy - st.height / 2
        else:
            x, y = cx + w / 2 + 10, cy - st.height / 2
        cmds.append(f"{t:.3f} [enter] overlay x {int(x)}, [enter] overlay y {int(y)};")
    cmd_file = sal.with_name(sal.stem + "_cmds.txt")
    cmd_file.write_text("\n".join(cmds) + "\n", encoding="utf-8")
    x0 = cmds[0].split(" overlay x ")[1].split(",")[0]
    y0 = cmds[0].split(" overlay y ")[1].rstrip(";")
    fc = (f"[1:v]format=rgba,fade=t=in:st={desde}:d=0.25:alpha=1,fade=t=out:st={max(desde, hasta - 0.25)}:d=0.25:alpha=1[m];"
          f"[0:v]sendcmd=f='{cmd_file.name}'[b];[b][m]overlay=x={x0}:y={y0}:shortest=1:enable='between(t,{desde},{hasta})',format=yuv420p[v]")
    r = subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", str(video.resolve()), "-loop", "1", "-i", png.name,
                        "-filter_complex", fc, "-map", "[v]", "-map", "0:a?", "-shortest", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "18", "-c:a", "copy", str(sal.resolve())], cwd=sal.parent, capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg falló:\n" + r.stderr[-1200:])
    sal.with_name(sal.stem + "_recorrido.json").write_text(json.dumps(
        {"rastreador": tipo, "perdidos": perdidos, "puntos": [[round(p, 2) for p in q] for q in lisos]}), encoding="utf-8")
    # hoja de control: qué vio en cada momento
    tiles = []
    for t, f, (x, y, w, h) in muestras[:12]:
        im = Image.fromarray(f[:, :, ::-1])
        dd = ImageDraw.Draw(im)
        g = max(6, im.width // 160)
        dd.rectangle([x, y, x + w, y + h], outline=(0, 0, 0), width=g + 4)
        dd.rectangle([x, y, x + w, y + h], outline=(0, 255, 120), width=g)
        im.thumbnail((320, 320))
        tiles.append(im)
    if tiles:
        tw, th = tiles[0].size
        hoja = Image.new("RGB", (tw * min(6, len(tiles)), th * ((len(tiles) + 5) // 6)))
        for i, im in enumerate(tiles):
            hoja.paste(im, ((i % 6) * tw, (i // 6) * th))
        hoja.save(sal.with_name(sal.stem + "_control.jpg"), quality=85)
    print(f"LISTO {sal} (rastreador {tipo})", flush=True)


if __name__ == "__main__":
    main()
