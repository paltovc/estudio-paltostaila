# Evaluador de un video antes de terminarlo: mide lo que se puede medir, pone nota por ejes, clasifica y propone
# mejoras con su minuto. El agente "evaluador" completa lo que no se mide (claridad de la promesa, emoción, empaque).
# Ninguna nota garantiza que un video se viralice: mide qué tan preparado está frente a lo que suele funcionar.
#   python evaluar.py "<proyecto>" [--video "<final>.mp4"] [--tipo largo|short]
# Deja en <proyecto>\06_RECETA: evaluacion_<video>.md y .json (y la carpeta ritmo_<video> con el gráfico y las hojas).
import json, re, statistics, sys
from pathlib import Path
from estudio import Proyecto, FFMPEG, FFPROBE, run, palabras, buscar, norm
import ritmo

pr = Proyecto()
mmss = lambda t: f"{int(t // 60)}:{int(t % 60):02d}"
A = sys.argv[1:]
opt = lambda k, d=None: A[A.index(k) + 1] if k in A else d

RIESGOS = ["garantizado", "garantizada", "sin riesgo", "hazte rico", "hacerte rico", "dinero fácil", "100% seguro", "seguro que ganas",
           "nunca pierdes", "duplica tu dinero", "rentabilidad asegurada", "secreto que los bancos", "libertad financiera en"]
BUCLES = ["más adelante", "al final", "lo tercero", "lo más importante", "pero hay algo", "ahora vamos", "y aquí viene", "quédate",
          "te voy a mostrar", "primera pregunta", "segunda pregunta", "tercera pregunta"]
CIERRE = ["comenta", "comentarios", "suscríbete", "suscribete", "próximo video", "siguiente video", "sígueme", "guarda este"]


def elegir_video():
    if opt("--video"):
        return Path(opt("--video"))
    for patron in ("*_con-subtitulos.mp4", "*_youtube.mp4", "*_9x16.mp4", "*_vertical.mp4", "*.mp4"):
        c = sorted((f for f in pr.salida.glob(patron) if ".parcial" not in f.name and "prueba" not in f.name),
                   key=lambda f: -f.stat().st_mtime)
        if c:
            return c[0]
    sys.exit("No hay un video en 07_RENDER: indicar --video")


def dims(v):
    w, h = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", v]).strip().split(",")[:2]
    return int(w), int(h)


def volumen(v):
    s = run([FFMPEG, "-hide_banner", "-i", v, "-af", "ebur128=peak=true", "-f", "null", "-"])
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", s)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", s)
    return (float(i[-1]) if i else None), (float(p[-1]) if p else None)


def nota(valor, ideal_min, ideal_max, malo_min, malo_max):
    """10 dentro del rango ideal, bajando hasta 2 en los bordes malos."""
    if valor is None:
        return None
    if ideal_min <= valor <= ideal_max:
        return 10.0
    if valor < ideal_min:
        return max(2.0, 10 - 8 * (ideal_min - valor) / max(ideal_min - malo_min, 1e-6))
    return max(2.0, 10 - 8 * (valor - ideal_max) / max(malo_max - ideal_max, 1e-6))


def momentos_short(pals, frases, elementos, dur_total, largo=(30, 58)):
    """Ventanas de 30-58 s que empiezan en una frase y tienen más densidad de palabras clave, números, preguntas y elementos."""
    claves = {norm(x)[0] for x in pr["subtitulos"].get("palabras_clave", []) if norm(x)}
    cand = []
    for f in frases:
        a = f["start"]
        fin = next((g["end"] for g in frases if g["end"] - a >= largo[0] and g["end"] - a <= largo[1]), None)
        if fin is None or fin > dur_total:
            continue
        ws = [w for w in pals if a <= w.get("start", -1) < fin]
        puntos = sum(1 for w in ws if (norm(w["word"]) or [""])[0] in claves or re.search(r"\d", w["word"]))
        puntos += 2 * sum(1 for g in frases if a <= g["start"] < fin and g["text"].strip().endswith("?"))
        puntos += 1.5 * sum(1 for e in elementos if a <= e.get("a", -1) < fin)
        arranque = 3 if f["text"].strip().endswith("?") or re.search(r"\d", f["text"]) else 0
        cand.append((puntos / ((fin - a) / 60) + arranque, a, fin, f["text"].strip()))
    cand.sort(reverse=True)
    elegidos = []
    for c in cand:
        if all(abs(c[1] - e[1]) > 40 for e in elegidos):
            elegidos.append(c)
        if len(elegidos) == 3:
            break
    return [{"desde_s": round(a, 2), "hasta_s": round(b, 2), "dura_s": round(b - a, 1), "empieza": t[:90], "densidad": round(p, 1)}
            for p, a, b, t in elegidos]


def main():
    video = elegir_video()
    w, h = dims(video)
    tipo = opt("--tipo") or ("short" if h > w else "largo")
    segs, pals = palabras(pr)
    pals = [p for p in pals if "start" in p]
    frases = [s for s in segs if s.get("text")]
    r, vol, carpeta_ritmo = ritmo.analizar(video, pr.dir / "06_RECETA" / f"ritmo_{video.stem}")
    ritmo.grafico([(r, vol)], carpeta_ritmo / "ritmo.png")
    ritmo.informe(r, carpeta_ritmo)
    dur = r["duracion_s"]
    lufs, pico = volumen(video)
    import vivo
    v = vivo.Vivo(pr, pals, w, h, vertical=h > w) if pals else None
    elementos = [e for e in (v.linea_de_tiempo() if v else []) if "a" in e]
    texto = " ".join(p["word"] for p in pals).lower()
    mejoras, ejes = [], {}

    # 1. GANCHO
    primera = pals[0]["start"] if pals else None
    pal_5s = sum(1 for p in pals if p["start"] < 5)
    frase1 = frases[0]["text"].strip() if frases else ""
    claves = [norm(x)[0] for x in pr["subtitulos"].get("palabras_clave", []) if norm(x)]
    t_clave = next((p["start"] for p in pals if (norm(p["word"]) or [""])[0] in claves or re.search(r"\d", p["word"])), None)
    g = []
    g.append(10 if primera is not None and primera <= 0.6 else 5 if primera is not None and primera <= 1.5 else 2)
    if primera is not None and primera > 0.6:
        mejoras.append((0, "gancho", f"La voz empieza en el segundo {primera:.1f}: que la primera palabra suene antes de 0,5 s."))
    g.append(nota(pal_5s, 10, 16, 3, 24))
    cortes3 = r["cortes_primeros_3s"] + sum(1 for m in r["momentos_suaves"] if m <= 3)
    obj3 = (2, 4) if tipo == "short" else (1, 3)
    g.append(nota(cortes3 + sum(1 for e in elementos if e["a"] <= 3), obj3[0], 6, 0, 10))
    if cortes3 + sum(1 for e in elementos if e["a"] <= 3) < obj3[0]:
        mejoras.append((0, "gancho", "En los primeros 3 s no cambia nada en pantalla: agregar un corte, un acercamiento o un elemento de la capa viva en la palabra clave del gancho."))
    largo_f1 = len(frase1.split())
    g.append(10 if 4 <= largo_f1 <= 14 else 6 if largo_f1 <= 20 else 3)
    if largo_f1 > 14:
        mejoras.append((0, "gancho", f"La primera frase tiene {largo_f1} palabras: partirla; el gancho se entiende mejor en menos de 12."))
    abre = bool(re.search(r"\?|\d|\btú\b|\btu\b|\bte\b|nunca|error|nadie|todos|antes de", frase1.lower()))
    g.append(9 if abre else 5)
    if not abre:
        mejoras.append((0, "gancho", "La primera frase no abre una pregunta, una cifra ni le habla directo a la persona: probar un gancho a la contra o con una pregunta."))
    if t_clave is None or t_clave > 8:
        mejoras.append((0, "gancho", "La primera palabra clave o cifra llega tarde: adelantarla a los primeros 5 s y destacarla en la capa viva."))
    ejes["gancho"] = round(statistics.mean(x for x in g if x is not None), 1)

    # 2. RITMO VISUAL
    cpm = r["cortes_por_minuto"] + r["cambios_suaves_por_minuto"] + (len(elementos) / (dur / 60) if dur else 0)
    rango = (20, 45, 8, 70) if tipo == "short" else (6, 16, 2, 30)
    quietos = [(a, l) for a, l in r["tramos_quietos_mas_de_6s"] if not any(a <= e["a"] <= a + l for e in elementos)]
    ejes["ritmo"] = round(statistics.mean([nota(cpm, *rango), max(2, 10 - 1.5 * len(quietos))]), 1)
    for a, l in quietos[:6]:
        mejoras.append((a, "ritmo", f"{l:.0f} s sin ningún cambio en pantalla desde {mmss(a)}: partir la escena, mover la cámara o poner un elemento."))

    # 3. VOZ Y AUDIO
    habla = sum(p["end"] - p["start"] for p in pals) or 1
    ppm = len(pals) / (dur / 60) if dur else 0
    pausas_largas = [(a["end"], b["start"] - a["end"]) for a, b in zip(pals, pals[1:]) if b["start"] - a["end"] > 1.2]
    vz = [nota(ppm, 130, 175, 90, 220) if tipo == "largo" else nota(ppm, 150, 200, 100, 240),
          nota(lufs, -15, -13, -22, -9), max(2, 10 - len(pausas_largas))]
    if pico is not None and pico > -0.5:
        vz.append(5); mejoras.append((0, "audio", f"Pico de {pico} dBFS: puede saturar; bajar el limitador a -1 dB."))
    if lufs is not None and not -15 <= lufs <= -13:
        mejoras.append((0, "audio", f"Volumen integrado {lufs} LUFS: llevarlo a -14 (terminar.py lo hace)."))
    for a, l in pausas_largas[:4]:
        mejoras.append((a, "audio", f"Silencio de {l:.1f} s en {mmss(a)}: recortarlo (recortar_pausas.py) o cubrirlo con música o un efecto."))
    ejes["voz_y_audio"] = round(statistics.mean(x for x in vz if x is not None), 1)

    # 4. SUBTÍTULOS Y CAPA VIVA
    viva = pr["subtitulos"].get("estilo") == "vivo"
    epm = len(elementos) / (dur / 60) if dur else 0
    cv = [10 if viva else 6, nota(epm, 1.5, 5, 0, 12) if tipo == "largo" else nota(epm, 6, 20, 1, 40),
          10 if pr["subtitulos"].get("palabras_clave") else 6]
    if not viva:
        mejoras.append((0, "capa viva", "Subtítulos clásicos: probar el estilo dinámico del canal (subtitulos.estilo = vivo)."))
    if epm < (1.5 if tipo == "largo" else 6):
        mejoras.append((0, "capa viva", f"{len(elementos)} elementos animados ({epm:.1f} por minuto): agregar íconos, cifras o tarjetas en las palabras que nombran algo visual."))
    ejes["subtitulos_y_capa_viva"] = round(statistics.mean(cv), 1)

    # 5. ESTRUCTURA Y RETENCIÓN
    bucles = sum(texto.count(b) for b in BUCLES)
    final = " ".join(p["word"] for p in pals if p["start"] > dur * 0.85).lower()
    cierre = any(c in final for c in CIERRE)
    caps = len(pr["capitulos"])
    es = [nota(dur / 60, 6, 15, 2, 30) if tipo == "largo" else nota(dur, 20, 60, 8, 180),
          nota(bucles / max(dur / 60, 1), 0.4, 2, 0, 5), 10 if cierre else 4]
    if tipo == "largo":
        es.append(10 if caps >= 3 else 5)
        if caps < 3:
            mejoras.append((0, "estructura", f"{caps} capítulos: con 3 o más YouTube muestra los capítulos y ayuda a la retención."))
    if not cierre:
        mejoras.append((dur * 0.9, "estructura", "No hay un cierre con acción (comentar, suscribirse, próximo video) en el último 15 %."))
    if bucles == 0:
        mejoras.append((dur * 0.3, "estructura", "No hay anuncios de lo que viene (\"más adelante\", \"lo tercero es lo más importante\"): sumar uno o dos para sostener la atención."))
    ejes["estructura"] = round(statistics.mean(x for x in es if x is not None), 1)

    # 6. EMPAQUE (título y miniatura)
    pub = [d for d in pr.dir.glob("08_PUBLICAR*") if d.is_dir()] + [pr.dir / "08_PUBLICAR"]
    minis = [f for d in pub if d.exists() for f in list(d.glob("*miniatura*.jpg")) + list(d.glob("*miniatura*.png"))]
    titulo = pr.cfg.get("titulo") or next((re.sub(r"^[#*\-\s]*(T[ií]tulo[^:]*:)?\s*", "", l).strip() for d in pub if d.exists()
                                           for f in d.glob("*.md") for l in f.read_text(encoding="utf-8", errors="ignore").splitlines()
                                           if re.match(r"^[#*\-\s]*T[ií]tulo", l)), None)
    em = []
    if titulo:
        n = len(titulo)
        em.append(nota(n, 35, 60, 15, 90))
        if n > 60:
            mejoras.append((0, "empaque", f"El título tiene {n} caracteres: en el celular se corta pasado ~60."))
    else:
        em.append(None); mejoras.append((0, "empaque", "No encontré el título elegido: anotarlo en proyecto.json (\"titulo\") o en el paquete de publicación."))
    if minis:
        try:
            import receta_miniatura as rm
            m = rm.medir(minis[0])
            em.append(nota(m["contraste"], 0.4, 0.8, 0.15, 1.2))
            if m["contraste"] < 0.4:
                mejoras.append((0, "empaque", f"La miniatura {minis[0].name} tiene poco contraste ({m['contraste']}): oscurecer el fondo o aclarar el sujeto."))
        except Exception:
            pass
    else:
        em.append(None); mejoras.append((0, "empaque", "No hay miniatura en 08_PUBLICAR: armarla con diseno.py y el kit del canal."))
    em = [x for x in em if x is not None]
    ejes["empaque"] = round(statistics.mean(em), 1) if em else None

    # 7. RIESGOS (monetización y confianza)
    hallados = [rz for rz in RIESGOS if rz in texto]
    ejes["riesgos"] = 10.0 if not hallados else max(2.0, 10 - 3 * len(hallados))
    for rz in hallados:
        try:
            t = buscar(pals, rz)
        except ValueError:
            t = 0
        mejoras.append((t, "riesgos", f"Frase riesgosa «{rz}»: promete o asegura resultados; reescribir con lenguaje responsable (y revisar monetizacion.md)."))

    pesos = {"gancho": 0.25, "ritmo": 0.15, "voz_y_audio": 0.10, "subtitulos_y_capa_viva": 0.10, "estructura": 0.15, "empaque": 0.15, "riesgos": 0.10}
    validos = {k: v for k, v in ejes.items() if v is not None}
    total = round(sum(validos[k] * pesos[k] for k in validos) / sum(pesos[k] for k in validos), 1)
    clase = "A" if total >= 8 else "B" if total >= 6 else "C"
    if (ejes.get("empaque") is None or not titulo or not minis) and clase == "A":
        clase = "B"          # sin título o sin miniatura elegidos no está listo para publicar
    decision = {"A": "listo: publicar (después del control de calidad)", "B": "publicar después de los arreglos rápidos de abajo",
                "C": "mejorar antes de publicar: rehacer las partes marcadas"}[clase]
    shorts = momentos_short(pals, frases, elementos, dur) if tipo == "largo" else []
    res = {"video": str(video), "tipo": tipo, "duracion_s": dur, "nota_medida": total, "clase_medida": clase, "decision": decision,
           "ejes": ejes, "pesos": pesos,
           "medidas": {"primera_palabra_s": primera, "palabras_primeros_5s": pal_5s, "primera_frase": frase1,
                       "cambios_por_minuto_con_elementos": round(cpm, 1), "tramos_quietos": quietos, "palabras_por_minuto": round(ppm),
                       "volumen_lufs": lufs, "pico_dbfs": pico, "pausas_largas": len(pausas_largas), "elementos": len(elementos),
                       "capitulos": caps, "bucles_abiertos": bucles, "cierre_con_accion": cierre, "titulo": titulo,
                       "miniaturas": [m.name for m in minis], "frases_riesgosas": hallados},
           "momentos_para_shorts": shorts,
           "mejoras": [{"minuto": mmss(t), "segundo": round(t, 1), "eje": e, "que_hacer": q} for t, e, q in sorted(mejoras, key=lambda x: x[0])]}
    out = pr.dir / "06_RECETA" / f"evaluacion_{video.stem}"
    out.with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    etiqueta = {"gancho": "Gancho (25 %)", "ritmo": "Ritmo visual (15 %)", "voz_y_audio": "Voz y audio (10 %)",
                "subtitulos_y_capa_viva": "Subtítulos y capa viva (10 %)", "estructura": "Estructura y retención (15 %)",
                "empaque": "Título y miniatura (15 %)", "riesgos": "Riesgos de monetización (10 %)"}
    md = [f"# Evaluación de {video.name}", "",
          f"**Nota medida: {total}/10 · Clase {clase}** — {decision}.",
          f"Tipo: {tipo}, {mmss(dur)}. Esta nota mide qué tan preparado está el video frente a lo que suele funcionar; "
          "no garantiza vistas. El agente evaluador la ajusta mirando el video.", "",
          "| eje | nota |", "|---|---|"] + [f"| {etiqueta[k]} | {v if v is not None else 'sin datos'} |" for k, v in ejes.items()]
    md += ["", "## Mejoras, en orden de aparición"] + [f"- **{m['minuto']}** [{m['eje']}] {m['que_hacer']}" for m in res["mejoras"]]
    if shorts:
        md += ["", "## Mejores momentos para Shorts (para `vertical` en proyecto.json)"] + \
              [f"- {mmss(s['desde_s'])}–{mmss(s['hasta_s'])} ({s['dura_s']} s): «{s['empieza']}»" for s in shorts]
    md += ["", f"Ritmo medido: `{carpeta_ritmo.name}\\ritmo.md`, gráfico `ritmo.png` y hojas de cortes."]
    out.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:14 + len(ejes)]), flush=True)
    print("LISTO", out.with_suffix(".md"), flush=True)


if __name__ == "__main__":
    main()
