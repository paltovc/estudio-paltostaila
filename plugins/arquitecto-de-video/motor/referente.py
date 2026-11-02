# Disecciona un video publicado (YouTube, TikTok o Instagram) para entender por que funciona:
# numeros y comparacion con el canal, gancho de los primeros segundos, ritmo de cortes, guion con tiempos,
# miniatura y comentarios. Deja todo en EstudioPaltostaila\referentes\<plataforma>_<id>\ para que el
# agente analista-de-referentes escriba el informe.
#   python referente.py URL                   todo (descarga el video en 720p como maximo)
#   python referente.py URL --sin-video        solo datos y comentarios (rapido)
#   python referente.py URL --transcribir      si no hay subtitulos, transcribe con WhisperX (lento)
#   python referente.py URL --dest "C:\carpeta"
import glob, json, re, subprocess, sys
from pathlib import Path
from estudio import FFMPEG, run, mmss, duracion_medio
from redes import ESTUDIO, llamar, info, promedio_canal, resumen, nombre_seguro, plataforma

args = [a for a in sys.argv[1:]]
if not args or args[0].startswith("-"):
    sys.exit("Uso: python referente.py URL [--sin-video] [--transcribir] [--dest carpeta]")
URL = args[0]
DEST_BASE = Path(args[args.index("--dest") + 1]) if "--dest" in args else ESTUDIO / "referentes"


def vtt_a_texto(ruta):
    """Subtitulos .vtt -> lista de (segundo, texto) sin repeticiones (los automaticos repiten lineas)."""
    out, ultimo = [], ""
    t = 0.0
    for linea in Path(ruta).read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"(\d+):(\d+):(\d+)[.,](\d+) -->", linea) or re.match(r"(\d+):(\d+)[.,](\d+) -->", linea)
        if m:
            g = [int(x) for x in m.groups()]
            t = g[0] * 3600 + g[1] * 60 + g[2] if len(g) == 4 else g[0] * 60 + g[1]
            continue
        limpio = re.sub(r"<[^>]+>", "", linea).strip()
        if not limpio or limpio.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or "-->" in limpio or limpio == ultimo:
            continue
        out.append((t, limpio))
        ultimo = limpio
    return out


def cortes_de_escena(video, umbral=0.3):
    s = run([FFMPEG, "-hide_banner", "-i", video, "-vf", f"select='gt(scene,{umbral})',showinfo", "-an", "-f", "null", "-"])
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", s)]


def main():
    print("leyendo datos y comentarios...", flush=True)
    i = info(URL)
    pl = plataforma(i.get("webpage_url") or URL)
    carpeta = DEST_BASE / f"{pl}_{nombre_seguro(i.get('id'), 40)}"
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = resumen(i)
    mediana, n = promedio_canal(i)
    if mediana:
        datos["mediana_vistas_canal"] = int(mediana)
        datos["videos_canal_comparados"] = n
        datos["veces_sobre_su_canal"] = round(datos["vistas"] / mediana, 1) if datos["vistas"] else None
    coms = sorted(i.get("comments") or [], key=lambda c: -(c.get("like_count") or 0))
    (carpeta / "comentarios.json").write_text(json.dumps(
        [{"texto": c.get("text"), "likes": c.get("like_count"), "autor_es_creador": c.get("author_is_uploader"),
          "respuesta_a": c.get("parent") if c.get("parent") != "root" else None} for c in coms], ensure_ascii=False, indent=1), encoding="utf-8")

    transcripcion = []
    if "--sin-video" not in args:
        print("descargando video (720p max), miniatura y subtitulos...", flush=True)
        ffdir = str(Path(FFMPEG).parent) if Path(FFMPEG).is_absolute() else None
        extra = ["--ffmpeg-location", ffdir] if ffdir else []
        try:
            llamar(["--no-playlist", "--no-warnings", *extra, "-f", "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4",
                    "-o", str(carpeta / "video.%(ext)s"), "--write-thumbnail", "--convert-thumbnails", "jpg", URL], timeout=1800)
        except RuntimeError as e:
            print("aviso: no se pudo descargar el video ->", str(e)[-300:])
        for langs in ("es-orig,es", "es.*", "en-orig,en,pt-orig,pt"):   # subtitulos aparte: un error aqui no frena el resto
            if list(carpeta.glob("video*.vtt")):
                break
            try:
                llamar(["--no-playlist", "--no-warnings", "--skip-download", "--write-subs", "--write-auto-subs",
                        "--sub-langs", langs, "--sub-format", "vtt", "-o", str(carpeta / "video.%(ext)s"), URL], timeout=300)
            except RuntimeError as e:
                print("aviso subtitulos", langs, "->", str(e)[-150:])
        video = next(iter(sorted(carpeta.glob("video*.mp4"))), None)
        subs = sorted(carpeta.glob("video*.vtt"), key=lambda p: (".es" not in p.name, p.name))
        if subs:
            transcripcion = vtt_a_texto(subs[0])
        if video:
            dur = duracion_medio(video)
            cortes = cortes_de_escena(video)
            datos["cortes_total"] = len(cortes)
            datos["cortes_por_minuto"] = round(len(cortes) / (dur / 60), 1) if dur else None
            datos["plano_promedio_s"] = round(dur / (len(cortes) + 1), 1)
            datos["cortes_primeros_10s"] = sum(1 for c in cortes if c <= 10)
            datos["momentos_de_corte"] = [round(c, 2) for c in cortes[:120]]
            run([FFMPEG, "-v", "error", "-y", "-i", video, "-t", "3", "-vf", "fps=2,scale=480:-1,tile=3x2", "-frames:v", "1", carpeta / "gancho_0a3s.jpg"])
            paso = max(dur / 24, 1)
            run([FFMPEG, "-v", "error", "-y", "-i", video, "-vf", f"fps=1/{paso:.2f},scale=360:-1,tile=6x4", "-frames:v", "1", carpeta / "hoja_completa.jpg"])
            if "--transcribir" in args and not transcripcion:
                transcripcion = whisperx(video, carpeta)
    texto = "\n".join(f"[{mmss(t)}] {x}" for t, x in transcripcion)
    if texto:
        (carpeta / "transcripcion.txt").write_text(texto, encoding="utf-8")
    (carpeta / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")

    m = [f"# Referente: {datos['titulo']}", "", f"{datos['url']}", "",
         "| dato | valor |", "|---|---|"]
    for k in ["plataforma", "canal", "seguidores", "fecha", "dias_publicado", "duracion_s", "vistas", "vistas_por_dia",
              "likes", "likes_por_1000_vistas", "comentarios", "comentarios_por_1000_vistas", "mediana_vistas_canal",
              "veces_sobre_su_canal", "cortes_por_minuto", "plano_promedio_s", "cortes_primeros_10s"]:
        if datos.get(k) is not None:
            m.append(f"| {k.replace('_', ' ')} | {datos[k]} |")
    gancho = [x for t, x in transcripcion if t <= 15]
    m += ["", "## Lo que se dice en los primeros 15 s", " ".join(gancho) or "(sin transcripcion)",
          "", "## Comentarios con mas likes"]
    m += [f"- ({c.get('like_count') or 0}) {(c.get('text') or '').strip()[:300]}" for c in coms[:40]]
    m += ["", "## Archivos", "gancho_0a3s.jpg (6 cuadros de los primeros 3 s), hoja_completa.jpg (24 cuadros), miniatura (video*.jpg),",
          "transcripcion.txt, comentarios.json (todos), datos.json"]
    (carpeta / "informe_base.md").write_text("\n".join(m), encoding="utf-8")
    print("\n".join(m[:25]))
    print(f"\n{len(coms)} comentarios leidos. Carpeta: {carpeta}")


def whisperx(video, carpeta):
    exe = next((p for p in [ESTUDIO / "whisperx-venv" / "Scripts" / "whisperx.exe",
                            Path.home() / ".cache" / "watch" / "whisperx-venv" / "Scripts" / "whisperx.exe"] if p.exists()), None)
    if not exe:
        print("aviso: no hay WhisperX; sin transcripcion")
        return []
    wav = carpeta / "audio_16k.wav"
    run([FFMPEG, "-v", "error", "-y", "-i", video, "-ac", "1", "-ar", "16000", wav])
    subprocess.run([str(exe), str(wav), "--model", "medium", "--compute_type", "int8", "--device", "cpu",
                    "--output_format", "json", "--output_dir", str(carpeta)])
    j = carpeta / "audio_16k.json"
    if not j.exists():
        return []
    return [(s["start"], s["text"].strip()) for s in json.loads(j.read_text(encoding="utf-8"))["segments"]]


if __name__ == "__main__":
    main()
