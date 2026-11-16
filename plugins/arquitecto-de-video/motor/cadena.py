# Un comando por etapa: corre los scripts del motor en orden, guarda TODO en un log y muestra solo un resumen corto.
# Sirve para gastar menos uso de Claude: Claude lee el resumen (10-20 líneas), no la salida completa.
#   python cadena.py "<proyecto>" revisar   evaluar → terminado → escuchar (sin transcribir) → ficha     (no toca videos;
#                                           escribe sus informes)
#   python cadena.py "<proyecto>" escuchar  escuchar completo (transcribe la mezcla: tarda)                  (solo lee)
#   python cadena.py "<proyecto>" final     terminar → vertical → evaluar → terminado → escuchar → ficha    (arma la versión)
#   python cadena.py "<proyecto>" shorts    vertical → terminado → ficha                                    (arma los Shorts)
# Deja trabajo\cadenas\<ID>_<etapa>_<fecha>.log (todo) y .md (el resumen). No pisa nada: cada corrida tiene su nombre.
import re, subprocess, sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ESTUDIO = AQUI.parent
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ETAPAS = {
    "revisar": [("evaluar", ["evaluar.py", "{P}", "--video", "{CS}"]), ("terminado", ["terminado.py", "{P}"]),
                ("escuchar", ["escuchar.py", "{P}", "--sin-transcribir"]), ("ficha", ["ficha.py", "{P}"])],
    "escuchar": [("escuchar", ["escuchar.py", "{P}"])],
    "final": [("terminar", ["terminar.py", "{P}"]), ("vertical", ["vertical.py", "{P}"]),
              ("evaluar", ["evaluar.py", "{P}", "--video", "{CS}"]), ("terminado", ["terminado.py", "{P}"]),
              ("escuchar", ["escuchar.py", "{P}"]), ("ficha", ["ficha.py", "{P}"])],
    "shorts": [("vertical", ["vertical.py", "{P}"]), ("terminado", ["terminado.py", "{P}"]), ("ficha", ["ficha.py", "{P}"])],
}
# lo que se copia al resumen de cada paso: líneas que dicen el resultado, no el proceso
CLAVE = re.compile(r"^(LISTO|AVISO|ERROR|NO SE FIRMA|\*\*S[ÍI]|\*\*NO|PRUEBA|Nota|nota|Clase|clase|\*\*Se entiende|\| \d+ \|.*\| [✗?] \||"
                   r"\| \d+:\d\d|.*estado\"|.*cambió mientras)")
# los pasos de armado se detienen si fallan; los de revisión siguen (un NO de terminado es información, no un error)
ARMA = {"terminar", "vertical"}


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[1] not in ETAPAS:
        sys.exit("uso: python cadena.py \"<proyecto>\" " + "|".join(ETAPAS))
    pdir = Path(a[0]).resolve()
    if not (pdir / "proyecto.json").exists():
        sys.exit(f"No encuentro proyecto.json en {pdir}")
    sys.path.insert(0, str(AQUI))
    sys.argv = [sys.argv[0], str(pdir)]
    from estudio import Proyecto
    pr = Proyecto(pdir)
    cs = pr.salida / f"{pr.base_nombre}_con-subtitulos.mp4"
    dest = ESTUDIO / "trabajo" / "cadenas"
    dest.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d-%H%M%S")
    log = dest / f"{pr.base_nombre}_{a[1]}_{marca}.log"
    res = [f"# {pr.base_nombre} · {a[1]} · {datetime.now():%Y-%m-%d %H:%M}", ""]
    with open(log, "w", encoding="utf-8") as L:
        for nombre, args in ETAPAS[a[1]]:
            args = [x.replace("{P}", str(pdir)).replace("{CS}", str(cs)) for x in args]
            ini = datetime.now()
            L.write(f"\n===== {nombre}: {' '.join(args)}\n"); L.flush()
            r = subprocess.run([sys.executable, *args], cwd=AQUI, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env={**__import__("os").environ, "PYTHONUTF8": "1"})
            salida = (r.stdout or "") + (r.stderr or "")
            L.write(salida); L.flush()
            seg = (datetime.now() - ini).seconds
            todas = [l.strip() for l in salida.splitlines() if CLAVE.match(l.strip())]
            critico = re.compile(r"^(\*\*Se entiende|\*\*Aviso|NO SE FIRMA|\*\*NO|ERROR|.*no comprobado)")
            fijas = [l for l in todas if critico.match(l)]
            claves = fijas + [l for l in todas if l not in fijas][-(max(3, 10 - len(fijas))):]
            if r.returncode:
                claves += [l.strip() for l in (r.stderr or salida).splitlines() if l.strip()][-2:]
            res.append(f"**{nombre}** · {'ok' if r.returncode == 0 else 'código ' + str(r.returncode)} · {seg} s")
            res += [f"- {c[:220]}" for c in claves]
            if r.returncode and nombre in ARMA:
                res.append(f"- se detuvo aquí: {nombre} falló (detalle en el log)")
                break
    res += ["", f"log completo: {log}"]
    md = log.with_suffix(".md")
    md.write_text("\n".join(res) + "\n", encoding="utf-8")
    print("\n".join(res), flush=True)


if __name__ == "__main__":
    main()
