# Prueba de las herramientas de cámara con material inventado que trae GPS y datos de celular.
# Corre grabado.py (proponer, cortar, armar), montaje_tomas.py y doblaje.py (voz desde archivos + mezclar --quemar)
# y revisa con metadatos_personales() cada video o audio que producen. No toca nada fuera de una carpeta temporal nueva.
#   python prueba_camara.py "<carpeta del motor>"
import json, subprocess, sys, tempfile
from pathlib import Path

MOTOR = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(MOTOR))
from estudio import FFMPEG, metadatos_personales  # noqa: E402

py = sys.executable
base = Path(tempfile.mkdtemp(prefix="prueba_camara_"))
mat = base / "material"; mat.mkdir()
fallas = []


def ff(*a):
    subprocess.run([str(FFMPEG), "-v", "error", "-y", *map(str, a)], check=True)


def paso(*a):
    r = subprocess.run([py, *map(str, a)], cwd=MOTOR, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ult = (r.stdout.strip().splitlines() or [""])[-1]
    print(("OK   " if r.returncode == 0 else "FALLA") + f" {Path(str(a[0])).name} {a[2] if len(a) > 2 else ''}: {ult[:150]}", flush=True)
    if r.returncode:
        print(r.stdout[-1500:], r.stderr[-2500:])
        fallas.append(str(a[:3]))
    return r


CEL = ["-metadata", "location=+33.4489-070.6693/", "-metadata", "make=Apple", "-metadata", "model=iPhone 15",
       "-metadata", "creation_time=2026-01-01T10:00:00Z", "-metadata:s:v", "handler_name=Core Media Video"]
for i, (f, col) in enumerate([("cam1.mp4", "blue"), ("cam2.mp4", "green")], 1):
    ff("-f", "lavfi", "-i", f"testsrc2=d=9:s=1280x720:r=30", "-f", "lavfi", "-i", f"sine=f={300 + 100 * i}:d=9",
       *CEL, "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac", "-shortest", mat / f)
ff("-f", "lavfi", "-i", "color=c=orange:s=1280x720:d=1", "-frames:v", "1", mat / "foto.jpg")
ff("-f", "lavfi", "-i", "sine=f=440:d=30", "-metadata", "title=Cancion de prueba", "-metadata", "artist=Alguien",
   mat / "cancion.wav")
assert "location" in (metadatos_personales(mat / "cam1.mp4") or []), "el material de ensayo debía traer GPS"


def revisar(nombre, archivos):
    archivos = [p for p in archivos if p.suffix.lower() in (".mp4", ".wav", ".m4a", ".mp3", ".mov")]
    if not archivos:
        print(f"FALLA {nombre}: no produjo archivos"); fallas.append(nombre); return
    malos = {p.name: metadatos_personales(p) for p in archivos}
    malos = {k: ("no se pudo leer" if v is None else v) for k, v in malos.items() if v is None or v}
    print(("OK   " if not malos else "FALLA") + f" {nombre}: {len(archivos)} archivos revisados" +
          (f"; con metadatos: {malos}" if malos else ", ninguno con GPS ni datos del celular"), flush=True)
    if malos:
        fallas.append(nombre)


# ---------- grabado.py (cursos) ----------
cur = base / "Curso"
paso(MOTOR / "nuevo_proyecto.py", cur, "--nombre", "Curso")
cfg_f = cur / "proyecto.json"; cfg = json.loads(cfg_f.read_text(encoding="utf-8"))
cfg["grabado"] = {"material": str(mat), "look": "natural", "limpiar_voz": True}
cfg_f.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
(cur / "06_RECETA" / "tomas").mkdir(parents=True, exist_ok=True)
textos = {"cam1": ["Hola, hoy vamos a ver cómo ahorrar.", "Primero, anota tus gastos."],
          "cam2": ["Segundo, separa un monto fijo.", "Y listo, eso es todo."]}
for toma, frases in textos.items():
    segs, t = [], 0.5
    for fr in frases:
        ws = []
        for w in fr.split():
            ws.append({"word": w, "start": round(t, 2), "end": round(t + 0.3, 2), "score": 0.9}); t += 0.4
        segs.append({"start": ws[0]["start"], "end": ws[-1]["end"], "text": fr, "words": ws}); t += 0.8
    (cur / "06_RECETA" / "tomas" / f"{toma}.json").write_text(json.dumps({"segments": segs}, ensure_ascii=False), encoding="utf-8")
for p in ("proponer", "cortar", "armar"):
    paso(MOTOR / "grabado.py", cur, p)
revisar("grabado.py", [*(cur / "07_RENDER" / "tmp").glob("solo_video*.mp4"), *(cur / "02_VOZ").glob("*grabado*.wav"),
                       *(cur / "07_RENDER" / "tmp" / "grabado").glob("*.mp4")])

# ---------- montaje_tomas.py (videos musicales) ----------
mus = base / "Musica"; (mus / "02_CANCION").mkdir(parents=True)
ff("-i", mat / "cancion.wav", "-c", "copy", mus / "02_CANCION" / "cancion.wav")   # copia de ensayo con sus etiquetas
(mus / "montaje.json").write_text(json.dumps({
    "id": "NDF-PRUEBA", "version": "v1", "material": str(mat), "ancho": 720, "alto": 1280, "fps": 30, "look": "calido",
    "audio": {"archivo": "02_CANCION/cancion.wav", "desde": 1.0, "hasta": 13.0, "entrada": 0.3, "salida": 1.0},
    "tramos": [{"archivo": "cam1.mp4", "hasta": 5.0, "desde_clip": 1.0},
               {"archivo": "foto.jpg", "hasta": 8.0, "zoom": "entra", "transicion": ["mezcla", 9]},
               {"archivo": "cam2.mp4", "hasta": 13.0, "desde_clip": 0.5, "transicion": ["giro", 11]}]},
    ensure_ascii=False), encoding="utf-8")
paso(MOTOR / "montaje_tomas.py", mus)
revisar("montaje_tomas.py", [p for p in (mus / "07_RENDER").rglob("*.mp4")])

# ---------- doblaje.py ----------
vid = base / "ingles" / "video_en.mp4"; vid.parent.mkdir()
ff("-i", mat / "cam1.mp4", "-c", "copy", "-map_metadata", "0", vid)        # copia de ensayo con su GPS
c = vid.parent / "video_en_doblaje"; (c / "voces").mkdir(parents=True)
segm = [{"id": 1, "inicio": 0.5, "fin": 3.0, "original": "Hello there", "traduccion": "Hola a todos"},
        {"id": 2, "inicio": 4.0, "fin": 7.0, "original": "Save money", "traduccion": "Ahorra dinero"}]
(c / "segmentos.json").write_text(json.dumps({"video": str(vid), "idioma": "en", "segmentos": segm}, ensure_ascii=False), encoding="utf-8")
for s in segm:
    ff("-f", "lavfi", "-i", "sine=f=500:d=1.5", "-metadata", "artist=Pagina de voz", c / "voces" / f"{s['id']:03d}.mp3")
paso(MOTOR / "doblaje.py", "voz", c, "--desde-archivos")
paso(MOTOR / "doblaje.py", "mezclar", c, "--quemar")
revisar("doblaje.py", [p for p in c.rglob("*") if p.is_file() and "voces" not in p.parts])

print("\n" + ("PRUEBA DE CÁMARA SUPERADA" if not fallas else f"FALLÓ: {fallas}") + f"  (carpeta: {base})")
sys.exit(1 if fallas else 0)
