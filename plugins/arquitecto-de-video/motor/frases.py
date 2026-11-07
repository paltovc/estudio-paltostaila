# Prepara la receta de escenas: corta la narracion en tramos de 3 a 12 s que empiezan en una frase
# y deja una receta borrador con la columna "archivo" vacia para asignar una imagen a cada tramo.
#   python frases.py "C:\ruta\video"            crea 06_RECETA/receta_borrador.csv (no toca receta.csv)
#   python frases.py "C:\ruta\video" --validar  revisa receta.csv: imagenes que faltan, huecos, solapes, duraciones
import csv, sys
from estudio import Proyecto, palabras, mmss

pr = Proyecto()
MIN_S, MAX_S = 3.0, 12.0
CAMPOS = ["numero", "archivo", "inicio", "fin", "duracion", "frase", "tipo", "origen", "nota"]


def frases(segs):
    """Frases completas (terminan en . ? ! o …) con sus tiempos."""
    out, actual = [], []
    for s in segs:
        for w in s["words"]:
            actual.append(w)
            if w["word"].rstrip("»\"'”").endswith((".", "?", "!", "…")):
                out.append(actual); actual = []
    if actual:
        out.append(actual)
    return [(f[0]["start"], f[-1]["end"], " ".join(w["word"] for w in f)) for f in out]


def borrador():
    segs, _ = palabras(pr)
    fr = frases(segs)
    dur = pr.duracion()
    tramos, actual = [], []
    for f in fr:
        if actual and (f[1] - actual[0][0] > MAX_S) and (actual[-1][1] - actual[0][0] >= MIN_S):
            tramos.append(actual); actual = []
        actual.append(f)
    if actual:
        tramos.append(actual)
    filas = []
    for i, t in enumerate(tramos):
        ini = 0.0 if i == 0 else t[0][0]
        fin = tramos[i + 1][0][0] if i + 1 < len(tramos) else dur
        filas.append(dict(numero=i + 1, archivo="", inicio=mmss(ini), fin=mmss(fin), duracion=f"{fin - ini:.2f}",
                          frase=" ".join(x[2] for x in t)[:300], tipo="imagen", origen="", nota=""))
    ruta = pr.receta.with_name("receta_borrador.csv")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, delimiter=";")
        w.writeheader(); w.writerows(filas)
    imgs = sorted(p.name for p in pr.imagenes.glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"))
    print(f"{len(fr)} frases -> {len(filas)} tramos en {ruta}")
    print(f"{len(imgs)} imagenes disponibles en {pr.imagenes}")
    print("Siguiente: completar 'archivo' en cada fila (una imagen por idea; se puede repetir) y guardar como receta.csv")


def validar():
    filas = pr.escenas()
    dur = pr.duracion()
    errores, avisos = [], []
    if not filas:
        errores.append("la receta no tiene escenas")
    for i, r in enumerate(filas):
        if not r["archivo"] or not (pr.imagenes / r["archivo"]).exists():
            errores.append(f"escena {r['n']}: falta la imagen '{r['archivo']}'")
        d = r["t1"] - r["t0"]
        if d < 1.0:
            errores.append(f"escena {r['n']}: dura {d:.2f} s (muy corta para sus transiciones)")
        elif d < 2.5 or d > 14:
            avisos.append(f"escena {r['n']}: dura {d:.1f} s")
        if i and abs(r["t0"] - filas[i - 1]["t1"]) > 0.02:
            errores.append(f"escena {r['n']}: empieza en {mmss(r['t0'])} pero la anterior termina en {mmss(filas[i - 1]['t1'])}")
    if filas and filas[0]["t0"] > 0.02:
        errores.append("la primera escena no empieza en 0:00")
    if filas and abs(filas[-1]["t1"] - dur) > 0.5:
        avisos.append(f"la ultima escena termina en {mmss(filas[-1]['t1'])} y la voz dura {mmss(dur)}")
    for e in errores:
        print("ERROR", e)
    for a in avisos:
        print("aviso", a)
    print(f"{len(filas)} escenas, {len(errores)} errores, {len(avisos)} avisos")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    validar() if "--validar" in sys.argv else borrador()
