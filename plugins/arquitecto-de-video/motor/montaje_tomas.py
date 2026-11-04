# Montaje con material grabado (videos y fotos) sobre una canción o un audio, cortando en los golpes del ritmo.
# Lee <proyecto>/montaje.json, arma cada tramo con su color (color.py), los une y pone la canción a -14 LUFS.
# No toca los originales: lee de la carpeta de material y escribe en <proyecto>/07_RENDER.
#   python montaje_tomas.py "<proyecto>"            -> video final + revisión
#   python montaje_tomas.py "<proyecto>" --tramo 3  -> rehace solo ese tramo y vuelve a unir
#
# montaje.json:
# { "id": "NDF-001", "version": "v1", "material": "G:\\...\\carpeta", "ancho": 1080, "alto": 1920, "fps": 30,
#   "look": "calido",
#   "audio": {"archivo": "02_CANCION/cancion.wav", "desde": 195.72, "hasta": 244.55, "entrada": 0.4, "salida": 3.0},
#   "tramos": [ {"archivo": "foto.jpg", "hasta": 199.62, "zoom": "entra"},
#               {"archivo": "video.mp4", "hasta": 211.30, "desde_clip": 5.0, "velocidad": 1.0, "brillo": 0.02},
#               {"archivo": "baile.mp4", "hasta": 220.0, "rampa": [1.0, 0.35], "estabilizar": true} ] }
# "rampa": curva de velocidad de v0 a v1 (cámara lenta que entra de a poco); "estabilizar": quita el temblor de la mano.
# Efectos (efectos.py): "efectos": ["brillo", "grano"] por tramo (o en la raíz para todos), "congelar": {"en": 1.2,
#   "dura": 0.8} (cuadro congelado con destello, el tramo sigue durando lo mismo) y "fluido": true (cámara lenta sin saltos).
# Transiciones (las 68 de transiciones.py, con nombre del estudio, de CapCut o de ffmpeg; duración en cuadros):
#   en un tramo: "transicion": ["giro", 10]  -> transición AL ENTRAR a ese tramo (desde el anterior)
#   para todos:  "transicion": ["mezcla", 8] en la raíz de montaje.json, o "variar_transiciones": ["empujar", "golpe", ...]
#   "transicion": "corte" en un tramo deja ese cambio como corte seco. Sin nada de esto: cortes secos en el golpe.
#   El tramo nuevo empieza igual en su golpe: la transición se monta encima de ese instante, así que no se corre el ritmo.
# Cada tramo empieza donde termina el anterior ("hasta" en segundos de la canción, idealmente en un golpe).
import math, json, re, subprocess, sys
from pathlib import Path
from color import cadena, LOOKS
import transiciones
import efectos as fx

try:
    from estudio import FFMPEG, FFPROBE
except Exception:
    FFMPEG, FFPROBE = "ffmpeg", "ffprobe"

FOTO = {".jpg", ".jpeg", ".png", ".webp"}
LOOKS.setdefault("calido_foto", dict(c=1.02, s=1.0, g=1.0, med=(0.04, 0.01, -0.04), alt=(0.02, 0.0, -0.02), vin=1))


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit("ffmpeg falló:\n" + " ".join(map(str, cmd))[:600] + "\n" + r.stderr[-1500:])
    return r.stderr


def tamano(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_side_data=rotation",
                        "-of", "json", str(p)], capture_output=True, text=True)
    s = json.loads(r.stdout)["streams"][0]
    w, h = s["width"], s["height"]
    rot = next((abs(int(float(d["rotation"]))) for d in s.get("side_data_list", []) if "rotation" in d), 0)
    return (h, w) if rot in (90, 270) else (w, h)


def tramo_foto(ruta, dur, t, W, H, fps, look, sal):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(ruta))
    w, h = im.size
    n = max(1, round(dur * fps))
    z = {"entra": f"1+0.07*on/{n}", "sale": f"1.07-0.07*on/{n}"}.get(t.get("zoom", "entra"), "1")
    cx = t.get("centro_x", 0.5)
    color = cadena(ruta, look + "_foto" if look + "_foto" in LOOKS else look, t.get("brillo", 0.0))
    if h / w >= H / W * 0.9:   # foto vertical: llena la pantalla
        pw, ph = int(W * 1.5), int(H * 1.5)
        fc = (f"[0]scale={pw}:{ph}:force_original_aspect_ratio=increase,crop={pw}:{ph}:(iw-{pw})*{cx}:(ih-{ph})/2,"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={fps},{color}[v]")
    else:                      # foto horizontal: completa al centro sobre un fondo desenfocado de la misma foto
        fh = int(W * h / w) // 2 * 2
        fc = (f"[0]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:2,"
              f"eq=brightness=-0.10:saturation=0.8[bg];[b]scale={W * 2}:-2,"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{fh}:fps={fps}[fg];"
              f"[bg][fg]overlay=0:(H-h)/2,{color}[v]")
    if t.get("efectos"):
        fc = fc[:-3] + "," + fx.cadena(t["efectos"]) + "[v]"
    run([FFMPEG, "-v", "error", "-y", "-loop", "1", "-framerate", fps, "-t", f"{dur:.3f}", "-i", ruta,
         "-filter_complex", fc, "-map", "[v]", "-frames:v", n, "-c:v", "libx264", "-preset", "veryfast", "-crf", 18,
         "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", sal])


def tramo_video(ruta, dur, t, W, H, fps, look, sal):
    vel = t.get("velocidad", 1.0)
    w, h = tamano(ruta)
    cx = t.get("centro_x", 0.5)
    if w / h > W / H:   # video horizontal en salida vertical: recorte
        enc = f"scale=-2:{H}:flags=lanczos,crop={W}:{H}:(iw-{W})*{cx}:0"
    else:
        enc = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    nitidez = ",unsharp=5:5:0.6" if max(w, h) < 1200 else ""
    estab = "deshake=rx=24:ry=24," if t.get("estabilizar") else ""          # toma movida a mano (como Stabilize de CapCut)
    if t.get("rampa"):     # curva de velocidad (speed ramp): pasa de v0 a v1 a lo largo de la toma, p. ej. [1.0, 0.35]
        v0, v1 = (float(x) for x in t["rampa"])
        fuente = dur * (v1 - v0) / math.log(v1 / v0) if abs(v1 - v0) > 1e-3 else dur * v0
        k = fuente / (v1 - v0) if abs(v1 - v0) > 1e-3 else 0
        tiempo = (f"setpts='({k:.5f}*log(({v0}+({v1 - v0:.5f})*T/{fuente:.5f})/{v0}))/TB'" if k
                  else f"setpts=PTS/{v0}")
        consumo = fuente
    else:
        tiempo, consumo = f"setpts=PTS/{vel}", dur * vel
    lento = t.get("rampa") or vel < 1
    ritmo = fx.fluido(fps) if t.get("fluido") and lento else f"fps={fps}"     # cámara lenta que inventa cuadros
    vf = f"{estab}{enc},{cadena(ruta, look, t.get('brillo', 0.0))}{nitidez},{tiempo},{ritmo}"
    if t.get("congelar"):
        c = t["congelar"]
        vf += "," + fx.congelar(float(c["en"]), float(c.get("dura", 0.8)), fps, c.get("destello", True))
    if t.get("efectos"):
        vf += "," + fx.cadena(t["efectos"])
    run([FFMPEG, "-v", "error", "-y", "-ss", f"{t.get('desde_clip', 0):.3f}", "-t", f"{consumo + 0.5:.3f}", "-i", ruta,
         "-an", "-vf", vf, "-frames:v", round(dur * fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", 18,
         "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", sal])


def unir_con_transiciones(lista, cuadros, TRS, W, H, fps, tmp):
    """Cada tramo i ya trae TRS[i+1] cuadros de más al final. Se arma: cuerpo_1, trans_1_2, cuerpo_2, ...
    cuerpo_i = cuadros [entrada_i, cuadros_i) del tramo; trans = cola del anterior + primeros d cuadros del siguiente.
    El total de cuadros no cambia y cada tramo sigue empezando en su golpe."""
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", 18, "-pix_fmt", "yuv420p",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
    piezas = []
    for i, ruta in enumerate(lista):
        h = TRS[i][1] if TRS[i] else 0
        if h >= cuadros[i]:
            raise SystemExit(f"Tramo {i + 1}: dura menos que su transición de entrada ({h} cuadros); acórtala o alarga el tramo")
        cuerpo = tmp / f"cuerpo_{i + 1:02d}.mp4"
        run([FFMPEG, "-v", "error", "-y", "-i", ruta, "-vf", f"trim=start_frame={h}:end_frame={cuadros[i]},setpts=PTS-STARTPTS",
             "-an", *enc, cuerpo])
        piezas.append(cuerpo)
        if i + 1 < len(lista) and TRS[i + 1]:
            nombre, d = TRS[i + 1]
            pieza = tmp / f"trans_{i + 1:02d}_{i + 2:02d}.mp4"
            fc = (f"[0]trim=start_frame={cuadros[i]}:end_frame={cuadros[i] + d},setpts=PTS-STARTPTS[p];"
                  f"[1]trim=end_frame={d},setpts=PTS-STARTPTS[q];" + transiciones.cadena(nombre, d, fps, W, H, "p", "q", "v"))
            run([FFMPEG, "-v", "error", "-y", "-i", ruta, "-i", lista[i + 1], "-filter_complex", fc, "-map", "[v]",
                 "-frames:v", d, "-an", *enc, pieza])
            piezas.append(pieza)
    return piezas


def audio(cfg, base, sal, objetivo=-14.0):
    a = cfg["audio"]
    dur = a["hasta"] - a["desde"]
    filtro = f"afade=t=in:d={a.get('entrada', 0.3)},afade=t=out:st={dur - a.get('salida', 2.5):.3f}:d={a.get('salida', 2.5)}"
    tmp = sal.with_name("_audio_previo.wav")
    run([FFMPEG, "-v", "error", "-y", "-ss", a["desde"], "-t", f"{dur:.3f}", "-i", base / a["archivo"], "-af", filtro, "-ar", 48000, tmp])
    ganancia = 0.0
    for _ in range(4):
        s = run([FFMPEG, "-hide_banner", "-i", tmp, "-af", f"volume={ganancia}dB,alimiter=limit=0.89:level=0,ebur128", "-f", "null", "-"])
        i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", s)[-1])
        if abs(i - objetivo) < 0.3:
            break
        ganancia += objetivo - i
    run([FFMPEG, "-v", "error", "-y", "-i", tmp, "-af", f"volume={ganancia}dB,alimiter=limit=0.89:level=0", sal])
    tmp.unlink()
    return i


def main():
    base = Path(sys.argv[1])
    cfg = json.loads((base / "montaje.json").read_text(encoding="utf-8-sig"))
    W, H, fps, look = cfg.get("ancho", 1080), cfg.get("alto", 1920), cfg.get("fps", 30), cfg.get("look", "calido")
    mat = Path(cfg["material"])
    tmp = base / "07_RENDER" / "tmp"; tmp.mkdir(parents=True, exist_ok=True)
    solo = int(sys.argv[sys.argv.index("--tramo") + 1]) if "--tramo" in sys.argv else None
    tramos = cfg["tramos"]
    variar = cfg.get("variar_transiciones", [])
    def entrada(i):                       # transición al entrar al tramo i (0-based); None = corte
        if i == 0:
            return None
        t = tramos[i].get("transicion", cfg.get("transicion"))
        if t is None and variar:
            t = [variar[(i - 1) % len(variar)], cfg.get("cuadros_transicion", 8)]
        if not t or t == "corte":
            return None
        return (t, cfg.get("cuadros_transicion", 8)) if isinstance(t, str) else (t[0], int(t[1]))
    TRS = [entrada(i) for i in range(len(tramos))]
    inicio, lista, cuadros = cfg["audio"]["desde"], [], []
    for n, t in enumerate(tramos, 1):
        dur = t["hasta"] - inicio
        inicio = t["hasta"]
        cuadros.append(round(dur * fps))
        cola = TRS[n][1] if n < len(tramos) and TRS[n] else 0     # cuadros extra para la transición de salida
        sal = tmp / f"tramo_{n:02d}.mp4"
        lista.append(sal)
        if solo and n != solo and sal.exists():
            continue
        ruta = mat / t["archivo"]
        t = dict(t, efectos=t.get("efectos", cfg.get("efectos")))
        (tramo_foto if ruta.suffix.lower() in FOTO else tramo_video)(ruta, dur + cola / fps, t, W, H, fps, look, sal)
        print(f"tramo {n}/{len(tramos)} {t['archivo']} {dur:.2f} s", flush=True)
    if any(TRS):
        lista = unir_con_transiciones(lista, cuadros, TRS, W, H, fps, tmp)
    (tmp / "lista.txt").write_text("".join(f"file '{p.name}'\n" for p in lista), encoding="utf-8")
    run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", 0, "-i", tmp / "lista.txt", "-c", "copy", tmp / "imagen.mp4"])
    lufs = audio(cfg, base, tmp / "audio.wav")
    total = cfg["audio"]["hasta"] - cfg["audio"]["desde"]
    final = base / "07_RENDER" / f"{cfg['id']}_{cfg['version']}_vertical.mp4"
    run([FFMPEG, "-v", "error", "-y", "-i", tmp / "imagen.mp4", "-i", tmp / "audio.wav",
         "-vf", f"fade=t=in:d=0.4,fade=t=out:st={total - 1.2:.3f}:d=1.2", "-c:v", "libx264", "-preset", "medium", "-crf", 18,
         "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "aac", "-b:a", "256k", "-t", f"{total:.3f}", "-movflags", "+faststart", final])
    rev = base / "05_REVISION"; rev.mkdir(exist_ok=True)
    run([FFMPEG, "-v", "error", "-y", "-i", final, "-vf", "fps=1/2,scale=270:-1,tile=8x3", "-frames:v", 1, "-q:v", 4,
         rev / f"{cfg['id']}_{cfg['version']}_hoja.jpg"])
    s = run([FFMPEG, "-hide_banner", "-i", final, "-vf", "blackdetect=d=0.2:pix_th=0.05", "-af", "ebur128", "-f", "null", "-"])
    negros = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", s)
    print(f"\nlisto: {final}\nduración {total:.2f} s, volumen {lufs:.1f} LUFS, tramos negros: {negros or 'ninguno'}")


if __name__ == "__main__":
    main()
