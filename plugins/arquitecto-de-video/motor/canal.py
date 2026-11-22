# Historia de un canal de YouTube (investigación de canales que se viralizaron): qué publicó, cuándo despegó y qué
# cambió antes y después. Solo datos públicos con yt-dlp, sin cookies ni inicio de sesión; no baja ningún video.
#   python canal.py "<url del canal>" [--max 400] [--exactas] [--comparar "<url de otro canal>"] [--dest carpeta]
#     <url>: https://www.youtube.com/@nombre (o /channel/UC..., /c/..., /user/...; da lo mismo si termina en /videos)
#     --max N      cuántos videos se leen de cada pestaña (largos y Shorts), los más recientes primero (por defecto 400)
#     --exactas    además pide la fecha exacta de cada video (un pedido por video: lento, varios minutos en canales grandes)
#     --comparar   analiza también otro canal (p. ej. el mismo nicho en otro idioma) y deja comparacion.md
# Deja en %USERPROFILE%\EstudioPaltostaila\referentes\canal_<id>\ (o canal_<id>_2 si ya existe: nunca encima):
#   datos.json (cada video con fecha, vistas, duración, título, múltiplo sobre la mediana) · informe_base.md · vistas.png
# Límites (se escriben también en el informe):
#   - En la lista rápida de un canal, YouTube no da la fecha exacta: yt-dlp la estima desde «hace 3 semanas»
#     (fecha_aproximada = true). Con --exactas se pide la real (más lento). Sin ninguna fecha se usa el orden de la lista.
#   - Las vistas de la lista de Shorts vienen redondeadas («1,2 M») y muchas veces sin duración.
#   - Solo se ve lo que hoy está público: lo borrado u oculto no aparece; las vistas son las de hoy, no las de su semana.
#   - El análisis es para entender y aprender; el material de otros canales no se reutiliza en los videos propios.
import json, re, statistics, subprocess, sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from redes import ESTUDIO, llamar, nombre_seguro, ytdlp

try:      # un log de Windows en cp1252 no puede botar el informe por un carácter
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

PESTANAS = {"largo": "videos", "short": "shorts"}
LIMITES = [
    "Las fechas de la lista rápida son aproximadas (yt-dlp las estima desde «hace N semanas»); con --exactas se piden las reales.",
    "Las vistas de los Shorts vienen redondeadas y casi siempre sin duración.",
    "Solo aparece lo que hoy es público; las vistas son las acumuladas a hoy (un video viejo tuvo más tiempo para sumar).",
    "El múltiplo es vistas / mediana del mismo formato en todo lo leído; el «despegue» es el primer video, en orden de "
    "publicación, que llega a 3 y a 10 veces esa mediana.",
]
VACIAS = set("""
de la el los las y en un una que por para con del al se su sus lo es como más mas pero sin sobre este esta esto tu te mi
the a an and or of to in on for with your you my is are how what why this that from at by it be i we our not
o os as um uma do da dos das no na nos nas com por para seu sua você voce não nao mais como que
""".split())
IDIOMA_PALABRAS = {"es": set("de la el los las y en que por para con del una como más pero tu".split()),
                   "en": set("the a and of to in for with your you how what why is this".split()),
                   "pt": set("de o os as e em que por para com do da um uma você não mais".split())}


def nombre_libre(p):
    p = Path(p)
    if not p.exists():
        return p
    k = 2
    while p.with_name(f"{p.name}_{k}").exists():
        k += 1
    return p.with_name(f"{p.name}_{k}")


def base_canal(url):
    u = url.strip().split("?")[0].rstrip("/")
    if "youtube.com" not in u and "youtu.be" not in u:
        if u.startswith("@"):
            u = "https://www.youtube.com/" + u
        else:
            sys.exit("canal.py trabaja con canales de YouTube: pasar la dirección del canal (https://www.youtube.com/@nombre)")
    u = re.sub(r"/(videos|shorts|streams|featured|playlists|about|community|live|podcasts)$", "", u)
    if not re.search(r"/(@[^/]+|channel/[^/]+|c/[^/]+|user/[^/]+)$", u):
        sys.exit(f"No reconozco la dirección del canal: {url} (usar https://www.youtube.com/@nombre o /channel/UC...)")
    return u


def _fecha(e):
    """(fecha ISO o None, aproximada). La lista rápida trae upload_date/timestamp estimados (approximate_date)."""
    d = e.get("upload_date")
    if d and re.fullmatch(r"\d{8}", str(d)):
        return f"{d[:4]}-{d[4:6]}-{d[6:]}", True
    t = e.get("timestamp") or e.get("release_timestamp")
    if isinstance(t, (int, float)):
        return datetime.fromtimestamp(t, timezone.utc).date().isoformat(), True
    return None, True


def listar(base, formato, maximo):
    """(datos del canal, videos) de una pestaña, del más reciente al más antiguo, sin bajar nada."""
    url = f"{base}/{PESTANAS[formato]}"
    try:
        d = json.loads(llamar(["-J", "--flat-playlist", "--no-warnings", "--playlist-end", str(maximo),
                               "--extractor-args", "youtubetab:approximate_date", url], timeout=900))
    except Exception as e:
        print(f"aviso: no se pudo leer {url} -> {str(e)[-200:]}", flush=True)
        return {}, []
    out = []
    for i, e in enumerate(x for x in d.get("entries") or [] if x and x.get("id")):
        f, aprox = _fecha(e)
        out.append({"id": e["id"], "titulo": e.get("title") or "", "fecha": f, "fecha_aproximada": aprox if f else None,
                    "vistas": e.get("view_count"), "duracion_s": e.get("duration"), "formato": formato,
                    "orden_lista": i, "url": (f"https://www.youtube.com/shorts/{e['id']}" if formato == "short"
                                              else f"https://www.youtube.com/watch?v={e['id']}")})
    return d, out


def exactas(base, formato, videos, maximo):
    """Fecha exacta (y vistas y duración al día) de cada video: un pedido por video. Lo que falle queda como estaba."""
    url = f"{base}/{PESTANAS[formato]}"
    cmd = ytdlp() + ["--skip-download", "--no-warnings", "--ignore-errors", "--sleep-requests", "0.5",
                     "--playlist-end", str(maximo), "--print", "%(id)s\t%(upload_date)s\t%(view_count)s\t%(duration)s", url]
    print(f"fechas exactas de {url} (un pedido por video; puede tardar)...", flush=True)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=4 * 3600)
    except subprocess.TimeoutExpired:
        print("aviso: las fechas exactas tardaron demasiado; quedan las aproximadas", flush=True)
        return 0
    por_id = {v["id"]: v for v in videos}
    n = 0
    for l in r.stdout.splitlines():
        p = l.split("\t")
        if len(p) != 4 or p[0] not in por_id:
            continue
        v = por_id[p[0]]
        if re.fullmatch(r"\d{8}", p[1]):
            v["fecha"], v["fecha_aproximada"] = f"{p[1][:4]}-{p[1][4:6]}-{p[1][6:]}", False
            n += 1
        if p[2].isdigit():
            v["vistas"] = int(p[2])
        if re.fullmatch(r"\d+(\.\d+)?", p[3]):
            v["duracion_s"] = float(p[3])
    return n


def cronologico(videos):
    """Del más antiguo al más nuevo: por fecha si la hay; si no, el orden inverso de la lista (que viene del más nuevo)."""
    if videos and all(v["fecha"] for v in videos):
        return sorted(videos, key=lambda v: (v["fecha"], -v["orden_lista"]))
    return sorted(videos, key=lambda v: -v["orden_lista"])


def titulos(vs):
    """Patrones de los títulos: largo, números, preguntas, mayúsculas, emojis, separadores, palabras repetidas e idioma."""
    ts = [v["titulo"] for v in vs if v["titulo"]]
    if not ts:
        return {}
    pct = lambda f: round(100 * sum(1 for t in ts if f(t)) / len(ts))
    palabras = [w for t in ts for w in re.findall(r"[^\W\d_]{3,}", t.lower())]
    cuenta = Counter(w for w in palabras if w not in VACIAS)
    puntos = {k: sum(1 for w in re.findall(r"[^\W\d_]+", " ".join(ts).lower()) if w in s) for k, s in IDIOMA_PALABRAS.items()}
    idioma = max(puntos, key=puntos.get) if any(puntos.values()) else "?"
    return {"titulos": len(ts), "caracteres_mediana": statistics.median(len(t) for t in ts),
            "palabras_mediana": statistics.median(len(t.split()) for t in ts),
            "con_numero_pct": pct(lambda t: re.search(r"\d", t)), "pregunta_pct": pct(lambda t: "?" in t or "¿" in t),
            "exclamacion_pct": pct(lambda t: "!" in t or "¡" in t),
            "palabra_en_mayusculas_pct": pct(lambda t: re.search(r"\b[A-ZÁÉÍÓÚÑÃÕÇ]{3,}\b", t)),
            "emoji_pct": pct(lambda t: any(ord(c) >= 0x2600 for c in t)),
            "separador_pct": pct(lambda t: re.search(r"[|:–—]", t)),
            "palabras_repetidas": [[w, n] for w, n in cuenta.most_common(15) if n >= 2],
            "idioma_estimado": idioma, "idioma_puntos": puntos}


def frecuencia(vs):
    """Videos por mes (con fecha) y ritmo medio: videos cada 30 días en el tramo cubierto."""
    fs = sorted(v["fecha"] for v in vs if v["fecha"])
    meses = Counter(f[:7] for f in fs)
    ritmo = None
    if len(fs) >= 2:
        dias = (date.fromisoformat(fs[-1]) - date.fromisoformat(fs[0])).days or 1
        ritmo = round(len(fs) / dias * 30, 1)
    return dict(sorted(meses.items())), ritmo


TRAMOS = {"largo": [(0, 60, "<1 min"), (60, 180, "1-3"), (180, 480, "3-8"), (480, 900, "8-15"), (900, 1800, "15-30"),
                    (1800, 3600, "30-60"), (3600, 10 ** 9, ">60")],
          "short": [(0, 15, "<15 s"), (15, 30, "15-30"), (30, 45, "30-45"), (45, 61, "45-60"), (61, 10 ** 9, ">60 s")]}


def duraciones(vs, formato):
    con = [v["duracion_s"] for v in vs if isinstance(v.get("duracion_s"), (int, float))]
    return {"con_duracion": len(con), "mediana_s": statistics.median(con) if con else None,
            "tramos": {n: sum(1 for d in con if a <= d < b) for a, b, n in TRAMOS[formato]}}


def resumen_tramo(vs):
    """Lo que caracteriza un tramo de videos (para comparar antes y después del despegue)."""
    if not vs:
        return {}
    dur = [v["duracion_s"] for v in vs if isinstance(v.get("duracion_s"), (int, float))]
    _, ritmo = frecuencia(vs)
    t = titulos(vs)
    vis = [v["vistas"] for v in vs if v.get("vistas")]
    return {"videos": len(vs), "desde": vs[0]["fecha"], "hasta": vs[-1]["fecha"],
            "vistas_mediana": statistics.median(vis) if vis else None,
            "duracion_mediana_s": statistics.median(dur) if dur else None, "videos_cada_30_dias": ritmo,
            "titulo_caracteres": t.get("caracteres_mediana"), "titulo_numero_pct": t.get("con_numero_pct"),
            "titulo_pregunta_pct": t.get("pregunta_pct"), "titulo_mayusculas_pct": t.get("palabra_en_mayusculas_pct"),
            "ejemplos": [v["titulo"] for v in vs[:3]]}


def analizar_formato(videos, formato):
    vs = cronologico([v for v in videos if v["formato"] == formato])
    vis = [v["vistas"] for v in vs if v.get("vistas")]
    if not vs:
        return {"videos": 0}
    med = statistics.median(vis) if vis else None
    for i, v in enumerate(vs):
        v["n"] = i + 1
        v["multiplo"] = round(v["vistas"] / med, 2) if med and v.get("vistas") else None
        previas = [x["vistas"] for x in vs[max(0, i - 10):i] if x.get("vistas")]
        mp = statistics.median(previas) if len(previas) >= 3 else None
        v["multiplo_sobre_10_anteriores"] = round(v["vistas"] / mp, 2) if mp and v.get("vistas") else None
    despegue = {}
    for umbral in (3, 10):
        k = next((i for i, v in enumerate(vs) if (v["multiplo"] or 0) >= umbral), None)
        if k is None:
            despegue[f"x{umbral}"] = None
            continue
        v = vs[k]
        despegue[f"x{umbral}"] = {"n": v["n"], "titulo": v["titulo"], "fecha": v["fecha"], "vistas": v["vistas"],
                                  "multiplo": v["multiplo"], "url": v["url"],
                                  "antes": resumen_tramo(vs[max(0, k - 10):k]), "despues": resumen_tramo(vs[k:k + 10])}
    meses, ritmo = frecuencia(vs)
    return {"videos": len(vs), "con_vistas": len(vis), "mediana_vistas": med,
            "con_fecha": sum(1 for v in vs if v["fecha"]), "fechas_exactas": sum(1 for v in vs if v["fecha_aproximada"] is False),
            "despegue": despegue, "por_mes": meses, "videos_cada_30_dias": ritmo, "duraciones": duraciones(vs, formato),
            "titulos": titulos(vs),
            "top10_vistas": [v["id"] for v in sorted(vs, key=lambda v: -(v.get("vistas") or 0))[:10]],
            "top10_multiplo_10_anteriores": [v["id"] for v in sorted(
                (v for v in vs if v["multiplo_sobre_10_anteriores"]), key=lambda v: -v["multiplo_sobre_10_anteriores"])[:10]],
            "lista": vs}


COLOR = {"largo": (36, 99, 166), "short": (240, 130, 40)}


def _letra(tam):
    from PIL import ImageFont
    for n in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def grafico(nombre, an, destino):
    """Vistas de cada video en el tiempo (escala logarítmica), una nube por formato, con su mediana y el despegue x3."""
    import math
    from PIL import Image, ImageDraw
    W, H, L, R, T, B = 1400, 640, 95, 30, 70, 80
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f, fc = _letra(22), _letra(15)
    todos = [v for k in ("largo", "short") for v in an[k].get("lista", []) if v.get("vistas")]
    if not todos:
        d.text((L, T), "sin vistas para graficar", fill=(0, 0, 0), font=f)
        img.save(destino)
        return
    por_fecha = all(v["fecha"] for v in todos)
    if por_fecha:
        xs = [date.fromisoformat(v["fecha"]).toordinal() for v in todos]
        x0, x1 = min(xs), max(xs) or 1
        X = lambda v: L + (date.fromisoformat(v["fecha"]).toordinal() - x0) / max(1, x1 - x0) * (W - L - R)
    else:                     # sin fechas: cada formato en su propio orden de publicación, de 0 a 1
        tot = {k: max(1, an[k].get("videos", 1) - 1) for k in ("largo", "short")}
        X = lambda v: L + (v["n"] - 1) / tot[v["formato"]] * (W - L - R)
    y0, y1 = math.log10(max(1, min(v["vistas"] for v in todos))), math.log10(max(v["vistas"] for v in todos))
    y1 = y1 if y1 > y0 else y0 + 1
    Y = lambda vistas: H - B - (math.log10(max(1, vistas)) - y0) / (y1 - y0) * (H - T - B)
    for e in range(int(y0), int(y1) + 2):                  # líneas guía en 10, 100, 1.000…
        if y0 <= e <= y1 + 0.01:
            yy = Y(10 ** e)
            d.line([L, yy, W - R, yy], fill=(232, 232, 232))
            d.text((8, yy - 9), f"{10 ** e:,}".replace(",", "."), fill=(110, 110, 110), font=fc)
    for k in ("largo", "short"):
        a = an[k]
        for v in a.get("lista", []):
            if v.get("vistas"):
                x, y = X(v), Y(v["vistas"])
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=COLOR[k])
        if a.get("mediana_vistas"):
            yy = Y(a["mediana_vistas"])
            for xx in range(L, W - R, 14):
                d.line([xx, yy, xx + 7, yy], fill=COLOR[k], width=2)
        dx = (a.get("despegue") or {}).get("x3")
        if dx:
            v = next(x for x in a["lista"] if x["n"] == dx["n"])
            xx = X(v)
            for yy in range(T, H - B, 12):
                d.line([xx, yy, xx, yy + 6], fill=COLOR[k], width=1)
            d.text((xx + 4, T + (0 if k == "largo" else 18)), f"despegue x3 ({k})", fill=COLOR[k], font=fc)
    d.text((L, 18), f"{nombre}: vistas de cada video ({'por fecha' if por_fecha else 'por orden de publicación'}, escala log)",
           fill=(20, 20, 20), font=f)
    d.text((L, H - B + 30), "azul = videos largos · naranja = Shorts · línea cortada = mediana del formato · vertical = despegue x3"
           + ("" if por_fecha else " · sin fechas: cada formato va en su propio orden"), fill=(90, 90, 90), font=fc)
    if por_fecha:
        for k in range(6):
            o = x0 + (x1 - x0) * k / 5
            d.text((L + (o - x0) / max(1, x1 - x0) * (W - L - R) - 30, H - B + 8), date.fromordinal(int(o)).strftime("%Y-%m"),
                   fill=(110, 110, 110), font=fc)
    img.save(destino)


def _n(x):
    return "—" if x is None else (f"{x:,.0f}".replace(",", ".") if isinstance(x, (int, float)) and abs(x) >= 100 else str(x))


def informe(info, an, carpeta):
    M = [f"# Historia del canal: {info['nombre']}", "", f"{info['url']} · leído el {info['leido']} · "
         f"{info.get('seguidores') and _n(info['seguidores']) + ' suscriptores · ' or ''}"
         f"{an['largo'].get('videos', 0)} videos largos y {an['short'].get('videos', 0)} Shorts leídos (máximo {info['max']} por pestaña)", "",
         "## Límites de estos datos"] + [f"- {x}" for x in LIMITES] + [""]
    for k, nombre in (("largo", "Videos largos"), ("short", "Shorts")):
        a = an[k]
        if not a.get("videos"):
            M += [f"## {nombre}", "", "No hay (o no se pudieron leer).", ""]
            continue
        por_id = {v["id"]: v for v in a["lista"]}
        M += [f"## {nombre}", "",
              f"- Mediana de vistas: {_n(a['mediana_vistas'])} · videos con fecha: {a['con_fecha']} de {a['videos']} "
              f"({a['fechas_exactas']} exactas) · ritmo: {a['videos_cada_30_dias'] or '—'} videos cada 30 días",
              f"- Duración mediana: {_n(a['duraciones']['mediana_s'])} s · por tramos: "
              + ", ".join(f"{t}: {n}" for t, n in a["duraciones"]["tramos"].items()), ""]
        for u in ("x3", "x10"):
            dx = a["despegue"].get(u)
            if not dx:
                M += [f"**Despegue {u}:** ningún video llega a {u[1:]} veces la mediana.", ""]
                continue
            M += [f"**Despegue {u}:** video {dx['n']} ({dx['fecha'] or 'sin fecha'}) «{dx['titulo']}» · {_n(dx['vistas'])} vistas "
                  f"({dx['multiplo']}x) · {dx['url']}", "", "| | 10 antes | desde ahí (10) |", "|---|---|---|"]
            for campo, et in (("vistas_mediana", "vistas (mediana)"), ("duracion_mediana_s", "duración mediana (s)"),
                              ("videos_cada_30_dias", "videos cada 30 días"), ("titulo_caracteres", "largo del título"),
                              ("titulo_numero_pct", "% títulos con número"), ("titulo_pregunta_pct", "% títulos con pregunta"),
                              ("titulo_mayusculas_pct", "% títulos con MAYÚSCULAS")):
                M.append(f"| {et} | {_n(dx['antes'].get(campo))} | {_n(dx['despues'].get(campo))} |")
            M += ["", "Títulos justo antes: " + " · ".join(f"«{t}»" for t in dx["antes"].get("ejemplos", [])) or "—",
                  "Títulos desde el despegue: " + " · ".join(f"«{t}»" for t in dx["despues"].get("ejemplos", [])), ""]
        M += ["**Los 10 con más vistas:**", "", "| # | fecha | vistas | x mediana | dur | título |", "|---|---|---|---|---|---|"]
        for i, vid in enumerate(a["top10_vistas"], 1):
            v = por_id[vid]
            M.append(f"| {i} | {v['fecha'] or '?'} | {_n(v['vistas'])} | {v['multiplo'] or '?'} | {_n(v.get('duracion_s'))} | "
                     f"[{v['titulo'][:80]}]({v['url']}) |")
        M += ["", "**Los 10 que más superaron a sus 10 anteriores** (señal de tema o empaque que funcionó):", ""]
        M += [f"- {por_id[vid]['multiplo_sobre_10_anteriores']}x · {por_id[vid]['fecha'] or '?'} · «{por_id[vid]['titulo'][:90]}»"
              for vid in a["top10_multiplo_10_anteriores"]] or ["- (pocos videos para comparar)"]
        t = a["titulos"]
        M += ["", "**Títulos:** " + (f"{t['caracteres_mediana']} caracteres y {t['palabras_mediana']} palabras (mediana) · "
              f"número {t['con_numero_pct']} % · pregunta {t['pregunta_pct']} % · exclamación {t['exclamacion_pct']} % · "
              f"MAYÚSCULAS {t['palabra_en_mayusculas_pct']} % · emoji {t['emoji_pct']} % · separador (| : –) {t['separador_pct']} % · "
              f"idioma estimado {t['idioma_estimado']}" if t else "—"),
              "Palabras que se repiten: " + (", ".join(f"{w} ({n})" for w, n in t.get("palabras_repetidas", [])) or "—"), ""]
        meses = list(a["por_mes"].items())[-24:]
        if meses:
            M += ["**Videos por mes** (últimos 24 con fecha): " + " · ".join(f"{m}: {n}" for m, n in meses), ""]
    M += ["## Archivos", "datos.json (cada video con fecha, vistas, duración, título y múltiplos), vistas.png (gráfico).",
          "Siguiente: el analista mira 3-5 videos del despegue con referente.py y escribe qué cambió (empaque, tema, gancho)."]
    (carpeta / "informe_base.md").write_text("\n".join(M) + "\n", encoding="utf-8")
    return M


def analizar_canal(url, maximo=400, con_exactas=False, dest=None):
    base = base_canal(url)
    print(f"leyendo {base} (largos y Shorts, hasta {maximo} de cada uno, sin descargar videos)...", flush=True)
    meta, largos = listar(base, "largo", maximo)
    meta2, cortos = listar(base, "short", maximo)
    if not largos and not cortos:
        sys.exit(f"No se pudo leer ningún video de {base} (¿dirección correcta? ¿canal público?)")
    meta = meta or meta2
    if con_exactas:
        n = exactas(base, "largo", largos, maximo) + exactas(base, "short", cortos, maximo)
        print(f"  {n} fechas exactas", flush=True)
    cid = meta.get("channel_id") or meta.get("uploader_id") or meta.get("id") or base.rsplit("/", 1)[-1]
    info = {"nombre": meta.get("channel") or meta.get("uploader") or re.sub(r" - (Videos|Shorts)$", "", meta.get("title") or cid),
            "id": cid, "url": base, "seguidores": meta.get("channel_follower_count"), "leido": date.today().isoformat(),
            "max": maximo, "fechas_exactas_pedidas": con_exactas, "limites": LIMITES}
    an = {"largo": analizar_formato(largos + cortos, "largo"), "short": analizar_formato(largos + cortos, "short")}
    carpeta = nombre_libre((Path(dest) if dest else ESTUDIO / "referentes") / f"canal_{nombre_seguro(cid, 40)}")
    carpeta.mkdir(parents=True)                   # carpeta nueva: nunca se escribe encima de otro análisis
    (carpeta / "datos.json").write_text(json.dumps({"canal": info, **an}, ensure_ascii=False, indent=1), encoding="utf-8")
    M = informe(info, an, carpeta)                # primero los datos y el informe: un fallo del gráfico no los impide
    try:
        grafico(info["nombre"], an, carpeta / "vistas.png")
    except Exception as e:
        print("aviso gráfico ->", str(e)[-200:], flush=True)
    print("\n".join(M[:12]), flush=True)
    print("guardado en", carpeta, flush=True)
    return info, an, carpeta


def comparar(a, b, carpeta):
    """Dos canales lado a lado (p. ej. el mismo nicho en inglés y en español)."""
    (ia, aa), (ib, ab) = a, b
    filas = [("videos leídos", lambda an, k: an[k].get("videos")), ("mediana de vistas", lambda an, k: an[k].get("mediana_vistas")),
             ("videos cada 30 días", lambda an, k: an[k].get("videos_cada_30_dias")),
             ("duración mediana (s)", lambda an, k: (an[k].get("duraciones") or {}).get("mediana_s")),
             ("título: caracteres", lambda an, k: (an[k].get("titulos") or {}).get("caracteres_mediana")),
             ("título: % con número", lambda an, k: (an[k].get("titulos") or {}).get("con_numero_pct")),
             ("título: % pregunta", lambda an, k: (an[k].get("titulos") or {}).get("pregunta_pct")),
             ("idioma estimado", lambda an, k: (an[k].get("titulos") or {}).get("idioma_estimado")),
             ("despegue x3: video n.º", lambda an, k: ((an[k].get("despegue") or {}).get("x3") or {}).get("n")),
             ("despegue x3: fecha", lambda an, k: ((an[k].get("despegue") or {}).get("x3") or {}).get("fecha")),
             ("despegue x10: video n.º", lambda an, k: ((an[k].get("despegue") or {}).get("x10") or {}).get("n"))]
    M = [f"# Comparación: {ia['nombre']} y {ib['nombre']}", "", f"Leído el {ia['leido']}. Mismos límites que en cada informe_base.md.", ""]
    for k, nombre in (("largo", "Videos largos"), ("short", "Shorts")):
        M += [f"## {nombre}", "", f"| dato | {ia['nombre']} | {ib['nombre']} |", "|---|---|---|"]
        M += [f"| {et} | {_n(f(aa, k))} | {_n(f(ab, k))} |" for et, f in filas]
        M.append("")
    M += ["Para leer: qué hace igual el que despegó antes (frecuencia, duración, títulos), y qué temas de los 10 mejores de uno "
          "no existen en el otro idioma (eso es una brecha que se puede aprovechar con contenido propio, no copiando)."]
    (carpeta / "comparacion.md").write_text("\n".join(M) + "\n", encoding="utf-8")
    print("\n".join(M), flush=True)


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        sys.exit('uso: python canal.py "<url del canal>" [--max 400] [--exactas] [--comparar "<url>"] [--dest carpeta]')
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    try:
        maximo = max(10, min(5000, int(op("--max", 400))))
    except ValueError:
        sys.exit("--max tiene que ser un número")
    ia, aa, carpeta = analizar_canal(a[0], maximo, "--exactas" in a, op("--dest"))
    if op("--comparar"):
        ib, ab, _ = analizar_canal(op("--comparar"), maximo, "--exactas" in a, op("--dest"))
        comparar((ia, aa), (ib, ab), carpeta)
    print("LISTO", carpeta, flush=True)


if __name__ == "__main__":
    main()
