# Color para material grabado: pasa el HDR del celular (HDR10/HLG, se ve gris y lavado fuera del celular) a SDR
# y aplica un "look" igual en todas las tomas. Muestra antes y después antes de renderizar nada.
#   python color.py muestras "<salida>" "archivo.mp4@12.5" "foto.jpg" ... [--look calido] [--alto 960] [--luz]
#   (--luz, 0.15: agrega la iluminación automática de luz.py; el orden siempre es HDR->SDR -> luz -> LUT/look)
#   (desde otro script)  from color import cadena; vf = cadena(ruta, "calido")
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    from estudio import FFMPEG, FFPROBE
except Exception:
    FFMPEG, FFPROBE = "ffmpeg", "ffprobe"

LOOKS = {
    # contraste, saturación, gamma, balance de medios y altas (rojo, verde, azul), viñeta
    "natural":  dict(c=1.03, s=1.05, g=1.00, med=(0.00, 0.00, 0.00), alt=(0.00, 0.00, 0.00), vin=0),
    "calido":   dict(c=1.05, s=1.08, g=1.00, med=(0.05, 0.01, -0.05), alt=(0.03, 0.01, -0.03), vin=1),
    "atardecer": dict(c=1.10, s=1.18, g=1.03, med=(0.08, 0.02, -0.06), alt=(0.05, 0.02, -0.05), vin=1),
    "cine":     dict(c=1.14, s=0.95, g=0.98, med=(0.02, 0.00, 0.03), alt=(0.05, 0.02, -0.04), vin=1),
}


def es_hdr(ruta):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                        "-of", "json", str(ruta)], capture_output=True, text=True)
    try:
        t = json.loads(r.stdout)["streams"][0].get("color_transfer", "")
    except Exception:
        t = ""
    return t in ("smpte2084", "arib-std-b67")


def hdr_sdr(ruta):
    """Solo el paso de HDR a SDR (cadena vacía si el archivo no es HDR o es una foto). Lo usa luz.py para medir."""
    if Path(ruta).suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp") and es_hdr(ruta):
        return ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=reinhard:param=0.6:desat=0,"
                "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    return ""


def cadena(ruta, look="calido", brillo=0.0, luz=""):
    """Filtro de ffmpeg: HDR->SDR si hace falta + look. brillo: -0.1 a 0.15 para tomas oscuras o claras.
    luz (0.15): filtro de luz.py (exposición, balance de blancos, realce de cara); va después del paso a SDR y antes
    de la LUT y del look. Vacío = igual que siempre."""
    lut = None
    if str(look).startswith("lut:"):      # una LUT .cube propia o gratuita (como los LUT de CapCut o DaVinci)
        lut = Path(str(look)[4:])
        look = "natural"
    L = LOOKS[look]
    partes = []
    sdr = hdr_sdr(ruta)
    if sdr:
        partes.append(sdr)
    if luz:
        partes.append(luz)
    if lut:
        ruta_lut = str(lut.resolve()).replace("\\", "/").replace(":", "\\:")
        partes.append(f"lut3d=file='{ruta_lut}'")
    rm, gm, bm = L["med"]; rh, gh, bh = L["alt"]
    partes.append(f"eq=contrast={L['c']}:saturation={L['s']}:gamma={L['g']}:brightness={brillo}")
    partes.append(f"colorbalance=rm={rm}:gm={gm}:bm={bm}:rh={rh}:gh={gh}:bh={bh}")
    if L["vin"]:
        partes.append("vignette=angle=PI/5")
    return ",".join(partes)


def fotograma(ruta, t, vf, destino, alto):
    cmd = [FFMPEG, "-v", "error", "-y"]
    if t is not None:
        cmd += ["-ss", f"{t:.2f}"]
    cmd += ["-i", str(ruta), "-frames:v", "1", "-vf", (vf + "," if vf else "") + f"scale=-2:{alto}", "-q:v", "3", str(destino)]
    subprocess.run(cmd, capture_output=True)
    return Image.open(destino).convert("RGB")


def muestras():
    args = sys.argv[2:]
    look = args[args.index("--look") + 1] if "--look" in args else "calido"
    alto = int(args[args.index("--alto") + 1]) if "--alto" in args else 960
    salida = Path(args[0]); salida.mkdir(parents=True, exist_ok=True)
    pedidos = [a for a in args[1:] if not a.startswith("--") and a not in (look, str(alto))]
    try:
        fuente = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        fuente = ImageFont.load_default()
    import shutil, tempfile
    import atexit
    tmp = Path(tempfile.mkdtemp(prefix="color_muestras_"))   # los cuadros sueltos: carpeta temporal propia
    atexit.register(shutil.rmtree, tmp, True)               # se borra aunque algo falle a mitad
    for i, p in enumerate(pedidos, 1):
        ruta, _, t = p.rpartition("@") if "@" in p else (p, "", "")
        ruta = Path(ruta); t = float(t) if t else None
        antes = fotograma(ruta, t, "", tmp / f"_a{i}.jpg", alto)
        fl = ""
        if "--luz" in args:                       # 0.15: la muestra incluye la luz automática de luz.py
            import luz as _luz
            fl, inf = _luz.para_toma(ruta, {"auto": True})
            print("luz", ruta.name, inf["resumen"], flush=True)
        despues = fotograma(ruta, t, cadena(ruta, look, luz=fl), tmp / f"_d{i}.jpg", alto)
        hoja = Image.new("RGB", (antes.width + despues.width + 30, alto + 50), (20, 20, 24))
        hoja.paste(antes, (10, 45)); hoja.paste(despues, (antes.width + 20, 45))
        d = ImageDraw.Draw(hoja)
        d.text((14, 10), f"ANTES  {ruta.name}" + (f" @ {t:.1f}s" if t is not None else ""), fill=(230, 230, 230), font=fuente)
        d.text((antes.width + 24, 10), f"DESPUÉS  look {look}" + ("  + luz automática" if fl else ""), fill=(255, 200, 110), font=fuente)
        sal = salida / f"color_{look}_{i:02d}.jpg"
        k = 2
        while sal.exists():                       # nunca encima de una hoja anterior
            sal = salida / f"color_{look}_{i:02d}_{k}.jpg"; k += 1
        hoja.save(sal, quality=85)
        print("ok", sal, flush=True)
    shutil.rmtree(tmp, ignore_errors=True)       # solo la carpeta temporal de arriba


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "muestras":
        muestras()
    else:
        sys.exit(__doc__ or 'Uso: python color.py muestras "<salida>" "video.mp4@12.5" "foto.jpg" [--look calido]')
