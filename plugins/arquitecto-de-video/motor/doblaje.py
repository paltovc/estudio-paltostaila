# Doblaje y subtítulos de un video a otro idioma, en cualquier dirección entre español, inglés y portugués (0.15;
# antes solo inglés → español, que sigue siendo lo que pasa si no se dice nada).
# Nada clona voces: la voz nueva es una voz del estudio (edge-tts) o la que se genere en la página de voz del canal
# (o una voz local con licencia, p. ej. Kokoro, cargada como archivos con --desde-archivos).
#
#   1) python doblaje.py preparar "<video.mp4>" [--origen en] [--destino es] [--carpeta <trabajo>]
#        (--idioma es el nombre antiguo de --origen y sigue sirviendo)
#        transcribe (WhisperX o faster-whisper, local) y deja <video>_doblaje\segmentos.json con cada frase:
#        {"id", "inicio", "fin", "original", "traduccion": "", "max_caracteres"} + original.srt
#   2) Claude (o la persona) llena "traduccion" (en el idioma destino) en segmentos.json. Regla: que se pueda decir en el
#        mismo tiempo: "max_caracteres" sale del ritmo del idioma destino (CPS: es 15, en 14, pt 15 caracteres por segundo;
#        se cambia con --cps); mejor una frase más corta que una voz apurada.
#   3) python doblaje.py voz "<carpeta>" [--voz <voz>] [--velocidad_max 25]
#        sin --voz usa la del idioma destino (VOCES: es-CL-LorenzoNeural, en-US-GuyNeural, pt-BR-AntonioNeural; para
#        Oceanía en-AU-WilliamNeural). La voz tiene que ser del idioma destino (o multilingüe): si no, se detiene.
#        genera la voz frase por frase calzada con su tiempo (si no cabe, la acelera hasta --velocidad_max %; si aún no cabe,
#        usa la pausa siguiente y lo avisa) -> voz_traducida.wav + traduccion.srt
#        O con voces hechas afuera (página de voz con licencia): textos_para_voz.txt tiene las frases numeradas;
#        guardar 001.mp3, 002.mp3 ... en <carpeta>\voces y correr: python doblaje.py voz "<carpeta>" --desde-archivos
#   4) python doblaje.py mezclar "<carpeta>" [--original -16|sin] [--quemar]
#        <video>_<DESTINO>.mp4 (_ES, _EN o _PT): imagen original + voz nueva; el audio original queda debajo y baja solo
#        cuando habla la voz nueva (estilo documental) o "sin" lo quita. --quemar: también una versión con subtítulos.
#        Las dos salen con fast start y sin listas de edición (0.15).
#   Solo subtítulos (sin voz): después del paso 2, python doblaje.py subtitulos "<carpeta>" -> traduccion.srt
# Licencias: edge-tts no trae licencia comercial explícita (ver voces.py): para lo que se publica, la voz de la página con
# licencia (--desde-archivos). Cada corrida con edge-tts lo deja escrito en avisos.txt.
import asyncio, json, re, shutil, subprocess, sys
from pathlib import Path

try:
    from estudio import FFMPEG, FFPROBE, nombre_libre, apartar_anterior
except Exception:
    FFMPEG, FFPROBE = "ffmpeg", "ffprobe"
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

try:
    from estudio import SIN_LISTAS             # 0.15: entregas sin listas de edición (edts/elst)
except Exception:
    SIN_LISTAS = ["-use_editlist", "0"]

ESTUDIO = Path.home() / "EstudioPaltostaila"
IDIOMAS = ("es", "en", "pt")
# voz del estudio por idioma destino (edge-tts; nombres de `voces.py listar --idioma <xx>`, revisar ahí si alguna deja
# de estar). Para publicar, mejor la página de voz con licencia o una voz local con licencia (--desde-archivos).
VOCES = {"es": "es-CL-LorenzoNeural", "en": "en-US-GuyNeural", "pt": "pt-BR-AntonioNeural"}
OTRAS_VOCES = {"en": ["en-AU-WilliamNeural", "en-AU-NatashaNeural", "en-US-JennyNeural"], "pt": ["pt-BR-FranciscaNeural"],
               "es": ["es-CL-CatalinaNeural", "es-MX-JorgeNeural"]}
# caracteres por segundo que se pueden decir con calma (aproximado; el español y el portugués usan palabras más largas)
CPS = {"es": 15, "en": 14, "pt": 15}
AVISO_LICENCIA = ("AVISO licencia: la voz se hizo con edge-tts (servicio de Edge usado de forma no oficial, sin licencia "
                  "comercial explícita). Sirve para probar y para borradores; para publicar, generar las frases en la "
                  "página de voz con licencia y usar --desde-archivos (ver voces.py).")


def _idioma(x, defecto):
    x = (x or defecto).lower()[:2]
    if x not in IDIOMAS:
        sys.exit(f"Idioma «{x}» no soportado: usar es, en o pt")
    return x


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


def preparar(video, idioma="en", carpeta=None, destino="es", cps=None):
    idioma, destino = _idioma(idioma, "en"), _idioma(destino, "es")
    if idioma == destino:
        sys.exit(f"El origen y el destino son el mismo idioma ({idioma}): no hay nada que doblar")
    cps = float(cps or CPS[destino])
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
    run([FFMPEG, "-v", "error", "-y", "-i", video, "-vn", "-ac", 1, "-ar", 16000, *SIN_METADATOS, wav])
    print("transcribiendo (puede tardar unos minutos por minuto de video)...", flush=True)
    segs = frases(transcribir(wav, idioma, c))
    for s in segs:                       # guía para la traducción: lo que cabe en ese tiempo al ritmo del idioma destino
        s["max_caracteres"] = max(4, int((s["fin"] - s["inicio"]) * cps))
    # "idioma" = idioma de origen (nombre de siempre); "origen"/"destino"/"cps" desde el 0.15
    (c / "segmentos.json").write_text(json.dumps({"video": str(video.resolve()), "idioma": idioma, "origen": idioma,
                                                  "destino": destino, "cps": cps, "segmentos": segs},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    escribir_srt(segs, "original", c / "original.srt")
    print(f"{len(segs)} frases {idioma} -> {destino} -> {c / 'segmentos.json'}  (llenar \"traduccion\" en {destino}, "
          f"hasta \"max_caracteres\" por frase: {cps:g} caracteres por segundo)")
    return c


def destino_de(d):
    """Idioma destino de una carpeta de doblaje (las hechas antes del 0.15 son inglés → español)."""
    return _idioma(d.get("destino"), "es")


def cargar(c):
    d = json.loads((Path(c) / "segmentos.json").read_text(encoding="utf-8"))
    falta = [s["id"] for s in d["segmentos"] if not s.get("traduccion")]
    if falta:
        print(f"AVISO {len(falta)} frases sin traducción (ids {falta[:10]}{'...' if len(falta) > 10 else ''}); quedan sin voz")
    return d


def recortar(src, carpeta=None):
    """Quita el silencio del principio y del final (las voces generadas traen aire) -> .wav en `carpeta` (o al lado);
    devuelve su largo."""
    w = (Path(carpeta) if carpeta else Path(src).parent) / (Path(src).stem + ".recortado.wav")
    sil = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03"
    run([FFMPEG, "-v", "error", "-y", "-i", src, "-af", f"{sil},areverse,{sil},areverse", "-ar", 48000, *SIN_METADATOS, w])
    return w, dur(w)


async def _tts(texto, voz, destino, vel):
    import edge_tts
    await edge_tts.Communicate(texto, voz, rate=f"{vel:+d}%").save(str(destino))


def voz(c, nombre_voz=None, vel_max=25, desde_archivos=False):
    c = Path(c)
    d = cargar(c)
    dest = destino_de(d)
    nombre_voz = nombre_voz or VOCES[dest]
    if not desde_archivos and not nombre_voz.lower().startswith(dest + "-") and "multilingual" not in nombre_voz.lower():
        sys.exit(f"La voz {nombre_voz} no es del idioma destino ({dest}). Usar {VOCES[dest]}"
                 + (f" (u otra: {', '.join(OTRAS_VOCES.get(dest, []))})" if OTRAS_VOCES.get(dest) else "")
                 + f", una multilingüe, o ver python voces.py listar --idioma {dest}")
    segs = [s for s in d["segmentos"] if s.get("traduccion")]
    cps = float(d.get("cps") or CPS[dest])
    apuradas = [f"frase {s['id']} ({s['inicio']:.1f} s): {len(s['traduccion'])} caracteres en {s['fin'] - s['inicio']:.1f} s "
                f"(caben ~{int((s['fin'] - s['inicio']) * cps)} a {cps:g}/s en {dest}): acortarla"
                for s in segs if len(s["traduccion"]) > (s["fin"] - s["inicio"]) * cps * 1.15 + 3]
    (c / "textos_para_voz.txt").write_text("".join(f"{s['id']:03d}  ({s['fin'] - s['inicio']:.1f} s)  {s['traduccion']}\n" for s in segs),
                                          encoding="utf-8")
    vdir = c / "voces"                 # voces hechas afuera (página de voz con licencia): aquí solo se LEE
    tdir = c / "voces_tts"             # voces del estudio (edge-tts): nunca en voces\, para no pisar las de afuera
    if desde_archivos:
        vdir.mkdir(exist_ok=True)
    tdir.mkdir(exist_ok=True)
    import datetime as _dt
    hecha_antes = (c / "segmentos.json").exists() and _dt.date.fromtimestamp((c / "segmentos.json").stat().st_ctime) <= _dt.date(2026, 11, 8)
    if desde_archivos and any(vdir.glob("*.mp3")) and hecha_antes:      # carpeta hecha antes del cambio
        print("AVISO: antes del 08-11-2026 las voces del estudio (edge-tts) también se guardaban en voces\\. "
              "Confirma que las de esa carpeta son las hechas afuera con licencia.", flush=True)
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
            src, largo = recortar(src, tdir)          # el recorte va a voces_tts\\: voces\\ solo se lee
        else:
            src, vel = tdir / f"{s['id']:03d}.mp3", 0
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
    r = subprocess.run([str(x) for x in [FFMPEG, "-v", "error", "-y", *ins, "-/filter_complex", script, *SIN_METADATOS, *cola]],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex_script", script, *SIN_METADATOS, *cola])
    import audio as au
    au.normalizar(c / "voz_traducida_paso.wav", c / "voz_traducida.wav")
    (c / "voz_traducida_paso.wav").unlink()
    escribir_srt(d["segmentos"], "traduccion", c / "traduccion.srt")
    avisos = ([] if desde_archivos else [AVISO_LICENCIA + f" Voz: {nombre_voz}."]) + apuradas + avisos
    (c / "avisos.txt").write_text("\n".join(avisos) + "\n", encoding="utf-8")
    print(*avisos, sep="\n")
    print("listo:", c / "voz_traducida.wav", "y", c / "traduccion.srt", f"({dest})")


def mezclar(c, original="-16", quemar=False):
    c = Path(c)
    d = cargar(c)
    video = Path(d["video"])
    suf = destino_de(d).upper()                   # _ES como siempre; _EN o _PT para los otros destinos
    sal = nombre_libre(c / f"{video.stem}_{suf}.mp4")
    if original == "sin":
        fc = "[1:a]anull[aud]"
    else:
        import audio as au
        fc = au.filtro_musica(1, 0, float(original), True, "aud")
    run([FFMPEG, "-v", "error", "-y", "-i", video, "-i", c / "voz_traducida.wav", "-filter_complex", fc,
         "-map", "0:v", "-map", "[aud]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", *SIN_METADATOS, *SIN_LISTAS,
         "-movflags", "+faststart", sal])
    print("listo:", sal)
    if quemar:
        sub = c / "traduccion.srt"
        sal2 = nombre_libre(c / f"{video.stem}_{suf}_subtitulado.mp4")      # un segundo --quemar no pisa el anterior
        run([FFMPEG, "-v", "error", "-y", "-i", sal.name, "-vf",
             "subtitles=traduccion.srt:force_style='FontName=Arial,FontSize=20,Bold=1,Outline=2,MarginV=40'",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "copy", *SIN_METADATOS, *SIN_LISTAS,
             "-movflags", "+faststart", sal2.name], cwd=c)          # 0.15: fast start también en la subtitulada
        print("listo:", sal2)
    try:
        from estudio import metadatos_personales
    except ImportError:
        return
    malos = []
    for v in [sal] + ([sal2] if quemar else []):
        m = metadatos_personales(Path(c) / Path(v).name)
        print("metadatos personales:", Path(v).name, "no se pudo leer (revisar)" if m is None else ("ninguno" if not m else "REVISAR: " + ", ".join(m)))
        if m is None or m:
            malos.append(Path(v).name)
    if malos:
        sys.exit("REVISAR metadatos en: " + ", ".join(malos))


def main():
    a = sys.argv[1:]
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a:
        sys.exit("Uso: ver el encabezado de doblaje.py")
    if a[0] == "preparar":
        preparar(a[1], op("--origen") or op("--idioma", "en"), op("--carpeta"), op("--destino", "es"), op("--cps"))
    elif a[0] == "voz":
        voz(a[1], op("--voz"), int(op("--velocidad_max", 25)), "--desde-archivos" in a)
    elif a[0] == "subtitulos":
        d = cargar(a[1])
        escribir_srt(d["segmentos"], "traduccion", Path(a[1]) / "traduccion.srt")
        print("listo:", Path(a[1]) / "traduccion.srt")
    elif a[0] == "mezclar":
        mezclar(a[1], op("--original", "-16"), "--quemar" in a)
    print("LISTO", flush=True)


if __name__ == "__main__":
    main()
