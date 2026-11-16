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
        "alinear": "inicio",       # 0.14: "ataque" (el primer sonido audible cae en el momento) o "pico"; "inicio" = como
                                   # siempre. Los proyectos NUEVOS nacen con "ataque" (nuevo_proyecto.py); los que ya
                                   # existen no cambian de sonido si se vuelven a armar.
        "baja_sobre_voz": 0,       # dB que baja un efecto puesto por "segundo" o "escena" si parte en medio de una palabra
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
        self.id = self.cfg.get("id") or self.cfg["nombre"]     # por ejemplo FIN-003
        self.version = ver or "v1"
        self.base_nombre = f"{self.id}_{self.version}"         # todo lo que sale del estudio empieza asi

    def ruta(self, p):
        p = Path(os.path.expandvars(os.path.expanduser(str(p))))
        return p if p.is_absolute() else (self.dir / p).resolve()

    def __getitem__(self, k):
        return self.cfg[k]

    def audios(self):
        patrones = self.cfg["audios"] if isinstance(self.cfg["audios"], list) else [self.cfg["audios"]]
        patron = ", ".join(str(self.ruta(p)) for p in patrones)
        lista = sorted({Path(x) for p in patrones for x in glob.glob(str(self.ruta(p)))
                        if Path(x).suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac") and not es_resto(x)})
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

# Perfil bajo (T1, 08-11-2026): un video que sale del PC no lleva los metadatos del original (GPS, marca y modelo del
# celular, fecha de grabación, capítulos). Se pone justo antes del archivo de salida en cada comando que escribe una entrega.
SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]
# Lo único que puede quedar: etiquetas técnicas con los valores que pone el propio ffmpeg. Cualquier otra cosa, o un valor
# distinto (por ejemplo handler_name="Core Media Video" de un iPhone), se informa para revisar.
_TECNICAS = {"major_brand": {"isom", "mp42", "mp41", "iso5", "iso6", "M4A ", "M4A", "M4V ", "M4V", "qt  ", "qt"},
             "minor_version": None, "compatible_brands": None, "language": None,
             "duration": None,                                 # MKV y WEBM guardan la duración de cada pista como etiqueta
             "vendor_id": {"[0][0][0][0]", "FFMP"}, "encoder": ("Lavf", "Lavc", "Lavc6", "Lavc7"),
             "handler_name": {"VideoHandler", "SoundHandler", "SubtitleHandler", "DataHandler"}}


def _tecnica(k, v):
    regla = _TECNICAS.get(k.lower(), False)
    if regla is False:
        return False
    if regla is None:
        return True
    if k.lower() == "major_brand":
        return str(v).strip() in {x.strip() for x in regla}
    if isinstance(regla, tuple):
        return str(v).startswith(regla)
    return str(v) in regla


def metadatos_personales(p):
    """Etiquetas que no son técnicas en un video (formato, pistas y capítulos): [] = limpio; None = no se pudo leer
    (ffprobe falló o no devolvió el formato): eso nunca cuenta como limpio."""
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries", "format=format_name:format_tags:stream_tags:chapters",
                        "-of", "json", str(p)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        return None
    try:
        d = json.loads(r.stdout or "{}")
    except ValueError:
        return None
    if not d.get("format"):
        return None
    tags = list((d["format"].get("tags") or {}).items())
    for s in d.get("streams", []):
        tags += list((s.get("tags") or {}).items())
    malos = {f"{k}={v}" if k.lower() in _TECNICAS else k for k, v in tags if not _tecnica(k, v)}
    if d.get("chapters"):
        malos.add(f"capítulos ({len(d['chapters'])})")
    return sorted(malos)


def run(cmd, cwd=None):
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(" ".join(map(str, cmd))[:400] + "\n" + r.stderr[-1500:])
    return r.stdout + r.stderr


def duracion_medio(p):
    return float(run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).strip())


def huella(p):
    """sha256 de un archivo (para saber si la evaluación o la aprobación corresponden a ESTE archivo)."""
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def ataque_y_pico(p, umbral_db=-40.0, max_s=12.0):
    """(ataque, pico) en segundos de un sonido: cuándo empieza a oírse (primera muestra sobre el umbral, medido
    contra su propio máximo) y cuándo llega a su punto más fuerte. (0.0, 0.0) si no se pudo leer o es silencio."""
    import array
    r = subprocess.run([str(FFMPEG), "-v", "error", "-t", str(max_s), "-i", str(p), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                       capture_output=True)
    if r.returncode or len(r.stdout) < 4:
        return 0.0, 0.0
    m = array.array("h"); m.frombytes(r.stdout[:len(r.stdout) // 2 * 2])
    if sys.byteorder == "big":
        m.byteswap()
    tope = max(max(m), -min(m))
    if tope < 30:
        return 0.0, 0.0
    lim = tope * 10 ** (umbral_db / 20)
    ataque = next((i for i, x in enumerate(m) if abs(x) >= lim), 0)
    pico = next(i for i, x in enumerate(m) if abs(x) == tope)
    return round(ataque / 8000, 3), round(pico / 8000, 3)


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

def slug(s, n=40):
    """texto -> nombre de archivo legible: minusculas, sin tildes ni espacios ("Dos personas" -> dos-personas)."""
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-") or "x"


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


# ---------- clips de Flow: que hay en la carpeta y que quedo dentro del video armado ----------

def clips_disponibles(pr):
    """{escena: ruta} de las escenas de la receta que tienen clip escena_NNN.mp4 (o alias) en la carpeta de clips."""
    alias = {int(k): int(v) for k, v in pr["alias_clips"].items()}
    out = {}
    for r in pr.escenas():
        base = alias.get(r["n"], r["n"])
        p = pr.clips / f"escena_{base:03d}.mp4"
        if p.exists():
            out[str(r["n"])] = p
        for q in sorted(pr.clips.glob(f"escena_{base:03d}_p*.mp4")):   # clips hechos para un plano
            out[f"{r['n']}_{q.stem.split('_')[-1]}"] = q
    return out


def manifiesto(pr, video="solo_video.mp4"):
    p = pr.tmp / (Path(video).stem + ".json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def clips_pendientes(pr, video="solo_video.mp4"):
    """Clips que estan en la carpeta pero NO en el video armado (o que cambiaron despues de armarlo)."""
    m = manifiesto(pr, video)
    usados = (m or {}).get("clips", {})
    hasta = (m or {}).get("hasta")
    if not pr.receta.exists():          # video sin receta de escenas (material grabado, montaje): no hay clips de Flow
        return m, []
    inicio = {r["n"]: r["t0"] for r in pr.escenas()}
    pend = []
    for n, p in clips_disponibles(pr).items():
        if hasta and inicio[int(str(n).split("_")[0])] >= hasta:   # borrador: solo cuenta lo que entra en los primeros segundos
            continue
        u = usados.get(str(n))
        if not u or abs(u["mtime"] - p.stat().st_mtime) > 1 or u["archivo"] != p.name:
            pend.append((n, p.name, "nuevo" if not u else "cambió"))
    return m, pend


def nombre_libre(p):
    """Devuelve la misma ruta si no existe; si existe, la siguiente libre (_2, _3...). Nunca se pisa una entrega."""
    p = Path(p)
    if not p.exists():
        return p
    k = 2
    while (p.with_name(f"{p.stem}_{k}{p.suffix}")).exists():
        k += 1
    return p.with_name(f"{p.stem}_{k}{p.suffix}")


def apartar_anterior(p):
    """Si p existe, lo renombra a <nombre>_anterior-<fecha>.<ext> (queda guardado) y devuelve esa ruta; si no, None."""
    from datetime import datetime as _dt
    p = Path(p)
    if not p.exists():
        return None
    dest = nombre_libre(p.with_name(f"{p.stem}_anterior-{_dt.now():%Y%m%d-%H%M%S}{p.suffix}"))
    p.rename(dest)
    return dest


def es_resto(p):
    """Copias que el estudio guarda o deja a medias (<nombre>_anterior-<fecha>, <nombre>.parcial): nunca cuentan como
    la voz, el video o la entrega vigente."""
    n = Path(p).name
    return "_anterior-" in n or ".parcial" in n


def escribir_entrega(ruta, texto):
    """Escribe un archivo de texto de la entrega (.srt, capítulos, transcripción) sin perder el anterior: si existe y
    cambia, el anterior queda como <nombre>_anterior-<fecha>. Si es igual, no se toca."""
    ruta = Path(ruta)
    if ruta.exists() and ruta.read_text(encoding="utf-8", errors="replace") == texto:
        return None
    guardada = apartar_anterior(ruta)
    ruta.write_text(texto, encoding="utf-8")
    return guardada


def entregar(parcial, final):
    """Cierra una entrega sin pisar la anterior: si `final` existe queda guardado como <nombre>_anterior-<fecha>, y el
    archivo nuevo (escrito antes como .parcial) toma el nombre final. Devuelve la ruta de la anterior o None.
    Si Windows no deja renombrar (el video está abierto en la sala, VLC o CapCut), lo reintenta y si no puede
    se detiene con un mensaje claro: el trabajo nuevo queda a salvo en el .parcial."""
    import time
    parcial, final = Path(parcial), Path(final)
    guardada = None
    for intento in range(5):
        try:
            guardada = apartar_anterior(final) or guardada
            parcial.rename(final)
            break
        except PermissionError:
            if intento == 4:
                if guardada:      # la anterior ya se apartó; lo que no se pudo renombrar es el archivo nuevo
                    sys.exit(f"No pude dejar el archivo nuevo como {final.name}: Windows tiene abierto {parcial.name} "
                             f"(¿un antivirus o un reproductor?). La entrega anterior está guardada como {guardada.name} "
                             f"y la nueva a salvo como {parcial.name}: renómbrala o vuelve a correr el paso.")
                sys.exit(f"No pude cerrar la entrega: {final.name} está abierto en otro programa (sala, VLC, CapCut...). "
                         f"El archivo nuevo quedó a salvo como {parcial.name}. Ciérralo y vuelve a correr el paso.")
            time.sleep(2)
    if guardada:
        print(f"la entrega anterior quedó guardada como {guardada.name}", flush=True)
    return guardada


def parcial_de(final):
    """Nombre temporal para escribir una entrega antes de cerrarla con entregar()."""
    final = Path(final)
    return nombre_libre(final.with_name(final.stem + ".parcial" + final.suffix))


def destino(salida, *entradas):
    """Ruta de salida segura para las herramientas: nunca igual a una entrada y nunca encima de un archivo existente."""
    sal = Path(salida)
    for e in entradas:
        try:
            if e and Path(e).exists() and sal.resolve() == Path(e).resolve():
                sys.exit(f"La salida {sal.name} es el mismo archivo de entrada: elige otro nombre (los originales no se tocan)")
        except OSError:
            pass
    libre = nombre_libre(sal)
    if libre != sal:
        print(f"{sal.name} ya existe; se guarda como {libre.name}", flush=True)
    return libre


def formato_plataformas(p):
    """Lo que piden YouTube, TikTok e Instagram (MP4 + H.264 4:2:0 + AAC-LC 48 kHz estéreo, índice al principio,
    hasta 60 fps). Devuelve la lista de diferencias ([] = ideal) o None si no se pudo leer."""
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries",
                        "stream=codec_type,codec_name,profile,pix_fmt,r_frame_rate,sample_rate,channels:format=format_name",
                        "-of", "json", str(p)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        return None
    try:
        d = json.loads(r.stdout or "{}")
    except ValueError:
        return None
    if not d.get("format"):
        return None
    dif = []
    if Path(p).suffix.lower() != ".mp4" or "mp4" not in d["format"].get("format_name", ""):
        dif.append("no es MP4")
    v = [s for s in d.get("streams", []) if s.get("codec_type") == "video"]
    a = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
    if not v:
        dif.append("sin video")
    for s in v[:1]:
        if s.get("codec_name") != "h264":
            dif.append(f"video {s.get('codec_name')} (piden H.264)")
        if s.get("pix_fmt") != "yuv420p":
            dif.append(f"color {s.get('pix_fmt')} (piden yuv420p)")
        try:
            n, m = s.get("r_frame_rate", "0/1").split("/")
            if float(n) / float(m or 1) > 60.5:
                dif.append(f"{float(n) / float(m or 1):.0f} fps (máximo 60)")
        except ValueError:
            pass
    for s in a[:1]:
        if s.get("codec_name") != "aac" or s.get("profile") not in ("LC", None):
            dif.append(f"audio {s.get('codec_name')} {s.get('profile') or ''} (piden AAC-LC)".replace("  ", " "))
        if str(s.get("sample_rate")) != "48000":
            dif.append(f"audio a {s.get('sample_rate')} Hz (piden 48 kHz)")
        if s.get("channels") != 2:
            dif.append(f"audio con {s.get('channels')} canales (piden estéreo)")
    try:                                                   # índice (moov) antes que los datos (mdat): "fast start"
        with open(p, "rb") as f:
            pos, orden = 0, []
            while len(orden) < 12:
                f.seek(pos); h = f.read(16)
                if len(h) < 8:
                    break
                tam = int.from_bytes(h[:4], "big"); tipo = h[4:8].decode("latin-1")
                if tam == 1:
                    tam = int.from_bytes(h[8:16], "big")
                orden.append(tipo)
                if tam < 8:
                    break
                pos += tam
            if "moov" in orden and "mdat" in orden and orden.index("moov") > orden.index("mdat"):
                dif.append("el índice va al final (falta fast start)")
    except OSError:
        return None
    return dif


if __name__ == "__main__":
    # python estudio.py metadatos "<archivo o carpeta>"   revisa videos y audios hechos fuera del flujo normal
    # (exportes de CapCut, doblajes, montajes): ✓ limpio · ✗ quedan etiquetas · ? no se pudo leer. Solo lee.
    if len(sys.argv) >= 3 and sys.argv[1] == "metadatos":
        ruta = Path(sys.argv[2])
        archivos = [ruta] if ruta.is_file() else sorted(p for p in ruta.rglob("*") if p.suffix.lower() in
                                                         (".mp4", ".mov", ".m4v", ".m4a", ".wav", ".mp3", ".mkv", ".webm"))
        malos = 0
        for p in archivos:
            m = metadatos_personales(p)
            malos += m is None or bool(m)
            print(("?" if m is None else ("✗" if m else "✓")), p, "" if not m else ", ".join(m), flush=True)
        print(f"{len(archivos)} archivos; {malos} para revisar")
        sys.exit(1 if malos or not archivos else 0)
    if len(sys.argv) >= 3 and sys.argv[1] == "formato":
        ruta = Path(sys.argv[2])
        archivos = [ruta] if ruta.is_file() else sorted(ruta.rglob("*.mp4"))
        malos = 0
        for p in archivos:
            d = formato_plataformas(p)
            malos += d is None or bool(d)
            print(("?" if d is None else ("✗" if d else "✓")), p, "" if not d else "; ".join(d), flush=True)
        print(f"{len(archivos)} videos; {malos} con diferencias")
        sys.exit(1 if malos or not archivos else 0)
    sys.exit('Uso: python estudio.py metadatos|formato "<archivo o carpeta>"')
