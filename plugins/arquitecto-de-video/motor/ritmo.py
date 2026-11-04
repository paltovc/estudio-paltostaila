# Ritmo visual y sonoro medido de un video (ingeniería inversa de la edición, sin copiar nada):
# cortes por minuto y cada 10 s, duración de cada plano, tramos quietos de más de 6 s, volumen en el tiempo,
# pausas, y una hoja con el cuadro de cada corte (para leer qué texto aparece en pantalla y cómo entra).
#   python ritmo.py "video.mp4"                         -> carpeta ritmo_<nombre> al lado del video
#   python ritmo.py "referente.mp4" --comparar "nuestro.mp4"   -> además compara los dos
#   python ritmo.py "video.mp4" --umbral 0.25 --salida "C:\carpeta"
# Sirve con el video de un referente que la persona entregó, con referente.py o con nuestros propios renders.
import json, re, statistics, sys
from pathlib import Path
from estudio import FFMPEG, run, duracion_medio, mmss

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None


def cortes(video, umbral):
    s = run([FFMPEG, "-hide_banner", "-i", video, "-vf", f"select='gt(scene,{umbral})',showinfo", "-an", "-f", "null", "-"])
    out = []
    for t in (float(x) for x in re.findall(r"pts_time:([\d.]+)", s)):
        if not out or t - out[-1] > 0.25:          # destellos y fundidos dan varios cortes seguidos
            out.append(round(t, 2))
    return out


def volumen(video):
    """Volumen momentáneo (LUFS) cada ~0,1 s, y pausas de la voz."""
    s = run([FFMPEG, "-hide_banner", "-i", video, "-vn", "-af", "ebur128=metadata=0", "-f", "null", "-"])
    pts = [(float(t), float(m)) for t, m in re.findall(r"t:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+)", s)]
    sil = run([FFMPEG, "-hide_banner", "-i", video, "-vn", "-af", "silencedetect=n=-35dB:d=0.4", "-f", "null", "-"])
    ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", sil)]
    fin = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", sil)]
    return pts, [(round(a, 2), round(b, 2)) for a, b in zip(ini, fin)]


def analizar(video, salida=None, umbral=0.3):
    video = Path(video)
    salida = Path(salida) if salida else video.parent / f"ritmo_{video.stem}"
    salida.mkdir(parents=True, exist_ok=True)
    dur = duracion_medio(video)
    cs = cortes(video, umbral)
    # cambios suaves: saltos de corte en el mismo plano y acercamientos (punch-in), que el umbral normal no ve
    suaves = [c for c in cortes(video, max(0.08, umbral * 0.4)) if all(abs(c - x) > 0.3 for x in cs)]
    bordes = [0.0] + cs + [dur]
    planos = [round(b - a, 2) for a, b in zip(bordes, bordes[1:]) if b - a > 0.05]
    cada10 = [sum(1 for c in cs if k * 10 <= c < (k + 1) * 10) for k in range(int(dur // 10) + 1)]
    quietos = [(round(a, 1), round(b - a, 1)) for a, b in zip(bordes, bordes[1:]) if b - a > 6]
    vol, pausas = volumen(video)
    d = {"video": str(video), "duracion_s": round(dur, 1), "cortes": len(cs),
         "cortes_por_minuto": round(len(cs) / (dur / 60), 1) if dur else 0,
         "plano_promedio_s": round(statistics.mean(planos), 2) if planos else dur,
         "plano_mediana_s": round(statistics.median(planos), 2) if planos else dur,
         "plano_mas_largo_s": max(planos) if planos else dur,
         "cortes_primeros_3s": sum(c <= 3 for c in cs), "cortes_primeros_10s": sum(c <= 10 for c in cs),
         "cortes_cada_10s": cada10, "tramos_quietos_mas_de_6s": quietos,
         "pausas_de_voz": len(pausas), "pausa_mas_larga_s": max((b - a for a, b in pausas), default=0),
         "cambios_suaves": len(suaves), "cambios_suaves_por_minuto": round(len(suaves) / (dur / 60), 1) if dur else 0,
         "momentos_de_corte": cs, "momentos_suaves": suaves}
    if vol:
        ms = [m for _, m in vol if m > -70]
        d["volumen_promedio_lufs"] = round(statistics.mean(ms), 1) if ms else None
        d["volumen_rango_lufs"] = round(max(ms) - min(ms), 1) if ms else None
    (salida / "ritmo.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    hoja_cortes(video, sorted(cs + suaves), salida, dur)
    return d, vol, salida


def hoja_cortes(video, cs, salida, dur, por_hoja=24):
    """Un cuadro 0,25 s después de cada corte, con su minuto: para ver qué texto aparece y cómo es cada plano."""
    momentos = [0.0] + cs
    for n in range(0, min(len(momentos), 96), por_hoja):
        grupo = momentos[n:n + por_hoja]
        tmp = salida / "_cuadros"
        tmp.mkdir(exist_ok=True)
        cuadros = []
        for k, t in enumerate(grupo):
            f = tmp / f"c{n + k:03d}.jpg"
            run([FFMPEG, "-v", "error", "-y", "-ss", f"{min(t + 0.25, max(0, dur - 0.3)):.2f}", "-i", video, "-frames:v", "1", "-vf", "scale=320:-2", "-q:v", "4", f])
            if f.exists():
                cuadros.append((t, f))
        if not cuadros or Image is None:
            continue
        w, h = Image.open(cuadros[0][1]).size
        cols = 6
        filas = (len(cuadros) + cols - 1) // cols
        hoja = Image.new("RGB", (cols * w, filas * (h + 26)), (18, 18, 18))
        dib = ImageDraw.Draw(hoja)
        letra = fuente(18)
        for k, (t, f) in enumerate(cuadros):
            x, y = (k % cols) * w, (k // cols) * (h + 26)
            hoja.paste(Image.open(f).resize((w, h)), (x, y + 26))
            dib.text((x + 6, y + 3), f"#{n + k}  {mmss(t)}", fill=(255, 210, 63), font=letra)
        hoja.save(salida / f"hoja_cortes_{n // por_hoja + 1:02d}.jpg", quality=85)
        for _, f in cuadros:
            f.unlink(missing_ok=True)
    try:
        (salida / "_cuadros").rmdir()
    except OSError:
        pass


def fuente(tam):
    for nombre in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(nombre, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def grafico(series, destino):
    """Una franja por video: barras = cortes cada 10 s, línea = volumen, marcas = cada corte."""
    if Image is None:
        return
    W, alto = 1400, 230
    img = Image.new("RGB", (W, alto * len(series) + 20), (255, 255, 255))
    dib = ImageDraw.Draw(img)
    f, fc = fuente(20), fuente(15)
    dmax = max(d["duracion_s"] for d, _ in series)
    cmax = max(max(d["cortes_cada_10s"] or [1]) for d, _ in series) or 1
    for i, (d, vol) in enumerate(series):
        y0, x0, ancho = i * alto + 20, 70, W - 100
        X = lambda t: x0 + t / dmax * ancho
        dib.text((x0, y0), f"{Path(d['video']).name}: {d['cortes_por_minuto']} cortes/min, plano promedio {d['plano_promedio_s']} s",
                 fill=(20, 20, 20), font=f)
        base = y0 + 190
        for k, n in enumerate(d["cortes_cada_10s"]):
            h = n / cmax * 120
            dib.rectangle([X(k * 10) + 2, base - h, X(min((k + 1) * 10, d["duracion_s"])) - 2, base], fill=(79, 195, 247))
        for c in d["momentos_de_corte"]:
            dib.line([X(c), base + 4, X(c), base + 12], fill=(40, 40, 40))
        for c in d.get("momentos_suaves", []):
            dib.line([X(c), base + 4, X(c), base + 9], fill=(150, 150, 150))
        for a, largo in d["tramos_quietos_mas_de_6s"]:
            dib.rectangle([X(a), base - 150, X(a + largo), base - 144], fill=(255, 94, 94))
        pts = [(X(t), base - 10 - (max(-60, min(-10, m)) + 60) / 50 * 110) for t, m in vol[::5] if m > -70]
        if len(pts) > 1:
            dib.line(pts, fill=(255, 140, 66), width=2)
        for s in range(0, int(d["duracion_s"]) + 1, 30 if dmax > 120 else 10):
            dib.text((X(s) - 10, base + 14), mmss(s).split(".")[0], fill=(120, 120, 120), font=fc)
        dib.text((x0 - 62, base - 12), f"{cmax}/10s", fill=(79, 150, 200), font=fc)
    dib.text((W - 560, 2), "azul = cortes cada 10 s · naranja = volumen · rojo = más de 6 s sin corte", fill=(90, 90, 90), font=fc)
    img.save(destino, quality=90)


def informe(d, salida, otro=None):
    filas = [("Duración", "duracion_s", "s"), ("Cortes por minuto", "cortes_por_minuto", ""), ("Plano promedio", "plano_promedio_s", "s"),
             ("Plano mediana", "plano_mediana_s", "s"), ("Plano más largo", "plano_mas_largo_s", "s"),
             ("Cambios suaves por minuto (saltos, acercamientos)", "cambios_suaves_por_minuto", ""), ("Cortes en los primeros 3 s", "cortes_primeros_3s", ""), ("Cortes en los primeros 10 s", "cortes_primeros_10s", ""),
             ("Pausas de voz (>0,4 s)", "pausas_de_voz", ""), ("Volumen promedio", "volumen_promedio_lufs", "LUFS")]
    cab = f"| dato | {Path(d['video']).name} |" + (f" {Path(otro['video']).name} |" if otro else "")
    m = [f"# Ritmo de {Path(d['video']).name}", "", cab, "|---|---|" + ("---|" if otro else "")]
    for nombre, k, u in filas:
        m.append(f"| {nombre} | {d.get(k)} {u} |" + (f" {otro.get(k)} {u} |" if otro else ""))
    m += ["", "## Tramos de más de 6 s sin corte"] + ([f"- {mmss(a)} durante {b} s" for a, b in d["tramos_quietos_mas_de_6s"]] or ["- ninguno"])
    m += ["", "## Cortes cada 10 s", " ".join(f"{k * 10}s:{n}" for k, n in enumerate(d["cortes_cada_10s"])),
          "", "Archivos: ritmo.json, ritmo.png (gráfico), hoja_cortes_NN.jpg (cuadro de cada corte con su minuto).",
          "Leer las hojas para anotar: texto en pantalla (cuántas palabras, dónde, cómo entra), tipo de plano y transiciones."]
    if otro:
        dif = round(otro["cortes_por_minuto"] - d["cortes_por_minuto"], 1)
        m += ["", f"**Comparación:** el segundo video tiene {abs(dif)} cortes por minuto {'más' if dif > 0 else 'menos'} y planos de "
              f"{otro['plano_promedio_s']} s frente a {d['plano_promedio_s']} s."]
    (salida / "ritmo.md").write_text("\n".join(m) + "\n", encoding="utf-8")
    print("\n".join(m[:14]), flush=True)


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        sys.exit("uso: python ritmo.py video.mp4 [--comparar otro.mp4] [--umbral 0.3] [--salida carpeta]")
    opt = lambda k, x=None: a[a.index(k) + 1] if k in a else x
    umbral = float(opt("--umbral", 0.3))
    d, vol, salida = analizar(a[0], opt("--salida"), umbral)
    series, otro = [(d, vol)], None
    if opt("--comparar"):
        otro, vol2, _ = analizar(opt("--comparar"), salida / "comparado", umbral)
        series.append((otro, vol2))
    grafico(series, salida / "ritmo.png")
    informe(d, salida, otro)
    print("LISTO", salida, flush=True)


if __name__ == "__main__":
    main()
