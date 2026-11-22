# Crea (o completa) la carpeta de un video con su estructura y un proyecto.json de partida.
# Nunca mueve, renombra ni borra lo que ya existe: si la carpeta ya tiene imagenes o audios, se apunta a ellos.
#   python nuevo_proyecto.py "C:\...\FIN-003_fondo-de-emergencia" --id FIN-003 --nombre "Fondo de emergencia" --canal finanzas
#     --id: codigo del video (prefijo del canal + numero). Todo lo que sale del estudio se llama <ID>_<version>_...
#     --codigo FIN --numero 3   arma el ID solo (FIN-003) si no se da --id; sin --codigo, el código sale de la biblia del
#                               canal («Código de los videos: `FIN`» en canales\<canal>\canal.md) (0.15)
#     --idioma es|en|pt         idioma del video (0.15): queda en "idioma" y en la transcripción (whisperx.idioma)
#     --tipo-video narrado|animado|persona|musical|curso   (0.15) lo lee evaluar.py para pesar los ejes
#   opciones:
#     --formato vertical            video principal 9:16 (TikTok, Reels, Shorts); por defecto horizontal 16:9
#     --imagenes "C:\ruta\imagenes"  usar una carpeta de imagenes que ya existe (no se copia)
#     --voz "C:\ruta\audios"         usar una carpeta de audios que ya existe (no se copia)
#     --personaje "C:\a.png;C:\b.png" o "C:\carpeta"   copia las imagenes del personaje a la carpeta del canal
import json, re, shutil, sys
from datetime import date
from pathlib import Path

ESTUDIO = Path.home() / "EstudioPaltostaila"
EXT_IMG = (".png", ".jpg", ".jpeg", ".webp")

args = [a for a in sys.argv[1:]]
if not args or args[0].startswith("-"):
    sys.exit('Uso: python nuevo_proyecto.py "C:\\ruta\\del\\video" --nombre Video03 [--canal finanzas] [--formato vertical] '
             '[--imagenes ruta] [--voz ruta] [--personaje "img1;img2" o carpeta]')
carpeta = Path(args[0]).resolve()
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
nombre = opt("--nombre", carpeta.name)
canal = opt("--canal", "")


def codigo_del_canal(c):
    """Código de los videos del canal (FIN, …): el de su biblia (canales\\<canal>\\canal.md, línea «Código de los videos:
    `XXX`») y, si no lo dice, las tres primeras letras del canal (como antes del 0.15)."""
    for base in (ESTUDIO / "canales" / c, Path(__file__).resolve().parent.parent / "canales" / c):
        try:
            m = re.search(r"C[oó]digo de los videos:\s*`([A-Za-z0-9]{2,8})`", (base / "canal.md").read_text(encoding="utf-8-sig"))
            if m:
                return m.group(1).upper()
        except OSError:
            continue
    return c[:3].upper()


vid = opt("--id") or (f"{(opt('--codigo') or codigo_del_canal(canal)).upper()}-{int(opt('--numero')):03d}" if opt("--numero") else None)
if not canal:
    print("AVISO sin --canal: el proyecto queda sin canal (la biblia, la marca y el gerente lo necesitan); se puede anotar "
          "después en proyecto.json → \"canal\"")
idioma = (opt("--idioma") or "").lower()[:2]                 # 0.15: es, en o pt (también el de la transcripción)
if idioma and idioma not in ("es", "en", "pt"):
    sys.exit("--idioma tiene que ser es, en o pt")
tipo_video = (opt("--tipo-video") or "").lower()             # 0.15: narrado, animado, persona, musical o curso (evaluar.py)
if tipo_video and tipo_video not in ("narrado", "animado", "persona", "musical", "curso"):
    sys.exit("--tipo-video tiene que ser narrado, animado, persona, musical o curso")
vertical = (opt("--formato", "horizontal") or "").lower().startswith("vert")
imagenes_ext, voz_ext = opt("--imagenes"), opt("--voz")

LEEME = {
    "01_GUION": "Guion final en .txt o .md (sirve para corregir los subtitulos). Tambien investigacion, empaque y referentes.",
    "02_VOZ": "Audios de voz (.mp3/.wav). Si son 2 o 3 partes, nombrarlas en orden: parte1, parte2...",
    "03_IMAGENES": "Imagenes en orden: <ID>_img-001_tema.png ... Las descargas sueltas van a _entrantes y ordenar_imagenes.py las numera.",
    "04_CLIPS_FLOW": "Clips descargados de Flow, sin renombrar. asignar_clips.py los reconoce y crea escena_NNN.mp4.",
    "05_SONIDOS": "Sonidos propios de este video (opcional). El banco general esta en EstudioPaltostaila\\sonidos.",
    "06_RECETA": "transcripcion.json, receta.csv (que imagen va en cada momento) y diferencias con el guion.",
    "07_RENDER": "Videos finales, borradores y revision. Se puede vaciar 07_RENDER\\tmp cuando el video ya se publico.",
    "08_PUBLICAR": "Paquete por plataforma: titulos, descripcion, etiquetas, miniaturas, capitulos.",
}
existia = carpeta.exists() and any(carpeta.iterdir())
if existia:
    print("La carpeta ya tiene contenido; no se mueve ni se renombra nada:")
    for p in sorted(carpeta.iterdir())[:30]:
        print("   ", ("[carpeta] " if p.is_dir() else "") + p.name)
for sub, texto in LEEME.items():
    if sub == "03_IMAGENES" and imagenes_ext:
        continue
    if sub == "02_VOZ" and voz_ext:
        continue
    (carpeta / sub).mkdir(parents=True, exist_ok=True)
    if sub == "03_IMAGENES":
        (carpeta / sub / "_entrantes").mkdir(exist_ok=True)
    leeme = carpeta / sub / "LEEME.txt"
    if not leeme.exists():
        leeme.write_text(texto + "\n", encoding="utf-8")

# Personaje: copia de las referencias (los originales quedan donde estaban)
refs_destino = None
if opt("--personaje"):
    fuentes = []
    for parte in opt("--personaje").split(";"):
        p = Path(parte.strip().strip('"'))
        if p.is_dir():
            fuentes += sorted(x for x in p.iterdir() if x.suffix.lower() in EXT_IMG)
        elif p.is_file():
            fuentes.append(p)
        else:
            print("AVISO no encuentro", p)
    refs_destino = (ESTUDIO / "canales" / canal / "personaje" / "referencias") if canal else (carpeta / "00_PERSONAJE" / "referencias")
    refs_destino.mkdir(parents=True, exist_ok=True)
    for f in fuentes:
        destino = refs_destino / f.name
        k = 1
        while destino.exists():                     # nunca encima de una referencia que ya está
            destino = refs_destino / f"{f.stem}_{date.today():%Y%m%d}{'' if k == 1 else f'_{k}'}{f.suffix}"
            k += 1
        shutil.copy2(f, destino)
    print(f"{len(fuentes)} imagenes del personaje copiadas a {refs_destino}")

pj = carpeta / "proyecto.json"
if pj.exists():
    print("ya existe", pj, "- no se toca")
else:
    cfg = {
        "id": vid or nombre, "nombre": nombre, "canal": canal, "version": "v1",
        "audios": (str(Path(voz_ext) / "*") if voz_ext else "02_VOZ/*"),
        "carpetas": {k: v for k, v in {"imagenes": imagenes_ext}.items() if v},
        "escenas_capitulo": [], "planos": {}, "alias_clips": {}, "correcciones": [],
        "rotulos": [], "capitulos": [],
        "sonidos": {"efectos": [], "lapiz": [], "clips_con_sonido": [], "recorte_clip": {},
                    "alinear": "ataque", "baja_sobre_voz": -3},      # 0.14: solo los proyectos nuevos
        "vertical": [], "miniaturas": [],
        "vertical_esquivar_caras": True,     # 0.15: en los Shorts los elementos esquivan caras (solo proyectos nuevos; lo lee vertical.py)
    }
    if idioma:
        cfg["idioma"] = idioma
        cfg["whisperx"] = {"idioma": idioma}       # la transcripción en el idioma del video (el resto, por defecto)
    if tipo_video:
        cfg["tipo_video"] = tipo_video
    if vertical:
        cfg["video"] = {"fps": 30, "ancho": 1080, "alto": 1920, "crf": 20}
        cfg["subtitulos"] = {"max_caracteres": 42, "fuente": "Arial", "tamano": 38}
    pj.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("creado", pj, "(formato vertical 9:16)" if vertical else "(formato horizontal 16:9)")

brief = carpeta / "00_BRIEF.md"
if not brief.exists():
    brief.write_text(f"""# Brief — {vid + ' · ' if vid else ''}{nombre}
Fecha: {date.today():%d-%m-%Y} · Canal: {canal or '(sin canal)'}

- Objetivo:
- Plataforma principal y formato: {'vertical 9:16' if vertical else 'horizontal 16:9'}
- Otras plataformas (cortes):
- Duracion objetivo:
- Publico:
- Tono:
- Idea que debe llevarse quien mira:
- Llamado a la accion:
- Guion: trae el suyo / escribir desde cero / adaptar
- Voz:
- Personaje: {('referencias en ' + str(refs_destino)) if refs_destino else 'sí/no'}
- Imagenes y clips: {('carpeta existente ' + imagenes_ext) if imagenes_ext else 'quién los genera'}
- Referentes:
- Carpeta de trabajo: {carpeta}
- Supuestos tomados (si no hubo respuesta):
""", encoding="utf-8")
print("carpeta lista:", carpeta)
