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
import re as _re
from estudio import SIN_METADATOS, metadatos_personales
def _comandos_ffmpeg(texto):
    """Cada lista [FFMPEG, ...] del código, completa (respeta corchetes y paréntesis anidados)."""
    for m in _re.finditer(r'\[\s*(?:str\()?\s*(?:FFMPEG|ffmpeg)\s*\)?\s*,', texto):
        d = 0
        for j in range(m.start(), len(texto)):
            if texto[j] in "[({":
                d += 1
            elif texto[j] in "])}":
                d -= 1
                if d == 0:
                    yield m.start(), texto[m.start():j + 1]
                    break


_sin = []
def _ultimo(c):
    """Texto del último elemento de primer nivel de una lista (el archivo de salida en un comando ffmpeg)."""
    d, q, ult = 0, None, 0
    for k, ch in enumerate(c):
        if q:
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
        elif ch in "[({":
            d += 1
        elif ch in "])}":
            d -= 1
        elif ch == "," and d == 1:
            ult = k
    return c[ult + 1:-1].strip()


for _q in sorted(AQUI.glob("*.py")):
    if _q.name in ("prueba.py", "prueba_camara.py"):   # archivos de ensayo con metadatos a propósito
        continue
    _s = _q.read_text(encoding="utf-8")
    for _i, _c in _comandos_ffmpeg(_s):
        _plano = " ".join(_c.split())
        _sigue = _s[_i + len(_c):_i + len(_c) + 4].strip()
        _asignada = _s[max(0, _i - 4):_i].rstrip().endswith("=")      # cmd = [...]: la salida se agrega después
        if _ultimo(_c) == "*SIN_METADATOS" and not _sigue.startswith("+") and not _asignada:
            _sin.append(f"{_q.name}:{_s.count(chr(10), 0, _i) + 1} (la lista va DESPUÉS de la salida: ffmpeg la ignora)")
            continue
        if _q.name == "color.py" and _plano == '[FFMPEG, "-v", "error", "-y"]':   # fotograma(): solo imágenes de muestra
            continue
        if ("SIN_METADATOS" in _c or "salida_cod(" in _c or '"-f", "null"' in _plano or '"image2pipe"' in _c
                or _plano.rstrip("]").rstrip().endswith('"-"') or _re.search(r'"-frames:v", "?1"?[,\]]', _plano)):   # un fotograma = imagen
            continue
        _sin.append(f"{_q.name}:{_s.count(chr(10), 0, _i) + 1}")
assert _ultimo('[FFMPEG, "-i", a, salida, *SIN_METADATOS]') == "*SIN_METADATOS" and _ultimo('[FFMPEG, "-i", a, *SIN_METADATOS, salida]') == "salida", "el escáner debía ver dónde va la lista"
assert not _sin, f"comandos ffmpeg que escriben un archivo sin SIN_METADATOS (llevarían GPS o el celular del original): {_sin}"
_gps = tmp / "con_gps.mp4"; _limpio = tmp / "limpio.mp4"
subprocess.run([str(FFMPEG), "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=d=0.5:s=160x120", "-metadata", "location=+33.4489-070.6693/",
                "-metadata", "model=Celular de prueba", "-metadata:s:v", "creation_time=2026-01-01T10:00:00Z", "-pix_fmt", "yuv420p", _gps], check=True)
subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", _gps, "-c", "copy", *SIN_METADATOS, _limpio], check=True)
assert "location" in (metadatos_personales(_gps) or []), f"la prueba debía detectar el GPS: {metadatos_personales(_gps)}"
assert metadatos_personales(_limpio) == [], f"quedaron metadatos personales: {metadatos_personales(_limpio)}"
_iph = tmp / "handler.mp4"
subprocess.run([str(FFMPEG), "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=d=0.5:s=160x120", "-metadata:s:v",
                "handler_name=Core Media Video", "-pix_fmt", "yuv420p", _iph], check=True)
assert any("handler_name" in x for x in (metadatos_personales(_iph) or [])), "un handler_name de celular debía detectarse"
assert metadatos_personales(tmp / "no_existe.mp4") is None, "un archivo ilegible debía quedar como no comprobado"
print("OK   metadatos: todas las salidas los quitan y terminado.py sabe leerlos (GPS, celular, fecha)")
import revisar_idioma as ri
assert ri.sospechosas("BILL $$$") == ["BILL"] and ri.sospechosas("FEES") == ["FEES"]
assert ri.sospechosas("Comisiones que podrían evitarse") == [] and ri.sospechosas("CREENCIAS antes de invertir") == []
assert ri.sospechosas("Un plan basado únicamente") == [] and ri.sospechosas("Sale caro") == []
print("OK   revisar_idioma: reconoce inglés y deja pasar el español")
import vivo
class _PR:
    cfg = {"subtitulos": {"preset": "finanzas"}, "elementos": [
        {"tipo": "icono", "en": "sigue", "icono": "estrella", "pos": [0.87, 0.10]},
        {"tipo": "progreso", "en": "primera", "hasta": "segunda", "actual": 1, "total": 4, "etiqueta": "Paso"},
        {"tipo": "progreso", "en": "segunda", "hasta": "fin", "actual": 2, "total": 4, "etiqueta": "Paso", "tarjeta": True}]}
_pals = [{"word": w, "start": i * 1.0, "end": i * 1.0 + 0.3} for i, w in enumerate("hola la primera y sigue mucho texto aqui la segunda viene y fin".split())]
_v = vivo.Vivo(_PR(), _pals, 1920, 1080)
_ev = _v.elementos()
assert len(_v.ocupado) == 2 and _v.ocupado[0][2][1] == _v.ocupado[1][2][1], "el contador debía quedar en la misma esquina"
assert _v.movidos and _v.movidos[0][1] == "icono", "el ícono debía correrse para no tapar el contador"
_corte = vivo.Vivo(_PR(), _pals, 1080, 1920, vertical=True).elementos(4.5, 8)
assert any(",0:00:00.00," in e for e in _corte), "en un Short que empieza a mitad de bloque el contador debía verse desde el inicio"
assert all(e.split(",")[1] < e.split(",")[2] for e in _ev + _corte), "hay eventos que terminan antes de empezar"
print("OK   progreso: misma esquina, los demás lo evitan y se ve en un Short que empieza a mitad")
class _MapaFalso:      # escena 1: cara a la izquierda · escena 2: cara a la derecha · escena 3: caras en todo el cuadro
    def regiones(self, a, b, maximo=8):
        m = (a + b) / 2
        if m < 4:
            return [((100, 100, 800, 900), 10, "cara")]
        if m < 7:
            return [((1100, 50, 1900, 1000), 10, "cara")]
        return [((0, 0, 1920, 1080), 10, "cara")]
class _PR2:
    cfg = {"subtitulos": {"preset": "finanzas"}, "elementos": [
        {"tipo": "lista", "titulo": "Prueba", "en": "uno", "items": [{"texto": "a", "frase": "uno"}, {"texto": "b", "frase": "dos"}, {"texto": "c", "frase": "tres"}]}]}
    def escenas(self):
        return [{"t0": 0}, {"t0": 4}, {"t0": 7}, {"t0": 10}]
_pals2 = [{"word": w, "start": float(i), "end": i + 0.3} for i, w in enumerate("x uno x x x dos x x tres x x x x".split())]
_v2 = vivo.Vivo(_PR2(), _pals2, 1920, 1080)
_v2.mapa = _MapaFalso()
_ev2 = _v2.elementos()
def _seg(t):
    h, m, s_ = t.split(":"); return int(h) * 3600 + int(m) * 60 + float(s_)
_tarjetas = [(e, _seg(e.split(",")[1]), _seg(e.split(",")[2])) for e in _ev2 if e.startswith("Dialogue: 3,")]
_posiciones = {e.split("\\pos(")[1].split(")")[0] for e, _, _ in _tarjetas}
assert len(_posiciones) == 2, f"la lista debía cambiar de lugar en el corte (posiciones: {_posiciones})"
assert all(b <= 7.01 for _, _, b in _tarjetas), "en la escena sin lugar libre la lista debía ocultarse"
assert any(m[1] == "lista oculta" for m in _v2.movidos), "la escena oculta debía quedar anotada"
assert any(m[1] == "item_sin_mostrar" and m[5] >= 1 for m in _v2.movidos), "el ítem que cae en la escena oculta debía quedar para revisar"
assert all(_seg(e.split(",")[1]) < _seg(e.split(",")[2]) for e in _ev2), "hay eventos que terminan antes de empezar"
_x1 = int(sorted(_tarjetas, key=lambda t: t[1])[0][0].split("\\pos(")[1].split(",")[0])
_x2 = int(sorted(_tarjetas, key=lambda t: t[1])[-1][0].split("\\pos(")[1].split(",")[0])
assert _x1 > 800 and _x2 + round(0.34 * 1920) < 1100, f"la lista debía evitar la cara en cada escena (x {_x1} y {_x2})"
print("OK   lista: cambia de lugar en cada corte para no tapar caras y se oculta si no hay lugar libre")
import caras
_caja = (0, 0, 650, 300)
assert caras.castigo(_caja, [((100, 100, 200, 200), 10, "cabeza")]) < 1 <= caras.tapa(_caja, [((100, 100, 200, 200), 10, "cabeza")]), \
    "tapar entera una cabeza chica debía contar como tapar"
assert caras.tapa(_caja, [((550, 100, 750, 140), 2.0, "texto")]) >= 1 > caras.tapa(_caja, [((600, 100, 800, 140), 2.0, "texto")]), \
    "tapar la mitad de un texto dibujado debía contar como tapar (un cuarto, no)"
class _PR3:
    def __init__(self, el): self.cfg = {"subtitulos": {"preset": "finanzas"}, "elementos": [el]}
    def escenas(self): return [{"t0": 0}, {"t0": 20}]
_pals3 = [{"word": w, "start": float(i), "end": i + 0.3} for i, w in enumerate("x uno dos tres x x x x x x".split())]
_el3 = {"tipo": "lista", "titulo": "Prueba", "pos": "derecha", "en": "uno",
        "items": [{"texto": "a", "frase": "uno"}, {"texto": "b", "frase": "dos"}, {"texto": "c", "frase": "tres"}]}
class _MapaChicas:     # una sola escena llena de cabezas chicas (como tarjetas con el personaje en miniatura)
    def regiones(self, a, b, maximo=8):
        return [((x, y, x + 110, y + 110), 10, "cabeza") for x in range(40, 1900, 230) for y in range(40, 1000, 230)]
_v3 = vivo.Vivo(_PR3(_el3), _pals3, 1920, 1080); _v3.mapa = _MapaChicas()
_ev3 = _v3.elementos()
assert not [e for e in _ev3 if e.startswith("Dialogue: 3,")] and any(m[1] == "lista oculta" for m in _v3.movidos), \
    "una lista de una sola escena sin lugar libre debía ocultarse y quedar anotada"
assert any(m[1] == "lista_entera_oculta" and m[5] >= 1 for m in _v3.movidos), "la lista oculta entera debía quedar para revisar a mano"
assert vivo.Vivo(_PR3({"tipo": "lista", "en": "uno", "items": []}), _pals3, 1920, 1080).elementos() == [], "una lista vacía no debía romper"
_TXT = (1150, 120, 1850, 260)
class _MapaTexto:      # una sola escena con una palabra dibujada arriba a la derecha, donde iría la lista
    def regiones(self, a, b, maximo=8):
        return [(_TXT, 2.0, "texto")]
_v4 = vivo.Vivo(_PR3(_el3), _pals3, 1920, 1080); _v4.mapa = _MapaTexto()
_t4 = [e for e in _v4.elementos() if e.startswith("Dialogue: 3,")]
_x4, _y4 = map(int, _t4[0].split("\\pos(")[1].split(")")[0].split(","))
_c4 = (_x4, _y4, _x4 + round(0.34 * 1920), _y4 + round((110 + 62 * 3) * _v4.esc))
assert _t4 and caras.cruce(_c4, _TXT) == 0, f"la lista debía evitar el texto dibujado (caja {_c4})"
_v5 = vivo.Vivo(_PR(), _pals, 1920, 1080); _v5.elementos()
_esq = _v5.ocupado[0][2]
class _MapaTextoEsquina:   # texto dibujado justo donde va el contador
    def regiones(self, a, b, maximo=8):
        return [(_esq, 2.0, "texto")]
class _PR5(_PR):
    def escenas(self): return [{"t0": 0}]
_v6 = vivo.Vivo(_PR5(), _pals, 1920, 1080); _v6.mapa = _MapaTextoEsquina(); _v6.elementos()
assert all(caras.tapa(o, [(_esq, 2.0, "texto")]) < 1 for _, _, o in _v6.ocupado), "el contador debía dejar libre el texto dibujado"
print("OK   lista y contador: no tapan cabezas chicas ni texto dibujado; lo que se oculta queda para revisar a mano")
import os
_jb = tmp / "juez_base"; (_jb / "tmp").mkdir(parents=True); (_jb / "claves").mkdir()
(_jb / "tmp" / "x.log").write_text('k = "AIza' + "B" * 35 + '"\n', encoding="utf-8")
(_jb / "claves" / "youtube.env").write_text("API=AIza" + "C" * 35 + "\n", encoding="utf-8")
_env = dict(os.environ, ESTUDIO_BASE=str(_jb), PYTHONIOENCODING="cp1252")
_r = subprocess.run([py, "juez.py", "todo"], cwd=AQUI, capture_output=True, text=True, env=_env, encoding="cp1252", errors="replace")
_inf = list((_jb / "trabajo" / "juez").glob("juez_*.md"))
assert _r.returncode == 0 and _inf and "x.log:1" in _inf[0].read_text(encoding="utf-8") \
    and "youtube.env" not in _inf[0].read_text(encoding="utf-8") and "B" * 20 not in _inf[0].read_text(encoding="utf-8"), \
    "el juez debía encontrar la clave del log (tapada) e ignorar la carpeta claves: " + _r.stdout[-300:] + _r.stderr[-500:]
_r2 = subprocess.run([py, "juez.py", "permitir", "abc123"], cwd=AQUI, capture_output=True, text=True, env=_env, encoding="cp1252", errors="replace")
assert _r2.returncode != 0 and not (_jb / "juez" / "permitidos.json").exists(), "permitir debía exigir --por y --motivo"
(_jb / "motor").mkdir()
(_jb / "motor" / "x.py").write_text("import os\nos.remove(p)\nos.remove(p)\n", encoding="utf-8")
subprocess.run([py, "juez.py", "originales", "--salida", str(_jb / "o")], cwd=AQUI, capture_output=True, env=_env)
_ids = [l.split("|")[1].strip() for l in next((_jb / "o").glob("juez_*.md")).read_text(encoding="utf-8").splitlines() if "borra un archivo" in l]
assert len(_ids) == 2 and len(set(_ids)) == 2, f"dos líneas iguales debían tener ids distintos: {_ids}"
print("OK   juez: encuentra claves fuera de claves\\ (tapadas), no pisa informes, no acepta hallazgos sin el sí de alguien y separa líneas repetidas")
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
paso("vertical.py", str(carpeta))
if not list((carpeta / "07_RENDER").glob("*_9x16_anterior-*.mp4")):
    sys.exit(f"vertical.py pisó el Short anterior en vez de guardarlo. Carpeta conservada: {carpeta}")
print("OK   vertical.py no pisa el Short anterior: queda como *_anterior-<fecha>")
import estudio as _es
_pr = _es.Proyecto(carpeta)
_voces = _pr.audios()
_dv = _voces[0].parent
(_dv / ("x_anterior-20261108-000000" + _voces[0].suffix)).write_bytes(_voces[0].read_bytes())
(_dv / ("x.parcial" + _voces[0].suffix)).write_bytes(b"0")
if _pr.audios() != _voces:
    sys.exit(f"audios() tomó una voz guardada o a medias como parte de la narración: {_pr.audios()}")
(_dv / ("x_anterior-20261108-000000" + _voces[0].suffix)).unlink(); (_dv / ("x.parcial" + _voces[0].suffix)).unlink()
_t = carpeta / "07_RENDER" / "entrega.srt"
_es.escribir_entrega(_t, "uno"); _es.escribir_entrega(_t, "uno"); _es.escribir_entrega(_t, "dos")
if _t.read_text(encoding="utf-8") != "dos" or len(list(_t.parent.glob("entrega_anterior-*.srt"))) != 1:
    sys.exit("escribir_entrega debía guardar el .srt anterior una sola vez y no tocarlo si no cambia")
for _f in [_t, *_t.parent.glob("entrega_anterior-*.srt")]:
    _f.unlink()
print("OK   las voces guardadas o a medias no entran en la narración, y el .srt anterior queda guardado")
paso("terminado.py", str(carpeta))
_dis = carpeta / "08_PUBLICAR"; _dis.mkdir(exist_ok=True)
_mini = _dis / "mini.png"
subprocess.run([py, "diseno.py", "plantilla", "miniatura-centro", "--campo", "titulo=UNO", "--campo", f"imagen={carpeta / '03_IMAGENES' / 'img_1.png'}", "--salida", str(_mini)], cwd=AQUI, capture_output=True)
_h1 = _mini.read_bytes() if _mini.exists() else b""
subprocess.run([py, "diseno.py", "plantilla", "miniatura-centro", "--campo", "titulo=DOS", "--campo", f"imagen={carpeta / '03_IMAGENES' / 'img_1.png'}", "--salida", str(_mini)], cwd=AQUI, capture_output=True)
if not _h1 or _mini.read_bytes() != _h1 or not (_dis / "mini_2.png").exists():
    sys.exit("diseno.py debía dejar la miniatura elegida intacta y guardar la nueva como mini_2.png")
print("OK   diseno.py no pisa una miniatura ya hecha (la nueva va como _2)")
_extra = carpeta / "07_RENDER" / "VideoPrueba_v1_extra.mp4"          # una entrega con GPS: el punto 11 debe atraparla
subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", carpeta / "07_RENDER" / "VideoPrueba_v1_youtube.mp4", "-c", "copy",
                "-metadata", "location=+33.4489-070.6693/", _extra], check=True)
_r11 = subprocess.run([py, "terminado.py", str(carpeta)], cwd=AQUI, capture_output=True, text=True, encoding="utf-8", errors="replace")
_extra.unlink()
if _r11.returncode == 0 or "| 11 |" not in _r11.stdout or "location" not in _r11.stdout:
    sys.exit("terminado.py debía rechazar (punto 11) un video de la versión con GPS:\n" + _r11.stdout[-800:])
print("OK   terminado.py punto 11 rechaza una entrega con GPS")
paso("terminado.py", str(carpeta))
_rc = subprocess.run([py, "prueba_camara.py", str(AQUI)], cwd=AQUI, capture_output=True, text=True, encoding="utf-8", errors="replace")
if _rc.returncode:
    sys.exit("prueba_camara.py (grabado, montaje y doblaje con tomas con GPS) falló:\n" + _rc.stdout[-1500:] + _rc.stderr[-800:])
print("OK   cámara: grabado, montaje_tomas y doblaje salen sin GPS ni datos del celular", flush=True)
informe = paso("revisar.py", str(carpeta))
if "0 puntos a revisar" in informe:
    shutil.rmtree(carpeta.parent, ignore_errors=True)
    print("\nPRUEBA SUPERADA: el estudio funciona en este computador.")
else:
    print(informe)
    print(f"\nLa prueba termino con observaciones. Carpeta conservada: {carpeta}")
