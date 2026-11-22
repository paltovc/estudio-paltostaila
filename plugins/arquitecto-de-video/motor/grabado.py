# Edición de material grabado a cámara (cursos, clases, tutoriales, alguien hablando): elegir tomas por lo que se dice,
# sacar muletillas, trabas y silencios, cortes que no se noten (micro-fundido de audio, punch-in alternado en los
# cortes del mismo plano, cortes J/L entre planos distintos) y el mismo color en todas las tomas.
# Nunca toca los originales: lee la carpeta de material y escribe en el proyecto.
#
#   python grabado.py "<proyecto>" transcribir     transcribe cada toma (WhisperX) -> 06_RECETA/tomas.md + orden propuesto
#   python grabado.py "<proyecto>" cortar          calcula qué se queda (06_RECETA/cortes.md) y la transcripción final
#   python grabado.py "<proyecto>" armar [--borrador 60]   arma tmp/solo_video.mp4 y la voz editada; después terminar.py
#
# En proyecto.json:
# "grabado": {"material": "C:\\...\\tomas", "look": "natural", "referencia_color": "C0012.MP4",
#             "pausa_max": 0.45, "margen": 0.08, "punch": 1.08, "jl": 0.0, "limpiar_voz": true,
#             "muletillas_extra": ["o sea"],
#             "orden": [{"archivo": "C0012.MP4", "desde": 3.2, "hasta": 45.0, "nota": "intro"}, ...]}
# Sin "orden" se usa el orden propuesto (06_RECETA/orden_propuesto.json): todas las frases, quitando las que se
# repiten más adelante (se queda la última versión, que suele ser la buena).
#
# 0.15 (todo opcional; sin estos campos el armado es el de siempre). Detalle en references/motor-0150-camara.md:
#   "grabado": {"luz": {"auto": true, "realce_cara": 0.15, "balance": "auto"},          iluminación automática (luz.py)
#               "enfasis": {"zoom": 1.12, "dura": 0.6, "max_por_min": 6, "palabras": ["clave"], "marcas": [{"segundo": 12}]},
#               "angulos": {"modo": "alternar", "planos": ["general", "medio", "cerrado"], "cambio_cada": [4, 9]}}
#   "apoyo": [{"en": "frase exacta", "archivo": "foto.jpg", "dura": 3, "modo": "completo"}]   material de apoyo (apoyo.py)
# Prioridad de la cámara: 1) ángulos (encuadre base; cambian en cortes o pausas)  2) punch (solo en un corte del mismo
# plano donde el ángulo no cambió)  3) énfasis (zoom suave encima del encuadre, nunca cruza un corte).
import difflib, json, random, re, shutil, subprocess, sys
from pathlib import Path
from estudio import Proyecto, FFMPEG, FFPROBE, run, norm, nombre_libre, entregar, parcial_de, palabras, buscar
from color import cadena
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

pr = Proyecto()
G = {"material": "", "look": "natural", "pausa_max": 0.45, "margen": 0.08, "punch": 1.08, "jl": 0.0, "limpiar_voz": True,
     "muletillas_extra": [], **pr.cfg.get("grabado", {})}
MULETILLAS = {"eh", "ehh", "ehm", "em", "emm", "mm", "mmm", "hmm", "ah", "aah", "uh", "um"}
VIDEO = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".mts"}
DIR_T = pr.dir / "06_RECETA" / "tomas"
TMP = pr.tmp / "grabado"
W, H, FPS = pr.ancho, pr.alto, pr.fps


def material():
    m = pr.ruta(G["material"]) if G["material"] else pr.dir / "00_MATERIAL"
    if not m.exists():
        sys.exit(f"No encuentro la carpeta de tomas {m}. Ponla en proyecto.json -> grabado.material")
    return m, sorted(f for f in m.iterdir() if f.suffix.lower() in VIDEO and "(1)" not in f.stem)


def ruta_toma(nombre):
    m, _ = material()
    return m / nombre


def dur(p):
    return float(run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).strip())


def tok(w):
    t = norm(w)
    return t[0] if t else ""


# ---------- 1. transcribir y proponer tomas ----------
def transcribir():
    from transcribir import whisperx
    _, tomas = material()
    DIR_T.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    wx = pr["whisperx"]
    for f in tomas:
        js = DIR_T / f"{f.stem}.json"
        if js.exists() and "--rehacer" not in sys.argv:
            continue
        wav = TMP / f"{f.stem}.wav"
        run([FFMPEG, "-v", "error", "-y", "-i", f, "-vn", "-ac", "1", "-ar", "16000", *SIN_METADATOS, wav])
        print(f"transcribiendo {f.name} ({dur(f):.0f} s)...", flush=True)
        r = subprocess.run([whisperx(), str(wav), "--language", wx["idioma"], "--model", wx["modelo"], "--compute_type",
                            wx["compute_type"], "--device", "cpu", "--output_format", "json", "--output_dir", str(TMP)])
        if r.returncode:
            sys.exit(f"WhisperX falló con {f.name}")
        shutil.copy2(TMP / f"{f.stem}.json", js)
    proponer(tomas)


def proponer(tomas):
    frases = []
    for f in tomas:
        js = DIR_T / f"{f.stem}.json"
        for s in json.loads(js.read_text(encoding="utf-8"))["segments"]:
            frases.append({"archivo": f.name, "desde": round(s["start"], 2), "hasta": round(s["end"], 2), "texto": s["text"].strip()})
    for i, fr in enumerate(frases):   # una frase que se vuelve a decir más adelante es una toma fallida
        a = " ".join(norm(fr["texto"]))
        for j in range(i + 1, min(len(frases), i + 12)):
            b = " ".join(norm(frases[j]["texto"]))
            if a and difflib.SequenceMatcher(None, a, b).ratio() > 0.72 or (len(a) > 12 and b.startswith(a[: len(a) // 2])):
                fr["repetida_en"] = f"{frases[j]['archivo']}@{frases[j]['desde']}"
                break
    md = [f"# Tomas de {pr.id}", "", "Frases en orden de grabación. ✗ = se repite después (toma fallida); se propone quedarse con la última.", ""]
    actual = None
    for fr in frases:
        if fr["archivo"] != actual:
            actual = fr["archivo"]
            md += ["", f"## {actual}"]
        marca = f" ✗ (se repite en {fr['repetida_en']})" if "repetida_en" in fr else ""
        md.append(f"- {fr['desde']:7.2f}–{fr['hasta']:7.2f}  {fr['texto']}{marca}")
    (pr.dir / "06_RECETA" / "tomas.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    orden, ult = [], None
    for fr in frases:
        if "repetida_en" in fr:
            continue
        if ult and ult["archivo"] == fr["archivo"] and fr["desde"] - ult["hasta"] < 1.5:
            ult["hasta"] = fr["hasta"]
        else:
            ult = {"archivo": fr["archivo"], "desde": fr["desde"], "hasta": fr["hasta"]}
            orden.append(ult)
    (pr.dir / "06_RECETA" / "orden_propuesto.json").write_text(json.dumps(orden, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(frases)} frases; {sum('repetida_en' in f for f in frases)} marcadas como repetidas. "
          f"Revisar 06_RECETA/tomas.md y, si hace falta, copiar/ajustar el orden en proyecto.json -> grabado.orden", flush=True)


# ---------- 2. cortar ----------
def cortar():
    orden = G.get("orden") or json.loads((pr.dir / "06_RECETA" / "orden_propuesto.json").read_text(encoding="utf-8"))
    mul = MULETILLAS | {norm(m)[0] for m in G["muletillas_extra"] if len(norm(m)) == 1}
    mul_multi = [norm(m) for m in G["muletillas_extra"] if len(norm(m)) > 1]
    pmax, mg = float(G["pausa_max"]), float(G["margen"])
    cortes, quitado, salida_segs, t_out = [], [], [], 0.0
    cache = {}
    for pieza in orden:
        arch = pieza["archivo"]
        if arch not in cache:
            cache[arch] = json.loads((DIR_T / f"{Path(arch).stem}.json").read_text(encoding="utf-8"))["segments"]
        segs = cache[arch]
        ws = [dict(w, seg=k) for k, s in enumerate(segs) for w in s.get("words", []) if "start" in w
              and w["start"] >= pieza["desde"] - 0.05 and w["end"] <= pieza["hasta"] + 0.3]
        toks = [tok(w["word"]) for w in ws]
        fuera = set()
        for i, t in enumerate(toks):
            if t in mul or w_corta(ws[i]["word"]):
                fuera.add(i)
            elif i + 1 < len(toks) and t and t == toks[i + 1]:      # "el el", "que que": traba
                fuera.add(i)
        for m in mul_multi:
            for i in range(len(toks) - len(m) + 1):
                if toks[i:i + len(m)] == m:
                    fuera.update(range(i, i + len(m)))
        for i in sorted(fuera):   # si se saca la primera palabra de una frase, la siguiente pasa a mayúscula
            sig = next((j for j in range(i + 1, len(ws)) if j not in fuera), None)
            if sig is not None and ws[i]["word"][:1].isupper() and ws[sig]["word"][:1].islower():
                ws[sig]["word"] = ws[sig]["word"][:1].upper() + ws[sig]["word"][1:]
        for i in sorted(fuera):
            quitado.append(f"{arch} {ws[i]['start']:.2f}  «{ws[i]['word']}»")
        bloques, bloque = [], []
        for i, w in enumerate(ws):
            if i in fuera:
                if bloque:
                    bloques.append(bloque); bloque = []
                continue
            if bloque and w["start"] - bloque[-1]["end"] > pmax:
                quitado.append(f"{arch} {bloque[-1]['end']:.2f}  pausa de {w['start'] - bloque[-1]['end']:.1f} s")
                bloques.append(bloque); bloque = []
            bloque.append(w)
        if bloque:
            bloques.append(bloque)
        for k, bl in enumerate(bloques):
            a = bl[0]["start"] - mg
            b = bl[-1]["end"] + mg
            if k and a < cortes[-1]["b"] and cortes[-1]["archivo"] == arch:
                a = (cortes[-1]["b"] + a) / 2
            a = max(a, pieza["desde"] - 0.1, 0)
            if cortes and cortes[-1]["archivo"] == arch and a - cortes[-1]["b"] < 0.12:   # casi seguidos: se unen
                c = cortes[-1]
                t_out += b - c["b"]
                c["b"] = b
                c["palabras"] += bl
                continue
            cortes.append({"archivo": arch, "a": round(a, 3), "b": round(b, 3), "salida": round(t_out, 3), "palabras": list(bl)})
            t_out += b - a
    # transcripción en el tiempo del video editado, agrupada por las frases originales
    final, clave = [], None
    for c in cortes:
        for w in c["palabras"]:
            nw = {"word": w["word"], "start": round(w["start"] - c["a"] + c["salida"], 3), "end": round(w["end"] - c["a"] + c["salida"], 3)}
            k = (c["archivo"], w["seg"])
            if k != clave:
                final.append({"start": nw["start"], "end": nw["end"], "text": "", "words": []}); clave = k
            final[-1]["words"].append(nw)
            final[-1]["end"] = nw["end"]
    for s in final:
        s["text"] = " ".join(w["word"] for w in s["words"])
    destino = pr.dir / "06_RECETA" / "transcripcion.json"
    if destino.exists():
        shutil.copy2(destino, nombre_libre(destino.with_name("transcripcion_antes_grabado.json")))   # cada pasada guarda su respaldo
    destino.write_text(json.dumps({"segments": final, "origen": "grabado.py"}, ensure_ascii=False, indent=1), encoding="utf-8")
    original = sum(p["hasta"] - p["desde"] for p in orden)
    limpio = [{k: v for k, v in c.items() if k != "palabras"} for c in cortes]
    (pr.dir / "06_RECETA" / "cortes.json").write_text(json.dumps(limpio, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# Cortes de {pr.id}", "", f"Tomas elegidas: {original:.0f} s → editado: {t_out:.0f} s ({len(cortes)} tramos).", "",
          "## Lo que se quita", *[f"- {q}" for q in quitado], "", "## Tramos", *[f"- {c['salida']:7.2f}  {c['archivo']} {c['a']:.2f}–{c['b']:.2f}" for c in limpio]]
    (pr.dir / "06_RECETA" / "cortes.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(cortes)} tramos, {original:.0f} s → {t_out:.0f} s; se quitan {len(quitado)} muletillas, trabas o pausas. "
          "Ver 06_RECETA/cortes.md. Transcripción final lista para subtítulos.", flush=True)


def w_corta(w):
    return w.strip().endswith("-") and len(w.strip()) > 1      # palabra cortada: "inver-"


# ---------- 3. armar ----------
def stats(ruta, look, luz=""):
    vals = {"Y": [], "S": []}
    d = dur(ruta)
    for f in (0.2, 0.5, 0.8):
        r = subprocess.run([FFMPEG, "-v", "info", "-ss", f"{d * f:.2f}", "-i", str(ruta), "-frames:v", "1", "-vf",
                            cadena(ruta, look, luz=luz) + ",signalstats,metadata=print", "-f", "null", "-"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        y = re.findall(r"signalstats\.YAVG=([\d.]+)", r.stderr)
        s = re.findall(r"signalstats\.SATAVG=([\d.]+)", r.stderr)
        if y and s:
            vals["Y"].append(float(y[-1])); vals["S"].append(float(s[-1]))
    return (sum(vals["Y"]) / len(vals["Y"]), sum(vals["S"]) / len(vals["S"])) if vals["Y"] else (None, None)


# ---------- 3b. cámara virtual (0.15): ángulos desde una sola cámara, zooms de énfasis y encuadre sobre la cara ----------
LUZ = G.get("luz") or {}
ENF = G.get("enfasis") or {}
ANG = G.get("angulos") or {}
PLANOS = {"general": 1.0, "medio": 1.25, "cerrado": 1.5, **(ANG.get("zoom") or {})}     # zoom de cada plano


def cara_de_toma(ruta, rangos):
    """Dónde está la cara en lo que se usa de una toma: {"asp", "cx", "cy", "ancho", "alto"} (medianas, en fracción del
    cuadro ya girado; asp = ancho/alto del cuadro). Si no hay una cara estable solo trae "asp"; None si no se pudo mirar."""
    try:
        import caras
    except Exception as ex:
        print(f"AVISO cámara: no se pueden buscar caras ({ex}); el encuadre queda al centro", flush=True)
        return None
    tiempos = [a + (b - a) * f for a, b in sorted(rangos, key=lambda r: r[0] - r[1])[:4] for f in (0.25, 0.5, 0.75)][:8]
    vistas, asp, mirados = [], None, 0
    for t in tiempos:
        im = caras.cuadro(ruta, t)
        if im is None:
            continue
        mirados += 1
        asp = im.width / im.height
        c = caras.cara_principal(im)
        if c:
            vistas.append(c)
    if asp is None:
        return None
    if not vistas or len(vistas) * 2 < mirados:
        return {"asp": asp}
    med = lambda k: sorted(v[k] for v in vistas)[len(vistas) // 2]
    return {"asp": asp, "cx": med(0), "cy": med(1), "ancho": med(2), "alto": med(3)}


def zoom_max(cara):
    """Zoom más cerrado que deja la cabeza entera dentro del cuadro (con pelo y un poco de aire). Sin cara: sin tope."""
    if not cara or "cx" not in cara:
        return 9.0
    alto_rel = max(1.0, (W / H) / cara["asp"])        # alto de la toma escalada (zoom 1), medido en altos de salida
    ancho_rel = max(1.0, cara["asp"] / (W / H))
    return max(1.0, min(0.86 / (1.9 * cara["alto"] * alto_rel), 0.90 / (1.6 * cara["ancho"] * ancho_rel)))


def encuadre(z, cara, q=1):
    """Recorte de (W*q) x (H*q) sobre la toma escalada con zoom z, centrado en la cara si se conoce y sin cortar la
    cabeza. Devuelve (filtro "scale=...,crop=...", (fx, fy)): dónde queda el centro de la cara dentro del recorte."""
    Wq, Hq = W * q, H * q
    zw, zh = int(Wq * z) // 2 * 2, int(Hq * z) // 2 * 2
    esc = f"scale={zw}:{zh}:force_original_aspect_ratio=increase"
    if not cara or "cx" not in cara:
        return f"{esc},crop={Wq}:{Hq}:(iw-{Wq})/2:(ih-{Hq})/2", (0.5, 0.5)
    iw, ih = (zh * cara["asp"], zh) if cara["asp"] >= zw / zh else (zw, zw / cara["asp"])
    x = min(max(iw * cara["cx"] - Wq / 2, 0), max(iw - Wq, 0))
    y_cara = ih * cara["cy"] - 0.42 * Hq                                   # la cara un poco sobre el centro
    y_tope = ih * (cara["cy"] - 0.95 * cara["alto"]) - 0.03 * Hq           # la cabeza completa (con pelo) queda dentro
    y = min(max(min(y_cara, y_tope), 0), max(ih - Hq, 0))
    return f"{esc},crop={Wq}:{Hq}:{int(x)}:{int(y)}", ((iw * cara["cx"] - x) / Wq, (ih * cara["cy"] - y) / Hq)


class Camara:
    """Plan de cámara de todo el video (en el tiempo ya editado) y encuadre de cada pieza al armar."""

    def __init__(self, cortes, total):
        self.cortes, self.total, self.pz, self.notas = cortes, total, 1.0, []
        try:
            _, self.pals = palabras(pr)
        except (SystemExit, Exception):
            self.pals = []
            print("AVISO cámara: sin transcripción del video editado (corre «cortar»): solo se usan los cortes y las marcas por segundo", flush=True)
        self.caras = {}
        for a in dict.fromkeys(c["archivo"] for c in cortes):
            self.caras[a] = cara_de_toma(ruta_toma(a), [(c["a"], c["b"]) for c in cortes if c["archivo"] == a])
            ca = self.caras[a]
            print(f"cámara {a}: " + (f"cara en ({ca['cx']:.2f}, {ca['cy']:.2f}), alto {ca['alto']:.2f}; zoom máximo {zoom_max(ca):.2f}"
                                     if ca and "cx" in ca else "sin cara estable: encuadre al centro"), flush=True)
        self.cambios = self._angulos()
        self.enf = self._enfasis()
        self.usados = set()

    def _angulos(self):
        """[(segundo, plano, "inicio" | "corte" | "pausa")]: en qué momento se pasa a cada plano."""
        planos = [p for p in ANG.get("planos", ["general", "medio", "cerrado"]) if p in PLANOS] or ["general"]
        if not ANG or ANG.get("modo") == "fijo" or len(planos) < 2:
            return [(0.0, planos[0] if ANG else "general", "inicio")]
        cc = ANG.get("cambio_cada", [4, 9])
        lo, hi = (float(cc[0]), float(cc[-1])) if isinstance(cc, (list, tuple)) else (float(cc), float(cc))
        donde, pausa = ANG.get("cambia_en", "ambos"), float(ANG.get("pausa", 0.22))
        t_cortes = [c["salida"] for c in self.cortes[1:]]
        cand = [(t, "corte") for t in t_cortes] if donde in ("ambos", "cortes") else []
        if donde in ("ambos", "pausas"):
            for w, w2 in zip(self.pals, self.pals[1:]):
                t = (w["end"] + w2["start"]) / 2
                fin_frase = w["word"].rstrip("»\"'”)").endswith((".", "?", "!", "…"))
                if (w2["start"] - w["end"] >= pausa or fin_frase) and all(abs(t - s) > 0.4 for s in t_cortes):
                    cand.append((t, "pausa"))
        rng = random.Random(15)                       # siempre el mismo plan para el mismo video
        cambios, actual, previo, t_ult, objetivo = [(0.0, planos[0], "inicio")], planos[0], None, 0.0, rng.uniform(lo, hi)
        for t, tipo in sorted(cand):
            if t >= self.total - lo:                  # no cambiar justo antes del final
                break
            if t - t_ult >= (lo if tipo == "corte" else objetivo):      # en un corte basta el mínimo: ahí el cambio ayuda
                if ANG.get("modo", "alternar") == "variar":
                    otros = [p for p in planos if p != actual and (p != previo or len(planos) < 3)]
                    sig = rng.choice(otros)
                else:                                 # alternar: en el orden de la lista, en ronda
                    sig = planos[(planos.index(actual) + 1) % len(planos)]
                previo, actual = actual, sig
                cambios.append((t, actual, tipo)); t_ult, objetivo = t, rng.uniform(lo, hi)
        return cambios

    def _enfasis(self):
        """[(segundo de la palabra o marca, motivo)]: dónde va un zoom de énfasis, ya con los límites de frecuencia."""
        if not ENF:
            return []
        marcas = []
        for mk in ENF.get("marcas", []):
            try:
                t = float(mk["segundo"]) if "segundo" in mk else buscar(self.pals, mk["frase"])
                marcas.append((t + float(mk.get("desfase", 0)), "marca"))
            except (ValueError, KeyError) as ex:
                print("AVISO énfasis: marca sin momento:", ex, flush=True)
        lista = list(ENF.get("palabras") or [])
        if ENF.get("claves", not lista and not ENF.get("marcas")):     # sin lista propia ni marcas: las palabras clave
            lista += pr.cfg.get("subtitulos", {}).get("palabras_clave", [])
        toks, halladas = [tok(w["word"]) for w in self.pals], []
        for obj in [norm(x) for x in lista if norm(x)]:
            for i in range(len(toks) - len(obj) + 1):
                if toks[i:i + len(obj)] == obj:
                    halladas.append((self.pals[i]["start"], " ".join(obj)))
        sep, tope = float(ENF.get("separacion", 4)), int(ENF.get("max_por_min", 6))
        ok = sorted(marcas)                            # las marcas puestas a mano siempre entran
        for t, motivo in sorted(halladas):
            if all(abs(t - u) >= sep for u, _ in ok) and sum(1 for u, _ in ok if abs(u - t) < 30) < tope:
                ok.append((t, motivo))
        return sorted(ok)

    def piezas(self, i, f0, n):
        """Divide los n cuadros del tramo i (que parte en el cuadro f0 del video) en piezas con su encuadre:
        [{"k0": cuadro inicial dentro del tramo, "n": cuadros, "z": zoom, "plano", "cara", "enf": None o
        (cuadros de entrada, cuadro donde empieza a salir o None, zoom extra), "nota"}]."""
        c = self.cortes
        arch, ini = c[i]["archivo"], c[i]["salida"]
        fin = c[i + 1]["salida"] if i + 1 < len(c) else self.total
        cara = self.caras.get(arch)
        plano_en = lambda t: [p for s, p, _ in self.cambios if s <= t + 1e-6][-1]
        cambio_aqui = any(tipo == "corte" and abs(s - ini) < 1e-6 for s, _, tipo in self.cambios)     # el ángulo cambia en este corte
        punch = float(G["punch"])
        if i > 0 and c[i - 1]["archivo"] == arch and not cambio_aqui and punch > 1:
            self.pz = punch if self.pz == 1.0 else 1.0        # corte en el mismo plano sin cambio de ángulo: punch alternado
        else:
            self.pz = 1.0
        inicios = [(0, ini)] + [(k, s) for k, s in ((round(s * FPS) - f0, s) for s, _, tipo in self.cambios
                                                    if tipo == "pausa" and ini + 0.2 < s < fin - 0.2) if 6 < k < n - 6]
        zoom_e, dura = float(ENF.get("zoom", 1.12)), float(ENF.get("dura", 0.6))
        NI, sost = max(2, round(dura * FPS)), round(float(ENF.get("sostiene", 1.2)) * FPS)
        out = []
        for j, (k0, t_ref) in enumerate(inicios):
            k1 = inicios[j + 1][0] if j + 1 < len(inicios) else n
            plano = plano_en(t_ref)
            pedido = PLANOS[plano] * (self.pz if j == 0 else 1.0)
            z = max(1.0, min(pedido, zoom_max(cara)))
            if z < pedido - 0.01:
                self.notas.append(f"{ini + k0 / FPS:7.2f}  plano {plano}: zoom {pedido:.2f} bajado a {z:.2f} para no cortar la cabeza")
            base = {"z": z, "plano": plano, "cara": cara, "enf": None, "nota": "punch" if j == 0 and self.pz > 1 else ""}
            cursor, a_s, b_s = k0, (f0 + k0) / FPS, (f0 + k1) / FPS
            for n_e, (t, motivo) in enumerate(self.enf):
                if n_e in self.usados or not (a_s <= t < b_s):
                    continue
                self.usados.add(n_e)
                ki = max(round((t - dura * 0.5) * FPS) - f0, k0 + round(0.3 * FPS), cursor)     # lejos del corte anterior
                z_e = min(zoom_e, zoom_max(cara) / z)
                if ki / FPS + f0 / FPS > t + 0.4 or k1 - ki < NI + round(0.5 * FPS) or z_e < 1.03:
                    self.notas.append(f"{t:7.2f}  énfasis «{motivo}» omitido: " + ("ya no cabe sin cortar la cabeza" if z_e < 1.03 else "muy cerca de un corte"))
                    continue
                kf = ki + NI + sost + NI
                sale = NI + sost
                if k1 - kf < round(0.4 * FPS):        # el corte llega antes: se queda cerca hasta el corte (el corte lo suelta)
                    kf, sale = k1, None
                if ki > cursor:
                    out.append({**base, "k0": cursor, "n": ki - cursor})
                out.append({**base, "k0": ki, "n": kf - ki, "enf": (NI, sale, z_e), "nota": f"énfasis «{motivo}»"})
                cursor = kf
            if k1 > cursor:
                out.append({**base, "k0": cursor, "n": k1 - cursor})
            if j + 1 < len(inicios):
                self.pz = 1.0                          # después de un cambio de ángulo en una pausa, el punch parte de nuevo
        return out

    def filtro(self, p, color_vf):
        """Filtro de ffmpeg de una pieza: color + encuadre fijo, o encuadre con zoom suave (ease) si lleva énfasis."""
        if not p["enf"]:
            enc, _ = encuadre(p["z"], p["cara"])
            return f"{color_vf},{enc},fps={FPS},setsar=1,format=yuv420p"
        NI, sale, z_e = p["enf"]
        enc, (fx, fy) = encuadre(p["z"], p["cara"], 2)        # al doble de tamaño: el zoom no pierde nitidez ni tiembla
        suave = lambda u: f"({u})*({u})*(3-2*({u}))"           # entra y sale con ease (smoothstep)
        zexp = f"1+{z_e - 1:.4f}*({suave(f'clip(on/{NI},0,1)')}" + (f"-{suave(f'clip((on-{sale})/{NI},0,1)')}" if sale is not None else "") + ")"
        return (f"{color_vf},{enc},fps={FPS},zoompan=z='{zexp}':x='max(0,min(iw-iw/zoom,iw*{fx:.4f}-iw/zoom/2))':"
                f"y='max(0,min(ih-ih/zoom,ih*{fy:.4f}-ih/zoom/2))':d=1:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p")

    def informe(self):
        md = [f"# Cámara de {pr.id}", "", "Prioridad: 1) ángulos  2) punch (corte en el mismo plano sin cambio de ángulo)  3) énfasis.", "",
              "## Cambios de plano", *[f"- {t:7.2f}  {p}  ({tipo})" for t, p, tipo in self.cambios], "",
              "## Énfasis previstos", *[f"- {t:7.2f}  {m}" for t, m in self.enf], "",
              "## Notas (lo que se ajustó u omitió)", *[f"- {x}" for x in self.notas]]
        (pr.dir / "06_RECETA" / "camara.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def armar():
    cortes = json.loads((pr.dir / "06_RECETA" / "cortes.json").read_text(encoding="utf-8"))
    if "--borrador" in sys.argv:
        limite = float(sys.argv[sys.argv.index("--borrador") + 1])
        cortes = [c for c in cortes if c["salida"] < limite]
    TMP.mkdir(parents=True, exist_ok=True)
    look = G["look"]
    archivos = list(dict.fromkeys(c["archivo"] for c in cortes))
    ref = G.get("referencia_color") or max(archivos, key=lambda a: sum(c["b"] - c["a"] for c in cortes if c["archivo"] == a))
    luces = {}                     # 0.15: iluminación automática por toma (luz.py); va después del HDR->SDR y antes del look
    if LUZ.get("auto"):
        import luz as _luz
        informes = {}
        for a in archivos:
            usados = [(c["a"], c["b"]) for c in cortes if c["archivo"] == a]
            luces[a], informes[a] = _luz.para_toma(ruta_toma(a), LUZ, min(u[0] for u in usados), max(u[1] for u in usados))
            print(f"luz {a}: {informes[a]['resumen']}", flush=True)
        (TMP / "luz.json").write_text(json.dumps(informes, ensure_ascii=False, indent=1), encoding="utf-8")
    st = {a: stats(ruta_toma(a), look, luces.get(a, "")) for a in archivos}
    yr, sr = st[ref]
    ajuste = {}
    for a, (y, s) in st.items():   # igualar brillo y saturación con la toma de referencia
        if y is None or yr is None:
            ajuste[a] = ""
        else:
            ajuste[a] = f",eq=brightness={max(-0.12, min(0.12, (yr - y) / 255)):.3f}:saturation={max(0.8, min(1.25, sr / max(s, 1))):.3f}"
        print(f"color {a}: brillo {y and round(y)} saturación {s and round(s)}{'  (referencia)' if a == ref else ''}", flush=True)
    jl, punch = float(G["jl"]), float(G["punch"])
    lista_v, lista_a, zoom = [], [], 1.0
    total = cortes[-1]["salida"] + cortes[-1]["b"] - cortes[-1]["a"]
    cam = Camara(cortes, total) if (ENF or ANG) else None      # 0.15: sin "enfasis" ni "angulos", el encuadre de siempre
    for i, c in enumerate(cortes):
        ruta = ruta_toma(c["archivo"])
        mismo_antes = i > 0 and cortes[i - 1]["archivo"] == c["archivo"]
        zoom = (punch if zoom == 1.0 else 1.0) if mismo_antes and punch > 1 else 1.0   # salto de corte -> cambia el encuadre
        # J/L solo entre planos distintos (en el mismo plano se notaría que la boca no calza)
        da = -jl if i > 0 and not mismo_antes and jl else 0.0
        db = -jl if i + 1 < len(cortes) and cortes[i + 1]["archivo"] != c["archivo"] and jl else 0.0
        f0 = round((c["salida"] + (da if i else 0)) * FPS)
        fin_salida = cortes[i + 1]["salida"] + db if i + 1 < len(cortes) else total
        n = round(fin_salida * FPS) - f0
        color_vf = f"{cadena(ruta, look, luz=luces.get(c['archivo'], ''))}{ajuste[c['archivo']]}"
        nota_cam = ""
        if cam is None:
            zw, zh = int(W * zoom) // 2 * 2, int(H * zoom) // 2 * 2
            vf = (f"{color_vf},scale={zw}:{zh}:force_original_aspect_ratio=increase,"
                  f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2,fps={FPS},setsar=1,format=yuv420p")
            v = TMP / f"v_{i:03d}.mp4"
            run([FFMPEG, "-v", "error", "-y", "-ss", f"{max(0, c['a'] + da):.3f}", "-i", ruta, "-an", "-vf", vf, "-frames:v", str(n),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-r", str(FPS), *SIN_METADATOS, v])
            lista_v.append(v)
        else:                       # cámara virtual: el tramo se arma en piezas, cada una con su encuadre
            zoom = 1.0
            piezas = cam.piezas(i, f0, n)
            for k, p in enumerate(piezas):
                v = TMP / f"v_{i:03d}_{k:02d}.mp4"
                run([FFMPEG, "-v", "error", "-y", "-ss", f"{max(0, c['a'] + da) + p['k0'] / FPS:.3f}", "-i", ruta, "-an",
                     "-vf", cam.filtro(p, color_vf), "-frames:v", str(p["n"]),
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-r", str(FPS), *SIN_METADATOS, v])
                lista_v.append(v)
            nota_cam = "  " + " · ".join(dict.fromkeys(f"{p['plano']} x{p['z']:.2f}" + (f" ({p['nota']})" if p["nota"] else "") for p in piezas))
        a_ = TMP / f"a_{i:03d}.wav"
        d = c["b"] - c["a"]
        run([FFMPEG, "-v", "error", "-y", "-ss", f"{c['a']:.3f}", "-t", f"{d:.3f}", "-i", ruta, "-vn", "-af",
             f"afade=t=in:d=0.012,afade=t=out:st={max(0, d - 0.012):.3f}:d=0.012", "-ac", "2", "-ar", "48000", *SIN_METADATOS, a_])
        lista_a.append(a_)
        print(f"  tramo {i + 1}/{len(cortes)}  {c['archivo']} {c['a']:.1f}-{c['b']:.1f}{'  punch-in' if zoom > 1 else ''}{nota_cam}", flush=True)
    if cam is not None:
        cam.informe()
        print(f"cámara: {len(cam.cambios) - 1} cambios de plano, {sum(1 for x in cam.notas if 'omitido' in x)} énfasis omitidos de "
              f"{len(cam.enf)}; detalle en 06_RECETA/camara.md", flush=True)
    (TMP / "v.txt").write_text("".join(f"file '{p.name}'\n" for p in lista_v), encoding="utf-8")
    (TMP / "a.txt").write_text("".join(f"file '{p.name}'\n" for p in lista_a), encoding="utf-8")
    nombre_v = "solo_video_borrador_{}s.mp4".format(int(limite)) if "--borrador" in sys.argv else "solo_video.mp4"
    apoyos = pr.cfg.get("apoyo") or []          # 0.15: material de apoyo encima de la persona (la voz sigue debajo)
    run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "v.txt", "-c", "copy", *SIN_METADATOS,
         "base_sin_apoyo.mp4" if apoyos else f"../{nombre_v}"], cwd=TMP)
    if apoyos:
        import apoyo as _ap
        puestos = _ap.aplicar(pr, TMP / "base_sin_apoyo.mp4", pr.tmp / nombre_v, apoyos, W, H, FPS)
        print(f"apoyo: {len(puestos)} de {len(apoyos)} inserciones puestas (tmp/apoyo_aplicado.json)", flush=True)
    (pr.tmp / (Path(nombre_v).stem + ".json")).write_text(json.dumps({"clips": {}, "origen": "grabado.py", "tramos": len(cortes)}), encoding="utf-8")
    lv = G["limpiar_voz"]          # true (básica), false, o "suave" / "media" / "fuerte" / "radio" (audio.py)
    if isinstance(lv, str):
        import audio as _au
        limpia = _au.cadena_voz(None if lv == "radio" else lv, lv == "radio") or "anull"
    else:
        limpia = "highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120" if lv else "anull"
    borr = f"_borrador-{int(limite)}s" if "--borrador" in sys.argv else ""     # el borrador nunca reemplaza la voz completa
    voz = pr.dir / "02_VOZ" / f"{pr.id}_voz-grabado{borr}.wav"
    voz.parent.mkdir(exist_ok=True)
    parcial = parcial_de(voz)                 # la voz editada anterior queda como *_anterior-<fecha>
    run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "a.txt", "-af", limpia, *SIN_METADATOS, str(parcial)], cwd=TMP)
    entregar(parcial, voz)
    cfg_f = pr.dir / "proyecto.json"
    cfg = json.loads(cfg_f.read_text(encoding="utf-8"))
    if not borr and cfg.get("audios") != f"02_VOZ/{voz.name}":     # el borrador no cambia la voz del proyecto
        shutil.copy2(cfg_f, nombre_libre(cfg_f.with_name("proyecto_antes_grabado.json")))       # respaldo antes de cambiarlo
        cfg["audios"] = f"02_VOZ/{voz.name}"
        cfg.setdefault("carpetas", {})["transcripcion"] = "06_RECETA/transcripcion.json"
        cfg_f.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"LISTO {pr.tmp / nombre_v} + {voz.name} ({total:.0f} s). Siguiente: terminar.py (subtítulos, capa viva, volumen) "
          "y vertical.py para los cortes.", flush=True)


if __name__ == "__main__":
    paso = next((a for a in sys.argv[1:] if a in ("transcribir", "cortar", "armar", "proponer")), None)
    if paso == "transcribir":
        transcribir()
    elif paso == "proponer":
        proponer(material()[1])
    elif paso == "cortar":
        cortar()
    elif paso == "armar":
        armar()
    else:
        sys.exit(__doc__ or "uso: python grabado.py \"<proyecto>\" transcribir | cortar | armar [--borrador 60]")
