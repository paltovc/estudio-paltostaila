# Terminacion: subtitulos rehechos palabra por palabra, rotulos, voz a -14 LUFS, capa de efectos
# (si sonidos.py la dejo lista) y los archivos finales para YouTube y TikTok.
#   python terminar.py "C:\ruta\video"                 finales completos
#   python terminar.py "C:\ruta\video" --borrador 60    borrador con todo, sobre el armado de 60 s
#   python terminar.py "C:\ruta\video" --muestras 16,80 fotogramas con subtitulos en esos segundos
#   python terminar.py "C:\ruta\video" --solo-audio     rehace el audio y lo cambia sin recodificar la imagen
import json, os, re, sys
from pathlib import Path
from estudio import Proyecto, FFMPEG, run, palabras, buscar, cues, ts, mmss, clips_pendientes, apartar_anterior
import vivo

pr = Proyecto()
ARG = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
SUB = pr["subtitulos"]
W, H = pr.ancho, pr.alto
F = SUB["fuente"]
esc = H / 1080   # los tamanos estan pensados para 1080 de alto

CABECERA = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{F},{round(SUB['tamano'] * esc)},&H00FFFFFF,&H00FFFFFF,&H64000000,&H64000000,-1,0,0,0,100,100,0,0,3,{round(12 * esc)},0,2,{round(260 * W / 1920)},{round(260 * W / 1920)},{round(48 * esc)},1
Style: Rotulo,{F},{round(52 * esc)},&H00FFFFFF,&H00FFFFFF,&H183A1F0B,&H183A1F0B,-1,0,0,0,100,100,0,0,3,{round(18 * esc)},0,7,48,48,{round(44 * esc)},1
Style: Definicion,{F},{round(44 * esc)},&H002B2118,&H002B2118,&H10EDF8FA,&H10EDF8FA,-1,0,0,0,100,100,0,0,3,{round(18 * esc)},0,9,48,48,{round(44 * esc)},1
Style: Pregunta,{F},{round(56 * esc)},&H00FFFFFF,&H00FFFFFF,&H183A1F0B,&H183A1F0B,-1,0,0,0,100,100,0,0,3,{round(20 * esc)},0,8,220,220,{round(56 * esc)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def escribir_ass(ruta, rotulos, subs, extra=(), estilos=()):
    lineas = [vivo.insertar(CABECERA, estilos) if estilos else CABECERA]
    for t0, t1, chico, grande, estilo in rotulos:
        g = round({"Rotulo": 52, "Pregunta": 56, "Definicion": 44}[estilo] * esc)
        c_chico, c_grande = ("&H3F9E3A&", "&H2B2118&") if estilo == "Definicion" else ("&H6AD15B&", "&HFFFFFF&")
        txt = f"{{\\fad(300,300)}}{{\\fs{round(32 * esc)}\\c{c_chico}}}{chico}\\N{{\\fs{g}\\c{c_grande}}}{grande}"
        lineas.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},{estilo},,0,0,0,,{txt}\n")
    for t0, t1, txt in subs:
        lineas.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},Sub,,0,0,0,,{txt}\n")
    lineas += [l + "\n" for l in extra]
    Path(ruta).write_text("".join(lineas), encoding="utf-8-sig")


def audio(dur):
    """Voz unida y a -14 LUFS (dos pasadas) -> tmp/voz.wav; con efectos -> tmp/narracion.m4a"""
    auds = pr.audios()
    ins = sum([["-i", a] for a in auds], [])
    base = f"concat=n={len(auds)}:v=0:a=1"
    av = pr.cfg.get("audio_voz") or {}
    import audio as _au
    limpieza = _au.cadena_voz(av.get("limpiar"), av.get("radio", False))
    if limpieza:                                   # limpieza y ecualización de la voz (audio.py), antes de medir
        base += "," + limpieza
        print(f"audio: voz limpiada ({av.get('limpiar') or 'sin limpieza'}{', voz de radio' if av.get('radio') else ''})", flush=True)
    L = pr["volumen_lufs"]
    medida = run([FFMPEG, "-hide_banner", *ins, "-filter_complex", f"{base},loudnorm=I={L}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = json.loads(medida[medida.rindex("{"):medida.rindex("}") + 1])
    # ganancia hasta el objetivo + limitador; se repite porque el limitador baja un poco el volumen en voces
    # con picos altos (loudnorm lineal se quedaba corto: -15,7 en vez de -14)
    ganancia = L - float(m["input_i"])
    lim = "alimiter=limit=0.89:attack=5:release=80:level=0"
    run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex",
         f"{base},volume={ganancia:.2f}dB,{lim},aresample=48000,aformat=channel_layouts=stereo",
         "-t", f"{dur:.3f}", pr.tmp / "voz_paso.wav"])
    for _ in range(3):
        med = run([FFMPEG, "-hide_banner", "-i", pr.tmp / "voz_paso.wav", "-af", "ebur128", "-f", "null", "-"])
        actual = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", med)[-1])
        if abs(actual - L) <= 0.3:
            break
        run([FFMPEG, "-v", "error", "-y", "-i", pr.tmp / "voz_paso.wav", "-af", f"volume={L - actual:.2f}dB,{lim}",
             pr.tmp / "voz_paso2.wav"])
        (pr.tmp / "voz_paso2.wav").replace(pr.tmp / "voz_paso.wav")
    run([FFMPEG, "-v", "error", "-y", "-i", pr.tmp / "voz_paso.wav", "-af",
         f"afade=t=in:d=0.3,afade=t=out:st={dur - 1.2:.3f}:d=1.2", pr.tmp / "voz.wav"])
    mus = pr.cfg.get("musica") or {}
    voz_final = pr.tmp / "voz.wav"                 # voz.wav queda siempre solo con la voz (paquete de CapCut, doblaje)
    if mus.get("archivo"):                         # música bajo la voz, con ducking (audio.py)
        con_mus = pr.tmp / "voz_musica.wav"
        _au.mezclar(pr.tmp / "voz.wav", pr.ruta(mus["archivo"]), con_mus, mus.get("volumen", -20), mus.get("ducking", True),
                    mus.get("desde", 0.0))
        run([FFMPEG, "-v", "error", "-y", "-i", con_mus, "-af", f"afade=t=out:st={dur - 2.0:.3f}:d=2.0", "-t", f"{dur:.3f}",
             pr.tmp / "voz_musica2.wav"])
        voz_final = pr.tmp / "voz_musica2.wav"
        print(f"audio: música bajo la voz ({mus.get('volumen', -20)} dB, ducking {'sí' if mus.get('ducking', True) else 'no'})", flush=True)
    efectos = pr.tmp / "efectos.wav"
    if efectos.exists() and pr["sonidos"]["activar"] and os.environ.get("SIN_EFECTOS") != "1":
        run([FFMPEG, "-v", "error", "-y", "-i", voz_final, "-i", efectos, "-filter_complex",
             "[0:a][1:a]amix=inputs=2:normalize=0:dropout_transition=0,alimiter=limit=0.89:level=0",
             "-t", f"{dur:.3f}", "-c:a", "aac", "-b:a", "192k", pr.tmp / "narracion.m4a"])
        print("audio: voz + efectos", flush=True)
    else:
        run([FFMPEG, "-v", "error", "-y", "-i", voz_final, "-c:a", "aac", "-b:a", "192k", pr.tmp / "narracion.m4a"])
        print("audio: solo voz", flush=True)


ENCODE = ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(pr["video"]["crf"]), "-pix_fmt", "yuv420p", "-r", str(pr.fps)]


def preparar():
    segs, pals = palabras(pr, avisar=True)
    subs = cues(segs, SUB["max_caracteres"])
    pares = sorted(((buscar(pals, r["frase"]), r) for r in pr["rotulos"]), key=lambda x: x[0])
    tiempos = [t for t, _ in pares]
    rotulos = []
    for i, (t0, r) in enumerate(pares):
        fin = t0 + float(r.get("segundos", 5))
        if i + 1 < len(tiempos) and tiempos[i + 1] > t0:
            fin = min(fin, tiempos[i + 1] - 0.15)
        estilo = {"pregunta": "Pregunta", "definicion": "Definicion"}.get(r.get("estilo", ""), "Rotulo")
        if r["chico"].upper().startswith("PREGUNTA") and "estilo" not in r:
            estilo = "Pregunta"
        rotulos.append((t0, fin, r["chico"], r["grande"], estilo))
    if vivo.activo(pr):   # subtítulos dinámicos y/o elementos animados (vivo.py)
        v = vivo.Vivo(pr, pals, W, H, vertical=H > W)
        if SUB.get("evitar_caras", True) and pr.cfg.get("elementos"):   # no tapar caras, cabezas, globos ni texto
            v.usar_mapa(pr.tmp / "solo_video.mp4", SUB.get("evitar_texto", True))
        elementos = v.elementos()
        if SUB.get("evitar_caras", True) and pr.cfg.get("elementos"):    # el registro se escribe siempre, aunque nada se haya movido
            rep = [f"{a:7.1f} s  {tipo:7s} {p0} -> {p1}  (tapaba {c0}, ahora {c1})" for a, tipo, p0, p1, c0, c1 in v.movidos]
            rep.insert(0, f"# version: {pr.base_nombre} · segundo · tipo · de -> a · (castigo antes; 'ahora' = lo que aún tapa de caras o cabezas)")
            (pr.tmp / "capa_viva_lugares.txt").write_text("\n".join(rep) + "\n", encoding="utf-8")
            print(f"capa viva: {len(v.movidos)} elementos corridos para no tapar caras o texto (tmp/capa_viva_lugares.txt)", flush=True)
        dinamicos = v.subtitulos() if SUB.get("estilo") == "vivo" else []
        escribir_ass(pr.tmp / "rotulos.ass", rotulos, [], elementos, v.estilos())
        escribir_ass(pr.tmp / "todo.ass", rotulos, [] if dinamicos else subs, dinamicos + elementos, v.estilos())
        print(f"capa viva: {len(dinamicos)} eventos de subtítulo, {len(elementos)} de elementos "
              f"(preset {SUB.get('preset', 'finanzas')})", flush=True)
    else:
        escribir_ass(pr.tmp / "rotulos.ass", rotulos, [])
        escribir_ass(pr.tmp / "todo.ass", rotulos, subs)
    srt = "".join(f"{i}\n{ts(a, False)} --> {ts(b, False)}\n{t}\n\n" for i, (a, b, t) in enumerate(subs, 1))
    (pr.salida / f"{pr.base_nombre}_subtitulos.srt").write_text(srt, encoding="utf-8")
    if pr["capitulos"]:
        caps = [(0.0 if i == 0 else buscar(pals, c["frase"]), c["titulo"]) for i, c in enumerate(pr["capitulos"])]
        txt = "\n".join(f"{int(t // 60)}:{int(t % 60):02d} {titulo}" for t, titulo in caps)
        (pr.salida / f"{pr.base_nombre}_capitulos.txt").write_text(txt + "\n", encoding="utf-8")
        print(txt, flush=True)
    print(f"{len(subs)} subtitulos, {len(rotulos)} rotulos", flush=True)
    for t0, _, chico, grande, _ in rotulos:
        print(f"  rotulo {mmss(t0)}  {chico}: {grande}")


def revisar_clips(video):
    m, pend = clips_pendientes(pr, video)
    if m is None:
        print(f"AVISO: {video} no tiene registro de clips (se armó con un motor anterior); no se puede comprobar.")
        return
    if pend and "--forzar" not in sys.argv:
        sys.exit("ALTO: hay clips de Flow en la carpeta que NO están en el video armado:\n" +
                 "\n".join(f"   escena {n}: {a} ({e})" for n, a, e in pend) +
                 "\nVuelve a correr armar.py (y sube la versión en proyecto.json). Para seguir igual: --forzar")


def main():
    if not (ARG("--muestras") or ARG("--borrador") or "--solo-audio" in sys.argv or "--rehacer" in sys.argv):
        ya = [n for n in (f"{pr.base_nombre}_youtube.mp4", f"{pr.base_nombre}_con-subtitulos.mp4") if (pr.salida / n).exists()]
        if ya:          # se revisa antes de escribir nada (srt, capítulos, registro de la capa viva)
            sys.exit(f"Ya existe {', '.join(ya)}: sube \"version\" en proyecto.json para una versión nueva, "
                     f"o agrega --rehacer (la entrega anterior queda guardada como *_anterior-<fecha>.mp4)")
    if not ARG("--muestras"):
        revisar_clips(f"solo_video_borrador_{int(float(ARG('--borrador')))}s.mp4" if ARG("--borrador") else "solo_video.mp4")
    preparar()
    dur = pr.duracion()
    solo = "tmp/solo_video.mp4"
    if ARG("--muestras"):
        for t in [float(x) for x in ARG("--muestras").split(",")]:
            run([FFMPEG, "-v", "error", "-y", "-copyts", "-ss", t, "-i", solo, "-vf", "ass=tmp/todo.ass",
                 "-frames:v", "1", "-q:v", "3", f"tmp/muestra_{int(t)}s.jpg"], cwd=pr.salida)
        print("MUESTRAS en", pr.tmp, flush=True)
        return
    audio(dur)
    if ARG("--borrador"):
        n = int(float(ARG("--borrador")))
        nombre = f"{pr.base_nombre}_borrador-{n}s.mp4"
        run([FFMPEG, "-v", "error", "-y", "-i", f"tmp/solo_video_borrador_{n}s.mp4", "-i", "tmp/narracion.m4a",
             "-map", "0:v", "-map", "1:a", "-vf",
             (lambda l: (l + "," if l else "") + "ass=tmp/todo.ass,fade=t=in:d=0.5")(__import__("efectos").cadena(pr.cfg.get("efectos_video"))),
             *ENCODE, "-c:a", "aac",
             "-shortest", "-movflags", "+faststart", nombre], cwd=pr.salida)
        print("LISTO", pr.salida / nombre, flush=True)
        return
    finales = ((f"{pr.base_nombre}_youtube.mp4", "tmp/rotulos.ass"),                # sin subtitulos (el .srt se sube aparte)
               (f"{pr.base_nombre}_con-subtitulos.mp4", "tmp/todo.ass"))
    if "--solo-audio" in sys.argv:
        for nombre, _ in finales:
            parcial = nombre.replace(".mp4", ".parcial.mp4")
            run([FFMPEG, "-v", "error", "-y", "-i", nombre, "-i", "tmp/narracion.m4a", "-map", "0:v", "-map", "1:a",
                 "-c", "copy", "-movflags", "+faststart", parcial], cwd=pr.salida)
            guardada = apartar_anterior(pr.salida / nombre)
            if guardada:
                print("la entrega anterior quedó como", guardada.name, flush=True)
            (pr.salida / parcial).rename(pr.salida / nombre)
            print("audio cambiado:", nombre, flush=True)
        return
    fades = f"fade=t=in:d=0.5,fade=t=out:st={dur - 1.2:.3f}:d=1.2"
    import efectos as _fx
    look = _fx.cadena(pr.cfg.get("efectos_video"))          # grano, viñeta, antiguo, vhs... debajo de los textos
    if look:
        print(f"efectos de imagen: {', '.join(pr.cfg['efectos_video'])}", flush=True)
    for nombre, ass in finales:
        parcial = nombre.replace(".mp4", ".parcial.mp4")
        run([FFMPEG, "-v", "error", "-y", "-i", solo, "-i", "tmp/narracion.m4a", "-map", "0:v", "-map", "1:a",
             "-vf", f"{look + ',' if look else ''}ass={ass},{fades}", *ENCODE, "-c:a", "copy", "-shortest", "-movflags", "+faststart", parcial], cwd=pr.salida)
        guardada = apartar_anterior(pr.salida / nombre)
        if guardada:
            print("la entrega anterior quedó como", guardada.name, flush=True)
        (pr.salida / parcial).rename(pr.salida / nombre)
        print("listo:", pr.salida / nombre, flush=True)
    print("LISTO", flush=True)


if __name__ == "__main__":
    main()
