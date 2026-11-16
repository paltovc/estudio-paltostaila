from comun import carpeta_publicar
# Aprobación de Patricio (o su pareja) para publicar piezas de un proyecto.
#   python aprobar.py "<proyecto>" --tabla [--piezas a,b]
#       muestra COMPLETO lo que se aprueba: archivos, títulos, descripción y textos por red sin recortar, etiquetas,
#       miniatura, subtítulos, lista, rutas, horas en Santiago y en los mercados, IA, niños, canal y la huella.
#       No escribe nada.
#   python aprobar.py "<proyecto>" --por "Patricio" --huellas largo:ab12cd34,short1:ef56gh78 [--nota "..."]
#       Claude lo corre SOLO después de un sí explícito, con las huellas (8 caracteres) que mostró la tabla: si algo
#       cambió entre medio (otro render, otra fecha, otro texto, otro canal), no aprueba.
#   python aprobar.py "<proyecto>" --revocar --piezas short1 --por "Patricio"
#       anula la aprobación (aunque falten archivos) y avisa lo que ya quedó programado: eso se cancela aparte, con su sí.
import re, sys
from pathlib import Path
from comun import (APROBACIONES, a_utc, ahora_utc, bloqueo, config, contexto, escribir_estado, escribir_nuevo, huella,
                   huella_pieza, leer_json, opt, p, proyecto_dir, publicacion, registro, ruta_segura)


def bloque(titulo, texto):
    return [f"**{titulo}:**", "", "```", texto or "(vacío)", "```", ""]


def tabla(pdir, pub, claves):
    from zoneinfo import ZoneInfo
    cfg = config()
    ctx = contexto(pub, cfg)
    zs = [cfg["zona"]] + cfg["zonas_publico"]
    L = [f"# Para aprobar: {pub['id']} {pub['version']}", "",
         f"Canal del proyecto: {ctx['canal']} · canal de YouTube conectado: {ctx['youtube_canal_id'] or '(sin confirmar: correr yt_api.py canal)'}"
         f" · idioma {ctx['idioma']} · categoría {ctx['categoria']} · avisar a suscriptores: {'sí' if ctx['notificar'] else 'no'}", ""]
    for x in pub["piezas"]:
        if x["clave"] not in claves:
            continue
        hp = huella_pieza(pdir, x, ctx=ctx)
        L += [f"## {x['clave']} ({x['tipo']}) · huella **{hp[:8]}**", "",
              f"- Archivo: `{x['archivo']}` (sha {huella(ruta_segura(pdir, x['archivo']))[:8]})",
              f"- Miniatura: `{x.get('miniatura', '—')}` · Subtítulos: `{x.get('subtitulos', '—')}` · Lista: {x.get('lista', '—')}",
              f"- IA realista: {'sí (se marca la etiqueta)' if x['ia_realista'] else 'no'} · Para niños: {'sí' if x['para_ninos'] else 'no'}",
              f"- Etiquetas: {', '.join(x.get('etiquetas', [])) or '—'}", ""]
        redes = [d["red"] for d in x["destinos"]]
        if "youtube" in redes:
            L += [f"**Título de YouTube:** {x.get('titulo', '')}", ""] + bloque("Descripción de YouTube", x.get("descripcion", ""))
        for r in ("tiktok", "instagram"):
            if r in redes:
                L += bloque(f"Texto para {r}", x.get(f"texto_{r}", x.get("texto", "")))
        for d in x["destinos"]:
            u = a_utc(d["fecha"], d["zona"])
            horas = " · ".join(f"{z.split('/')[-1]} {u.astimezone(ZoneInfo(z)):%d-%m %H:%M}" for z in zs)
            L.append(f"- {d['red']} ({d['ruta']}): {horas}")
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
lineas = [f"# Aprobación {pub['id']} {pub['version']}", "",
          f"Por: {por} · {ahora_utc():%Y-%m-%d %H:%M} UTC · nivel {cfg['nivel']} · canal {ctx['canal']} / {ctx['youtube_canal_id'] or 'sin confirmar'}", ""]
nuevas = []
for c, h8 in pedidas.items():
    x = next((y for y in pub["piezas"] if y["clave"] == c), None)
    if not x:
        sys.exit(f"No existe la pieza {c}")
    hp = huella_pieza(pdir, x, ctx=ctx)
    if hp[:8] != h8:
        sys.exit(f"La pieza {c} cambió desde que se mostró la tabla (huella ahora {hp[:8]}, aprobada {h8}). "
                 "Mostrar la tabla otra vez y volver a preguntar.")
    nuevas.append({"clave": f"{pub['id']}|{pub['version']}|{c}", "pieza": c, "archivo": x["archivo"],
                   "sha256": huella(ruta_segura(pdir, x["archivo"])), "huella_pieza": hp, "contexto": ctx, "por": por,
                   "fecha": ahora_utc().isoformat(timespec="seconds"), "nota": opt(a, "--nota", ""),
                   "destinos": [f"{d['red']} {d['fecha']} {d['zona']}" for d in x["destinos"]]})
    lineas.append(f"- {c} (huella {hp[:8]}): {x['archivo']} → " + ", ".join(f"{d['red']} {d['fecha']}" for d in x["destinos"]))
with bloqueo("aprobaciones"):
    ap = leer_json(APROBACIONES, {"aprobaciones": []})
    ap["aprobaciones"] += nuevas
    escribir_estado(APROBACIONES, ap)
copia = escribir_nuevo(carpeta_publicar(pdir) / f"aprobacion_{pub['version']}.md", "\n".join(lineas) + "\n")
p("\n".join(lineas))
p("LISTO", copia)
