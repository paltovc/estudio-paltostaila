# Capa de efectos de sonido (sin musica): sonidos puntuales cuando aparece algo que suena,
# el audio propio de los clips de Flow y un "whoosh" suave al abrir cada bloque.
# Sale tmp/efectos.wav con la duracion del video; terminar.py la mezcla bajo la voz.
# 0.14: cada efecto se alinea por lo que se oye, no por el inicio del archivo: "alinear": "ataque" (el primer sonido
# audible cae en el momento; es lo normal), "pico" (el punto más fuerte cae en el momento: llegadas, impactos, whoosh)
# o "inicio" (como antes). Si un efecto parte encima de una palabra, baja unos dB. Queda una hoja de cues con
# tiempo, archivo, ganancia, fuente y licencia en 06_RECETA\hoja_cues_<ID>_<version>.csv.
#   python sonidos.py "C:\ruta\video"
# En proyecto.json, "sonidos": {"efectos": [{"frase": "abre la puerta", "archivo": "doorOpen_1.ogg"},
#                                          {"escena": 12, "desfase": 0.2, "archivo": "cloth2.ogg", "ganancia": -2}]}
import csv, io, sys
from pathlib import Path
from estudio import Proyecto, FFMPEG, run, palabras, momento, mmss, ataque_y_pico, escribir_entrega, apartar_anterior
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

pr = Proyecto()
S = pr["sonidos"]
BANCOS = [pr.sonidos, Path(__file__).resolve().parent.parent / "sonidos", Path.home() / "EstudioPaltostaila" / "sonidos"]


def buscar_wav(nombre):
    """Ruta del sonido en 05_SONIDOS del proyecto o en el banco del estudio; None si no está."""
    for banco in BANCOS:
        if banco.exists():
            hallado = next(banco.rglob(nombre), None)
            if hallado:
                return hallado
    return None


def wav(nombre):
    hallado = buscar_wav(nombre)
    if hallado:
        return hallado
    sys.exit(f"No encuentro el sonido {nombre} en {', '.join(str(b) for b in BANCOS)}")


def pico_db(f):
    """Nivel máximo de un sonido en dB (0 = tope digital); None si no se pudo medir."""
    import re, subprocess
    r = subprocess.run([str(FFMPEG), "-hide_banner", "-i", str(f), "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.findall(r"max_volume:\s*(-?[\d.]+) dB", r.stderr)
    return float(m[-1]) if m else None


def origen(f):
    """(fuente, licencia) de un sonido. Solo se anota CC0 si el paquete del banco trae su archivo de licencia y dice
    CC0; todo lo demás queda como «revisar» (un archivo suelto dejado en el banco no se da por libre)."""
    f = Path(f).resolve()
    if pr.sonidos.exists() and pr.sonidos.resolve() in f.parents:
        return "carpeta 05_SONIDOS del proyecto", "revisar (anotar en licencias\\registro.md)"
    for banco in BANCOS[1:]:
        b = banco.resolve()
        if b in f.parents:
            paquete = b / f.relative_to(b).parts[0]
            if paquete.is_dir():
                for lic in paquete.iterdir():
                    if lic.is_file() and lic.name.lower() in ("license.txt", "licencia.txt", "license.md"):
                        t = lic.read_text(encoding="utf-8", errors="replace").lower()
                        if "cc0" in t or "creative commons zero" in t:
                            return f"banco del estudio, paquete {paquete.name}", f"CC0 según {lic.name} del paquete"
            return "banco del estudio (sin archivo de licencia en su paquete)", "revisar"
    return "fuera del banco", "revisar"


def retirar_hoja():
    """Si ya no hay capa de efectos, la hoja de cues vieja no puede quedar como vigente: se guarda como _anterior."""
    vieja = pr.receta.parent / f"hoja_cues_{pr.base_nombre}.csv"
    g = apartar_anterior(vieja)
    if g:
        print(f"la hoja de cues anterior quedó guardada como {g.name}", flush=True)


def main():
    if not S["activar"]:
        print("sonidos desactivados en proyecto.json")
        retirar_hoja()
        return
    dur = pr.duracion()
    escenas = pr.escenas() if pr.receta.exists() else []     # 0.15: material grabado no tiene receta de escenas
    _, pals = palabras(pr)
    ini_escena = {r["n"]: r["t0"] for r in escenas}
    fin_escena = {r["n"]: r["t1"] for r in escenas}
    ins, filtros, etiquetas, resumen, hoja = [], [], [], [], []
    modo_general = str(S.get("alinear", "inicio"))
    baja = -abs(float(S.get("baja_sobre_voz", 0)))     # siempre baja: un 3 escrito sin signo no puede subir el efecto

    def en_medio_de_palabra(t):
        return any(w.get("start", 1e9) + 0.05 < t < w.get("end", -1) - 0.02 for w in pals)

    def agregar(entrada, cadena, t, etiqueta, ganancia=0.0, alineado="inicio", fuente="sintetizado por el motor", licencia="propio", recortar=False):
        if t < 0 and recortar:        # no cabe entero antes del 0: se recorta el comienzo en vez de correrlo
            if entrada[0] == "-ss":   # ya traía un corte (ataque o pico): un solo -ss con la suma (ffmpeg usa el último)
                entrada = ["-ss", f"{float(entrada[1]) - t:.3f}", *entrada[2:]]
            else:
                entrada = ["-ss", f"{-t:.3f}", *entrada]
            alineado += f", recortado {-t:.2f} s al inicio"
            t = 0.0
        elif t < 0:                   # con alinear = "inicio" (proyectos de antes de la 0.14) suena entero desde el 0
            t = 0.0
        ins.extend(entrada)
        idx = sum(1 for x in ins if x == "-i") - 1
        ms = int(t * 1000)
        filtros.append(f"[{idx}:a]{cadena},aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms}[e{idx}]")
        etiquetas.append(f"[e{idx}]")
        resumen.append((t, etiqueta))
        hoja.append((t, etiqueta, ganancia, alineado, fuente, licencia))

    for e in S["efectos"]:
        t, f = momento(pr, pals, escenas, e), wav(e["archivo"])
        d, g = float(e.get("duracion", 2)), float(e.get("ganancia", 0))
        modo = str(e.get("alinear", modo_general))
        ataque, pico = ataque_y_pico(f) if modo in ("ataque", "pico") else (0.0, 0.0)
        if modo in ("ataque", "pico") and (ataque, pico) == (0.0, 0.0):
            nota = f"{modo}: no se pudo medir el sonido, va por el inicio"
            modo = "inicio"
        else:
            nota = modo + (f" (-{ataque:.3f} s)" if modo == "ataque" and ataque else f" (pico a {pico:.3f} s)" if modo == "pico" else "")
        corte, llega = 0.0, t
        if modo == "ataque":
            corte = ataque                                            # se salta el silencio inicial del archivo
        elif modo == "pico":
            d = max(d, pico + 0.5)                                    # el punto más fuerte tiene que alcanzar a sonar
            llega = t - pico                                          # y caer justo en el momento
            if llega < 0:
                corte, llega = -llega, 0.0
                nota += f", recortado {corte:.2f} s al inicio"
        vol = S["vol_efectos"] + g
        if baja and "frase" not in e and not e.get("sobre_voz") and en_medio_de_palabra(t):
            vol += baja                                               # baja el efecto, no sube la voz
            nota += f", {baja:g} dB por caer en medio de una palabra"
        fuente, licencia = origen(f)
        agregar(["-ss", f"{corte:.3f}", "-i", f] if corte else ["-i", f],
                f"atrim=0:{d},volume={vol}dB,afade=t=out:st={max(d - 0.3, 0)}:d=0.3", llega, f.name, vol, nota, fuente, licencia, recortar=modo != "inicio")
    for n in S["clips_con_sonido"]:
        f = pr.clips / f"escena_{int(n):03d}.mp4"
        if not f.exists():
            continue
        d = float(S["recorte_clip"].get(str(n), fin_escena[int(n)] - ini_escena[int(n)]))
        agregar(["-i", f], f"atrim=0:{d:.2f},volume={S['vol_clips']}dB,afade=t=in:d=0.15,afade=t=out:st={max(d - 0.5, 0):.2f}:d=0.5",
                ini_escena[int(n)], f"sonido del clip {f.name}", S["vol_clips"], "inicio", "audio del propio clip", "la del generador del clip (ver registro)")
    if S["whoosh_en_capitulos"]:
        antes = 0.35 if modo_general == "inicio" else 0.45     # con "ataque" o "pico", su punto más fuerte cae en el cambio
        for n in pr["escenas_capitulo"]:
            agregar(["-f", "lavfi", "-i", "anoisesrc=color=pink:duration=0.8:amplitude=0.6"],
                    f"highpass=f=350,lowpass=f=2800,afade=t=in:d=0.45,afade=t=out:st=0.45:d=0.35,volume={S['whoosh_db']}dB",
                    ini_escena[int(n)] - antes, "whoosh (cambio de bloque)", S["whoosh_db"],
                    "inicio" if modo_general == "inicio" else "pico en la llegada", recortar=modo_general != "inicio")
    for e in S["lapiz"]:   # lapiz escribiendo, sintetizado
        agregar(["-f", "lavfi", "-i", "anoisesrc=color=white:duration=2.6:amplitude=0.5"],
                f"bandpass=f=4200:width_type=h:w=2600,tremolo=f=6:d=0.85,afade=t=in:d=0.2,afade=t=out:st=2.2:d=0.4,volume={S['whoosh_db'] - 2}dB",
                momento(pr, pals, escenas, e), "lapiz", S["whoosh_db"] - 2)
    # 0.15: sonidos sincronizados con los subtítulos dinámicos y con los elementos de la capa viva (apagado si no se pide).
    # "sonido_volumen" es cuánto queda bajo la voz (-14 = unos 14 dB bajo la voz): el sonido se mide y se lleva a ese nivel.
    import vivo
    por_archivo = {}
    for t, nombre, vol, etiqueta in vivo.cues_sonido(pr, pals):
        f = buscar_wav(vivo.SONIDOS.get(str(nombre).lower(), str(nombre)))
        if f is None:
            print(f"AVISO: no encuentro el sonido «{nombre}» para {etiqueta}; se salta", flush=True)
            continue
        por_archivo.setdefault(f, []).append((max(0.0, t), vol, etiqueta))
    for f, lista in por_archivo.items():          # el archivo entra una sola vez y se reparte (pueden ser muchos pops)
        ataque, pico = ataque_y_pico(f)[0], pico_db(f)
        fuente, licencia = origen(f)
        ins.extend(["-ss", f"{ataque:.3f}", "-i", f] if ataque else ["-i", f])      # el primer sonido audible cae en la palabra
        idx = sum(1 for x in ins if x == "-i") - 1
        filtros.append(f"[{idx}:a]atrim=0:1.2,afade=t=out:st=0.9:d=0.3,aformat=sample_rates=48000:channel_layouts=stereo,"
                       f"asplit={len(lista)}" + "".join(f"[v{idx}_{k}]" for k in range(len(lista))))
        for k, (t, vol, etiqueta) in enumerate(lista):
            bajo_voz = -abs(float(vol if vol is not None else -14))
            # un sonido corto cuyo máximo queda ~9 dB sobre el volumen de la voz suena más o menos igual de fuerte que ella
            g = S["vol_efectos"] if pico is None else pr["volumen_lufs"] + bajo_voz + 9 - pico
            ms = int(t * 1000)
            filtros.append(f"[v{idx}_{k}]volume={g:.1f}dB,adelay={ms}|{ms}[e{idx}_{k}]")
            etiquetas.append(f"[e{idx}_{k}]")
            resumen.append((t, f"{f.name} ({etiqueta})"))
            hoja.append((t, f"{f.name} ({etiqueta})", round(g, 1), f"ataque, {bajo_voz:g} dB bajo la voz", fuente, licencia))
    if not etiquetas:
        print("no hay efectos definidos; no se crea la capa")
        (pr.tmp / "efectos.wav").unlink(missing_ok=True)
        retirar_hoja()
        return
    mezcla = ";".join(filtros) + ";" + "".join(etiquetas) + \
        f"amix=inputs={len(etiquetas)}:normalize=0:dropout_transition=0,apad,atrim=0:{dur},alimiter=limit={S['limite_capa']}:level=0[out]"
    run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex", mezcla, "-map", "[out]", "-ar", "48000", *SIN_METADATOS, pr.tmp / "efectos.wav"])
    print(f"{len(etiquetas)} sonidos en {pr.tmp / 'efectos.wav'}", flush=True)
    for t, nombre in sorted(resumen):
        print(f"  {mmss(t)}  {nombre}")
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", lineterminator="\n")
    w.writerow(["tiempo", "segundo", "sonido", "volumen_db", "alineado", "fuente", "licencia"])
    for t, n, g, a, fu, li in sorted(hoja):
        w.writerow([mmss(t), f"{t:.3f}".replace(".", ","), n, f"{g:g}".replace(".", ","), a, fu, li])
    cues = pr.receta.parent / f"hoja_cues_{pr.base_nombre}.csv"
    escribir_entrega(cues, "\ufeff" + buf.getvalue())           # con BOM y coma decimal: abre bien en Excel
    print(f"hoja de cues: {cues}", flush=True)


if __name__ == "__main__":
    main()
