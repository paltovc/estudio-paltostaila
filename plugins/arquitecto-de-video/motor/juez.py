# El juez del estudio: revisa en SOLO LECTURA lo que puede salir mal en cualquier punto del proceso y entrega un informe.
# No arregla nada, no borra nada y no publica nada. Lo que encuentra lo decide la persona.
#   python juez.py todo [carpeta extra ...]   las tres revisiones; informe en trabajo\juez\juez_<fecha>.md (nombre nuevo)
#   python juez.py secretos [carpeta ...]     claves, tokens o contraseñas fuera de claves\ (también en logs y tmp)
#   python juez.py originales                 operaciones del motor y del gerente que borran, mueven o pisan archivos
#   python juez.py estado                     versiones, repositorio, envíos inciertos, nivel y presupuesto de créditos
#   python juez.py permitir <id> --por "<quién>" --motivo "<por qué>"
#        marca un hallazgo como revisado y aceptado (solo con el sí de la persona); deja de salir en las rondas
# Cada hallazgo tiene un id estable (archivo + texto de la línea): si la línea cambia, vuelve a salir.
import argparse, csv, datetime as dt, hashlib, json, os, re, subprocess, sys
from pathlib import Path

BASE = Path(os.environ.get("ESTUDIO_BASE") or Path.home() / "EstudioPaltostaila")
ESTADO = BASE / "juez"
PERMITIDOS = ESTADO / "permitidos.json"
TEXTO = {".py", ".md", ".json", ".txt", ".log", ".env", ".cmd", ".bat", ".ps1", ".csv", ".html", ".js", ".yml",
         ".yaml", ".ini", ".cfg", ".toml", ".srt", ".ass", ".xml"}
SALTAR = {"claves", "modelos", "sonidos", "voces", "__pycache__", ".git", "node_modules", "juez"}
MAX_BYTES = 3_000_000

SECRETOS = [  # (nombre, patrón, gravedad)
    ("clave de API de Google", r"AIza[0-9A-Za-z_\-]{35}", "alta"),
    ("token de acceso de Google", r"ya29\.[0-9A-Za-z_\-]{20,}", "alta"),
    ("token de renovación de Google", r"1//0[0-9A-Za-z_\-]{20,}", "alta"),
    ("secreto de cliente OAuth", r"\"client_secret\"\s*:\s*\"[^\"]{8,}\"", "alta"),
    ("llave privada", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "alta"),
    ("token de GitHub", r"\b(?:gh[pousr]_[0-9A-Za-z]{30,}|github_pat_[0-9A-Za-z_]{40,})", "alta"),
    ("clave tipo sk- (OpenAI, Anthropic u otra)", r"\bsk-(?:ant-)?[A-Za-z0-9_\-]{24,}", "alta"),
    ("posible contraseña escrita", r"(?i)\b(?:password|passwd|contraseña|contrasena)\s*[:=]\s*[\"']?[^\s\"']{6,}", "media"),
]
PELIGROS = [  # operaciones que pueden borrar, mover o pisar archivos
    ("borra un archivo", r"\.unlink\(|\bos\.remove\(|\bos\.unlink\("),
    ("borra una carpeta entera", r"shutil\.rmtree\(|\.rmdir\("),
    ("mueve o renombra", r"shutil\.move\(|\bos\.rename\(|\bos\.replace\(|\.rename\("),
    ("ffmpeg pisa la salida sin preguntar (-y)", r"[\"']-y[\"']"),
    ("copia encima de un destino", r"shutil\.copy(?:file|2)?\("),
    ("guarda una imagen o un audio (revisar que el nombre sea nuevo)", r"\.save\(|cv2\.imwrite\("),
    ("escribe un archivo de texto (revisar que no sea de la persona)", r"\.write_(?:text|bytes)\(|open\([^)]*[\"'][wa]b?[\"']"),
]


def _id(*partes):
    return hashlib.sha1("|".join(partes).encode("utf-8", "replace")).hexdigest()[:12]


def permitidos():
    try:
        return {p["id"] for p in json.loads(PERMITIDOS.read_text(encoding="utf-8"))}
    except Exception:
        return set()


def _textos(raiz):
    raiz = Path(raiz)
    if raiz.is_file():
        yield raiz
        return
    for dirpath, dirs, files in os.walk(raiz):
        dirs[:] = [d for d in dirs if d not in SALTAR and not d.startswith("motor_")]
        for f in files:
            p = Path(dirpath) / f
            if p.suffix.lower() in TEXTO or f.lower() == ".env":
                try:
                    if p.stat().st_size <= MAX_BYTES:
                        yield p
                except OSError:
                    pass


def _tapar(s):
    return s[:4] + "…" + f"({len(s)} caracteres)"


def secretos(raices=None):
    raices = [Path(r) for r in (raices or [BASE])]
    out = []
    for raiz in raices:
        for p in _textos(raiz):
            try:
                lineas = p.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for n, l in enumerate(lineas, 1):
                for nombre, pat, grav in SECRETOS:
                    m = re.search(pat, l)
                    if m:
                        out.append({"id": _id("secreto", str(p), l.strip()), "gravedad": grav, "tipo": nombre,
                                    "donde": f"{p}:{n}", "detalle": _tapar(m.group(0))})
    return out


def originales():
    out = []
    for carpeta in (BASE / "motor", BASE / "gerente"):
        if not carpeta.exists():
            continue
        for p in sorted(carpeta.glob("*.py")):
            if p.name in ("prueba.py", "prueba_gerente.py", "juez.py"):
                continue          # las pruebas trabajan en carpetas temporales propias
            lineas = p.read_text(encoding="utf-8", errors="replace").splitlines()
            vistas = {}
            for n, l in enumerate(lineas, 1):
                if l.lstrip().startswith("#"):
                    continue
                cae = [nombre for nombre, pat in PELIGROS if re.search(pat, l)
                       and not (nombre.startswith("escribe") and re.search(r"\b(?:tmp|TMP)\b", l))]   # escribir en tmp no toca nada de la persona
                for nombre, pat in PELIGROS:
                    if nombre in cae:
                        # la segunda vez que aparece la misma línea en el archivo lleva su propio id: aceptar una no acepta la otra
                        k = vistas[(nombre, l.strip())] = vistas.get((nombre, l.strip()), 0) + 1
                        # si la línea cae en más de un patrón, cada uno lleva su id (aceptar uno no acepta el otro);
                        # el número de aparición depende del orden: una línea igual agregada ANTES corre los números
                        partes = (("peligro", p.name, l.strip()) + ((f"#{k}",) if k > 1 else ())
                                  + ((nombre,) if len(cae) > 1 and nombre != cae[0] else ()))
                        out.append({"id": _id(*partes), "gravedad": "baja" if nombre.startswith(("guarda", "escribe")) else "media",
                                    "tipo": nombre, "donde": f"{p}:{n}", "detalle": l.strip()[:160]})
    return out


def _version(p):
    try:
        return Path(p).read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", timeout=60)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def gitleaks():
    """Ruta de gitleaks: en el PATH o donde lo deja winget (una consola abierta antes de instalarlo no lo ve en el PATH)."""
    import shutil
    if shutil.which("gitleaks"):
        return shutil.which("gitleaks")
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet"
    for p in [base / "Links" / "gitleaks.exe", *sorted((base / "Packages").glob("Gitleaks.Gitleaks*/gitleaks.exe"))]:
        if p.exists():
            return str(p)
    return None


def estado():
    out = []
    def hall(grav, tipo, donde, detalle):
        out.append({"id": _id("estado", tipo, donde, detalle), "gravedad": grav, "tipo": tipo, "donde": donde, "detalle": detalle})
    repo = BASE / "repo" / "estudio-paltostaila"
    vers = {"motor instalado": _version(BASE / "motor" / "VERSION"),
            "motor en el repositorio": _version(repo / "plugins" / "arquitecto-de-video" / "motor" / "VERSION"),
            "gerente instalado": _version(BASE / "gerente" / "VERSION"),
            "gerente en el repositorio": _version(repo / "plugins" / "gerente-de-canales" / "scripts" / "VERSION")}
    for k, v in vers.items():
        hall("info", "versión", k, v or "no encontrada")
    if vers["motor instalado"] and vers["motor en el repositorio"] and vers["motor instalado"] != vers["motor en el repositorio"]:
        hall("media", "motor distinto al del repositorio", str(repo),
             f"instalado {vers['motor instalado']} y publicado {vers['motor en el repositorio']}: publicar o anotar por qué")
    if repo.exists():
        sucio = _git(repo, "status", "--porcelain")
        if sucio:
            hall("media", "repositorio con cambios sin guardar", str(repo), f"{len(sucio.splitlines())} archivos")
        gi = repo / ".gitignore"
        reglas = gi.read_text(encoding="utf-8", errors="replace") if gi.exists() else ""
        for r in ("claves/", "*.env", "*token*.json"):
            if r not in reglas:
                hall("alta" if r == "claves/" else "media", ".gitignore incompleto", str(gi), f"falta la regla {r}")
        if (repo / "claves").exists():
            hall("alta", "carpeta claves dentro del repositorio", str(repo / "claves"), "sacarla del repositorio")
        hook = repo / ".git" / "hooks" / "pre-commit"
        if not hook.exists() or "gitleaks" not in hook.read_text(encoding="utf-8", errors="replace"):
            hall("media", "sin control de secretos al guardar", str(hook), "falta el gancho pre-commit con gitleaks")
    else:
        hall("baja", "repositorio no encontrado", str(repo), "")
    gl = gitleaks()
    if gl:
        try:
            r = subprocess.run([gl, "version"], capture_output=True, text=True, timeout=30)
            hall("info", "gitleaks", gl, r.stdout.strip() or "instalado")
        except Exception as e:
            hall("media", "gitleaks no responde", gl, str(e))
    else:
        hall("media", "gitleaks no instalado", "PATH y WinGet", "sin escaneo de secretos del historial del repositorio")
    cfg_p = BASE / "gerente" / "config.json"
    if cfg_p.exists():
        try:
            cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
            nivel = cfg.get("nivel")
            hall("info", "nivel de autonomía del gerente", str(cfg_p), str(nivel))
            if nivel not in (0, 1, 2):
                hall("alta", "nivel de autonomía inválido", str(cfg_p), repr(nivel))
            cred = (cfg.get("vidiq") or {}).get("creditos_mes_autorizados")
            if cred not in (0, None):
                hall("media", "presupuesto de créditos de vidIQ distinto de 0", str(cfg_p), f"{cred}: confirmar que Patricio lo autorizó")
        except Exception as e:
            hall("alta", "config del gerente ilegible", str(cfg_p), str(e))
    reg = BASE / "gerente" / "registro_publicaciones.csv"
    if reg.exists():
        ultimo = {}
        try:
            with open(reg, encoding="utf-8-sig", newline="") as f:
                for fila in csv.DictReader(f):
                    if fila.get("estado", "").startswith("medido"):
                        continue
                    ultimo[(fila.get("id"), fila.get("version"), fila.get("pieza"), fila.get("red"))] = fila
        except Exception as e:
            hall("alta", "registro de publicaciones ilegible", str(reg), str(e))
        for k, fila in ultimo.items():
            if fila.get("estado") in ("incierto", "en_curso"):
                hall("alta", f"envío {fila['estado']}", str(reg), "_".join(x or "" for x in k) + ": mirarlo en la plataforma y anotarlo")
    for v in sorted((BASE / "tmp").glob("*.log"))[-40:] if (BASE / "tmp").exists() else []:
        try:
            t = v.read_text(encoding="utf-8", errors="replace")[-4000:]
        except OSError:
            continue
        if re.search(r"Traceback \(most recent call last\)", t):
            hall("baja", "un log reciente terminó con error", str(v), "revisar si quedó algo a medias")
    return out


def informe(grupos, carpeta=None):
    ok = permitidos()
    hoy = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    L = [f"# Juez del estudio — {hoy}", "",
         "Revisión en solo lectura. Lo marcado ALTA se corrige antes de publicar o de seguir; lo MEDIA se decide; "
         "lo aceptado se registra con `juez.py permitir`.", ""]
    total = {"alta": 0, "media": 0, "baja": 0}
    for titulo, hall in grupos:
        nuevos = [h for h in hall if h["id"] not in ok]
        L += [f"## {titulo}", ""]
        if not nuevos:
            L += ["Sin hallazgos nuevos.", ""]
            continue
        L += ["| id | gravedad | qué | dónde | detalle |", "|---|---|---|---|---|"]
        for h in sorted(nuevos, key=lambda h: ("alta", "media", "baja", "info").index(h["gravedad"])):
            total[h["gravedad"]] = total.get(h["gravedad"], 0) + 1
            det = str(h["detalle"]).replace("|", "\\|")
            L.append(f"| {h['id']} | {h['gravedad']} | {h['tipo']} | `{h['donde']}` | {det} |")
        L.append("")
    L.insert(4, f"**Resumen:** {total['alta']} altas · {total['media']} medias · {total['baja']} bajas.\n")
    carpeta = Path(carpeta or BASE / "trabajo" / "juez")
    carpeta.mkdir(parents=True, exist_ok=True)
    sal = carpeta / f"juez_{dt.datetime.now().strftime('%Y-%m-%d')}.md"
    k = 2
    while sal.exists():
        sal = carpeta / f"juez_{dt.datetime.now().strftime('%Y-%m-%d')}_{k}.md"
        k += 1
    sal.write_text("\n".join(L) + "\n", encoding="utf-8")
    return sal, total


def permitir(id_, por, motivo):
    if not por or not motivo:
        sys.exit("Falta --por y --motivo: un hallazgo se acepta solo con el sí de la persona y con su razón.")
    ESTADO.mkdir(parents=True, exist_ok=True)
    try:
        lista = json.loads(PERMITIDOS.read_text(encoding="utf-8"))
    except Exception:
        lista = []
    if any(p["id"] == id_ for p in lista):
        print("Ya estaba aceptado:", id_)
        return
    lista.append({"id": id_, "por": por, "motivo": motivo, "fecha": dt.date.today().isoformat()})
    tmp = PERMITIDOS.with_suffix(".tmp")
    tmp.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, PERMITIDOS)
    print("ACEPTADO", id_, "por", por)


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Juez del estudio (solo lectura)")
    ap.add_argument("accion", choices=["todo", "secretos", "originales", "estado", "permitir"])
    ap.add_argument("extra", nargs="*")
    ap.add_argument("--por")
    ap.add_argument("--motivo")
    ap.add_argument("--salida", help="carpeta del informe (por defecto trabajo\\juez)")
    a = ap.parse_args()
    if a.accion == "permitir":
        if len(a.extra) != 1:
            sys.exit("Uso: juez.py permitir <id> --por \"<quién>\" --motivo \"<por qué>\"")
        return permitir(a.extra[0], a.por, a.motivo)
    grupos = []
    if a.accion in ("todo", "secretos"):
        grupos.append(("Claves y secretos fuera de claves\\", secretos([BASE] + a.extra)))
    if a.accion in ("todo", "originales"):
        grupos.append(("Operaciones que borran, mueven o pisan archivos (motor y gerente)", originales()))
    if a.accion in ("todo", "estado"):
        grupos.append(("Estado del estudio", estado()))
    sal, total = informe(grupos, a.salida)
    print(f"JUEZ: {total['alta']} altas, {total['media']} medias, {total['baja']} bajas · informe: {sal}", flush=True)


if __name__ == "__main__":
    main()
