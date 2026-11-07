# Reemplaza imágenes dentro de un video YA TERMINADO (por ejemplo, editado en CapCut) sin tocar el original.
# Sirve cuando un video quedó con imágenes en inglés y ya existen (o se hicieron con Codex/ChatGPT) las versiones en español.
#   python reemplazar_imagen.py plan.json --analizar     -> solo mide los tramos (no escribe nada)
#   python reemplazar_imagen.py plan.json --muestras     -> además deja cuadros de prueba en la carpeta "trabajo" del plan
#   python reemplazar_imagen.py plan.json                -> renderiza la versión nueva (nombre nuevo; nunca pisa nada)
# plan.json:
#   {"video": "...\\FIN-001_v1_youtube.mp4", "salida": "...\\FIN-001_v3_youtube.mp4" (opcional),
#    "carpeta_imagenes": "...\\traducidas_codex", "trabajo": "...\\carpeta para muestras" (opcional),
#    "cambios": [{"t": 43, "imagen": "red_es.png", "conservar": ["titulo"]}, ...],         # un segundo dentro de cada tramo
#    "letreros": [{"desde": 44.2, "hasta": 50, "referencia": 43, "textos": {"BILL": "CUENTA"}, "siempre": true}]}
#   letreros = tramos animados; los cuadros que son un cruce con otra escena no se tocan, salvo "siempre": true
#   (úsese cuando en ese tramo no hay cruces, solo la misma escena girando o desenfocada)
# Cómo funciona: busca el tramo donde se ve la imagen vieja (la misma imagen con zoom/desplazamiento; ORB), pone la nueva
# con el mismo movimiento y vuelve a dibujar encima, desde el cuadro original, los subtítulos quemados y los rótulos de la
# edición ("titulo" = texto negro arriba a la izquierda, "numero" = número azul arriba). En tramos animados cambia solo los
# letreros siguiendo el movimiento. Después de renderizar: revisar cuadros (en los cruces entre escenas puede verse la vieja).
import json, subprocess, sys
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from estudio import FFMPEG, FFPROBE, nombre_libre

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
if not ARGS:
    sys.exit("Uso: python reemplazar_imagen.py plan.json [--analizar | --muestras]")
PLAN = json.loads(Path(ARGS[0]).read_text(encoding="utf-8"))
V = Path(PLAN["video"])
NUEVAS = Path(PLAN.get("carpeta_imagenes") or Path(ARGS[0]).parent)
SAL = Path(PLAN["salida"]) if PLAN.get("salida") else V.with_name(V.stem + "_imagenes-es.mp4")
TRAB = Path(PLAN.get("trabajo") or Path(ARGS[0]).parent)
CAMBIOS = [(c["t"], c["imagen"], c.get("conservar", []), *([c["umbral"]] if c.get("umbral") else [])) for c in PLAN.get("cambios", [])]
PARCHES = [(p["desde"], p["hasta"], p["referencia"], p["textos"], p.get("siempre", False)) for p in PLAN.get("letreros", [])]
FUENTE = PLAN.get("fuente", "C:/Windows/Fonts/arialbd.ttf")
LW, LH = 480, 270
UMBRAL = 9


def probe():
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                        "-of", "json", str(V)], capture_output=True, text=True)
    s = json.loads(r.stdout)["streams"][0]
    a, b = map(int, s["r_frame_rate"].split("/"))
    return s["width"], s["height"], a / b


def mascara(w, h):
    m = np.full((h, w), 255, np.uint8)
    m[int(h * 0.55):, int(w * 0.18):int(w * 0.82)] = 0      # subtítulos
    m[:int(h * 0.14), :int(w * 0.42)] = 0                     # título de la edición
    m[:int(h * 0.24), int(w * 0.26):int(w * 0.44)] = 0        # número de la edición
    return m


def leer_bajo(n0, n, fps):
    r = subprocess.run([str(FFMPEG), "-v", "error", "-ss", f"{n0 / fps:.4f}", "-i", str(V), "-frames:v", str(n),
                        "-vf", f"scale={LW}:{LH},format=gray", "-f", "rawvideo", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, LH, LW)


ORB = cv2.ORB_create(2000)
BF = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


def transf(ref, kd0, f, m):
    kp0, d0 = kd0
    kp, d = ORB.detectAndCompute(f, m)
    if d is None or d0 is None:
        return None
    mt = BF.match(d0, d)
    if len(mt) < 25:
        return None
    p0 = np.float32([kp0[x.queryIdx].pt for x in mt]); p1 = np.float32([kp[x.trainIdx].pt for x in mt])
    M, inl = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=2.5)
    if M is None or inl.sum() < 25:
        return None
    w = cv2.warpAffine(ref, M, (LW, LH), borderMode=cv2.BORDER_REPLICATE)
    dif = np.abs(w.astype(np.int16) - f.astype(np.int16))[m > 0].mean()
    return M if dif < UMBRAL else None


def tramo(t, fps):
    n0 = max(0, int((t - 14) * fps)); n = int(28 * fps)
    c = leer_bajo(n0, n, fps)
    m = mascara(LW, LH)
    i0 = int(t * fps) - n0
    ref = c[i0]; kd0 = ORB.detectAndCompute(ref, m)
    T = {i0: np.float32([[1, 0, 0], [0, 1, 0]])}
    for paso in (-1, 1):
        i = i0 + paso
        while 0 <= i < len(c):
            M = transf(ref, kd0, c[i], m)
            if M is None:
                break
            T[i] = M; i += paso
    ks = sorted(T)
    return n0 + ks[0], n0 + ks[-1], {n0 + k: T[k] for k in ks}


def zoom_base(Ts, W, H):
    # zoom extra (centrado) para que la imagen nueva siempre cubra el cuadro con el movimiento medido
    esq = np.float32([[0, 0], [W, 0], [0, H], [W, H]])
    for S in np.arange(1.0, 1.3, 0.005):
        Z = np.float32([[S, 0, W / 2 * (1 - S)], [0, S, H / 2 * (1 - S)], [0, 0, 1]])
        ok = True
        for M in list(Ts.values())[::3]:
            A = np.vstack([M, [0, 0, 1]]) @ Z
            inv = np.linalg.inv(A)
            p = (inv @ np.c_[esq, np.ones(4)].T).T
            if (p[:, 0] < -0.5).any() or (p[:, 0] > W + 0.5).any() or (p[:, 1] < -0.5).any() or (p[:, 1] > H + 0.5).any():
                ok = False; break
        if ok:
            return Z
    return Z


def subtitulo_letras(org):
    """Rectángulos de las líneas de subtítulo quemadas: texto blanco sobre caja oscura, centrado."""
    H, W = org.shape[:2]
    y0 = int(H * 0.45)
    b = org[y0:]
    blanco = (b.min(axis=2) > 205).astype(np.uint8)
    oscuro = (b.max(axis=2) < 85).astype(np.uint8)
    cerca = cv2.dilate(oscuro, np.ones((11, 11), np.uint8))
    letra = blanco & cerca
    lineas = cv2.morphologyEx(letra, cv2.MORPH_CLOSE, np.ones((int(H * 0.02), int(W * 0.022)), np.uint8))
    n, lab, est, cen = cv2.connectedComponentsWithStats(lineas)
    out = []
    for k in range(1, n):
        x, y, w, h, a = est[k]
        if w < W * 0.035 or not (H * 0.012 < h < H * 0.09) or not (W * 0.22 < x + w / 2 < W * 0.78):
            continue
        sub = letra[y:y + h, x:x + w]
        nl, _, el, _ = cv2.connectedComponentsWithStats(sub)
        letras = [e for e in el[1:] if e[4] < W * H * 0.0015]
        if len(letras) < 4:
            continue
        px, py = int(W * 0.013), int(H * 0.014)
        out.append((max(0, x - px), max(0, y0 + y - py), min(W, x + w + px), min(H, y0 + y + h + py)))
    return out


def subtitulo_caja(org):
    """Cajas grises/negras rellenas con letras blancas (sirve cuando el fondo es claro o hay paneles)."""
    H, W = org.shape[:2]
    y0 = int(H * 0.40)
    b = org[y0:]
    mx, mn = b.max(axis=2).astype(np.int16), b.min(axis=2).astype(np.int16)
    caja = ((mx < 90) & (mx - mn < 28)) | (mn > 205)          # gris oscuro de la caja o letra blanca
    oscuro = ((mx < 90) & (mx - mn < 28)).astype(np.uint8)
    m = cv2.morphologyEx(oscuro, cv2.MORPH_CLOSE, np.ones((int(H * 0.035), int(W * 0.02)), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((int(H * 0.03), int(W * 0.05)), np.uint8))
    n, lab, est, _ = cv2.connectedComponentsWithStats(m)
    out = []
    for k in range(1, n):
        x, y, w, h, a = est[k]
        if not (W * 0.05 < w < W * 0.8) or not (H * 0.03 < h < H * 0.2) or not (W * 0.2 < x + w / 2 < W * 0.8):
            continue
        if x <= 2 or x + w >= W - 2:
            continue
        r = caja[y:y + h, x:x + w]; bl = (mn[y:y + h, x:x + w] > 205)
        if r.mean() < 0.9 or not (0.04 < bl.mean() < 0.45):
            continue
        out.append((x, y0 + y, x + w, y0 + y + h))
    return out


def rotulos_subtitulo(org, nuevo):
    """Subtítulos quemados del video viejo, comparando con la imagen nueva ya alineada:
    (a) caja semitransparente: mucho más oscura y gris que la imagen nueva en ese lugar;
    (b) letras blancas sobre caja oscura, solo donde la imagen nueva también es oscura (fondos negros/azules)."""
    H, W = org.shape[:2]
    y0 = int(H * 0.40)
    o, n = org[y0:], nuevo[y0:]
    go = cv2.GaussianBlur(cv2.cvtColor(o, cv2.COLOR_BGR2GRAY), (0, 0), 9).astype(np.float32)
    gn = cv2.GaussianBlur(cv2.cvtColor(n, cv2.COLOR_BGR2GRAY), (0, 0), 9).astype(np.float32)
    mx, mn = o.max(axis=2).astype(np.int16), o.min(axis=2).astype(np.int16)
    neutro = cv2.blur(((mx - mn) < 30).astype(np.float32), (25, 25)) > 0.7
    a = (go < gn * 0.55) & (gn > 90) & neutro
    claro_osc = (gn <= 90)
    blanco = (mn > 200)
    oscuro = (mx < 90).astype(np.uint8)
    kh = int(H * 0.05)
    arriba = cv2.dilate(oscuro, np.ones((kh, 1), np.uint8), anchor=(0, kh - 1)) > 0
    abajo = cv2.dilate(oscuro, np.ones((kh, 1), np.uint8), anchor=(0, 0)) > 0
    b = blanco & arriba & abajo & claro_osc
    m = (a | b).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((int(H * 0.03), int(W * 0.02)), np.uint8))
    nn, lab, est, _ = cv2.connectedComponentsWithStats(m)
    out = []
    for k in range(1, nn):
        x, y, w, h, ar = est[k]
        if w < W * 0.04 or not (H * 0.025 < h < H * 0.25) or not (W * 0.15 < x + w / 2 < W * 0.85):
            continue
        letras = (blanco[y:y + h, x:x + w]).astype(np.uint8)
        nl, _, el, _ = cv2.connectedComponentsWithStats(letras)
        if len([e for e in el[1:] if 15 < e[4] < W * H * 0.001]) < 4:
            continue
        p = 6
        out.append((max(0, x - p), max(0, y0 + y - p), min(W, x + w + p), min(H, y0 + y + h + p)))
    return out


def copiar_rotulos(nuevo, org, tipos):
    H, W = org.shape[:2]
    for (x0, y0, x1, y1) in rotulos_subtitulo(org, nuevo):
        nuevo[y0:y1, x0:x1] = org[y0:y1, x0:x1]
    if "titulo" in tipos:                                  # texto negro arriba a la izquierda
        r = org[:int(H * 0.14), :int(W * 0.42)]
        m = cv2.dilate((r.max(axis=2) < 90).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        nuevo[:int(H * 0.14), :int(W * 0.42)][m] = r[m]
    if "numero" in tipos:                                  # número azul/violeta de la lista
        y1, x0, x1 = int(H * 0.24), int(W * 0.26), int(W * 0.44)
        r = org[:y1, x0:x1].astype(np.int16)
        azul = (r[:, :, 0] > 150) & (r[:, :, 0] - r[:, :, 2] > 60) & (r[:, :, 1] < 170)   # BGR
        m = cv2.dilate(azul.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        nuevo[:y1, x0:x1][m] = org[:y1, x0:x1][m]
    return nuevo


def _dist(a, b):
    """distancia de edición (para aceptar una letra mal leída por el OCR)"""
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
    return d[-1]


def parecida(txt, cambios):
    import re as _re
    for tok in _re.findall(r"[A-Za-zÁÉÍÓÚÑ]+", txt.upper()):
        for k in cambios:
            if tok == k.upper() or (len(k) >= 4 and _dist(tok, k.upper()) <= 1):
                return k
    return None


def preparar_parches(fps, W, H, ocupados):
    from rapidocr_onnxruntime import RapidOCR
    from PIL import Image, ImageDraw, ImageFont
    ocr = RapidOCR()
    out = {}
    for a, b, tref, cambios, siempre in PARCHES:
        r = subprocess.run([str(FFMPEG), "-v", "error", "-ss", str(tref), "-i", str(V), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           capture_output=True)
        ref = np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3).copy()
        res, _ = ocr(ref[:, :, ::-1])
        res = list(res or [])
        if any(not any(parecida(x[1], {k: 1}) for x in res) for k in cambios):     # palabra chica: probar también reducida (como revisar_idioma)
            k_ = 1280 / W
            res2, _ = ocr(cv2.resize(ref, (1280, int(H * k_)), interpolation=cv2.INTER_AREA)[:, :, ::-1])
            res += [([[q[0] / k_, q[1] / k_] for q in caja], txt, conf) for caja, txt, conf in (res2 or [])
                    if not any(parecida(txt, {k: 1}) and parecida(x[1], {k: 1}) for x in res for k in cambios)]
        letreros = []
        for caja, txt, conf in res or []:
            t = parecida(txt, cambios)
            if t:
                xs, ys = [q[0] for q in caja], [q[1] for q in caja]
                x0, y0, x1, y1 = min(xs) - 3, min(ys) - 3, max(xs) + 3, max(ys) + 3
                anillo = np.concatenate([ref[int(y0) - 4:int(y0) - 1, int(x0):int(x1)].reshape(-1, 3), ref[int(y1) + 1:int(y1) + 4, int(x0):int(x1)].reshape(-1, 3)])
                caja_px = ref[int(y0):int(y1), int(x0):int(x1)].reshape(-1, 3)
                fondo = tuple(int(c) for c in np.percentile(caja_px, 88, axis=0))   # el papel/cartel, no el borde
                tinta = tuple(int(c) for c in np.percentile(ref[int(y0):int(y1), int(x0):int(x1)].reshape(-1, 3), 3, axis=0))
                # letrero nuevo dibujado en coordenadas del cuadro de referencia (con margen para palabras más largas)
                cx, w0, h0 = (x0 + x1) / 2, x1 - x0, y1 - y0
                ancho = max(w0, w0 * len(cambios[t]) / max(1, len(t)) * 0.95)
                X0, X1 = cx - ancho / 2, cx + ancho / 2
                capa = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
                d.rectangle([x0, y0, x1, y1], fill=fondo[::-1] + (255,))
                tam = int(h0 * 0.9)
                while tam > 6:
                    f = ImageFont.truetype(FUENTE, tam)
                    bb = d.textbbox((0, 0), cambios[t], font=f)
                    if bb[2] - bb[0] <= ancho - 4 and bb[3] - bb[1] <= h0 - 2:
                        break
                    tam -= 1
                if X0 < x0 or X1 > x1:
                    d.rectangle([X0, y0, X1, y1], fill=fondo[::-1] + (255,))
                tx = cx - (bb[2] - bb[0]) / 2 - bb[0]; ty = (y0 + y1) / 2 - (bb[3] - bb[1]) / 2 - bb[1]
                d.text((tx, ty), cambios[t], font=f, fill=tinta[::-1] + (255,))
                letreros.append(np.array(capa)[:, :, [2, 1, 0, 3]])
                print(f"  letrero {t} -> {cambios[t]} en {int(x0)},{int(y0)} ({int(w0)}x{int(h0)})")
        if not letreros:
            print("  no encontré los letreros en", tref, "· leí:", ", ".join(x[1] for x in res or [])[:200]); continue
        capa = letreros[0]
        for l in letreros[1:]:
            m = l[:, :, 3:] > 0
            capa = np.where(m, l, capa)
        # movimiento cuadro a cuadro respecto del cuadro de referencia (homografía con ORB, bajo resolución)
        m = mascara(LW, LH)
        refb = cv2.resize(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), (LW, LH), interpolation=cv2.INTER_AREA)
        kp0, d0 = ORB.detectAndCompute(refb, m)
        n0, n1 = int(a * fps), int(b * fps)
        c = leer_bajo(n0, n1 - n0, fps)
        k = W / LW
        S = np.diag([k, k, 1.0]); Si = np.diag([1 / k, 1 / k, 1.0])
        bien = saltados = 0
        for j, f in enumerate(c):
            i = n0 + j
            if any(p0 <= i <= p1 for p0, p1 in ocupados) or f.mean() > 225:
                continue
            kp, dd = ORB.detectAndCompute(f, m)
            if dd is None:
                continue
            mt = BF.match(d0, dd)
            if len(mt) < 40:
                continue
            p0 = np.float32([kp0[x.queryIdx].pt for x in mt]); p1 = np.float32([kp[x.trainIdx].pt for x in mt])
            Hm, inl = cv2.findHomography(p0, p1, cv2.RANSAC, 3.0)
            if Hm is None or inl.sum() < 40:
                continue
            # ¿el cuadro es la imagen de referencia (quizás con un fundido a un color) o un cruce con otra escena?
            wr = cv2.warpPerspective(refb, Hm, (LW, LH)).astype(np.float32)
            dentro = (m > 0) & (cv2.warpPerspective(np.full_like(refb, 255), Hm, (LW, LH)) > 0)
            x, y = wr[dentro], f.astype(np.float32)[dentro]
            if x.size < 500:
                continue
            (al, be), *_ = np.linalg.lstsq(np.vstack([x, np.ones_like(x)]).T, y, rcond=None)
            if al < 0.2:                                                # casi todo fundido (destello, negro): no se dibuja
                saltados += 1
                continue
            if np.median(np.abs(y - (al * x + be))) > 6:                # cruce con otra escena (cambia toda la imagen)
                if not siempre:                                         # "siempre": la misma escena animada (giro, desenfoque)
                    saltados += 1
                    continue
                al, be = 1.0, 0.0
            out[i] = (capa, S @ Hm @ Si, float(al), float(be)); bien += 1
        print(f"  parche {a}-{b} s: {bien} cuadros con letreros cambiados ({saltados} en cruces con otra escena, sin tocar)", flush=True)
    return out


def main():
    W, H, fps = probe()
    plan = []
    global UMBRAL
    for t, nombre, tipos, *u in CAMBIOS:
        UMBRAL = u[0] if u else 9
        img = NUEVAS / nombre
        if not img.exists():
            print("FALTA", nombre, "(se deja la imagen original en ese tramo)"); continue
        a, b, Ts = tramo(t, fps)
        k = W / LW
        Tfull = {i: np.float32([[M[0, 0], M[0, 1], M[0, 2] * k], [M[1, 0], M[1, 1], M[1, 2] * k]]) for i, M in Ts.items()}
        Z = zoom_base(Tfull, W, H)
        nueva = cv2.resize(cv2.imread(str(img)), (W, H), interpolation=cv2.INTER_AREA)
        esc = [float(np.hypot(*M[:, 0])) for M in Ts.values()]
        if any(a <= q[1] and b >= q[0] for q in plan):
            a = max(a, max(q[1] for q in plan if a <= q[1] and b >= q[0]) + 1)
        print(f"{nombre}: tramo {a / fps:.2f}–{(b + 1) / fps:.2f} s ({b - a + 1} cuadros), zoom {min(esc):.3f}–{max(esc):.3f}, base {Z[0, 0]:.3f}")
        plan.append((a, b, Tfull, Z, nueva, tipos))
    parches = preparar_parches(fps, W, H, [(p[0], p[1]) for p in plan])
    if "--muestras" in sys.argv:
        TRAB.mkdir(parents=True, exist_ok=True)
        for a, b, Tf, Z, nueva, tipos in plan:      # un cuadro al medio de cada imagen reemplazada
            i = (a + b) // 2
            r = subprocess.run([str(FFMPEG), "-v", "error", "-ss", f"{i / fps:.4f}", "-i", str(V), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
            org = np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3)
            A = (np.vstack([Tf[i], [0, 0, 1]]) @ Z)[:2]
            nuevo = copiar_rotulos(cv2.warpAffine(nueva, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), org, tipos)
            cv2.imwrite(str(TRAB / f"muestra_cambio_{i / fps:.1f}.jpg"), cv2.resize(np.hstack([org, nuevo]), (1920, 540)))          # cuadros de prueba con los letreros, sin renderizar todo
        ks = sorted(parches)
        for i in sorted(set(ks[::12] + ks[-1:] + [k for j, k in enumerate(ks) if j and ks[j - 1] != k - 1])):
            r = subprocess.run([str(FFMPEG), "-v", "error", "-ss", f"{i / fps:.4f}", "-i", str(V), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
            org = np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3)
            capa, Hf, ga, gb = parches[i]
            w = cv2.warpPerspective(capa, Hf, (W, H)); al = w[:, :, 3:4].astype(np.float32) / 255
            col = np.clip(w[:, :, :3].astype(np.float32) * ga + gb, 0, 255)
            cv2.imwrite(str(TRAB / f"muestra_parche_{i / fps:.1f}.jpg"), cv2.resize((org * (1 - al) + col * al).astype(np.uint8), (960, 540)))
        return
    if "--analizar" in sys.argv or "--solo-analisis" in sys.argv or not (plan or parches):
        return
    if SAL.resolve() == V.resolve():
        sys.exit("La salida no puede ser el video original")
    sal = nombre_libre(SAL)
    if sal != SAL:
        print(f"{SAL.name} ya existe; se guarda como {sal.name}", flush=True)
    parcial = sal.with_name(sal.stem + ".parcial.mp4")
    dec = subprocess.Popen([str(FFMPEG), "-v", "error", "-i", str(V), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen([str(FFMPEG), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", f"{fps}",
                            "-i", "-", "-i", str(V), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                            "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(parcial)], stdin=subprocess.PIPE)
    tam = W * H * 3
    i = 0
    while True:
        buf = dec.stdout.read(tam)
        if len(buf) < tam:
            break
        for a, b, Tf, Z, nueva, tipos in plan:
            if a <= i <= b:
                org = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
                A = (np.vstack([Tf[i], [0, 0, 1]]) @ Z)[:2]
                nuevo = cv2.warpAffine(nueva, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                buf = copiar_rotulos(nuevo, org, tipos).tobytes()
                break
        if i in parches:
            capa, Hf, ga, gb = parches[i]
            org = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            w = cv2.warpPerspective(capa, Hf, (W, H), flags=cv2.INTER_LINEAR)
            al = w[:, :, 3:4].astype(np.float32) / 255
            if al.any():
                col = np.clip(w[:, :, :3].astype(np.float32) * ga + gb, 0, 255)      # mismo fundido que la imagen
                fr = org.astype(np.float32) * (1 - al) + col * al
                buf = fr.astype(np.uint8).tobytes()
        enc.stdin.write(buf)
        i += 1
        if i % 1800 == 0:
            print("cuadro", i, flush=True)
    enc.stdin.close(); re_, rd = enc.wait(), dec.wait()
    if re_ or rd:
        sys.exit(f"ERROR: ffmpeg terminó con código {re_ or rd}; el resultado incompleto quedó como {parcial.name} (no es una entrega)")
    n_esp = int(float(subprocess.run([FFPROBE, "-v", "error", "-count_packets", "-select_streams", "v", "-show_entries",
                                      "stream=nb_read_packets", "-of", "csv=p=0", str(V)], capture_output=True, text=True).stdout.strip() or 0))
    n_sal = int(float(subprocess.run([FFPROBE, "-v", "error", "-count_packets", "-select_streams", "v", "-show_entries",
                                      "stream=nb_read_packets", "-of", "csv=p=0", str(parcial)], capture_output=True, text=True).stdout.strip() or 0))
    if not n_esp or not n_sal or abs(n_esp - n_sal) > 1:
        sys.exit(f"ERROR: el video nuevo tiene {n_sal} cuadros y el original {n_esp}; quedó como {parcial.name} (no es una entrega)")
    parcial.rename(sal)
    informe = sal.with_suffix(".cambios.json")
    informe.write_text(json.dumps({"original": str(V), "salida": str(sal), "cuadros": n_sal,
                                   "tramos": [{"imagen": c[1], "desde_s": round(p[0] / fps, 2), "hasta_s": round((p[1] + 1) / fps, 2)}
                                              for c, p in zip([c for c in CAMBIOS if (NUEVAS / c[1]).exists()], plan)],
                                   "letreros_cuadros": len(parches)}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("LISTO", sal, "· informe:", informe.name)


if __name__ == "__main__":
    main()
