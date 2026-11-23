from comun import carpeta_publicar
# Calendario de publicación de todos los canales (gerente\calendario.json).
#   python calendario.py importar "<proyecto>"         agrega las piezas de publicacion.json (sin duplicar)
#   python calendario.py ver [--mes 2026-11] [--todo]  tabla con la hora local y la de los mercados del público
#   python calendario.py pendientes [--dias 7]         qué hay que subir/programar ahora y qué espera a Patricio
#   python calendario.py estado <id> <estado> [--enlace URL] [--nota texto]
#   python calendario.py cupo [--mes 2026-11]          publicaciones de Metricool usadas en el mes
#   python calendario.py hoja "<proyecto>"             hoja para publicar a mano (ruta manual), archivo nuevo; antes corre
#                                                      las mismas puertas que la ruta api y, si están cerradas, no la
#                                                      escribe y dice qué falta (lleva el sha256 del archivo aprobado)
#   0.2.0 (varios canales en paralelo): ver/pendientes/cupo aceptan --canal <nombre>;
#   python calendario.py canales [--mes 2026-11]       vista conjunta: un resumen por canal (estados, próximos 7 días,
#                                                      modo lanzamiento y cupo de Metricool de cada uno)
import sys
from pathlib import Path
from comun import (CALENDARIO, ESTADOS, a_utc, ahora_utc, bloqueo, canal_cfg, config, escribir_estado, escribir_nuevo,
                   leer_json, modo_lanzamiento, opt as _opt, p, proyecto_dir, publicacion, zonas_de)


def cargar():
    return leer_json(CALENDARIO, {"entradas": []})


def importar(pdir):
    """publicacion.json manda: agrega lo nuevo y actualiza fecha, zona o ruta si cambiaron."""
    pub = publicacion(pdir)
    nuevas = cambios = 0
    with bloqueo("calendario"):
        c = cargar()
        for x in pub["piezas"]:
            for d in x["destinos"]:
                eid = f"{pub['id']}_{pub['version']}_{x['clave']}_{d['red']}"
                e = next((y for y in c["entradas"] if y["id"] == eid), None)
                if e is None:
                    c["entradas"].append({"id": eid, "proyecto": str(pdir), "canal": pub["canal"], "video": pub["id"],
                                          "version": pub["version"], "pieza": x["clave"], "tipo": x["tipo"], "red": d["red"],
                                          "ruta": d["ruta"], "fecha": d["fecha"], "zona": d["zona"], "estado": "por_aprobar",
                                          "enlace": "", "nota": "", "actualizado": ahora_utc().isoformat(timespec="seconds")})
                    nuevas += 1
                    continue
                dif = {k: (e[k], d[k]) for k in ("fecha", "zona", "ruta") if e[k] != d[k]}
                if not dif:
                    continue
                if e["estado"] in ("por_aprobar", "aprobado"):
                    e.update({k: v[1] for k, v in dif.items()})
                    e["estado"] = "por_aprobar"
                    e["actualizado"] = ahora_utc().isoformat(timespec="seconds")
                    cambios += 1
                    p(f"CAMBIO {eid}: " + ", ".join(f"{k} {v[0]} → {v[1]}" for k, v in dif.items()) + " (vuelve a por_aprobar)")
                else:
                    p(f"AVISO {eid} ya está {e['estado']} y publicacion.json cambió " +
                      ", ".join(f"{k} {v[0]} → {v[1]}" for k, v in dif.items()) + ": revisar en la plataforma")
        escribir_estado(CALENDARIO, c)
    p(f"{nuevas} entradas nuevas en el calendario, {cambios} actualizadas")


def _local(e, zona):
    from zoneinfo import ZoneInfo
    return a_utc(e["fecha"], e["zona"]).astimezone(ZoneInfo(zona)).strftime("%d-%m %H:%M")


def ver(mes=None, todo=False, canal=None):
    """Vista conjunta de todos los canales (columna «canal»), o de uno con --canal (con las zonas de su público)."""
    cfg = config()
    zs = zonas_de(cfg, canal) if canal else cfg["zonas_publico"]
    es = sorted(cargar()["entradas"], key=lambda e: a_utc(e["fecha"], e["zona"]))
    if canal:
        es = [e for e in es if e.get("canal") == canal]
    if mes:
        es = [e for e in es if e["fecha"].startswith(mes)]
    if not todo:
        es = [e for e in es if e["estado"] not in ("cancelado",)]
    cab = ["id", "canal", "red", "ruta", "estado", f"{cfg['zona'].split('/')[-1]}"] + [z.split("/")[-1] for z in zs]
    p("| " + " | ".join(cab) + " |")
    p("|" + "---|" * len(cab))
    for e in es:
        p("| " + " | ".join([e["id"], str(e.get("canal") or "?"), e["red"], e["ruta"], e["estado"], _local(e, cfg["zona"])] +
                            [_local(e, z) for z in zs]) + " |")
    p(f"{len(es)} entradas")


def canales(mes=None):
    """Un resumen por canal, todos juntos: entradas por estado, lo que viene, modo lanzamiento y cupo de Metricool."""
    import datetime as dt
    from puertas import cupo_metricool
    cfg = config()
    mes = mes or ahora_utc().strftime("%Y-%m")
    es = cargar()["entradas"]
    nombres = sorted({e.get("canal") or "?" for e in es} | set((cfg.get("canales") or {}).keys()))
    ahora = ahora_utc()
    p(f"| canal | por aprobar | aprobadas | programadas/publicadas ({mes}) | próximos 7 días | modo lanzamiento | Metricool {mes} |")
    p("|---|---|---|---|---|---|---|")
    avisos = []
    for c in nombres:
        xs = [e for e in es if (e.get("canal") or "?") == c]
        prox = [e for e in xs if e["estado"] not in ("cancelado", "error")
                and ahora <= a_utc(e["fecha"], e["zona"]) <= ahora + dt.timedelta(days=7)]
        sal = [e for e in xs if e["estado"] in ("programado", "publicado", "medido_48h", "medido_7d") and e["fecha"].startswith(mes)]
        ml = modo_lanzamiento(cfg, c)
        usados, lim = cupo_metricool(mes, cfg, None, c)
        propio = isinstance(canal_cfg(cfg, c).get("metricool"), dict)
        # corrección B2 (juicio 0.15): en modo lanzamiento el contador sale de lo anotado; lo subido a mano y sin anotar
        # no cuenta, y el modo (más permisivo) duraría más de lo acordado
        atrasadas = [e for e in xs if ml["activo"] and e["estado"] in ("por_aprobar", "aprobado", "en_curso", "incierto",
                                                                       "subido_privado")
                     and a_utc(e["fecha"], e["zona"]) < ahora]
        if atrasadas:
            avisos.append(f"AVISO canal «{c}» ({ml['detalle']}): {len(atrasadas)} piezas con la fecha pasada y sin anotar "
                          f"como publicadas ({', '.join(e['id'] for e in atrasadas[:8])}{' …' if len(atrasadas) > 8 else ''}). "
                          "Si se subieron a mano: anotar.py \"<P>\" <pieza> <red> --estado publicado --enlace <url>; si no, "
                          "cancelarlas o cambiarles la fecha. Mientras tanto el contador del modo lanzamiento se queda corto.")
        p(f"| {c} | {sum(e['estado'] == 'por_aprobar' for e in xs)} | {sum(e['estado'] == 'aprobado' for e in xs)} | "
          f"{len(sal)} | {len(prox)} | {ml['detalle'] if ml['configurado'] else '—'}"
          f"{f' (⚠ {len(atrasadas)} sin anotar)' if atrasadas else ''} | "
          f"{usados}/{lim}{'' if propio else ' (cuenta compartida)'} |")
    p(f"{len(nombres)} canales")
    for t in avisos:
        p(t)


def pendientes(dias=7, canal=None):
    import datetime as dt
    ahora = ahora_utc()
    lim = ahora + dt.timedelta(days=dias)
    es = [e for e in cargar()["entradas"] if not canal or e.get("canal") == canal]
    grupos = {
        "Esperan aprobación de Patricio": [e for e in es if e["estado"] == "por_aprobar"],
        f"Aprobadas para subir o programar (fecha en los próximos {dias} días)":
            [e for e in es if e["estado"] == "aprobado" and a_utc(e["fecha"], e["zona"]) <= lim],
        "Subidas en privado: falta programarlas o publicarlas": [e for e in es if e["estado"] == "subido_privado"],
        "REVISAR EN LA PLATAFORMA (envío cortado o reservado sin respuesta)": [e for e in es if e["estado"] in ("incierto", "en_curso")],
        "Fecha pasada sin publicar (revisar)": [e for e in es if e["estado"] in ("por_aprobar", "aprobado")
                                                and a_utc(e["fecha"], e["zona"]) < ahora],
        "Publicadas: toca medir a las 48 h": [e for e in es if e["estado"] in ("programado", "publicado")
                                              and a_utc(e["fecha"], e["zona"]) <= ahora - dt.timedelta(hours=48)],
        "Medidas a 48 h: toca medir a los 7 días": [e for e in es if e["estado"] == "medido_48h"
                                                    and a_utc(e["fecha"], e["zona"]) <= ahora - dt.timedelta(days=7)],
    }
    for t, xs in grupos.items():
        p(f"## {t}: {len(xs)}")
        for e in xs:
            p(f"- {e['id']} · {e['fecha']} {e['zona']} · {e['ruta']} · canal {e.get('canal') or '?'}")


def estado(eid, nuevo, enlace="", nota=""):
    if nuevo not in ESTADOS:
        sys.exit(f"Estado no válido. Usar: {', '.join(ESTADOS)}")
    with bloqueo("calendario"):
        c = cargar()
        e = next((x for x in c["entradas"] if x["id"] == eid), None)
        if not e:
            sys.exit(f"No existe {eid}")
        e["estado"] = nuevo
        if enlace:
            e["enlace"] = enlace
        if nota:
            e["nota"] = nota
        e["actualizado"] = ahora_utc().isoformat(timespec="seconds")
        escribir_estado(CALENDARIO, c)
    p(f"{eid} -> {nuevo}")


def cupo(mes=None, canal=None):
    """Cupo de Metricool del mes. Con --canal: si ese canal tiene su propia cuenta de Metricool (config.json), solo lo
    suyo; si comparte la cuenta general, el cupo es de todos los canales juntos (se avisa)."""
    from puertas import cupo_metricool
    cfg = config()
    mes = mes or ahora_utc().strftime("%Y-%m")
    propio = bool(canal) and isinstance(canal_cfg(cfg, canal).get("metricool"), dict)
    usados, lim = cupo_metricool(mes, cfg, None, canal)
    agendadas = [e for e in cargar()["entradas"] if e["ruta"] == "metricool" and e["fecha"].startswith(mes)
                 and e["estado"] not in ("cancelado", "error", "medido_48h", "medido_7d", "publicado", "programado")
                 and (not propio or e.get("canal") == canal)]
    if canal and not propio:
        p(f"(el canal {canal} comparte la cuenta general de Metricool: el cupo es de todos los canales juntos)")
    p(f"Metricool {mes}{' · ' + canal if propio else ''}: {usados} publicadas o programadas de {lim}; "
      f"{len(agendadas)} más por enviar ese mes")
    if usados + len(agendadas) > lim:
        p(f"AVISO: el calendario pide {usados + len(agendadas)} y el plan gratis publica {lim}. Mover piezas, pasar algunas a "
          "manual o decidir un plan de pago (solo con el sí de Patricio).")


def hoja(pdir):
    """Hoja para subir a mano. Corrección M1 (juicio 0.15): antes de escribirla corre las MISMAS puertas que la ruta api
    (puertas.revisar: terminado con huella, monetización, evaluación o nota aceptada en modo lanzamiento, juicio del juez,
    aprobación vigente con huella…) por cada destino manual. Si alguna está cerrada no escribe nada y dice qué falta.
    La hoja lleva el sha256 del archivo aprobado, para comprobar que se sube ese y no otro."""
    from comun import huella, ruta_segura
    from puertas import aprobacion, revisar, tabla, todo_ok
    pub = publicacion(pdir)
    manuales = [(x, d) for x in pub["piezas"] for d in x["destinos"] if d["ruta"] == "manual"]
    if not manuales:
        p("No hay destinos con ruta manual en publicacion.json: no hay hoja que hacer.")
        return
    cerradas, avisos, shas = [], {}, {}
    for x, d in manuales:
        R = revisar(pdir, x["clave"], d["red"])
        if not todo_ok(R):
            p(f"## {x['clave']} → {d['red']}: PUERTAS CERRADAS")
            p(tabla(R))
            cerradas += [f"{x['clave']}/{d['red']}: {n} ({det})" for n, ok, det in R if not ok]
            continue
        avisos[(x["clave"], d["red"])] = [f"{n}: {det}" for n, ok, det in R if str(det).startswith("AVISO")]
        a = aprobacion(pub, x["clave"])
        sha = huella(ruta_segura(pdir, x["archivo"]))
        if not a or a["sha256"] != sha:          # el archivo cambió mientras se revisaba
            cerradas.append(f"{x['clave']}/{d['red']}: el archivo cambió mientras se revisaban las puertas")
        shas[x["clave"]] = (sha, a)
    if cerradas:
        p("NO SE ESCRIBE LA HOJA: las puertas están cerradas. Falta:")
        for c in cerradas:
            p(f"- {c}")
        sys.exit(1)
    L = [f"# Hoja de publicación manual · {pub['id']} {pub['version']}", "",
         f"Puertas revisadas el {ahora_utc():%Y-%m-%d %H:%M} UTC (las mismas de la ruta api): abiertas para cada destino de abajo.",
         "Si el video se rehízo después de esta hoja, la hoja no vale: hacerla de nuevo.", ""]
    for x, d in manuales:
        sha, a = shas[x["clave"]]
        txt = x.get(f"texto_{d['red']}", x.get("texto", ""))
        L += [f"## {x['clave']} → {d['red']} · {d['fecha']} ({d['zona']})", "",
              f"- Archivo: `{x['archivo']}`",
              f"- sha256 del archivo aprobado: `{sha}` (empieza con **{sha[:8]}**). Antes de subir, comprobarlo en "
              f"PowerShell, desde la carpeta del proyecto: `Get-FileHash -Algorithm SHA256 \"{x['archivo']}\"`; si no es igual, NO subir.",
              f"- Aprobado por {a['por']} el {a['fecha'][:10]} (huella de la pieza {a.get('huella_pieza', '')[:8]})"]
        L += [f"- ⚠ {t}" for t in avisos.get((x["clave"], d["red"]), [])]
        L += [f"- Contenido hecho con IA realista: {'Sí, marcar la etiqueta' if x['ia_realista'] else 'No'}", ""]
        if d["red"] == "youtube":
            L += [f"**Título:** {x.get('titulo', '')}", "", "**Descripción:**", "", "```", x.get("descripcion", ""), "```",
                  f"- Para niños: {'Sí' if x.get('para_ninos') else 'No'}", ""]
        else:
            L += ["**Texto:**", "", "```", txt, "```", ""]
        L += ["- [ ] Subido", "- [ ] Avisar a Claude para marcarlo en el calendario", ""]
    destino = escribir_nuevo(carpeta_publicar(pdir) / f"hoja_de_publicacion_{pub['version']}.md", "\n".join(L))
    p("LISTO", destino)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit("uso: python calendario.py importar|ver|pendientes|estado|cupo|canales|hoja ...")
    op = a[0]
    opt = lambda k, d=None: _opt(a, k, d)
    if op == "importar":
        importar(proyecto_dir(a[1]))
    elif op == "ver":
        ver(opt("--mes"), "--todo" in a, opt("--canal"))
    elif op == "pendientes":
        pendientes(int(opt("--dias", 7)), opt("--canal"))
    elif op == "estado":
        estado(a[1], a[2], opt("--enlace", ""), opt("--nota", ""))
    elif op == "cupo":
        cupo(opt("--mes"), opt("--canal"))
    elif op == "canales":
        canales(opt("--mes"))
    elif op == "hoja":
        hoja(proyecto_dir(a[1]))
    else:
        sys.exit(f"Operación desconocida: {op}")
