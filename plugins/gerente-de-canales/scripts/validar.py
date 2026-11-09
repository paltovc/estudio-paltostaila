# Valida 08_PUBLICAR\publicacion.json de un proyecto (lo que se va a publicar, dónde y cuándo).
#   python validar.py "<proyecto>"                      revisa; no toca nada
#   python validar.py "<proyecto>" --adoptar <archivo>  respalda el publicacion.json actual como publicacion_<n>.json
#                                                       y deja el archivo nuevo en su lugar (solo si es válido)
# Termina con código 0 si no hay errores.
import json, os, shutil, sys
from pathlib import Path
from comun import REDES, RUTAS, a_utc, bloqueo, leer_json, opt, p, proyecto_dir, ruta_segura

# miniatura_bytes es un límite propio del estudio (el que pide YouTube Studio), más estricto que el de la API
LIM = {"titulo_yt": 100, "desc_yt": 5000, "etiquetas_yt": 500, "texto_tiktok": 2200, "texto_instagram": 2200,
       "hashtags_instagram": 30, "miniatura_bytes": 2 * 1024 * 1024}


def largo_etiquetas(etiquetas):
    """Cómo cuenta YouTube el límite de 500: comas entre etiquetas y comillas en las que llevan espacios."""
    return sum(len(e) + (2 if " " in e else 0) for e in etiquetas) + max(0, len(etiquetas) - 1)
RUTAS_POR_RED = {"youtube": ("api", "manual"), "tiktok": ("metricool", "manual"), "instagram": ("metricool", "vidiq", "manual")}


def validar(pdir, pub=None):
    pdir = Path(pdir)
    errores, avisos = [], []
    pub = pub if pub is not None else leer_json(pdir / "08_PUBLICAR" / "publicacion.json")
    if pub is None:
        return ["falta 08_PUBLICAR/publicacion.json"], avisos
    for k in ("id", "version", "canal"):
        if not pub.get(k):
            errores.append(f"falta «{k}»")
    piezas = pub.get("piezas") or []
    if not piezas:
        errores.append("no hay piezas")
    claves = [x.get("clave") for x in piezas]
    if len(set(claves)) != len(claves):
        errores.append("hay claves de pieza repetidas")
    for x in piezas:
        c = x.get("clave", "?")
        arch = ruta_segura(pdir, x.get("archivo", ""))
        if not arch or not arch.is_file():
            errores.append(f"{c}: no existe el archivo {x.get('archivo')} dentro del proyecto")
        if x.get("tipo") not in ("largo", "short"):
            errores.append(f"{c}: tipo debe ser largo o short")
        for k in ("ia_realista", "para_ninos"):
            if not isinstance(x.get(k), bool):
                errores.append(f"{c}: falta {k} (true/false)")
        destinos = x.get("destinos") or []
        if not destinos:
            errores.append(f"{c}: sin destinos")
        redes = [d.get("red") for d in destinos]
        if len(set(redes)) != len(redes):
            errores.append(f"{c}: una red aparece dos veces")
        for d in destinos:
            r, ruta = d.get("red"), d.get("ruta")
            if r not in REDES:
                errores.append(f"{c}: red desconocida {r}")
                continue
            if ruta not in RUTAS or ruta not in RUTAS_POR_RED[r]:
                errores.append(f"{c}/{r}: ruta «{ruta}» no sirve para {r} (válidas: {', '.join(RUTAS_POR_RED[r])}; "
                               "la ruta api propia solo existe para YouTube)")
            if ruta == "vidiq" and "youtube" not in redes:
                errores.append(f"{c}/instagram: la ruta vidiq publica desde el Short de YouTube: falta el destino youtube")
            try:
                a_utc(d.get("fecha", ""), d.get("zona", ""))
            except Exception as e:
                errores.append(f"{c}/{r}: fecha «{d.get('fecha')}» o zona «{d.get('zona')}» no válidas ({e}); "
                               "usar AAAA-MM-DDTHH:MM y una zona IANA")
            if r == "youtube":
                t = x.get("titulo", "")
                if not t:
                    errores.append(f"{c}: YouTube necesita titulo")
                if len(t) > LIM["titulo_yt"]:
                    errores.append(f"{c}: título de {len(t)} caracteres (máximo 100)")
                desc = x.get("descripcion", "")
                if len(desc.encode("utf-8")) > LIM["desc_yt"]:
                    errores.append(f"{c}: descripción supera 5000 bytes")
                if any(ch in t + desc for ch in "<>"):
                    errores.append(f"{c}: YouTube rechaza los signos < y > en título o descripción")
                if largo_etiquetas(x.get("etiquetas", [])) > LIM["etiquetas_yt"]:
                    errores.append(f"{c}: etiquetas superan 500 caracteres")
                for k in ("miniatura", "subtitulos"):
                    if x.get(k):
                        q = ruta_segura(pdir, x[k])
                        if not q or not q.is_file():
                            errores.append(f"{c}: no existe {k} {x[k]} dentro del proyecto")
                        elif k == "miniatura":
                            if q.stat().st_size > LIM["miniatura_bytes"]:
                                errores.append(f"{c}: la miniatura pesa más de 2 MB (límite del estudio, el de YouTube Studio)")
                            if q.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                                errores.append(f"{c}: la miniatura debe ser JPG o PNG")
                if x.get("tipo") == "largo" and not x.get("miniatura"):
                    avisos.append(f"{c}: video largo sin miniatura propia")
            if r in ("tiktok", "instagram"):
                txt = x.get(f"texto_{r}", x.get("texto", ""))
                if len(txt) > LIM[f"texto_{r}"]:
                    errores.append(f"{c}/{r}: texto de {len(txt)} caracteres (máximo 2200)")
                if r == "instagram" and txt.count("#") > LIM["hashtags_instagram"]:
                    errores.append(f"{c}/instagram: más de 30 hashtags")
                if ruta == "metricool" and not d.get("enlace_publico"):
                    avisos.append(f"{c}/{r}: Metricool necesita enlace_publico del video (se completa antes de programar)")
    return errores, avisos


def adoptar(pdir, nuevo):
    nuevo = Path(nuevo)
    datos = leer_json(nuevo)
    if datos is None:
        sys.exit(f"No existe {nuevo}")
    e, a = validar(pdir, datos)
    if e:
        for x in e:
            p("ERROR", x)
        sys.exit("No se adopta: el archivo nuevo no es válido")
    actual = Path(pdir) / "08_PUBLICAR" / "publicacion.json"
    import hashlib
    with bloqueo("adoptar_" + hashlib.sha256(str(Path(pdir).resolve()).lower().encode()).hexdigest()[:12]):
        if actual.exists():
            n = 1
            while True:
                resp = actual.parent / f"publicacion_{n}.json"
                try:
                    with open(resp, "xb") as fo:          # respaldo exclusivo: nunca pisa otro respaldo
                        fo.write(actual.read_bytes())
                    p(f"Respaldo: {resp.name}")
                    break
                except FileExistsError:
                    n += 1
        tmp = actual.with_name(f"publicacion.json.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        for i in range(10):
            try:
                os.replace(tmp, actual)
                break
            except PermissionError:
                import time
                time.sleep(0.5 * (i + 1))
        else:
            sys.exit(f"No pude reemplazar {actual} (¿abierto en otro programa?). Quedó la versión nueva en {tmp}.")
    p("LISTO publicacion.json adoptado. Ojo: si cambió algo de una pieza, su aprobación anterior ya no vale.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit("uso: python validar.py <proyecto> [--adoptar <archivo nuevo>]")
    pd = proyecto_dir(a[0])
    if "--adoptar" in a:
        adoptar(pd, opt(a, "--adoptar"))
        sys.exit(0)
    e, av = validar(pd)
    for x in av:
        p("AVISO", x)
    for x in e:
        p("ERROR", x)
    p("VALIDO" if not e else f"NO VALIDO: {len(e)} errores")
    sys.exit(0 if not e else 1)
