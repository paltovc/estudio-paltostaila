from comun import carpeta_publicar
# YouTube con la API propia del estudio (OAuth del canal; nada de contraseñas ni cookies).
#   python yt_api.py autorizar                         abre el navegador UNA vez para dar permiso; guarda el token en claves
#   python yt_api.py canal [--confirmar [--canal <nombre>]]  muestra a qué canal quedó conectado; --confirmar lo fija en
#                                                      config (con --canal, solo para ese canal del estudio, 0.2.0)
#                                                      (solo después de que Patricio diga que es el canal correcto)
#   python yt_api.py subir "<proyecto>" <pieza> [--simular]
#       pasa las puertas → sube PRIVADO y SIN fecha → guarda el ID → miniatura, subtítulos y lista → revisa que la
#       aprobación siga vigente → recién ahí pone la fecha de publicación (nivel 2). Si algo falla, queda privado.
#   python yt_api.py metricas <videoId> [--proyecto "<proyecto>"]   vistas, retención, países, fuentes
#   python yt_api.py progreso                          estimación de avance hacia el Programa de Partners
#   python yt_api.py desprogramar "<proyecto>" <pieza> --confirmado-por "Patricio"
#       quita la fecha de publicación de un video ya subido y lo deja privado (solo con el sí de Patricio)
# Las subidas largas van en segundo plano con log (la terminal corta cerca de 58 s).
# Archivos en claves\: youtube_cliente.json (lo descarga Patricio de Google Cloud) y youtube_token.json (lo crea autorizar).
import datetime as dt, json, os, shutil, sys, time, uuid
from pathlib import Path
from comun import (CLAVES, CONFIG, GER, TMP, a_utc, ahora_utc, bloqueo, config, contexto, diario, escribir_estado,
                   escribir_nuevo, huella, huella_pieza, nivel, opt, p, pieza, proyecto_dir, publicacion, registrar,
                   ruta_segura, ultimo_estado, ya_enviado, youtube_de)

ALCANCES = ["https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/yt-analytics.readonly"]
CLIENTE = CLAVES / "youtube_cliente.json"
TOKEN = CLAVES / "youtube_token.json"
# Umbrales del Programa de Partners (verificar en support.google.com/youtube/answer/72851 antes de informar)
YPP = {"fan_funding": {"subs": 500, "horas": 3000, "shorts": 3_000_000, "subidas_90d": 3},
       "anuncios": {"subs": 1000, "horas": 4000, "shorts": 10_000_000},
       "anuncios_desde_2027_02_01": {"subs": 1000, "horas": 8000, "shorts": 20_000_000}}
CAMPOS_STATUS = ("privacyStatus", "embeddable", "license", "publicStatsViewable", "selfDeclaredMadeForKids",
                 "containsSyntheticMedia")


def _guardar_token(cr):
    CLAVES.mkdir(parents=True, exist_ok=True)
    tmp = TOKEN.with_name(f"{TOKEN.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(cr.to_json(), encoding="utf-8")
    for i in range(10):
        try:
            os.replace(tmp, TOKEN)
            return
        except PermissionError:
            time.sleep(0.5 * (i + 1))
    sys.exit("No pude guardar el permiso renovado de YouTube (archivo bloqueado). Repetir.")


def credenciales():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError, TransportError
    if not TOKEN.exists():
        sys.exit("Falta autorizar: python yt_api.py autorizar (ver references/configurar-cuentas.md)")
    with bloqueo("token_youtube"):            # leer, renovar y guardar sin pisarse entre procesos
        concedidos = set(json.loads(TOKEN.read_text(encoding="utf-8")).get("scopes") or [])
        faltan = [s for s in ALCANCES if concedidos and s not in concedidos]
        if faltan:
            sys.exit("El permiso guardado no incluye: " + ", ".join(s.rsplit("/", 1)[-1] for s in faltan)
                     + ". Correr python yt_api.py autorizar para darlos.")
        cr = Credentials.from_authorized_user_file(str(TOKEN), ALCANCES)
        if not cr.valid:
            if not cr.refresh_token:
                sys.exit("El permiso guardado no se puede renovar: correr otra vez python yt_api.py autorizar")
            try:
                cr.refresh(Request())
            except TransportError as e:
                sys.exit(f"Sin conexión con Google al renovar el permiso ({str(e)[:80]}). Reintentar más tarde.")
            except RefreshError:
                sys.exit("Google rechazó el permiso (¿revocado, o la app quedó en modo Prueba y venció a los 7 días?). "
                         "Correr python yt_api.py autorizar y, si se repite, pasar la app a «En producción».")
            _guardar_token(cr)
        if not cr.valid:
            sys.exit("El permiso de YouTube no es válido: correr python yt_api.py autorizar")
        return cr


def servicio(nombre="youtube", version="v3"):
    from googleapiclient.discovery import build
    return build(nombre, version, credentials=credenciales(), cache_discovery=False)


def autorizar():
    from google_auth_oauthlib.flow import InstalledAppFlow
    if not CLIENTE.exists():
        sys.exit(f"Falta {CLIENTE}. Descargarlo de Google Cloud (ver references/configurar-cuentas.md).")
    flujo = InstalledAppFlow.from_client_secrets_file(str(CLIENTE), ALCANCES)
    cr = flujo.run_local_server(port=0, prompt="consent", open_browser=True)
    with bloqueo("token_youtube"):
        _guardar_token(cr)
    p("LISTO: permiso guardado en", TOKEN.name, "(no se muestra su contenido). Ahora: python yt_api.py canal")


def canal(yt=None, confirmar=False, nombre=None):
    """--confirmar fija el canal de YouTube en la configuración general; con --canal <nombre> lo fija solo para ese canal
    del estudio (config.json → canales → <nombre> → youtube → canal_id). El permiso (token) sigue siendo uno solo: para
    subir a otro canal de YouTube hay que autorizar esa cuenta (ver cambios-0200.md); mientras tanto, ruta manual."""
    yt = yt or servicio()
    r = yt.channels().list(part="snippet,statistics", mine=True).execute()
    it = r.get("items", [])
    if not it:
        sys.exit("La cuenta autorizada no tiene canal de YouTube.")
    c = it[0]
    p(f"Canal: {c['snippet']['title']} ({c['id']}) · {c['statistics'].get('subscriberCount')} suscriptores")
    if confirmar:
        with bloqueo("config"):
            cfg = config()
            if nombre:
                cfg.setdefault("canales", {}).setdefault(nombre, {}).setdefault("youtube", {})["canal_id"] = c["id"]
            else:
                cfg["youtube"]["canal_id"] = c["id"]
            escribir_estado(CONFIG, cfg)
        p(f"LISTO: canal confirmado{' para ' + nombre if nombre else ''}. Las aprobaciones nuevas quedan atadas a este canal.")
    return c


def cuerpo(pub, x, d, cfg):
    """Cuerpo del video para insertar: siempre privado y sin fecha (la fecha se pone al final, en programar())."""
    yc = youtube_de(cfg, pub.get("canal"))       # 0.2.0: valores del canal del proyecto (sin config propia = los generales)
    st = {"privacyStatus": "private", "selfDeclaredMadeForKids": bool(x["para_ninos"]),
          "containsSyntheticMedia": bool(x["ia_realista"]), "embeddable": True, "license": "youtube"}
    sn = {"title": x["titulo"], "description": x.get("descripcion", ""), "categoryId": str(x.get("categoria", yc.get("categoria", "27"))),
          "defaultLanguage": x.get("idioma", yc.get("idioma", "es")), "defaultAudioLanguage": x.get("idioma", yc.get("idioma", "es"))}
    if x.get("etiquetas"):
        sn["tags"] = x["etiquetas"]
    programar = nivel(cfg) == 2 and not yc.get("forzar_privado")
    fecha = a_utc(d["fecha"], d["zona"]).strftime("%Y-%m-%dT%H:%M:%S.000Z") if programar else None
    return {"snippet": sn, "status": st}, fecha


NOMBRE_PISTA = {"es": "Español", "en": "English", "pt": "Português"}
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".srt": "application/octet-stream"}


def _media(ruta, **k):
    from googleapiclient.http import MediaFileUpload
    return MediaFileUpload(str(ruta), **k)


def _cerrar(m):
    try:
        st = m.stream() if hasattr(m, "stream") else None
        if st is not None:
            st.close()
    except Exception:
        pass


def _copia_verificada(origen, sha_esperado):
    """Copia a gerente\\tmp con nombre por huella y comprueba que es lo aprobado: así un render que corre justo
    ahora no puede colarse en la subida."""
    TMP.mkdir(parents=True, exist_ok=True)
    destino = TMP / f"{sha_esperado[:16]}_{os.getpid()}_{uuid.uuid4().hex[:6]}{Path(origen).suffix.lower()}"
    shutil.copy2(origen, destino)
    if huella(destino) != sha_esperado:
        destino.unlink(missing_ok=True)
        raise RuntimeError(f"{Path(origen).name} cambió mientras se preparaba la subida")
    return destino


def _vigente(pdir, pub, clave, x, cfg, sha, copias=None):
    """La aprobación sigue vigente para exactamente esto (se revisa justo antes de cada paso remoto)."""
    from puertas import aprobacion
    a = aprobacion(pub, clave)
    return bool(a) and a["sha256"] == sha and a.get("huella_pieza") == huella_pieza(pdir, x, copias, contexto(pub, cfg))


def _status_actual(yt, vid):
    it = yt.videos().list(part="status", id=vid).execute().get("items", [])
    if not it:
        raise RuntimeError(f"YouTube no encuentra el video {vid}")
    return {k: v for k, v in it[0]["status"].items() if k in CAMPOS_STATUS}, it[0]["status"]


def subir(pdir, clave, simular=False, yt=None, media=_media, ahora=None):
    from puertas import margen_minutos, revisar, tabla, todo_ok
    pdir = Path(pdir)
    cfg = config()
    pub = publicacion(pdir)
    x = pieza(pub, clave)
    d = next((y for y in x["destinos"] if y["red"] == "youtube"), None)
    if not d or d["ruta"] != "api":
        sys.exit(f"La pieza {clave} no va a YouTube por la ruta api")
    R = revisar(pdir, clave, "youtube", ahora=ahora)
    p(tabla(R))
    if not todo_ok(R):
        p("PUERTAS CERRADAS: no se sube nada")
        return None
    body, fecha = cuerpo(pub, x, d, cfg)
    if simular:
        p("SIMULACIÓN (no se envía nada). Se sube privado y sin fecha con:")
        p(json.dumps(body, ensure_ascii=False, indent=1))
        p(f"y al final, si todo salió bien: publishAt {fecha}" if fecha else "y queda privado (nivel 1)")
        return {"simulado": True, "body": body, "publishAt": fecha}
    yc = youtube_de(cfg, pub.get("canal"))       # 0.2.0: canal confirmado y avisos del canal del proyecto
    canal_id = yc.get("canal_id")
    if not canal_id:
        p("Falta confirmar el canal: python yt_api.py canal y, si Patricio dice que es el correcto, --confirmar"
          f" (para un canal con configuración propia: --confirmar --canal {pub.get('canal')}).")
        return None
    arch = ruta_segura(pdir, x["archivo"])
    sha = huella(arch)
    TMP.mkdir(parents=True, exist_ok=True)
    candado = TMP / f"subiendo_{sha[:16]}_youtube.lock"
    try:
        fd = os.open(candado, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, f"{os.getpid()} {ahora_utc().isoformat()}".encode())
        os.close(fd)
    except FileExistsError:
        p(f"YA HAY UNA SUBIDA EN CURSO de este archivo ({candado.name}). No se lanza otra. Si de verdad no hay "
          "ninguna (el PC se apagó), revisar YouTube Studio y recién ahí borrar ese .lock.")
        return None
    copias, medios = {}, []
    base = dict(proyecto=str(pdir), id=pub["id"], version=pub["version"], pieza=clave, red="youtube", ruta="api",
                sha256=sha, fecha_publicacion=d["fecha"], zona=d["zona"])
    try:
        # dentro del candado se vuelve a comprobar todo lo que pudo cambiar mientras tanto
        mot = ya_enviado(sha, "youtube", pub["id"], clave)
        if mot:
            p("NO SE SUBE: " + "; ".join(mot))
            return None
        try:
            copias["archivo"] = _copia_verificada(arch, sha)
            for k in ("miniatura", "subtitulos"):
                if x.get(k):
                    q = ruta_segura(pdir, x[k])
                    copias[k] = _copia_verificada(q, huella(q))
        except RuntimeError as e:
            p(f"NO SE SUBE: {e}. Aprobar de nuevo.")
            return None
        if not _vigente(pdir, pub, clave, x, cfg, sha, copias):
            p("NO SE SUBE: la aprobación ya no está vigente (revocada, cancelada o la pieza cambió).")
            return None
        yt = yt or servicio()
        conectado = yt.channels().list(part="id", mine=True).execute().get("items", [{}])[0].get("id")
        if conectado != canal_id:
            p(f"NO SE SUBE: el permiso de YouTube es de otro canal ({conectado}), no del confirmado ({canal_id}).")
            return None
        registrar(estado="en_curso", nota="subida iniciada", **base)    # falla aquí (antes de subir) si el CSV está bloqueado
        try:
            m = media(copias["archivo"], chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/*")
            medios.append(m)
            req = yt.videos().insert(part="snippet,status", body=body, notifySubscribers=yc.get("notificar", True),
                                     media_body=m)
            resp, t0 = None, time.time()
            while resp is None:
                estado_s, resp = req.next_chunk(num_retries=5)
                if estado_s:
                    p(f"subiendo {int(estado_s.progress() * 100)} % ({time.time() - t0:.0f} s)")
        except Exception as e:
            # no se sabe si YouTube alcanzó a recibirlo: «incierto» bloquea otro envío hasta revisarlo en Studio
            diario(estado="incierto", error=str(e)[:300], **base)
            registrar(estado="incierto", nota=f"la subida se cortó: {str(e)[:200]}", **base)
            p(f"SUBIDA INCIERTA: {str(e)[:300]}")
            p("Mirar en YouTube Studio si quedó un video. Si quedó, anotarlo con anotar.py (subido_privado con su enlace); "
              "si no, anotarlo como error. Hasta entonces no se puede volver a subir esta pieza.")
            return None
        vid = resp["id"]
        enlace = f"https://youtu.be/{vid}"
        diario(estado="subido_privado", video=vid, enlace=enlace, respuesta=resp, **base)   # primero el diario
        registrar(estado="subido_privado", enlace=enlace, nota="subido privado, sin fecha todavía", **base)
        fallos = []
        if "miniatura" in copias:
            try:
                m = media(copias["miniatura"], mimetype=MIME.get(copias["miniatura"].suffix, "image/png"))
                medios.append(m)
                yt.thumbnails().set(videoId=vid, media_body=m).execute()
            except Exception as e:  # p. ej. canal sin verificar por teléfono, o un Short aún procesándose
                fallos.append(f"miniatura: {str(e)[:120]}")
        if "subtitulos" in copias:
            try:
                m = media(copias["subtitulos"], mimetype="application/octet-stream")
                medios.append(m)
                leng = x.get("idioma", yc.get("idioma", "es"))     # 0.2.0: el idioma de la pista sale de la pieza o del canal
                yt.captions().insert(part="snippet", body={"snippet": {"videoId": vid, "language": leng,
                                                                       "name": NOMBRE_PISTA.get(str(leng)[:2], "Español"),
                                                                       "isDraft": False}},
                                     media_body=m).execute()
            except Exception as e:
                fallos.append(f"subtítulos: {str(e)[:120]}")
        if x.get("lista"):
            try:
                yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": x["lista"], "resourceId": {
                    "kind": "youtube#video", "videoId": vid}}}).execute()
            except Exception as e:
                fallos.append(f"lista: {str(e)[:120]}")
        quedo, notas = "subido_privado", list(fallos)
        if fecha:
            ahora2 = ahora or ahora_utc()
            if fallos:
                notas.append("NO se programó: falta completar lo de arriba; queda privado")
            elif not _vigente(pdir, pub, clave, x, cfg, sha, copias):
                notas.append("NO se programó: la aprobación dejó de estar vigente durante la subida; queda privado")
            elif a_utc(d["fecha"], d["zona"]) < ahora2 + dt.timedelta(minutes=cfg.get("minutos_minimos_antes", 30)):
                notas.append("NO se programó: la hora quedó demasiado cerca; queda privado (elegir otra y aprobar)")
            else:
                try:
                    st, _ = _status_actual(yt, vid)
                    st.update({"privacyStatus": "private", "publishAt": fecha})
                    r2 = yt.videos().update(part="status", body={"id": vid, "status": st}).execute()
                    if r2.get("status", {}).get("publishAt"):
                        quedo = "programado"
                    else:
                        notas.append("YouTube no confirmó la fecha: queda privado, revisar en Studio")
                except Exception as e:
                    notas.append(f"NO se programó: {str(e)[:150]}; queda privado")
        if quedo == "programado":
            diario(estado="programado", video=vid, enlace=enlace, publishAt=fecha, **base)
            registrar(estado="programado", enlace=enlace, nota="; ".join(notas), **base)
        elif notas:
            registrar(estado="subido_privado", enlace=enlace, nota="; ".join(notas), **base)
        try:
            from calendario import estado as cal_estado
            cal_estado(f"{pub['id']}_{pub['version']}_{clave}_youtube", quedo, enlace, "; ".join(notas))
        except SystemExit:
            p("AVISO: la pieza no estaba en el calendario (correr calendario.py importar)")
        p(f"LISTO {quedo}: {enlace} · publica {fecha if quedo == 'programado' else '— (privado)'}")
        for n in notas:
            p("AVISO", n)
        return {"id": vid, "estado": quedo, "notas": notas}
    finally:
        for m in medios:
            _cerrar(m)
        for q in copias.values():  # copias temporales propias del gerente, no originales
            try:
                Path(q).unlink(missing_ok=True)
            except OSError as e:
                p(f"AVISO: no pude borrar la copia temporal {Path(q).name} ({e}); se puede borrar a mano")
        try:
            candado.unlink(missing_ok=True)
        except OSError:
            p(f"AVISO: no pude quitar el candado {candado.name}")


def desprogramar(pdir, clave, por, yt=None, ahora=None):
    pub = publicacion(pdir)
    fila = ultimo_estado(lambda r: (r["id"], r["version"], r["pieza"], r["red"])).get(
        (pub["id"], pub["version"], clave, "youtube"))
    if not fila or fila["estado"] not in ("programado", "subido_privado") or not fila["enlace"]:
        sys.exit(f"No hay un video programado de {clave} en el registro")
    vid = fila["enlace"].rsplit("/", 1)[-1]
    yt = yt or servicio()
    st, completo = _status_actual(yt, vid)
    if completo.get("privacyStatus") == "public":
        sys.exit("El video ya es público: no se toca (cambiar su privacidad necesita una decisión aparte de Patricio).")
    if completo.get("publishAt"):
        hora = dt.datetime.fromisoformat(completo["publishAt"].replace("Z", "+00:00"))
        if hora <= (ahora or ahora_utc()) + dt.timedelta(minutes=10):
            sys.exit("Faltan menos de 10 minutos para que se publique (o ya pasó la hora): no se toca para no chocar "
                     "con la publicación. Revisarlo en YouTube Studio.")
    st["privacyStatus"] = "private"
    st.pop("publishAt", None)
    r2 = yt.videos().update(part="status", body={"id": vid, "status": st}).execute()
    if r2.get("status", {}).get("publishAt"):
        sys.exit("YouTube mantuvo la fecha: revisar en Studio.")
    base = dict(proyecto=str(pdir), id=pub["id"], version=pub["version"], pieza=clave, red="youtube", ruta="api",
                sha256=fila["sha256"], fecha_publicacion=fila["fecha_publicacion"], zona=fila["zona"], enlace=fila["enlace"])
    diario(estado="cancelado", por=por, **base)
    registrar(estado="cancelado", nota=f"desprogramado, queda privado (sí de {por})", **base)
    try:
        from calendario import estado as cal_estado
        cal_estado(f"{pub['id']}_{pub['version']}_{clave}_youtube", "cancelado", fila["enlace"], f"desprogramado (sí de {por})")
    except SystemExit:
        pass
    p(f"LISTO: {fila['enlace']} queda privado y sin fecha de publicación. Para volver a publicarlo hace falta una aprobación nueva.")


def _consulta(ya, inicio, fin, metricas, **k):
    return ya.reports().query(ids="channel==MINE", startDate=inicio, endDate=fin, metrics=metricas, **k).execute()


def _filas(r):
    cab = [h["name"] for h in r.get("columnHeaders", [])]
    return [dict(zip(cab, f)) for f in r.get("rows", [])]


def _dia_analytics(iso_utc):
    """YouTube Analytics cuenta los días en hora del Pacífico: la fecha de inicio se calcula en esa zona."""
    from zoneinfo import ZoneInfo
    t = dt.datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    return t.astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat()


def metricas(vid, pdir=None, yt=None, ya=None):
    from googleapiclient.errors import HttpError
    yt = yt or servicio()
    ya = ya or servicio("youtubeAnalytics", "v2")
    its = yt.videos().list(part="snippet,statistics,contentDetails,status", id=vid).execute().get("items", [])
    if not its:
        sys.exit(f"YouTube no encuentra el video {vid} (¿es de este canal?)")
    v = its[0]
    inicio = _dia_analytics(v["snippet"]["publishedAt"])
    fin = _dia_analytics(ahora_utc().isoformat())
    out = {"video": vid, "titulo": v["snippet"]["title"], "publicado": v["snippet"]["publishedAt"],
           "medido_utc": ahora_utc().isoformat(timespec="seconds"), "periodo_analytics": [inicio, fin],
           "contadores": v["statistics"]}
    base = "views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes,comments,shares"
    try:
        out["resumen"] = _filas(_consulta(ya, inicio, fin, base, filters=f"video=={vid}"))
    except HttpError as e:
        if getattr(getattr(e, "resp", None), "status", None) != 400:
            raise
        out["resumen"] = _filas(_consulta(ya, inicio, fin, base.replace("engagedViews,", ""), filters=f"video=={vid}"))
    for nombre, k in {"retencion": dict(metrics="audienceWatchRatio,relativeRetentionPerformance", dimensions="elapsedVideoTimeRatio"),
                      "paises": dict(metrics="views,estimatedMinutesWatched", dimensions="country", sort="-views", maxResults=25),
                      "fuentes": dict(metrics="views,estimatedMinutesWatched", dimensions="insightTrafficSourceType", sort="-views")}.items():
        try:
            m = k.pop("metrics")
            out[nombre] = _filas(_consulta(ya, inicio, fin, m, filters=f"video=={vid}", **k))
        except HttpError as e:
            out[nombre] = {"sin_datos": str(e)[:160]}
    out["nota"] = ("YouTube Analytics tarda 1-3 días en consolidar y cuenta días completos en hora del Pacífico (no es una "
                   "ventana exacta de 48 h); a las 48 h los contadores del video son más fiables. Desde fines de agosto "
                   "de 2026 'views' de los largos cuenta desde el primer cuadro: comparar con engagedViews.")
    destino_dir = (carpeta_publicar(pdir) / "metricas") if pdir else (GER / "metricas")
    dest = escribir_nuevo(destino_dir / f"{vid}_{fin}.json", json.dumps(out, ensure_ascii=False, indent=1))
    p(f"LISTO métricas de {vid}: {dest}")
    return out


def _subidas_publicas_90d(yt, lista, hoy):
    limite = (hoy - dt.timedelta(days=90)).isoformat()
    ids, token = [], None
    for _ in range(10):                       # hasta 500 subidas recientes
        k = dict(part="contentDetails", playlistId=lista, maxResults=50)
        if token:
            k["pageToken"] = token
        r = yt.playlistItems().list(**k).execute()
        nuevos = [i["contentDetails"]["videoId"] for i in r.get("items", [])
                  if i["contentDetails"].get("videoPublishedAt", "")[:10] >= limite]
        ids += nuevos
        token = r.get("nextPageToken")
        if not token or len(nuevos) < len(r.get("items", [])):
            break
    publicos = 0
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="status", id=",".join(ids[i:i + 50])).execute()
        publicos += sum(1 for v in r.get("items", []) if v["status"].get("privacyStatus") == "public")
    return publicos


def progreso(yt=None, ya=None):
    yt = yt or servicio()
    ya = ya or servicio("youtubeAnalytics", "v2")
    hoy = ahora_utc().date()
    c = yt.channels().list(part="statistics,contentDetails", mine=True).execute()["items"][0]
    subs = int(c["statistics"].get("subscriberCount", 0))
    try:
        subidas90 = _subidas_publicas_90d(yt, c["contentDetails"]["relatedPlaylists"]["uploads"], hoy)
    except Exception:
        subidas90 = None
    a365 = (hoy - dt.timedelta(days=365)).isoformat()
    a90 = (hoy - dt.timedelta(days=90)).isoformat()
    por_tipo = {f["creatorContentType"]: f for f in _filas(_consulta(ya, a365, hoy.isoformat(), "views,estimatedMinutesWatched",
                                                                       dimensions="creatorContentType"))}
    shorts90 = {f["creatorContentType"]: f for f in _filas(_consulta(ya, a90, hoy.isoformat(), "views",
                                                                       dimensions="creatorContentType"))}
    horas = round(sum(float(por_tipo.get(t, {}).get("estimatedMinutesWatched", 0)) for t in ("VIDEO_ON_DEMAND", "LIVE_STREAM")) / 60, 1)
    vshorts = int(shorts90.get("SHORTS", {}).get("views", 0))
    res = {"medido": hoy.isoformat(), "suscriptores": subs, "horas_largos_365d": horas, "vistas_shorts_90d": vshorts,
           "subidas_publicas_90d": subidas90, "metas": {},
           "nota": "ESTIMACIÓN: YouTube cuenta solo horas públicas válidas y vistas de Shorts del feed. "
                   "La elegibilidad real se ve en YouTube Studio → Ingresos."}
    for nivel_, m in YPP.items():
        res["metas"][nivel_] = {"suscriptores": f"{subs}/{m['subs']}", "horas": f"{horas}/{m['horas']}",
                                "shorts": f"{vshorts}/{m['shorts']}",
                                "alcanzaria_estimado": subs >= m["subs"] and (horas >= m["horas"] or vshorts >= m["shorts"])
                                and (("subidas_90d" not in m) or (subidas90 or 0) >= m["subidas_90d"])}
    p(json.dumps(res, ensure_ascii=False, indent=1))
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit("uso: python yt_api.py autorizar|canal|subir|metricas|progreso|desprogramar ...")
    if a[0] == "autorizar":
        autorizar()
    elif a[0] == "canal":
        canal(confirmar="--confirmar" in a, nombre=opt(a, "--canal"))
    elif a[0] == "subir":
        r = subir(proyecto_dir(a[1]), a[2], simular="--simular" in a)
        sys.exit(0 if r else 1)
    elif a[0] == "desprogramar":
        por = opt(a, "--confirmado-por")
        if not por:
            sys.exit("Falta --confirmado-por <quién dijo que sí>")
        desprogramar(proyecto_dir(a[1]), a[2], por)
    elif a[0] == "metricas":
        metricas(a[1], proyecto_dir(opt(a, "--proyecto")) if "--proyecto" in a else None)
    elif a[0] == "progreso":
        progreso()
    else:
        sys.exit(f"Operación desconocida: {a[0]}")
