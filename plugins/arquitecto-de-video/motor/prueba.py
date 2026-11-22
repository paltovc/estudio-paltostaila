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
from estudio import ataque_y_pico, huella
import hashlib as _hl
_son = tmp / "con_silencio.wav"       # 0,25 s de silencio, un tono que sube y su punto más fuerte en 0,65 s
subprocess.run([str(FFMPEG), "-v", "error", "-y", "-f", "lavfi", "-i",
                "aevalsrc='if(lt(t,0.25),0,sin(2*PI*880*t)*min(1,(t-0.25)/0.4)*if(lt(t,0.65),1,0.2))':d=1:s=48000", *SIN_METADATOS, _son], check=True)
_at, _pi = ataque_y_pico(_son)
assert 0.22 <= _at <= 0.30 and 0.60 <= _pi <= 0.68, f"ataque y pico mal medidos: {_at}, {_pi}"
assert ataque_y_pico(tmp / "no_existe.wav") == (0.0, 0.0), "un sonido ilegible debía dar (0, 0), no romper"
assert huella(_son) == _hl.sha256(_son.read_bytes()).hexdigest()
print("OK   sonidos: mide cuándo empieza a oírse un efecto y dónde está su punto más fuerte; huella sha256")
import revisar_idioma as ri
assert ri.sospechosas("BILL $$$") == ["BILL"] and ri.sospechosas("FEES") == ["FEES"]
assert ri.sospechosas("Comisiones que podrían evitarse") == [] and ri.sospechosas("CREENCIAS antes de invertir") == []
assert ri.sospechosas("Un plan basado únicamente") == [] and ri.sospechosas("Sale caro") == []
print("OK   revisar_idioma: reconoce inglés y deja pasar el español")
# 0.15: idioma destino en o pt
assert ri.sospechosas("Your monthly budget", "en") == [] and ri.sospechosas("Tu presupuesto del mes", "en") == ["del", "mes"], \
    ri.sospechosas("Tu presupuesto del mes", "en")
assert "Você" in ri.sospechosas("Você pode poupar", "en") and ri.sospechosas("Poupança do mês", "pt") == []
assert ri.sospechosas("BILLS do mês", "pt") == ["BILLS"] and "dinero" in ri.sospechosas("Ahorra dinero", "pt")
assert ri.sospechosas("Educação financeira", "es") == ["Educação"], ri.sospechosas("Educação financeira", "es")
print("OK   revisar_idioma 0.15: destino inglés o portugués, y portugués claro dentro de un video en español")
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
cfg["sonidos"] = dict(cfg.get("sonidos") or {}, efectos=[                # un proyecto nuevo ya nace con alinear = "ataque"
    {"segundo": 2.0, "archivo": "bip_prueba.wav", "duracion": 0.6},      # 2,0 s cae en medio de una palabra (1,9 a 2,25)
    {"frase": "Gracias", "archivo": "bip_prueba.wav", "duracion": 0.6},  # anclado a una frase: no se baja
    {"segundo": 9.0, "archivo": "pico_prueba.wav", "alinear": "pico", "duracion": 0.3}])   # pico a 1,5 s: duracion se alarga
(carpeta / "05_SONIDOS").mkdir(exist_ok=True)
subprocess.run([str(FFMPEG), "-v", "error", "-y", "-f", "lavfi", "-i", "aevalsrc='if(lt(t,0.25),0,sin(2*PI*880*t))':d=0.8:s=48000",
                "-map_metadata", "-1", carpeta / "05_SONIDOS" / "bip_prueba.wav"], check=True)
subprocess.run([str(FFMPEG), "-v", "error", "-y", "-f", "lavfi", "-i", "aevalsrc='0.05*sin(2*PI*300*t)+if(between(t,1.5,1.52),0.9,0)':d=2:s=48000",
                "-map_metadata", "-1", carpeta / "05_SONIDOS" / "pico_prueba.wav"], check=True)
assert cfg["sonidos"].get("alinear") == "ataque", "un proyecto nuevo debía nacer con los efectos alineados por ataque"
import estudio as _es0
assert _es0.DEFAULTS["sonidos"]["alinear"] == "inicio" and _es0.DEFAULTS["sonidos"]["baja_sobre_voz"] == 0, \
    "un proyecto que ya existía no puede cambiar de sonido al volver a armarse"
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
_cues = [q for q in (carpeta / "06_RECETA").glob("hoja_cues_*.csv") if "_anterior-" not in q.name]
import csv as _csv
_filas = list(_csv.reader(_cues[0].read_text(encoding="utf-8-sig").splitlines(), delimiter=";")) if _cues else []
_ef = carpeta / "07_RENDER" / "tmp" / "efectos.wav"
if len(_filas) != 5 or any(len(x) != 7 for x in _filas):
    sys.exit(f"la hoja de cues debía tener el encabezado y 4 sonidos, todos con 7 columnas: {_filas}. Carpeta conservada: {carpeta}")
_bip = [x for x in _filas if x[2] == "bip_prueba.wav"]
if not ("ataque (-0,25" in _bip[0][4].replace(".", ",") and "en medio de una palabra" in _bip[0][4] and _bip[0][3] == "-22"
        and "palabra" not in _bip[1][4] and _bip[1][3] == "-19" and all(x[6] == "revisar (anotar en licencias\\registro.md)" for x in _bip)):
    sys.exit(f"sonidos.py: solo el efecto puesto por segundo en medio de una palabra debía bajar 3 dB: {_bip}. Carpeta conservada: {carpeta}")
def _nivel(a, b):       # volumen medio de un tramo de la capa de efectos
    r = subprocess.run([str(FFMPEG), "-hide_banner", "-ss", str(a), "-t", str(b - a), "-i", str(_ef), "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    import re as _r2
    m = _r2.findall(r"max_volume: (-?[\d.]+) dB", r.stderr)
    return float(m[-1]) if m else None
_a2, _ = ataque_y_pico(_ef)
if not 1.97 <= _a2 <= 2.04:
    sys.exit(f"el efecto debía empezar a oírse en 2,0 s (sin el silencio del archivo) y se oye en {_a2}. Carpeta conservada: {carpeta}")
_n1, _n2 = _nivel(2.05, 2.4), _nivel(_es0.buscar(_es0.palabras(_es0.Proyecto(carpeta))[1], "Gracias") + 0.05, _es0.buscar(_es0.palabras(_es0.Proyecto(carpeta))[1], "Gracias") + 0.4)
if _n1 is None or _n2 is None or not 2.0 <= _n2 - _n1 <= 4.0:
    sys.exit(f"el efecto en medio de una palabra debía sonar unos 3 dB más bajo que el anclado a una frase ({_n1} y {_n2} dB)")
_p1, _p2 = _nivel(8.9, 9.1), _nivel(8.0, 8.8)
if _p1 is None or _p2 is None or _p1 - _p2 < 6:
    sys.exit(f"en modo pico, el punto más fuerte debía caer en 9,0 s ({_p1} dB ahí y {_p2} dB antes)")
print("OK   sonidos.py: ataque y pico caen en su momento (medido en el audio), solo baja lo que cae en medio de una palabra, y la hoja de cues sale con sus 7 columnas")
_cfg2 = json.loads((carpeta / "proyecto.json").read_text(encoding="utf-8")); _ef_guardados = _cfg2["sonidos"]["efectos"]
_cfg2["sonidos"]["efectos"] = []; _cfg2["escenas_capitulo"] = []
(carpeta / "proyecto.json").write_text(json.dumps(_cfg2, ensure_ascii=False, indent=2), encoding="utf-8")
paso("sonidos.py", str(carpeta))
if [q for q in (carpeta / "06_RECETA").glob("hoja_cues_*.csv") if "_anterior-" not in q.name] or not list((carpeta / "06_RECETA").glob("hoja_cues_*_anterior-*.csv")):
    sys.exit("sin efectos, la hoja de cues anterior debía quedar guardada como _anterior y no como vigente")
_cfg2["sonidos"]["efectos"] = _ef_guardados; _cfg2["escenas_capitulo"] = [2]
(carpeta / "proyecto.json").write_text(json.dumps(_cfg2, ensure_ascii=False, indent=2), encoding="utf-8")
paso("sonidos.py", str(carpeta))
print("OK   sonidos.py: sin efectos, la hoja de cues vieja se retira (queda guardada)")
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
_fin = paso("terminado.py", str(carpeta))
import re as _re13
if not _re13.search(r"\| 13 \|.*\| ✓ \| máximo -?\d+(\.\d+)? dBTP en \d+ videos \|", _fin):
    sys.exit("terminado.py debía medir el pico real (punto 13):\n" + _fin[-600:])
print("OK   terminado.py mide el pico real (punto 13, recomendado)")
# corrección B1 (juicio 0.15): --solo-audio sobre finales sin sello (anteriores al 0.15) no deja un sello sin origen,
# y un sello sin origen ya escrito cuenta como «sin sello» (punto 14 recomendado, no bloquea)
_og = carpeta / "07_RENDER" / "VideoPrueba_v1_origen.json"
if _og.exists():
    _og.unlink()
paso("terminar.py", str(carpeta), "--solo-audio")
if _og.exists():
    sys.exit(f"terminar.py --solo-audio sin sello previo no debía escribir un sello sin origen. Carpeta conservada: {carpeta}")
_og.write_text(json.dumps({"base": "VideoPrueba_v1", "modo": "solo-audio", "solo_video": None, "narracion": None,
                           "finales": {}}), encoding="utf-8")
_f14 = paso("terminado.py", str(carpeta))          # paso() se detiene si terminado.py no firma
if "| 14 | Los dos finales salen del mismo armado (sello de terminar.py) (recomendado) |" not in _f14:
    sys.exit("terminado.py debía tratar un sello sin origen como recomendado (punto 14):\n" + _f14[-600:])
_og.unlink()
paso("terminado.py", str(carpeta))
print("OK   terminar.py --solo-audio sin sello previo no bloquea el punto 14 de terminado.py")
# corrección M3 (juicio 0.15): el tipo de video no baja el peso de «riesgos» bajo el de siempre (se lee de evaluar.py sin
# correrlo: evaluar.py arma el proyecto al importarlo)
import ast as _ast
_src_ev = (AQUI / "evaluar.py").read_text(encoding="utf-8")
_ns = {}
for _nodo in _ast.parse(_src_ev).body:
    if (isinstance(_nodo, _ast.Assign) and any(getattr(t, "id", "") in ("PESOS_POR_TIPO", "PISO_RIESGOS") for t in _nodo.targets)) \
            or (isinstance(_nodo, _ast.FunctionDef) and _nodo.name == "pesos_de_tipo"):
        exec(compile(_ast.Module([_nodo], []), "evaluar.py", "exec"), _ns)
for _tv in _ns["PESOS_POR_TIPO"]:
    _t, _pw, _decl, _piso, _ = _ns["pesos_de_tipo"](_tv)
    if _pw["riesgos"] < _ns["PISO_RIESGOS"] or abs(sum(_pw.values()) - 1) > 0.01:
        sys.exit(f"evaluar.py: con tipo_video «{_tv}» el peso de riesgos quedó bajo el piso o los pesos no suman 1: {_pw}")
if _ns["pesos_de_tipo"](None)[1] != _ns["PESOS_POR_TIPO"]["narrado"] or _ns["pesos_de_tipo"](None)[2]:
    sys.exit("evaluar.py: sin tipo_video los pesos tenían que ser exactamente los de siempre")
print("OK   evaluar.py: el tipo de video no baja el peso de riesgos (piso) y sin tipo_video nada cambia")
_f1 = paso("ficha.py", str(carpeta))
_fj = json.loads((carpeta / "ficha.json").read_text(encoding="utf-8"))
if (_fj["estado"] != "armado, con pendientes" or "la evaluación" not in _fj["falta"] or not _fj["terminado"]["si"]
        or _fj["terminado"]["vigente"] is not True or _fj.get("hecha_por") != "ficha.py" or "(actualizada)" not in _f1):
    sys.exit(f"ficha.py debía leer el estado del video de sus archivos: {_fj}")
if "(sin cambios)" not in paso("ficha.py", str(carpeta)):
    sys.exit("ficha.py debía dejar la ficha intacta si nada cambió")
import ficha as _fi, hashlib as _h2
_cs = carpeta / "07_RENDER" / "VideoPrueba_v1_con-subtitulos.mp4"
_evp = carpeta / "06_RECETA" / "evaluacion_VideoPrueba_v1_con-subtitulos.json"
_pj = json.loads((carpeta / "proyecto.json").read_text(encoding="utf-8")); _pj["titulo"] = "Título de prueba"
(carpeta / "proyecto.json").write_text(json.dumps(_pj, ensure_ascii=False, indent=2), encoding="utf-8")
(carpeta / "08_PUBLICAR" / "x_miniatura_1.png").write_bytes(b"png")
def _ev(nota, clase, sha=True, texto=None):
    _evp.write_text(texto if texto is not None else json.dumps({"nota_medida": nota, "clase_medida": clase,
                    **({"sha256": _h2.sha256(_cs.read_bytes()).hexdigest()} if sha else {})}), encoding="utf-8")
    return _fi.ficha(carpeta)
_r = _ev(8.4, "A")
assert _r["estado"] == "listo para aprobar" and not _r["falta"], f"con todo comprobado debía quedar listo: {_r['falta']}"
assert _ev(3.1, "C")["estado"] != "listo para aprobar", "una nota 3,1 clase C no puede quedar «listo para aprobar»"
assert _ev(8.4, "A", sha=False)["estado"] != "listo para aprobar", "una evaluación sin huella no cuenta como comprobada"
assert _ev(0, "", texto="{rota")["estado"] != "listo para aprobar", "una evaluación ilegible no cuenta como comprobada"
assert _ev(0, "", texto="[1, 2]")["estado"] != "listo para aprobar", "una evaluación que no es un objeto no cuenta"
_ev(8.4, "A")
_yt0 = carpeta / "07_RENDER" / "VideoPrueba_v1_youtube.mp4"; _b0 = _yt0.read_bytes()
_yt0.write_bytes(_b0 + b"0")
_r = _fi.ficha(carpeta)
assert _r["estado"] != "listo para aprobar" and any("cambió después de terminado" in x for x in _r["falta"]), \
    f"si el video cambia después de terminado.py, la ficha no puede decir listo: {_r['falta']}"
_yt0.write_bytes(_b0)
assert _fi.ficha(carpeta)["estado"] == "listo para aprobar"
_evp.unlink(); (carpeta / "08_PUBLICAR" / "x_miniatura_1.png").unlink()
_aj = carpeta / "ficha.json"; _mio = _aj.read_text(encoding="utf-8")
_aj.write_text('{"personaje": "ficha ajena"}', encoding="utf-8")
_env2 = dict(os.environ, ESTUDIO_BASE=str(carpeta.parent / "base_fichas"), PYTHONIOENCODING="cp1252")
_r3 = subprocess.run([py, "ficha.py", str(carpeta)], cwd=AQUI, capture_output=True, text=True, env=_env2, encoding="cp1252", errors="replace")
assert _r3.returncode == 0 and _aj.read_text(encoding="utf-8") == '{"personaje": "ficha ajena"}' \
    and list((carpeta.parent / "base_fichas" / "trabajo" / "fichas").glob("ficha_*.json")), \
    "un ficha.json que no es del estudio no se toca: la ficha debía ir a trabajo\\fichas\n" + _r3.stdout[-400:] + _r3.stderr[-400:]
_aj.write_text("esto no es json", encoding="utf-8")
subprocess.run([py, "ficha.py", str(carpeta)], cwd=AQUI, capture_output=True, env=_env2)
assert _aj.read_text(encoding="utf-8") == "esto no es json", "un ficha.json ilegible tampoco se toca"
_aj.write_text(_mio, encoding="utf-8")
(carpeta.parent / "base_fichas" / "proyectos" / "c").mkdir(parents=True)
shutil.copytree(carpeta, carpeta.parent / "base_fichas" / "proyectos" / "c" / "VideoPrueba")
_r4 = subprocess.run([py, "ficha.py", "tabla"], cwd=AQUI, capture_output=True, text=True, env=_env2, encoding="cp1252", errors="replace")
assert _r4.returncode == 0 and "VideoPrueba" in _r4.stdout and list((carpeta.parent / "base_fichas" / "trabajo" / "fichas").glob("tabla_*.md")), \
    "ficha.py tabla debía funcionar con salida cp1252 y dejar la tabla:\n" + _r4.stdout[-300:] + _r4.stderr[-500:]
print("OK   ficha.py: «listo para aprobar» solo con todo comprobado; no pisa un ficha.json ajeno; la tabla sale en cp1252")
# 0.16: equipo.py (qué video local puede correr este computador), regla de resolución y mensaje de bienvenida
import os
_eb = Path(tempfile.mkdtemp(prefix="prueba_equipo_"))
def _equipo(sim, *args):
    e = dict(os.environ, ESTUDIO_BASE=str(_eb), ESTUDIO_SIN_VENTANA="1", PYTHONIOENCODING="utf-8",
             ESTUDIO_EQUIPO_SIMULADO=json.dumps(sim))
    r = subprocess.run([py, "equipo.py", *args], cwd=AQUI, capture_output=True, text=True, env=e, encoding="utf-8", errors="replace")
    assert r.returncode == 0, "equipo.py falló:\n" + r.stdout[-400:] + r.stderr[-800:]
    return r.stdout
_j = json.loads(_equipo({"nvidia": [["NVIDIA GeForce RTX 3060", 12288]], "graficas": ["NVIDIA GeForce RTX 3060"]}, "--json"))
assert _j["ruta"] == "nvidia_wangp" and _j["resolucion_local"] == "720p" and _j["imagen_a_video"], _j
_j = json.loads(_equipo({"nvidia": [["NVIDIA GeForce GTX 1660", 6144]], "graficas": ["NVIDIA GeForce GTX 1660"]}, "--json"))
assert _j["ruta"] == "nvidia_wangp" and _j["resolucion_local"] == "480p", _j
_j = json.loads(_equipo({"nvidia": [["NVIDIA GeForce GT 1030", 2048]], "graficas": ["NVIDIA GeForce GT 1030"]}, "--json"))
assert _j["ruta"] == "ninguna" and "no alcanza" in _j["mensaje"] and "puerta" in _j["mensaje"], _j
_j = json.loads(_equipo({"nvidia": [], "graficas": ["Intel(R) Iris(R) Xe Graphics"]}, "--json"))
assert _j["ruta"] == "ninguna" and "no tiene tarjeta NVIDIA" in _j["mensaje"], _j
_j = json.loads(_equipo({"nvidia": [["NVIDIA GeForce RTX 4060 Laptop GPU", 8188, 8.9]], "graficas": ["NVIDIA GeForce RTX 4060 Laptop GPU"]}, "--json"))
assert _j["ruta"] == "nvidia_wangp" and _j["resolucion_local"] == "720p" and "(8 GB)" in _j["mensaje"], _j
_j = json.loads(_equipo({"nvidia": [["NVIDIA GeForce GTX 1070", 8192, 6.1]], "graficas": ["NVIDIA GeForce GTX 1070"]}, "--json"))
assert _j["ruta"] == "ninguna" and "antigua" in _j["mensaje"], _j
_j = json.loads(_equipo({"nvidia": [["NVIDIA GeForce GT 710", None]], "graficas": ["NVIDIA GeForce GT 710"]}, "--json"))
assert _j["ruta"] == "ninguna" and "no se pudo leer" in _j["mensaje"], _j
_j = json.loads(_equipo({"nvidia": [["NVIDIA GeForce GT 1030", 2048], ["NVIDIA RTX A6000", 49152]], "graficas": []}, "--json"))
assert _j["ruta"] == "ninguna", _j   # WanGP usa la GPU 0
(_eb / "video_local").mkdir()
(_eb / "video_local" / "s4_resultado.json").write_text(json.dumps({"usable": True, "resolucion": "512x288"}), encoding="utf-8-sig")   # con BOM, como PowerShell
_j = json.loads(_equipo({"nvidia": [], "graficas": ["Intel(R) Iris(R) Xe Graphics"]}, "--json"))
assert _j["ruta"] == "intel_experimental" and not _j["imagen_a_video"], _j
assert _equipo({}, "resolucion", "1080p", "720p").strip() == "720p" and _equipo({}, "resolucion", "1080p", "1080p").strip() == "1080p"
assert _equipo({"nvidia": [], "graficas": ["Intel(R) Iris(R) Xe Graphics"]}, "ruta").strip() == "intel_experimental"
_b1 = _equipo({}, "bienvenida"); _b2 = _equipo({}, "bienvenida")
assert "dejó la puerta abierta" in _b1 and "dejó la puerta abierta" not in _b2 and (_eb / "video_local" / ".bienvenida_vista").exists(), (_b1, _b2)
shutil.rmtree(_eb, ignore_errors=True)
print("OK   equipo.py: NVIDIA 12 GB y 8188 MiB → WanGP 720p, 6 GB → 480p; 2 GB, GTX 10xx, memoria ilegible, GPU 0 chica o Intel → puerta abierta; BOM; resolución única por video; bienvenida una sola vez")
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
