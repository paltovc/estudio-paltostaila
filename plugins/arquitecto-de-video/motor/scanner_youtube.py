# Escáner de nichos con la API oficial de YouTube (YouTube Data API v3, solo datos públicos, sin OAuth).
# Busca videos recientes de varios términos, compara cada uno con la MEDIANA de los últimos 10 envíos de su canal
# y ordena por "nota" = vistas / mediana. Nota 10 = el video hizo 10 veces lo normal de ese canal.
#
# La clave se lee de YT_API_KEY (variable de entorno) o de %USERPROFILE%\EstudioPaltostaila\claves\youtube.env
# (una línea YT_API_KEY=...).
# Nunca se muestra ni se guarda en los resultados. Sin clave: usar tendencias.py (yt-dlp, más lento).
#
#   python scanner_youtube.py "finanzas personales" "ahorrar dinero" "invertir desde cero" [--dias 10] [--region CL]
#          [--idioma es] [--paginas 2] [--shorts | --largos] [--min-min 8] [--max-busquedas 40] [--nombre finanzas]
#   python scanner_youtube.py --terminos terminos.txt ...      (un término por línea)
#
# Cuota diaria del proyecto (se reinicia a medianoche hora del Pacífico): cada búsqueda vale 100 unidades
# (100 búsquedas al día como máximo); estadísticas de 50 videos, datos de 50 canales o una lista de envíos = 1.
# El escáner se detiene solo antes de pasarse y al final dice cuánto gastó.
# Política de la API: los datos guardados se renuevan o borran a los 30 días (resultados con fecha en el nombre).
import csv, json, os, re, statistics, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ESTUDIO = Path.home() / "EstudioPaltostaila"
API = "https://www.googleapis.com/youtube/v3/"
args = sys.argv[1:]
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
gasto = {"busquedas": 0, "unidades": 0}


def clave():
    k = os.environ.get("YT_API_KEY", "").strip()
    env = ESTUDIO / "claves" / "youtube.env"
    for archivo in (env, ESTUDIO / ".env"):
        if not k and archivo.exists():
            for linea in archivo.read_text(encoding="utf-8-sig").splitlines():
                if linea.strip().startswith("YT_API_KEY="):
                    k = linea.split("=", 1)[1].strip().strip('"').strip("'")
    if not k or "COLE" in k.upper() or "PEGA" in k.upper():
        sys.exit(f"No hay clave de la API de YouTube. Crear {env} con la línea YT_API_KEY=<tu clave> "
                 "(ver instrucciones en la skill instalar-estudio) o usar tendencias.py.")
    return k


KEY = None


def get(recurso, coste, **p):
    if recurso == "search":
        if gasto["busquedas"] >= int(opt("--max-busquedas", 40)):
            raise RuntimeError("límite de búsquedas de esta corrida")
        gasto["busquedas"] += 1
    gasto["unidades"] += coste
    url = API + recurso + "?" + urllib.parse.urlencode({**p, "key": KEY})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", "replace").replace(KEY, "***")
        motivo = re.findall(r'"reason":\s*"(\w+)"', cuerpo)
        raise RuntimeError(f"YouTube respondió {e.code} {motivo[:1]}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"sin conexión con YouTube: {str(e.reason).replace(KEY, '***')}") from None


def segundos(iso):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    d, h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0, 0)
    return d * 86400 + h * 3600 + mi * 60 + s


def lotes(xs, n=50):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def main():
    global KEY
    if not args or args[0] in ("-h", "--ayuda"):
        sys.exit(__doc__)
    KEY = clave()
    terminos = [a for a in args if not a.startswith("--") and a not in
                {opt(k) for k in ("--dias", "--region", "--idioma", "--paginas", "--min-min", "--max-busquedas", "--nombre", "--terminos")}]
    if opt("--terminos"):
        terminos += [l.strip() for l in Path(opt("--terminos")).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    dias, region, idioma = int(opt("--dias", 10)), opt("--region", "CL"), opt("--idioma", "es")
    paginas, min_min = int(opt("--paginas", 2)), float(opt("--min-min", 0))
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids, aviso = [], ""
    try:
        for t in terminos:
            token = None
            for _ in range(paginas):
                p = dict(part="id", q=t, type="video", publishedAfter=desde, order="viewCount", maxResults=50,
                         regionCode=region, relevanceLanguage=idioma)
                if "--shorts" in args:
                    p["videoDuration"] = "short"
                if token:
                    p["pageToken"] = token
                r = get("search", 100, **p)
                ids += [i["id"]["videoId"] for i in r.get("items", []) if i.get("id", {}).get("videoId")]
                token = r.get("nextPageToken")
                print(f"  '{t}': {len(r.get('items', []))} videos", flush=True)
                if not token:
                    break
    except RuntimeError as e:
        aviso = f"Búsqueda detenida: {e}. Se analizan los videos encontrados hasta ahí."
        print(aviso)
    ids = list(dict.fromkeys(ids))
    videos = {}
    for l in lotes(ids):
        for v in get("videos", 1, part="snippet,statistics,contentDetails", id=",".join(l)).get("items", []):
            dur = segundos(v["contentDetails"].get("duration"))
            if "--shorts" in args and dur > 180 or "--largos" in args and dur <= 180 or dur < min_min * 60:
                continue
            videos[v["id"]] = {"id": v["id"], "titulo": v["snippet"]["title"], "canal": v["snippet"]["channelTitle"],
                               "canal_id": v["snippet"]["channelId"], "vistas": int(v["statistics"].get("viewCount", 0)),
                               "duracion_min": round(dur / 60, 1), "fecha": v["snippet"]["publishedAt"][:10],
                               "miniatura": (v["snippet"].get("thumbnails", {}).get("high") or {}).get("url", "")}
    canales = {}
    for l in lotes(list({v["canal_id"] for v in videos.values()})):
        for c in get("channels", 1, part="statistics,contentDetails", id=",".join(l)).get("items", []):
            canales[c["id"]] = {"inscritos": None if c["statistics"].get("hiddenSubscriberCount") else int(c["statistics"].get("subscriberCount", 0)),
                                "envios": c["contentDetails"]["relatedPlaylists"]["uploads"], "ultimos": []}
    for cid, c in canales.items():
        try:
            r = get("playlistItems", 1, part="contentDetails", playlistId=c["envios"], maxResults=11)
            c["ultimos"] = [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        except RuntimeError:
            pass
    todos = list({x for c in canales.values() for x in c["ultimos"]})
    vistas = {}
    for l in lotes(todos):
        for v in get("videos", 1, part="statistics", id=",".join(l)).get("items", []):
            vistas[v["id"]] = int(v["statistics"].get("viewCount", 0))
    filas = []
    for v in videos.values():
        c = canales.get(v["canal_id"], {})
        otros = [vistas[x] for x in c.get("ultimos", []) if x != v["id"] and x in vistas][:10]
        med = statistics.median(otros) if len(otros) >= 3 else None
        filas.append({**v, "inscritos": c.get("inscritos"), "mediana_canal": int(med) if med else None,
                      "nota": round(v["vistas"] / med, 1) if med else None,
                      "enlace": f"https://www.youtube.com/watch?v={v['id']}"})
    filas.sort(key=lambda f: -(f["nota"] or 0))
    nombre = re.sub(r"[^\w-]+", "-", opt("--nombre", terminos[0] if terminos else "scanner")).strip("-")[:40]
    out = ESTUDIO / "tendencias" / f"scanner_{nombre}_{datetime.now():%Y-%m-%d}"
    out.mkdir(parents=True, exist_ok=True)
    campos = ["titulo", "canal", "inscritos", "vistas", "mediana_canal", "nota", "duracion_min", "fecha", "enlace", "miniatura"]
    with open(out / "resultado.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore", delimiter=";")
        w.writeheader(); w.writerows(filas)
    pequenos = [f for f in filas if f["nota"] and f["nota"] >= 10 and (f["inscritos"] or 0) < 20000]
    md = [f"# Escáner: {', '.join(terminos)}", "",
          f"Últimos {dias} días, región {region}, idioma {idioma}. {len(filas)} videos de {len(canales)} canales.",
          f"Nota = vistas / mediana de los últimos 10 envíos del canal. Canales pequeños (<20 mil) con nota ≥10: {len(pequenos)}.",
          f"Cuota usada: {gasto['busquedas']} búsquedas, {gasto['unidades']} unidades.", "" + (f"**{aviso}**\n" if aviso else ""),
          "| # | nota | vistas | mediana canal | inscritos | min | canal | título |", "|---|---|---|---|---|---|---|---|"]
    for k, f in enumerate(filas[:40], 1):
        md.append(f"| {k} | {f['nota'] or '?'} | {f['vistas']:,} | {f['mediana_canal'] or '?'} | "
                  f"{f['inscritos'] if f['inscritos'] is not None else 'oculto'} | {f['duracion_min']} | {f['canal']} | [{f['titulo']}]({f['enlace']}) |")
    md += ["", "Siguiente: mirar las miniaturas de los 40 primeros (con rostro / sin rostro / duda), buscar lo que se repite"
           " en al menos 70 % y confirmar abriendo 5 videos de cada canal. Una nota alta sola puede ser suerte: buscar canales que repiten."]
    (out / "resultado.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[:6]))
    print(f"\nguardado en {out}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        sys.exit(f"Error: {e}. Cuota usada: {gasto['busquedas']} búsquedas, {gasto['unidades']} unidades.")
