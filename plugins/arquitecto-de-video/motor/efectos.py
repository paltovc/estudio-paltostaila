# Efectos de imagen propios (como los "Effects" de CapCut, hechos con filtros de ffmpeg):
#   grano · vineta · blanco_negro · antiguo (sepia + parpadeo + grano) · vhs (colores corridos, líneas, ruido)
#   brillo (resplandor suave, romántico) · desenfoque · sueño (desenfoque + brillo) · contraste · nitidez
#   + congelar cuadro con destello y cámara lenta fluida (inventa los cuadros intermedios).
#
#   python efectos.py aplicar "<entrada.mp4>" "<salida.mp4>" --efectos vhs,grano [--desde 3 --hasta 8]
#        [--congelar 2.5:0.8] [--fluido 0.5]          (--fluido 0.5 = mitad de velocidad, suave)
#   python efectos.py muestra "<imagen o video>"     hoja con cada efecto para elegir
#
# En proyecto.json (videos narrados): "efectos_video": ["grano", "vineta"]  -> terminar.py los pone debajo de los
#   subtítulos (los textos quedan limpios). Ideal para el documental retro: ["antiguo"] o ["vhs"].
# En montaje.json (videos sobre música), por tramo: "efectos": ["brillo"], "congelar": {"en": 1.2, "dura": 0.8},
#   "fluido": true (cámara lenta sin saltos cuando "velocidad" < 1 o hay "rampa"); en la raíz "efectos" para todos.
import subprocess, sys
from pathlib import Path

try:
    from estudio import FFMPEG
except Exception:
    FFMPEG = "ffmpeg"

EFECTOS = {
    "grano": "noise=alls=10:allf=t",
    "vineta": "vignette=angle=PI/4.6",
    "blanco_negro": "hue=s=0,eq=contrast=1.12",
    "contraste": "eq=contrast=1.15:saturation=1.1",
    "nitidez": "unsharp=5:5:0.7",
    "desenfoque": "gblur=sigma=6",
    "antiguo": ("colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,eq=contrast=1.05:"
                "brightness='0.025*sin(t*23)+0.015*sin(t*61)':eval=frame,noise=alls=16:allf=t,vignette=angle=PI/4"),
    "vhs": ("rgbashift=rh=4:bh=-4:rv=1,boxblur=2:1,eq=saturation=1.3:contrast=1.05,noise=alls=14:allf=t,"
            "drawgrid=w=iw:h=4:t=1:c=black@0.22"),
    # la mezcla "screen" se hace en RGB (en YUV corre los colores hacia el morado)
    "brillo": ("format=gbrp,split[fx_a][fx_b];[fx_b]gblur=sigma=22[fx_g];[fx_a][fx_g]blend=all_mode=screen:all_opacity=0.28,"
               "format=yuv420p"),
    "sueno": ("format=gbrp,split[fx_a][fx_b];[fx_b]gblur=sigma=30[fx_g];[fx_a][fx_g]blend=all_mode=screen:all_opacity=0.42,"
              "format=yuv420p,eq=saturation=0.9,vignette=angle=PI/5"),
}
NOMBRES = {"viñeta": "vineta", "sepia": "antiguo", "retro": "antiguo", "bn": "blanco_negro", "glow": "brillo",
           "blur": "desenfoque", "grain": "grano", "dream": "sueno", "sueño": "sueno"}


def cadena(lista):
    """'grano,vineta' o ['vhs'] -> filtro para -vf (vacío si no hay nada). Las etiquetas internas se numeran."""
    if not lista:
        return ""
    if isinstance(lista, str):
        lista = [x.strip() for x in lista.split(",") if x.strip()]
    partes = []
    for i, e in enumerate(lista):
        e = NOMBRES.get(e, e)
        if e not in EFECTOS:
            print(f"AVISO efecto desconocido «{e}»; opciones: {', '.join(EFECTOS)}", flush=True)
            continue
        partes.append(EFECTOS[e].replace("fx_", f"fx{i}_"))
    return ",".join(partes)


def congelar(en, dura, fps, destello=True):
    """Repite el cuadro del segundo 'en' durante 'dura' s (el resto del tramo se corre). Con destello blanco breve."""
    n = max(1, round(dura * fps))
    f = f"loop=loop={n}:size=1:start={round(en * fps)},setpts=N/{fps}/TB"
    if destello:
        f += f",eq=brightness='if(between(t,{en:.3f},{en + 0.18:.3f}),0.45*(1-(t-{en:.3f})/0.18),0)':eval=frame"
    return f


def fluido(fps):
    """Cámara lenta suave: inventa cuadros intermedios por movimiento (lento de calcular; usar en tramos cortos)."""
    return f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"


def aplicar(entrada, salida, efectos=None, desde=None, hasta=None, cong=None, lento=None, fps=30):
    fx = cadena(efectos)
    pasos = []
    if lento:
        pasos += [f"setpts=PTS/{lento}", fluido(fps)]
    if cong:
        en, dura = (float(x) for x in str(cong).split(":"))
        pasos.append(congelar(en, dura, fps))
    if fx and desde is not None:            # efecto solo en un tramo: se arma con dos ramas y se une
        hasta = hasta if hasta is not None else 1e9
        base = ",".join(pasos) or "null"
        vf = (f"{base},split[fx_o][fx_c];[fx_c]{fx}[fx_e];[fx_o][fx_e]overlay=enable='between(t,{desde},{hasta})'")
    else:
        vf = ",".join(p for p in pasos + [fx] if p) or "null"
    cmd = [FFMPEG, "-v", "error", "-y", "-i", entrada, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
           "-pix_fmt", "yuv420p"]
    cmd += ["-an"] if lento or cong else ["-c:a", "copy"]       # el audio no calzaría con la imagen estirada
    r = subprocess.run([str(c) for c in cmd + [salida]], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit("ffmpeg falló:\n" + r.stderr[-1200:])
    return salida


def muestra(entrada, salida=None):
    from estudio import destino
    salida = str(destino(salida or Path(entrada).with_name(Path(entrada).stem + "_efectos.jpg"), entrada))
    nombres = list(EFECTOS)
    es_img = Path(entrada).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ent = (["-loop", "1", "-t", "1"] if es_img else ["-ss", "1"]) + ["-i", entrada]
    ramas = ";".join(f"[s{i}]{EFECTOS[n].replace('fx_', f'fx{i}_')},scale=480:270,setsar=1,"
                     f"drawtext=text='{n}':x=10:y=10:fontsize=26:fontcolor=white:borderw=2[o{i}]" for i, n in enumerate(nombres))
    k = len(nombres)
    fc = (f"[0]scale=960:540,setsar=1,split={k}" + "".join(f"[s{i}]" for i in range(k)) + ";" + ramas + ";" +
          "".join(f"[o{i}]" for i in range(k)) + f"xstack=inputs={k}:grid=5x2[v]")
    r = subprocess.run([str(FFMPEG), "-v", "error", "-y", *ent, "-filter_complex", fc, "-map", "[v]", "-frames:v", "1", salida],
                       capture_output=True, text=True)
    if r.returncode:   # sin fuente para drawtext: sin nombres
        fc = (f"[0]scale=960:540,setsar=1,split={k}" + "".join(f"[s{i}]" for i in range(k)) + ";" +
              ";".join(f"[s{i}]{EFECTOS[n].replace('fx_', f'fx{i}_')},scale=480:270,setsar=1[o{i}]" for i, n in enumerate(nombres))
              + ";" + "".join(f"[o{i}]" for i in range(k)) + f"xstack=inputs={k}:grid=5x2[v]")
        subprocess.run([str(FFMPEG), "-v", "error", "-y", *ent, "-filter_complex", fc, "-map", "[v]", "-frames:v", "1", salida], check=True)
        print("orden (izq→der, arriba→abajo):", ", ".join(nombres))
    return salida


def main():
    a = sys.argv[1:]
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a:
        sys.exit("Uso: ver el encabezado de efectos.py. Efectos: " + ", ".join(EFECTOS))
    if a[0] == "muestra":
        print("LISTO", muestra(a[1], op("--salida")))
    elif a[0] == "aplicar":
        aplicar(a[1], a[2], op("--efectos"), float(op("--desde")) if op("--desde") else None,
                float(op("--hasta")) if op("--hasta") else None, op("--congelar"), float(op("--fluido")) if op("--fluido") else None,
                int(op("--fps", 30)))
        print("LISTO", a[2])


if __name__ == "__main__":
    main()
