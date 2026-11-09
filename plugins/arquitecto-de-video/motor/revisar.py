# Control de calidad de los archivos finales: duraciones, volumen, fotogramas negros,
# hoja de contacto y fotogramas en los momentos con mas texto. Deja todo en 07_RENDER/revision.
#   python revisar.py "C:\ruta\video"
import re
import tempfile
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
from estudio import Proyecto, FFMPEG, FFPROBE, run, palabras, cues, buscar, mmss, clips_pendientes, manifiesto
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

pr = Proyecto()
REV = pr.salida / "revision"
REV.mkdir(exist_ok=True)


def info(p):
    s = run([FFPROBE, "-v", "error", "-show_entries", "stream=codec_type,width,height,duration", "-of", "csv=p=0", p])
    return [x.split(",") for x in s.strip().splitlines()]


def lufs(p):
    s = run([FFMPEG, "-hide_banner", "-i", p, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", s)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", s)
    return float(i[-1]) if i else None, float(tp[-1]) if tp else None


def negros(p):
    s = run([FFMPEG, "-hide_banner", "-i", p, "-vf", "blackdetect=d=0.1:pix_th=0.06", "-an", "-f", "null", "-"])
    return re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", s)


def huella(video, t, tmp, nombre):
    out = Path(tmp) / f"{nombre}.png"
    run([FFMPEG, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-vf",
         f"scale={pr.ancho}:{pr.alto}:force_original_aspect_ratio=increase,crop={pr.ancho}:{pr.alto}", *SIN_METADATOS, out])
    return Image.open(out).convert("L").resize((64, 36))


def revisar_clips(principal, lineas):
    """Comprueba que cada clip de Flow este de verdad dentro del video final, en su escena."""
    from estudio import clips_disponibles
    m, pend = clips_pendientes(pr)
    problemas = 0
    lineas.append("\nClips de Flow:")
    if m is None:   # video armado con un motor anterior: se comprueban los clips que hay en la carpeta
        lineas.append("   (sin registro del armado: se comparan los clips de la carpeta con el video)")
        esc = {r["n"]: r for r in pr.escenas()}
        m = {"clips": {k: {"archivo": p.name, "inicio_s": esc[int(k.split("_")[0])]["t0"],
                           "dura_s": esc[int(k.split("_")[0])]["t1"] - esc[int(k.split("_")[0])]["t0"]}
                       for k, p in clips_disponibles(pr).items() if "_p" not in k}}
        pend = []
    for n, a, e in pend:
        lineas.append(f"   REVISAR escena {n}: {a} está en la carpeta pero no en el video armado ({e}) -> volver a armar")
        problemas += 1
    usados = (m or {}).get("clips", {})
    with tempfile.TemporaryDirectory() as tmp:
        for k, u in sorted(usados.items(), key=lambda x: (int(x[0].split("_")[0]), x[0])):
            n = int(k.split("_")[0])
            t0 = u["inicio_s"]
            off = min(2.0, u["dura_s"] / 2)
            a = huella(principal, t0 + off, tmp, f"v{n}")
            b = huella(pr.clips / u["archivo"], off, tmp, f"c{n}")
            c = huella(pr.clips / u["archivo"], 0.05, tmp, f"p{n}")
            d_clip = ImageStat.Stat(ImageChops.difference(a, b)).mean[0]
            d_foto = ImageStat.Stat(ImageChops.difference(a, c)).mean[0]
            ok = d_clip < 15 and d_clip <= d_foto + 1
            problemas += not ok
            lineas.append(f"   {'OK     ' if ok else 'REVISAR'} escena {n:03d} en {mmss(t0)} ({u['dura_s']:.1f} s): {u['archivo']}"
                          f" (parecido {d_clip:.1f}{'' if ok else '; no se ve el movimiento del clip'})")
    plan = [str(x) for x in pr.cfg.get("clips_plan", [])]
    faltan = [n for n in plan if n not in usados and n not in [str(p[0]) for p in pend]]
    etiqueta = lambda k: "escena_" + (f"{int(k):03d}" if k.isdigit() else f"{int(k.split('_')[0]):03d}_{k.split('_')[1]}")
    if faltan:
        lineas.append(f"   aviso: clips del plan que todavía no existen: {', '.join(etiqueta(n) for n in faltan)}")
    return problemas


def main():
    dur = pr.duracion()
    lineas = [f"Revision de {pr.base_nombre} - voz: {mmss(dur)} ({dur:.2f} s)\n"]
    finales = [f for f in sorted(set(pr.salida.glob(f"{pr.base_nombre}_*.mp4")))
               if ".parcial" not in f.name and "_borrador" not in f.name and "_anterior-" not in f.name]
    problemas = 0
    for f in finales:
        st = info(f)
        dv = next((float(x[-1]) for x in st if x[0] == "video" and x[-1] not in ("", "N/A")), 0)
        da = next((float(x[-1]) for x in st if x[0] == "audio" and x[-1] not in ("", "N/A")), 0)
        res = next((f"{x[1]}x{x[2]}" for x in st if x[0] == "video"), "?")
        i, tp = lufs(f)
        ng = negros(f)
        vertical = "_9x16" in f.name
        ok_dur = vertical or abs(dv - dur) < 0.2
        ok_vol = i is not None and abs(i - pr["volumen_lufs"]) <= 2
        ok_neg = all(float(b) < 0.6 or float(a) > dv - 1.5 for a, b in ng)   # se aceptan los fundidos de entrada y salida
        problemas += (not ok_dur) + (not ok_vol) + (not ok_neg)
        lineas.append(f"{f.name}\n   {res}, video {dv:.2f} s, audio {da:.2f} s {'OK' if ok_dur else 'REVISAR DURACION'}"
                      f"\n   volumen {i} LUFS, pico {tp} dBFS {'OK' if ok_vol else 'REVISAR VOLUMEN'}"
                      f"\n   tramos negros: {len(ng)} {'OK' if ok_neg else 'REVISAR: ' + str(ng[:5])}")
    principal = next((f for f in finales if f.name.endswith("_con-subtitulos.mp4")), finales[0] if finales else None)
    if principal:
        run([FFMPEG, "-v", "error", "-y", "-i", principal, "-vf", "fps=1/5,scale=480:-1,tile=4x3", "-q:v", "4", *SIN_METADATOS,
             REV / "hoja_%02d.jpg"])
        segs, pals = palabras(pr)
        largos = sorted(cues(segs, pr["subtitulos"]["max_caracteres"]), key=lambda c: -len(c[2]))[:4]
        momentos = [(c[0] + 0.3, "subtitulo largo") for c in largos]
        for r in pr["rotulos"]:
            momentos.append((buscar(pals, r["frase"]) + 1.0, "rotulo " + r["chico"]))
        for t, motivo in sorted(momentos):
            nombre = f"fotograma_{int(t // 60)}m{int(t % 60):02d}s.jpg"
            run([FFMPEG, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", principal, "-frames:v", "1", "-q:v", "3", *SIN_METADATOS, REV / nombre])
            lineas.append(f"   {nombre}: {motivo}")
    if principal and not "_9x16" in principal.name:
        problemas += revisar_clips(principal, lineas)
    lineas.append(f"\n{len(finales)} archivos revisados, {problemas} puntos a revisar."
                  "\nFalta siempre: escuchar el video completo (voz, efectos y el audio que trae cada clip de Flow).")
    (REV / "informe.txt").write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas))
    print("\nhojas y fotogramas en", REV)


if __name__ == "__main__":
    main()
