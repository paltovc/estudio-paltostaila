# Copia liviana para mirar en el celular (720p, poco peso) y, si se pide, con la zona segura marcada en rojo.
# Si existe Google Drive para escritorio (G:\Mi unidad), también la deja en Mi unidad\EstudioPaltostaila\celu\<ID>
# para abrirla desde la app de Drive del teléfono. Nunca toca el video original.
#   python celu.py "<proyecto>"                    los finales más recientes de 07_RENDER
#   python celu.py "<proyecto>" archivo.mp4 [...]  archivos puntuales (de 07_RENDER o rutas completas)
#   python celu.py "<proyecto>" --zona             marca la zona de botones de TikTok/Reels/Shorts (solo para revisar)
import os, shutil, sys
from pathlib import Path
from estudio import Proyecto, FFMPEG, FFPROBE, run

pr = Proyecto()


def dims(f):
    w, h = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", f]).strip().split(",")[:2]
    return int(w), int(h)


def drive():
    for raiz in (os.environ.get("ESTUDIO_DRIVE", ""), r"G:\Mi unidad", r"G:\My Drive"):
        if raiz and Path(raiz).exists():
            return Path(raiz) / "EstudioPaltostaila" / "celu" / pr.id
    return None


def main():
    pedidos = [a for a in sys.argv[2:] if not a.startswith("--")]
    if pedidos:
        archivos = [Path(a) if Path(a).is_absolute() else pr.salida / a for a in pedidos]
    else:
        claves = ("_youtube", "_con-subtitulos", "_9x16", "_vertical", "_borrador", "vivo-prueba")
        archivos = [f for f in sorted(pr.salida.glob("*.mp4"), key=lambda x: -x.stat().st_mtime)
                    if any(k in f.name for k in claves) and ".parcial" not in f.name][:6]
    if not archivos:
        sys.exit("No hay videos en 07_RENDER todavía.")
    destino = pr.salida / "celu"
    destino.mkdir(exist_ok=True)
    nube = drive()
    for f in archivos:
        w, h = dims(f)
        vertical = h > w
        vf = "scale=720:-2" if vertical else "scale=-2:720"
        if "--zona" in sys.argv and vertical:
            vf += (",drawbox=x=0:y=0:w=iw:h=ih*0.12:color=red@0.35:t=fill,drawbox=x=0:y=ih*0.80:w=iw:h=ih*0.20:color=red@0.35:t=fill,"
                   "drawbox=x=iw*0.86:y=ih*0.38:w=iw*0.14:h=ih*0.42:color=red@0.35:t=fill")
        nombre = f"{f.stem}_celu{'-zona' if '--zona' in sys.argv and vertical else ''}.mp4"
        run([FFMPEG, "-v", "error", "-y", "-i", f, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", destino / nombre])
        mb = (destino / nombre).stat().st_size / 1e6
        linea = f"listo: {destino / nombre} ({mb:.1f} MB)"
        if nube:
            nube.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destino / nombre, nube / nombre)
            linea += f"  → también en Drive: {nube / nombre}"
        print(linea, flush=True)


if __name__ == "__main__":
    main()
