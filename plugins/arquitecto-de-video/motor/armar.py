# Arma la imagen del video desde la receta: movimiento de camara en cada imagen, planos dentro
# de una misma imagen, transiciones como en CapCut y clips de Flow (escena_NNN.mp4) insertados solos.
#   python armar.py "C:\ruta\video"            video completo
#   python armar.py "C:\ruta\video" --hasta 60  borrador de los primeros 60 s
import sys
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime
from estudio import Proyecto, FFMPEG, FFPROBE, run, duracion_medio
import transiciones

pr = Proyecto()
HASTA = float(sys.argv[sys.argv.index("--hasta") + 1]) if "--hasta" in sys.argv else None
FPS, W, H = pr.fps, pr.ancho, pr.alto
TR = {k: tuple(v) for k, v in pr["transiciones"].items() if k in ("normal", "capitulo", "plano")}
VARIAR = list(pr["transiciones"].get("variar", []))          # rota entre estas en las escenas normales
POR_ESCENA = {int(k): tuple(v) for k, v in pr["transiciones"].get("por_escena", {}).items()}
CAPITULOS = set(int(x) for x in pr["escenas_capitulo"])
ALIAS = {int(k): int(v) for k, v in pr["alias_clips"].items()}
PLANOS = {int(k): v for k, v in pr["planos"].items()}
MOVS = pr["movimientos"]
PZ = pr.tmp / "piezas"


def escalar(mov, seg):
    (z0, x0, y0), (z1, x1, y1) = mov
    f = min(1.0, seg / 6.0)   # escenas cortas: movimiento mas corto, misma velocidad aproximada
    return (z0, x0, y0), (z0 + (z1 - z0) * f, x0 + (x1 - x0) * f, y0 + (y1 - y0) * f)


def tomas():
    lista, k = [], 0
    for r in pr.escenas():
        n = r["n"]
        a, b = round(r["t0"] * FPS), round(r["t1"] * FPS)
        if HASTA and a >= HASTA * FPS:
            break
        if HASTA:
            b = min(b, round(HASTA * FPS))
        img = pr.imagenes / r["archivo"]
        if not img.exists():
            sys.exit(f"Escena {n}: no existe la imagen {img}")
        if n in POR_ESCENA:
            t_escena = POR_ESCENA[n]
        elif n in CAPITULOS:
            t_escena = TR["capitulo"]
        elif VARIAR:
            t_escena = (VARIAR[k % len(VARIAR)], TR["normal"][1])
        else:
            t_escena = TR["normal"]
        clip = pr.clips / f"escena_{ALIAS.get(n, n):03d}.mp4"
        if n in PLANOS:   # planos de camara; si hay clip, el clip reemplaza el primer plano
            cortes = PLANOS[n]
            for i, (seg, c0, c1) in enumerate(cortes):
                pa = round(seg * FPS) if i else a
                pb = min(round(cortes[i + 1][0] * FPS) if i + 1 < len(cortes) else b, b)
                if pa >= pb:
                    continue
                propio = pr.clips / f"escena_{ALIAS.get(n, n):03d}_p{i + 1}.mp4"   # clip hecho para este plano
                t_p = t_escena if i == 0 else TR["plano"]
                if i == 0 and clip.exists():
                    lista.append(dict(n=n, tipo="clip", src=clip, a=pa, b=pb, cam=None, t=t_p, c0=pa, clave=str(n)))
                elif i > 0 and propio.exists():
                    lista.append(dict(n=n, tipo="clip", src=propio, a=pa, b=pb, cam=None, t=t_p, c0=pa, clave=f"{n}_p{i + 1}"))
                elif i > 0 and clip.exists() and pr.cfg.get("planos_sobre_clip", True):
                    # el clip sigue corriendo y el plano cerrado se hace sobre el clip (no sobre la imagen quieta)
                    lista.append(dict(n=n, tipo="clipcam", src=clip, a=pa, b=pb, cam=(c0, c1), t=t_p, c0=a, clave=str(n)))
                else:
                    lista.append(dict(n=n, tipo="img", src=img, a=pa, b=pb, cam=(c0, c1), t=t_escena if i == 0 else TR["plano"]))
        elif clip.exists():
            cf = int(duracion_medio(clip) * FPS) - 4
            if cf >= (b - a) - 45:   # si falta 1,5 s o menos, se sostiene el ultimo cuadro del clip
                lista.append(dict(n=n, tipo="clip", src=clip, a=a, b=b, cam=None, t=t_escena, c0=a, clave=str(n)))
            else:   # el clip no alcanza: clip y despues la imagen con movimiento
                lista.append(dict(n=n, tipo="clip", src=clip, a=a, b=a + cf, cam=None, t=t_escena, c0=a, clave=str(n)))
                lista.append(dict(n=n, tipo="img", src=img, a=a + cf, b=b,
                                  cam=escalar(MOVS[k % len(MOVS)], (b - a - cf) / FPS), t=TR["normal"]))
        else:
            lista.append(dict(n=n, tipo="img", src=img, a=a, b=b, cam=escalar(MOVS[k % len(MOVS)], (b - a) / FPS), t=t_escena))
        k += 1
    lista[0]["t"] = None
    for i, s in enumerate(lista):   # medias transiciones antes y despues de cada toma
        d_in = s["t"][1] if s["t"] else 0
        d_out = lista[i + 1]["t"][1] if i + 1 < len(lista) else 0
        s["pre"], s["post"] = d_in // 2, d_out // 2
        s["ea"] = s["a"] - s["pre"]
        s["ne"] = (s["b"] + s["post"]) - s["ea"]
        if s["b"] - s["a"] < s["pre"] + s["post"] + 2:
            sys.exit(f"Escena {s['n']}: dura menos que sus transiciones; alarga la escena o acorta la transicion")
    return lista


SUB = 2 if W * H <= 1920 * 1080 else 1.5   # en 1440p/4K se trabaja a 1,5x para no hacerlo eterno
CW, CH = int(W * SUB) // 2 * 2, int(H * SUB) // 2 * 2
COVER = f"scale={CW}:{CH}:force_original_aspect_ratio=increase,crop={CW}:{CH},setsar=1"


def flujo(s, idx, ini, cant, lab):
    if s["tipo"] in ("clip", "clipcam"):
        desde = ini + max(0, s["ea"] - s.get("c0", s["ea"]))   # cuadro del clip que corresponde a este momento
        base = (f"[{idx}:v]scale={W if s['tipo'] == 'clip' else CW}:{H if s['tipo'] == 'clip' else CH}:force_original_aspect_ratio=increase,"
                f"crop={W if s['tipo'] == 'clip' else CW}:{H if s['tipo'] == 'clip' else CH},setsar=1,fps={FPS},"
                f"tpad=stop_mode=clone:stop_duration=60,trim=start_frame={desde}:end_frame={desde + cant},setpts=PTS-STARTPTS")
        if s["tipo"] == "clip":
            return base + f",format=yuv420p[{lab}]"
        (z0, x0, y0), (z1, x1, y1) = s["cam"]
        e = f"(1-cos(PI*(on+{ini})/{max(s['ne'] - 1, 1)}))/2"
        z = f"{z0}+({z1 - z0})*{e}"
        x = f"max(0,min(iw-iw/zoom,({x0}+({x1 - x0})*{e})*iw-iw/zoom/2))"
        y = f"max(0,min(ih-ih/zoom,({y0}+({y1 - y0})*{e})*ih-ih/zoom/2))"
        return base + f",zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS},format=yuv420p,setsar=1[{lab}]"
    (z0, x0, y0), (z1, x1, y1) = s["cam"]
    e = f"(1-cos(PI*(on+{ini})/{max(s['ne'] - 1, 1)}))/2"
    z = f"{z0}+({z1 - z0})*{e}"
    x = f"max(0,min(iw-iw/zoom,({x0}+({x1 - x0})*{e})*iw-iw/zoom/2))"
    y = f"max(0,min(ih-ih/zoom,({y0}+({y1 - y0})*{e})*ih-ih/zoom/2))"
    return (f"[{idx}:v]{COVER},zoompan=z='{z}':x='{x}':y='{y}':d={cant}:s={W}x{H}:fps={FPS},"
            f"format=yuv420p,setsar=1[{lab}]")


ENCODE = ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(pr["video"]["crf"]), "-pix_fmt", "yuv420p",
          "-r", str(FPS), "-profile:v", "high", "-g", str(FPS * 2)]


def pieza(trabajo):
    clase, datos, destino = trabajo
    parcial = destino.with_suffix(".parcial.mp4")
    if clase == "cuerpo":
        s = datos
        ini, cant = 2 * s["pre"], (s["b"] - s["post"]) - (s["a"] + s["pre"])
        cmd = [FFMPEG, "-v", "error", "-y", "-i", s["src"], "-filter_complex", flujo(s, 0, ini, cant, "v"),
               "-map", "[v]", "-frames:v", cant]
    else:
        s1, s2 = datos
        tipo, d = s2["t"]
        ini1 = (s1["b"] - s1["post"]) - s1["ea"]
        fc = (flujo(s1, 0, ini1, d, "p") + ";" + flujo(s2, 1, 0, d, "q") + ";"
              + transiciones.cadena(tipo, d, FPS, W, H, "p", "q", "v"))
        cmd = [FFMPEG, "-v", "error", "-y", "-i", s1["src"], "-i", s2["src"], "-filter_complex", fc,
               "-map", "[v]", "-frames:v", d]
    run(cmd + ENCODE + [parcial])
    parcial.replace(destino)
    return destino


def main():
    PZ.mkdir(parents=True, exist_ok=True)
    for viejo in PZ.glob("*.mp4"):
        viejo.unlink()
    lista = tomas()
    trabajos = []
    for i, s in enumerate(lista):
        trabajos.append(("cuerpo", s, PZ / f"p{len(trabajos):04d}.mp4"))
        if i + 1 < len(lista):
            trabajos.append(("trans", (s, lista[i + 1]), PZ / f"p{len(trabajos):04d}.mp4"))
    total = lista[-1]["b"] - lista[0]["a"]
    clips = sorted({s["src"].name for s in lista if s["tipo"] in ("clip", "clipcam")})
    print(f"{len(lista)} tomas, {len(trabajos)} piezas, {total / FPS:.2f} s; clips de Flow: {', '.join(clips) or 'ninguno'}", flush=True)
    with ThreadPoolExecutor(max_workers=3) as ex:
        archivos = list(ex.map(pieza, trabajos))
    (PZ / "lista.txt").write_text("".join(f"file '{a.name}'\n" for a in archivos), encoding="utf-8")
    salida = pr.tmp / ("solo_video.mp4" if not HASTA else f"solo_video_borrador_{int(HASTA)}s.mp4")
    run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", PZ / "lista.txt", "-c", "copy", salida])
    n = int(run([FFPROBE, "-v", "error", "-count_packets", "-select_streams", "v", "-show_entries",
                 "stream=nb_read_packets", "-of", "csv=p=0", salida]).strip())
    print(f"cuadros: {n} (esperados {total}) {'OK' if n == total else 'REVISAR'}", flush=True)
    clips = {}
    for s in lista:
        if s["tipo"] == "clip" and s["clave"] not in clips:
            clips[s["clave"]] = {"archivo": s["src"].name, "mtime": s["src"].stat().st_mtime, "inicio_s": round(s["a"] / FPS, 3),
                                  "dura_s": round((s["b"] - s["a"]) / FPS, 3)}
    (salida.with_suffix(".json")).write_text(json.dumps(
        {"video": salida.name, "fecha": datetime.now().isoformat(timespec="seconds"), "hasta": HASTA,
         "receta": pr.receta.name, "clips": clips}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"clips de Flow dentro del video: {len(clips)} -> " + (", ".join(f"escena {k}" for k in clips) or "ninguno"), flush=True)
    print("LISTO", salida, flush=True)


if __name__ == "__main__":
    main()
