from comun import carpeta_publicar
# Puertas antes de subir o programar: si una falla, no se publica nada.
#   python puertas.py "<proyecto>" --pieza <clave> [--red youtube|tiktok|instagram]
# Revisa: publicacion.json válido · nivel · terminado.py con los puntos obligatorios en ✓ y con la HUELLA del archivo
# que se sube (terminado_<base>.json) · checklist de monetización DE ESTA VERSIÓN con «MONETIZACIÓN: OK» · evaluación
# con nota 8 o más (7 en los Shorts), clase A o B y la huella del video evaluado · aprobación vigente con la huella de la pieza completa y su contexto (y posterior a cualquier cancelación) ·
# fecha futura · que no se haya enviado antes · enlace público con el mismo contenido y cupo (Metricool) ·
# ventana horaria y Short ya público (vidIQ). Termina con 0 solo si todo pasa.
import datetime as dt, re, sys
from pathlib import Path
from comun import (APROBACIONES, a_utc, ahora_utc, config, contexto, huella, huella_pieza, leer_json, nivel, opt, p,
                   proyecto_dir, registro, ruta_segura, ultimo_estado, ya_enviado)
from validar import validar

OBLIGATORIOS = {"1", "2", "3", "4", "5", "6", "11"}   # obligatorios de terminado.py (11 = sin GPS ni datos del celular)
NOTA_LARGO, NOTA_SHORT = 8, 7                    # decisión de Patricio (15-11-2026): fijas, no se leen de config.json
VENTANA_VIDIQ = (-10, 60)                        # minutos alrededor de la hora: vidIQ publica en el momento


def carpetas_render(pdir):
    return [d for d in Path(pdir).iterdir() if d.is_dir() and d.name.upper().startswith("07_RENDER")]


def _exacto(carpetas, nombres):
    xs = [d / n for d in carpetas for n in nombres if (d / n).is_file()]
    return max(xs, key=lambda q: q.stat().st_mtime) if xs else None


def revisar_terminado(pdir, id_, ver, archivos):
    """Devuelve (ok, detalle, huellas, carpeta). Desde la 0.1.4 el «terminado» tiene que ser de ESTOS archivos:
    terminado.py (motor 0.14) deja terminado_<base>.json con el sha256 de cada video que revisó. El archivo que se
    sube tiene que estar ahí, con la misma huella. La fecha no cuenta: sin ese .json la puerta queda cerrada."""
    t = _exacto(carpetas_render(pdir), [f"terminado_{id_}_{ver}.md"])
    if not t:
        return False, f"falta terminado_{id_}_{ver}.md en 07_RENDER* (correr terminado.py del estudio)", {}, None
    texto = t.read_text(encoding="utf-8-sig")
    malos, vistos = [], set()
    for l in texto.splitlines():
        s = l.strip()
        if not s.startswith("|") or s.startswith("|---") or s.startswith("| #"):
            continue
        m = re.match(r"\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(\S*)\s*\|", s)
        if not m:
            malos.append(f"fila no reconocida: {s[:40]}")
            continue
        vistos.add(m.group(1))
        if "(recomendado)" not in m.group(2) and m.group(3) != "✓":
            malos.append(f"{m.group(1)} {m.group(2)} [{m.group(3) or 'vacío'}]")
    faltan = OBLIGATORIOS - vistos
    if faltan:
        malos.append(f"faltan los puntos obligatorios {', '.join(sorted(faltan, key=int))}")
    if "SÍ: lo obligatorio pasa" not in texto:
        malos.append("el resumen no dice «SÍ: lo obligatorio pasa»")
    tj = t.with_suffix(".json")
    try:
        hj = leer_json(tj)["videos"] if tj.is_file() else None
    except Exception:
        hj = None
    if not isinstance(hj, dict) or not hj:
        hj = {}
        malos.append(f"falta {tj.name} con las huellas de los videos revisados (terminado anterior al motor 0.14, o "
                     "ilegible): correr terminado.py otra vez")
    else:
        for a in archivos:
            if not a or not a.is_file():
                continue
            try:
                rel = a.resolve().relative_to(t.parent.resolve()).as_posix()
            except ValueError:
                rel = None
            if (rel is not None and rel.lower().startswith("celu/")) or "_celu" in a.name.lower():
                malos.append(f"{a.name} es la copia para el celular: se sube el video de la carpeta de render, no el de celu")
            elif rel is None or rel not in hj:
                malos.append(f"{a.name} no es uno de los videos que revisó terminado.py ({t.name})")
            elif huella(a) != hj[rel]:
                malos.append(f"{a.name} cambió después de terminado.py: correr terminado.py otra vez")
    return (not malos), (f"{t.name} (huella del video comprobada)" if not malos else "; ".join(malos)), hj, t.parent


def revisar_evaluacion(pdir, nombres, archivo, sellados=None, carpeta=None, nota_minima=8):
    """La evaluación tiene que ser de ESTE video, comprobado por huella (evaluar.py la guarda desde el motor 0.14; una
    evaluación sin huella no vale). Si se evaluó el hermano con subtítulos, ese hermano tiene que estar en la misma
    corrida de terminado.py que el archivo que se sube. Nota mínima: 8 el largo (igual que el motor) y 7 los Shorts; clase A o B."""
    e = _exacto([Path(pdir) / "06_RECETA"], [f"evaluacion_{n}.json" for n in nombres])
    if not e:
        return False, f"falta 06_RECETA/evaluacion_{nombres[0]}.json (correr evaluar.py sobre ese video)"
    try:
        d = leer_json(e)
        if not isinstance(d, dict):
            raise ValueError("no es un objeto")
    except Exception:
        return False, f"{e.name} no se puede leer: evaluar otra vez"
    evaluado = Path(str(d["video"]).replace("\\", "/")).stem if d.get("video") else None
    if evaluado and evaluado not in nombres:
        return False, f"{e.name} evaluó otro video ({Path(str(d['video']).replace(chr(92), '/')).name})"
    if not d.get("sha256"):
        return False, f"{e.name} no trae la huella del video evaluado (evaluación anterior al motor 0.14): evaluar otra vez"
    if evaluado in (None, archivo.stem):
        real = archivo
    else:                                       # se evaluó el hermano con subtítulos
        real = (Path(carpeta) if carpeta else archivo.parent) / (evaluado + archivo.suffix)
        if not real.is_file():
            return False, f"{e.name} evaluó {real.name}, que ya no está junto al terminado: evaluar otra vez"
    if huella(real) != d["sha256"]:
        return False, f"{real.name} cambió después de la evaluación ({e.name}): evaluar otra vez"
    junto = ""
    if real != archivo:
        if (sellados or {}).get(real.name) != d["sha256"]:
            return False, (f"{real.name} (el evaluado) no está entre los videos que revisó terminado.py junto con "
                           f"{archivo.name}: correr terminado.py otra vez")
        junto = f", de la misma corrida de terminado.py que {archivo.name}"
    nota, clase = d.get("nota_medida"), d.get("clase_medida")
    ok = isinstance(nota, (int, float)) and not isinstance(nota, bool) and nota >= nota_minima and clase in ("A", "B")
    return ok, (f"{e.name}: nota {nota} clase {clase} (huella de {real.name} comprobada{junto})"
                + ("" if ok else f" · se exige nota {nota_minima} o más y clase A o B"))


def aprobacion(pub, clave, filas=None):
    """Última aprobación vigente: no revocada y posterior a cualquier cancelación de esa pieza (lo cancelado no se
    vuelve a publicar con la aprobación vieja)."""
    ap = leer_json(APROBACIONES, {"aprobaciones": []})
    k = f"{pub['id']}|{pub['version']}|{clave}"
    xs = [a for a in ap["aprobaciones"] if a["clave"] == k]
    if not xs or xs[-1].get("revocada"):
        return None
    a = xs[-1]
    filas = registro() if filas is None else filas
    cancelado = [r["fecha_utc"] for r in filas if r["id"] == pub["id"] and r["version"] == pub["version"]
                 and r["pieza"] == clave and r["estado"] == "cancelado"]
    if cancelado and max(cancelado) >= a["fecha"]:
        return None
    return a


def cupo_metricool(mes, cfg, filas=None):
    u = ultimo_estado(lambda r: (r["id"], r["version"], r["pieza"], r["red"], r["ruta"]), filas)
    usados = sum(1 for r in u.values() if r["ruta"] == "metricool"
                 and r["estado"] in ("en_curso", "incierto", "programado", "publicado")
                 and r["fecha_publicacion"][:7] == mes)
    return usados, cfg["metricool"].get("limite_mes", 20)


def margen_minutos(cfg, archivo):
    """30 min fijos más ~1 min por cada 60 MB (una subida larga no debe llegar con la hora ya pasada)."""
    return cfg.get("minutos_minimos_antes", 30) + archivo.stat().st_size / (60 * 1024 * 1024)


def revisar(pdir, clave, red=None, ahora=None, revisar_enlace=None, huella_enlace=None):
    from enlace import revisar_contra, revisar as rev_real, huella_remota
    pdir = Path(pdir)
    cfg = config()
    ahora = ahora or ahora_utc()
    R = []
    err, _ = validar(pdir)
    R.append(("publicacion.json válido", not err, "; ".join(err[:4]) if err else "ok"))
    if err:
        return R
    pub = leer_json(carpeta_publicar(pdir) / "publicacion.json")
    x = next((y for y in pub["piezas"] if y["clave"] == clave), None)
    R.append((f"existe la pieza «{clave}»", bool(x), "ok" if x else "no está en publicacion.json"))
    if not x:
        return R
    destinos = [d for d in x["destinos"] if not red or d["red"] == red]
    R.append((f"{clave}: tiene destino {red or '(alguno)'}", bool(destinos), "ok" if destinos else f"la pieza no va a {red}"))
    if not destinos:
        return R
    nv = nivel(cfg)
    R.append(("nivel de autonomía válido y ≥ 1", nv is not None and nv >= 1, f"nivel {cfg.get('nivel')!r}"))
    arch = ruta_segura(pdir, x["archivo"])
    ok, det, sellados, carp = revisar_terminado(pdir, pub["id"], pub["version"], [arch])
    R.append(("terminado.py del mismo video: lo obligatorio en ✓", ok, det))
    chk = carpeta_publicar(pdir) / f"checklist_publicacion_monetizacion_{pub['version']}.md"
    txt = chk.read_text(encoding="utf-8-sig") if chk.is_file() else ""
    ok = bool(txt) and re.search(r"MONETIZACI[ÓO]N:\s*OK", txt, re.I) and "corregir antes de publicar" not in txt.lower()
    R.append((f"checklist de monetización de la {pub['version']} con «MONETIZACIÓN: OK»", bool(ok),
              chk.name if ok else f"falta {chk.name} con la línea «MONETIZACIÓN: OK» (o dice «corregir antes de publicar»)"))
    es_short = arch.name.lower().endswith("_9x16.mp4")
    es_largo = arch.stem.lower().endswith(("_youtube", "_con-subtitulos"))
    calza = es_short if x["tipo"] == "short" else (es_largo and not es_short)
    R.append((f"{clave}: el tipo «{x['tipo']}» calza con el archivo", calza,
              arch.name if calza else f"{arch.name}: un Short termina en _9x16.mp4 y un largo en _youtube.mp4 o "
              "_con-subtitulos.mp4 (el tipo decide la nota mínima: no se cambia a mano)"))
    if x["tipo"] == "largo":
        nombres = [arch.stem, f"{pub['id']}_{pub['version']}_con-subtitulos", f"{pub['id']}_{pub['version']}_youtube"]
        ok, det = revisar_evaluacion(pdir, nombres, arch, sellados, carp, NOTA_LARGO)
        R.append((f"{clave}: evaluación con nota {NOTA_LARGO} o más del mismo video", ok, det))
    elif cfg.get("exigir_evaluacion_shorts", True):
        ok, det = revisar_evaluacion(pdir, [arch.stem], arch, sellados, carp, NOTA_SHORT)
        R.append((f"{clave}: evaluación con nota {NOTA_SHORT} o más del mismo Short", ok, det))
    filas = registro()
    sha = huella(arch)
    hp = huella_pieza(pdir, x, ctx=contexto(pub, cfg))
    a = aprobacion(pub, clave, filas)
    if not a:
        det = "sin aprobación vigente (falta, fue revocada o la pieza se canceló después)"
    elif a["sha256"] != sha:
        det = "el video cambió después de aprobarlo: aprobar de nuevo"
    elif a.get("huella_pieza") != hp:
        det = ("cambió el título, un texto, una fecha, una red, la miniatura, los subtítulos, el canal o la configuración "
               "de YouTube: aprobar de nuevo")
    else:
        det = f"aprobado por {a['por']} el {a['fecha'][:10]} (huella {hp[:8]})"
    R.append((f"{clave}: aprobado tal como está", bool(a) and a["sha256"] == sha and a.get("huella_pieza") == hp, det))
    for d in destinos:
        r = d["red"]
        if d["ruta"] == "manual":
            R.append((f"{clave}/{r}: ruta manual (la sube Patricio)", True, "se prepara hoja de publicación"))
            continue
        mot = ya_enviado(sha, r, pub["id"], clave)
        R.append((f"{clave}/{r}: no se envió antes", not mot, "ok" if not mot else "; ".join(mot)))
        cuando = a_utc(d["fecha"], d["zona"])
        if d["ruta"] == "vidiq":
            desde, hasta = (cuando + dt.timedelta(minutes=m) for m in VENTANA_VIDIQ)
            R.append((f"{clave}/{r}: es la hora (vidIQ publica en el momento)", desde <= ahora <= hasta,
                      f"{d['fecha']} {d['zona']}: se publica entre {VENTANA_VIDIQ[0]} y +{VENTANA_VIDIQ[1]} minutos"))
            yt = next((y for y in x["destinos"] if y["red"] == "youtube"), None)
            fila = ultimo_estado(lambda q: (q["sha256"], q["red"]), filas).get((sha, "youtube"))
            ok = bool(yt and fila and fila["estado"] in ("programado", "publicado") and fila["enlace"]
                      and a_utc(yt["fecha"], yt["zona"]) <= ahora)
            R.append((f"{clave}/{r}: el Short ya es público en YouTube", ok,
                      (fila["enlace"] + " (confirmar abriéndolo antes de publicar)") if ok
                      else "primero el Short tiene que estar publicado en YouTube (su hora ya pasó)"))
        else:
            minimo = ahora + dt.timedelta(minutes=margen_minutos(cfg, arch))
            R.append((f"{clave}/{r}: fecha futura con margen", cuando >= minimo,
                      f"{d['fecha']} {d['zona']} ({cuando:%Y-%m-%d %H:%M} UTC)"))
        if d["ruta"] in ("metricool", "vidiq"):
            R.append((f"{clave}/{r}: nivel 2 para programar en {d['ruta']}", nv == 2, f"nivel {cfg.get('nivel')!r}"))
        if d["ruta"] == "metricool":
            url = d.get("enlace_publico")
            if url:
                ok, det = revisar_contra(url, arch, revisar_enlace or rev_real, huella_enlace or huella_remota)
            else:
                ok, det = False, "falta enlace_publico (ver references/publicar.md)"
            R.append((f"{clave}/{r}: enlace público con el mismo video", ok, det))
            usados, lim = cupo_metricool(d["fecha"][:7], cfg, filas)
            R.append((f"{clave}/{r}: cupo Metricool del mes", usados < lim, f"{usados} de {lim} en {d['fecha'][:7]}"))
    return R


def todo_ok(R):
    return bool(R) and all(ok for _, ok, _ in R)


def tabla(R):
    filas = ["| puerta | | detalle |", "|---|---|---|"]
    filas += [f"| {n} | {'✓' if ok else '✗'} | {d} |" for n, ok, d in R]
    return "\n".join(filas)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or "--pieza" not in a:
        sys.exit("uso: python puertas.py <proyecto> --pieza <clave> [--red youtube|tiktok|instagram]")
    R = revisar(proyecto_dir(a[0]), opt(a, "--pieza"), opt(a, "--red"))
    p(tabla(R))
    p("PUERTAS ABIERTAS" if todo_ok(R) else "PUERTAS CERRADAS: no se publica")
    sys.exit(0 if todo_ok(R) else 1)
