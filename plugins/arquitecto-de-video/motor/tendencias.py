# Busca en YouTube los videos de un tema que mas destacan: no solo los de mas vistas, sino los que
# superan por mucho el promedio de su propio canal (eso indica que el tema o el empaque funcionaron).
#   python tendencias.py "invertir para principiantes"
#   python tendencias.py "ahorro" --shorts --n 40 --recientes      (--recientes = ordena la busqueda por fecha)
#   python tendencias.py "ahorro" --top 8                           (cuantos se analizan a fondo; default 10)
# Deja EstudioPaltostaila\tendencias\<tema>_<fecha>.md con la tabla y los enlaces.
import json, sys
from datetime import date
from redes import ESTUDIO, llamar, info, promedio_canal, resumen, nombre_seguro

args = sys.argv[1:]
if not args or args[0].startswith("-"):
    sys.exit('Uso: python tendencias.py "tema" [--shorts] [--n 30] [--top 10] [--recientes]')
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


if __name__ == "__main__":
    main()
