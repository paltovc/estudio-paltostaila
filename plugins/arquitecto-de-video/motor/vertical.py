# Cortes verticales 9:16 (TikTok, Shorts, Reels) desde el video ya armado.
# En proyecto.json: "vertical": [{"nombre": "Short_Creencia1", "desde": "frase inicial", "hasta": "frase donde termina",
#                                 "chico": "CREENCIA 1", "titulo": "¿Invertir es solo\\Npara ricos?"}]
#   python vertical.py "C:\ruta\video"
import sys
from estudio import Proyecto, FFMPEG, run, palabras, buscar, cues, ts, slug, entregar, parcial_de
import vivo
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

pr = Proyecto()
F = pr["subtitulos"]["fuente"]
CAB = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{F},66,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,8,70,70,1330,1
Style: Titulo,{F},92,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,8,60,60,330,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def seguir(video, t0, dur, ancho_fuente):
    """Reencuadre automático (como Auto Reframe de CapCut): dónde está el sujeto en cada segundo.
    Usa la cara si OpenCV está instalado; si no, lo que más se mueve y tiene más detalle. Devuelve la expresión de x
    para el crop de 1080 px sobre el video escalado a 1920 de alto, suavizada para que la cámara no salte."""
    import subprocess
    w, h = 480, 270
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", str(video), "-vf",
                        f"fps=2,scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    datos = r.stdout
    n = len(datos) // (w * h)
    try:
        import cv2, numpy as np
        caras = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        if caras.empty():
            raise RuntimeError("sin el archivo de caras")
    except Exception:
        cv2 = np = caras = None
    centros, previo = [], None
    for k in range(n):
        cuadro = datos[k * w * h:(k + 1) * w * h]
        cx = None
        if cv2 is not None:
            g = np.frombuffer(cuadro, dtype=np.uint8).reshape(h, w)
            enc = caras.detectMultiScale(g, 1.1, 5, minSize=(20, 20))
            if len(enc):
                x, y, fw, fh = max(enc, key=lambda e: e[2] * e[3])
                cx = (x + fw / 2) / w
        if cx is None:     # sin cara: columnas con más movimiento y detalle
            col = [0.0] * w
            for y in range(0, h, 3):
                fila = cuadro[y * w:(y + 1) * w]
                ant = previo[y * w:(y + 1) * w] if previo else None
                for x in range(1, w - 1, 2):
                    v = abs(fila[x + 1] - fila[x - 1]) + (abs(fila[x] - ant[x]) * 2 if ant else 0)
                    col[x] += v
            tot = sum(col)
            cx = sum(i * c for i, c in enumerate(col)) / tot / w if tot else 0.5
        centros.append(cx)
        previo = cuadro
    if not centros:
        return "(iw-1080)/2"
    # suavizar: mediana de 5 y luego promedio móvil de 5 (la "cámara" se desliza, no salta)
    med = [sorted(centros[max(0, i - 2):i + 3])[len(centros[max(0, i - 2):i + 3]) // 2] for i in range(len(centros))]
    suave = [sum(med[max(0, i - 2):i + 3]) / len(med[max(0, i - 2):i + 3]) for i in range(len(med))]
    pts, ultimo = [], None
    for i, c in enumerate(suave):            # puntos clave: cada 0,5 s, solo cuando cambia de verdad o cada 4 s
        t = i / 2
        if ultimo is None or abs(c - ultimo[1]) > 0.03 or t - ultimo[0] >= 4 or i == len(suave) - 1:
            pts.append((t, c)); ultimo = (t, c)
    X = lambda c: f"max(0,min(iw-1080,iw*{c:.4f}-540))"
    expr = X(pts[-1][1])
    for (ta, ca), (tb, cb) in reversed(list(zip(pts, pts[1:]))):
        expr = f"if(lt(t,{tb:.2f}),max(0,min(iw-1080,iw*({ca:.4f}+({cb - ca:.4f})*(t-{ta:.2f})/{max(tb - ta, 0.01):.2f})-540)),{expr})"
    print(f"  reencuadre: {len(pts)} puntos ({'caras' if cv2 is not None else 'movimiento'}), sujeto entre "
          f"{min(suave):.2f} y {max(suave):.2f} del ancho", flush=True)
    return expr


def corte(segs, pals, v):
    t0 = float(v["desde_s"]) if "desde_s" in v else buscar(pals, v["desde"]) - 0.15
    if "hasta_s" in v:
        t1 = float(v["hasta_s"])
    else:
        t1 = buscar(pals, v["hasta"]) - 0.3 if v.get("hasta") else pr.duracion()
    dur = t1 - t0
    if not 15 <= dur <= 180:
        print(f"AVISO {v['nombre']}: dura {dur:.1f} s (lo ideal para vertical es 45-90 s)")
    viva = vivo.Vivo(pr, pals, 1080, 1920, vertical=True) if vivo.activo(pr) else None
    lineas = [vivo.insertar(CAB, viva.estilos()) if viva else CAB]
    if v.get("titulo"):
        lineas.append(f"Dialogue: 1,{ts(0)},{ts(dur)},Titulo,,0,0,0,,{{\\fs52\\c&H6AD15B&}}{v.get('chico', '')}\\N{{\\fs92\\c&HFFFFFF&}}{v['titulo']}\n")
    if viva and pr["subtitulos"].get("estilo") == "vivo":
        lineas += [l + "\n" for l in viva.subtitulos(t0, t1)]
    else:
        for a, b, txt in cues(segs, 60):
            if b > t0 and a < t1:
                lineas.append(f"Dialogue: 0,{ts(max(a - t0, 0))},{ts(min(b, t1) - t0)},Sub,,0,0,0,,{txt}\n")
    if viva and v.get("elementos", True):
        lineas += [l + "\n" for l in viva.elementos(t0, t1)]
    ass = f"tmp/vertical_{v['nombre']}.ass"
    (pr.salida / ass).write_text("".join(lineas), encoding="utf-8-sig")
    if dur > 180:
        sys.exit(f"{v['nombre']}: dura {dur:.0f} s; un Short de YouTube puede durar como maximo 3 minutos")
    if v.get("modo") == "seguir":    # pantalla completa y el recorte sigue al sujeto
        x = seguir(pr.salida / "tmp" / "solo_video.mp4", t0, dur, None)
        vf = (f"[0:v]scale=-2:1920,crop=1080:1920:x='{x}':y=0,"
              f"ass={ass},fade=t=in:d=0.3,fade=t=out:st={dur - 0.6:.3f}:d=0.6[v]")
    elif v.get("modo") == "recorte":   # pantalla completa: recorta del 16:9 una franja vertical (cuidado con personajes en los bordes)
        cx = float(v.get("centro_x", 0.5))
        vf = (f"[0:v]scale=-2:1920,crop=1080:1920:x='max(0,min(iw-1080,iw*{cx}-540))':y=0,"
              f"ass={ass},fade=t=in:d=0.3,fade=t=out:st={dur - 0.6:.3f}:d=0.6[v]")
    else:   # marco: el video completo al centro sobre una copia desenfocada (no corta nada)
        vf = ("[0:v]split[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=30:2,eq=brightness=-0.18[fondo];"
              "[b]scale=1080:-2[frente];[fondo][frente]overlay=0:(H-h)/2,"
              f"ass={ass},fade=t=in:d=0.3,fade=t=out:st={dur - 0.6:.3f}:d=0.6[v]")
    nombre = f"{pr.base_nombre}_{slug(v['nombre'])}_9x16.mp4"
    parcial = parcial_de(pr.salida / nombre).name      # el Short anterior no se pisa: queda como *_anterior-<fecha>
    run([FFMPEG, "-v", "error", "-y", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", "tmp/solo_video.mp4",
         "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", "tmp/narracion.m4a", "-filter_complex", vf,
         "-map", "[v]", "-map", "1:a", "-af", f"afade=t=in:d=0.2,afade=t=out:st={dur - 0.6:.3f}:d=0.6",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(pr.fps),
         "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", "-shortest", *SIN_METADATOS, "-movflags", "+faststart", parcial], cwd=pr.salida)
    entregar(pr.salida / parcial, pr.salida / nombre)
    print(f"LISTO {pr.salida / nombre} ({dur:.1f} s)", flush=True)


def main():
    if not pr["vertical"]:
        print("no hay cortes verticales definidos en proyecto.json")
        return
    segs, pals = palabras(pr)
    for v in pr["vertical"]:
        corte(segs, pals, v)


if __name__ == "__main__":
    main()
