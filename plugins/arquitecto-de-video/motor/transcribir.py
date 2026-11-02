# Transcripcion por palabra con WhisperX (local: el audio no sale del computador).
# Une los audios de voz en orden de nombre, transcribe, y compara con el guion si hay uno en 01_GUION.
#   python transcribir.py "C:\ruta\video"            transcribe (tarda: unos 2-3 min por minuto de audio en CPU)
#   python transcribir.py "C:\ruta\video" --comparar solo compara la transcripcion existente con el guion
import difflib, glob, os, shutil, subprocess, sys
from pathlib import Path
from estudio import Proyecto, FFMPEG, run, cargar, norm, mmss

pr = Proyecto()
WX = pr["whisperx"]


def whisperx():
    candidatos = [WX.get("ruta", ""),
                  str(Path.home() / "EstudioPaltostaila" / "whisperx-venv" / "Scripts" / "whisperx.exe"),
                  str(Path.home() / ".cache" / "watch" / "whisperx-venv" / "Scripts" / "whisperx.exe"),
                  shutil.which("whisperx") or ""]
    for c in candidatos:
        if c and Path(c).exists():
            return c
    sys.exit("No encuentro WhisperX. Ejecuta instalar.cmd (opcion de transcripcion) o indica la ruta en proyecto.json -> whisperx.ruta")


def transcribir():
    auds = pr.audios()
    print("audios en orden:", *[a.name for a in auds], sep="\n  ")
    wav = pr.tmp / "voz_16k.wav"
    ins = sum([["-i", a] for a in auds], [])
    run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex", f"concat=n={len(auds)}:v=0:a=1", "-ac", "1", "-ar", "16000", wav])
    salida = pr.tmp / "whisperx"
    salida.mkdir(exist_ok=True)
    cmd = [whisperx(), str(wav), "--language", WX["idioma"], "--model", WX["modelo"], "--compute_type", WX["compute_type"],
           "--device", "cpu", "--output_format", "json", "--output_dir", str(salida)]
    print("transcribiendo con", WX["modelo"], "... (puede tardar)", flush=True)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit("WhisperX fallo; revisa el mensaje de arriba")
    pr.transcripcion.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(salida / "voz_16k.json", pr.transcripcion)
    print("transcripcion:", pr.transcripcion)


def pausas():
    pals = [w for s in cargar(pr) for w in s["words"]]
    largas = [(a["end"], b["start"] - a["end"]) for a, b in zip(pals, pals[1:]) if b["start"] - a["end"] > 0.8]
    total = sum(d for _, d in largas)
    print(f"\npausas de mas de 0,8 s: {len(largas)}, suman {total:.0f} s "
          f"(dejarlas en 0,35 s ahorraria unos {total - 0.35 * len(largas):.0f} s)")


def comparar():
    guiones = sorted((Path(p) for ext in ("txt", "md") for p in glob.glob(str(pr.ruta(pr["carpetas"]["guion"]) / f"*.{ext}"))
                      if not Path(p).name.upper().startswith(("LEEME", "INVESTIGACION", "FUENTES"))),
                     key=lambda p: -p.stat().st_size)
    if not guiones:
        print("\nno hay guion en", pr["carpetas"]["guion"], "(.txt o .md); no se compara")
        return
    texto = guiones[0].read_text(encoding="utf-8", errors="replace")
    g = norm(texto)
    pals = [w for s in cargar(pr) for w in s["words"]]
    t = [norm(w["word"])[0] if norm(w["word"]) else "" for w in pals]
    sm = difflib.SequenceMatcher(None, t, g, autojunk=False)
    difs = [op for op in sm.get_opcodes() if op[0] != "equal"]
    informe = [f"Comparacion transcripcion vs guion ({guiones[0].name}): {len(difs)} diferencias, coincidencia {sm.ratio():.1%}\n"]
    for op, i1, i2, j1, j2 in difs:
        momento = mmss(pals[min(i1, len(pals) - 1)]["start"]) if pals else "?"
        oido = " ".join(w["word"] for w in pals[max(i1 - 2, 0):i2 + 2])
        guion = " ".join(g[max(j1 - 2, 0):j2 + 2])
        informe.append(f"{momento}  [{op}]\n   se oye: {oido}\n   guion:  {guion}\n")
    ruta = pr.tmp / "diferencias_con_guion.txt"
    ruta.write_text("\n".join(informe), encoding="utf-8")
    print(f"\n{len(difs)} diferencias con el guion -> {ruta}")
    print("Revisarlas y anotar las reales en proyecto.json -> correcciones [texto oido, texto correcto]")


if __name__ == "__main__":
    if "--comparar" not in sys.argv:
        transcribir()
    pausas()
    comparar()
