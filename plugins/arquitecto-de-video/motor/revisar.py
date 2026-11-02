# Control de calidad de los archivos finales: duraciones, volumen, fotogramas negros,
# hoja de contacto y fotogramas en los momentos con mas texto. Deja todo en 07_RENDER/revision.
#   python revisar.py "C:\ruta\video"
import re
from estudio import Proyecto, FFMPEG, FFPROBE, run, palabras, cues, buscar, mmss

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


def main():
    dur = pr.duracion()
    lineas = [f"Revision de {pr.base_nombre} - voz: {mmss(dur)} ({dur:.2f} s)\n"]
    finales = [f for f in sorted(pr.salida.glob(f"{pr.base_nombre}_*.mp4")) + sorted(pr.salida.glob("*_9x16*.mp4"))
               if ".parcial" not in f.name]
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
    principal = next((f for f in finales if f.name.endswith("_con_subtitulos.mp4")), finales[0] if finales else None)
    if principal:
        run([FFMPEG, "-v", "error", "-y", "-i", principal, "-vf", "fps=1/5,scale=480:-1,tile=4x3", "-q:v", "4",
             REV / "hoja_%02d.jpg"])
        segs, pals = palabras(pr)
        largos = sorted(cues(segs, pr["subtitulos"]["max_caracteres"]), key=lambda c: -len(c[2]))[:4]
        momentos = [(c[0] + 0.3, "subtitulo largo") for c in largos]
        for r in pr["rotulos"]:
            momentos.append((buscar(pals, r["frase"]) + 1.0, "rotulo " + r["chico"]))
        for t, motivo in sorted(momentos):
            nombre = f"fotograma_{int(t // 60)}m{int(t % 60):02d}s.jpg"
            run([FFMPEG, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", principal, "-frames:v", "1", "-q:v", "3", REV / nombre])
            lineas.append(f"   {nombre}: {motivo}")
    lineas.append(f"\n{len(finales)} archivos revisados, {problemas} puntos a revisar."
                  "\nFalta siempre: escuchar el video completo (voz, efectos y el audio que trae cada clip de Flow).")
    (REV / "informe.txt").write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas))
    print("\nhojas y fotogramas en", REV)


if __name__ == "__main__":
    main()
