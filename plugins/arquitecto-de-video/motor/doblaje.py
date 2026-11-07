# Doblaje y subtítulos de un video a otro idioma (pensado para pasar los videos en inglés de la pareja al español).
# Nada clona voces: la voz nueva es una voz del estudio (edge-tts) o la que se genere en la página de voz del canal.
#
#   1) python doblaje.py preparar "<video.mp4>" [--idioma en] [--carpeta <trabajo>]
#        transcribe (WhisperX o faster-whisper, local) y deja <video>_doblaje\segmentos.json con cada frase:
#        {"id", "inicio", "fin", "original", "traduccion": ""} + original.srt
#   2) Claude (o la persona) llena "traduccion" en segmentos.json. Regla: que se pueda decir en el mismo tiempo
#        (unos 15 caracteres por segundo); mejor una frase más corta que una voz apurada.
#   3) python doblaje.py voz "<carpeta>" [--voz es-CL-LorenzoNeural] [--velocidad_max 25]
#        genera la voz frase por frase calzada con su tiempo (si no cabe, la acelera hasta --velocidad_max %; si aún no cabe,
#        usa la pausa siguiente y lo avisa) -> voz_traducida.wav + traduccion.srt
#        O con voces hechas afuera (página de voz con licencia): textos_para_voz.txt tiene las frases numeradas;
#        guardar 001.mp3, 002.mp3 ... en <carpeta>\voces y correr: python doblaje.py voz "<carpeta>" --desde-archivos
#   4) python doblaje.py mezclar "<carpeta>" [--original -16|sin] [--quemar]
#        <video>_ES.mp4: imagen original + voz nueva; el audio original queda debajo y baja solo cuando habla la voz nueva
#        (estilo documental, conserva música y ambiente) o "sin" lo quita. --quemar: también una versión con subtítulos.
#   Solo subtítulos (sin voz): después del paso 2, python doblaje.py subtitulos "<carpeta>" -> traduccion.srt
import asyncio, json, re, shutil, subprocess, sys
from pathlib import Path

try:
    from estudio import FFMPEG, FFPROBE, nombre_libre, apartar_anterior
except Exception:
    FFMPEG, FFPROBE = "ffmpeg", "ffprobe"

ESTUDIO = Path.home() / "EstudioPaltostaila"


def run(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode:
        raise SystemExit("falló:\n" + " ".join(map(str, cmd))[:300] + "\n" + r.stderr[-1200:])
    return r.stdout + r.stderr


def dur(p):
    return float(run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).strip().splitlines()[-1])


def srt_t(t):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def escribir_srt(segs, campo, ruta):
    ruta.write_text("".join(f"{i}\n{srt_t(s['inicio'])} --> {srt_t(s['fin'])}\n{s[campo]}\n\n"
                            for i, s in enumerate((x for x in segs if x.get(campo)), 1)), encoding="utf-8")


def transcribir(wav, idioma, carpeta):
    wx = [ESTUDIO / "whisperx-venv" / "Scripts" / "whisperx.exe",
          Path.home() / ".cache" / "watch" / "whisperx-venv" / "Scripts" / "whisperx.exe", Path(shutil.which("whisperx") or "-")]
    exe = next((p for p in wx if p.exists()), None)
    if exe:
        run([exe, wav, "--language", idioma, "--model", "large-v3", "--compute_type", "int8", "--device", "cpu",
             "--output_format", "json", "--output_dir", carpeta])
        return json.loads((carpeta / (Path(wav).stem + ".json")).read_text(encoding="utf-8"))["segments"]
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("No encuentro WhisperX ni faster-whisper para transcribir (instalar-estudio, opción de transcripción).")
    m = WhisperModel("medium", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(str(wav), language=idioma, word_timestamps=True, vad_filter=True)
    return [{"start": s.start, "end": s.end, "text": s.text} for s in segs]


def frases(segs, maximo=12.0):
    """Une trozos de la transcripción en frases completas de hasta 'maximo' segundos."""
    out, actual = [], None
    for s in segs:
        t = s["text"].strip()
        if not t:
            continue
        if actual and (s["end"] - actual["inicio"] <= maximo) and not actual["original"].rstrip().endswith((".", "?", "!")):
            actual["original"] += " " + t
            actual["fin"] = s["end"]
        else:
            if actual:
                out.append(actual)
            actual = {"inicio": round(s["start"], 3), "fin": round(s["end"], 3), "original": t}
    if actual:
        out.append(actual)
    for i, f in enumerate(out, 1):
        f.update(id=i, traduccion="", inicio=round(f["inicio"], 3), fin=round(f["fin"], 3))
    return [{k: f[k] for k in ("id", "inicio", "fin", "original", "traduccion")} for f in out]


def preparar(video, idioma="en", carpeta=None):
    video = Path(video)
    c = Path(carpeta) if carpeta else video.with_name(video.stem + "_doblaje")
    c.mkdir(parents=True, exist_ok=True)
    viejo = c / "segmentos.json"
    if viejo.exists():
        hechas = [s for s in json.loads(viejo.read_text(encoding="utf-8")).get("segmentos", []) if s.get("traduccion")]
        if hechas and "--rehacer" not in sys.argv:
            sys.exit(f"{viejo} ya tiene {len(hechas)} traducciones: no se borran. Usa --rehacer para transcribir de nuevo "
                     "(el archivo actual queda guardado como segmentos_anterior-<fecha>.json)")
        apartar_anterior(viejo)
    wav = c / "audio_16k.wav"
    run([FFMPEG, "-v", "error", "-y", "-i", video, "-vn", "-ac", 1, "-ar", 16000, wav])
    print("transcribiendo (puede tardar unos minutos por minuto de video)...", flush=True)
    segs = frases(transcribir(wav, idioma, c))
    (c / "segmentos.json").write_text(json.dumps({"video": str(video.resolve()), "idioma": idioma, "segmentos": segs},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    escribir_srt(segs, "original", c / "original.srt")
    print(f"{len(segs)} frases -> {c / 'segmentos.json'}  (llenar \"traduccion\")")
    return c


def cargar(c):
    d = json.loads((Path(c) / "segmentos.json").read_text(encoding="utf-8"))
    falta = [s["id"] for s in d["segmentos"] if not s.get("traduccion")]
    if falta:
        print(f"AVISO {len(falta)} frases sin traducción (ids {falta[:10]}{'...' if len(falta) > 10 else ''}); quedan sin voz")
    return d


def recortar(src):
    """Quita el silencio del principio y del final (las voces generadas traen aire) -> .wav al lado; devuelve su largo."""
    w = Path(src).with_suffix(".recortado.wav")
    sil = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03"
    run([FFMPEG, "-v", "error", "-y", "-i", src, "-af", f"{sil},areverse,{sil},areverse", "-ar", 48000, w])
    return w, dur(w)


async def _tts(texto, voz, destino, vel):
    import edge_tts
    await edge_tts.Communicate(texto, voz, rate=f"{vel:+d}%").save(str(destino))


def voz(c, nombre_voz="es-CL-LorenzoNeural", vel_max=25, desde_archivos=False):
    c = Path(c)
    d = cargar(c)
    segs = [s for s in d["segmentos"] if s.get("traduccion")]
    (c / "textos_para_voz.txt").write_text("".join(f"{s['id']:03d}  ({s['fin'] - s['inicio']:.1f} s)  {s['traduccion']}\n" for s in segs),
                                          encoding="utf-8")
    vdir = c / "voces"
    vdir.mkdir(exist_ok=True)
    total = dur(d["video"])
    partes, avisos, solapes = [], [], []
    for i, s in enumerate(segs):
        hueco = (segs[i + 1]["inicio"] if i + 1 < len(segs) else total) - s["inicio"]
        espacio = s["fin"] - s["inicio"]
        if desde_archivos:
            src = next((p for p in sorted(vdir.glob(f"{s['id']:03d}.*")) if ".recortado" not in p.name), None)
            if not src:
                avisos.append(f"frase {s['id']}: falta voces\\{s['id']:03d}.mp3")
                continue
            vel = 0
            src, largo = recortar(src)
        else:
            src, vel = vdir / f"{s['id']:03d}.mp3", 0
            asyncio.run(_tts(s["traduccion"], nombre_voz, src, 0))
            src_w, largo = recortar(src)
            if largo > espacio * 1.02:                         # no cabe: acelerar lo justo
                vel = min(vel_max, int((largo / espacio - 1) * 100) + 3)
                asyncio.run(_tts(s["traduccion"], nombre_voz, src, vel))
                src_w, largo = recortar(src)
            src = src_w
        tempo = 1.0
        if largo > hueco:                                       # ni acelerada cabe antes de la frase siguiente
            tempo = min(1.25, largo / hueco)
            if largo / tempo > hueco + 0.1:
                solapes.append(f"frase {s['id']} ({s['inicio']:.1f} s): dura {largo / tempo:.1f} s y hay {hueco:.1f} s; acórtala")
            else:
                avisos.append(f"frase {s['id']} ({s['inicio']:.1f} s): la traducción es larga; acórtala (va {tempo:.2f}x)")
        elif largo > espacio:
            avisos.append(f"frase {s['id']} ({s['inicio']:.1f} s): usa {largo - espacio:.1f} s de la pausa siguiente")
        partes.append((s["inicio"], src, tempo))
        print(f"  {s['id']:03d} {largo:.1f}/{espacio:.1f} s{' +%d%%' % vel if vel else ''}", flush=True)
    if solapes and "--permitir-solapes" not in sys.argv:
        (c / "frases_largas.txt").write_text("\n".join(solapes) + "\n", encoding="utf-8")
        print(*solapes, sep="\n")
        sys.exit(f"{len(solapes)} frases se montan sobre la siguiente (lista en frases_largas.txt): acórtalas en segmentos.json "
                 "y vuelve a correr voz (o usa --permitir-solapes)")
    # línea de tiempo: cada frase en su segundo
    ins, filtros = [], []
    for k, (t0, src, tempo) in enumerate(partes):
        ins += ["-i", src]
        filtros.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo{',atempo=%.3f' % tempo if tempo > 1 else ''},"
                       f"adelay={int(t0 * 1000)}:all=1[a{k}]")
    mezcla = ";".join(filtros) + ";" + "".join(f"[a{k}]" for k in range(len(partes))) + \
        f"amix=inputs={len(partes)}:normalize=0:dropout_transition=0,apad,atrim=0:{total:.3f}[v]"
    script = c / "_mezcla.txt"
    script.write_text(mezcla, encoding="utf-8")
    # ffmpeg 7.1+ lee el filtro desde archivo con "-/filter_complex"; las versiones viejas con "-filter_complex_script"
    cola = ["-map", "[v]", c / "voz_traducida_paso.wav"]
    r = subprocess.run([str(x) for x in [FFMPEG, "-v", "error", "-y", *ins, "-/filter_complex", script, *cola]],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex_script", script, *cola])
    import audio as au
    au.normalizar(c / "voz_traducida_paso.wav", c / "voz_traducida.wav")
    (c / "voz_traducida_paso.wav").unlink()
    escribir_srt(d["segmentos"], "traduccion", c / "traduccion.srt")
    (c / "avisos.txt").write_text("\n".join(avisos) + "\n", encoding="utf-8")
    print(*avisos, sep="\n")
    print("listo:", c / "voz_traducida.wav", "y", c / "traduccion.srt")


def mezclar(c, original="-16", quemar=False):
    c = Path(c)
    d = cargar(c)
    video = Path(d["video"])
    sal = nombre_libre(c / f"{video.stem}_ES.mp4")
    if original == "sin":
        fc = "[1:a]anull[aud]"
    else:
        import audio as au
        fc = au.filtro_musica(1, 0, float(original), True, "aud")
    run([FFMPEG, "-v", "error", "-y", "-i", video, "-i", c / "voz_traducida.wav", "-filter_complex", fc,
         "-map", "0:v", "-map", "[aud]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", sal])
    print("listo:", sal)
    if quemar:
        sub = c / "traduccion.srt"
        sal2 = c / f"{video.stem}_ES_subtitulado.mp4"
        run([FFMPEG, "-v", "error", "-y", "-i", sal.name, "-vf",
             "subtitles=traduccion.srt:force_style='FontName=Arial,FontSize=20,Bold=1,Outline=2,MarginV=40'",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "copy", sal2.name], cwd=c)
        print("listo:", sal2)


def main():
    a = sys.argv[1:]
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a:
        sys.exit("Uso: ver el encabezado de doblaje.py")
    if a[0] == "preparar":
        preparar(a[1], op("--idioma", "en"), op("--carpeta"))
    elif a[0] == "voz":
        voz(a[1], op("--voz", "es-CL-LorenzoNeural"), int(op("--velocidad_max", 25)), "--desde-archivos" in a)
    elif a[0] == "subtitulos":
        d = cargar(a[1])
        escribir_srt(d["segmentos"], "traduccion", Path(a[1]) / "traduccion.srt")
        print("listo:", Path(a[1]) / "traduccion.srt")
    elif a[0] == "mezclar":
        mezclar(a[1], op("--original", "-16"), "--quemar" in a)
    print("LISTO", flush=True)


if __name__ == "__main__":
    main()
