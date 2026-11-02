# Motor del Estudio Paltostaila: piezas comunes para todos los scripts.
# Cada video vive en su carpeta con un proyecto.json; los scripts reciben esa carpeta:
#   python armar.py "C:\ruta\al\video"        (o se ejecutan desde dentro de la carpeta)
import glob, json, os, re, shutil, subprocess, sys
from pathlib import Path

DEFAULTS = {
    "nombre": "Video",
    "version": "",
    "carpetas": {
        "guion": "01_GUION",
        "voz": "02_VOZ",
        "imagenes": "03_IMAGENES",
        "clips": "04_CLIPS_FLOW",
        "sonidos": "05_SONIDOS",
        "receta": "06_RECETA/receta.csv",
        "transcripcion": "06_RECETA/transcripcion.json",
        "salida": "07_RENDER",
        "publicar": "08_PUBLICAR",
    },
    "audios": "02_VOZ/*",
    "video": {"fps": 30, "ancho": 1920, "alto": 1080, "crf": 20},
    "transiciones": {"normal": ["fade", 12], "capitulo": ["smoothleft", 18], "plano": ["fade", 6]},
    "escenas_capitulo": [],
    "alias_clips": {},
    "planos": {},
    "movimientos": [
        [[1.00, .50, .50], [1.10, .50, .45]],
        [[1.10, .42, .48], [1.10, .58, .48]],
        [[1.12, .50, .44], [1.00, .50, .50]],
        [[1.10, .58, .48], [1.10, .42, .48]],
        [[1.00, .50, .50], [1.13, .50, .38]],
    ],
    "correcciones": [],
    "subtitulos": {"max_caracteres": 80, "fuente": "Arial", "tamano": 54},
    "rotulos": [],
    "capitulos": [],
    "volumen_lufs": -14,
    "sonidos": {
        "activar": True,
        "vol_efectos": -19,
        "vol_clips": -16,
        "whoosh_db": -25,
        "whoosh_en_capitulos": True,
        "efectos": [],
        "lapiz": [],
        "clips_con_sonido": [],
        "recorte_clip": {},
        "limite_capa": 0.3,
    },
    "vertical": [],
    "miniaturas": [],
    "whisperx": {"modelo": "large-v3", "idioma": "es", "compute_type": "int8"},
}


CALIDADES = {"720p": (1280, 720), "1080p": (1920, 1080), "1440p": (2560, 1440), "2k": (2560, 1440),
             "4k": (3840, 2160), "2160p": (3840, 2160)}


def _mezclar(base, extra):
    out = dict(base)
    for k, v in (extra or {}).items():
        out[k] = _mezclar(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


class Proyecto:
    """Lee proyecto.json y resuelve rutas relativas a la carpeta del video."""

    def __init__(self, carpeta=None):
        if carpeta is None:
            carpeta = next((a for a in sys.argv[1:] if not a.startswith("-") and Path(a).is_dir()), ".")
        self.dir = Path(carpeta).resolve()
        archivo = self.dir / "proyecto.json"
        if not archivo.exists():
            sys.exit(f"No encuentro {archivo}. Crea el proyecto con nuevo_proyecto.py.")
        self.cfg = _mezclar(DEFAULTS, json.loads(archivo.read_text(encoding="utf-8")))
        c = self.cfg["carpetas"]
        r = self.ruta
        self.imagenes, self.voz, self.clips = r(c["imagenes"]), r(c["voz"]), r(c["clips"])
        self.sonidos, self.receta, self.transcripcion = r(c["sonidos"]), r(c["receta"]), r(c["transcripcion"])
        self.salida, self.publicar = r(c["salida"]), r(c["publicar"])
        self.tmp = self.salida / "tmp"
        self.tmp.mkdir(parents=True, exist_ok=True)
        v = self.cfg["video"]
        self.fps, self.ancho, self.alto = v["fps"], v["ancho"], v["alto"]
        if v.get("calidad"):   # "720p", "1080p", "1440p" o "4k"; respeta si el video es vertical
            lado = CALIDADES[str(v["calidad"]).lower()]
            self.ancho, self.alto = (lado[1], lado[0]) if v["alto"] > v["ancho"] else lado
        ver = self.cfg["version"]
        self.base_nombre = self.cfg["nombre"] + (f"_{ver}" if ver else "")

    def ruta(self, p):
        p = Path(os.path.expandvars(os.path.expanduser(str(p))))
        return p if p.is_absolute() else (self.dir / p).resolve()

    def __getitem__(self, k):
        return self.cfg[k]

    def audios(self):
        patrones = self.cfg["audios"] if isinstance(self.cfg["audios"], list) else [self.cfg["audios"]]
        patron = ", ".join(str(self.ruta(p)) for p in patrones)
        lista = sorted({Path(x) for p in patrones for x in glob.glob(str(self.ruta(p)))
                        if Path(x).suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")})
        if not lista:
            sys.exit(f"No encuentro audios de voz con el patron {patron}")
        return lista

    def duracion(self):
        return round(sum(duracion_medio(a) for a in self.audios()), 3)

    def escenas(self):
        import csv
        with open(self.receta, encoding="utf-8-sig", newline="") as f:
            filas = list(csv.DictReader(f, delimiter=";"))
        for r in filas:
            r["n"] = int(r["numero"])
            r["t0"], r["t1"] = t2s(r["inicio"]), t2s(r["fin"])
        return filas


# ---------- herramientas externas ----------

def _buscar_ffmpeg(nombre):
    env = os.environ.get("ESTUDIO_FFMPEG_DIR")
    if env and (Path(env) / f"{nombre}.exe").exists():
        return str(Path(env) / f"{nombre}.exe")
    encontrado = shutil.which(nombre)
    if encontrado:
        return encontrado
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        for p in glob.glob(os.path.join(local, "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "**", "bin", f"{nombre}.exe"), recursive=True):
            return p
    sys.exit(f"No encuentro {nombre}. Ejecuta instalar.cmd o instala ffmpeg (winget install Gyan.FFmpeg).")


FFMPEG = _buscar_ffmpeg("ffmpeg")
FFPROBE = _buscar_ffmpeg("ffprobe")


def run(cmd, cwd=None):
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(" ".join(map(str, cmd))[:400] + "\n" + r.stderr[-1500:])
    return r.stdout + r.stderr


def duracion_medio(p):
    return float(run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).strip())


def t2s(t):
    t = str(t).strip().replace(",", ".")
    partes = [float(x) for x in t.split(":")]
    s = 0.0
    for x in partes:
        s = s * 60 + x
    return s


def ts(t, ass=True):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h}:{m:02d}:{s:05.2f}" if ass else f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def mmss(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


# ---------- transcripcion por palabra ----------

def norm(s):
    return re.sub(r"[^\wáéíóúñü ]", "", s.lower()).split()


def cargar(pr):
    if not pr.transcripcion.exists():
        sys.exit(f"Falta la transcripcion {pr.transcripcion}. Ejecuta transcribir.py primero.")
    segs = json.loads(pr.transcripcion.read_text(encoding="utf-8"))["segments"]
    for s in segs:   # palabras sin marca (numeros): se reparten dentro del segmento
        ws = s.get("words") or [{"word": w, "start": s["start"], "end": s["end"]} for w in s["text"].split()]
        s["words"] = ws
        for i, w in enumerate(ws):
            if "start" not in w:
                prev = next((x["end"] for x in reversed(ws[:i]) if "end" in x), s["start"])
                nxt = next((x["start"] for x in ws[i + 1:] if "start" in x), s["end"])
                w["start"], w["end"] = prev, nxt
    return segs


def corregir(pr, segs, avisar=True):
    """Aplica las correcciones del proyecto sobre las palabras, conservando sus tiempos."""
    for a, b in pr["correcciones"]:
        va, vb, hecho = a.split(), b.split(), False
        for s in segs:
            ws = s["words"]
            toks = [w["word"] for w in ws]
            for i in range(len(toks) - len(va) + 1):
                if toks[i:i + len(va)] == va:
                    t0, t1 = ws[i]["start"], ws[i + len(va) - 1]["end"]
                    paso = (t1 - t0) / len(vb)
                    nuevas = [{"word": p, "start": t0 + k * paso, "end": t0 + (k + 1) * paso} for k, p in enumerate(vb)]
                    s["words"] = ws[:i] + nuevas + ws[i + len(va):]
                    hecho = True
                    break
            if hecho:
                break
        if avisar:
            print(("corregido: " if hecho else "AVISO correccion no encontrada: ") + a, flush=True)
    return segs


def palabras(pr, avisar=False):
    segs = corregir(pr, cargar(pr), avisar)
    return segs, [w for s in segs for w in s["words"]]


def buscar(pals, frase):
    objetivo = norm(frase)
    toks = [norm(w["word"])[0] if norm(w["word"]) else "" for w in pals]
    for i in range(len(toks) - len(objetivo) + 1):
        if toks[i:i + len(objetivo)] == objetivo:
            return pals[i]["start"]
    raise ValueError(f"No encontre la frase en la transcripcion: {frase}")


def cues(segs, max_chars=80):
    out = []
    for s in segs:
        ws, grupo = s["words"], []
        for w in ws:
            grupo.append(w)
            texto = " ".join(x["word"] for x in grupo)
            corte = (len(texto) >= max_chars * 0.55 and w["word"].endswith((",", ";", ":"))) or \
                    (len(texto) >= max_chars * 0.35 and w["word"].endswith((".", "?", "!", "…")))
            if len(texto) >= max_chars - 12 or corte:
                out.append(grupo); grupo = []
        if grupo:
            if out and out[-1][0] in ws and len(" ".join(x["word"] for x in out[-1] + grupo)) <= max_chars:
                out[-1] += grupo   # no dejar una palabra suelta al final de una frase
            else:
                out.append(grupo)
    lista = [[g[0]["start"], g[-1]["end"], " ".join(x["word"] for x in g)] for g in out]
    for i, c in enumerate(lista):   # dejar el texto un poco mas en pantalla si hay espacio
        sig = lista[i + 1][0] if i + 1 < len(lista) else c[1] + 1.0
        c[1] = min(max(c[1] + 0.4, c[0] + 1.0), sig - 0.04)
    return lista


def momento(pr, pals, escenas, d):
    """Un momento del video descrito como {"frase": ...} o {"escena": n} con "desfase" opcional."""
    if "frase" in d:
        t = buscar(pals, d["frase"])
    elif "escena" in d:
        t = next(r["t0"] for r in escenas if r["n"] == int(d["escena"]))
    else:
        t = float(d["segundo"])
    return t + float(d.get("desfase", 0))
