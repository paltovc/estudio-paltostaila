# Cortes verticales 9:16 (TikTok, Shorts, Reels) desde el video ya armado.
# En proyecto.json: "vertical": [{"nombre": "Short_Creencia1", "desde": "frase inicial", "hasta": "frase donde termina",
#                                 "chico": "CREENCIA 1", "titulo": "¿Invertir es solo\\Npara ricos?"}]
#   python vertical.py "C:\ruta\video"
from estudio import Proyecto, FFMPEG, run, palabras, buscar, cues, ts

pr = Proyecto()
F = pr["subtitulos"]["fuente"]
CAB = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{F},66,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,8,70,70,1330,1
Style: Titulo,{F},92,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,8,60,60,330,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def corte(segs, pals, v):
    t0 = buscar(pals, v["desde"]) - 0.15
    t1 = buscar(pals, v["hasta"]) - 0.3 if v.get("hasta") else pr.duracion()
    dur = t1 - t0
    if not 15 <= dur <= 180:
        print(f"AVISO {v['nombre']}: dura {dur:.1f} s (lo ideal para vertical es 45-90 s)")
    lineas = [CAB]
    if v.get("titulo"):
        lineas.append(f"Dialogue: 1,{ts(0)},{ts(dur)},Titulo,,0,0,0,,{{\\fs52\\c&H6AD15B&}}{v.get('chico', '')}\\N{{\\fs92\\c&HFFFFFF&}}{v['titulo']}\n")
    for a, b, txt in cues(segs, 60):
        if b > t0 and a < t1:
            lineas.append(f"Dialogue: 0,{ts(max(a - t0, 0))},{ts(min(b, t1) - t0)},Sub,,0,0,0,,{txt}\n")
    ass = f"tmp/vertical_{v['nombre']}.ass"
    (pr.salida / ass).write_text("".join(lineas), encoding="utf-8-sig")
    vf = ("[0:v]split[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=30:2,eq=brightness=-0.18[fondo];"
          "[b]scale=1080:-2[frente];[fondo][frente]overlay=0:(H-h)/2,"
          f"ass={ass},fade=t=in:d=0.3,fade=t=out:st={dur - 0.6:.3f}:d=0.6[v]")
    nombre = f"{v['nombre']}_9x16{('_' + pr['version']) if pr['version'] else ''}.mp4"
    run([FFMPEG, "-v", "error", "-y", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", "tmp/solo_video.mp4",
         "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", "tmp/narracion.m4a", "-filter_complex", vf,
         "-map", "[v]", "-map", "1:a", "-af", f"afade=t=in:d=0.2,afade=t=out:st={dur - 0.6:.3f}:d=0.6",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(pr.fps),
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", nombre], cwd=pr.salida)
    print(f"LISTO {pr.salida / nombre} ({dur:.1f} s)", flush=True)


def main():
    if not pr["vertical"]:
        print("no hay cortes verticales definidos en proyecto.json")
        return
    segs, pals = palabras(pr)
    for v in pr["vertical"]:
        corte(segs, pals, v)


if __name__ == "__main__":
    main()
