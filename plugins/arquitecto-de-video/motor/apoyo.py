# Material de apoyo (B-roll) para videos de una persona hablando (0.15): imágenes o clips que entran encima de la
# persona en la frase que los nombra. La voz sigue debajo (el audio del clip de apoyo no se usa). Solo lee el material:
# nunca lo copia, mueve ni modifica. Solo material propio o con licencia para uso comercial.
#
#   python apoyo.py "<proyecto>" proponer ["<carpeta de material>"]
#       Lee la transcripción del video ya editado y los nombres de archivo (y etiquetas) de la carpeta, y propone dónde
#       poner cada uno -> 06_RECETA/apoyo_propuesto.json. No cambia el proyecto: la persona aprueba y se copia la lista
#       "apoyo" a proyecto.json. Carpeta por defecto: "apoyo_material" de proyecto.json o 00_APOYO del proyecto.
#       Etiquetas opcionales: un etiquetas.json en la carpeta ({"playa.mp4": ["mar", "vacaciones"]}).
#   python apoyo.py "<proyecto>" aplicar
#       Prueba suelta sobre el armado: tmp/solo_video.mp4 -> tmp/solo_video_con-apoyo.mp4 (no reemplaza nada).
#       En el flujo normal no hace falta: grabado.py armar lo aplica solo si proyecto.json trae "apoyo".
#
# En proyecto.json:
#   "apoyo": [{"en": "frase exacta", "archivo": "00_APOYO/playa.mp4", "dura": 3, "modo": "completo"},
#             {"en": {"frase": "la segunda vez", "despues": "frase anterior", "desfase": 0.3}, "archivo": "foto.jpg", "modo": "pip"},
#             {"en": {"segundo": 42.5}, "archivo": "grafico.png", "dura": 4, "modo": "dividido"}]
#   modo: "completo" (llena la pantalla), "pip" (recuadro en una esquina; la persona sigue de fondo) o "dividido"
#   (pantalla partida: la persona en una mitad, el apoyo en la otra; en 9:16 el apoyo va arriba).
#   Opcionales por inserción: "desde" (segundo del clip donde empieza), "esquina" y "tam" (pip), "lado" (dividido:
#   lado de la persona, "izq" o "der"), "fundido" (segundos, 0.15).
import json, sys, unicodedata
from pathlib import Path
from estudio import FFMPEG, run, buscar, norm
import capas                                    # se reutilizan sus piezas (máscaras, posiciones, colores de marca)
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

VIDEO = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm"}
VACIAS = set("de la el los las un una unos unas y o a en con por para que se del al lo su sus es son como mas muy pero si no "
             "ya me mi te tu le nos este esta esto ese esa eso hay fue ser estar tiene tener cuando donde porque sobre entre "
             "img image imagen foto video clip copia final nuevo nueva vid dsc mov pxl screenshot captura".split())


def cuando(pals, en):
    """Segundo (del video editado) de un momento escrito como "frase", {"frase", "despues", "desfase"} o {"segundo"}."""
    if isinstance(en, (int, float)):
        return float(en)
    if isinstance(en, str):
        en = {"frase": en}
    if "frase" not in en:
        return float(en["segundo"]) + float(en.get("desfase", 0))
    desde = 0.0
    if "despues" in en:
        d = en["despues"]
        desde = float(d) if isinstance(d, (int, float)) else buscar(pals, d)
    obj = norm(en["frase"])
    toks = [(norm(w["word"]) or [""])[0] for w in pals]
    for i in range(len(toks) - len(obj) + 1):
        if toks[i:i + len(obj)] == obj and pals[i]["start"] >= desde - 0.01:
            return pals[i]["start"] + float(en.get("desfase", 0))
    raise ValueError(f"no encontré la frase «{en['frase']}» en la transcripción")


def _cara_en(base, t):
    """Centro (x, y) de la cara en el armado en ese segundo, en fracción del cuadro; None si no se ve."""
    try:
        import caras
        im = caras.cuadro(base, t)
        c = caras.cara_principal(im) if im is not None else None
        return (c[0], c[1]) if c else None
    except Exception:
        return None


def _tam(f):
    if capas.es_img(f):
        from PIL import Image
        with Image.open(f) as im:
            return im.size[0], im.size[1], 0.0
    return capas.info(f)


def aplicar(pr, base, salida, items, W, H, FPS, pals=None):
    """Pone las inserciones de `items` sobre el video `base` (sin audio) y escribe `salida`. Un solo paso de ffmpeg.
    Devuelve la lista de lo que se puso ([{"a", "b", "archivo", "modo"}]) y la deja en tmp/apoyo_aplicado.json.
    Lo que no se puede poner (frase que no está, archivo que falta) se avisa y se salta: el armado no se detiene."""
    base, salida = Path(base), Path(salida)
    if pals is None:
        from estudio import palabras
        try:
            _, pals = palabras(pr)
        except (SystemExit, Exception):
            pals = []
    dur_base = capas.info(base)[2]
    plan = []
    for d in items:
        try:
            a = max(0.0, cuando(pals, d["en"]))
        except (ValueError, KeyError) as ex:
            print("AVISO apoyo:", ex, "(se salta)", flush=True)
            continue
        f = pr.ruta(d.get("archivo", ""))
        if not d.get("archivo") or not f.is_file():
            print(f"AVISO apoyo: no encuentro el archivo {f} (se salta)", flush=True)
            continue
        ew, eh, ed = _tam(f)
        dura, desde = float(d.get("dura", 3)), float(d.get("desde", 0))
        if not capas.es_img(f):
            dura = min(dura, max(0.0, ed - desde))
        b = min(a + dura, dur_base)
        if b - a < 0.4 or not ew or not eh:
            print(f"AVISO apoyo: {f.name} no cabe en el segundo {a:.1f} (se salta)", flush=True)
            continue
        plan.append({"a": round(a, 3), "b": round(b, 3), "f": f, "ew": ew, "eh": eh, "desde": desde, "d": d,
                     "modo": d.get("modo", "completo")})
    plan.sort(key=lambda p: p["a"])
    for ant, sig in zip(plan, plan[1:]):          # dos inserciones no se pisan: la anterior termina donde empieza la otra
        ant["b"] = min(ant["b"], sig["a"])
    plan = [p for p in plan if p["b"] - p["a"] >= 0.4]
    if not plan:
        import shutil
        shutil.copy2(base, salida)
        return []
    ins, fc, cur = ["-i", base], [], "[0:v]"
    n_in = 1

    def entrada(args):
        nonlocal n_in
        ins.extend(args)
        n_in += 1
        return n_in - 1

    for k, p in enumerate(plan):
        a, b, f, d = p["a"], p["b"], p["f"], p["d"]
        dur = b - a
        fd = min(float(d.get("fundido", 0.15)), dur / 3)
        i_f = entrada(["-loop", "1", "-t", f"{dur:.3f}", "-framerate", str(FPS), "-i", f] if capas.es_img(f)
                      else ["-ss", f"{p['desde']:.3f}", "-t", f"{dur:.3f}", "-i", f])
        # entra y sale con un fundido corto y se corre al segundo donde va
        cola = (f"fps={FPS},setpts=PTS-STARTPTS,format=yuva420p,fade=t=in:st=0:d={fd:.3f}:alpha=1,"
                f"fade=t=out:st={dur - fd:.3f}:d={fd:.3f}:alpha=1,setpts=PTS+{a:.3f}/TB")
        act = f":enable='between(t,{a:.3f},{b:.3f})'"
        llenar = lambda w, h: f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"
        cara = _cara_en(base, (a + b) / 2) if p["modo"] in ("pip", "dividido") else None
        if p["modo"] == "pip":
            w = int(W * float(d.get("tam", 0.5 if H > W else 0.38))) // 2 * 2
            h = int(w * p["eh"] / p["ew"]) // 2 * 2
            borde = max(4, w // 60)
            esquina = d.get("esquina") or ("arriba_izq" if cara and cara[0] > 0.5 else "arriba_der")    # lejos de la cara
            x, y = capas.posicion(esquina, W, H, w + 2 * borde, h + 2 * borde, int(W * 0.03))
            if H > W:
                y = max(y, int(H * 0.14)) if esquina.startswith("arriba") else min(y, int(H * 0.78) - h - 2 * borde)   # zona segura
            mk = capas.forma_png(w, h, "redondeado", capas.TMP / f"apoyo_mascara_{k}.png")
            marco = capas.forma_png(w + 2 * borde, h + 2 * borde, "redondeado", capas.TMP / f"apoyo_marco_{k}.png", borde=1,
                                    color=capas.color_rgb(d.get("borde", "acento"), pr.cfg.get("canal")))
            i_m = entrada(["-loop", "1", "-t", f"{dur:.3f}", "-framerate", str(FPS), "-i", mk])
            i_b = entrada(["-loop", "1", "-t", f"{dur:.3f}", "-framerate", str(FPS), "-i", marco])
            fc += [f"[{i_f}:v]{llenar(w, h)},format=rgba[p{k}]", f"[{i_m}:v]format=gray[m{k}]",
                   f"[p{k}][m{k}]alphamerge,{cola}[s{k}]", f"[{i_b}:v]{cola}[b{k}]",
                   f"{cur}[b{k}]overlay={x}:{y}:eof_action=pass{act}[q{k}]",
                   f"[q{k}][s{k}]overlay={x + borde}:{y + borde}:eof_action=pass{act}[o{k}]"]
        elif p["modo"] == "dividido":
            if H > W:                 # 9:16: el apoyo arriba y la persona abajo
                hw, hh = W, H // 2 // 2 * 2
                py = int(min(max((cara[1] if cara else 0.4) * H - hh / 2, 0), H - hh))
                rec, pos_p, pos_a, linea = f"crop={hw}:{hh}:0:{py}", f"0:{H - hh}", "0:0", f"drawbox=x=0:y={hh - 3}:w={W}:h=6:color=black:t=fill"
            else:                     # 16:9: mitad y mitad; la persona queda del lado donde ya está
                hw, hh = W // 2 // 2 * 2, H
                lado = d.get("lado") or ("der" if cara and cara[0] > 0.5 else "izq")
                px = int(min(max((cara[0] if cara else 0.5) * W - hw / 2, 0), W - hw))
                rec = f"crop={hw}:{hh}:{px}:0"
                pos_p, pos_a = ("0:0", f"{W - hw}:0") if lado == "izq" else (f"{W - hw}:0", "0:0")
                linea = f"drawbox=x={W // 2 - 3}:y=0:w=6:h={H}:color=black:t=fill"
            fc += [f"{cur}split[c{k}][d{k}]", f"[d{k}]{rec}[r{k}]", f"[{i_f}:v]{llenar(hw, hh)},{cola}[s{k}]",
                   f"[c{k}][r{k}]overlay={pos_p}{act}[q{k}]",
                   f"[q{k}][s{k}]overlay={pos_a}:eof_action=pass{act},{linea}{act}[o{k}]"]
        else:                         # completo
            fc += [f"[{i_f}:v]{llenar(W, H)},{cola}[s{k}]", f"{cur}[s{k}]overlay=0:0:eof_action=pass{act}[o{k}]"]
        cur = f"[o{k}]"
    fc.append(f"{cur}format=yuv420p[v]")
    run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[v]", "-an", "-t", f"{dur_base:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-r", str(FPS), "-pix_fmt", "yuv420p", *SIN_METADATOS, salida])
    hecho = [{"a": p["a"], "b": p["b"], "archivo": str(p["f"]), "modo": p["modo"]} for p in plan]
    (pr.tmp / "apoyo_aplicado.json").write_text(json.dumps(hecho, ensure_ascii=False, indent=1), encoding="utf-8")
    for h_ in hecho:
        print(f"  apoyo {h_['a']:7.2f}-{h_['b']:7.2f}  {Path(h_['archivo']).name}  ({h_['modo']})", flush=True)
    return hecho


# ---------- proponer: qué material calza con qué frase ----------
def raiz(t):
    """Palabra sin tildes ni plural, para comparar «casas» con «casa» o «inversión» con «inversiones»."""
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch) and ch.isalpha())
    if len(t) > 5 and t.endswith("es"):
        return t[:-2]
    if len(t) > 4 and t.endswith("s"):
        return t[:-1]
    return t


def etiquetas_de(f, extra):
    """Raíces con las que se reconoce un archivo: las palabras de su nombre más las de etiquetas.json."""
    import re
    textos = re.split(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", f.stem) + [p for e in extra.get(f.name, []) for p in str(e).split()]
    return {r for r in (raiz(t) for t in textos if t.lower() not in VACIAS) if len(r) >= 3 and r not in VACIAS}


def proponer(pr, carpeta=None):
    from estudio import palabras, escribir_entrega
    _, pals = palabras(pr)
    carpeta = Path(carpeta) if carpeta else pr.ruta(pr.cfg.get("apoyo_material", "00_APOYO"))
    if not carpeta.is_dir():
        sys.exit(f"No encuentro la carpeta de material de apoyo {carpeta}. Pásala como argumento o en proyecto.json -> apoyo_material")
    extra = {}
    if (carpeta / "etiquetas.json").exists():
        extra = json.loads((carpeta / "etiquetas.json").read_text(encoding="utf-8"))
    archivos = sorted(f for f in carpeta.rglob("*") if f.is_file() and (f.suffix.lower() in VIDEO or capas.es_img(f)))
    raices = [raiz(w["word"]) for w in pals]
    cand, sin = [], []
    for f in archivos:
        tags = etiquetas_de(f, extra)
        mejor = None
        for i, r in enumerate(raices):
            if r in tags:
                vistos = sorted({x for x in raices[i:i + 12] if x in tags})          # etiquetas dichas en la misma frase (unos 5 s)
                if mejor is None or len(vistos) > len(mejor[1]):
                    mejor = (i, vistos)
        if mejor is None:
            sin.append(f.name)
        else:
            cand.append((len(mejor[1]), mejor[0], f, mejor[1]))
    sep = float(pr.cfg.get("apoyo_separacion", 8))
    lista, puestos = [], []
    for puntos, i, f, vistos in sorted(cand, key=lambda c: (-c[0], c[1])):    # primero lo que calza mejor
        t = pals[i]["start"]
        if any(abs(t - u) < sep for u in puestos):
            sin.append(f"{f.name} (calza en {t:.1f} s, pero queda a menos de {sep:g} s de otra inserción)")
            continue
        puestos.append(t)
        en = {"segundo": round(t, 2)}
        for n in range(3, 9):                    # una frase corta y exacta que solo aparezca ahí; si no hay, por segundo
            frase = " ".join(w["word"] for w in pals[i:i + n])
            try:
                if abs(buscar(pals, frase) - t) < 0.01:
                    en = frase
                    break
            except ValueError:
                break
        try:
            ruta = str(f.relative_to(pr.dir)).replace("\\", "/")
        except ValueError:
            ruta = str(f)
        dura = 3.0 if capas.es_img(f) else round(min(4.0, capas.info(f)[2] or 3.0), 1)
        lista.append({"en": en, "archivo": ruta, "dura": dura, "modo": "completo", "segundo": round(t, 2),
                      "motivo": "se dice: " + ", ".join(vistos)})
    lista.sort(key=lambda d: d["segundo"])
    doc = {"nota": "Propuesta de material de apoyo. Revisar una por una (¿la imagen muestra de verdad lo que se dice?), ajustar "
                   "\"dura\" y \"modo\" (completo, pip, dividido) y copiar la lista \"apoyo\" aprobada a proyecto.json. "
                   "\"segundo\" y \"motivo\" son solo para revisar.",
           "carpeta": str(carpeta), "apoyo": lista, "sin_lugar": sin}
    destino = pr.dir / "06_RECETA" / "apoyo_propuesto.json"
    guardada = escribir_entrega(destino, json.dumps(doc, ensure_ascii=False, indent=1) + "\n")     # la propuesta anterior no se pierde
    if guardada:
        print(f"la propuesta anterior quedó guardada como {guardada.name}", flush=True)
    print(f"{len(lista)} inserciones propuestas de {len(archivos)} archivos; {len(sin)} sin lugar. Revisar {destino}", flush=True)
    for d in lista:
        print(f"  {d['segundo']:7.2f}  {Path(d['archivo']).name}  ({d['motivo']})")


if __name__ == "__main__":
    paso = next((a for a in sys.argv[1:] if a in ("proponer", "aplicar")), None)
    if paso is None:
        sys.exit('Uso: python apoyo.py "<proyecto>" proponer ["<carpeta de material>"]  |  python apoyo.py "<proyecto>" aplicar')
    from estudio import Proyecto, nombre_libre
    _pr = Proyecto()
    if paso == "proponer":
        _resto = [a for a in sys.argv[sys.argv.index("proponer") + 1:] if not a.startswith("-")]
        proponer(_pr, _resto[0] if _resto else None)
    else:
        _base = _pr.tmp / "solo_video.mp4"
        if not _base.exists():
            sys.exit(f"Falta {_base}: primero hay que armar el video")
        if not _pr.cfg.get("apoyo"):
            sys.exit('proyecto.json no trae la lista "apoyo"')
        _sal = nombre_libre(_pr.tmp / "solo_video_con-apoyo.mp4")       # prueba suelta: nunca encima del armado
        aplicar(_pr, _base, _sal, _pr.cfg["apoyo"], _pr.ancho, _pr.alto, _pr.fps)
        print("LISTO", _sal, flush=True)
