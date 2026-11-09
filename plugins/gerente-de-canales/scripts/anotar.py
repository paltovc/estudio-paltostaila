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
if est in ("programado", "publicado", "subido_privado") and d["ruta"] != "manual" and (not ap or ap["sha256"] != sha):
    nota = ("IRREGULAR: el archivo enviado no tiene una aprobación vigente con esta huella. " + nota).strip()
    p("AVISO: " + nota + " Revisarlo con Patricio.")
diario(estado=est, enlace=enl, nota=nota, **base)
registrar(estado=est, enlace=enl, nota=nota, **base)
try:
    from calendario import estado
    estado(f"{pub['id']}_{pub['version']}_{clave}_{red}", est, enl, nota)
except SystemExit:
    p("AVISO: no estaba en el calendario (correr calendario.py importar)")
p("LISTO anotado", clave, red, est)
