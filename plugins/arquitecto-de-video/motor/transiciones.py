# Biblioteca de transiciones (aprendidas de las que ofrece CapCut, hechas con ffmpeg y código propio).
# Se usan en armar.py entre escenas, sin descalzar la voz (cada escena deja medio tramo de margen a cada lado).
#
# En proyecto.json:
#   "transiciones": {"normal": ["mezcla", 12], "capitulo": ["barrido_izq", 18], "plano": ["mezcla", 6],
#                    "variar": ["mezcla", "empujar", "deslizar_izq", "desenfoque"],     (opcional: rota entre escenas normales)
#                    "por_escena": {"7": ["giro", 14], "15": ["destello", 8]}}       (opcional: una escena puntual)
#   El número es la duración en cuadros (12 = 0,4 s a 30 fps). Nombres en español o el nombre parecido de CapCut.
#
#   python transiciones.py --lista                 todas las transiciones con su nombre en CapCut
#   python transiciones.py --catalogo [carpeta]    un video con cada transición rotulada, para elegir mirando
import subprocess, sys
from pathlib import Path
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

# nombre -> (equivalente de ffmpeg xfade o "propia:<efecto>", nombre parecido en CapCut, descripción)
CATALOGO = {
    "mezcla": ("fade", "Mix", "fundido suave de una imagen a la otra"),
    "disolver": ("dissolve", "Dissolve", "se disuelve en puntos"),
    "negro": ("fadeblack", "Black fade", "pasa por negro"),
    "destello": ("fadewhite", "Flash / White", "destello blanco"),
    "grises": ("fadegrays", "Fade gray", "pasa por blanco y negro"),
    "rapido": ("fadefast", "Mix (rápido)", "fundido rápido"),
    "lento": ("fadeslow", "Mix (lento)", "fundido lento"),
    "cortina_izq": ("wipeleft", "Wipe left", "cortina hacia la izquierda"),
    "cortina_der": ("wiperight", "Wipe right", "cortina hacia la derecha"),
    "cortina_arriba": ("wipeup", "Wipe up", "cortina hacia arriba"),
    "cortina_abajo": ("wipedown", "Wipe down", "cortina hacia abajo"),
    "deslizar_izq": ("slideleft", "Slide left", "la imagen nueva empuja a la anterior hacia la izquierda"),
    "deslizar_der": ("slideright", "Slide right", "empuja hacia la derecha"),
    "deslizar_arriba": ("slideup", "Slide up", "empuja hacia arriba"),
    "deslizar_abajo": ("slidedown", "Slide down", "empuja hacia abajo"),
    "suave_izq": ("smoothleft", "Smooth left", "cortina con borde difuminado a la izquierda"),
    "suave_der": ("smoothright", "Smooth right", "borde difuminado a la derecha"),
    "suave_arriba": ("smoothup", "Smooth up", "borde difuminado hacia arriba"),
    "suave_abajo": ("smoothdown", "Smooth down", "borde difuminado hacia abajo"),
    "cubrir_izq": ("coverleft", "Cover left", "la nueva entra encima desde la derecha"),
    "cubrir_der": ("coverright", "Cover right", "entra encima desde la izquierda"),
    "cubrir_arriba": ("coverup", "Cover up", "entra encima desde abajo"),
    "cubrir_abajo": ("coverdown", "Cover down", "entra encima desde arriba"),
    "revelar_izq": ("revealleft", "Reveal left", "la anterior se va y descubre la nueva"),
    "revelar_der": ("revealright", "Reveal right", "se va hacia la derecha"),
    "revelar_arriba": ("revealup", "Reveal up", "se va hacia arriba"),
    "revelar_abajo": ("revealdown", "Reveal down", "se va hacia abajo"),
    "circulo_abrir": ("circleopen", "Circle open", "círculo que se abre"),
    "circulo_cerrar": ("circleclose", "Circle close", "círculo que se cierra"),
    "circulo": ("circlecrop", "Circle", "se cierra en círculo y se abre la nueva"),
    "rectangulo": ("rectcrop", "Rectangle", "se cierra en rectángulo"),
    "abrir_vertical": ("vertopen", "Split open", "se abre al medio como puertas"),
    "cerrar_vertical": ("vertclose", "Split close", "se cierra al medio"),
    "abrir_horizontal": ("horzopen", "Split horizontal", "se abre de arriba y abajo"),
    "cerrar_horizontal": ("horzclose", "Split horizontal close", "se cierra de arriba y abajo"),
    "reloj": ("radial", "Clock wipe", "barrido como aguja de reloj"),
    "pixelar": ("pixelize", "Pixelate", "se pixela y aparece la nueva"),
    "diagonal_arriba_izq": ("diagtl", "Diagonal", "diagonal desde arriba a la izquierda"),
    "diagonal_arriba_der": ("diagtr", "Diagonal", "diagonal desde arriba a la derecha"),
    "diagonal_abajo_izq": ("diagbl", "Diagonal", "diagonal desde abajo a la izquierda"),
    "diagonal_abajo_der": ("diagbr", "Diagonal", "diagonal desde abajo a la derecha"),
    "esquina_arriba_izq": ("wipetl", "Corner wipe", "cortina desde la esquina"),
    "esquina_arriba_der": ("wipetr", "Corner wipe", "cortina desde la esquina"),
    "esquina_abajo_izq": ("wipebl", "Corner wipe", "cortina desde la esquina"),
    "esquina_abajo_der": ("wipebr", "Corner wipe", "cortina desde la esquina"),
    "persiana_izq": ("hlslice", "Blinds", "franjas verticales hacia la izquierda"),
    "persiana_der": ("hrslice", "Blinds", "franjas hacia la derecha"),
    "persiana_arriba": ("vuslice", "Blinds", "franjas horizontales hacia arriba"),
    "persiana_abajo": ("vdslice", "Blinds", "franjas hacia abajo"),
    "viento_izq": ("hlwind", "Wind", "se lleva la imagen como viento hacia la izquierda"),
    "viento_der": ("hrwind", "Wind", "viento hacia la derecha"),
    "viento_arriba": ("vuwind", "Wind", "viento hacia arriba"),
    "viento_abajo": ("vdwind", "Wind", "viento hacia abajo"),
    "apretar_horizontal": ("squeezeh", "Squeeze", "se aprieta hacia los lados"),
    "apretar_vertical": ("squeezev", "Squeeze", "se aprieta hacia arriba y abajo"),
    "distancia": ("distance", "Distort", "se deforma hacia la nueva"),
    "zoom": ("zoomin", "Zoom in", "acerca la anterior y aparece la nueva"),
    "desenfoque_horizontal": ("hblur", "Blur (horizontal)", "desenfoque de movimiento horizontal"),
    # propias (no vienen en ffmpeg): hechas con varios filtros
    "empujar": ("propia:empujar", "Pull in", "la cámara se mete hacia adelante y sale en la nueva"),
    "alejar": ("propia:alejar", "Zoom out", "la cámara se aleja de la anterior y llega a la nueva"),
    "golpe": ("propia:golpe", "Zoom punch / Pop", "golpe de zoom rápido, ideal en el pulso de la música"),
    "giro": ("propia:giro", "Spin / Rotate", "la imagen gira y aparece la nueva girando"),
    "barrido_izq": ("propia:barrido_izq", "Whip / Swipe left", "barrido rápido con desenfoque de movimiento"),
    "barrido_der": ("propia:barrido_der", "Whip / Swipe right", "barrido rápido hacia la derecha"),
    "desenfoque": ("propia:desenfoque", "Blur", "se desenfoca, cambia y se vuelve a enfocar"),
    "sacudida": ("propia:sacudida", "Shake", "sacudón de cámara en el cambio"),
    "glitch": ("propia:glitch", "Glitch", "falla digital: colores corridos y ruido"),
    "fuga_de_luz": ("propia:fuga_de_luz", "Light leak / Flash warm", "destello cálido como luz que se cuela"),
}
ALIAS = {"fade": "mezcla", "mix": "mezcla", "flash": "destello", "black": "negro", "blur": "desenfoque", "spin": "giro",
         "rotate": "giro", "whip": "barrido_izq", "swipe": "barrido_izq", "shake": "sacudida", "pull": "empujar",
         "pull in": "empujar", "zoom out": "alejar", "zoom in": "zoom", "pop": "golpe", "light leak": "fuga_de_luz",
         "pixelate": "pixelar", "clock": "reloj", "wind": "viento_izq", "squeeze": "apretar_horizontal"}
XFADE = {v[0] for v in CATALOGO.values() if not v[0].startswith("propia:")}


def resolver(nombre):
    """Nombre del estudio, de CapCut o de ffmpeg -> clave del catálogo."""
    n = str(nombre).strip().lower()
    if n in CATALOGO:
        return n
    if n in ALIAS:
        return ALIAS[n]
    for k, v in CATALOGO.items():
        if v[0] == n:
            return k
    print(f"AVISO transición desconocida «{nombre}»: se usa mezcla", flush=True)
    return "mezcla"


def cadena(nombre, d, fps, W, H, p="p", q="q", sal="v"):
    """Filtro que une [p] (los últimos d cuadros de la escena anterior) y [q] (los primeros d de la siguiente)."""
    k = resolver(nombre)
    tipo = CATALOGO[k][0]
    dur = f"{d / fps:.4f}"
    if not tipo.startswith("propia:"):
        return f"[{p}][{q}]xfade=transition={tipo}:duration={dur}:offset=0,format=yuv420p[{sal}]"
    efecto = tipo.split(":", 1)[1]
    D = max(d - 1, 1)
    zp = lambda z: f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={fps}"
    if efecto in ("empujar", "alejar"):
        # empujar: la cámara entra en la anterior (1 -> 1,6) y sale de la nueva (1,6 -> 1)
        # alejar: la nueva aparece desde muy cerca y la cámara se aleja hasta su encuadre (1,5 -> 1)
        a, b = (f"1+0.6*on/{D}", f"1.6-0.6*on/{D}") if efecto == "empujar" else ("1", f"1.5-0.5*on/{D}")
        return (f"[{p}]{zp(a)}[pz];[{q}]{zp(b)}[qz];"
                f"[pz][qz]xfade=transition=fade:duration={dur}:offset=0,format=yuv420p[{sal}]")
    if efecto == "golpe":
        return (f"[{p}]{zp(f'1+0.35*on/{D}')}[pz];[{q}]{zp(f'1.35-0.35*on/{D}')}[qz];"
                f"[pz][qz]xfade=transition=fadefast:duration={dur}:offset=0,format=yuv420p[{sal}]")
    if efecto == "giro":
        return (f"[{p}]scale=iw*1.6:-2,rotate=a='PI*0.5*n/{D}':ow={W}:oh={H}:c=black[pr];"
                f"[{q}]scale=iw*1.6:-2,rotate=a='-PI*0.5*(1-n/{D})':ow={W}:oh={H}:c=black[qr];"
                f"[pr][qr]xfade=transition=fade:duration={dur}:offset=0,format=yuv420p[{sal}]")
    if efecto in ("barrido_izq", "barrido_der"):
        lado = "slideleft" if efecto == "barrido_izq" else "slideright"
        return (f"[{p}][{q}]xfade=transition={lado}:duration={dur}:offset=0,tmix=frames=5,format=yuv420p[{sal}]")
    if efecto == "desenfoque":
        return (f"[{p}]split[p0][p1];[p1]gblur=sigma=28[pb];[p0][pb]xfade=transition=fade:duration={dur}:offset=0[pp];"
                f"[{q}]split[q0][q1];[q1]gblur=sigma=28[qb];[qb][q0]xfade=transition=fade:duration={dur}:offset=0[qq];"
                f"[pp][qq]xfade=transition=fade:duration={dur}:offset=0,format=yuv420p[{sal}]")
    if efecto == "sacudida":
        return (f"[{p}][{q}]xfade=transition=fadefast:duration={dur}:offset=0,"
                f"crop=iw*0.9:ih*0.9:x='(iw-ow)/2+iw*0.04*sin(n*2.7)*(1-abs(n-{D}/2)/({D}/2+1))':"
                f"y='(ih-oh)/2+ih*0.04*cos(n*3.1)*(1-abs(n-{D}/2)/({D}/2+1))',scale={W}:{H},setsar=1,format=yuv420p[{sal}]")
    if efecto == "glitch":
        return (f"[{p}][{q}]xfade=transition=pixelize:duration={dur}:offset=0,"
                f"rgbashift=rh=16:bh=-16:gv=6,noise=alls=30:allf=t,format=yuv420p[{sal}]")
    if efecto == "fuga_de_luz":
        return (f"[{p}][{q}]xfade=transition=fadewhite:duration={dur}:offset=0,"
                f"colorbalance=rs=0.35:gs=0.12:bs=-0.25:rm=0.2:bm=-0.15,format=yuv420p[{sal}]")
    return f"[{p}][{q}]xfade=transition=fade:duration={dur}:offset=0,format=yuv420p[{sal}]"


def catalogo(carpeta, ffmpeg="ffmpeg", W=1280, H=720, fps=30, d=18):
    """Video con cada transición entre dos cartas de color, con su nombre y el de CapCut."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    piezas = []
    colores = [("0x1D3557", "0xE76F51"), ("0x2A9D8F", "0x264653"), ("0x6D597A", "0xE9C46A")]
    for i, (k, (tipo, capcut, desc)) in enumerate(CATALOGO.items()):
        c1, c2 = colores[i % len(colores)]
        out = carpeta / f"_t{i:03d}.mp4"
        txt = f"{k}  ·  CapCut: {capcut}".replace(":", "\\:").replace("'", "")
        carta = lambda c, letra: (f"color=c={c}:s={W}x{H}:r={fps}:d={(d + 24) / fps:.3f},"
                                  f"drawgrid=w=80:h=80:t=2:c=white@0.12,"
                                  f"drawbox=x={W // 2 - 120}:y={H // 2 - 120}:w=240:h=240:color=white@0.85:t=fill")
        fc = (f"{carta(c1, 'A')}[a];{carta(c2, 'B')}[b];[a]trim=start_frame=12,setpts=PTS-STARTPTS[a2];"
              f"[b]trim=end_frame={d + 12},setpts=PTS-STARTPTS[b2];[a2]trim=end_frame={d},setpts=PTS-STARTPTS[p];"
              f"[b2]trim=end_frame={d},setpts=PTS-STARTPTS[q];" + cadena(k, d, fps, W, H, "p", "q", "t") +
              f";[t]drawtext=text='{txt}':fontcolor=white:fontsize=34:x=(w-tw)/2:y=h-70:box=1:boxcolor=black@0.6:boxborderw=12[v]")
        r = subprocess.run([ffmpeg, "-v", "error", "-y", "-filter_complex", fc, "-map", "[v]", "-frames:v", str(d),
                            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", *SIN_METADATOS, str(out)], capture_output=True, text=True)
        if r.returncode:     # sin fontconfig (drawtext): igual se genera, sin el rótulo
            fc = fc.rsplit(";[t]drawtext", 1)[0].replace("[t]", "[v]")
            r = subprocess.run([ffmpeg, "-v", "error", "-y", "-filter_complex", fc, "-map", "[v]", "-frames:v", str(d),
                                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", *SIN_METADATOS, str(out)], capture_output=True, text=True)
        if r.returncode:
            print(f"  FALLÓ {k}: {r.stderr[-200:]}", flush=True)
            continue
        piezas.append(out)
        print(f"  {k}", flush=True)
    (carpeta / "_lista.txt").write_text("".join(f"file '{x.name}'\n" for x in piezas), encoding="utf-8")
    final = carpeta / "catalogo_transiciones.mp4"
    subprocess.run([ffmpeg, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(carpeta / "_lista.txt"), "-c", "copy", *SIN_METADATOS, str(final)])
    for x in piezas:
        x.unlink(missing_ok=True)
    (carpeta / "_lista.txt").unlink(missing_ok=True)
    lineas = [f"{i + 1:02d}. {k} (CapCut: {v[1]}) — {v[2]}" for i, (k, v) in enumerate(CATALOGO.items())]
    (carpeta / "catalogo_transiciones.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"LISTO {final} ({len(piezas)} transiciones, {len(piezas) * d / fps:.0f} s)", flush=True)


if __name__ == "__main__":
    if "--lista" in sys.argv:
        for i, (k, v) in enumerate(CATALOGO.items(), 1):
            print(f"{i:02d}. {k:22s} CapCut: {v[1]:24s} {v[2]}")
    elif "--catalogo" in sys.argv:
        try:
            from estudio import FFMPEG
        except Exception:
            FFMPEG = "ffmpeg"
        i = sys.argv.index("--catalogo")
        destino = sys.argv[i + 1] if len(sys.argv) > i + 1 else str(Path.home() / "EstudioPaltostaila" / "recursos" / "transiciones")
        catalogo(destino, FFMPEG)
    else:
        print(__doc__ or "uso: python transiciones.py --lista | --catalogo [carpeta]")
