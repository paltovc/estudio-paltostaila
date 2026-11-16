from comun import carpeta_publicar
# Calendario de publicación de todos los canales (gerente\calendario.json).
#   python calendario.py importar "<proyecto>"         agrega las piezas de publicacion.json (sin duplicar)
#   python calendario.py ver [--mes 2026-11] [--todo]  tabla con la hora local y la de los mercados del público
#   python calendario.py pendientes [--dias 7]         qué hay que subir/programar ahora y qué espera a Patricio
#   python calendario.py estado <id> <estado> [--enlace URL] [--nota texto]
#   python calendario.py cupo [--mes 2026-11]          publicaciones de Metricool usadas en el mes
#   python calendario.py hoja "<proyecto>"             hoja para publicar a mano (ruta manual), archivo nuevo
import sys
from pathlib import Path
from comun import (CALENDARIO, ESTADOS, a_utc, ahora_utc, bloqueo, config, escribir_estado, escribir_nuevo, leer_json,
                   opt as _opt, p, proyecto_dir, publicacion)


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


def ver(mes=None, todo=False):
    cfg = config()
    zs = cfg["zonas_publico"]
    es = sorted(cargar()["entradas"], key=lambda e: a_utc(e["fecha"], e["zona"]))
    if mes:
        es = [e for e in es if e["fecha"].startswith(mes)]
    if not todo:
        es = [e for e in es if e["estado"] not in ("cancelado",)]
    cab = ["id", "red", "ruta", "estado", f"{cfg['zona'].split('/')[-1]}"] + [z.split("/")[-1] for z in zs]
    p("| " + " | ".join(cab) + " |")
    p("|" + "---|" * len(cab))
    for e in es:
        p("| " + " | ".join([e["id"], e["red"], e["ruta"], e["estado"], _local(e, cfg["zona"])] +
                            [_local(e, z) for z in zs]) + " |")
    p(f"{len(es)} entradas")


def pendientes(dias=7):
    import datetime as dt
    ahora = ahora_utc()
    lim = ahora + dt.timedelta(days=dias)
    es = cargar()["entradas"]
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
            p(f"- {e['id']} · {e['fecha']} {e['zona']} · {e['ruta']}")


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


def cupo(mes=None):
    from puertas import cupo_metricool
    mes = mes or ahora_utc().strftime("%Y-%m")
    usados, lim = cupo_metricool(mes, config())
    agendadas = [e for e in cargar()["entradas"] if e["ruta"] == "metricool" and e["fecha"].startswith(mes)
                 and e["estado"] not in ("cancelado", "error", "medido_48h", "medido_7d", "publicado", "programado")]
    p(f"Metricool {mes}: {usados} publicadas o programadas de {lim}; {len(agendadas)} más por enviar ese mes")
    if usados + len(agendadas) > lim:
        p(f"AVISO: el calendario pide {usados + len(agendadas)} y el plan gratis publica {lim}. Mover piezas, pasar algunas a "
          "manual o decidir un plan de pago (solo con el sí de Patricio).")


def hoja(pdir):
    pub = publicacion(pdir)
    L = [f"# Hoja de publicación manual · {pub['id']} {pub['version']}", ""]
    for x in pub["piezas"]:
        for d in x["destinos"]:
            if d["ruta"] != "manual":
                continue
            txt = x.get(f"texto_{d['red']}", x.get("texto", ""))
            L += [f"## {x['clave']} → {d['red']} · {d['fecha']} ({d['zona']})", "",
                  f"- Archivo: `{x['archivo']}`",
                  f"- Contenido hecho con IA realista: {'Sí, marcar la etiqueta' if x['ia_realista'] else 'No'}", ""]
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
        sys.exit("uso: python calendario.py importar|ver|pendientes|estado|cupo|hoja ...")
    op = a[0]
    opt = lambda k, d=None: _opt(a, k, d)
    if op == "importar":
        importar(proyecto_dir(a[1]))
    elif op == "ver":
        ver(opt("--mes"), "--todo" in a)
    elif op == "pendientes":
        pendientes(int(opt("--dias", 7)))
    elif op == "estado":
        estado(a[1], a[2], opt("--enlace", ""), opt("--nota", ""))
    elif op == "cupo":
        cupo(opt("--mes"))
    elif op == "hoja":
        hoja(proyecto_dir(a[1]))
    else:
        sys.exit(f"Operación desconocida: {op}")
