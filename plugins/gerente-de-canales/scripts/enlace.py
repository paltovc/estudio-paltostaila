# Comprueba que un enlace público sirve el video tal cual (Metricool lo descarga desde ahí).
#   python enlace.py "<url>" ["<archivo aprobado>"]
# Sin archivo: pide solo la cabecera. Con archivo: además descarga el video del enlace y compara su huella (sha256)
# con la del archivo aprobado (mismo tamaño no basta: podría ser otro render). Termina con 0 solo si coincide.
import hashlib, sys, urllib.request
from pathlib import Path


def revisar(url, timeout=20):
    """Devuelve (ok, detalle, tamaño_en_bytes_o_None)."""
    if not str(url).lower().startswith("https://"):
        return False, "el enlace debe empezar con https://", None
    ultimo = ""
    for metodo, extra in (("HEAD", {}), ("GET", {"Range": "bytes=0-0"})):
        try:
            req = urllib.request.Request(url, method=metodo, headers={"User-Agent": "gerente-de-canales", **extra})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                tipo = r.headers.get("Content-Type", "")
                rango = r.headers.get("Content-Range", "")
                largo = rango.split("/")[-1] if "/" in rango else r.headers.get("Content-Length")
                largo = int(largo) if largo and str(largo).isdigit() else None
                if "text/html" in tipo:
                    return False, f"devuelve una página web ({tipo}), no el archivo: usar el enlace de descarga directa", largo
                if not (tipo.startswith("video/") or "octet-stream" in tipo):
                    return False, f"tipo de contenido inesperado: {tipo}", largo
                return True, f"{tipo}, {largo} bytes", largo
        except Exception as e:
            ultimo = str(e)[:160]
    return False, f"no responde: {ultimo}", None


def huella_remota(url, maximo=800 * 1024 * 1024, timeout=60):
    h, n = hashlib.sha256(), 0
    req = urllib.request.Request(url, headers={"User-Agent": "gerente-de-canales"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for b in iter(lambda: r.read(1 << 20), b""):
            n += len(b)
            if n > maximo:
                raise ValueError("el enlace entrega más de 800 MB")
            h.update(b)
    return h.hexdigest()


def revisar_contra(url, archivo, revisar_fn=revisar, huella_fn=huella_remota):
    from comun import huella
    ok, det, largo = revisar_fn(url)
    if not ok:
        return False, det
    real = Path(archivo).stat().st_size
    if largo is not None and largo != real:
        return False, f"el enlace entrega {largo} bytes y el archivo aprobado tiene {real}: ¿es otro render?"
    try:
        remota = huella_fn(url)
    except Exception as e:
        return False, f"no pude descargar el video del enlace para compararlo: {str(e)[:120]}"
    if remota != huella(archivo):
        return False, "el enlace entrega OTRO video (la huella no coincide con el archivo aprobado)"
    return True, f"{det}; mismo contenido (huella {remota[:8]})"


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit("uso: python enlace.py <url> [archivo]")
    ok, det = revisar_contra(a[0], a[1]) if len(a) > 1 else revisar(a[0])[:2]
    print(("ENLACE OK: " if ok else "ENLACE NO SIRVE: ") + det, flush=True)
    sys.exit(0 if ok else 1)
