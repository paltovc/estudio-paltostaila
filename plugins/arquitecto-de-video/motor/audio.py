# Audio profesional con filtros propios de ffmpeg (como "Reducir ruido", "Realzar voz", ecualizador y "Ducking" de CapCut):
#   python audio.py limpiar "<entrada>" "<salida.wav>" [--nivel suave|media|fuerte] [--radio] [--sin-normalizar]
#   python audio.py mezclar "<voz>" "<musica>" "<salida.wav>" [--musica -20] [--sin-ducking] [--desde 0]
#   python audio.py efecto "<entrada>" "<salida.wav>" --tipo eco|sala|telefono|radio_antigua|grave|aguda
#   python audio.py medir "<archivo>"       volumen (LUFS), pico y ruido de fondo, con una recomendación
#
# En proyecto.json (terminar.py lo aplica solo):
#   "audio_voz": {"limpiar": "media", "radio": true}             limpia y ecualiza la voz antes de llevarla a -14 LUFS
#   "musica": {"archivo": "02_MUSICA/tema.mp3", "volumen": -20, "ducking": true, "desde": 0}
#       música bajo la voz: baja sola cuando se habla y sube en las pausas. Solo música con licencia para usarla.
# En grabado.py ya hay una limpieza básica (limpiar_voz); "audio_voz" la reemplaza por la que se elija aquí.
# Nada de esto clona ni cambia la identidad de una voz.
import json, re, subprocess, sys
from pathlib import Path

try:
    from estudio import FFMPEG
except Exception:
    FFMPEG = "ffmpeg"

LIMPIEZA = {
    # quita retumbe y soplido sin que se note el filtro
    "suave": "highpass=f=70,afftdn=nf=-20:nr=8:tn=1",
    # ruido de fondo constante (ventilador, refrigerador, calle) + sibilantes
    "media": "highpass=f=80,lowpass=f=15000,afftdn=nf=-25:nr=14:tn=1,deesser=i=0.3",
    # mucho ruido: dos pasadas de reducción y una compuerta suave entre palabras (también baja la cola del eco)
    "fuerte": "highpass=f=90,lowpass=f=12000,afftdn=nf=-28:nr=20:tn=1,afftdn=nf=-35:nr=10,"
              "agate=threshold=0.015:ratio=2.5:attack=10:release=250:range=0.12,deesser=i=0.4",
}
# "voz de radio": cuerpo en los graves, menos encierro en 300 Hz, presencia en 3-5 kHz y compresión pareja
RADIO = ("equalizer=f=120:t=q:w=1:g=2,equalizer=f=320:t=q:w=1.2:g=-3,equalizer=f=3500:t=q:w=1.4:g=3,"
         "equalizer=f=9000:t=q:w=1:g=1.5,acompressor=threshold=-20dB:ratio=3:attack=6:release=120:makeup=2")
EFECTOS = {
    "eco": "aecho=0.8:0.7:180:0.35",
    "sala": "aecho=0.8:0.85:40|70|110:0.3|0.22|0.15",
    "telefono": "highpass=f=400,lowpass=f=3200,acompressor=threshold=-18dB:ratio=6,volume=2dB",
    "radio_antigua": "highpass=f=300,lowpass=f=4500,acrusher=bits=10:mode=log:aa=1,volume=1dB",
    "grave": "asetrate=48000*0.88,aresample=48000,atempo=1/0.88",
    "aguda": "asetrate=48000*1.12,aresample=48000,atempo=1/1.12",
}


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit("ffmpeg falló:\n" + r.stderr[-1200:])
    return r.stderr


def cadena_voz(nivel=None, radio=False):
    """Filtro de limpieza (+ ecualización) para pegar en otra cadena; '' si no se pidió nada."""
    partes = []
    if nivel:
        partes.append(LIMPIEZA[nivel])
    if radio:
        partes.append(RADIO)
    return ",".join(partes)


def medir(p):
    s = run([FFMPEG, "-hide_banner", "-i", p, "-af", "ebur128=peak=true,astats=metadata=0:measure_overall=Noise_floor", "-f", "null", "-"])
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", s)[-1])
    pico = float((re.findall(r"Peak:\s+(-?[\d.]+) dBFS", s) or ["0"])[-1])
    ruido = re.findall(r"Noise floor dB:\s+(-?[\d.inf]+)", s)
    ruido = float(ruido[-1]) if ruido and "inf" not in ruido[-1] else None
    return lufs, pico, ruido


def normalizar(entrada, salida, objetivo=-14.0):
    lufs, _, _ = medir(entrada)
    g = objetivo - lufs
    for _ in range(3):
        run([FFMPEG, "-v", "error", "-y", "-i", entrada, "-af", f"volume={g:.2f}dB,alimiter=limit=0.89:level=0", "-ar", 48000, salida])
        actual, _, _ = medir(salida)
        if abs(actual - objetivo) <= 0.3:
            break
        g += objetivo - actual
    return actual


def limpiar(entrada, salida, nivel="media", radio=False, normal=True):
    tmp = Path(salida).with_name("_limpia_paso.wav")
    run([FFMPEG, "-v", "error", "-y", "-i", entrada, "-vn", "-af", cadena_voz(nivel, radio) or "anull", "-ar", 48000, tmp])
    if normal:
        normalizar(tmp, salida)
        tmp.unlink()
    else:
        tmp.replace(salida)
    return salida


def filtro_musica(i_voz, i_mus, volumen=-20, ducking=True, sal="mezcla"):
    """Grafo: música a 'volumen' dB y, si ducking, comprimida por la voz (baja unos 8-10 dB cuando hay voz)."""
    m = f"[{i_mus}:a]aresample=48000,aformat=channel_layouts=stereo,volume={volume_db(volumen)}[mus];"
    if ducking:
        return (m + f"[{i_voz}:a]asplit=2[v1][vsc];[mus][vsc]sidechaincompress=threshold=0.02:ratio=6:attack=40:release=450:"
                f"makeup=1[duck];[v1][duck]amix=inputs=2:normalize=0:dropout_transition=0,alimiter=limit=0.89:level=0[{sal}]")
    return m + f"[{i_voz}:a][mus]amix=inputs=2:normalize=0:dropout_transition=0,alimiter=limit=0.89:level=0[{sal}]"


def volume_db(v):
    return f"{float(v):.1f}dB"


def mezclar(voz, musica, salida, volumen=-20, ducking=True, desde=0.0):
    run([FFMPEG, "-v", "error", "-y", "-i", voz, "-stream_loop", -1, "-ss", f"{desde:.3f}", "-i", musica, "-filter_complex",
         filtro_musica(0, 1, volumen, ducking), "-map", "[mezcla]", "-shortest", "-ar", 48000, salida])
    return salida


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit("Uso: ver el encabezado de audio.py")
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a[0] == "medir":
        lufs, pico, ruido = medir(a[1])
        print(f"volumen {lufs:.1f} LUFS (objetivo -14) · pico {pico:.1f} dBFS · ruido de fondo {ruido if ruido is not None else '?'} dB")
        if ruido is not None:
            snr = lufs - ruido          # cuánto más fuerte es la voz que el ruido de las pausas
            print(f"voz sobre ruido: {snr:.0f} dB -> limpieza recomendada:",
                  "ninguna" if snr > 45 else "suave" if snr > 35 else "media" if snr > 22 else "fuerte")
    elif a[0] == "limpiar":
        limpiar(a[1], a[2], op("--nivel", "media"), "--radio" in a, "--sin-normalizar" not in a)
        print("LISTO", a[2])
    elif a[0] == "mezclar":
        mezclar(a[1], a[2], a[3], float(op("--musica", -20)), "--sin-ducking" not in a, float(op("--desde", 0)))
        print("LISTO", a[3])
    elif a[0] == "efecto":
        run([FFMPEG, "-v", "error", "-y", "-i", a[1], "-vn", "-af", EFECTOS[op("--tipo", "eco")], "-ar", 48000, a[2]])
        print("LISTO", a[2])


if __name__ == "__main__":
    main()
