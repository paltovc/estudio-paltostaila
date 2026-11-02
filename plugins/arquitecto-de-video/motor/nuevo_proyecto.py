# Crea la carpeta de un video nuevo con su estructura y un proyecto.json de partida.
#   python nuevo_proyecto.py "C:\Videos\Finanzas\Video03" --nombre Video03 --canal finanzas
import json, sys
from pathlib import Path
from estudio import DEFAULTS

args = [a for a in sys.argv[1:]]
if not args or args[0].startswith("-"):
    sys.exit('Uso: python nuevo_proyecto.py "C:\\ruta\\del\\video" --nombre Video03 [--canal finanzas]')
carpeta = Path(args[0]).resolve()
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
nombre = opt("--nombre", carpeta.name)
canal = opt("--canal", "")

LEEME = {
    "01_GUION": "Guion final en .txt o .md (sirve para corregir los subtitulos). Tambien notas de investigacion y fuentes.",
    "02_VOZ": "Audios de voz (.mp3/.wav). Si son 2 o 3 partes, nombrarlas en orden: parte1, parte2...",
    "03_IMAGENES": "Imagenes de ChatGPT u otras. Aqui tambien queda prompts_imagenes.md con lo que hay que generar.",
    "04_CLIPS_FLOW": "Clips descargados de Flow, sin renombrar. asignar_clips.py los reconoce y crea escena_NNN.mp4.",
    "05_SONIDOS": "Sonidos propios de este video (opcional). El banco general esta en EstudioPaltostaila\\sonidos.",
    "06_RECETA": "transcripcion.json, receta.csv (que imagen va en cada momento) y diferencias con el guion.",
    "07_RENDER": "Videos finales, borradores y revision. Se puede borrar 07_RENDER\\tmp cuando el video ya se publico.",
    "08_PUBLICAR": "Paquete por plataforma: titulos, descripcion, etiquetas, miniaturas, capitulos.",
}
for sub, texto in LEEME.items():
    (carpeta / sub).mkdir(parents=True, exist_ok=True)
    leeme = carpeta / sub / "LEEME.txt"
    if not leeme.exists():
        leeme.write_text(texto + "\n", encoding="utf-8")

pj = carpeta / "proyecto.json"
if pj.exists():
    print("ya existe", pj, "- no se toca")
else:
    cfg = {
        "nombre": nombre,
        "canal": canal,
        "version": "",
        "audios": "02_VOZ/*",
        "escenas_capitulo": [],
        "planos": {},
        "alias_clips": {},
        "correcciones": [],
        "rotulos": [],
        "capitulos": [],
        "sonidos": {"efectos": [], "lapiz": [], "clips_con_sonido": [], "recorte_clip": {}},
        "vertical": [],
        "miniaturas": [],
    }
    pj.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("creado", pj)
print("carpeta lista:", carpeta)
