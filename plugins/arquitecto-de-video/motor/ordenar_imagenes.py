# Pone en orden y con nombre las imagenes que llegan de ChatGPT, Codex u otro generador.
# Las descargas llegan con nombres al azar ("ChatGPT Image 2 nov 2026, 16_47_10.png"): se toman en el orden en que
# se crearon (fecha del archivo) y se COPIAN como  <ID>_img-001_<tema>.png, <ID>_img-002_<tema>.png ...
# El tema sale de 03_IMAGENES/prompts_imagenes.md si existe (tabla con n.º y archivo sugerido). Los originales no se tocan.
#   python ordenar_imagenes.py "C:\ruta\video"                         toma 03_IMAGENES\_entrantes
#   python ordenar_imagenes.py "C:\ruta\video" --desde "C:\Users\yo\Downloads" --ultimas 12
#   opciones: --inicio 5 (primer numero; por defecto el siguiente libre)  --por-nombre (orden por nombre, no por fecha)
#             --aplicar (sin esto solo muestra el plan)
import csv, re, shutil, sys
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw
from estudio import Proyecto, slug

pr = Proyecto()
args = sys.argv
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
EXT = (".png", ".jpg", ".jpeg", ".webp")
desde = Path(opt("--desde", str(pr.imagenes / "_entrantes")))
if not desde.exists():
    desde.mkdir(parents=True, exist_ok=True)
    sys.exit(f"Deja las imagenes descargadas en {desde} (o usa --desde) y vuelve a correr.")

patron = re.compile(rf"^{re.escape(pr.id)}_img-(\d{{3}})", re.I)
usados = sorted(int(m.group(1)) for p in pr.imagenes.glob("*") if (m := patron.match(p.name)))
inicio = int(opt("--inicio", (usados[-1] + 1) if usados else 1))

ya_ordenadas = set()
if (pr.imagenes / "orden_imagenes.csv").exists():
    with open(pr.imagenes / "orden_imagenes.csv", encoding="utf-8-sig", newline="") as fh:
        ya_ordenadas = {r["original"] for r in csv.DictReader(fh, delimiter=";")}
fuentes = [p for p in desde.iterdir() if p.suffix.lower() in EXT and not patron.match(p.name) and str(p) not in ya_ordenadas]
fuentes.sort(key=(lambda p: p.name.lower()) if "--por-nombre" in args else (lambda p: p.stat().st_mtime))
if opt("--ultimas"):
    fuentes = fuentes[-int(opt("--ultimas")):]
if not fuentes:
    sys.exit(f"No hay imagenes nuevas en {desde}")

# temas desde la tabla de prompts: | 1 | Imagen_001_dos_personas | ... |
temas = {}
prompts = pr.imagenes / "prompts_imagenes.md"
if prompts.exists():
    for linea in prompts.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*`?([^|`]+?)`?\s*\|", linea)
        if m:
            nombre = re.sub(r"^(img|imagen)[-_ ]?\d+[-_ ]?", "", Path(m.group(2).strip()).stem, flags=re.I)
            nombre = re.sub(rf"^{re.escape(pr.id)}_", "", nombre)
            temas[int(m.group(1))] = slug(nombre, 30) if nombre else ""

plan = []
for k, f in enumerate(fuentes):
    n = inicio + k
    tema = temas.get(n, "")
    nuevo = f"{pr.id}_img-{n:03d}{('_' + tema) if tema else ''}{f.suffix.lower()}"
    plan.append((n, f, pr.imagenes / nuevo))
    print(f"{n:03d}  {f.name[:60]:<60} -> {nuevo}")

# hoja de control: miniaturas numeradas para comprobar que el orden calza con el guion
W, H, cols = 320, 214, 5
filas = (len(plan) + cols - 1) // cols
hoja = Image.new("RGB", (W * cols, H * filas), "white")
d = ImageDraw.Draw(hoja)
for i, (n, f, _) in enumerate(plan):
    im = Image.open(f).convert("RGB")
    im.thumbnail((W, H))
    x, y = (i % cols) * W, (i // cols) * H
    hoja.paste(im, (x, y))
    d.rectangle((x, y, x + 54, y + 26), fill="black")
    d.text((x + 6, y + 6), f"{n:03d}", fill="yellow")
control = pr.imagenes / f"{pr.id}_control_orden_{datetime.now():%Y%m%d_%H%M}.jpg"
hoja.save(control, quality=85)
print(f"\nhoja de control: {control}")

if "--aplicar" not in args:
    print("Nada copiado todavia. Revisar la hoja de control y repetir con --aplicar.")
    sys.exit(0)
registro = pr.imagenes / "orden_imagenes.csv"
nuevo_registro = not registro.exists()
with open(registro, "a", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    if nuevo_registro:
        w.writerow(["numero", "archivo", "original", "copiado"])
    for n, f, destino in plan:
        if destino.exists():
            print("YA EXISTE, no se pisa:", destino.name)
            continue
        shutil.copy2(f, destino)
        w.writerow([n, destino.name, str(f), f"{datetime.now():%Y-%m-%d %H:%M}"])
print(f"{len(plan)} imagenes copiadas en orden a {pr.imagenes} (registro: {registro.name})")
