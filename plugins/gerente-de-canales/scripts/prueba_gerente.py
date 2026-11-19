# Prueba del gerente sin red ni cuentas: arma un proyecto falso (ruta con espacios y tildes) en una carpeta temporal
# y revisa validación, puertas, aprobación con huella, calendario, cupo, hoja manual, reservas, y subidas con un
# YouTube de mentira (copias verificadas, candado, fecha al final, envíos inciertos, otro canal), revocación,
# cancelación, desprogramar y progreso. Los subprocesos corren con salida cp1252, como un log en Windows.
#   python prueba_gerente.py      → debe terminar en «PRUEBA SUPERADA»
import datetime as dt, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TMPD = Path(tempfile.mkdtemp(prefix="gerente_prueba_"))
os.environ["ESTUDIO_BASE"] = str(TMPD / "EstudioPaltostaila")
sys.path.insert(0, str(AQUI))
fallas = []


def check(nombre, cond, extra=""):
    print(("OK   " if cond else "FALLA") + " " + nombre + (f" · {str(extra)[-700:]}" if extra and not cond else ""), flush=True)
    if not cond:
        fallas.append(nombre)


def correr(*args):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"  # como cuando la salida va a un log en Windows
    r = subprocess.run([sys.executable, *map(str, args)], cwd=AQUI, capture_output=True, env=env)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


def escribir_pub(d):
    (P / "08_PUBLICAR" / "publicacion.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def huellas_tabla():
    c, out = correr("aprobar.py", P, "--tabla")
    return dict(re.findall(r"## (\w+) \(\w+\) · huella \*\*(\w{8})\*\*", out)), out


def aprobar(*claves):
    H, _ = huellas_tabla()
    return correr("aprobar.py", P, "--por", "Patricio (prueba)", "--huellas", ",".join(f"{c}:{H[c]}" for c in claves))


# --- proyecto falso
P = TMPD / "Images video 2" / "Producción FIN-900"
for d in ("07_RENDER_ESTUDIO", "06_RECETA", "08_PUBLICAR"):
    (P / d).mkdir(parents=True)
R7 = P / "07_RENDER_ESTUDIO"
(R7 / "FIN-900_v1_youtube.mp4").write_bytes(b"video largo de prueba" * 100)
(R7 / "FIN-900_v1_short1_9x16.mp4").write_bytes(b"short de prueba" * 50)
(R7 / "FIN-900_v1_subtitulos.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nHola\n", encoding="utf-8")
(P / "08_PUBLICAR" / "FIN-900_miniatura_1.png").write_bytes(b"\x89PNG" + b"0" * 100)
CHK = P / "08_PUBLICAR" / "checklist_publicacion_monetizacion_v1.md"
CHK.write_text("# checklist v1\n7 respuestas revisadas\n\nMONETIZACIÓN: OK\n", encoding="utf-8")
TERM = R7 / "terminado_FIN-900_v1.md"
TERM_OK = ("# ¿Terminado? FIN-900_v1\n\n**SÍ: lo obligatorio pasa**\n\n| # | punto | | detalle |\n|---|---|---|---|\n"
           + "".join(f"| {n} | punto {n} | ✓ | |\n" for n in range(1, 7)) + "| 7 | Evaluación (recomendado) | – | |\n"
           + "| 11 | Sin metadatos personales (GPS, celular, fecha) | ✓ | |\n")
time.sleep(0.05)
TERM.write_text(TERM_OK, encoding="utf-8")
EV = P / "06_RECETA" / "evaluacion_FIN-900_v1_con-subtitulos.json"
CS = R7 / "FIN-900_v1_con-subtitulos.mp4"
CS.write_bytes(b"con subtitulos" * 80)
TERMJ = R7 / "terminado_FIN-900_v1.json"
EVS = P / "06_RECETA" / "evaluacion_FIN-900_v1_short1_9x16.json"
SHORT = R7 / "FIN-900_v1_short1_9x16.mp4"


import hashlib


def _h(q):
    return hashlib.sha256(Path(q).read_bytes()).hexdigest()


def sellar():       # lo que deja terminado.py del motor 0.14: la huella de cada video que revisó
    TERMJ.write_text(json.dumps({"base": "FIN-900_v1", "ok": True,
                                 "videos": {q.name: _h(q) for q in sorted(R7.glob("*.mp4"))}}), encoding="utf-8")


def evaluar_falso(nota=8.2, clase="A", nota_short=7.2):     # lo que deja evaluar.py del motor 0.14: nota y huella del video evaluado
    EV.write_text(json.dumps({"video": str(CS), "sha256": _h(CS), "nota_medida": nota, "clase_medida": clase}), encoding="utf-8")
    EVS.write_text(json.dumps({"video": SHORT.name, "sha256": _h(SHORT), "nota_medida": nota_short, "clase_medida": "B"}), encoding="utf-8")


sellar()
evaluar_falso()
manana = (dt.datetime.now() + dt.timedelta(days=2)).strftime("%Y-%m-%dT19:00")
pasado = (dt.datetime.now() + dt.timedelta(days=3)).strftime("%Y-%m-%dT19:00")
PUB = {"id": "FIN-900", "version": "v1", "canal": "finanzas", "piezas": [
    {"clave": "largo", "archivo": "07_RENDER_ESTUDIO/FIN-900_v1_youtube.mp4", "tipo": "largo", "titulo": "Prueba del gerente",
     "descripcion": "Descripción de prueba. No es asesoría financiera. " + "x" * 300, "etiquetas": ["finanzas", "ahorro"],
     "miniatura": "08_PUBLICAR/FIN-900_miniatura_1.png", "subtitulos": "07_RENDER_ESTUDIO/FIN-900_v1_subtitulos.srt",
     "para_ninos": False, "ia_realista": False,
     "destinos": [{"red": "youtube", "ruta": "api", "fecha": manana, "zona": "America/Santiago"}]},
    {"clave": "short1", "archivo": "07_RENDER_ESTUDIO/FIN-900_v1_short1_9x16.mp4", "tipo": "short", "titulo": "Short de prueba #shorts",
     "texto": "Texto del short #ahorro", "texto_instagram": "TEXTO PROPIO DE INSTAGRAM " + "y" * 200, "para_ninos": False, "ia_realista": False,
     "destinos": [{"red": "youtube", "ruta": "api", "fecha": manana, "zona": "America/Santiago"},
                  {"red": "tiktok", "ruta": "metricool", "fecha": pasado, "zona": "America/Santiago",
                   "enlace_publico": "https://ejemplo.invalid/short1.mp4"},
                  {"red": "instagram", "ruta": "manual", "fecha": pasado, "zona": "America/Santiago"}]}]}
escribir_pub(PUB)

import comun
cfg = comun.config()
cfg["youtube"]["canal_id"] = "UC_CANAL_BUENO"
comun.escribir_estado(comun.CONFIG, cfg)

# --- validar
c, out = correr("validar.py", P)
check("validar acepta un publicacion.json correcto (ruta con espacios y tildes, salida cp1252)", c == 0, out)
malo = json.loads(json.dumps(PUB))
malo["piezas"][0]["titulo"] = "x" * 120
malo["piezas"][1]["destinos"][1]["ruta"] = "api"
malo["piezas"][1]["archivo"] = "../../fuera.mp4"
malo["piezas"][1]["destinos"][2]["fecha"] = manana + "+00:00"
escribir_pub(malo)
c, out = correr("validar.py", P)
check("validar rechaza título largo, ruta api en TikTok, archivo fuera del proyecto y fecha con desfase",
      c == 1 and "100" in out and "no sirve para tiktok" in out and "dentro del proyecto" in out and "desfase" in out, out)
malo = json.loads(json.dumps(PUB)); malo["piezas"][1]["destinos"][2]["fecha"] = "2026-09-06T00:30"
escribir_pub(malo)
c, out = correr("validar.py", P)
check("validar rechaza una hora que no existe por el cambio de hora", c == 1 and "no existe" in out, out)
escribir_pub(PUB)

# --- puertas y aprobación
c, out = correr("puertas.py", P, "--pieza", "largo")
check("puertas cerradas sin aprobación", c == 1 and "sin aprobación" in out, out)
c, out = correr("puertas.py", P, "--pieza", "Largo")
check("puertas cerradas si la pieza no existe", c == 1 and "no está en publicacion.json" in out, out)
c, out = correr("puertas.py", P, "--pieza", "largo", "--red", "instagram")
check("puertas cerradas si la pieza no va a esa red", c == 1 and "no va a instagram" in out, out)
c, out = correr("aprobar.py", P, "--por", "Patricio")
check("aprobar exige las huellas de la tabla", c != 0 and "--huellas" in out, out)
H, out = huellas_tabla()
check("la tabla muestra huella, horas de Sídney/Auckland, la descripción completa y el texto propio de Instagram",
      set(H) == {"largo", "short1"} and "Sydney" in out and "Auckland" in out and "x" * 300 in out
      and "TEXTO PROPIO DE INSTAGRAM " + "y" * 200 in out and "UC_CANAL_BUENO" in out, out)
for mala in ("largo:", "largo:a", "largo:00000000"):
    c, out = correr("aprobar.py", P, "--por", "Patricio", "--huellas", mala)
    check(f"aprobar rechaza la huella {mala!r}", c != 0 and ("inválida" in out or "cambió" in out), out)
c, out = aprobar("largo")
check("aprobación parcial: solo el largo", c == 0, out)
c, out = correr("puertas.py", P, "--pieza", "short1", "--red", "youtube")
check("el Short sigue cerrado (no se aprobó)", c == 1 and "sin aprobación" in out, out)
c, out = correr("puertas.py", P, "--pieza", "largo")
check("puertas abiertas para el largo aprobado", c == 0 and "PUERTAS ABIERTAS" in out, out)

# cambios después de aprobar
otro = json.loads(json.dumps(PUB)); otro["piezas"][0]["titulo"] = "Otro título"
escribir_pub(otro)
c, out = correr("puertas.py", P, "--pieza", "largo")
check("cambiar el título después de aprobar cierra las puertas", c == 1 and "aprobar de nuevo" in out, out)
escribir_pub(PUB)
cfg = comun.leer_json(comun.CONFIG); cfg["youtube"]["idioma"] = "en"; comun.escribir_estado(comun.CONFIG, cfg)
c, out = correr("puertas.py", P, "--pieza", "largo")
check("cambiar la configuración heredada de YouTube (idioma) invalida la aprobación", c == 1 and "aprobar de nuevo" in out, out)
cfg["youtube"]["idioma"] = "es"; comun.escribir_estado(comun.CONFIG, cfg)
CHK.rename(CHK.with_name("checklist_publicacion_monetizacion_v0.md"))
c, out = correr("puertas.py", P, "--pieza", "largo")
check("el checklist de otra versión no sirve", c == 1 and "checklist_publicacion_monetizacion_v1.md" in out, out)
CHK.with_name("checklist_publicacion_monetizacion_v0.md").rename(CHK)
EV.rename(P / "06_RECETA" / "evaluacion_FIN-900_v10_con-subtitulos.json")
c, out = correr("puertas.py", P, "--pieza", "largo")
check("la evaluación de otra versión (v10) no sirve para la v1", c == 1 and "falta 06_RECETA" in out, out)
(P / "06_RECETA" / "evaluacion_FIN-900_v10_con-subtitulos.json").rename(EV)
TERM.write_text("# ¿Terminado?\n\n**SÍ: lo obligatorio pasa**\n", encoding="utf-8")
c, out = correr("puertas.py", P, "--pieza", "largo")
check("un terminado sin los puntos obligatorios no sirve", c == 1 and "faltan los puntos obligatorios" in out, out)
TERM.write_text(TERM_OK.replace("| 11 | Sin metadatos personales (GPS, celular, fecha) | ✓ | |\n", ""), encoding="utf-8")
c, out = correr("puertas.py", P, "--pieza", "largo")
check("un terminado antiguo, sin el punto 11 (GPS y datos del celular), no sirve", c == 1 and "obligatorios 11" in out, out)
TERM.write_text(TERM_OK, encoding="utf-8")
# 0.1.4: terminado y evaluación atados por HUELLA al archivo que se sube (la fecha ya no cuenta)
def _pl():
    return correr("puertas.py", P, "--pieza", "largo")


c, out = _pl()
check("evaluación del hermano con subtítulos, sellado en la misma corrida de terminado.py: pasa",
      "huella del video comprobada" in out and "misma corrida de terminado.py" in out, out)
_tj = TERMJ.read_text(encoding="utf-8")
TERMJ.unlink()
c, out = _pl()
check("sin terminado_*.json (terminado anterior al motor 0.14) la puerta se cierra", c == 1 and "con las huellas" in out, out)
TERMJ.write_text("{rota", encoding="utf-8")
c, out = _pl()
check("un terminado_*.json ilegible cierra la puerta, sin traza", c == 1 and "con las huellas" in out and "Traceback" not in out, out)
TERMJ.write_text(_tj, encoding="utf-8")
_yt = R7 / "FIN-900_v1_youtube.mp4"; _b = _yt.read_bytes(); _st = _yt.stat()
_yt.write_bytes(_b + b"0"); os.utime(_yt, (_st.st_atime, _st.st_mtime - 3600))
c, out = _pl()
check("un video cambiado después de terminado.py no pasa aunque su fecha sea anterior",
      c == 1 and "cambió después de terminado.py" in out, out)
_yt.write_bytes(_b); os.utime(_yt, (_st.st_atime, _st.st_mtime))
_copia = P / "08_PUBLICAR" / "FIN-900_v1_export.mp4"; _copia.write_bytes(_b)
os.utime(_copia, (_st.st_atime, _st.st_mtime - 3600))
_otro = json.loads(json.dumps(PUB)); _otro["piezas"][0]["archivo"] = "08_PUBLICAR/FIN-900_v1_export.mp4"; escribir_pub(_otro)
c, out = _pl()
check("un MP4 que terminado.py nunca revisó (una copia en 08_PUBLICAR, con fecha vieja) no pasa",
      c == 1 and "no es uno de los videos que revisó" in out, out)
escribir_pub(PUB); _copia.unlink()
_csb = CS.read_bytes()
CS.write_bytes(b"otro render" * 80)
c, out = _pl()
check("si el video evaluado cambió después de la nota, la puerta se cierra", c == 1 and "cambió después de la evaluación" in out, out)
CS.write_bytes(_csb)
_d = json.loads(_tj); _d["videos"].pop(CS.name); TERMJ.write_text(json.dumps(_d), encoding="utf-8")
c, out = _pl()
check("si el video evaluado no está en la misma corrida de terminado.py que el que se sube, la puerta se cierra",
      c == 1 and "no está entre los videos que revisó" in out, out)
TERMJ.write_text(_tj, encoding="utf-8")
CS.rename(CS.with_suffix(".guardado"))
c, out = _pl()
check("si el video evaluado ya no está, la puerta se cierra", c == 1 and "ya no está" in out, out)
CS.with_suffix(".guardado").rename(CS)
EV.write_text(json.dumps({"video": str(CS), "nota_medida": 8.2, "clase_medida": "A"}), encoding="utf-8")
c, out = _pl()
check("una evaluación sin huella no vale (misma regla que el motor)", c == 1 and "no trae la huella" in out, out)
EV.write_text("{rota", encoding="utf-8")
c, out = _pl()
check("una evaluación ilegible cierra la puerta con una fila, sin traza", c == 1 and "no se puede leer" in out and "Traceback" not in out, out)
evaluar_falso(7.4, "B")
c, out = _pl()
check("nota bajo 8 no pasa aunque la clase sea B (misma regla que el motor)", c == 1 and "se exige nota 8" in out, out)
evaluar_falso(nota_short=6.8)
c, out = correr("puertas.py", P, "--pieza", "short1")
check("un Short con nota bajo 7 no pasa; con 7,2 sí (mínimo aparte del largo, que pide 8)",
      c == 1 and "se exige nota 7" in out and "nota 7 o más del mismo Short" in out, out)
evaluar_falso()
c, out = correr("puertas.py", P, "--pieza", "short1")
check("el Short con 7,2 pasa su evaluación", "se exige nota" not in out and "nota 7.2 clase B (huella de" in out, out)
(R7 / "celu").mkdir()
_cel = R7 / "celu" / "FIN-900_v1_youtube_celu.mp4"; _cel.write_bytes(_b)
_d = json.loads(_tj); _d["videos"]["celu/" + _cel.name] = _h(_cel); TERMJ.write_text(json.dumps(_d), encoding="utf-8")
_otro = json.loads(json.dumps(PUB)); _otro["piezas"][0]["archivo"] = "07_RENDER_ESTUDIO/celu/" + _cel.name; escribir_pub(_otro)
c, out = _pl()
check("la copia para el celular no se puede subir como pieza, aunque esté sellada", c == 1 and "copia para el celular" in out, out)
escribir_pub(PUB); TERMJ.write_text(_tj, encoding="utf-8"); shutil.rmtree(R7 / "celu")
evaluar_falso()
c, out = _pl()
check("con todo en su lugar otra vez, terminado y evaluación vuelven a pasar",
      "huella del video comprobada" in out and "misma corrida de terminado.py" in out, out)
c, out = aprobar("short1")
check("aprobar el Short", c == 0, out)

# 0.1.6: la carpeta de publicación sale de proyecto.json, como en el motor
_pp = TMPD / "proyecto_publicar"; _pp.mkdir()
check("sin proyecto.json la carpeta de publicación es 08_PUBLICAR", comun.carpeta_publicar(_pp).name == "08_PUBLICAR")
(_pp / "proyecto.json").write_text(json.dumps({"carpetas": {"publicar": "08_PUBLICAR_ESTUDIO"}}), encoding="utf-8")
check("con \"publicar\" en proyecto.json se usa esa carpeta (FIN-002: 08_PUBLICAR_ESTUDIO)",
      comun.carpeta_publicar(_pp) == _pp / "08_PUBLICAR_ESTUDIO")
# 0.1.8: un valor presente pero inválido detiene al gerente (no vuelve en silencio a 08_PUBLICAR)
def _se_detiene(pj):
    (_pp / "proyecto.json").write_text(json.dumps(pj), encoding="utf-8")
    try:
        comun.carpeta_publicar(_pp)
        return False
    except SystemExit as e:
        return "proyecto.json" in str(e.code)
for _v, _que in (("..\\otra", "«..» y barra"), (".", "«.»"), ("", "vacío"), ("08_PUBLICAR/ES", "subcarpeta"),
                 ("08_PUBLICAR\\ES", "subcarpeta con barra invertida"), (" 08_X", "espacio al inicio"),
                 ("08_X ", "espacio al final"), (5, "un número")):
    check(f"carpetas.publicar inválido ({_que}): el gerente se detiene con un mensaje", _se_detiene({"carpetas": {"publicar": _v}}))
check("«carpetas» que no es un diccionario: el gerente se detiene", _se_detiene({"carpetas": ["08_PUBLICAR"]}))
(_pp / "proyecto.json").write_text(json.dumps({"publicar": "OTRA"}), encoding="utf-8")
check("una clave «publicar» en la raíz no se lee (el motor tampoco): 08_PUBLICAR", comun.carpeta_publicar(_pp).name == "08_PUBLICAR")
(_pp / "proyecto.json").write_text(json.dumps({"publicar": "OTRA", "carpetas": {"voz": "02_VOZ"}}), encoding="utf-8")
check("«carpetas» sin «publicar»: 08_PUBLICAR, como el motor", comun.carpeta_publicar(_pp).name == "08_PUBLICAR")
(_pp / "proyecto.json").write_text("{rota", encoding="utf-8")
check("un proyecto.json ilegible no bota al gerente: 08_PUBLICAR", comun.carpeta_publicar(_pp).name == "08_PUBLICAR")
(P / "proyecto.json").write_text(json.dumps({"carpetas": {"publicar": "08_PUBLICAR_ESTUDIO"}}), encoding="utf-8")
c, out = correr("puertas.py", P, "--pieza", "largo")
check("si proyecto.json apunta a otra carpeta, el gerente busca ahí publicacion.json (y no en 08_PUBLICAR)",
      c == 1 and "falta 08_PUBLICAR" in out, out)
(P / "proyecto.json").write_text(json.dumps({"carpetas": {"publicar": "08_PUBLICAR/ES"}}), encoding="utf-8")
c, out = correr("puertas.py", P, "--pieza", "largo")
check("puertas.py con carpetas.publicar inválido se detiene (no revisa 08_PUBLICAR)", c != 0 and "carpetas.publicar" in out, out)
(P / "proyecto.json").unlink()

# 0.1.6: la nota mínima la decide el archivo, no la etiqueta "tipo"
_otro = json.loads(json.dumps(PUB)); _otro["piezas"][0]["tipo"] = "short"; escribir_pub(_otro)
c, out = correr("puertas.py", P, "--pieza", "largo")
check("un largo etiquetado como Short no pasa (no se baja la nota mínima cambiando el tipo)",
      c == 1 and "calza con el archivo | ✗" in out, out)
_otro = json.loads(json.dumps(PUB)); _otro["piezas"][1]["tipo"] = "largo"; escribir_pub(_otro)
c, out = correr("puertas.py", P, "--pieza", "short1")
check("un Short etiquetado como largo no pasa (no toma prestada la nota del largo)",
      c == 1 and "calza con el archivo | ✗" in out, out)
escribir_pub(PUB)
c, out = correr("puertas.py", P, "--pieza", "largo")
check("con el tipo correcto, la fila del tipo pasa", "calza con el archivo | ✓" in out, out)

# --- calendario
c, out = correr("calendario.py", "importar", P)
check("calendario importa 4 entradas", c == 0 and "4 entradas nuevas" in out, out)
c, out = correr("calendario.py", "importar", P)
check("calendario no duplica", "0 entradas nuevas" in out, out)
c, out = correr("calendario.py", "ver")
check("calendario muestra horas de Sídney y Auckland", "Sydney" in out and "Auckland" in out, out)
c, out = correr("calendario.py", "estado", "FIN-900_v1_largo_youtube", "aprobado")
check("calendario cambia estado", c == 0, out)
c, out = correr("calendario.py", "pendientes")
check("pendientes lista lo aprobado", "FIN-900_v1_largo_youtube" in out, out)
c, out = correr("calendario.py", "hoja", P)
hojas = list((P / "08_PUBLICAR").glob("hoja_de_publicacion_v1*.md"))
check("hoja manual creada para Instagram", c == 0 and hojas and "instagram" in hojas[0].read_text(encoding="utf-8"), out)

# --- subidas con YouTube de mentira
import yt_api, puertas
from comun import huella

SHA_LARGO = huella(R7 / "FIN-900_v1_youtube.mp4")


class Medio:
    """Como MediaFileUpload: abre el archivo; el gerente debe cerrarlo al terminar."""
    def __init__(self, ruta, **k):
        self.ruta, self.f = Path(ruta), open(ruta, "rb")
    def stream(self):
        return self.f


class Req:
    def __init__(self, r, error=None): self.r, self.error = r, error
    def execute(self):
        if self.error:
            raise self.error
        return self.r
    def next_chunk(self, num_retries=0):
        if self.error:
            raise self.error
        return None, self.r


PRIVACIDAD = []     # lo que el gerente le dijo a YouTube en cada subida o cambio de estado (desde el 02-11-2026,
                    # una subida sin privacidad queda PÚBLICA por defecto: nunca puede faltar ni ser otra cosa que private)


class FakeYT:
    def __init__(self, error=None, canal="UC_CANAL_BUENO", falla_miniatura=False):
        self.llamadas, self.error, self.canal, self.falla_miniatura = [], error, canal, falla_miniatura
        self.subido, self.status, self.medios = None, {}, []
    def channels(self): return self._as("channels")
    def videos(self): return self._as("videos")
    def thumbnails(self): return self._as("thumbnails")
    def captions(self): return self._as("captions")
    def playlistItems(self): return self._as("playlistItems")
    def _as(self, n): self.recurso = n; return self
    def list(self, **k):
        if self.recurso == "channels":
            return Req({"items": [{"id": self.canal}]})
        return Req({"items": [{"status": dict(self.status)}]})
    def insert(self, **k):
        self.llamadas.append((self.recurso, "insert", k))
        if self.recurso == "videos":
            PRIVACIDAD.append(k["body"].get("status", {}).get("privacyStatus"))
            m = k["media_body"]; self.medios.append(m)
            self.subido = (m.ruta.parent == comun.TMP, huella(m.ruta), "publishAt" in k["body"]["status"])
            self.status = dict(k["body"]["status"])
            return Req({"id": "VID123", "status": dict(self.status)}, self.error)
        if "media_body" in k:
            self.medios.append(k["media_body"])
        return Req({})
    def set(self, **k):
        self.llamadas.append((self.recurso, "set", k)); self.medios.append(k["media_body"])
        return Req({}, RuntimeError("miniatura rechazada") if self.falla_miniatura else None)
    def update(self, **k):
        self.llamadas.append((self.recurso, "update", k)); self.status = dict(k["body"]["status"])
        PRIVACIDAD.append(k["body"].get("status", {}).get("privacyStatus"))
        return Req({"status": dict(self.status)})


r = yt_api.subir(P, "largo", simular=True)
check("simulación: privado y SIN fecha en el envío; la fecha va al final (nivel 2)",
      r and r["body"]["status"]["privacyStatus"] == "private" and "publishAt" not in r["body"]["status"]
      and str(r["publishAt"]).endswith("Z") and r["body"]["status"]["containsSyntheticMedia"] is False)
check("otro canal conectado: no se sube", yt_api.subir(P, "largo", yt=FakeYT(canal="UC_OTRO"), media=Medio) is None)
yt = FakeYT()
r = yt_api.subir(P, "largo", yt=yt, media=Medio)
check("subida queda programada", r and r["estado"] == "programado", str(r))
check("se sube una copia verificada, privada y sin fecha; la fecha se pone después con update",
      yt.subido == (True, SHA_LARGO, False) and any(x[1] == "update" for x in yt.llamadas)
      and yt.status.get("publishAt", "").endswith("Z"), str(yt.subido))
check("se pusieron miniatura y subtítulos ANTES de programar",
      [x[0] for x in yt.llamadas if x[1] in ("set", "insert", "update")] == ["videos", "thumbnails", "captions", "videos"], str(yt.llamadas))
check("los archivos quedan cerrados, las copias temporales borradas y sin candado",
      all(m.f.closed for m in yt.medios) and not list(comun.TMP.glob("*.mp4")) and not list(comun.TMP.glob("subiendo_*")))
check("hay diario de la operación", len(list((comun.GER / "diario").glob("*_largo_youtube_programado.json"))) == 1)
check("no se sube dos veces el mismo archivo", yt_api.subir(P, "largo", yt=FakeYT(), media=Medio) is None)
c, out = correr("anotar.py", P, "largo", "youtube", "--estado", "medido_48h")
check("anotar una medición no hace olvidar que está publicado", yt_api.subir(P, "largo", yt=FakeYT(), media=Medio) is None, out)

# candado, falla de miniatura y envíos inciertos con el Short
SHA_S = huella(R7 / "FIN-900_v1_short1_9x16.mp4")
cand = comun.TMP / f"subiendo_{SHA_S[:16]}_youtube.lock"
cand.write_text("otro proceso", encoding="utf-8")
check("con otra subida en curso no se lanza una segunda", yt_api.subir(P, "short1", yt=FakeYT(), media=Medio) is None)
cand.unlink()
r = yt_api.subir(P, "short1", yt=FakeYT(error=RuntimeError("se cortó la conexión")), media=Medio)
ult = comun.registro()[-1]
check("si la subida se corta, queda «incierto» y se libera el candado", r is None and ult["estado"] == "incierto" and not cand.exists(), str(ult))
check("un envío incierto bloquea otro intento", yt_api.subir(P, "short1", yt=FakeYT(), media=Medio) is None)
c, out = correr("calendario.py", "pendientes")
check("pendientes avisa lo que hay que revisar en la plataforma", "REVISAR EN LA PLATAFORMA" in out, out)
c, out = correr("anotar.py", P, "short1", "youtube", "--estado", "error", "--nota", "revisado en Studio: no quedó nada")
yt2 = FakeYT(falla_miniatura=True)
pz = json.loads(json.dumps(PUB)); pz["piezas"][1]["miniatura"] = "08_PUBLICAR/FIN-900_miniatura_1.png"; escribir_pub(pz)
aprobar("short1")
r = yt_api.subir(P, "short1", yt=yt2, media=Medio)
check("si la miniatura falla, NO se programa: queda privado", r and r["estado"] == "subido_privado"
      and not any(x[1] == "update" for x in yt2.llamadas) and any("NO se programó" in n for n in r["notas"]), str(r))
escribir_pub(PUB)
aprobar("short1")

# reservas para conectores
c, out = correr("anotar.py", P, "short1", "instagram", "--reservar")
check("reservar revisa las puertas (Instagram manual) y deja en_curso", c == 0 and "RESERVADO" in out, out)

# niveles
cfg = comun.leer_json(comun.CONFIG)
tam = (R7 / "FIN-900_v1_short1_9x16.mp4").stat().st_size
SHA_ACTUAL_S = huella(R7 / "FIN-900_v1_short1_9x16.mp4")
for valor in (1, 0, "2", 3):
    cfg["nivel"] = valor
    comun.escribir_estado(comun.CONFIG, cfg)
    rr = puertas.revisar(P, "largo", "youtube")
    nivel_ok = [ok for n, ok, _ in rr if n.startswith("nivel")]
    if valor == 1:
        check("nivel 1 abre la puerta de nivel", nivel_ok == [True])
        rm = puertas.revisar(P, "short1", "tiktok", revisar_enlace=lambda u: (True, "video/mp4", tam), huella_enlace=lambda u: SHA_ACTUAL_S)
        check("nivel 1 no permite programar en Metricool", not puertas.todo_ok(rm) and any("nivel 2" in n and not ok for n, ok, _ in rm))
    else:
        check(f"nivel {valor!r} cierra las puertas", nivel_ok == [False], str(rr))
cfg["nivel"] = 2
comun.escribir_estado(comun.CONFIG, cfg)

# Metricool: contenido del enlace y cupo
aprobar("short1")
rm = puertas.revisar(P, "short1", "tiktok", revisar_enlace=lambda u: (True, "video/mp4", tam), huella_enlace=lambda u: SHA_ACTUAL_S)
check("Metricool: puertas abiertas con el mismo video en el enlace", puertas.todo_ok(rm), puertas.tabla(rm))
rm = puertas.revisar(P, "short1", "tiktok", revisar_enlace=lambda u: (True, "video/mp4", tam), huella_enlace=lambda u: "f" * 64)
check("Metricool: otro video del mismo tamaño cierra las puertas", not puertas.todo_ok(rm) and "OTRO video" in puertas.tabla(rm))
c, out = correr("anotar.py", P, "short1", "tiktok", "--estado", "programado", "--enlace", "https://app.metricool.com/x")
c2, out2 = correr("anotar.py", P, "short1", "tiktok", "--estado", "publicado")
c3, out3 = correr("anotar.py", P, "short1", "tiktok", "--estado", "medido_48h")
c4, out4 = correr("calendario.py", "cupo", "--mes", pasado[:7])
check("cupo cuenta una sola vez lo programado, publicado y medido", "1 publicadas o programadas de 20" in out4, out + out2 + out3 + out4)
check("anotar sin --enlace conserva el enlace anterior", comun.registro()[-1]["enlace"] == "https://app.metricool.com/x")

# vidIQ: ventana horaria y Short ya público
pv = json.loads(json.dumps(PUB)); pv["piezas"][1]["destinos"][2]["ruta"] = "vidiq"; escribir_pub(pv)
aprobar("short1")
hora_ig = comun.a_utc(pasado, "America/Santiago")
rv = puertas.revisar(P, "short1", "instagram", ahora=hora_ig - dt.timedelta(hours=3))
check("vidIQ: fuera de la hora, cerrado", not puertas.todo_ok(rv) and any("es la hora" in n and not ok for n, ok, _ in rv))
escribir_pub(PUB)

# revocar, cancelar y desprogramar
c, out = correr("aprobar.py", P, "--revocar", "--piezas", "largo", "--por", "Patricio")
check("revocar avisa que el largo sigue programado", c == 0 and "AVISO IMPORTANTE" in out and "desprogramar" in out, out)
c, out = correr("puertas.py", P, "--pieza", "largo")
check("tras revocar, las puertas del largo se cierran", c == 1 and "sin aprobación vigente" in out, out)
aprobar("largo")


class FakeUpd:
    def __init__(self, publish="2099-01-01T00:00:00Z"): self.cuerpo, self.publish = None, publish
    def videos(self): return self
    def list(self, **k): return Req({"items": [{"status": {"privacyStatus": "private", "publishAt": self.publish, "license": "youtube",
                                                           "embeddable": True, "selfDeclaredMadeForKids": False,
                                                           "containsSyntheticMedia": False, "uploadStatus": "processed"}}]})
    def update(self, **k):
        self.cuerpo = k["body"]; return Req({"status": {k2: v for k2, v in k["body"]["status"].items()}})


cerca = (comun.ahora_utc() + dt.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
try:
    yt_api.desprogramar(P, "largo", "Patricio", yt=FakeUpd(publish=cerca)); cerca_ok = False
except SystemExit:
    cerca_ok = True
check("desprogramar se niega si faltan menos de 10 minutos", cerca_ok)
fu = FakeUpd()
yt_api.desprogramar(P, "largo", "Patricio", yt=fu)
cal = comun.leer_json(comun.CALENDARIO)
check("desprogramar deja privado, sin publishAt, conserva los campos y actualiza el calendario",
      fu.cuerpo and "publishAt" not in fu.cuerpo["status"] and fu.cuerpo["status"]["privacyStatus"] == "private"
      and fu.cuerpo["status"].get("license") == "youtube" and "uploadStatus" not in fu.cuerpo["status"]
      and comun.registro()[-1]["estado"] == "cancelado"
      and next(e for e in cal["entradas"] if e["id"] == "FIN-900_v1_largo_youtube")["estado"] == "cancelado")
c, out = correr("puertas.py", P, "--pieza", "largo")
check("lo cancelado no se vuelve a publicar con la aprobación vieja", c == 1 and "sin aprobación vigente" in out, out)

# archivo y terminado
(R7 / "FIN-900_v1_short1_9x16.mp4").write_bytes(b"short re-renderizado" * 50)
c, out = correr("puertas.py", P, "--pieza", "short1", "--red", "instagram")
check("si el video cambia, la aprobación deja de valer y el terminado ya no es de ese archivo", c == 1 and "aprobar de nuevo" in out and "cambió después de terminado.py" in out, out)
TERM.write_text(TERM_OK.replace("| 2 | punto 2 | ✓ |", "| 2 | punto 2 | ✗ |"), encoding="utf-8")
c, out = correr("puertas.py", P, "--pieza", "largo")
check("terminado con ✗ obligatorio cierra las puertas", c == 1 and "punto 2" in out, out)
TERM.write_text(TERM_OK + "| 7a | fila rara | ✓ | |\n", encoding="utf-8")
c, out = correr("puertas.py", P, "--pieza", "largo")
check("una fila no reconocida en terminado cierra las puertas", c == 1 and "no reconocida" in out, out)

# calendario sigue a publicacion.json
otro = json.loads(json.dumps(PUB)); otro["piezas"][1]["destinos"][2]["fecha"] = (dt.datetime.now() + dt.timedelta(days=4)).strftime("%Y-%m-%dT20:00")
escribir_pub(otro)
c, out = correr("calendario.py", "importar", P)
check("si cambia la fecha en publicacion.json, el calendario se actualiza", "CAMBIO" in out or "AVISO" in out, out)

# bloqueo con dueño
with comun.bloqueo("prueba_dueno"):
    f = comun.TMP / "prueba_dueno.lock"
    f.write_text("de otro proceso", encoding="utf-8")
check("un bloqueo ajeno no se borra al salir", (comun.TMP / "prueba_dueno.lock").exists())
(comun.TMP / "prueba_dueno.lock").unlink()


# progreso
class FakeYA:
    def reports(self): return self
    def query(self, **k):
        if k["startDate"] < (dt.date.today() - dt.timedelta(days=100)).isoformat():
            return Req({"columnHeaders": [{"name": "creatorContentType"}, {"name": "views"}, {"name": "estimatedMinutesWatched"}],
                        "rows": [["VIDEO_ON_DEMAND", 5000, 180000], ["LIVE_STREAM", 10, 6000], ["SHORTS", 90000, 3000]]})
        return Req({"columnHeaders": [{"name": "creatorContentType"}, {"name": "views"}], "rows": [["SHORTS", 3_200_000]]})


class FakeCanal:
    def __init__(self): self.r = None
    def channels(self): self.r = "c"; return self
    def playlistItems(self): self.r = "p"; return self
    def videos(self): self.r = "v"; return self
    def list(self, **k):
        hoy = dt.date.today()
        if self.r == "p":
            if not k.get("pageToken"):
                return Req({"items": [{"contentDetails": {"videoId": f"a{d}", "videoPublishedAt": (hoy - dt.timedelta(days=d)).isoformat()}}
                                      for d in (3, 20)], "nextPageToken": "T2"})
            return Req({"items": [{"contentDetails": {"videoId": f"a{d}", "videoPublishedAt": (hoy - dt.timedelta(days=d)).isoformat()}}
                                  for d in (50, 60, 200)]})
        if self.r == "v":
            ids = k["id"].split(",")
            return Req({"items": [{"status": {"privacyStatus": "private" if i == "a60" else "public"}} for i in ids]})
        return Req({"items": [{"statistics": {"subscriberCount": "620"}, "contentDetails": {"relatedPlaylists": {"uploads": "UU1"}}}]})


res = yt_api.progreso(yt=FakeCanal(), ya=FakeYA())
check("progreso: horas de largos y directos, Shorts, y solo subidas PÚBLICAS de 90 días (con paginación)",
      res["horas_largos_365d"] == 3100.0 and res["vistas_shorts_90d"] == 3_200_000 and res["subidas_publicas_90d"] == 3, str(res))
check("progreso: alcanzaría fan funding (estimado) y no anuncios",
      res["metas"]["fan_funding"]["alcanzaria_estimado"] and not res["metas"]["anuncios"]["alcanzaria_estimado"])

shutil.rmtree(TMPD, ignore_errors=True)
check("toda subida y todo cambio de estado en YouTube dijo privacyStatus = private (nunca vacío ni público)",
      len(PRIVACIDAD) >= 3 and all(x == "private" for x in PRIVACIDAD), str(PRIVACIDAD))
import inspect as _ins
_src = _ins.getsource(yt_api)
check("yt_api.py no escribe nunca privacyStatus public ni unlisted",
      '"privacyStatus": "public"' not in _src and '"privacyStatus": "unlisted"' not in _src
      and "privacyStatus\"] = \"public" not in _src and "privacyStatus\"] = \"unlisted" not in _src)
print(flush=True)
if fallas:
    print(f"PRUEBA FALLIDA: {len(fallas)} puntos", flush=True)
    sys.exit(1)
print("PRUEBA SUPERADA", flush=True)
