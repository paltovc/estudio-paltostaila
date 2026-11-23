from comun import carpeta_publicar
# Aprobación de Patricio (o su pareja) para publicar piezas de un proyecto.
#   python aprobar.py "<proyecto>" --tabla [--piezas a,b]
#       muestra COMPLETO lo que se aprueba: archivos, títulos, descripción y textos por red sin recortar, etiquetas,
#       miniatura, subtítulos, lista, rutas, horas en Santiago y en los mercados, IA, niños, canal y la huella.
#       No escribe nada.
#   python aprobar.py "<proyecto>" --por "Patricio" --huellas largo:ab12cd34,short1:ef56gh78 [--nota "..."]
#       Claude lo corre SOLO después de un sí explícito, con las huellas (8 caracteres) que mostró la tabla: si algo
#       cambió entre medio (otro render, otra fecha, otro texto, otro canal), no aprueba.
#       0.2.0 modo lanzamiento del canal: si una pieza tiene la nota bajo el mínimo (8 largo / 7 Short), no se aprueba
#       sin --acepto-nota "<motivo>" (Patricio la acepta; queda en aprobaciones.json con la huella, quién y la nota).
#   python aprobar.py "<proyecto>" --revocar --piezas short1 --por "Patricio"
#       anula la aprobación (aunque falten archivos) y avisa lo que ya quedó programado: eso se cancela aparte, con su sí.
import re, sys
from pathlib import Path
from comun import (APROBACIONES, a_utc, ahora_utc, bloqueo, config, contexto, diario, escribir_estado, escribir_nuevo,
                   huella, huella_pieza, leer_json, modo_lanzamiento, numero_version, opt, p, proyecto_dir, publicacion,
                   registro, ruta_segura, zonas_de)


def bloque(titulo, texto):
    return [f"**{titulo}:**", "", "```", texto or "(vacío)", "```", ""]


def evaluacion(pdir, pub, x, cfg):
    """(fila, ok, detalle, info) de la evaluación de la pieza con la misma regla que las puertas, o None. Si algo no se
    puede leer, devuelve una evaluación «no válida» (las puertas la van a exigir igual)."""
    from puertas import evaluacion_de_pieza
    try:
        return evaluacion_de_pieza(pdir, pub, x, cfg)
    except Exception as e:
        return ("evaluación", False, f"no se pudo revisar la evaluación ({str(e)[:120]})", {"valida": False})


def lineas_evaluacion(pdir, pub, x, cfg, ml):
    ev = evaluacion(pdir, pub, x, cfg)
    if ev is None:
        return ["- Evaluación: no se exige para los Shorts (config.json)"]
    _, ok, det, info = ev
    if ok:
        return [f"- Evaluación: {det}"]
    if ml["activo"] and info.get("valida"):
        return [f"- Evaluación: ⚠ {det}", f"  **Modo lanzamiento:** la nota {info['nota']} está bajo el mínimo {info['minimo']} "
                "(referencia). Se puede aprobar igual solo si Patricio la acepta: --acepto-nota \"<motivo>\"."]
    return [f"- Evaluación: ✗ {det} (las puertas no dejarán publicar así)"]


def tabla(pdir, pub, claves):
    from zoneinfo import ZoneInfo
    cfg = config()
    ctx = contexto(pub, cfg)
    zs = [cfg["zona"]] + zonas_de(cfg, pub.get("canal"))
    ml = modo_lanzamiento(cfg, pub.get("canal"), pub["id"])
    L = [f"# Para aprobar: {pub['id']} {pub['version']}", "",
         f"Canal del proyecto: {ctx['canal']} · canal de YouTube conectado: {ctx['youtube_canal_id'] or '(sin confirmar: correr yt_api.py canal)'}"
         f" · idioma {ctx['idioma']} · categoría {ctx['categoria']} · avisar a suscriptores: {'sí' if ctx['notificar'] else 'no'}", ""]
    if ml["configurado"]:
        L += [f"**{ml['detalle']}.**" + (" El evaluador aconseja y no bloquea; una nota bajo el mínimo se aprueba solo con "
                                         "--acepto-nota \"<motivo>\". El juez revisa cada video." if ml["activo"] else ""), ""]
        nver = numero_version(pub["version"])
        if ml["activo"] and nver is not None and nver > 2:
            L += [f"AVISO: esta es la versión {nver}; en el modo lanzamiento se acordó un máximo de 2 por video.", ""]
    for x in pub["piezas"]:
        if x["clave"] not in claves:
            continue
        hp = huella_pieza(pdir, x, ctx=ctx)
        L += [f"## {x['clave']} ({x['tipo']}) · huella **{hp[:8]}**", "",
              f"- Archivo: `{x['archivo']}` (sha {huella(ruta_segura(pdir, x['archivo']))[:8]})",
              f"- Miniatura: `{x.get('miniatura', '—')}` · Subtítulos: `{x.get('subtitulos', '—')}` · Lista: {x.get('lista', '—')}",
              f"- IA realista: {'sí (se marca la etiqueta)' if x['ia_realista'] else 'no'} · Para niños: {'sí' if x['para_ninos'] else 'no'}",
              f"- Etiquetas: {', '.join(x.get('etiquetas', [])) or '—'}"]
        L += lineas_evaluacion(pdir, pub, x, cfg, ml) + [""]
        redes = [d["red"] for d in x["destinos"]]
        if "youtube" in redes:
            L += [f"**Título de YouTube:** {x.get('titulo', '')}", ""] + bloque("Descripción de YouTube", x.get("descripcion", ""))
        for r in ("tiktok", "instagram"):
            if r in redes:
                L += bloque(f"Texto para {r}", x.get(f"texto_{r}", x.get("texto", "")))
        for d in x["destinos"]:
            u = a_utc(d["fecha"], d["zona"])
            horas = " · ".join(f"{z.split('/')[-1]} {u.astimezone(ZoneInfo(z)):%d-%m %H:%M}" for z in zs)
            L.append(f"- {d['red']} ({d['ruta']}): {horas}" + (" · ✗ modo lanzamiento: subida a mano (hoja de calendario); "
                                                            "cambiar la ruta a «manual» antes de aprobar"
                                                            if ml["activo"] and d["ruta"] != "manual" else ""))
        L.append("")
    return "\n".join(L)


a = sys.argv[1:]
if not a:
    sys.exit("uso: ver el encabezado de aprobar.py")
pdir = proyecto_dir(a[0])
pub = publicacion(pdir)
todas = [x["clave"] for x in pub["piezas"]]

if "--revocar" in a:                          # se puede revocar aunque el proyecto ya no sea válido
    por = opt(a, "--por")
    if not por or "--piezas" not in a:
        sys.exit("Para revocar: --piezas <claves> --por <quién>")
    claves = opt(a, "--piezas").split(",")
    with bloqueo("aprobaciones"):
        ap = leer_json(APROBACIONES, {"aprobaciones": []})
        for c in claves:
            ap["aprobaciones"].append({"clave": f"{pub['id']}|{pub['version']}|{c}", "pieza": c, "por": por,
                                       "fecha": ahora_utc().isoformat(timespec="seconds"),
                                       "revocada": ahora_utc().isoformat(timespec="seconds"), "sha256": "", "huella_pieza": ""})
        escribir_estado(APROBACIONES, ap)
    vivos = [r for r in registro() if r["id"] == pub["id"] and r["pieza"] in claves
             and r["estado"] in ("en_curso", "incierto", "subido_privado", "programado")]
    p(f"REVOCADA la aprobación de {', '.join(claves)}.")
    for r in vivos:
        p(f"AVISO IMPORTANTE: {r['pieza']} sigue {r['estado']} en {r['red']} ({r['enlace'] or 'sin enlace'}). "
          + ("Con el sí de Patricio: python yt_api.py desprogramar \"<P>\" " + r['pieza'] + " --confirmado-por <quién>"
             if r["red"] == "youtube" else "Cancelarlo en Metricool (con el sí de Patricio) y anotar.py --estado cancelado."))
    sys.exit(0)

from validar import validar
err, _ = validar(pdir)
if err:
    sys.exit("publicacion.json no es válido: " + "; ".join(err[:3]))

if "--tabla" in a:
    claves = opt(a, "--piezas").split(",") if "--piezas" in a else todas
    p(tabla(pdir, pub, claves))
    sys.exit(0)

por = opt(a, "--por")
if not por:
    sys.exit("Falta --por <quién aprobó>")
if "--huellas" not in a:
    sys.exit("Falta --huellas pieza:huella8,... (las de la tabla que vio Patricio). Correr antes --tabla.")
pedidas = {}
for par in opt(a, "--huellas").split(","):
    c, _, h8 = par.partition(":")
    h8 = h8.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{8}", h8):
        sys.exit(f"Huella inválida para {c!r}: deben ser exactamente las 8 letras y números de la tabla")
    pedidas[c.strip()] = h8
cfg = config()
ctx = contexto(pub, cfg)
ml = modo_lanzamiento(cfg, pub.get("canal"), pub["id"])
acepto = opt(a, "--acepto-nota") if "--acepto-nota" in a else None
if acepto is not None and len(acepto.strip()) < 8:
    sys.exit("--acepto-nota necesita el motivo con palabras (al menos 8 letras): queda registrado junto a la aprobación")
lineas = [f"# Aprobación {pub['id']} {pub['version']}", "",
          f"Por: {por} · {ahora_utc():%Y-%m-%d %H:%M} UTC · nivel {cfg['nivel']} · canal {ctx['canal']} / {ctx['youtube_canal_id'] or 'sin confirmar'}", ""]
if ml["configurado"]:
    lineas += [ml["detalle"], ""]
nuevas, bajo_minimo, aceptadas = [], [], []
for c, h8 in pedidas.items():
    x = next((y for y in pub["piezas"] if y["clave"] == c), None)
    if not x:
        sys.exit(f"No existe la pieza {c}")
    hp = huella_pieza(pdir, x, ctx=ctx)
    if hp[:8] != h8:
        sys.exit(f"La pieza {c} cambió desde que se mostró la tabla (huella ahora {hp[:8]}, aprobada {h8}). "
                 "Mostrar la tabla otra vez y volver a preguntar.")
    entrada = {"clave": f"{pub['id']}|{pub['version']}|{c}", "pieza": c, "archivo": x["archivo"],
               "sha256": huella(ruta_segura(pdir, x["archivo"])), "huella_pieza": hp, "contexto": ctx, "por": por,
               "fecha": ahora_utc().isoformat(timespec="seconds"), "nota": opt(a, "--nota", ""),
               "destinos": [f"{d['red']} {d['fecha']} {d['zona']}" for d in x["destinos"]]}
    lineas.append(f"- {c} (huella {hp[:8]}): {x['archivo']} → " + ", ".join(f"{d['red']} {d['fecha']}" for d in x["destinos"]))
    ev = evaluacion(pdir, pub, x, cfg)
    if ev is not None and not ev[1]:
        info = ev[3]
        if ml["activo"] and info.get("valida"):           # modo lanzamiento: la nota baja se acepta de forma explícita
            bajo_minimo.append(f"{c} (nota {info['nota']} clase {info['clase']}, mínimo {info['minimo']})")
            if acepto is not None:
                entrada["aceptacion_nota"] = {"motivo": acepto.strip(), "por": por, "fecha": entrada["fecha"],
                                              "nota": info["nota"], "clase": info["clase"], "minimo": info["minimo"],
                                              "evaluacion": info.get("evaluacion"), "sha256_evaluado": info["sha256_evaluado"],
                                              "evaluado": info.get("evaluado"), "huella_pieza": hp,
                                              "tipo_video": info.get("tipo_video"), "pesos": info.get("pesos"),   # M3
                                              "modo": {"video": ml["publicados"] + 1, "hasta": ml["hasta"]}}
                aceptadas.append(entrada)
                lineas.append(f"  - AVISO aceptado: nota {info['nota']} clase {info['clase']} bajo el mínimo {info['minimo']} "
                              f"({ml['detalle']}). Motivo: «{acepto.strip()}»")
        else:
            p(f"AVISO {c}: {ev[2]}. Se aprueba, pero las puertas no dejarán publicar mientras eso no se resuelva.")
    nuevas.append(entrada)
if bajo_minimo and acepto is None:
    sys.exit("NO SE APRUEBA: en modo lanzamiento la nota baja se acepta de forma explícita. Bajo el mínimo: "
             + "; ".join(bajo_minimo) + ". Si Patricio la acepta, repetir con --acepto-nota \"<motivo>\".")
if acepto is not None and not bajo_minimo:
    p("AVISO: --acepto-nota no hacía falta (ninguna pieza está bajo el mínimo en modo lanzamiento); no se registra.")
with bloqueo("aprobaciones"):
    ap = leer_json(APROBACIONES, {"aprobaciones": []})
    ap["aprobaciones"] += nuevas
    escribir_estado(APROBACIONES, ap)
for e in aceptadas:          # queda también en el diario del gerente, un archivo por aceptación
    diario(estado="nota_aceptada", id=pub["id"], version=pub["version"], pieza=e["pieza"], red="", proyecto=str(pdir),
           sha256=e["sha256"], **{"aceptacion_nota": e["aceptacion_nota"]})
copia = escribir_nuevo(carpeta_publicar(pdir) / f"aprobacion_{pub['version']}.md", "\n".join(lineas) + "\n")
p("\n".join(lineas))
p("LISTO", copia)
