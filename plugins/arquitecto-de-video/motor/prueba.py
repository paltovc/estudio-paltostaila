# Prueba del motor: primero pruebas rápidas de las protecciones (sin render); después crea un video de 12 s con datos
# inventados en una carpeta temporal, lo arma completo (con transiciones de cuadros impares) y revisa el resultado.
# No toca nada fuera de esa carpeta.
#   python prueba.py            (borra la carpeta al terminar si todo salio bien)
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from estudio import FFMPEG   # tambien confirma que ffmpeg existe

carpeta = Path(tempfile.mkdtemp(prefix="prueba_estudio_")) / "VideoPrueba"
py = sys.executable


def paso(*args):
    r = subprocess.run([py, *args], cwd=AQUI, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ultima = (r.stdout.strip().splitlines() or [""])[-1]
    print(("OK   " if r.returncode == 0 else "FALLA") + f" {args[0]}: {ultima}")
    if r.returncode != 0:
        print(r.stdout[-800:], r.stderr[-1500:])
        sys.exit(f"La prueba fallo en {args[0]}. Carpeta conservada: {carpeta}")
    return r.stdout


def paso_falla(texto, *args):
    """El paso debe negarse (código distinto de 0) y decir `texto`."""
    r = subprocess.run([py, *args], cwd=AQUI, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sal = r.stdout + r.stderr
    bien = r.returncode != 0 and texto in sal
    print(("OK   " if bien else "FALLA") + f" {args[0]} se niega: {texto}")
    if not bien:
        print(sal[-1200:])
        sys.exit(f"La protección de {args[0]} no funcionó. Carpeta conservada: {carpeta}")


# ---- pruebas rápidas (sin render) ----
from estudio import nombre_libre, destino
tmp = Path(tempfile.mkdtemp(prefix="prueba_rapida_"))
f = tmp / "a.mp4"; f.write_bytes(b"x")
assert nombre_libre(tmp / "b.mp4") == tmp / "b.mp4"
assert nombre_libre(f) == tmp / "a_2.mp4", nombre_libre(f)
assert destino(f) == tmp / "a_2.mp4"
try:
    destino(f, f); raise AssertionError("destino aceptó escribir sobre la entrada")
except SystemExit:
    pass
print("OK   nombre_libre / destino: nunca se pisa un archivo ni la entrada")
import revisar_idioma as ri
assert ri.sospechosas("BILL $$$") == ["BILL"] and ri.sospechosas("FEES") == ["FEES"]
assert ri.sospechosas("Comisiones que podrían evitarse") == [] and ri.sospechosas("CREENCIAS antes de invertir") == []
assert ri.sospechosas("Un plan basado únicamente") == [] and ri.sospechosas("Sale caro") == []
print("OK   revisar_idioma: reconoce inglés y deja pasar el español")
seg = tmp / "v_doblaje"; seg.mkdir()
(seg / "segmentos.json").write_text(json.dumps({"video": str(f), "segmentos": [{"id": 1, "traduccion": "hola"}]}), encoding="utf-8")
paso_falla("no se borran", "doblaje.py", "preparar", str(f), "--carpeta", str(seg))
shutil.rmtree(tmp, ignore_errors=True)

paso("nuevo_proyecto.py", str(carpeta), "--nombre", "VideoPrueba")
for i, color in enumerate([(36, 99, 166), (64, 182, 107)], 1):
    im = Image.new("RGB", (1536, 1024), color)
    d = ImageDraw.Draw(im)
    d.ellipse((500, 250, 1036, 786), fill=(250, 248, 237))
    im.save(carpeta / "03_IMAGENES" / f"img_{i}.png")
subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=220:d=12", carpeta / "02_VOZ" / "parte1.mp3"], check=True)
texto = "Esta es una prueba del estudio. Si ves este video, el motor funciona bien. Gracias.".split()
words, t = [], 0.4
for w in texto:
    words.append({"word": w, "start": round(t, 2), "end": round(t + 0.35, 2)})
    t += 0.5 + (0.8 if w.endswith(".") else 0)
(carpeta / "06_RECETA" / "transcripcion.json").write_text(json.dumps(
    {"segments": [{"start": 0.4, "end": t, "text": " ".join(texto), "words": words}]}, ensure_ascii=False), encoding="utf-8")
(carpeta / "06_RECETA" / "receta.csv").write_text(
    "numero;archivo;inicio;fin;duracion;frase;tipo;origen;nota\n"
    "1;img_1.png;0:00.00;0:06.00;6;Esta es una prueba;imagen;;\n"
    "2;img_2.png;0:06.00;0:12.00;6;Si ves este video;imagen;;\n", encoding="utf-8-sig")
cfg = json.loads((carpeta / "proyecto.json").read_text(encoding="utf-8"))
cfg.update({"escenas_capitulo": [2],
            "transiciones": {"normal": ["fade", 13], "capitulo": ["smoothleft", 17], "plano": ["fade", 7]},   # impares a propósito
            "rotulos": [{"frase": "Si ves este video", "chico": "PRUEBA", "grande": "El motor funciona", "segundos": 3}],
            "vertical": [{"nombre": "Short_Prueba", "desde": "Esta es una prueba", "titulo": "Prueba"}]})
(carpeta / "proyecto.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

receta = carpeta / "06_RECETA" / "receta.csv"
contenido = receta.read_text(encoding="utf-8-sig")
receta.write_text("numero;archivo;inicio;fin;duracion;frase;tipo;origen;nota\n", encoding="utf-8-sig")
paso_falla("no tiene escenas", "frases.py", str(carpeta), "--validar")
receta.write_text(contenido, encoding="utf-8-sig")
paso("frases.py", str(carpeta), "--validar")
sal_armar = paso("armar.py", str(carpeta))
linea = next((l for l in sal_armar.splitlines() if l.startswith("cuadros:")), "")
if not linea.endswith("OK"):
    sys.exit(f"armar.py no dio los cuadros exactos con transiciones impares ({linea}). Carpeta conservada: {carpeta}")
print("OK   armar.py: cuadros exactos con transiciones impares (" + linea + ")")
paso("sonidos.py", str(carpeta))
paso("terminar.py", str(carpeta))
srts = {q: q.stat().st_mtime_ns for q in (carpeta / "07_RENDER").glob("*.srt")}
paso_falla("Ya existe", "terminar.py", str(carpeta))
if any(q.stat().st_mtime_ns != m for q, m in srts.items()):
    sys.exit(f"terminar.py se negó pero igual reescribió el .srt. Carpeta conservada: {carpeta}")
print("OK   terminar.py se niega antes de escribir nada (el .srt no cambió)")
paso("terminar.py", str(carpeta), "--rehacer")
if not list((carpeta / "07_RENDER").glob("*_anterior-*.mp4")):
    sys.exit(f"--rehacer no guardó la entrega anterior. Carpeta conservada: {carpeta}")
print("OK   terminar.py --rehacer guarda la entrega anterior")
paso("vertical.py", str(carpeta))
paso("terminado.py", str(carpeta))
informe = paso("revisar.py", str(carpeta))
if "0 puntos a revisar" in informe:
    shutil.rmtree(carpeta.parent, ignore_errors=True)
    print("\nPRUEBA SUPERADA: el estudio funciona en este computador.")
else:
    print(informe)
    print(f"\nLa prueba termino con observaciones. Carpeta conservada: {carpeta}")
