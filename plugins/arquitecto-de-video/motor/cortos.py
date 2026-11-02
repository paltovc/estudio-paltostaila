# Elige solo los mejores tramos del video largo para Shorts / TikTok / Reels (verticales 9:16).
# Busca tramos de 40-80 s que empiecen en una frase con gancho (pregunta, "imagina", un error, un numero),
# que no corten una idea a la mitad y que no se pisen entre si. Propone titulo para cada uno.
#   python cortos.py "C:\ruta\video"               muestra la propuesta (no cambia nada)
#   python cortos.py "C:\ruta\video" --aplicar      la guarda en proyecto.json -> "vertical" (reemplaza lo que haya)
#   python cortos.py "C:\ruta\video" --si-faltan    la guarda solo si "vertical" esta vacio (lo usa render.cmd)
#   opciones: --n 3 (cuantos cortos)  --min 40 --max 80 (segundos)  --modo recorte (pantalla completa) | marco
import json, re, sys
from estudio import Proyecto, palabras, buscar, mmss, norm

pr = Proyecto()
opt = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
N, MIN, MAX = opt("--n", 3), opt("--min", 40.0), opt("--max", 80.0)
MODO = opt("--modo", "marco")
IDEAL = (MIN + MAX) / 2

GANCHOS = ("imagina", "nadie", "la mayoría", "el error", "el problema", "la verdad", "sabías", "por qué", "qué pasa",
           "si tú", "si alguna vez", "hay una", "la primera", "la segunda", "la tercera", "lo que nadie", "piensa en",
           "cuánto", "cómo", "cuál", "nunca", "siempre", "deja de", "antes de")
CONECTORES = {"y", "pero", "entonces", "además", "porque", "también", "o", "ni", "aunque", "sino", "así", "luego", "después"}


def frases_de(segs):
    out, actual = [], []
    for s in segs:
        for w in s["words"]:
            actual.append(w)
            if w["word"].rstrip("»\"'”").endswith((".", "?", "!", "…")):
                out.append(actual); actual = []
    if actual:
        out.append(actual)
    return [{"t0": f[0]["start"], "t1": f[-1]["end"], "texto": " ".join(w["word"] for w in f)} for f in out]


def puntaje(tramo, inicios_bloque):
    primera = tramo[0]["texto"]
    p = norm(primera)
    s = 0.0
    if primera.strip().startswith("¿") or primera.strip().endswith("?"):
        s += 3
    if any(primera.lower().startswith(g) or (" " + g) in primera.lower()[:40] for g in GANCHOS):
        s += 2
    if re.search(r"\d", primera):
        s += 1
    if p and p[0] in CONECTORES:
        s -= 3   # empieza a mitad de una idea
    if any(abs(tramo[0]["t0"] - b) < 1.5 for b in inicios_bloque):
        s += 2   # empieza donde empieza un bloque: se entiende solo
    s += 0.5 * sum(1 for f in tramo[1:] if f["texto"].strip().endswith("?"))
    dur = tramo[-1]["t1"] - tramo[0]["t0"]
    s -= abs(dur - IDEAL) / 15
    return s


def titulo_para(t0, t1, frases):
    for r in pr["rotulos"]:   # un rotulo dentro del tramo es el mejor titulo
        try:
            tr = buscar(pals, r["frase"])
        except ValueError:
            continue
        if t0 - 1 <= tr <= t1:
            return r["chico"], r["grande"]
    previos = []   # si no hay rotulo: el titulo del capitulo donde cae el tramo
    for c in pr["capitulos"]:
        try:
            tc = buscar(pals, c["frase"])
        except ValueError:
            continue
        if tc <= t0 + 1.5:
            previos.append((tc, c["titulo"]))
    if previos:
        return "", max(previos)[1]
    return "", ""   # sin titulo: lo escribe el publicador (no repetir la primera frase, ya sale en subtitulos)


segs, pals = palabras(pr)
frases = frases_de(segs)
inicios_bloque = []
for c in pr["capitulos"]:
    try:
        inicios_bloque.append(buscar(pals, c["frase"]))
    except ValueError:
        pass
for r in pr["rotulos"]:
    try:
        inicios_bloque.append(buscar(pals, r["frase"]))
    except ValueError:
        pass
fin_video = pr.duracion()

candidatos = []
for i in range(len(frases)):
    tramo = []
    for j in range(i, len(frases)):
        tramo.append(frases[j])
        dur = frases[j]["t1"] - frases[i]["t0"]
        cruza_bloque = any(frases[i]["t0"] + 1.5 < b < frases[j]["t1"] - 0.5 for b in inicios_bloque) and dur > MIN
        if dur > MAX or cruza_bloque:
            tramo.pop()
            break
    if not tramo:
        continue
    dur = tramo[-1]["t1"] - tramo[0]["t0"]
    if dur >= MIN:
        candidatos.append((puntaje(tramo, inicios_bloque), tramo))

elegidos = []
for s, tramo in sorted(candidatos, key=lambda x: -x[0]):
    a, b = tramo[0]["t0"], tramo[-1]["t1"]
    if all(b <= x[0]["t0"] or a >= x[-1]["t1"] for _, x in elegidos):   # sin pisarse
        elegidos.append((s, tramo))
    if len(elegidos) >= N:
        break
elegidos.sort(key=lambda x: x[1][0]["t0"])

propuesta = []
for k, (s, tramo) in enumerate(elegidos, 1):
    a, b = tramo[0]["t0"], tramo[-1]["t1"]
    chico, titulo = titulo_para(a, b, tramo)
    siguiente = next((f["texto"] for f in frases if f["t0"] >= b - 0.05), None)
    v = {"nombre": f"Short{k}_{pr.base_nombre}", "desde": " ".join(tramo[0]["texto"].split()[:6]),
         "desde_s": round(max(a - 0.15, 0), 2), "hasta_s": round(min(b + 0.35, fin_video), 2),
         "chico": chico, "titulo": titulo.replace("\\N", " "), "modo": MODO}
    if siguiente:
        v["hasta"] = " ".join(siguiente.split()[:6])
    propuesta.append(v)
    print(f"Short {k}: {mmss(a)} -> {mmss(b)} ({b - a:.0f} s, puntaje {s:.1f})")
    print(f"   titulo: {(chico + ' · ' if chico else '') + titulo if titulo else '(falta: lo propone el publicador)'}")
    print(f"   empieza: {tramo[0]['texto'][:110]}")

if not propuesta:
    sys.exit(f"No encontre tramos de {MIN:.0f}-{MAX:.0f} s; probar con --min 30 o --max 120")
(pr.salida / "cortos_propuestos.json").write_text(json.dumps(propuesta, ensure_ascii=False, indent=2), encoding="utf-8")
aplicar = "--aplicar" in sys.argv or ("--si-faltan" in sys.argv and not pr["vertical"])
if aplicar:
    pj = pr.dir / "proyecto.json"
    cfg = json.loads(pj.read_text(encoding="utf-8"))
    cfg["vertical"] = propuesta
    pj.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(propuesta)} cortos guardados en proyecto.json; ahora: python vertical.py")
elif "--si-faltan" in sys.argv:
    print("\nproyecto.json ya tiene cortos definidos; se usan esos (propuesta nueva en cortos_propuestos.json)")
else:
    print("\nNada cambiado. Para usarlos: --aplicar (o editar los titulos en cortos_propuestos.json)")
