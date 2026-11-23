from comun import carpeta_publicar
# Puertas antes de subir o programar: si una falla, no se publica nada.
#   python puertas.py "<proyecto>" --pieza <clave> [--red youtube|tiktok|instagram]
# Revisa: publicacion.json válido · nivel · terminado.py con los puntos obligatorios en ✓ y con la HUELLA del archivo
# que se sube (terminado_<base>.json) · checklist de monetización DE ESTA VERSIÓN con «MONETIZACIÓN: OK» · evaluación
# con nota 8 o más (7 en los Shorts), clase A o B y la huella del video evaluado · aprobación vigente con la huella de la pieza completa y su contexto (y posterior a cualquier cancelación) ·
# fecha futura · que no se haya enviado antes · enlace público con el mismo contenido y cupo (Metricool) ·
# ventana horaria y Short ya público (vidIQ). Termina con 0 solo si todo pasa.
# 0.2.0: juicio del juez (con «rechazado» se cierra; en modo lanzamiento es obligatorio) y modo lanzamiento por canal
# (config.json → canales → <canal> → modo_lanzamiento): en los primeros N videos del canal una nota bajo el mínimo pasa
# como AVISO (⚠) solo si la aprobación vigente guarda su aceptación explícita (aprobar.py --acepto-nota).
# Correcciones tras el juicio del juez (0.2.0): el juicio se busca en la carpeta de publicación y en 08_PUBLICAR (M2); el
# veredicto es la palabra exacta de la primera línea y, si la segunda cita «sha256: …», tiene que ser de este video (B3);
# en modo lanzamiento las rutas api, metricool y vidiq quedan cerradas: subida a mano (M4); la fila de la evaluación
# muestra el tipo de video y los pesos con que se evaluó (M3). calendario.py hoja corre estas mismas puertas (M1).
import datetime as dt, re, sys
from pathlib import Path
from comun import (APROBACIONES, a_utc, ahora_utc, canal_cfg, config, contexto, huella, huella_pieza, leer_json,
                   modo_lanzamiento, nivel, numero_version, opt, p, proyecto_dir, registro, ruta_segura, ultimo_estado,
                   ya_enviado)
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


def _evaluacion(pdir, nombres, archivo, sellados=None, carpeta=None, nota_minima=8):
    """(ok, detalle, info). info["valida"] = la evaluación existe, se lee, trae huella y es de ESTE video (o del hermano
    sellado junto con él): solo entonces la nota cuenta, para aprobar o para aceptarla en modo lanzamiento."""
    info = {"valida": False, "minimo": nota_minima}
    e = _exacto([Path(pdir) / "06_RECETA"], [f"evaluacion_{n}.json" for n in nombres])
    if not e:
        return False, f"falta 06_RECETA/evaluacion_{nombres[0]}.json (correr evaluar.py sobre ese video)", info
    try:
        d = leer_json(e)
        if not isinstance(d, dict):
            raise ValueError("no es un objeto")
    except Exception:
        return False, f"{e.name} no se puede leer: evaluar otra vez", info
    evaluado = Path(str(d["video"]).replace("\\", "/")).stem if d.get("video") else None
    if evaluado and evaluado not in nombres:
        return False, f"{e.name} evaluó otro video ({Path(str(d['video']).replace(chr(92), '/')).name})", info
    if not d.get("sha256"):
        return False, f"{e.name} no trae la huella del video evaluado (evaluación anterior al motor 0.14): evaluar otra vez", info
    if evaluado in (None, archivo.stem):
        real = archivo
    else:                                       # se evaluó el hermano con subtítulos
        real = (Path(carpeta) if carpeta else archivo.parent) / (evaluado + archivo.suffix)
        if not real.is_file():
            return False, f"{e.name} evaluó {real.name}, que ya no está junto al terminado: evaluar otra vez", info
    if huella(real) != d["sha256"]:
        return False, f"{real.name} cambió después de la evaluación ({e.name}): evaluar otra vez", info
    junto = ""
    if real != archivo:
        if (sellados or {}).get(real.name) != d["sha256"]:
            return False, (f"{real.name} (el evaluado) no está entre los videos que revisó terminado.py junto con "
                           f"{archivo.name}: correr terminado.py otra vez"), info
        junto = f", de la misma corrida de terminado.py que {archivo.name}"
    nota, clase = d.get("nota_medida"), d.get("clase_medida")
    ok = isinstance(nota, (int, float)) and not isinstance(nota, bool) and nota >= nota_minima and clase in ("A", "B")
    info.update(valida=True, nota=nota, clase=clase, evaluacion=e.name, sha256_evaluado=d["sha256"], evaluado=real.name)
    # corrección M3 (juicio 0.15): el tipo de video cambia los pesos de la nota; se muestra con qué tipo y pesos se evaluó
    tv, pesos = d.get("tipo_video"), d.get("pesos")
    info.update(tipo_video=tv, pesos=pesos if isinstance(pesos, dict) else None)
    if tv:
        tipo_txt = f" · tipo de video «{tv}»" + (" (pesos " + ", ".join(
            f"{k} {round(v * 100)} %" for k, v in pesos.items() if isinstance(v, (int, float))) + ")"
            if isinstance(pesos, dict) and pesos else "")
    else:
        tipo_txt = " · tipo de video no registrado (pesos de siempre)"
    return ok, (f"{e.name}: nota {nota} clase {clase} (huella de {real.name} comprobada{junto}){tipo_txt}"
                + ("" if ok else f" · se exige nota {nota_minima} o más y clase A o B")), info


def revisar_evaluacion(pdir, nombres, archivo, sellados=None, carpeta=None, nota_minima=8):
    """La evaluación tiene que ser de ESTE video, comprobado por huella (evaluar.py la guarda desde el motor 0.14; una
    evaluación sin huella no vale). Si se evaluó el hermano con subtítulos, ese hermano tiene que estar en la misma
    corrida de terminado.py que el archivo que se sube. Nota mínima: 8 el largo (igual que el motor) y 7 los Shorts; clase A o B."""
    ok, det, _ = _evaluacion(pdir, nombres, archivo, sellados, carpeta, nota_minima)
    return ok, det


def evaluacion_de_pieza(pdir, pub, x, cfg=None):
    """Para aprobar.py y la tabla: (nombre de la fila, ok, detalle, info) de la evaluación de una pieza, o None si la
    pieza no la necesita (Short con exigir_evaluacion_shorts = false). Misma regla que las puertas."""
    cfg = cfg or config()
    arch = ruta_segura(pdir, x["archivo"])
    _, _, sellados, carp = revisar_terminado(pdir, pub["id"], pub["version"], [arch])
    if x["tipo"] == "largo":
        nombres = [arch.stem, f"{pub['id']}_{pub['version']}_con-subtitulos", f"{pub['id']}_{pub['version']}_youtube"]
        ok, det, info = _evaluacion(pdir, nombres, arch, sellados, carp, NOTA_LARGO)
        return f"{x['clave']}: evaluación con nota {NOTA_LARGO} o más del mismo video", ok, det, info
    if cfg.get("exigir_evaluacion_shorts", True):
        ok, det, info = _evaluacion(pdir, [arch.stem], arch, sellados, carp, NOTA_SHORT)
        return f"{x['clave']}: evaluación con nota {NOTA_SHORT} o más del mismo Short", ok, det, info
    return None


def aceptacion_vale(a, info):
    """La aceptación de la nota guardada en la aprobación es de ESTA evaluación (misma huella del video evaluado, misma
    nota y clase). Si se evaluó otra vez, la aceptación vieja no sirve."""
    ac = (a or {}).get("aceptacion_nota")
    return (isinstance(ac, dict) and bool(ac.get("motivo")) and ac.get("sha256_evaluado") == info.get("sha256_evaluado")
            and ac.get("nota") == info.get("nota") and ac.get("clase") == info.get("clase"))


VEREDICTOS = ("APROBADO", "OBSERVADO", "RECHAZADO")


def carpetas_juicio(pdir):
    """Corrección M2 (juicio 0.15): el juez escribe juicio_<v>.md en la carpeta de publicación del proyecto
    (proyecto.json → carpetas → "publicar", p. ej. 08_PUBLICAR_ESTUDIO) o en 08_PUBLICAR: se buscan las dos."""
    xs = []
    for c in (carpeta_publicar(pdir), Path(pdir) / "08_PUBLICAR"):
        if c not in xs:
            xs.append(c)
    return xs


SIN_CODIFICACION = "codificación"   # leer_juicio: el archivo no se pudo decodificar (N6)


def _texto_juicio(j):
    """Corrección N6 (verificación 0.2.0): UTF-8 con o sin BOM, o UTF-16 con BOM (Out-File / > de Windows PowerShell 5).
    Si no se puede decodificar devuelve None (la puerta se cierra diciendo por qué)."""
    b = j.read_bytes()
    try:
        if b.startswith((b"\xff\xfe", b"\xfe\xff")):
            return b.decode("utf-16")
        return b.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def leer_juicio(j):
    """Formato de agents/juez.md: la primera línea con texto es SOLO la palabra del veredicto (APROBADO, OBSERVADO o
    RECHAZADO) y después, seguidas, una línea «sha256: <hex>» por cada video que el juez revisó. Devuelve
    (veredicto, shas): veredicto «?» si la primera línea no es exactamente una de las tres palabras («NO APROBADO»,
    «Veredicto: …», un título antes…); shas None si no cita ningún sha256, «ilegible» si alguna de esas líneas lo cita
    mal, SIN_CODIFICACION si el archivo no se pudo decodificar, o la lista de los sha256 citados (en minúsculas)."""
    try:
        texto = _texto_juicio(j)
    except OSError:
        return "?", None
    if texto is None:
        return "?", SIN_CODIFICACION
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    v = lineas[0].upper() if lineas else ""
    v = v if v in VEREDICTOS else "?"
    shas = []
    for l in lineas[1:]:                          # corrección N1: varias líneas sha256 seguidas, una por video revisado
        if not re.match(r"sha256\b", l, re.I):
            break
        m = re.fullmatch(r"sha256\s*:\s*`?([0-9a-fA-F]{8,64})`?", l, re.I)
        if not m:
            return v, "ilegible"
        shas.append(m.group(1).lower())
    return v, (shas or None)


def pareja_del_largo(archivo):
    """Corrección N1 (decisión de Patricio, estricto): el único «hermano» que vale para el juicio es el par
    _youtube / _con-subtitulos del MISMO largo (mismo corte). Un Short, un borrador, la copia del celular o una prueba
    nunca son hermanos: cada uno necesita su propio sha256 en el juicio."""
    if not archivo:
        return set()
    st = archivo.stem
    for suf, otro in (("_youtube", "_con-subtitulos"), ("_con-subtitulos", "_youtube")):
        if st.lower().endswith(suf) and not st.lower().endswith("_9x16"):
            return {(st[: -len(suf)] + otro + archivo.suffix).lower()}
    return set()


def revisar_juicio(pdir, version, archivo, sellados=None):
    """Último juicio del agente juez para la versión (juicio_<v>.md o juicio_<v>_N.md, en la carpeta de publicación del
    proyecto o en 08_PUBLICAR; manda el más reciente). Devuelve (veredicto, detalle, vale_para_este_video, de_otro_video).
    veredicto: APROBADO, OBSERVADO, RECHAZADO, «?» (la primera línea no es exactamente la palabra) o None (no hay juicio).
    Si el juicio cita sha256 (uno o varios, uno por línea), uno tiene que ser el del archivo que se sube o el de su par
    _youtube / _con-subtitulos sellado en la misma corrida de terminado.py (corrección N1: nunca un borrador, la copia
    del celular, un Short u otra prueba; un Short necesita su propio sha256); si no cita ninguno, vale si es posterior
    al video."""
    patron = re.compile(rf"juicio_{re.escape(str(version))}(_\d+)?\.md", re.I)
    carps = carpetas_juicio(pdir)
    xs = [q for c in carps if c.is_dir() for q in c.glob("juicio_*.md") if patron.fullmatch(q.name)]
    if not xs:
        donde = f"{carps[0].name}/juicio_{version}.md" + (" (ni en 08_PUBLICAR)" if len(carps) > 1 else "")
        return None, f"falta {donde} (agente juez del estudio, modo video)", False, False
    j = max(xs, key=lambda q: q.stat().st_mtime)
    v, sha = leer_juicio(j)
    nombre = f"{j.parent.name}/{j.name}" if len(carps) > 1 else j.name
    det = f"{nombre}: {v}" + ("" if v != "?" else " (la primera línea tiene que ser solo APROBADO, OBSERVADO o RECHAZADO)")
    if sha == SIN_CODIFICACION:
        return v, (f"{nombre}: no se pudo leer el juicio (codificación) · guardarlo en UTF-8 (o UTF-16 con BOM) y "
                   "revisar otra vez"), False, True
    if sha == "ilegible":
        return v, det + " · una línea sha256 no trae un sha256 legible («sha256: <hex>»)", False, True
    if sha:
        real = huella(archivo) if archivo and archivo.is_file() else ""
        propio = next((s for s in sha if real and real.startswith(s)), None)
        if propio:
            return v, det + f" (sha256 {propio[:8]} = {archivo.name})", True, False
        pareja = pareja_del_largo(archivo)
        for s in sha:
            hermano = next((n for n, h in (sellados or {}).items()
                            if n.lower() in pareja and isinstance(h, str) and h.startswith(s)), None)
            if hermano:
                return v, det + (f" (sha256 {s[:8]} = {hermano}, el mismo largo de la misma corrida de "
                                 "terminado.py)"), True, False
        citados = ", ".join(s[:8] for s in sha)
        return v, det + (f" · el juicio revisó otro video (sha256 {citados}; ninguno es el de "
                         f"{archivo.name if archivo else 'la pieza'} ni el de su par _youtube/_con-subtitulos: "
                         "un Short, un borrador o la copia del celular necesitan su propio sha256 en el juicio)"), False, True
    nuevo = bool(archivo and archivo.is_file() and j.stat().st_mtime >= archivo.stat().st_mtime)
    return v, det + ("" if nuevo else f" (es anterior a {archivo.name if archivo else 'el video'})"), nuevo, False


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


def cupo_metricool(mes, cfg, filas=None, canal=None):
    """Envíos de Metricool del mes frente al límite del plan. Si el canal tiene su propia cuenta o marca de Metricool
    (config.json → canales → <canal> → "metricool"), cuenta solo los de ese canal contra su límite; si no, todos los
    canales comparten la cuenta general (como hasta la 0.1.6)."""
    from comun import _canal_de_proyecto
    propio = canal_cfg(cfg, canal).get("metricool") if canal else None
    u = ultimo_estado(lambda r: (r["id"], r["version"], r["pieza"], r["red"], r["ruta"]), filas)
    vivos = [r for r in u.values() if r["ruta"] == "metricool" and r["estado"] in ("en_curso", "incierto", "programado", "publicado")
             and r["fecha_publicacion"][:7] == mes]
    if isinstance(propio, dict):
        cache = {}
        vivos = [r for r in vivos if cache.setdefault(r["proyecto"], _canal_de_proyecto(r["proyecto"])) == canal]
        return len(vivos), propio.get("limite_mes", cfg["metricool"].get("limite_mes", 20))
    return len(vivos), cfg["metricool"].get("limite_mes", 20)


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
    filas = registro()
    sha = huella(arch)
    hp = huella_pieza(pdir, x, ctx=contexto(pub, cfg))
    a = aprobacion(pub, clave, filas)
    # 0.2.0 modo lanzamiento por canal (decisión de Patricio, 15-11-2026): solo cambia la nota mínima de BLOQUEO a AVISO,
    # y solo con una aceptación explícita guardada en la aprobación vigente. Todo lo demás sigue igual.
    ml = modo_lanzamiento(cfg, pub.get("canal"), pub["id"], filas)
    if ml["configurado"]:
        R.append(("modo lanzamiento del canal", True, ml["detalle"]))
    nver = numero_version(pub["version"])
    if ml["activo"] and nver is not None and nver > 2:
        R.append((f"versión {pub['version']}", True, f"AVISO: en el modo lanzamiento se acordó un máximo de 2 versiones "
                                                    f"por video; esta es la {nver} (no bloquea, se le avisa a Patricio)"))
    if x["tipo"] == "largo":
        nombres = [arch.stem, f"{pub['id']}_{pub['version']}_con-subtitulos", f"{pub['id']}_{pub['version']}_youtube"]
        fila_ev = f"{clave}: evaluación con nota {NOTA_LARGO} o más del mismo video"
        ok, det, info = _evaluacion(pdir, nombres, arch, sellados, carp, NOTA_LARGO)
    elif cfg.get("exigir_evaluacion_shorts", True):
        fila_ev = f"{clave}: evaluación con nota {NOTA_SHORT} o más del mismo Short"
        ok, det, info = _evaluacion(pdir, [arch.stem], arch, sellados, carp, NOTA_SHORT)
    else:
        fila_ev = None
    if fila_ev:
        # evaluación ausente, ilegible, sin huella o de otro video: bloquea siempre (también en modo lanzamiento)
        if not ok and ml["activo"] and info.get("valida"):
            vigente = bool(a) and a["sha256"] == sha and a.get("huella_pieza") == hp
            if vigente and aceptacion_vale(a, info):
                ac = a["aceptacion_nota"]
                ok, det = True, (f"AVISO ({ml['detalle']}): {det}; nota aceptada por {ac.get('por')} el "
                                 f"{str(ac.get('fecha'))[:10]}: «{ac.get('motivo')}»")
            else:
                det += (f" · {ml['detalle']}: el evaluador aconseja y no bloquea, pero la nota baja se acepta al aprobar: "
                        "aprobar.py \"<P>\" --por \"<quién>\" --huellas … --acepto-nota \"<motivo>\"")
        R.append((fila_ev, ok, det))
    # el juez: «rechazado» bloquea siempre; en modo lanzamiento su juicio de ESTA versión, posterior al video, es obligatorio
    # corrección B3 (juicio 0.15): veredicto solo como palabra exacta en la primera línea («?» cierra en los dos modos) y,
    # si el juicio cita el sha256 del video revisado, tiene que coincidir (si no, cierra en los dos modos)
    veredicto, det_j, nuevo, otro_video = revisar_juicio(pdir, pub["version"], arch, sellados)
    if ml["activo"]:
        ok_j = veredicto in ("APROBADO", "OBSERVADO") and nuevo
        R.append(("juicio del juez (obligatorio en modo lanzamiento)", ok_j,
                  det_j if ok_j else det_j + " · hace falta un juicio APROBADO u OBSERVADO de esta versión, de este video "
                                             "(su sha256) o posterior a él"))
    elif veredicto is not None:
        ok_j = veredicto in ("APROBADO", "OBSERVADO") and not otro_video
        R.append(("juicio del juez", ok_j,
                  det_j + ("" if ok_j else " · con «rechazado», un veredicto que no se reconoce o un juicio de otro video "
                                           "no se publica (pedir un juicio nuevo de este video)")))
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
            # corrección N2 (verificación 0.2.0): la ruta manual también respeta la puerta de duplicados; una segunda
            # hoja de algo ya publicado o programado sale cerrada
            mot = ya_enviado(sha, r, pub["id"], clave)
            R.append((f"{clave}/{r}: no se envió antes", not mot, "ok" if not mot else "; ".join(mot)))
            R.append((f"{clave}/{r}: ruta manual (la sube Patricio)", True, "se prepara hoja de publicación"))
            continue
        if ml["activo"]:
            # corrección M4 (juicio 0.15, decisión de Patricio): en el modo lanzamiento la subida es SOLO a mano; la ruta
            # api (yt_api.py subir/programar), Metricool y vidIQ quedan cerradas. Fuera del modo, todo igual.
            R.append((f"{clave}/{r}: ruta {d['ruta']}", False,
                      "modo lanzamiento: subida a mano (hoja de calendario) · cambiar la ruta a «manual» en "
                      "publicacion.json, aprobar de nuevo y usar calendario.py hoja"))
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
            usados, lim = cupo_metricool(d["fecha"][:7], cfg, filas, pub.get("canal"))
            R.append((f"{clave}/{r}: cupo Metricool del mes", usados < lim, f"{usados} de {lim} en {d['fecha'][:7]}"))
    return R


def todo_ok(R):
    return bool(R) and all(ok for _, ok, _ in R)


def cerradas_juicio_evaluacion(R):
    """Corrección N3 (verificación 0.2.0): de una revisión ya hecha, las filas cerradas del juicio del juez o de la
    evaluación (para que anotar.py deje constancia en la ruta manual sin repetir la lógica de las puertas)."""
    return [f"{n} ({d})" for n, ok, d in R
            if not ok and (n.startswith("juicio del juez") or ": evaluación con nota" in n)]


def tabla(R):
    filas = ["| puerta | | detalle |", "|---|---|---|"]
    # una fila que pasa con AVISO (modo lanzamiento) se marca ⚠: pasa, pero hay que contárselo a Patricio
    filas += [f"| {n} | {('⚠' if str(d).startswith('AVISO') else '✓') if ok else '✗'} | {d} |" for n, ok, d in R]
    return "\n".join(filas)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or "--pieza" not in a:
        sys.exit("uso: python puertas.py <proyecto> --pieza <clave> [--red youtube|tiktok|instagram]")
    R = revisar(proyecto_dir(a[0]), opt(a, "--pieza"), opt(a, "--red"))
    p(tabla(R))
    p("PUERTAS ABIERTAS" if todo_ok(R) else "PUERTAS CERRADAS: no se publica")
    sys.exit(0 if todo_ok(R) else 1)
