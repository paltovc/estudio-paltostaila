# Envíos hechos fuera de yt_api.py (Metricool o vidIQ por su conector, o a mano por Patricio).
#   python anotar.py "<proyecto>" <pieza> <red> --reservar
#       ANTES de llamar al conector: revisa las puertas bajo candado y, si están abiertas, deja la pieza «en_curso».
#       Mientras esté en_curso nadie más puede enviarla. Si el conector no responde, queda así hasta revisarlo.
#   python anotar.py "<proyecto>" <pieza> <red> --estado programado|publicado|cancelado|error|subido_privado
#                    [--enlace URL] [--nota texto]
#       DESPUÉS del conector (o cuando Patricio avisa que subió algo a mano). Registra la huella del archivo REAL;
#       si no coincide con la aprobación vigente, lo deja escrito como irregular.
import sys
from comun import (ESTADOS, bloqueo, diario, huella, opt, p, pieza, proyecto_dir, publicacion, registrar, registro,
                   ruta_segura, ultimo_estado)

a = sys.argv[1:]
if len(a) < 3 or ("--estado" not in a and "--reservar" not in a):
    sys.exit("uso: python anotar.py <proyecto> <pieza> <red> --reservar | --estado <estado> [--enlace URL] [--nota texto]")
pdir = proyecto_dir(a[0])
clave, red = a[1], a[2]
pub = publicacion(pdir)
x = pieza(pub, clave)
d = next((y for y in x["destinos"] if y["red"] == red), None)
if not d:
    sys.exit(f"La pieza {clave} no tiene destino {red}")
sha = huella(ruta_segura(pdir, x["archivo"]))
base = dict(proyecto=str(pdir), id=pub["id"], version=pub["version"], pieza=clave, red=red, ruta=d["ruta"],
            sha256=sha, fecha_publicacion=d["fecha"], zona=d["zona"])

if "--reservar" in a:
    from puertas import revisar, tabla, todo_ok
    with bloqueo(f"reserva_{pub['id']}_{clave}_{red}"):
        R = revisar(pdir, clave, red)
        p(tabla(R))
        if not todo_ok(R):
            sys.exit("PUERTAS CERRADAS: no se reserva ni se envía")
        diario(estado="en_curso", nota="reservado antes del conector", **base)
        registrar(estado="en_curso", nota=f"reservado para {d['ruta']}", **base)
    p(f"RESERVADO {clave} → {red}. Ahora sí llamar al conector; después: anotar.py ... --estado programado --enlace <url>")
    sys.exit(0)

est = opt(a, "--estado")
if est not in ESTADOS:
    sys.exit(f"Estado no válido: {est}")
nota = opt(a, "--nota", "")
anterior = ultimo_estado(lambda r: (r["id"], r["version"], r["pieza"], r["red"])).get((pub["id"], pub["version"], clave, red))
enl = opt(a, "--enlace", "") or (anterior["enlace"] if anterior else "")
from puertas import aprobacion
ap = aprobacion(pub, clave)
# corrección M1 (juicio 0.15): la ruta manual ya no queda exenta. Lo subido a mano tiene que tener una aprobación vigente
# con la huella del archivo Y la de la pieza (título, textos, fechas, contexto), igual que en las puertas.
if d["ruta"] == "manual":
    from comun import config, contexto, huella_pieza
    sin_aprobar = not ap or ap["sha256"] != sha or ap.get("huella_pieza") != huella_pieza(pdir, x, ctx=contexto(pub, config()))
else:
    sin_aprobar = not ap or ap["sha256"] != sha
enviado = est in ("programado", "publicado", "subido_privado")
# corrección N3 (verificación 0.2.0): en la ruta manual también se miran las puertas del juicio y de la evaluación al
# anotar (p. ej. un RECHAZADO que llegó después de aprobar). Se reusa puertas.revisar; no bloquea, solo deja constancia.
cerradas = []
if enviado and d["ruta"] == "manual":
    from puertas import cerradas_juicio_evaluacion, revisar
    try:
        cerradas = cerradas_juicio_evaluacion(revisar(pdir, clave, red))
    except Exception as e:
        cerradas = [f"no se pudieron revisar las puertas del juicio y de la evaluación ({e})"]
if enviado and (sin_aprobar or cerradas):
    motivos = (["el archivo enviado no tiene una aprobación vigente con esta huella"] if sin_aprobar else []) + \
              [f"puerta cerrada al anotar: {c}" for c in cerradas]
    nota = ("IRREGULAR: " + "; ".join(motivos)
            + (" (ruta manual)" if d["ruta"] == "manual" else "") + ". " + nota).strip()
    p("AVISO: " + nota + " Revisarlo con Patricio.")
diario(estado=est, enlace=enl, nota=nota, **base)
registrar(estado=est, enlace=enl, nota=nota, **base)
try:
    from calendario import estado
    estado(f"{pub['id']}_{pub['version']}_{clave}_{red}", est, enl, nota)
except SystemExit:
    p("AVISO: no estaba en el calendario (correr calendario.py importar)")
p("LISTO anotado", clave, red, est)
