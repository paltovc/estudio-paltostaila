# Capa de efectos de sonido (sin musica): sonidos puntuales cuando aparece algo que suena,
# el audio propio de los clips de Flow y un "whoosh" suave al abrir cada bloque.
# Sale tmp/efectos.wav con la duracion del video; terminar.py la mezcla bajo la voz.
#   python sonidos.py "C:\ruta\video"
# En proyecto.json, "sonidos": {"efectos": [{"frase": "abre la puerta", "archivo": "doorOpen_1.ogg"},
#                                          {"escena": 12, "desfase": 0.2, "archivo": "cloth2.ogg", "ganancia": -2}]}
import sys
from pathlib import Path
from estudio import Proyecto, FFMPEG, run, palabras, momento, mmss

pr = Proyecto()
S = pr["sonidos"]
BANCOS = [pr.sonidos, Path(__file__).resolve().parent.parent / "sonidos", Path.home() / "EstudioPaltostaila" / "sonidos"]


def wav(nombre):
    for banco in BANCOS:
        if banco.exists():
            hallado = next(banco.rglob(nombre), None)
            if hallado:
                return hallado
    sys.exit(f"No encuentro el sonido {nombre} en {', '.join(str(b) for b in BANCOS)}")


def main():
    if not S["activar"]:
        print("sonidos desactivados en proyecto.json")
        return
    dur = pr.duracion()
    escenas = pr.escenas()
    _, pals = palabras(pr)
    ini_escena = {r["n"]: r["t0"] for r in escenas}
    fin_escena = {r["n"]: r["t1"] for r in escenas}
    ins, filtros, etiquetas, resumen = [], [], [], []

    def agregar(entrada, cadena, t, etiqueta):
        ins.extend(entrada)
        idx = sum(1 for x in ins if x == "-i") - 1
        ms = max(0, int(t * 1000))
        filtros.append(f"[{idx}:a]{cadena},aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms}[e{idx}]")
        etiquetas.append(f"[e{idx}]")
        resumen.append((t, etiqueta))

    for e in S["efectos"]:
        t, f = momento(pr, pals, escenas, e), wav(e["archivo"])
        d, g = float(e.get("duracion", 2)), float(e.get("ganancia", 0))
        agregar(["-i", f], f"atrim=0:{d},volume={S['vol_efectos'] + g}dB,afade=t=out:st={max(d - 0.3, 0)}:d=0.3", t, f.name)
    for n in S["clips_con_sonido"]:
        f = pr.clips / f"escena_{int(n):03d}.mp4"
        if not f.exists():
            continue
        d = float(S["recorte_clip"].get(str(n), fin_escena[int(n)] - ini_escena[int(n)]))
        agregar(["-i", f], f"atrim=0:{d:.2f},volume={S['vol_clips']}dB,afade=t=in:d=0.15,afade=t=out:st={max(d - 0.5, 0):.2f}:d=0.5",
                ini_escena[int(n)], f"sonido del clip {f.name}")
    if S["whoosh_en_capitulos"]:
        for n in pr["escenas_capitulo"]:
            agregar(["-f", "lavfi", "-i", "anoisesrc=color=pink:duration=0.8:amplitude=0.6"],
                    f"highpass=f=350,lowpass=f=2800,afade=t=in:d=0.45,afade=t=out:st=0.45:d=0.35,volume={S['whoosh_db']}dB",
                    ini_escena[int(n)] - 0.35, "whoosh (cambio de bloque)")
    for e in S["lapiz"]:   # lapiz escribiendo, sintetizado
        agregar(["-f", "lavfi", "-i", "anoisesrc=color=white:duration=2.6:amplitude=0.5"],
                f"bandpass=f=4200:width_type=h:w=2600,tremolo=f=6:d=0.85,afade=t=in:d=0.2,afade=t=out:st=2.2:d=0.4,volume={S['whoosh_db'] - 2}dB",
                momento(pr, pals, escenas, e), "lapiz")
    if not etiquetas:
        print("no hay efectos definidos; no se crea la capa")
        (pr.tmp / "efectos.wav").unlink(missing_ok=True)
        return
    mezcla = ";".join(filtros) + ";" + "".join(etiquetas) + \
        f"amix=inputs={len(etiquetas)}:normalize=0:dropout_transition=0,apad,atrim=0:{dur},alimiter=limit={S['limite_capa']}:level=0[out]"
    run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex", mezcla, "-map", "[out]", "-ar", "48000", pr.tmp / "efectos.wav"])
    print(f"{len(etiquetas)} sonidos en {pr.tmp / 'efectos.wav'}", flush=True)
    for t, nombre in sorted(resumen):
        print(f"  {mmss(t)}  {nombre}")


if __name__ == "__main__":
    main()
