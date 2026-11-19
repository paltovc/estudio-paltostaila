import re
# Piezas comunes del gerente de canales: rutas, configuración, JSON seguro, bloqueos, huellas y registro.
# Todo vive en %USERPROFILE%\EstudioPaltostaila\gerente (o en ESTUDIO_BASE\gerente para pruebas).
import contextlib, csv, datetime as dt, hashlib, json, os, shutil, sys, time, uuid
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Windows con salida a un log usa cp1252: sin esto ✓ ✗ → hacen caer el script
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VERSION = (Path(__file__).with_name("VERSION").read_text(encoding="utf-8").strip()
           if Path(__file__).with_name("VERSION").exists() else "0.0.0")
BASE = Path(os.environ.get("ESTUDIO_BASE", Path.home() / "EstudioPaltostaila"))
GER = BASE / "gerente"
TMP = GER / "tmp"
CLAVES = BASE / "claves"
CONFIG = GER / "config.json"
CALENDARIO = GER / "calendario.json"
APROBACIONES = GER / "aprobaciones.json"
REGISTRO = GER / "registro_publicaciones.csv"
REDES = ("youtube", "tiktok", "instagram")
RUTAS = ("api", "metricool", "vidiq", "manual")
ESTADOS = ("por_aprobar", "aprobado", "en_curso", "incierto", "subido_privado", "programado", "publicado",
           "medido_48h", "medido_7d", "cancelado", "error")
# Estados que bloquean un segundo envío. «incierto» = no se sabe si la plataforma recibió el video: bloquea hasta
# revisarlo en la plataforma y anotarlo (cancelado o error) a mano.
ENVIADO = ("en_curso", "incierto", "subido_privado", "programado", "publicado")
MEDICION = ("medido_48h", "medido_7d")   # anotar una medición no cambia el estado de publicación

CONFIG_INICIAL = {
    "version": 1,
    "nivel": 2,  # 0 solo paquete · 1 sube privado a YouTube · 2 programa lo aprobado en todas las redes
    "zona": "America/Santiago",
    "zonas_publico": ["America/Mexico_City", "America/Bogota", "America/Argentina/Buenos_Aires",
                      "Europe/Madrid", "Australia/Sydney", "Pacific/Auckland"],
    "youtube": {"categoria": "27", "idioma": "es", "notificar": True},
    "metricool": {"plan": "free", "limite_mes": 20, "blog_id": ""},
    "vidiq": {"creditos_mes_autorizados": 0},
    "exigir_evaluacion_shorts": True,
    "minutos_minimos_antes": 30,
}


def ahora_utc():
    return dt.datetime.now(dt.timezone.utc)


def leer_json(p, defecto=None):
    p = Path(p)
    if not p.exists():
        return defecto
    return json.loads(p.read_text(encoding="utf-8-sig"))  # acepta el BOM que deja el Bloc de notas


@contextlib.contextmanager
def bloqueo(nombre, espera=30, vencido=600):
    """Bloqueo entre procesos con un archivo creado en exclusiva y una marca de dueño: al salir solo se borra si sigue
    siendo propio. Un bloqueo de más de `vencido` s se considera abandonado (proceso caído) y se recupera."""
    TMP.mkdir(parents=True, exist_ok=True)
    f = TMP / f"{nombre}.lock"
    marca = f"{os.getpid()} {uuid.uuid4().hex}"
    t0 = time.time()
    while True:
        try:
            fd = os.open(f, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, marca.encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                viejo = time.time() - f.stat().st_mtime > vencido
            except FileNotFoundError:
                continue
            if viejo:
                abandonado = f.with_name(f"{f.name}.{uuid.uuid4().hex[:8]}.abandonado")
                try:
                    os.replace(f, abandonado)   # se aparta (no se borra a ciegas) y se reintenta
                except OSError:
                    pass
                continue
            if time.time() - t0 > espera:
                sys.exit(f"Otro proceso está usando {nombre} (bloqueo {f}). Esperar o revisar.")
            time.sleep(0.3)
    try:
        yield
    finally:
        try:
            if f.read_text(encoding="utf-8") == marca:
                f.unlink()
        except OSError:
            pass


def escribir_estado(p, datos):
    """Escribe un archivo de estado del gerente: respaldo con nombre único y reemplazo atómico (con reintentos
    por si OneDrive o el antivirus lo tienen abierto). Nunca se usa sobre originales de un video."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        resp = p.parent / "respaldos"
        resp.mkdir(exist_ok=True)
        shutil.copy2(p, resp / f"{p.stem}_{ahora_utc():%Y%m%dT%H%M%S%f}_{uuid.uuid4().hex[:6]}{p.suffix}")
    tmp = p.with_name(f"{p.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    for i in range(10):
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            time.sleep(0.5 * (i + 1))
    sys.exit(f"No pude reemplazar {p} (¿abierto en otro programa?). Quedó la versión nueva en {tmp}.")


def escribir_nuevo(p, texto):
    """Archivo nuevo dentro de la carpeta de un video: si el nombre existe, agrega _2, _3... Nunca pisa."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    destino, n = p, 2
    while True:
        try:
            with open(destino, "x", encoding="utf-8") as f:
                f.write(texto)
            return destino
        except FileExistsError:
            destino = p.with_name(f"{p.stem}_{n}{p.suffix}")
            n += 1


def config():
    c = leer_json(CONFIG)
    if c is None:
        c = json.loads(json.dumps(CONFIG_INICIAL))
        escribir_estado(CONFIG, c)
    for k, v in CONFIG_INICIAL.items():
        c.setdefault(k, v)
    return c


def nivel(cfg):
    """Nivel válido (0, 1 o 2) o None. El 3 no se usa: se trata como inválido y cierra las puertas."""
    n = cfg.get("nivel")
    return n if isinstance(n, int) and not isinstance(n, bool) and n in (0, 1, 2) else None


def huella(p, bloque=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(bloque), b""):
            h.update(b)
    return h.hexdigest()


def ruta_segura(pdir, rel):
    """Ruta de un archivo del proyecto; None si sale de la carpeta del proyecto (absoluta o con ..)."""
    if not rel:
        return None
    pdir = Path(pdir).resolve()
    q = (pdir / rel).resolve()
    try:
        q.relative_to(pdir)
    except ValueError:
        return None
    return q


def contexto(pub, cfg):
    """Lo que no está en la pieza pero cambia lo que se envía: canal del proyecto, canal de YouTube conectado y los
    valores de YouTube que se heredan de la configuración. Entra en la huella de la aprobación."""
    yc = cfg.get("youtube", {})
    return {"canal": pub.get("canal"), "youtube_canal_id": yc.get("canal_id", ""), "idioma": yc.get("idioma", "es"),
            "categoria": str(yc.get("categoria", "27")), "notificar": bool(yc.get("notificar", True))}


def huella_pieza(pdir, x, reemplazos=None, ctx=None):
    """Huella de TODO lo que se aprueba de una pieza: metadatos, destinos y fechas, el contenido del video, la miniatura
    y los subtítulos, y el contexto (canal y valores heredados). Si cambia cualquier cosa, hay que aprobar de nuevo.
    No incluye enlace_publico (se verifica aparte contra el contenido del video)."""
    reemplazos = reemplazos or {}
    d = json.loads(json.dumps(x))
    d["_contexto"] = ctx or {}
    for dd in d.get("destinos", []):
        dd.pop("enlace_publico", None)
    for campo in ("archivo", "miniatura", "subtitulos"):
        if x.get(campo):
            q = reemplazos.get(campo) or ruta_segura(pdir, x[campo])
            d[f"_sha_{campo}"] = huella(q) if q and Path(q).is_file() else "FALTA"
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


CAMPOS_REGISTRO = ["fecha_utc", "proyecto", "id", "version", "pieza", "red", "ruta", "estado", "sha256",
                   "fecha_publicacion", "zona", "enlace", "nota", "gerente"]


def registrar(**fila):
    """Agrega una fila al registro (nunca se borra). Falla temprano si el archivo está bloqueado (p. ej. abierto en Excel)."""
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    fila = {k: fila.get(k, "") for k in CAMPOS_REGISTRO}
    fila["fecha_utc"] = ahora_utc().isoformat(timespec="seconds")
    fila["gerente"] = VERSION
    with bloqueo("registro"):
        vacio = not REGISTRO.exists() or REGISTRO.stat().st_size == 0
        try:
            with open(REGISTRO, "a", newline="", encoding="utf-8-sig" if vacio else "utf-8") as f:
                w = csv.DictWriter(f, fieldnames=CAMPOS_REGISTRO)
                if vacio:
                    w.writeheader()
                w.writerow(fila)
        except PermissionError:
            sys.exit(f"No puedo escribir {REGISTRO}: ¿está abierto en Excel? Cerrarlo y repetir.")


def registro():
    if not REGISTRO.exists() or REGISTRO.stat().st_size == 0:
        return []
    with open(REGISTRO, newline="", encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    if filas and "sha256" not in filas[0]:
        sys.exit(f"{REGISTRO} perdió sus columnas (¿se guardó desde Excel?). Recuperar el respaldo; no editarlo a mano.")
    return filas


def ultimo_estado(clave_fn, filas=None):
    """Último estado de PUBLICACIÓN por clave (el registro solo agrega filas: manda la más reciente; las filas de
    medición no cuentan, para que anotar «medido_48h» no haga olvidar que el video está publicado)."""
    u = {}
    for r in (registro() if filas is None else filas):
        if r["estado"] in MEDICION:
            continue
        u[clave_fn(r)] = r
    return u


def ya_enviado(sha, red, id_=None, pieza_=None):
    """Motivos para NO enviar: el mismo archivo ya va a esa red, u otra versión de la misma pieza ya va a esa red.
    Para reemplazar una versión, primero se cancela la anterior en la plataforma y se anota «cancelado»."""
    motivos = []
    filas = registro()
    por_sha = ultimo_estado(lambda r: (r["sha256"], r["red"]), filas)
    r = por_sha.get((sha, red))
    if r and r["estado"] in ENVIADO:
        motivos.append(f"este mismo archivo ya está {r['estado']} en {red}: {r['enlace'] or 'sin enlace'}")
    if id_ and pieza_:
        por_pieza = ultimo_estado(lambda r: (r["id"], r["version"], r["pieza"], r["red"], r["sha256"]), filas)
        for (i, v, pz, rd, sh), fila in por_pieza.items():
            if i == id_ and pz == pieza_ and rd == red and fila["estado"] in ENVIADO and sh != sha:
                motivos.append(f"otra versión ({v}) de {pieza_} ya está {fila['estado']} en {red} ({fila['enlace'] or 'sin enlace'}): "
                               "para reemplazarla, primero cancelarla (con el sí de Patricio) y anotarla como cancelada")
    return motivos


def diario(**datos):
    """Diario de operaciones: un archivo nuevo por evento, escrito antes que el CSV (si el CSV falla, queda esto)."""
    d = GER / "diario"
    d.mkdir(parents=True, exist_ok=True)
    datos["utc"] = ahora_utc().isoformat(timespec="seconds")
    nombre = f"{ahora_utc():%Y%m%dT%H%M%S}_{datos.get('id', '')}_{datos.get('pieza', '')}_{datos.get('red', '')}_{datos.get('estado', '')}.json"
    return escribir_nuevo(d / nombre, json.dumps(datos, ensure_ascii=False, indent=1))


def opt(args, k, defecto=None):
    if k not in args:
        return defecto
    i = args.index(k)
    if i + 1 >= len(args) or args[i + 1].startswith("--"):
        sys.exit(f"Falta el valor de {k}")
    return args[i + 1]


def carpeta_publicar(pdir):
    """Carpeta de publicación del proyecto, leída igual que el motor (estudio.py): "carpetas" → "publicar" en
    proyecto.json; si no existe esa clave (o no hay proyecto.json), 08_PUBLICAR. Una clave "publicar" en la raíz
    NO se lee: el motor tampoco la lee. Si carpetas.publicar existe pero no es una carpeta directa del proyecto
    (vacía, con barras, «..», «.», espacios al inicio o al final) el gerente se detiene: nunca vuelve en silencio
    a 08_PUBLICAR, donde podría quedar un paquete de otra versión."""
    pdir = Path(pdir)
    try:
        d = leer_json(pdir / "proyecto.json")
    except Exception:
        d = None    # ilegible: el motor no puede haber armado nada con él; queda la de siempre
    if not isinstance(d, dict) or "carpetas" not in d:
        return pdir / "08_PUBLICAR"
    c = d["carpetas"]
    if not isinstance(c, dict):
        sys.exit(f"proyecto.json de {pdir.name}: «carpetas» no es una lista de carpetas con nombre; corregirlo antes de publicar")
    if "publicar" not in c:
        return pdir / "08_PUBLICAR"
    n = c["publicar"]
    if not (isinstance(n, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_ .-]*", n) and ".." not in n
            and not n.endswith((" ", "."))):
        sys.exit(f"proyecto.json de {pdir.name}: carpetas.publicar = {n!r} no es una carpeta directa del proyecto "
                 "(sin barras, «..» ni espacios al final). El gerente no adivina la carpeta: corregirlo y repetir")
    return pdir / n


def proyecto_dir(arg):
    p = Path(arg).expanduser()
    if not p.is_dir():
        sys.exit(f"No encuentro la carpeta del proyecto: {p}")
    return p.resolve()


def publicacion(pdir):
    p = carpeta_publicar(pdir) / "publicacion.json"
    d = leer_json(p)
    if d is None:
        sys.exit(f"Falta {p} (lo escribe el distribuidor a partir del paquete del publicador).")
    return d


def pieza(pub, clave):
    for x in pub.get("piezas", []):
        if x.get("clave") == clave:
            return x
    sys.exit(f"No hay pieza «{clave}» en publicacion.json")


def a_utc(fecha_local, zona):
    """Fecha local «AAAA-MM-DDTHH:MM» de la zona IANA → instante UTC. Rechaza fechas con desfase escrito (para que no
    contradigan la zona) y las horas que no existen o se repiten por el cambio de hora."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        z = ZoneInfo(zona)
    except ZoneInfoNotFoundError:
        try:
            import tzdata  # noqa: F401
        except ImportError:
            raise ValueError("falta el paquete tzdata (python -m pip install tzdata)")
        raise ValueError(f"zona desconocida {zona}")
    f = dt.datetime.fromisoformat(fecha_local)
    if f.tzinfo is not None:
        raise ValueError("la fecha no debe llevar desfase (+00:00): se escribe en hora local y la zona va aparte")
    a, b = f.replace(tzinfo=z, fold=0), f.replace(tzinfo=z, fold=1)
    u = a.astimezone(dt.timezone.utc)
    if u.astimezone(z).replace(tzinfo=None) != f:
        raise ValueError(f"{fecha_local} no existe en {zona} (cambio de hora): elegir otra hora")
    if a.utcoffset() != b.utcoffset():
        raise ValueError(f"{fecha_local} se repite en {zona} por el cambio de hora: elegir otra hora")
    return u


def p(*a):
    print(*a, flush=True)
