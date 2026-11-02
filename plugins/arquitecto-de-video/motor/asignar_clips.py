# Reconoce a que escena pertenece cada clip descargado de Flow comparando su primer cuadro con
# las imagenes de la receta, y lo copia como escena_NNN.mp4 (el original no se toca).
#   python asignar_clips.py "C:\ruta\video"
import shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
from estudio import Proyecto, FFMPEG

pr = Proyecto()
LIMITE = 30.0   # diferencia maxima aceptada (0 = identico); mas alto = no se asigna


def huella(img):
    return img.convert("L").resize((64, 36), Image.BILINEAR)


def primer_cuadro(mp4, tmp):
    out = Path(tmp) / (mp4.stem + ".png")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", "0.05", "-i", str(mp4), "-frames:v", "1", str(out)], check=True)
    return huella(Image.open(out))


def main():
    huellas, vistos = {}, set()
    for r in pr.escenas():   # imagenes repetidas en la receta: se asigna a la primera aparicion
        if r["archivo"] not in vistos:
            vistos.add(r["archivo"])
            huellas[r["n"]] = huella(Image.open(pr.imagenes / r["archivo"]))
    nuevos = [p for p in pr.clips.glob("*.mp4") if not p.name.startswith("escena_")]
    if not nuevos:
        print("no hay clips nuevos en", pr.clips)
    with tempfile.TemporaryDirectory() as tmp:
        for mp4 in sorted(nuevos):
            h = primer_cuadro(mp4, tmp)
            dif = sorted((ImageStat.Stat(ImageChops.difference(h, ref)).mean[0], n) for n, ref in huellas.items())
            (d1, n1), (d2, n2) = dif[0], dif[1] if len(dif) > 1 else (999, 0)
            destino = pr.clips / f"escena_{n1:03d}.mp4"
            if d1 > LIMITE:
                print(f"SIN ASIGNAR  {mp4.name}: lo mas parecido es la escena {n1} (diferencia {d1:.1f})")
            elif destino.exists():
                print(f"YA EXISTE    {destino.name}; no se sobrescribe ({mp4.name})")
            else:
                shutil.copy2(mp4, destino)
                print(f"escena {n1:03d} <- {mp4.name}  (diferencia {d1:.1f}; siguiente {n2}: {d2:.1f})")


if __name__ == "__main__":
    main()
