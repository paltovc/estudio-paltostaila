# Paquete para terminar un video a mano en CapCut (la persona lo abre y edita; nada se automatiza dentro de CapCut,
# porque sus términos prohíben usar scripts para interactuar con el servicio).
#   python capcut_paquete.py "<proyecto>"
# Deja en <proyecto>\09_CAPCUT:
#   <ID>_video_limpio.mp4     imagen + voz final, sin subtítulos, rótulos ni elementos (para ponerlos en CapCut)
#   <ID>_solo_imagen.mp4      la imagen sin audio (si se quiere otra mezcla)
#   <ID>_voz.wav              la voz a -14 LUFS
#   <ID>_subtitulos.srt       los subtítulos (CapCut: Subtítulos > Agregar subtítulos > elegir el .srt)
#   <ID>_rotulos.txt          rótulos y capítulos con su minuto, para copiarlos como texto
#   LEEME.txt                 pasos
import shutil
from pathlib import Path
from estudio import Proyecto, FFMPEG, run, palabras, buscar, cues, ts, mmss

pr = Proyecto()


def main():
    solo, narr, voz = pr.tmp / "solo_video.mp4", pr.tmp / "narracion.m4a", pr.tmp / "voz.wav"
    if not solo.exists() or not narr.exists():
        raise SystemExit("Falta tmp/solo_video.mp4 o tmp/narracion.m4a: correr primero armar.py y terminar.py (o grabado.py armar).")
    d = pr.dir / "09_CAPCUT"
    d.mkdir(exist_ok=True)
    run([FFMPEG, "-v", "error", "-y", "-i", solo, "-i", narr, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-shortest", "-movflags", "+faststart", d / f"{pr.id}_video_limpio.mp4"])
    shutil.copy2(solo, d / f"{pr.id}_solo_imagen.mp4")
    if voz.exists():
        shutil.copy2(voz, d / f"{pr.id}_voz.wav")
    srt = pr.salida / f"{pr.base_nombre}_subtitulos.srt"
    if srt.exists():
        shutil.copy2(srt, d / f"{pr.id}_subtitulos.srt")
    else:
        segs, _ = palabras(pr)
        subs = cues(segs, pr["subtitulos"].get("max_caracteres", 80))
        (d / f"{pr.id}_subtitulos.srt").write_text("".join(f"{i}\n{ts(a, False)} --> {ts(b, False)}\n{t}\n\n"
                                                          for i, (a, b, t) in enumerate(subs, 1)), encoding="utf-8")
    _, pals = palabras(pr)
    lineas = []
    for r in pr["rotulos"]:
        try:
            lineas.append(f"{mmss(buscar(pals, r['frase']))}  {r.get('chico', '')} {r.get('grande', '')}".strip())
        except ValueError:
            pass
    for i, c in enumerate(pr["capitulos"]):
        try:
            lineas.append(f"{'0:00' if i == 0 else mmss(buscar(pals, c['frase']))}  CAPÍTULO: {c['titulo']}")
        except ValueError:
            pass
    (d / f"{pr.id}_rotulos.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    (d / "LEEME.txt").write_text(f"""Paquete de {pr.id} para terminar en CapCut (escritorio)

1. CapCut > Crear proyecto > Importar: {pr.id}_video_limpio.mp4 y arrastrarlo a la línea de tiempo.
2. Subtítulos: menú Subtítulos > Agregar subtítulos (o Importar) > elegir {pr.id}_subtitulos.srt. Después elegir
   un estilo y marcar "Aplicar a todos". (O usar los subtítulos automáticos de CapCut sobre la voz.)
3. Rótulos y capítulos: {pr.id}_rotulos.txt tiene cada texto con su minuto.
4. Si se quiere otra mezcla (música, efectos), usar {pr.id}_solo_imagen.mp4 + {pr.id}_voz.wav.
5. Exportar a 1080p o 4K, 30 fps. El volumen ya está a -14 LUFS: no subirlo en CapCut.
6. Antes de subir, pasar el video exportado por el evaluador: python evaluar.py "<proyecto>" --video "<exportado>.mp4"

Ojo: CapCut pide una licencia amplia sobre lo que se sube a su nube; trabajar con proyectos locales y guardar
siempre una copia propia. No usar recursos de CapCut marcados como de uso no comercial en videos monetizados.
""", encoding="utf-8")
    print("LISTO", d, flush=True)


if __name__ == "__main__":
    main()
