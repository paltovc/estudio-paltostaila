# Capas de video propias (como "Chroma key", "Superposición/PiP", "Pantalla dividida" y "Máscara" de CapCut):
#   python capas.py verde  "<fondo>" "<persona_con_fondo_verde>" "<salida.mp4>" [--color 00FF00] [--similitud 0.16]
#                          [--escala 1.0] [--x centro|izq|der] [--y abajo|centro]
#   python capas.py pip    "<fondo>" "<encima>" "<salida.mp4>" [--esquina abajo_der|abajo_izq|arriba_der|arriba_izq|centro]
#                          [--tam 0.30] [--forma redondeado|circulo|rect|corazon] [--borde acento] [--desde 3 --hasta 20]
#                          [--audio fondo|encima|ambos]
#   python capas.py dividir "<a>" "<b>" "<salida.mp4>" [--modo lado|arriba] [--ancho 1920 --alto 1080] [--audio a|b|ambos]
#   python capas.py mascara "<entrada>" "<salida.mp4>" --forma circulo|corazon|estrella|redondeado [--fondo desenfocado|negro|fondo]
#
# "<fondo>" y "<encima>" pueden ser video o imagen (una imagen dura lo que dure el otro). Uso típico en un curso: la
# presentación de fondo y la persona en una esquina en círculo; en un video musical: dos tomas lado a lado, o una
# toma dentro de un corazón. Los colores con nombre ("acento", "fondo") salen del kit de marca (--canal).
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw

try:
    from estudio import FFMPEG, FFPROBE
except Exception:
    FFMPEG, FFPROBE = "ffmpeg", "ffprobe"

IMG = {".jpg", ".jpeg", ".png", ".webp"}
TMP = Path(tempfile.gettempdir()) / "estudio_capas"
TMP.mkdir(exist_ok=True)


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit("ffmpeg falló:\n" + r.stderr[-1500:])
    return r.stderr


def es_img(p):
    return Path(p).suffix.lower() in IMG


def info(p):
    r = subprocess.run([str(FFPROBE), "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                        "-of", "default=nw=1", str(p)], capture_output=True, text=True).stdout
    d = dict(l.split("=") for l in r.split() if "=" in l)
    dur = float(d["duration"]) if d.get("duration", "N/A") != "N/A" else 0.0
    return int(d.get("width", 0)), int(d.get("height", 0)), dur


def tiene_audio(p):
    r = subprocess.run([str(FFPROBE), "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True).stdout
    return bool(r.strip())


def entradas(*rutas, dur=None):
    a = []
    for p in rutas:
        a += (["-loop", "1", "-t", f"{dur:.3f}", "-framerate", "30"] if es_img(p) else []) + ["-i", p]
    return a


def color_rgb(c, canal=None):
    import string
    if isinstance(c, str) and not (len(c.lstrip("#")) == 6 and all(ch in string.hexdigits for ch in c.lstrip("#"))):
        from diseno import marca, color
        return color(c, marca(canal))[:3]
    h = c.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def forma_png(w, h, forma, ruta, borde=0, color=(255, 255, 255)):
    """Máscara (blanco = se ve) o marco de color de la forma pedida, dibujada al cuádruple para bordes suaves."""
    k = 4
    W, H = w * k, h * k
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    if forma == "circulo":
        d.ellipse([0, 0, W - 1, H - 1], fill=255)
    elif forma == "redondeado":
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=int(min(W, H) * 0.08), fill=255)
    elif forma == "corazon":
        import math
        pts = []
        for i in range(400):
            t = 2 * math.pi * i / 400
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts.append((W / 2 + x / 17 * W / 2, H * 0.45 - y / 17 * H / 2))
        d.polygon(pts, fill=255)
    elif forma == "estrella":
        import math
        pts = [(W / 2 + (W / 2 if i % 2 == 0 else W / 5) * math.sin(math.pi * i / 5),
                H / 2 - (H / 2 if i % 2 == 0 else H / 5) * math.cos(math.pi * i / 5)) for i in range(10)]
        d.polygon(pts, fill=255)
    else:
        d.rectangle([0, 0, W, H], fill=255)
    m = m.resize((w, h), Image.LANCZOS)
    if borde:
        im = Image.new("RGBA", (w, h), color + (0,))
        im.putalpha(m)
        im.save(ruta)
    else:
        m.save(ruta)
    return ruta


def posicion(esquina, W, H, w, h, margen):
    x = {"izq": margen, "der": W - w - margen, "centro": (W - w) // 2}
    y = {"arriba": margen, "abajo": H - h - margen, "centro": (H - h) // 2}
    if esquina == "centro":
        return (W - w) // 2, (H - h) // 2
    v, hz = esquina.split("_")
    return x[hz], y[v]


def mapa_audio(cual, a, b, fa, fb):
    """Argumentos -map/-filter de audio según qué audio se quiere."""
    if cual == "ambos" and tiene_audio(fa) and tiene_audio(fb):
        return f";[{a}:a][{b}:a]amix=inputs=2:normalize=0[aud]", ["-map", "[aud]"]
    fuente = (b, fb) if cual in ("encima", "b") else (a, fa)
    return "", (["-map", f"{fuente[0]}:a?"] if not es_img(fuente[1]) else [])


def salida_cod(sal):
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", sal]


def verde(fondo, persona, sal, col="00FF00", sim=0.16, esc=1.0, x="centro", y="abajo"):
    W, H, d1 = info(fondo) if not es_img(fondo) else (*Image.open(fondo).size, 0)
    _, _, d2 = info(persona)
    dur = max(d1, d2) or 10
    ox = {"centro": "(W-w)/2", "izq": "W*0.04", "der": "W-w-W*0.04"}[x]
    oy = {"abajo": "H-h", "centro": "(H-h)/2"}[y]
    fc = (f"[0:v]scale={W}:{H},setsar=1[bg];[1:v]chromakey=0x{col}:{sim}:0.08,despill=type=green,"
          f"scale=-2:{int(H * esc)}[fg];[bg][fg]overlay={ox}:{oy}:shortest=0:eof_action=pass,format=yuv420p[v]")
    run([FFMPEG, "-v", "error", "-y", *entradas(fondo, persona, dur=dur), "-filter_complex", fc, "-map", "[v]",
         "-map", "1:a?", "-t", f"{d2 or dur:.3f}", *salida_cod(sal)])
    return sal


def pip(fondo, encima, sal, esquina="abajo_der", tam=0.30, forma="redondeado", borde="acento", desde=None, hasta=None,
        audio="fondo", canal=None):
    if es_img(fondo):
        W, H = Image.open(fondo).size
        d1 = 0
    else:
        W, H, d1 = info(fondo)
    ew, eh, d2 = info(encima) if not es_img(encima) else (*Image.open(encima).size, 0)
    dur = d1 or d2 or 10
    w = int(W * tam) // 2 * 2
    h = (w if forma in ("circulo", "corazon", "estrella") else int(w * eh / max(ew, 1))) // 2 * 2
    b = max(4, w // 60) if borde else 0
    mk = forma_png(w, h, forma, TMP / "pip_mascara.png")
    margen = int(W * 0.03)
    x, y = posicion(esquina, W, H, w + 2 * b, h + 2 * b, margen)
    en = f":enable='between(t,{desde or 0},{hasta if hasta is not None else 1e9})'"
    fc = (f"[0:v]scale={W}:{H},setsar=1[bg];[1:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=rgba[p];"
          f"[2:v]format=gray[m];[p][m]alphamerge[pa]")
    ins = entradas(fondo, encima, dur=dur) + ["-loop", "1", "-i", mk]
    if b:
        marco = forma_png(w + 2 * b, h + 2 * b, forma, TMP / "pip_marco.png", borde=1, color=color_rgb(borde, canal))
        ins += ["-loop", "1", "-i", marco]
        fc += f";[bg][3:v]overlay={x}:{y}{en}[b1];[b1][pa]overlay={x + b}:{y + b}:eof_action=pass{en},format=yuv420p[v]"
    else:
        fc += f";[bg][pa]overlay={x}:{y}:eof_action=pass{en},format=yuv420p[v]"
    extra, mapa = mapa_audio(audio, 0, 1, fondo, encima)
    run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex", fc + extra, "-map", "[v]", *mapa, "-t", f"{dur:.3f}", *salida_cod(sal)])
    return sal


def dividir(a, b, sal, modo="lado", W=1920, H=1080, audio="a"):
    da = 0 if es_img(a) else info(a)[2]
    db = 0 if es_img(b) else info(b)[2]
    dur = max(da, db) or 10
    if modo == "lado":
        w, h, pos = W // 2, H, f"{W // 2}:0"
    else:
        w, h, pos = W, H // 2, f"0:{H // 2}"
    fc = (f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1[a];"
          f"[1:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1[b];"
          f"color=black:s={W}x{H}:d={dur:.3f}[base];[base][a]overlay=0:0:eof_action=repeat[t];"
          f"[t][b]overlay={pos}:eof_action=repeat,drawbox=x={W // 2 - 2 if modo == 'lado' else 0}:y={0 if modo == 'lado' else H // 2 - 2}:"
          f"w={4 if modo == 'lado' else W}:h={H if modo == 'lado' else 4}:color=black:t=fill,format=yuv420p[v]")
    extra, mapa = mapa_audio("ambos" if audio == "ambos" else ("encima" if audio == "b" else "fondo"), 0, 1, a, b)
    run([FFMPEG, "-v", "error", "-y", *entradas(a, b, dur=dur), "-filter_complex", fc + extra, "-map", "[v]", *mapa,
         "-t", f"{dur:.3f}", *salida_cod(sal)])
    return sal


def mascara(ent, sal, forma="circulo", fondo="desenfocado", canal=None):
    W, H, dur = info(ent) if not es_img(ent) else (*Image.open(ent).size, 6)
    lado = int(min(W, H) * 0.86) // 2 * 2
    w, h = (lado, lado) if forma != "redondeado" else (int(W * 0.8) // 2 * 2, int(H * 0.8) // 2 * 2)
    mk = forma_png(w, h, forma, TMP / "mascara.png")
    if fondo == "desenfocado":
        bg = f"[0:v]scale={W}:{H},boxblur=30:3,eq=brightness=-0.12[bg]"
    else:
        c = color_rgb("fondo" if fondo == "fondo" else "#000000", canal)
        bg = f"color=0x{c[0]:02X}{c[1]:02X}{c[2]:02X}:s={W}x{H}:d={dur:.3f}[bg]"
    fc = (f"[0:v]split[o1][o2];{bg.replace('[0:v]', '[o1]')};[o2]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"format=rgba[p];[1:v]format=gray[m];[p][m]alphamerge[pa];[bg][pa]overlay=(W-w)/2:(H-h)/2:shortest=1,format=yuv420p[v]")
    run([FFMPEG, "-v", "error", "-y", *entradas(ent, dur=dur), "-loop", "1", "-i", mk, "-filter_complex", fc, "-map", "[v]",
         "-map", "0:a?", "-t", f"{dur:.3f}", *salida_cod(sal)])
    return sal


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit("Uso: ver el encabezado de capas.py")
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    f = lambda k: float(op(k)) if op(k) is not None else None
    from estudio import destino
    k = {"verde": 3, "pip": 3, "dividir": 3, "mascara": 2}.get(a[0])
    if k is not None and len(a) > k:
        a[k] = str(destino(a[k], *a[1:k]))
    if a[0] == "verde":
        verde(a[1], a[2], a[3], op("--color", "00FF00"), float(op("--similitud", 0.16)), float(op("--escala", 1.0)),
              op("--x", "centro"), op("--y", "abajo"))
    elif a[0] == "pip":
        pip(a[1], a[2], a[3], op("--esquina", "abajo_der"), float(op("--tam", 0.30)), op("--forma", "redondeado"),
            None if op("--borde") == "no" else op("--borde", "acento"), f("--desde"), f("--hasta"), op("--audio", "fondo"), op("--canal"))
    elif a[0] == "dividir":
        dividir(a[1], a[2], a[3], op("--modo", "lado"), int(op("--ancho", 1920)), int(op("--alto", 1080)), op("--audio", "a"))
    elif a[0] == "mascara":
        mascara(a[1], a[2], op("--forma", "circulo"), op("--fondo", "desenfocado"), op("--canal"))
    print("LISTO", a[3] if a[0] in ("verde", "pip", "dividir") else a[2], flush=True)


if __name__ == "__main__":
    main()
