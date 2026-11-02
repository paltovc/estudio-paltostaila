# Recorta los silencios largos de la voz (la voz sintetica deja ~1 s despues de cada frase) y
# reajusta solos todos los tiempos: transcripcion, receta, planos y efectos con segundo fijo.
# Los audios originales no se tocan: la voz recortada queda en 02_VOZ_RECORTADA.
#   python recortar_pausas.py "C:\ruta\video"                    ver cuanto se ahorra (no cambia nada)
#   python recortar_pausas.py "C:\ruta\video" --aplicar          recortar y reajustar
#   opciones: --umbral 0.6 (pausas mas largas que esto se acortan)  --deja 0.35 (lo que queda de cada pausa)
import bisect, csv, json, shutil, sys, wave
from pathlib import Path
from estudio import Proyecto, FFMPEG, run, cargar, mmss, duracion_medio, t2s

pr = Proyecto()
opt = lambda k, d: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
UMBRAL, DEJA = opt("--umbral", 0.6), opt("--deja", 0.35)


def cortes():
    pals = [w for s in cargar(pr) for w in s["words"]]
    out = []
    if pals and pals[0]["start"] > UMBRAL + 0.3:   # silencio al inicio: deja 0,3 s
        out.append((0.0, pals[0]["start"] - 0.3))
    for a, b in zip(pals, pals[1:]):
        hueco = b["start"] - a["end"]
        if hueco > UMBRAL:
            out.append((a["end"] + DEJA / 2, b["start"] - DEJA / 2))
    return [(round(x, 3), round(y, 3)) for x, y in out if y - x > 0.05]


class Mapa:
    def __init__(self, cs):
        self.cs = cs
        self.ini = [c[0] for c in cs]
        self.acum = []
        t = 0.0
        for a, b in cs:
            t += b - a
            self.acum.append(t)

    def __call__(self, t):
        i = bisect.bisect_right(self.ini, t) - 1
        if i < 0:
            return t
        a, b = self.cs[i]
        quitado_antes = self.acum[i - 1] if i else 0.0
        if t < b:   # dentro de un tramo quitado: cae al punto de corte
            return round(a - quitado_antes, 3)
        return round(t - self.acum[i], 3)


def main():
    if pr.cfg.get("recorte"):
        sys.exit(f"Este proyecto ya tiene las pausas recortadas ({pr.cfg['recorte']}). Para repetir, vuelve a proyecto_antes_de_recortar.json.")
    cs = cortes()
    ahorro = sum(b - a for a, b in cs)
    dur = pr.duracion()
    print(f"{len(cs)} pausas largas; se ahorran {ahorro:.1f} s: {mmss(dur)} -> {mmss(dur - ahorro)}")
    if "--aplicar" not in sys.argv:
        print("Nada cambiado. Para aplicar: agregar --aplicar")
        return
    f = Mapa(cs)
    # 1. voz recortada (wav sin perdida)
    destino = pr.dir / "02_VOZ_RECORTADA"
    destino.mkdir(exist_ok=True)
    auds = pr.audios()
    ins = sum([["-i", a] for a in auds], [])
    completa = pr.tmp / "voz_completa.wav"
    run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex", f"concat=n={len(auds)}:v=0:a=1", "-c:a", "pcm_s16le", completa])
    with wave.open(str(completa), "rb") as w:   # el corte se hace en Python: sin limites de largo del filtro
        sr, nc, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        datos = w.readframes(w.getnframes())
    paso = nc * sw
    guardar, t = [], 0.0
    for a, b in cs:
        guardar.append((t, a))
        t = b
    guardar.append((t, len(datos) / paso / sr))
    with wave.open(str(destino / "voz_recortada.wav"), "wb") as w:
        w.setnchannels(nc); w.setsampwidth(sw); w.setframerate(sr)
        for a, b in guardar:
            w.writeframes(datos[int(a * sr) * paso:int(b * sr) * paso])
    completa.unlink()
    nueva = duracion_medio(destino / "voz_recortada.wav")
    print(f"voz recortada: {mmss(nueva)} (esperado {mmss(dur - ahorro)})")
    # 2. transcripcion
    tr = json.loads(pr.transcripcion.read_text(encoding="utf-8"))
    for s in tr["segments"]:
        s["start"], s["end"] = f(s["start"]), f(s["end"])
        for w in s.get("words", []):
            if "start" in w:
                w["start"], w["end"] = f(w["start"]), f(w["end"])
    nueva_tr = pr.dir / "06_RECETA" / "transcripcion_recortada.json"
    nueva_tr.parent.mkdir(exist_ok=True)
    nueva_tr.write_text(json.dumps(tr, ensure_ascii=False), encoding="utf-8")
    # 3. receta
    with open(pr.receta, encoding="utf-8-sig", newline="") as fh:
        lector = csv.DictReader(fh, delimiter=";")
        campos, filas = lector.fieldnames, list(lector)
    inicio_viejo = {r["numero"]: t2s(r["inicio"]) for r in filas}
    for r in filas:
        a, b = f(t2s(r["inicio"])), f(t2s(r["fin"]))
        r["inicio"], r["fin"], r["duracion"] = mmss(a), mmss(b), f"{b - a:.2f}"
    filas[-1]["fin"] = mmss(nueva)
    filas[-1]["duracion"] = f"{nueva - t2s(filas[-1]['inicio']):.2f}"
    nueva_receta = pr.dir / "06_RECETA" / "receta_recortada.csv"
    with open(nueva_receta, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, delimiter=";")
        w.writeheader(); w.writerows(filas)
    # 4. proyecto.json (copia de respaldo primero)
    pj = pr.dir / "proyecto.json"
    shutil.copy2(pj, pr.dir / "proyecto_antes_de_recortar.json")
    cfg = json.loads(pj.read_text(encoding="utf-8"))
    cfg["audios"] = "02_VOZ_RECORTADA/voz_recortada.wav"
    cfg.setdefault("carpetas", {})
    cfg["carpetas"]["transcripcion"] = "06_RECETA/transcripcion_recortada.json"
    cfg["carpetas"]["receta"] = "06_RECETA/receta_recortada.csv"
    for n, cortes_plano in cfg.get("planos", {}).items():
        for p in cortes_plano:
            p[0] = f(p[0]) if p[0] else 0.0
    for e in cfg.get("sonidos", {}).get("efectos", []) + cfg.get("sonidos", {}).get("lapiz", []):
        if "segundo" in e:
            e["segundo"] = f(e["segundo"])
    rc = cfg.get("sonidos", {}).get("recorte_clip", {})
    for n, d in list(rc.items()):   # sonido de un clip recortado a mano: se reajusta igual que la escena
        t0 = inicio_viejo.get(str(n), 0.0)
        rc[n] = round(f(t0 + float(d)) - f(t0), 3)
    cfg["recorte"] = {"umbral": UMBRAL, "deja": DEJA, "pausas": len(cs), "ahorro_s": round(ahorro, 1)}
    pj.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    cortas = [r["numero"] for r in filas if float(r["duracion"]) < 1.2]
    print("listo: voz en 02_VOZ_RECORTADA, transcripcion y receta recortadas, proyecto.json actualizado")
    print("respaldo: proyecto_antes_de_recortar.json")
    if cortas:
        print("AVISO escenas que quedaron muy cortas (revisar o unir):", ", ".join(cortas))
    print("Siguiente: python frases.py --validar y un borrador antes del render completo")


if __name__ == "__main__":
    main()
