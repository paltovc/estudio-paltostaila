# Voces neuronales de Microsoft (las mismas que usan páginas como voicertool.com) directo desde el estudio,
# con edge-tts. Lista voces, crea muestras para escucharlas y genera la voz completa de un guion con los tiempos
# exactos de cada palabra (sirve como transcripcion: no hace falta WhisperX).
#
# AVISO: edge-tts usa el servicio de lectura en voz alta del navegador Edge de forma no oficial. Puede dejar de
# funcionar sin aviso y no da una licencia de uso comercial explícita. Para videos que se publican, usar la página
# de voz del canal (con su licencia) salvo que la persona decida otra cosa.
#
#   python voces.py listar [--idioma es]
#   python voces.py muestras "texto de prueba" [--idioma es] [--voces es-CL-LorenzoNeural,es-MX-JorgeNeural] [--multilingues]
#   python voces.py generar "C:\ruta\video" --voz es-CL-LorenzoNeural [--texto archivo.txt] [--velocidad +5%] [--tono +0Hz] [--volumen +0%]
import asyncio, html, json, re, subprocess, sys, unicodedata
from datetime import datetime
from pathlib import Path

try:
    import edge_tts
except ImportError:
    sys.exit("Falta edge-tts: python -m pip install --user edge-tts")

ESTUDIO = Path.home() / "EstudioPaltostaila"
args = sys.argv[1:]
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
PAIS = {"AR": "Argentina", "BO": "Bolivia", "CL": "Chile", "CO": "Colombia", "CR": "Costa Rica", "CU": "Cuba",
        "DO": "Rep. Dominicana", "EC": "Ecuador", "ES": "España", "GQ": "Guinea Ecuatorial", "GT": "Guatemala",
        "HN": "Honduras", "MX": "México", "NI": "Nicaragua", "PA": "Panamá", "PE": "Perú", "PR": "Puerto Rico",
        "PY": "Paraguay", "SV": "El Salvador", "US": "Estados Unidos", "UY": "Uruguay", "VE": "Venezuela"}


def voces(idioma=None, multilingues=False):
    vs = asyncio.run(edge_tts.list_voices())
    out = []
    for v in vs:
        multi = "Multilingual" in v["ShortName"]
        if idioma and not v["Locale"].startswith(idioma + "-") and not (multilingues and multi):
            continue
        tag = v.get("VoiceTag", {})
        out.append({"voz": v["ShortName"], "nombre": re.sub(r"(Multilingual)?Neural$", "", v["ShortName"].split("-")[-1]),
                    "locale": v["Locale"], "pais": PAIS.get(v["Locale"].split("-")[-1], v["Locale"]),
                    "genero": {"Male": "hombre", "Female": "mujer"}.get(v["Gender"], v["Gender"]),
                    "estilo": ", ".join(tag.get("VoicePersonalities", [])), "multilingue": multi})
    return sorted(out, key=lambda x: (x["multilingue"], x["pais"], x["genero"], x["nombre"]))


async def _hablar(texto, voz, destino, velocidad="+0%", tono="+0Hz", volumen="+0%", palabras=False):
    c = edge_tts.Communicate(texto, voz, rate=velocidad, pitch=tono, volume=volumen,
                             boundary="WordBoundary" if palabras else "SentenceBoundary")
    marcas = []
    with open(destino, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                marcas.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
    return marcas


def ffprobe_dur(p, exe="ffprobe"):
    r = subprocess.run([exe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def listar():
    vs = voces(opt("--idioma", "es"), "--multilingues" in args)
    for v in vs:
        print(f"{v['voz']:<38} {v['genero']:<7} {v['pais']:<16} {v['estilo']}{'  (multilingüe)' if v['multilingue'] else ''}")
    print(f"\n{len(vs)} voces")


def muestras():
    texto = args[1] if len(args) > 1 and not args[1].startswith("--") else \
        "Imagina a dos personas viendo el mismo video sobre inversiones. Una piensa: todavía no entiendo esto."
    vs = voces(opt("--idioma", "es"), "--multilingues" in args)
    if opt("--voces"):
        quiero = opt("--voces").split(",")
        vs = [v for v in vs if v["voz"] in quiero]
    carpeta = ESTUDIO / "voces" / f"muestras_{datetime.now():%Y%m%d_%H%M}"
    carpeta.mkdir(parents=True, exist_ok=True)
    filas = []
    for v in vs:
        mp3 = carpeta / f"{v['voz']}.mp3"
        try:
            asyncio.run(_hablar(texto, v["voz"], mp3, opt("--velocidad", "+0%"), opt("--tono", "+0Hz")))
            filas.append(v)
            print("ok", v["voz"])
        except Exception as e:
            print("falló", v["voz"], str(e)[:80])
    (carpeta / "voces.json").write_text(json.dumps({"texto": texto, "voces": filas}, ensure_ascii=False, indent=1), encoding="utf-8")
    items = "\n".join(
        f'<div class="v"><b>{html.escape(v["nombre"])}</b> · {v["genero"]} · {html.escape(v["pais"])}'
        f'{" · multilingüe" if v["multilingue"] else ""}<br><small>{html.escape(v["voz"])} {html.escape(v["estilo"])}</small>'
        f'<br><audio controls preload="none" src="{html.escape(v["voz"])}.mp3"></audio></div>' for v in filas)
    (carpeta / "escuchar.html").write_text(
        f'<!doctype html><meta charset="utf-8"><title>Voces</title><style>body{{font-family:Arial;margin:20px;background:#f6f6f2}}'
        f'.v{{display:inline-block;width:300px;margin:6px;padding:10px;background:#fff;border-radius:8px}}audio{{width:280px}}</style>'
        f'<h2>Muestras de voz</h2><p>{html.escape(texto)}</p>{items}', encoding="utf-8")
    print(f"\n{len(filas)} muestras en {carpeta}\nabrir: {carpeta / 'escuchar.html'}")


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9ñ]", "", "".join(c for c in s if not unicodedata.combining(c)))


def trozos(texto, maximo=2500):
    """Corta en párrafos o frases sin pasar del máximo (más corto = más estable)."""
    partes, actual = [], ""
    for frase in re.split(r"(?<=[.!?…])\s+|\n{2,}", texto):
        frase = frase.strip()
        if not frase:
            continue
        if actual and len(actual) + len(frase) + 1 > maximo:
            partes.append(actual); actual = frase
        else:
            actual = (actual + " " + frase).strip()
    if actual:
        partes.append(actual)
    return partes


def alinear(marcas, texto, base):
    """Pega la puntuación del texto original a cada palabra con tiempo (edge-tts entrega palabras sin signos)."""
    tokens = texto.split()
    out, j = [], 0
    for t0, t1, w in marcas:
        nw = norm(w)
        k = j
        while k < len(tokens) and k < j + 6 and not norm(tokens[k]).startswith(nw[:3] if nw else "\0"):
            k += 1
        if k < len(tokens) and k < j + 6:
            palabra, j = tokens[k], k + 1
        else:
            palabra = w
        out.append({"word": palabra, "start": round(base + t0, 3), "end": round(base + t1, 3)})
    return out


def generar():
    from estudio import Proyecto, FFMPEG, FFPROBE
    pr = Proyecto(args[1])
    voz = opt("--voz", "es-CL-LorenzoNeural")
    fuente = Path(opt("--texto")) if opt("--texto") else None
    if not fuente:
        g = pr.ruta(pr["carpetas"]["guion"])
        partes = sorted(g.glob("voz_parte*.txt"))
        fuente = partes or [g / "guion_para_voz.txt"]
    archivos = fuente if isinstance(fuente, list) else [fuente]
    faltan = [str(a) for a in archivos if not Path(a).exists()]
    if faltan:
        sys.exit("No encuentro el texto para la voz: " + ", ".join(faltan) + " (o indicar --texto archivo.txt)")
    texto = "\n\n".join(Path(a).read_text(encoding="utf-8-sig").strip() for a in archivos)   # -sig: el Bloc de notas agrega BOM
    voz_dir = pr.voz
    voz_dir.mkdir(exist_ok=True)
    ya = [p for p in voz_dir.iterdir() if p.suffix.lower() in (".mp3", ".wav", ".m4a")]
    if ya and "--reemplazar" not in args:
        voz_dir = pr.dir / "02_VOZ_GENERADA"
        voz_dir.mkdir(exist_ok=True)
        print(f"AVISO 02_VOZ ya tiene audios: la voz nueva va a {voz_dir}. Para usarla, en proyecto.json: \"audios\": \"02_VOZ_GENERADA/*\"")
    tmp = pr.tmp / "voz_trozos"
    tmp.mkdir(parents=True, exist_ok=True)
    palabras, base, lista = [], 0.0, []
    ts = trozos(texto)
    for i, t in enumerate(ts, 1):
        mp3 = tmp / f"trozo_{i:03d}.mp3"
        marcas = asyncio.run(_hablar(t, voz, mp3, opt("--velocidad", "+0%"), opt("--tono", "+0Hz"), opt("--volumen", "+0%"), True))
        palabras += alinear(marcas, t, base)
        base += ffprobe_dur(mp3, FFPROBE)
        lista.append(mp3)
        print(f"trozo {i}/{len(ts)} listo ({len(t)} caracteres)", flush=True)
    (tmp / "lista.txt").write_text("".join(f"file '{p.name}'\n" for p in lista), encoding="utf-8")
    salida = voz_dir / f"{pr.id}_voz-{voz.split('-')[-1].replace('Neural', '').lower()}.mp3"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"), "-c", "copy", str(salida)], check=True)
    segs, actual = [], []
    for w in palabras:
        actual.append(w)
        if w["word"].rstrip("»\"'”)").endswith((".", "?", "!", "…")):
            segs.append(actual); actual = []
    if actual:
        segs.append(actual)
    tr = {"segments": [{"start": s[0]["start"], "end": s[-1]["end"], "text": " ".join(w["word"] for w in s), "words": s} for s in segs],
          "origen": f"edge-tts {voz} {datetime.now():%Y-%m-%d %H:%M}"}
    destino_tr = pr.transcripcion
    if destino_tr.exists() and "--reemplazar" not in args:
        destino_tr = destino_tr.with_name(destino_tr.stem + "_voz_generada.json")
    destino_tr.parent.mkdir(parents=True, exist_ok=True)
    destino_tr.write_text(json.dumps(tr, ensure_ascii=False), encoding="utf-8")
    print(f"\nvoz: {salida} ({base:.1f} s, {voz})")
    print(f"tiempos por palabra: {destino_tr} (no hace falta transcribir con WhisperX)")


if __name__ == "__main__":
    accion = args[0] if args else ""
    {"listar": listar, "muestras": muestras, "generar": generar}.get(accion, lambda: sys.exit(
        'Uso: python voces.py listar | muestras "texto" | generar "C:\\ruta\\video" --voz es-CL-LorenzoNeural'))()
