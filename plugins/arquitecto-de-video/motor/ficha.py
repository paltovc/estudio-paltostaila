# Ficha de un video: una sola fuente de verdad sobre su estado (E4, 0.14). Solo LEE la carpeta del proyecto
# (proyecto.json, renders, terminado_*.md, evaluacion_*.json, 08_PUBLICAR) y escribe ficha.json en su raíz.
# La ficha es un índice que se calcula de nuevo cada vez (no es una entrega): se reescribe solo si cambió, y SOLO si
# el ficha.json que hay es del propio estudio (lleva "hecha_por": "ficha.py"). Si en la carpeta ya existe un
# ficha.json de otra cosa, no se toca: la ficha se guarda en EstudioPaltostaila\trabajo\fichas\ficha_<ID>.json.
# «Listo para aprobar» exige todo comprobado: terminado en SÍ y de ESTOS archivos, evaluación 8 o más de ESTE archivo.
#   python ficha.py "<proyecto>"        escribe <proyecto>\ficha.json y la muestra
#   python ficha.py tabla               recorre EstudioPaltostaila\proyectos y proyectos_externos.txt, actualiza cada
#                                       ficha y deja la tabla (markdown) en trabajo\fichas\tabla_<fecha>.md
#   python ficha.py tabla --sin-escribir   solo muestra la tabla
#   python ficha.py tabla --canal <nombre>   (0.15) solo los videos de ese canal (la tabla general muestra todos)
import json, os, re, sys
from datetime import datetime
from pathlib import Path
from estudio import DEFAULTS, _mezclar, es_resto, huella, idioma_de, nombre_libre

MARCA = "ficha.py"
try:      # un log de Windows en cp1252 no puede botar la tabla por un carácter
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

ESTUDIO = Path(os.environ.get("ESTUDIO_BASE") or Path(__file__).resolve().parent.parent)


def _ruta(base, p):
    p = Path(os.path.expandvars(os.path.expanduser(str(p))))
    return p if p.is_absolute() else (base / p)


def ficha(carpeta):
    """Estado de un proyecto leído de sus archivos. No crea carpetas ni toca nada."""
    d = Path(carpeta).resolve()
    cfg = _mezclar(DEFAULTS, json.loads((d / "proyecto.json").read_text(encoding="utf-8")))
    c = cfg["carpetas"]
    ident = cfg.get("id") or cfg["nombre"]
    ver = cfg["version"] or "v1"
    base = f"{ident}_{ver}"
    salida, publicar = _ruta(d, c["salida"]), _ruta(d, c["publicar"])
    imagenes, receta = _ruta(d, c["imagenes"]), _ruta(d, c["receta"])

    def cuenta(carp, exts):
        return sum(1 for q in carp.iterdir() if q.is_file() and q.suffix.lower() in exts and not es_resto(q)) if carp.is_dir() else 0

    import glob
    patrones = cfg["audios"] if isinstance(cfg["audios"], list) else [cfg["audios"]]      # igual que Proyecto.audios()
    audios = {x for pt in patrones for x in glob.glob(str(_ruta(d, pt)))
              if Path(x).suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac") and not es_resto(x)}
    videos = sorted(q for q in salida.glob(f"{base}_*.mp4") if not es_resto(q)) if salida.is_dir() else []
    yt = salida / f"{base}_youtube.mp4"
    cs = salida / f"{base}_con-subtitulos.mp4"
    f = {"id": ident, "nombre": cfg["nombre"], "canal": cfg.get("canal") or d.parent.name, "version": ver, "carpeta": str(d),
         "titulo": cfg.get("titulo"), "idioma": idioma_de(cfg), "tipo_video": cfg.get("tipo_video") or "narrado",   # 0.15
         "material": {"guion": _ruta(d, c["guion"]).is_dir() and any(_ruta(d, c["guion"]).iterdir()),
                      "audios_de_voz": len(audios),
                      "imagenes": cuenta(imagenes, {".png", ".jpg", ".jpeg", ".webp"}),
                      "receta": receta.exists(), "elementos_capa_viva": len(cfg.get("elementos") or [])},
         "render": {"youtube": yt.exists(), "con_subtitulos": cs.exists(),
                    "shorts": [q.name for q in videos if q.name.endswith("9x16.mp4")],
                    "shorts_pedidos": len(cfg.get("vertical") or [])}}
    # terminado: vale solo si es de ESTOS archivos (huellas que guarda terminado.py desde la 0.14; si no hay, por fecha)
    t = salida / f"terminado_{base}.md"
    if t.exists():
        txt = t.read_text(encoding="utf-8", errors="replace")
        filas = re.findall(r"^\| (\d+) \| (.+?) \| ([✓✗?–]) \| (.*?) \|$", txt, re.M)
        vigente, motivo = None, "terminado anterior a la 0.14 (sin huellas): volver a correr terminado.py"
        tj = salida / f"terminado_{base}.json"
        try:
            hj = json.loads(tj.read_text(encoding="utf-8"))["videos"] if tj.exists() else None
        except (ValueError, KeyError, TypeError):
            hj = None
        if isinstance(hj, dict) and hj:
            cambiados = [n for n, h in hj.items() if not (salida / n).exists() or huella(salida / n) != h]
            nuevos = [q.name for q in videos if q.name not in hj]
            vigente = not cambiados and not nuevos
            motivo = "" if vigente else "cambió después de terminado.py: " + ", ".join((cambiados + nuevos)[:4])
        elif any(q.stat().st_mtime > t.stat().st_mtime + 1 for q in videos):
            vigente, motivo = False, "hay videos más nuevos que terminado.py: volver a correrlo"
        f["terminado"] = {"si": "**SÍ" in txt, "vigente": vigente, "motivo": motivo,
                          "falla": [f"{n}. {p}: {det}".rstrip(": ") for n, p, m, det in filas if m == "✗"],
                          "no_comprobado": [f"{n}. {p}: {det}".rstrip(": ") for n, p, m, det in filas if m == "?"],
                          "recomendado_que_falta": [f"{n}. {p}" for n, p, m, det in filas if m == "–"],
                          "fecha": datetime.fromtimestamp(t.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}
    else:
        f["terminado"] = None
    # evaluación: None en "del_archivo_actual" = no se pudo comprobar (cuenta como pendiente, nunca como aprobado)
    ev = d / "06_RECETA" / f"evaluacion_{base}_con-subtitulos.json"
    if ev.exists():
        try:
            e = json.loads(ev.read_text(encoding="utf-8"))
            if not isinstance(e, dict):
                raise ValueError("no es un objeto")
            f["evaluacion"] = {"nota": e.get("nota_medida"), "clase": e.get("clase_medida"), "legible": True,
                               "del_archivo_actual": (huella(cs) == e["sha256"]) if e.get("sha256") and cs.exists() else None}
        except (ValueError, KeyError, TypeError):
            f["evaluacion"] = {"nota": None, "clase": None, "legible": False, "del_archivo_actual": None}
    else:
        f["evaluacion"] = None
    minis = sorted(q.name for q in publicar.glob("*miniatura*")) if publicar.is_dir() else []
    f["empaque"] = {"miniaturas": minis[:5], "publicacion_json": (publicar / "publicacion.json").exists() or (d / "publicacion.json").exists()}
    # qué falta, en orden. Lo que no se pudo comprobar va aquí: «no comprobado» nunca cuenta como listo.
    falta = []
    m = f["material"]
    hay_render = f["render"]["youtube"]
    if not hay_render:
        if not m["audios_de_voz"]:
            falta.append("la voz")
        if not m["imagenes"]:
            falta.append("las imágenes")
        if not m["receta"]:
            falta.append("la receta de escenas")
        falta.append(f"el render de la {ver}")
    else:
        T = f["terminado"]
        if T is None:
            falta.append("correr terminado.py")
        else:
            if T["vigente"] is not True:
                falta.append(T["motivo"])
            if not T["si"]:
                falta += T["falla"]
            falta += [x + " (no comprobado)" for x in T["no_comprobado"]]
        E = f["evaluacion"]
        if E is None:
            falta.append("la evaluación")
        elif not E["legible"]:
            falta.append("la evaluación no se puede leer: volver a evaluar")
        elif E["del_archivo_actual"] is False:
            falta.append("volver a evaluar (el video cambió después de la nota)")
        elif E["del_archivo_actual"] is None:
            falta.append("volver a evaluar (la nota no trae la huella del video)")
        elif not isinstance(E["nota"], (int, float)) or E["nota"] < 8 or E["clase"] == "C":
            falta.append(f"subir la nota (hoy {E['nota']}, clase {E['clase']}): aplicar las mejoras del evaluador")
        if not f["titulo"]:
            falta.append("el título")
        if not minis:
            falta.append("la miniatura")
        if len(f["render"]["shorts"]) < f["render"]["shorts_pedidos"]:
            falta.append(f"{f['render']['shorts_pedidos'] - len(f['render']['shorts'])} Shorts")
    f["falta"] = falta
    f["avisos"] = (f["terminado"] or {}).get("recomendado_que_falta", []) if hay_render else []
    f["estado"] = ("en preparación" if not hay_render and (m["audios_de_voz"] or m["imagenes"]) else "sin material" if not hay_render
                   else "listo para aprobar" if not falta else "armado, con pendientes")
    return f


def guardar(f):
    """Escribe la ficha solo si cambió (la fecha de lectura no cuenta). Devuelve (ruta, cambió). Un ficha.json que
    no sea del estudio (sin la marca, o ilegible) NO se toca: la ficha va a trabajo\\fichas."""
    f = dict(f, hecha_por=MARCA)
    p = Path(f["carpeta"]) / "ficha.json"
    if p.exists():
        try:
            viejo = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            viejo = None
        if not isinstance(viejo, dict) or viejo.get("hecha_por") != MARCA:
            dest = ESTUDIO / "trabajo" / "fichas"
            dest.mkdir(parents=True, exist_ok=True)
            p = dest / f"ficha_{re.sub(r'[^A-Za-z0-9_.-]+', '-', str(f['id']))}.json"
            print(f"AVISO: en {f['carpeta']} hay un ficha.json que no es del estudio; no se toca. La ficha va a {p}", flush=True)
            try:
                viejo = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
            except (ValueError, OSError):
                viejo = None
            if viejo is not None and (not isinstance(viejo, dict) or viejo.get("hecha_por") != MARCA):
                sys.exit(f"{p} existe y no es una ficha del estudio: no se escribe nada")
        if isinstance(viejo, dict):
            viejo.pop("leida", None)
            if viejo == f:
                return p, False
    p.write_text(json.dumps(dict(f, leida=datetime.now().strftime("%Y-%m-%d %H:%M")), ensure_ascii=False, indent=1), encoding="utf-8")
    return p, True


def proyectos():
    """Carpetas de video: las de EstudioPaltostaila\\proyectos y las de proyectos_externos.txt, cada una hasta dos niveles
    más adentro (igual que la sala). Cuenta proyecto.json (video narrado) y montaje.json (montaje sobre música)."""
    raices = [ESTUDIO / "proyectos"]
    extra = ESTUDIO / "proyectos_externos.txt"
    if extra.exists():
        for l in extra.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            l = l.strip().strip('"')
            if l and not l.startswith("#"):
                r = Path(os.path.expandvars(os.path.expanduser(l)))
                if r.is_absolute():          # una ruta relativa dependería de dónde se corra: se ignora
                    raices.append(r)
    vistos, out = set(), []
    for raiz in raices:
        if not raiz.is_dir():
            continue
        for nombre in ("proyecto.json", "montaje.json"):
            for patron in (nombre, f"*/{nombre}", f"*/*/{nombre}"):
                for q in raiz.glob(patron):
                    r = q.parent.resolve()
                    if r not in vistos and not es_resto(r):
                        vistos.add(r); out.append(r)
    return sorted(out, key=lambda q: q.name.lower())


def ficha_montaje(carpeta):
    """Ficha corta de un montaje sobre música (montaje.json, sin proyecto.json): qué renders hay."""
    d = Path(carpeta).resolve()
    sal = d / "07_RENDER"
    vids = sorted((q for q in sal.glob("*.mp4") if not es_resto(q)), key=lambda q: q.stat().st_mtime) if sal.is_dir() else []
    ident = d.name.split("_")[0]
    ver = (re.findall(r"_(v\d+)", vids[-1].name) or ["v1"])[-1] if vids else "v1"
    return {"id": ident, "nombre": d.name, "canal": d.parent.name, "version": ver, "carpeta": str(d), "titulo": None, "tipo": "montaje",
            "render": {"videos": [q.name for q in vids[-5:]]}, "evaluacion": None,
            "falta": [] if vids else ["el render"], "estado": "armado (montaje: se revisa a mano)" if vids else "en preparación"}


def tabla(fichas):
    L = ["| Video | Canal | Versión | Estado | Nota | Qué falta |", "|---|---|---|---|---|---|"]
    for f in fichas:
        e = f["evaluacion"]
        nota = "–" if not e or e["nota"] is None else f"{e['nota']} ({e['clase']})" + (" (!)" if e["del_archivo_actual"] is not True else "")
        L.append(f"| {f['id']} {f['titulo'] or f['nombre']} | {f['canal']} | {f['version']} | {f['estado']} | {nota} | "
                 f"{'; '.join(f['falta'][:6]) or 'nada'} |")
    return "\n".join(L)


def main():
    A = sys.argv[1:]
    if A and A[0] == "tabla":
        fichas, errores = [], []
        solo = A[A.index("--canal") + 1] if "--canal" in A and A.index("--canal") + 1 < len(A) else None   # 0.15
        for c in proyectos():
            try:
                f = ficha(c) if (c / "proyecto.json").exists() else ficha_montaje(c)
                if solo and str(f.get("canal")).lower() != solo.lower():
                    continue
                if "--sin-escribir" not in A:
                    guardar(f)
                fichas.append(f)
            except Exception as e:          # un proyecto.json roto no bota la tabla de los demás
                errores.append(f"{c}: {e}")
        txt = (f"# Estado de los videos{' del canal ' + solo if solo else ''} ({datetime.now():%Y-%m-%d %H:%M})\n\n"
               + tabla(fichas) + "\n")
        if errores:
            txt += "\nNo se pudieron leer:\n" + "\n".join(f"- {e}" for e in errores) + "\n"
        if "--sin-escribir" not in A:      # primero se guarda la tabla; después se muestra
            dest = ESTUDIO / "trabajo" / "fichas"
            dest.mkdir(parents=True, exist_ok=True)
            sal = nombre_libre(dest / f"tabla_{datetime.now():%Y%m%d}.md")
            sal.write_text(txt, encoding="utf-8")
        print(txt, flush=True)
        if "--sin-escribir" not in A:
            print("LISTO", sal)
        return
    carpeta = next((a for a in A if Path(a).is_dir()), ".")
    if not (Path(carpeta) / "proyecto.json").exists():
        sys.exit(f"No encuentro proyecto.json en {Path(carpeta).resolve()}")
    f = ficha(carpeta)
    ruta, cambio = guardar(f)
    print(json.dumps(f, ensure_ascii=False, indent=1), flush=True)
    print("LISTO", ruta, "(actualizada)" if cambio else "(sin cambios)")


if __name__ == "__main__":
    main()
