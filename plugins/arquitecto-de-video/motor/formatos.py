# Un video en todos los formatos y portadas animadas (como "Magic Switch / Resize" y "Magic Animate" de Canva, hechos aquí).
#   python formatos.py video "<video.mp4>" [--formatos 1x1,4x5,9x16] [--modo relleno|recorte] [--centro_x 0.5]
#        relleno: el video entero al centro sobre una copia desenfocada (no se pierde nada; ideal para textos y gráficos)
#        recorte: llena la pantalla cortando los lados (--centro_x elige qué parte queda; 0 = izquierda, 1 = derecha)
#        Para 9:16 que siga a la persona, mejor vertical.py con "modo": "seguir".
#        Sale <video>_1x1.mp4, _4x5.mp4 ... al lado del original (nunca lo reemplaza).
#   python formatos.py animar "<plantilla.json o nombre>" --datos "<datos.json>" [--campo titulo=...] [--salida portada.mp4]
#        [--dur 4] [--estilo subir|aparecer|golpe] [--canal finanzas] [--formato 9x16]
#        La portada o miniatura de diseno.py, con cada capa entrando por separado (la de atrás primero), y quieta al final.
#        Sirve para los primeros segundos de un Short o como tarjeta de presentación.
import json, subprocess, sys
from pathlib import Path
from PIL import Image

try:
    from estudio import FFMPEG
except Exception:
    FFMPEG = "ffmpeg"
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

TAM = {"16x9": (1920, 1080), "9x16": (1080, 1920), "1x1": (1080, 1080), "4x5": (1080, 1350)}


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit("ffmpeg falló:\n" + r.stderr[-1200:])


def video(ruta, formatos="1x1,4x5,9x16", modo="relleno", cx=0.5):
    ruta = Path(ruta)
    salidas = []
    for fm in formatos.split(","):
        W, H = TAM[fm]
        if modo == "relleno":
            fc = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,"
                  f"eq=brightness=-0.08[bg];[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
                  f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v]")
        else:
            fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}:(iw-{W})*{cx}:(ih-{H})/2,"
                  f"setsar=1,format=yuv420p[v]")
        from estudio import destino
        sal = destino(ruta.with_name(f"{ruta.stem}_{fm}.mp4"), ruta)
        run([FFMPEG, "-v", "error", "-y", "-i", ruta, "-filter_complex", fc, "-map", "[v]", "-map", "0:a?", "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "18", "-c:a", "copy", *SIN_METADATOS, "-movflags", "+faststart", sal])
        print("listo:", sal, flush=True)
        salidas.append(sal)
    return salidas


def capas_sueltas(plantilla, datos, base, canal):
    """Cada capa de la plantilla dibujada sola sobre transparente (mismo orden que diseno.render)."""
    import re
    import diseno as D
    mk = D.marca(canal or plantilla.get("canal") or datos.get("canal"), datos.get("proyecto"))
    W, H = plantilla.get("tamano", [1280, 720])
    fondo = Image.new("RGBA", (W, H), D.color(plantilla.get("fondo", "fondo"), mk))
    capas = []
    for c in plantilla["capas"]:
        c = {k: (re.sub(r"\{\{(\w+)\}\}", lambda m: str(datos.get(m.group(1), "")), v) if isinstance(v, str) and k != "texto" else v)
             for k, v in c.items()}
        if c.get("si") and not datos.get(c["si"]):
            continue
        lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        {"imagen": lambda: D.capa_imagen(lienzo, c, mk, base), "texto": lambda: D.capa_texto(lienzo, c, mk, datos),
         "forma": lambda: D.capa_forma(lienzo, c, mk), "logo": lambda: D.capa_logo(lienzo, c, mk)}[c["tipo"]]()
        capas.append((c["tipo"], lienzo))
    return fondo, capas


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def animar(plantilla, datos, base, sal, dur=4.0, estilo="subir", canal=None, fps=30):
    fondo, capas = capas_sueltas(plantilla, datos, base, canal)
    W, H = fondo.size
    paso, entra = 0.28, 0.55                      # cada capa empieza 0,28 s después de la anterior y tarda 0,55 s
    proc = subprocess.Popen([str(FFMPEG), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
                             "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", *SIN_METADATOS, str(sal)],
                            stdin=subprocess.PIPE)
    fin = None
    for i in range(round(dur * fps)):
        t = i / fps
        if fin is not None and t > paso * len(capas) + entra:
            proc.stdin.write(fin)
            continue
        cuadro = fondo.copy()
        for k, (tipo, capa) in enumerate(capas):
            p = suave((t - 0.15 - k * paso) / entra)
            if p <= 0:
                continue
            c = capa
            if p < 1:
                alfa = c.split()[3].point(lambda v, p=p: int(v * p))
                c = c.copy()
                c.putalpha(alfa)
                if estilo == "golpe" and tipo == "texto":
                    e = 0.7 + 0.3 * p + 0.08 * (1 - abs(1 - 2 * p))          # crece un poco más y vuelve
                    cw, ch = int(W * e), int(H * e)
                    g = c.resize((cw, ch), Image.LANCZOS)
                    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    c.alpha_composite(g, ((W - cw) // 2, (H - ch) // 2)) if e <= 1 else c.alpha_composite(
                        g.crop(((cw - W) // 2, (ch - H) // 2, (cw - W) // 2 + W, (ch - H) // 2 + H)))
                elif estilo == "subir":
                    d = int(H * 0.06 * (1 - p))
                    c2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    c2.alpha_composite(c.crop((0, 0, W, H - d)), (0, d))
                    c = c2
            cuadro.alpha_composite(c)
        datos_cuadro = cuadro.convert("RGB").tobytes()
        if t > paso * len(capas) + entra:
            fin = datos_cuadro
        proc.stdin.write(datos_cuadro)
    proc.stdin.close()
    if proc.wait():
        raise SystemExit("ffmpeg falló al escribir " + str(sal))
    return sal


def main():
    a = sys.argv[1:]
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a:
        sys.exit("Uso: ver el encabezado de formatos.py")
    if a[0] == "video":
        video(a[1], op("--formatos", "1x1,4x5,9x16"), op("--modo", "relleno"), float(op("--centro_x", 0.5)))
    elif a[0] == "animar":
        import diseno as D
        pl = Path(a[1]) if Path(a[1]).exists() else Path(__file__).with_name("plantillas") / f"{a[1]}.json"
        plantilla = json.loads(pl.read_text(encoding="utf-8-sig"))
        if op("--formato"):
            plantilla = D.escalar_plantilla(plantilla, *D.FORMATOS[op("--formato")])
        datos = json.loads(Path(op("--datos")).read_text(encoding="utf-8-sig")) if op("--datos") else {}
        for x in [a[i + 1] for i, v in enumerate(a) if v == "--campo"]:
            k, v = x.split("=", 1)
            datos[k] = v.replace("\\n", "\n")
        base = Path(op("--base") or (Path(op("--datos")).parent if op("--datos") else Path.cwd()))
        from estudio import destino
        sal = destino(op("--salida") or base / f"{pl.stem}_animada.mp4")
        animar(plantilla, datos, base, sal, float(op("--dur", 4)), op("--estilo", "subir"), op("--canal"))
        print("LISTO", sal)


if __name__ == "__main__":
    main()
