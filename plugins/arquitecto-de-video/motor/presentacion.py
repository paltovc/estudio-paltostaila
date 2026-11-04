# Presentación (PDF o PowerPoint) -> curso en video con el motor de siempre.
#   python presentacion.py "<presentacion.pdf|.pptx>" "<proyecto>" [--fondo fondo|blanco|negro] [--canal finanzas]
#   1) cada diapositiva queda como imagen 1920x1080 en 03_IMAGENES (<ID>_img-001_diapo.png, ...); si la proporción no
#      es 16:9 se completa con el color de fondo del canal (nunca se corta)
#   2) 06_RECETA\diapositivas.txt: el texto de cada diapositiva (para el guion o para revisar)
#   3) si ya está la transcripción de la voz (o de la grabación de la charla): 06_RECETA\receta_diapos.csv, una receta
#      borrador donde cada diapositiva empieza cuando la voz empieza a hablar de lo que dice (por palabras en común).
#      Se revisa, se copia como receta.csv y se valida con frases.py --validar, como siempre.
# Un .pptx se convierte a PDF con PowerPoint instalado (Windows). Si no hay PowerPoint: "Guardar como PDF" a mano.
# Para la persona en una esquina sobre las diapositivas: capas.py pip (después del render), o grabado.py si es charla grabada.
import csv, json, re, subprocess, sys
from pathlib import Path
from PIL import Image

PALABRAS_VACIAS = set("""a al algo como con cual cuando de del desde donde el ella ellas ellos en entre era es esa ese eso esta este
esto estos fue ha hay la las le les lo los mas me mi muy no nos o para pero por que se si sin sobre son su sus tambien te tiene
todo todos tu un una uno unos y ya the and for with this that from your are you""".split())


def a_pdf(pptx):
    pdf = Path(pptx).with_suffix(".pdf")
    if pdf.exists():
        return pdf
    ps = (f"$p = New-Object -ComObject PowerPoint.Application; $d = $p.Presentations.Open('{Path(pptx).resolve()}', $true, $false, $false);"
          f" $d.SaveAs('{pdf.resolve()}', 32); $d.Close(); $p.Quit()")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    if r.returncode or not pdf.exists():
        sys.exit("No pude convertir el .pptx (¿PowerPoint instalado?). Ábrelo y usa Archivo > Guardar como > PDF.\n" + r.stderr[-400:])
    return pdf


def claves(texto):
    return {w for w in re.findall(r"[a-záéíóúñü0-9]{4,}", texto.lower()) if w not in PALABRAS_VACIAS}


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit("Uso: python presentacion.py \"<presentacion.pdf|.pptx>\" \"<proyecto>\"")
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    fuente, carpeta = Path(a[0]), Path(a[1])
    if fuente.suffix.lower() in (".pptx", ".ppt"):
        fuente = a_pdf(fuente)
    try:
        import pypdfium2 as pdfium
    except ImportError:
        sys.exit("Falta el lector de PDF: python -m pip install pypdfium2")
    sys.argv = [sys.argv[0], str(carpeta)]
    from estudio import Proyecto, palabras, mmss
    from diseno import marca, color
    pr = Proyecto(carpeta)
    W, H = pr.ancho, pr.alto
    fondo = {"blanco": (255, 255, 255), "negro": (0, 0, 0)}.get(op("--fondo", "fondo")) or color("fondo", marca(op("--canal") or pr.cfg.get("canal")))[:3]
    pr.imagenes.mkdir(parents=True, exist_ok=True)
    doc = pdfium.PdfDocument(str(fuente))
    textos, archivos = [], []
    for i in range(len(doc)):
        pag = doc[i]
        ancho, alto = pag.get_size()
        esc = max(W / ancho, H / alto) * 1.0
        im = pag.render(scale=esc).to_pil().convert("RGB")
        im.thumbnail((W, H), Image.LANCZOS)
        lienzo = Image.new("RGB", (W, H), tuple(fondo))
        lienzo.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
        nombre = f"{pr.id}_img-{i + 1:03d}_diapo.png"
        destino = pr.imagenes / nombre
        if destino.exists():
            nombre = f"{pr.id}_img-{i + 1:03d}_diapo_{fuente.stem[:20]}.png"
            destino = pr.imagenes / nombre
        lienzo.save(destino)
        archivos.append(nombre)
        textos.append(pag.get_textpage().get_text_range().strip())
        print(f"diapositiva {i + 1}/{len(doc)} -> {nombre}", flush=True)
    rec = pr.receta.parent
    rec.mkdir(parents=True, exist_ok=True)
    (rec / "diapositivas.txt").write_text("".join(f"=== Diapositiva {i + 1} ({archivos[i]})\n{t}\n\n" for i, t in enumerate(textos)),
                                          encoding="utf-8")
    if not pr.transcripcion.exists():
        print("Sin transcripción todavía: después de transcribir la voz, vuelve a correr esto para la receta de diapositivas.")
        print("LISTO", flush=True)
        return
    segs, _ = palabras(pr)
    dur = pr.duracion()
    inicios, desde = [], 0
    for i, t in enumerate(textos):
        k = claves(t)
        mejor, cuando = 0, None
        for j in range(desde, len(segs)):
            puntos = len(k & claves(segs[j]["text"]))
            if puntos > mejor:
                mejor, cuando = puntos, j
        if i == 0:
            cuando = 0
        if cuando is None or mejor == 0:            # sin palabras en común: se reparte el tiempo que queda
            cuando = None
        inicios.append(cuando)
        if cuando is not None:
            desde = cuando + 1
    tiempos = []
    for i, j in enumerate(inicios):
        tiempos.append(segs[j]["start"] if j is not None else None)
    tiempos[0] = 0.0
    for i in range(len(tiempos)):                   # huecos: repartir entre las conocidas
        if tiempos[i] is None:
            sig = next((k for k in range(i + 1, len(tiempos)) if tiempos[k] is not None), None)
            fin = tiempos[sig] if sig is not None else dur
            n = (sig if sig is not None else len(tiempos)) - i + 1
            tiempos[i] = tiempos[i - 1] + (fin - tiempos[i - 1]) / n
    filas = []
    for i, t0 in enumerate(tiempos):
        t1 = tiempos[i + 1] if i + 1 < len(tiempos) else dur
        if t1 - t0 < 0.5:
            continue
        frase = next((" ".join(s["text"].split()[:6]) for s in segs if s["start"] >= t0 - 0.05), "")
        nota = "" if inicios[i] is not None or i == 0 else "tiempo repartido: revisar"
        filas.append([len(filas) + 1, archivos[i], mmss(t0), mmss(t1), round(t1 - t0, 2), frase, "imagen", "diapositiva", nota])
    with open(rec / "receta_diapos.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["numero", "archivo", "inicio", "fin", "duracion", "frase", "tipo", "origen", "nota"])
        w.writerows(filas)
    print(f"receta borrador: {rec / 'receta_diapos.csv'} ({len(filas)} escenas; revisar las marcadas)")
    print("LISTO", flush=True)


if __name__ == "__main__":
    main()
