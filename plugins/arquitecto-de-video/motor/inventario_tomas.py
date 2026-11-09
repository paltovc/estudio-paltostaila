# Inventario de material grabado (videos y fotos de celular o cámara) sin tocar los originales.
# Para cada video: duración, resolución real (aplica la rotación del celular), cuadros por segundo, audio
# y una tira de 6 fotogramas; para las fotos, una hoja con miniaturas. Deja todo en <salida>:
#   inventario.csv, hoja_videos_NN.jpg, hoja_fotos_NN.jpg
#   python inventario_tomas.py "C:\carpeta\material" "C:\carpeta\proyecto\05_REVISION"
import csv, json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

try:
    from estudio import FFMPEG, FFPROBE
except Exception:
    FFMPEG, FFPROBE = "ffmpeg", "ffprobe"

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
VID = {".mp4", ".mov", ".m4v", ".mts", ".avi", ".mkv", ".3gp"}
FOT = {".jpg", ".jpeg", ".png", ".heic", ".webp"}
archivos = sorted(p for p in src.iterdir() if p.is_file() and "(1)" not in p.stem)
try:
    fuente = ImageFont.truetype("arial.ttf", 18)
except Exception:
    fuente = ImageFont.load_default()


def probe(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(p)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return json.loads(r.stdout or "{}")


def rotacion(st):
    for sd in st.get("side_data_list", []) or []:
        if "rotation" in sd:
            return int(float(sd["rotation"]))
    return int(st.get("tags", {}).get("rotate", 0) or 0)


filas, tiras = [], []
with tempfile.TemporaryDirectory() as tmp:
    for p in archivos:
        ext = p.suffix.lower()
        if ext in VID:
            info = probe(p)
            v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
            if not v:
                continue
            a = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)
            dur = float(info.get("format", {}).get("duration", 0) or 0)
            w, h = int(v["width"]), int(v["height"])
            if abs(rotacion(v)) in (90, 270):
                w, h = h, w
            num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1").split("/")
            fps = round(float(num) / float(den or 1), 2) if float(den or 1) else 0
            cuadros = []
            for i in range(6):
                t = dur * (i + 0.5) / 6
                f = Path(tmp) / f"{p.stem}_{i}.jpg"
                subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1",
                                "-vf", "scale=-2:300", "-q:v", "4", *SIN_METADATOS, str(f)], capture_output=True)
                if f.exists():
                    cuadros.append((t, Image.open(f).convert("RGB")))
            filas.append({"archivo": p.name, "tipo": "video", "ancho": w, "alto": h,
                          "orientacion": "vertical" if h > w else "horizontal", "fps": fps,
                          "duracion_s": round(dur, 2), "audio": "sí" if a else "no",
                          "camara_lenta_posible": "x4" if fps >= 100 else ("x2" if fps >= 50 else ""),
                          "mb": round(p.stat().st_size / 1e6, 1)})
            tiras.append((p.name, filas[-1], cuadros))
            print("video", p.name, f"{w}x{h} {fps}fps {dur:.1f}s", flush=True)
        elif ext in FOT:
            try:
                im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
            except Exception as e:
                print("no se pudo abrir", p.name, e)
                continue
            filas.append({"archivo": p.name, "tipo": "foto", "ancho": im.width, "alto": im.height,
                          "orientacion": "vertical" if im.height > im.width else "horizontal", "fps": "",
                          "duracion_s": "", "audio": "", "camara_lenta_posible": "", "mb": round(p.stat().st_size / 1e6, 1)})
            im.thumbnail((360, 360))
            tiras.append((p.name, filas[-1], im))
            print("foto", p.name, flush=True)

with open(out / "inventario.csv", "w", newline="", encoding="utf-8-sig") as f:
    wr = csv.DictWriter(f, fieldnames=list(filas[0].keys()), delimiter=";")
    wr.writeheader(); wr.writerows(filas)

# hojas de videos: una fila por video, 6 fotogramas
vids = [t for t in tiras if t[1]["tipo"] == "video"]
for n in range(0, len(vids), 6):
    grupo = vids[n:n + 6]
    alto_fila = 340
    hoja = Image.new("RGB", (6 * 240 + 70, alto_fila * len(grupo)), (24, 24, 28))
    d = ImageDraw.Draw(hoja)
    for r, (nombre, fila, cuadros) in enumerate(grupo):
        y = r * alto_fila
        d.text((10, y + 6), f"V{n + r + 1:02d}  {nombre}  {fila['ancho']}x{fila['alto']}  {fila['fps']} fps  "
                            f"{fila['duracion_s']} s  {'(cámara lenta ' + fila['camara_lenta_posible'] + ')' if fila['camara_lenta_posible'] else ''}",
               fill=(255, 220, 120), font=fuente)
        x = 10
        for t, im in cuadros:
            im = im.copy(); im.thumbnail((230, 300))
            hoja.paste(im, (x, y + 32))
            d.text((x + 4, y + 36), f"{int(t // 60)}:{int(t % 60):02d}", fill=(255, 255, 255), font=fuente)
            x += im.width + 10
    hoja.save(out / f"hoja_videos_{n // 6 + 1:02d}.jpg", quality=82)

fotos = [t for t in tiras if t[1]["tipo"] == "foto"]
for n in range(0, len(fotos), 15):
    grupo = fotos[n:n + 15]
    hoja = Image.new("RGB", (5 * 300, 3 * 400), (24, 24, 28))
    d = ImageDraw.Draw(hoja)
    for i, (nombre, fila, im) in enumerate(grupo):
        x, y = (i % 5) * 300, (i // 5) * 400
        t = im.copy(); t.thumbnail((290, 360))
        hoja.paste(t, (x + 5, y + 30))
        d.text((x + 6, y + 6), f"F{n + i + 1:02d} {nombre[:22]}", fill=(255, 220, 120), font=fuente)
    hoja.save(out / f"hoja_fotos_{n // 15 + 1:02d}.jpg", quality=82)

print(f"\n{len(vids)} videos, {len(fotos)} fotos -> {out}")
