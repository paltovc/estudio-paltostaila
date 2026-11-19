# «Oído» del estudio: escucha el audio final de un video y dice, con minuto y causa, lo que se puede medir.
#   python escuchar.py "<proyecto>" [--video "<final>.mp4"] [--salida "<carpeta>"] [--sin-transcribir] [--modelo small]
#                                   [--comparar "<otro>.mp4"]
# Solo LEE el video y las pistas del armado. Deja escucha_<video>.md y .json (y las imágenes del sonido de cada tramo
# marcado) en --salida o, si no se indica, en 07_RENDER\escucha. No pisa informes anteriores.
# Qué mide:
#   1. Se entiende: vuelve a transcribir la mezcla final (WhisperX, local) y la compara con la transcripción de la voz.
#   2. Efectos: si cada efecto de la hoja de cues suena donde debe, y cuánto queda la voz por encima (pistas del armado).
#   3. Defectos: saturación, clics, silencios largos, saltos entre audios de voz, y cómo queda en mono (parlante del celular).
#   4. Comparación con otra versión: en qué segundos cambió el sonido.
# Lo que NO hace: juzgar gusto (si una voz es cálida o un efecto molesta). Para eso deja la lista corta de tramos a escuchar.
import csv, difflib, json, math, shutil, subprocess, sys, wave
from pathlib import Path
import numpy as np
import os
from estudio import Proyecto, FFMPEG, SIN_METADATOS, palabras, norm, mmss, huella, nombre_libre, duracion_medio

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
pr = Proyecto()
A = sys.argv[1:]
SR = 48000


def opt(k, defecto=None):
    return A[A.index(k) + 1] if k in A and A.index(k) + 1 < len(A) else defecto


def elegir_video():
    if opt("--video"):
        return Path(opt("--video"))
    for suf in ("_con-subtitulos.mp4", "_youtube.mp4"):
        q = pr.salida / f"{pr.base_nombre}{suf}"
        if q.exists():
            return q
    sys.exit("No hay un video de esta versión en la carpeta de render: indicar --video")


def a_wav(origen, destino, canales=2):
    r = subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", str(origen), "-vn", "-ac", str(canales), "-ar", str(SR),
                        "-c:a", "pcm_s16le", *SIN_METADATOS, str(destino)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode or not Path(destino).exists():
        return None
    with wave.open(str(destino), "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return x.reshape(-1, canales) if canales > 1 else x


def db(v):
    return round(20 * math.log10(max(float(v), 1e-7)), 1)


def rms(x, a, b):
    """Nivel (dB) del tramo a..b segundos de una pista mono."""
    i, j = max(0, int(a * SR)), min(len(x), int(b * SR))
    return -140.0 if j <= i else db(np.sqrt(np.mean(np.square(x[i:j]))))


def ff_stderr(*args):
    r = subprocess.run([str(FFMPEG), "-hide_banner", *map(str, args), "-f", "null", "-"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return None if r.returncode else r.stderr


def whisperx_exe():
    c = [pr["whisperx"].get("ruta", ""), str(Path.home() / "EstudioPaltostaila" / "whisperx-venv" / "Scripts" / "whisperx.exe"),
         str(Path.home() / ".cache" / "watch" / "whisperx-venv" / "Scripts" / "whisperx.exe"), shutil.which("whisperx") or ""]
    return next((x for x in c if x and Path(x).exists()), None)


def se_entiende(wav_mono16, trabajo, cues):
    """Transcribe la mezcla final y la compara con la transcripción de la voz sola (la del proyecto)."""
    exe = whisperx_exe()
    if not exe:
        return None, "no encuentro WhisperX: no se pudo comprobar si se entiende"
    WX = pr["whisperx"]
    modelo = opt("--modelo", WX["modelo"])
    out = trabajo / "whisperx"
    out.mkdir(exist_ok=True)
    print(f"transcribiendo la mezcla final con {modelo} (tarda unos 2 a 3 minutos por minuto de audio)...", flush=True)
    r = subprocess.run([exe, str(wav_mono16), "--language", WX["idioma"], "--model", modelo, "--compute_type", WX["compute_type"],
                        "--device", "cpu", "--output_format", "json", "--output_dir", str(out)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    js = out / (wav_mono16.stem + ".json")
    js.unlink(missing_ok=True)
    if r.returncode or not js.exists():
        return None, "WhisperX falló: no se pudo comprobar si se entiende"
    oido = [t for s in json.loads(js.read_text(encoding="utf-8"))["segments"] for w in s["text"].split() for t in norm(w)]
    _, pals = palabras(pr)
    ref = [(t, w["start"], w["end"]) for w in pals for t in norm(w["word"])]
    sm = difflib.SequenceMatcher(None, [t for t, _, _ in ref], oido, autojunk=False)
    iguales = sum(b.size for b in sm.get_matching_blocks())
    tramos = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete") and i2 > i1:
            a, b = ref[i1][1], ref[i2 - 1][2]
            cerca = [c["sonido"] for c in cues if a - 0.6 <= c["t"] <= b + 0.6]
            tramos.append({"desde": round(a, 2), "hasta": round(b, 2), "dice": " ".join(t for t, _, _ in ref[i1:i2]),
                           "se_oye": " ".join(oido[j1:j2]) or "(nada)", "palabras": i2 - i1, "efecto_cerca": cerca})
    return {"modelo": modelo, "palabras": len(ref), "iguales": iguales,
            "porcentaje": round(100 * iguales / max(1, len(ref)), 1), "tramos": tramos}, ""


def leer_cues():
    """Hoja de cues del motor 0.14 (06_RECETA\\hoja_cues_<base>.csv). Sin hoja, no hay efectos que comprobar uno a uno."""
    h = pr.receta.parent / f"hoja_cues_{pr.base_nombre}.csv"
    if not h.exists():
        return [], None
    filas = list(csv.DictReader(h.read_text(encoding="utf-8-sig").splitlines(), delimiter=";"))
    out = []
    for f in filas:
        try:
            out.append({"t": float(str(f["segundo"]).replace(",", ".")), "sonido": f["sonido"], "alineado": f.get("alineado", "")})
        except (KeyError, ValueError):
            continue
    return out, h


def revisar_efectos(cues, voz, fx, mezcla):
    """Por cada efecto: si suena cerca de su momento (en la pista de efectos) y cuánto queda la voz por encima."""
    res = []
    for c in cues:
        t = c["t"]
        d = {"t": round(t, 2), "sonido": c["sonido"], "alineado": c["alineado"], "detectado": c.get("detectado", False)}
        if fx is not None:
            antes, en = rms(fx, t - 0.5, t - 0.08), rms(fx, t - 0.03, t + 0.35)
            d["sube_db"] = round(en - antes, 1)
            d["suena"] = en > -60 and (en - antes > 6 or antes < -70)
            paso = int(0.01 * SR)                      # dónde empieza a oírse de verdad, en pasos de 10 ms
            i0 = max(0, int((t - 0.5) * SR))
            ventana = fx[i0:int((t + 0.8) * SR)]
            niveles = [db(np.sqrt(np.mean(np.square(ventana[k:k + paso])))) for k in range(0, max(0, len(ventana) - paso), paso)]
            if niveles and max(niveles) > -60:
                umbral = max(niveles) - 20
                primero = next(k for k, n in enumerate(niveles) if n >= umbral)
                d["desfase_s"] = round(i0 / SR + primero * 0.01 - t, 2)
            if voz is not None:
                d["voz_sobre_efecto_db"] = round(rms(voz, t, t + 0.4) - en, 1)
        else:
            d["sube_db"] = round(rms(mezcla, t - 0.03, t + 0.35) - rms(mezcla, t - 0.5, t - 0.08), 1)
        res.append(d)
    return res


def defectos(st, mono, video, cortes_voz):
    D = {}
    pico = float(np.max(np.abs(st)))
    D["saturacion"] = {"muestras_al_tope": int(np.sum(np.abs(st) >= 0.999)), "pico": db(pico)}
    salto = np.abs(np.diff(mono))                    # clic: un salto brusco entre dos muestras seguidas
    idx = np.where(salto > 0.45)[0]
    clics = []
    for i in idx:                                    # solo cuenta si está AISLADO: una voz fuerte o un efecto también saltan
        a, b = max(0, i - 480), min(len(mono), i + 480)
        vecinos = np.concatenate([mono[a:max(a, i - 48)], mono[min(b, i + 48):b]])
        if len(vecinos) and float(np.sqrt(np.mean(np.square(vecinos)))) < 0.06 and (not clics or i / SR - clics[-1] > 0.05):
            clics.append(round(i / SR, 2))
    D["clics"] = clics[:40]
    e = ff_stderr("-i", video, "-vn", "-af", "silencedetect=noise=-45dB:d=1.5")
    import re
    D["silencios"] = [] if e is None else [(round(float(a), 1), round(float(b), 1)) for a, b in
                                           re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", e)]
    e = ff_stderr("-i", video, "-vn", "-af", "ebur128=peak=true")
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", e or ""); p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e or "")
    D["lufs"], D["pico_real_dbtp"] = (float(m[-1]) if m else None), (float(p[-1]) if p else None)
    L, R = st[:, 0], st[:, 1]
    suma = np.sqrt(np.mean(np.square((L + R) / 2))); cada = (np.sqrt(np.mean(np.square(L))) + np.sqrt(np.mean(np.square(R)))) / 2
    D["mono"] = {"pierde_db": round(db(suma) - db(cada), 1),
                 "correlacion": round(float(np.corrcoef(L[::50], R[::50])[0, 1]), 2) if np.std(L) and np.std(R) else 1.0}
    saltos = []                                      # uniones entre audios de voz: cambio brusco de nivel de fondo
    for t in cortes_voz:
        a, b = rms(mono, t - 0.6, t - 0.05), rms(mono, t + 0.05, t + 0.6)
        if abs(a - b) > 9 and max(a, b) > -45:
            saltos.append({"t": round(t, 2), "antes_db": a, "despues_db": b})
    D["uniones_de_voz"] = saltos
    return D


def comparar(mono, otro_video, trabajo):
    o = a_wav(otro_video, trabajo / "otro.wav", 1)
    if o is None:
        return None
    n = min(len(mono), len(o)) // SR
    dif = []
    for s in range(n):
        a, b = rms(mono, s, s + 1), rms(o, s, s + 1)
        if abs(a - b) >= 3 and max(a, b) > -50:
            dif.append({"segundo": s, "este_db": a, "otro_db": b})
    return {"otro": Path(otro_video).name, "duracion_este": round(len(mono) / SR, 2), "duracion_otro": round(len(o) / SR, 2),
            "segundos_distintos": len(dif), "detalle": dif[:60]}


def imagen(video, t, destino):
    """Espectrograma de 6 s alrededor de t: es la forma de «mirar» el sonido de un tramo marcado."""
    a = max(0.0, t - 3)
    r = subprocess.run([str(FFMPEG), "-v", "error", "-y", "-ss", f"{a:.2f}", "-t", "6", "-i", str(video), "-vn", "-lavfi",
                        "showspectrumpic=s=960x360:legend=1:scale=log", "-frames:v", "1", str(destino)], capture_output=True)
    return destino.name if r.returncode == 0 and destino.exists() else None


def main():
    video = elegir_video()
    if not video.exists():
        sys.exit(f"No encuentro {video}")
    destino = Path(opt("--salida")) if opt("--salida") else pr.salida / "escucha"
    destino.mkdir(parents=True, exist_ok=True)
    trabajo = destino / f"tmp_escucha_{os.getpid()}"
    if trabajo.resolve() == pr.tmp.resolve() or pr.tmp.resolve() in trabajo.resolve().parents:
        sys.exit("--salida no puede ser la carpeta tmp del armado (ahí están la voz y los efectos)")
    trabajo.mkdir(exist_ok=True)
    sello = huella(video)
    st = a_wav(video, trabajo / "mezcla.wav", 2)
    if st is None:
        sys.exit("ffmpeg no pudo leer el audio del video")
    mono = st.mean(axis=1)
    cues, hoja = leer_cues()
    voz = a_wav(pr.tmp / "voz.wav", trabajo / "voz.wav", 1) if (pr.tmp / "voz.wav").exists() else None
    fx = a_wav(pr.tmp / "efectos.wav", trabajo / "fx.wav", 1) if (pr.tmp / "efectos.wav").exists() else None
    aviso_pistas = ""
    for nombre_p, pista in (("voz", voz), ("efectos", fx)):
        if pista is not None and abs(len(pista) - len(mono)) / SR > 0.5:
            aviso_pistas += f" la pista de {nombre_p} del armado no dura lo mismo que el video (es de otro armado): no se usó."
            if nombre_p == "voz":
                voz = None
            else:
                fx = None
    if not cues and fx is not None:      # video anterior a la 0.14 (sin hoja): los efectos se ubican en su propia pista
        paso = int(0.05 * SR)
        niv = [db(np.sqrt(np.mean(np.square(fx[k:k + paso])))) for k in range(0, len(fx) - paso, paso)]
        for k in range(6, len(niv)):
            if niv[k] > -50 and max(niv[k - 6:k]) < -62:
                cues.append({"t": k * 0.05, "sonido": "efecto (ubicado en la pista de efectos)", "alineado": "sin hoja de cues",
                             "detectado": True})
    cortes, acum = [], 0.0
    try:
        for a in pr.audios()[:-1]:
            acum += duracion_medio(a); cortes.append(acum)
    except SystemExit:
        pass
    R = {"video": video.name, "sha256": sello, "duracion_s": round(len(mono) / SR, 2), "hoja_de_cues": hoja.name if hoja else None,
         "pistas_del_armado": {"voz": voz is not None, "efectos": fx is not None}}
    R["defectos"] = defectos(st, mono, video, cortes)
    R["efectos"] = revisar_efectos(cues, voz, fx, mono)
    if "--sin-transcribir" in A:
        R["se_entiende"], R["se_entiende_nota"] = None, "no se pidió (--sin-transcribir)"
    else:
        w16 = trabajo / "mezcla_16k.wav"
        subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", *SIN_METADATOS, str(w16)])
        R["se_entiende"], R["se_entiende_nota"] = se_entiende(w16, trabajo, cues)
    if opt("--comparar"):
        R["comparacion"] = comparar(mono, opt("--comparar"), trabajo)
    if huella(video) != sello:
        sys.exit(f"{video.name} cambió mientras se escuchaba: repetir cuando termine el render")

    # --- qué hay que escuchar: lista corta, con minuto y causa
    O = []       # (segundo, gravedad, texto)
    D = R["defectos"]
    if D["lufs"] is None or D["pico_real_dbtp"] is None:
        O.append((0, "revisar", "no comprobado: ffmpeg no pudo medir el volumen ni el pico real"))
    else:
        if abs(D["lufs"] + 14) > 1:
            O.append((0, "revisar", f"volumen {D['lufs']} LUFS (el estudio usa -14 ±1)"))
        if D["pico_real_dbtp"] > -1:
            O.append((0, "revisar", f"pico real {D['pico_real_dbtp']} dBTP (máximo -1)"))
    if D["saturacion"]["muestras_al_tope"] > 20:
        O.append((0, "revisar", f"saturación: {D['saturacion']['muestras_al_tope']} muestras al tope"))
    for t in D["clics"][:10]:
        O.append((t, "revisar", "posible clic (salto brusco en la onda)"))
    for fin, dur in D["silencios"]:
        if fin - dur > 1 and fin < R["duracion_s"] - 1:
            O.append((fin - dur, "revisar", f"silencio de {dur} s"))
    for s in D["uniones_de_voz"]:
        O.append((s["t"], "revisar", f"cambio brusco en la unión de dos audios de voz ({s['antes_db']} → {s['despues_db']} dB)"))
    if D["mono"]["pierde_db"] < -3:
        O.append((0, "revisar", f"en mono (parlante del celular) pierde {abs(D['mono']['pierde_db'])} dB"))
    for e in R["efectos"]:
        if e.get("detectado"):
            pass                                        # ubicado en su propia pista: no hay contra qué comprobarlo
        elif e.get("suena") is False:
            O.append((e["t"], "revisar", f"el efecto {e['sonido']} no se nota en su momento (sube {e['sube_db']} dB)"))
        elif abs(e.get("desfase_s", 0)) > 0.12:
            O.append((e["t"], "revisar", f"el efecto {e['sonido']} empieza a oírse {e['desfase_s']:+.2f} s respecto de su momento"))
        if e.get("voz_sobre_efecto_db") is not None and e["voz_sobre_efecto_db"] < 6 and e.get("suena"):
            O.append((e["t"], "escuchar", f"el efecto {e['sonido']} queda a solo {e['voz_sobre_efecto_db']} dB bajo la voz"))
    S = R["se_entiende"]
    if S:
        for t in S["tramos"]:
            if t["palabras"] >= 2 or t["efecto_cerca"]:
                causa = f" (efecto cerca: {', '.join(t['efecto_cerca'])})" if t["efecto_cerca"] else ""
                O.append((t["desde"], "revisar" if t["efecto_cerca"] else "escuchar",
                          f"se dice «{t['dice']}» y se oye «{t['se_oye']}»{causa}"))
    O.sort()
    R["para_escuchar"] = [{"minuto": mmss(t), "segundo": round(t, 1), "tipo": g, "que": q} for t, g, q in O]
    for k, x in enumerate(R["para_escuchar"][:12]):
        x["imagen"] = imagen(video, x["segundo"], nombre_libre(destino / f"sonido_{video.stem}_{int(x['segundo']):04d}.png"))

    L = [f"# Escucha de {video.name}", "",
         f"Duración {mmss(R['duracion_s'])} · {D['lufs']} LUFS · pico real {D['pico_real_dbtp']} dBTP · "
         f"en mono {D['mono']['pierde_db']} dB · pistas del armado: voz {'sí' if voz is not None else 'no'}, "
         f"efectos {'sí' if fx is not None else 'no'} · hoja de cues: {hoja.name if hoja else 'no hay'}", ""]
    if S:
        L += [f"**Se entiende:** {S['porcentaje']} % de las {S['palabras']} palabras de la voz se reconocen igual en la mezcla final "
              f"(modelo {S['modelo']}; diferencias de una palabra suelta son normales).", ""]
    else:
        L += [f"**Se entiende:** no comprobado ({R['se_entiende_nota']}).", ""]
    det = sum(1 for e in R["efectos"] if e.get("detectado"))
    L += [f"**Efectos:** {len(R['efectos']) - det} comprobados contra la hoja de cues"
          + (f"; {det} solo ubicados en su pista (sin hoja de cues no hay contra qué comprobarlos)" if det else "")
          + ("" if R["efectos"] or hoja else " · sin hoja de cues ni pista de efectos"), ""]
    if aviso_pistas:
        L += [f"**Aviso:**{aviso_pistas}", ""]
    if R.get("comparacion"):
        c = R["comparacion"]
        L += [f"**Comparado con {c['otro']}:** {c['segundos_distintos']} segundos con 3 dB o más de diferencia "
              f"(duración {c['duracion_este']} s y {c['duracion_otro']} s).", ""]
    L += ["## Para escuchar (lo medible; el gusto lo decide la persona)", ""]
    if R["para_escuchar"]:
        L += ["| minuto | tipo | qué | imagen |", "|---|---|---|---|"]
        L += [f"| {x['minuto']} | {x['tipo']} | {x['que'].replace('|', '/')} | {x.get('imagen') or ''} |" for x in R["para_escuchar"]]
    else:
        L += ["Nada marcado."]
    md = nombre_libre(destino / f"escucha_{video.stem}.md")
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    md.with_suffix(".json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    import shutil as _sh
    _sh.rmtree(trabajo, ignore_errors=True)            # solo su carpeta temporal propia (tmp_escucha_<pid>)
    print("\n".join(L), flush=True)
    print("LISTO", md)


if __name__ == "__main__":
    main()
