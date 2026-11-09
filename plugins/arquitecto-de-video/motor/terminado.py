# Definición de "terminado" del estudio: una lista que se revisa con sí o no, sin opiniones.
#   python terminado.py "<proyecto>" [--version v8]
# Deja 07_RENDER\terminado_<ID>_<version>.md con cada punto (✓ / ✗ / –) y termina con código 0 solo si todo lo
# obligatorio pasa. Claude la corre antes de decir "listo" y entrega el resultado tal cual.
# Obligatorio: 1-6 y 11. Recomendado: 7-10 y 12 (si falla, se avisa pero no bloquea).
import json, re, subprocess, sys
from pathlib import Path
from estudio import Proyecto, FFMPEG, duracion_medio, metadatos_personales, formato_plataformas

pr = Proyecto()
args = sys.argv[1:]
ver = args[args.index("--version") + 1] if "--version" in args else pr.version
base = f"{pr.id}_{ver}"
R = []


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
    punto(2, True, "La duración calza con la voz (±1,5 s)", abs(dv - dz) <= 1.5, f"video {dv:.1f} s · voz {dz:.1f} s")
    # 3. volumen
    e = ff("-i", yt, "-af", "ebur128", "-vn")
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", e or "")
    lufs = float(m[-1]) if m else None
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
    e = json.loads(ev.read_text(encoding="utf-8"))
    punto(7, False, "Evaluación con nota 8 o más", e["nota_medida"] >= 8, f"{e['nota_medida']}/10 clase {e['clase_medida']}")
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
salen = sorted({p for p in (*pr.salida.glob(f"{base}_*.mp4"), *(pr.salida / "celu").glob(f"{base}_*.mp4"))
                if ".parcial" not in p.name and "_anterior-" not in p.name})
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
          ("distinto: " + " | ".join(con)) if con else (("no se pudo leer: " + ", ".join(sin_leer)) if sin_leer else f"{len(salen)} videos en el formato ideal"))

ok = all(r[3] is True for r in R if r[1])          # «no comprobado» (None) no cuenta como aprobado
nc = [str(r[0]) for r in R if r[1] and r[3] is None]
lineas = [f"# ¿Terminado? {base}", "", f"**{'SÍ: lo obligatorio pasa' if ok else 'NO: falla algo obligatorio' + (' o no se pudo comprobar (' + ', '.join(nc) + ')' if nc else '')}**", "",
          "✓ aprobado · ✗ falla · ? no comprobado (cuenta como no terminado) · – recomendado que falta", "",
          "| # | punto | | detalle |", "|---|---|---|---|"]
for n, ob, t, k, d in R:
    marca = "?" if k is None else ("✓" if k else ("✗" if ob else "–"))
    lineas.append(f"| {n} | {t}{'' if ob else ' (recomendado)'} | {marca} | {d} |")
sal = pr.salida / f"terminado_{base}.md"
sal.write_text("\n".join(lineas) + "\n", encoding="utf-8")
print("\n".join(lineas[2:]), flush=True)
print("LISTO", sal)
sys.exit(0 if ok else 1)
