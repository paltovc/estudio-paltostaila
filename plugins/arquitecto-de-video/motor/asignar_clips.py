# Reconoce a que escena pertenece cada clip descargado de Flow comparando su primer cuadro con
# las imagenes de la receta, y lo copia como escena_NNN.mp4 (el original no se toca).
#   python asignar_clips.py "C:\ruta\video"
import re, shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
from estudio import Proyecto, FFMPEG
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

pr = Proyecto()
LIMITE = 30.0   # diferencia maxima aceptada (0 = identico); mas alto = no se asigna


def huella(img):
    return img.convert("L").resize((64, 36), Image.BILINEAR)


def primer_cuadro(mp4, tmp):
    out = Path(tmp) / (mp4.stem + ".png")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", "0.05", "-i", str(mp4), "-frames:v", "1", *SIN_METADATOS, str(out)], check=True)
    return huella(Image.open(out))


def main():
    huellas, vistos = {}, set()
    for r in pr.escenas():   # imagenes repetidas en la receta: se asigna a la primera aparicion
        if r["archivo"] not in vistos:
            vistos.add(r["archivo"])
            huellas[f"escena_{r['n']:03d}"] = huella(Image.open(pr.imagenes / r["archivo"]))
    # imagenes de partida que se subieron a Flow (1_escena_001_p2.png ...): mandan sobre las de la receta
    for p in sorted(pr.clips.glob("SUBIR_A_FLOW*/*")):
        m = re.match(r"^\d+_(escena_\d{3}(?:_p\d+)?)\.(png|jpe?g|webp)$", p.name, re.I)
        if m:
            huellas[m.group(1)] = huella(Image.open(p))
    nuevos = [p for p in pr.clips.glob("*.mp4") if not p.name.startswith("escena_")]
    if not nuevos:
        print("no hay clips nuevos en", pr.clips)
    with tempfile.TemporaryDirectory() as tmp:
        for mp4 in sorted(nuevos):
            h = primer_cuadro(mp4, tmp)
            dif = sorted((ImageStat.Stat(ImageChops.difference(h, ref)).mean[0], n) for n, ref in huellas.items())
            (d1, n1), (d2, n2) = dif[0], dif[1] if len(dif) > 1 else (999, "-")
            destino = pr.clips / f"{n1}.mp4"
            if d1 > LIMITE:
                print(f"SIN ASIGNAR  {mp4.name}: lo mas parecido es {n1} (diferencia {d1:.1f})")
            elif destino.exists():
                print(f"YA EXISTE    {destino.name}; no se sobrescribe ({mp4.name})")
            else:
                shutil.copy2(mp4, destino)
                print(f"{n1} <- {mp4.name}  (diferencia {d1:.1f}; siguiente {n2}: {d2:.1f})")


if __name__ == "__main__":
    main()
