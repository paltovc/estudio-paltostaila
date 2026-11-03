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
#               {"archivo": "video.mp4", "hasta": 211.30, "desde_clip": 5.0, "velocidad": 1.0, "brillo": 0.02} ] }
# Cada tramo empieza donde termina el anterior ("hasta" en segundos de la canción, idealmente en un golpe).
import json, re, subprocess, sys
from pathlib import Path
from color import cadena, LOOKS

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
    vf = f"{enc},{cadena(ruta, look, t.get('brillo', 0.0))}{nitidez},setpts=PTS/{vel},fps={fps}"
    run([FFMPEG, "-v", "error", "-y", "-ss", f"{t.get('desde_clip', 0):.3f}", "-t", f"{dur * vel + 0.5:.3f}", "-i", ruta,
         "-an", "-vf", vf, "-frames:v", round(dur * fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", 18,
         "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", sal])


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
    inicio, lista = cfg["audio"]["desde"], []
    for n, t in enumerate(cfg["tramos"], 1):
        dur = t["hasta"] - inicio
        inicio = t["hasta"]
        sal = tmp / f"tramo_{n:02d}.mp4"
        lista.append(sal)
        if solo and n != solo and sal.exists():
            continue
        ruta = mat / t["archivo"]
        (tramo_foto if ruta.suffix.lower() in FOTO else tramo_video)(ruta, dur, t, W, H, fps, look, sal)
        print(f"tramo {n}/{len(cfg['tramos'])} {t['archivo']} {dur:.2f} s", flush=True)
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
