# Definición de "terminado" del estudio: una lista que se revisa con sí o no, sin opiniones.
#   python terminado.py "<proyecto>" [--version v8]
# Deja 07_RENDER\terminado_<ID>_<version>.md con cada punto (✓ / ✗ / –) y termina con código 0 solo si todo lo
# obligatorio pasa. Claude la corre antes de decir "listo" y entrega el resultado tal cual.
# Obligatorio: 1-6 y 11. Recomendado: 7-10, 12 y 13 (si falla, se avisa pero no bloquea).
import json, re, subprocess, sys
from pathlib import Path
from estudio import Proyecto, FFMPEG, duracion_medio, metadatos_personales, formato_plataformas, huella

pr = Proyecto()
args = sys.argv[1:]
ver = args[args.index("--version") + 1] if "--version" in args else pr.version
base = f"{pr.id}_{ver}"
R = []
try:      # un log de Windows en cp1252 no puede botar la tabla por un ✓ (falla cerrado, pero deja traza)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")     # ✓ y ✗ se distinguen también en un log de Windows
except Exception:
    pass


def videos_de_la_version():
    return sorted({p for p in (*pr.salida.glob(f"{base}_*.mp4"), *(pr.salida / "celu").glob(f"{base}_*.mp4"))
                   if ".parcial" not in p.name and "_anterior-" not in p.name})


def sellos():
    """Huella de cada video de la versión, con su ruta relativa a la carpeta de salida (celu/<nombre> para la copia
    del celular: así ficha.py y el gerente encuentran el mismo archivo)."""
    return {q.relative_to(pr.salida).as_posix(): huella(q) for q in videos_de_la_version()}


ANTES = sellos()      # se sella ANTES de medir: si un render cambia un video durante la revisión, no se firma nada


def punto(n, obligatorio, texto, ok, detalle=""):
    R.append((n, obligatorio, texto, ok, detalle))


def ff(*a):
    """stderr de un análisis de ffmpeg; None si ffmpeg falló (entonces el punto queda «no comprobado», nunca aprobado)."""
    r = subprocess.run([str(FFMPEG), "-hide_banner", *map(str, a), "-f", "null", "-"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return None if r.returncode else r.stderr


yt = pr.salida / f"{base}_youtube.mp4"
cs = pr.salida / f"{base}_con-subtitulos.mp4"
srt = pr.salida / f"{base}_subtitulos.srt"
# 1. archivos
faltan = [p.name for p in (yt, cs, srt) if not p.exists()]
punto(1, True, "Están el video YouTube, el con subtítulos y el .srt", not faltan, "faltan: " + ", ".join(faltan) if faltan else "")
# 2. duración igual a la voz
if yt.exists():
    dv, dz = duracion_medio(yt), pr.duracion()
    # el con subtítulos tiene que ser el MISMO corte que el de YouTube (el gerente sube uno con la nota del otro)
    dcs = duracion_medio(cs) if cs.exists() else None
    mismo = dcs is None or abs(dcs - dv) <= 0.2
    punto(2, True, "La duración calza con la voz (±1,5 s) y los dos videos duran lo mismo", abs(dv - dz) <= 1.5 and mismo,
          f"video {dv:.1f} s · voz {dz:.1f} s" + ("" if dcs is None else f" · con subtítulos {dcs:.1f} s")
          + ("" if mismo else " · el con subtítulos es de otro corte: volver a armar los dos"))
    # 3. volumen
    e = ff("-i", yt, "-af", "ebur128=peak=true", "-vn")
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", e or "")
    lufs = float(m[-1]) if m else None
    m = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e or "")
    pico_real = float(m[-1]) if m else None
    punto(3, True, "Volumen -14 LUFS (±1)", None if lufs is None else abs(lufs + 14) <= 1,
          f"{lufs} LUFS" if lufs is not None else "no se pudo medir")
    # 4. negros
    e = ff("-i", yt, "-vf", "blackdetect=d=0.4:pix_th=0.08", "-an")
    if e is None:
        punto(4, True, "Sin pantallas negras en medio del video", None, "ffmpeg no pudo analizar el video")
    else:
        negros = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", e)]
        medio = [(a, b) for a, b in negros if a > 1.0 and b < dv - 1.5]
        punto(4, True, "Sin pantallas negras en medio del video", not medio, ", ".join(f"{a:.1f}-{b:.1f} s" for a, b in medio))
else:
    for n, t in ((2, "La duración calza con la voz"), (3, "Volumen -14 LUFS"), (4, "Sin pantallas negras")):
        punto(n, True, t, False, "no hay video")
# 5. capa viva sin tapar caras
lug = pr.tmp / "capa_viva_lugares.txt"
if pr.cfg.get("elementos"):
    txt = lug.read_text(encoding="utf-8") if lug.exists() else ""
    if not lug.exists():
        punto(5, True, "La capa viva no tapa caras ni texto de la imagen", None, "sin registro: no se comprobó (render sin evitar_caras)")
    elif not (txt.splitlines() or [""])[0].startswith(f"# version: {base} ·"):
        punto(5, True, "La capa viva no tapa caras ni texto de la imagen", None, "el registro es de otra versión: volver a correr terminar.py")
    else:
        malos = []
        for l in txt.splitlines():
            m = re.search(r"^\s*([\d.]+) s\s+(\w+).*ahora ([\d.]+)\)", l)
            if m and float(m.group(3)) >= 1:
                malos.append(f"{m.group(2)} en {m.group(1)} s")
        punto(5, True, "La capa viva no tapa caras ni texto de la imagen", not malos,
              ("revisar a mano: " + ", ".join(malos)) if malos else "sin conflictos")
else:
    punto(5, True, "La capa viva no tapa caras ni texto de la imagen", True, "sin elementos")
# 6. versión anterior conservada
n = int(re.sub(r"\D", "", ver) or 1)
if n > 1:
    previa = f"v{n - 1}"
    hay = any(pr.salida.glob(f"{pr.id}_{previa}_*")) or (pr.dir / f"proyecto_{previa}.json").exists()
    punto(6, True, f"Se conserva la versión anterior ({previa})", hay)
else:
    punto(6, True, "Se conserva la versión anterior", True, "primera versión")
# 7. evaluación
ev = pr.dir / "06_RECETA" / f"evaluacion_{base}_con-subtitulos.json"
if ev.exists():
    try:
        e = json.loads(ev.read_text(encoding="utf-8"))
        det = f"{e['nota_medida']}/10 clase {e['clase_medida']}"
    except (ValueError, KeyError, TypeError):
        e = None
    if e is None:
        punto(7, False, "Evaluación con nota 8 o más", None, f"{ev.name} no se puede leer: volver a correr evaluar.py")
    elif not e.get("sha256") or not cs.exists():      # sin huella no se sabe si la nota es de ESTE archivo: no comprobado
        punto(7, False, "Evaluación con nota 8 o más", None, det + " · sin huella del video evaluado: volver a correr evaluar.py")
    elif huella(cs) != e["sha256"]:
        punto(7, False, "Evaluación con nota 8 o más", False, det + " · pero es de otro archivo (el video cambió después): volver a correr evaluar.py")
    else:
        punto(7, False, "Evaluación con nota 8 o más",
              (e["nota_medida"] >= 8) if isinstance(e["nota_medida"], (int, float)) else None, det)
else:
    punto(7, False, "Evaluación con nota 8 o más", False, f"falta correr evaluar.py sobre {cs.name}")
# 8. título
punto(8, False, "Título elegido", bool(pr.cfg.get("titulo")), pr.cfg.get("titulo", "sin título en proyecto.json"))
# 9. miniatura
minis = list(pr.publicar.glob("*miniatura*")) if pr.publicar.exists() else []
punto(9, False, "Miniatura lista", bool(minis), ", ".join(m.name for m in minis[:3]))
# 10. Shorts
if pr.cfg.get("vertical"):
    hechos = [q.name.lower().replace("_", "-") for q in pr.salida.glob(f"{base}_*9x16.mp4")]
    falta = [v["nombre"] for v in pr.cfg["vertical"] if not any(v["nombre"].lower().replace("_", "-") in h for h in hechos)]
    punto(10, False, "Shorts de esta versión", not falta, "faltan: " + ", ".join(falta) if falta else f"{len(pr.cfg['vertical'])} listos")
else:
    punto(10, False, "Shorts de esta versión", True, "no se pidieron")

# 11. perfil bajo: los videos que salen no llevan GPS, celular ni fecha del original (T1, 08-11-2026)
salen = videos_de_la_version()
if not salen:
    punto(11, True, "Sin metadatos personales (GPS, celular, fecha)", False, "no hay videos que revisar")
else:
    leidos = {p.name: metadatos_personales(p) for p in salen}
    sin_leer = [k for k, v in leidos.items() if v is None]
    con = [f"{k}: {', '.join(v)}" for k, v in leidos.items() if v]
    punto(11, True, "Sin metadatos personales (GPS, celular, fecha)",
          None if sin_leer and not con else not con,
          ("quedan: " + "; ".join(con)) if con else (("no se pudo leer: " + ", ".join(sin_leer)) if sin_leer else f"{len(salen)} videos limpios"))

# 12. formato ideal para YouTube, TikTok e Instagram (recomendado: las plataformas igual lo aceptan, pero lo recodifican peor)
if salen:
    difs = {p.name: formato_plataformas(p) for p in salen}
    con = [f"{k}: {'; '.join(v)}" for k, v in difs.items() if v]
    sin_leer = [k for k, v in difs.items() if v is None]
    punto(12, False, "Formato para las plataformas (MP4, H.264 4:2:0, AAC-LC 48 kHz estéreo, fast start)",
          None if sin_leer and not con else not con,
          ("distinto: " + " · ".join(con)) if con else (("no se pudo leer: " + ", ".join(sin_leer)) if sin_leer else f"{len(salen)} videos en el formato ideal"))

# 13. pico real (0.14): las plataformas recodifican; sobre -1 dBTP puede sonar saturado en el celular. Se mide en todos
#     los videos de la versión (largo, con subtítulos y Shorts), no solo en el de YouTube.
if salen:
    picos = {}
    for q in salen:
        if q == yt:
            picos[q.name] = pico_real
            continue
        e = ff("-i", q, "-af", "ebur128=peak=true", "-vn")
        m = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e or "")
        picos[q.name] = float(m[-1]) if m else None
    sin_medir = [k for k, v in picos.items() if v is None]
    altos = [f"{k}: {v} dBTP" for k, v in picos.items() if v is not None and v > -1.0]
    medidos = [v for v in picos.values() if v is not None]
    punto(13, False, "Pico real de -1 dBTP o menos", None if sin_medir and not altos else not altos,
          "; ".join(altos) if altos else (("no se pudo medir: " + ", ".join(sin_medir)) if sin_medir
                                          else f"máximo {max(medidos)} dBTP en {len(medidos)} videos"))

ok = all(r[3] is True for r in R if r[1])          # «no comprobado» (None) no cuenta como aprobado
nc = [str(r[0]) for r in R if r[1] and r[3] is None]
lineas = [f"# ¿Terminado? {base}", "", f"**{'SÍ: lo obligatorio pasa' if ok else 'NO: falla algo obligatorio' + (' o no se pudo comprobar (' + ', '.join(nc) + ')' if nc else '')}**", "",
          "✓ aprobado · ✗ falla · ? no comprobado (cuenta como no terminado) · – recomendado que falta", "",
          "| # | punto | | detalle |", "|---|---|---|---|"]
for n, ob, t, k, d in R:
    marca = "?" if k is None else ("✓" if k else ("✗" if ob else "–"))
    lineas.append(f"| {n} | {t}{'' if ob else ' (recomendado)'} | {marca} | {d} |")
DESPUES = sellos()
if DESPUES != ANTES:
    cambio = sorted(k for k in set(ANTES) | set(DESPUES) if ANTES.get(k) != DESPUES.get(k))
    print("NO SE FIRMA: cambió un video mientras se revisaba (" + ", ".join(cambio) + "). Esperar a que termine el render "
          "y correr terminado.py otra vez. No se escribió terminado_" + base + ".md ni .json.", flush=True)
    sys.exit(1)
sal = pr.salida / f"terminado_{base}.md"
sal.write_text("\n".join(lineas) + "\n", encoding="utf-8")
# lo que se revisó, con su huella: si un video cambia después, este «terminado» deja de valer (lo leen ficha.py y el gerente)
(pr.salida / f"terminado_{base}.json").write_text(json.dumps(
    {"base": base, "ok": ok, "videos": DESPUES}, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n".join(lineas[2:]), flush=True)
print("LISTO", sal)
sys.exit(0 if ok else 1)
