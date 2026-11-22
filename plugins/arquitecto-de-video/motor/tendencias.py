# Busca en YouTube los videos de un tema que mas destacan: no solo los de mas vistas, sino los que
# superan por mucho el promedio de su propio canal (eso indica que el tema o el empaque funcionaron).
#   python tendencias.py "invertir para principiantes"
#   python tendencias.py "ahorro" --shorts --n 40 --recientes      (--recientes = ordena la busqueda por fecha)
#   python tendencias.py "ahorro" --top 8                           (cuantos se analizan a fondo; default 10)
# Deja EstudioPaltostaila\tendencias\<tema>_<fecha>.md con la tabla y los enlaces.
#
# 0.15 Brecha de idioma: la misma búsqueda en dos o tres idiomas, para ver temas que funcionan en uno y casi no existen
# en otro. Claude entrega la consulta traducida (no se traduce sola), en el mismo orden que --idiomas:
#   python tendencias.py "finanzas para principiantes" --idiomas en,es,pt
#          --consultas "personal finance for beginners|finanzas para principiantes|finanças para iniciantes"
#          [--shorts] [--n 40] [--dias 30] [--top 5]
#   Por idioma: OFERTA = cuántos videos de los recientes (búsqueda por fecha) salieron en los últimos --dias días;
#   DEMANDA = vistas de los más relevantes (mediana y percentil 90) y OUTLIERS = de los --top con más vistas, cuántos
#   hacen 3 veces o más la mediana de su propio canal. Deja tendencias\brecha_<tema>_<fecha>.md y .json (nombre nuevo).
#   Límites: YouTube ordena según la región de la conexión (Chile) aunque se pida el idioma; las fechas de la búsqueda
#   son aproximadas («hace 2 semanas»); es una señal para investigar, no una medida del mercado.
import json, re, statistics, sys
from datetime import date, datetime, timedelta, timezone
from redes import ESTUDIO, llamar, info, promedio_canal, resumen, nombre_seguro

args = sys.argv[1:]
if not args or args[0].startswith("-"):
    sys.exit('Uso: python tendencias.py "tema" [--shorts] [--n 30] [--top 10] [--recientes]\n'
             '     python tendencias.py "tema" --idiomas en,es,pt --consultas "q en|q es|q pt" [--dias 30] [--top 5]')
TEMA = args[0]
opt = lambda k, d: int(args[args.index(k) + 1]) if k in args else d
N, TOP = opt("--n", 30), opt("--top", 10)
SHORTS = "--shorts" in args
consulta = TEMA + (" #shorts" if SHORTS else "")
prefijo = "ytsearchdate" if "--recientes" in args else "ytsearch"


def main():
    print(f"buscando '{consulta}' ({N} resultados)...", flush=True)
    d = json.loads(llamar(["-J", "--flat-playlist", "--no-warnings", f"{prefijo}{N}:{consulta}"], timeout=300))
    entradas = [e for e in d.get("entries", []) if e and e.get("view_count")]
    if SHORTS:
        entradas = [e for e in entradas if (e.get("duration") or 999) <= 180]
    else:
        entradas = [e for e in entradas if (e.get("duration") or 0) > 180]
    entradas.sort(key=lambda e: -e["view_count"])
    filas = []
    for e in entradas[:TOP * 2]:
        if len(filas) >= TOP:
            break
        url = e.get("url") or f"https://www.youtube.com/watch?v={e['id']}"
        try:
            i = info(url, comentarios=0)
        except Exception as ex:
            print("  salto", url, str(ex)[-120:])
            continue
        r = resumen(i)
        med, n = promedio_canal(i, 20)
        r["mediana_canal"] = int(med) if med else None
        r["veces_sobre_su_canal"] = round(r["vistas"] / med, 1) if med and r["vistas"] else None
        filas.append(r)
        print(f"  {r['vistas']:>10,} vistas  x{r['veces_sobre_su_canal'] or '?':<5} {r['titulo'][:70]}", flush=True)
    filas.sort(key=lambda r: -((r["veces_sobre_su_canal"] or 0) * 1000 + (r["vistas_por_dia"] or 0) / 1000))
    hoy = date.today().isoformat()
    out = ESTUDIO / "tendencias"
    out.mkdir(parents=True, exist_ok=True)
    ruta = out / f"{nombre_seguro(TEMA, 40)}{'_shorts' if SHORTS else ''}_{hoy}.md"
    m = [f"# Tendencias: {TEMA}{' (Shorts)' if SHORTS else ''} — {hoy}", "",
         "Orden: primero los que mas superan a su propio canal (x = vistas / mediana de los ultimos videos del canal).", "",
         "| # | x canal | vistas | vistas/dia | likes/1000 | dur | canal (seguidores) | titulo |", "|---|---|---|---|---|---|---|---|"]
    for k, r in enumerate(filas, 1):
        seg = f"{r['seguidores']:,}" if r.get("seguidores") else "?"
        m.append(f"| {k} | {r['veces_sobre_su_canal'] or '?'} | {r['vistas']:,} | {r['vistas_por_dia'] or '?'} | "
                 f"{r['likes_por_1000_vistas'] or '?'} | {r['duracion_s']}s | {r['canal']} ({seg}) | [{r['titulo']}]({r['url']}) |")
    m += ["", "Siguiente: elegir 2-3 y analizarlos a fondo con referente.py (o pedir 'analiza estos referentes')."]
    ruta.write_text("\n".join(m), encoding="utf-8")
    (ruta.with_suffix(".json")).write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(m))
    print("\nguardado en", ruta)


def _texto(k, d=None):
    return args[args.index(k) + 1] if k in args and args.index(k) + 1 < len(args) else d


def _buscar(q, n, idioma, por_fecha):
    pref = "ytsearchdate" if por_fecha else "ytsearch"
    d = json.loads(llamar(["-J", "--flat-playlist", "--no-warnings", "--extractor-args", f"youtube:lang={idioma}",
                           "--extractor-args", "youtubetab:approximate_date",
                           f"{pref}{n}:{q}{' #shorts' if SHORTS else ''}"], timeout=300))
    es = [e for e in d.get("entries", []) if e]
    if SHORTS:
        return [e for e in es if (e.get("duration") or 999) <= 180]
    return [e for e in es if (e.get("duration") or 0) > 180]


def _fecha(e):
    if e.get("upload_date") and re.fullmatch(r"\d{8}", str(e["upload_date"])):
        u = str(e["upload_date"])
        return date(int(u[:4]), int(u[4:6]), int(u[6:]))
    if isinstance(e.get("timestamp"), (int, float)):
        return datetime.fromtimestamp(e["timestamp"], timezone.utc).date()
    return None


def brecha():
    idiomas = [x.strip().lower() for x in _texto("--idiomas", "").split(",") if x.strip()]
    if len(idiomas) < 2 or any(i not in ("es", "en", "pt") for i in idiomas):
        sys.exit("--idiomas necesita dos o tres de: es, en, pt (p. ej. --idiomas en,es)")
    consultas = [x.strip() for x in (_texto("--consultas") or "").split("|")]
    if len(consultas) != len(idiomas) or not all(consultas):
        sys.exit("--consultas necesita una consulta por idioma, en el mismo orden, separadas por | "
                 "(Claude las traduce: el script no traduce)")
    dias, top = opt("--dias", 30), opt("--top", 5)
    limite = date.today() - timedelta(days=dias)
    res = []
    for idi, q in zip(idiomas, consultas):
        print(f"[{idi}] '{q}': recientes y más relevantes...", flush=True)
        try:
            recientes = _buscar(q, N, idi, True)
            relevantes = _buscar(q, N, idi, False)
        except Exception as ex:
            print(f"  no se pudo buscar en {idi}: {str(ex)[-160:]}", flush=True)
            res.append({"idioma": idi, "consulta": q, "error": str(ex)[-300:]})
            continue
        fechas = [_fecha(e) for e in recientes]
        con_fecha = [f for f in fechas if f]
        oferta = sum(1 for f in con_fecha if f >= limite) if con_fecha else None
        vistas = sorted(e["view_count"] for e in relevantes if e.get("view_count"))
        p90 = vistas[int(0.9 * (len(vistas) - 1))] if vistas else None
        outliers = []
        for e in sorted((e for e in relevantes if e.get("view_count")), key=lambda e: -e["view_count"])[:top]:
            url = e.get("url") or f"https://www.youtube.com/watch?v={e['id']}"
            try:
                i = info(url, comentarios=0)
                med, _n = promedio_canal(i, 20)
            except Exception as ex:
                print("  salto", url, str(ex)[-100:], flush=True)
                continue
            r = resumen(i)
            r["mediana_canal"] = int(med) if med else None
            r["veces_sobre_su_canal"] = round(r["vistas"] / med, 1) if med and r["vistas"] else None
            outliers.append(r)
        fuertes = [o for o in outliers if (o["veces_sobre_su_canal"] or 0) >= 3]
        res.append({"idioma": idi, "consulta": q, "recientes_leidos": len(recientes), "recientes_con_fecha": len(con_fecha),
                    f"oferta_ultimos_{dias}_dias": oferta, "demanda_mediana_vistas": statistics.median(vistas) if vistas else None,
                    "demanda_p90_vistas": p90, "outliers_3x": len(fuertes), "analizados": len(outliers), "top": outliers})
        print(f"  oferta {oferta if oferta is not None else '?'} en {dias} días · mediana {res[-1]['demanda_mediana_vistas']} · "
              f"{len(fuertes)} de {len(outliers)} sobre 3x su canal", flush=True)
    clave = f"oferta_ultimos_{dias}_dias"
    senales = []
    ok = [r for r in res if "error" not in r]
    for a in ok:
        for b in ok:
            if a is b:
                continue
            oa, ob = a[clave], b[clave]
            if a["outliers_3x"] >= 2 and oa is not None and ob is not None and ob <= max(1, oa / 3):
                senales.append(f"POSIBLE BRECHA {a['idioma']} → {b['idioma']}: en {a['idioma']} hay {a['outliers_3x']} videos que "
                               f"superan 3x a su canal y {oa} recientes; en {b['idioma']} solo {ob} recientes en {dias} días.")
            da, db = a["demanda_mediana_vistas"], b["demanda_mediana_vistas"]
            if db and da and db >= da and ob is not None and oa is not None and ob < oa / 2:
                senales.append(f"DEMANDA SIN OFERTA en {b['idioma']}: los más vistos tienen mediana {int(db):,} (≥ {a['idioma']}) "
                               f"con la mitad o menos de videos recientes ({ob} frente a {oa}).")
    hoy = date.today().isoformat()
    out = ESTUDIO / "tendencias"
    out.mkdir(parents=True, exist_ok=True)
    ruta = out / f"brecha_{nombre_seguro(TEMA, 40)}{'_shorts' if SHORTS else ''}_{hoy}.md"
    k = 2
    while ruta.exists() or ruta.with_suffix(".json").exists():          # nunca encima de otra corrida del mismo día
        ruta = out / f"brecha_{nombre_seguro(TEMA, 40)}{'_shorts' if SHORTS else ''}_{hoy}_{k}.md"
        k += 1
    m = [f"# Brecha de idioma: {TEMA}{' (Shorts)' if SHORTS else ''} — {hoy}", "",
         f"Misma búsqueda en {', '.join(idiomas)} ({N} resultados por búsqueda). Oferta = videos recientes en {dias} días; "
         f"demanda = vistas de los más relevantes; outliers = de los {top} más vistos, los que hacen 3x o más su canal.", "",
         "| idioma | consulta | oferta reciente | mediana vistas | p90 vistas | outliers ≥3x |", "|---|---|---|---|---|---|"]
    for r in res:
        if "error" in r:
            m.append(f"| {r['idioma']} | {r['consulta']} | error | | | |")
            continue
        m.append(f"| {r['idioma']} | {r['consulta']} | {r[clave] if r[clave] is not None else '? (sin fechas)'} | "
                 f"{int(r['demanda_mediana_vistas']):,} | {int(r['demanda_p90_vistas']):,} | {r['outliers_3x']} de {r['analizados']} |"
                 if r["demanda_mediana_vistas"] else f"| {r['idioma']} | {r['consulta']} | {r[clave]} | — | — | {r['outliers_3x']} |")
    m += ["", "## Señales"] + ([f"- {s}" for s in senales] or ["- ninguna clara con estos números"])
    for r in ok:
        m += ["", f"## Los más vistos en {r['idioma']}", "", "| x canal | vistas | canal | título |", "|---|---|---|---|"]
        m += [f"| {o['veces_sobre_su_canal'] or '?'} | {o['vistas']:,} | {o['canal']} | [{o['titulo']}]({o['url']}) |"
              for o in r["top"] if o.get("vistas")]
    m += ["", "Límites: YouTube ordena según la región de la conexión aunque se pida el idioma; las fechas de la búsqueda son "
          "aproximadas; es una señal para investigar (con canal.py y referente.py), no una medida del mercado."]
    ruta.write_text("\n".join(m) + "\n", encoding="utf-8")
    ruta.with_suffix(".json").write_text(json.dumps({"tema": TEMA, "dias": dias, "idiomas": res, "senales": senales},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(m), flush=True)
    print("\nguardado en", ruta)


if __name__ == "__main__":
    if "--idiomas" in args:
        brecha()
    else:
        main()
