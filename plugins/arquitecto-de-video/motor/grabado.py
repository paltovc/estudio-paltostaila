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
import difflib, json, re, shutil, subprocess, sys
from pathlib import Path
from estudio import Proyecto, FFMPEG, FFPROBE, run, norm
from color import cadena

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
        run([FFMPEG, "-v", "error", "-y", "-i", f, "-vn", "-ac", "1", "-ar", "16000", wav])
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
        shutil.copy2(destino, destino.with_name("transcripcion_antes_grabado.json"))
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
def stats(ruta, look):
    vals = {"Y": [], "S": []}
    d = dur(ruta)
    for f in (0.2, 0.5, 0.8):
        r = subprocess.run([FFMPEG, "-v", "info", "-ss", f"{d * f:.2f}", "-i", str(ruta), "-frames:v", "1", "-vf",
                            cadena(ruta, look) + ",signalstats,metadata=print", "-f", "null", "-"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        y = re.findall(r"signalstats\.YAVG=([\d.]+)", r.stderr)
        s = re.findall(r"signalstats\.SATAVG=([\d.]+)", r.stderr)
        if y and s:
            vals["Y"].append(float(y[-1])); vals["S"].append(float(s[-1]))
    return (sum(vals["Y"]) / len(vals["Y"]), sum(vals["S"]) / len(vals["S"])) if vals["Y"] else (None, None)


def armar():
    cortes = json.loads((pr.dir / "06_RECETA" / "cortes.json").read_text(encoding="utf-8"))
    if "--borrador" in sys.argv:
        limite = float(sys.argv[sys.argv.index("--borrador") + 1])
        cortes = [c for c in cortes if c["salida"] < limite]
    TMP.mkdir(parents=True, exist_ok=True)
    look = G["look"]
    archivos = list(dict.fromkeys(c["archivo"] for c in cortes))
    ref = G.get("referencia_color") or max(archivos, key=lambda a: sum(c["b"] - c["a"] for c in cortes if c["archivo"] == a))
    st = {a: stats(ruta_toma(a), look) for a in archivos}
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
        zw, zh = int(W * zoom) // 2 * 2, int(H * zoom) // 2 * 2
        vf = (f"{cadena(ruta, look)}{ajuste[c['archivo']]},scale={zw}:{zh}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2,fps={FPS},setsar=1,format=yuv420p")
        v = TMP / f"v_{i:03d}.mp4"
        run([FFMPEG, "-v", "error", "-y", "-ss", f"{max(0, c['a'] + da):.3f}", "-i", ruta, "-an", "-vf", vf, "-frames:v", str(n),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-r", str(FPS), v])
        a_ = TMP / f"a_{i:03d}.wav"
        d = c["b"] - c["a"]
        run([FFMPEG, "-v", "error", "-y", "-ss", f"{c['a']:.3f}", "-t", f"{d:.3f}", "-i", ruta, "-vn", "-af",
             f"afade=t=in:d=0.012,afade=t=out:st={max(0, d - 0.012):.3f}:d=0.012", "-ac", "2", "-ar", "48000", a_])
        lista_v.append(v); lista_a.append(a_)
        print(f"  tramo {i + 1}/{len(cortes)}  {c['archivo']} {c['a']:.1f}-{c['b']:.1f}{'  punch-in' if zoom > 1 else ''}", flush=True)
    (TMP / "v.txt").write_text("".join(f"file '{p.name}'\n" for p in lista_v), encoding="utf-8")
    (TMP / "a.txt").write_text("".join(f"file '{p.name}'\n" for p in lista_a), encoding="utf-8")
    nombre_v = "solo_video_borrador_{}s.mp4".format(int(limite)) if "--borrador" in sys.argv else "solo_video.mp4"
    run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "v.txt", "-c", "copy", f"../{nombre_v}"], cwd=TMP)
    (pr.tmp / (Path(nombre_v).stem + ".json")).write_text(json.dumps({"clips": {}, "origen": "grabado.py", "tramos": len(cortes)}), encoding="utf-8")
    limpia = "highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120" if G["limpiar_voz"] else "anull"
    voz = pr.dir / "02_VOZ" / f"{pr.id}_voz-grabado.wav"
    voz.parent.mkdir(exist_ok=True)
    run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "a.txt", "-af", limpia, str(voz)], cwd=TMP)
    cfg_f = pr.dir / "proyecto.json"
    cfg = json.loads(cfg_f.read_text(encoding="utf-8"))
    if cfg.get("audios") != f"02_VOZ/{voz.name}":
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
