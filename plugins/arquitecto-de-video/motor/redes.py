# Lectura de videos publicados (YouTube, TikTok, Instagram) con yt-dlp: datos, comentarios y video.
# Solo para analizar referentes; el material descargado no se reutiliza en los videos propios.
import glob, json, os, re, shutil, statistics, subprocess, sys
from datetime import date
from pathlib import Path

ESTUDIO = Path.home() / "EstudioPaltostaila"


def ytdlp():
    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]
    local = os.environ.get("LOCALAPPDATA", "")
    for p in glob.glob(os.path.join(local, "Microsoft", "WinGet", "Packages", "yt-dlp*", "yt-dlp.exe")):
        return [p]
    try:
        subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], capture_output=True, check=True)
        return [sys.executable, "-m", "yt_dlp"]
    except Exception:
        sys.exit("No encuentro yt-dlp. Instalar con: winget install yt-dlp.yt-dlp  (o pip install yt-dlp)")


def llamar(args, timeout=600):
    r = subprocess.run(ytdlp() + args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-1200:])
    return r.stdout


def plataforma(url):
    u = url.lower()
    if "tiktok.com" in u:
        return "tiktok"
    if "instagram.com" in u:
        return "instagram"
    if "youtu" in u:
        return "youtube"
    return "otro"


def info(url, comentarios=200):
    args = ["-J", "--no-playlist", "--no-warnings"]
    if comentarios:
        args += ["--get-comments", "--extractor-args",
                 f"youtube:max_comments={comentarios},all,0,0;comment_sort=top"]
    try:
        return json.loads(llamar(args + [url]))
    except RuntimeError as e:
        if comentarios:   # algunas plataformas fallan con comentarios: reintentar sin ellos
            print("aviso: sin comentarios ->", str(e)[-200:])
            return json.loads(llamar(["-J", "--no-playlist", "--no-warnings", url]))
        raise


def lista_plana(url, n=30):
    try:
        d = json.loads(llamar(["-J", "--flat-playlist", "--playlist-end", str(n), "--no-warnings", url], timeout=300))
    except Exception as e:
        print("aviso: no se pudo leer la lista", url, "->", str(e)[-200:])
        return []
    return [e for e in d.get("entries", []) if e]


def dias_desde(upload_date):
    try:
        y, m, d = int(upload_date[:4]), int(upload_date[4:6]), int(upload_date[6:8])
        return max((date.today() - date(y, m, d)).days, 1)
    except Exception:
        return None


def promedio_canal(i, n=30):
    """Mediana de vistas de los ultimos videos del canal (para saber si este video es un caso fuera de lo normal)."""
    base = i.get("channel_url") or i.get("uploader_url")
    if not base:
        return None, 0
    if plataforma(base) == "youtube":
        corto = (i.get("duration") or 0) <= 180 and ("/shorts/" in (i.get("webpage_url") or "") or i.get("height", 0) > i.get("width", 1))
        base = base.rstrip("/") + ("/shorts" if corto else "/videos")
    vistas = [e.get("view_count") for e in lista_plana(base, n) if e.get("view_count")]
    if len(vistas) < 5:
        return None, len(vistas)
    return statistics.median(vistas), len(vistas)


def resumen(i):
    vistas, likes, coms = i.get("view_count"), i.get("like_count"), i.get("comment_count")
    dias = dias_desde(i.get("upload_date") or "")
    return {
        "plataforma": plataforma(i.get("webpage_url") or ""),
        "titulo": i.get("title"), "canal": i.get("channel") or i.get("uploader"),
        "seguidores": i.get("channel_follower_count"), "url": i.get("webpage_url"),
        "fecha": i.get("upload_date"), "dias_publicado": dias, "duracion_s": i.get("duration"),
        "vistas": vistas, "likes": likes, "comentarios": coms,
        "vistas_por_dia": round(vistas / dias) if vistas and dias else None,
        "likes_por_1000_vistas": round(1000 * likes / vistas, 1) if vistas and likes else None,
        "comentarios_por_1000_vistas": round(1000 * coms / vistas, 2) if vistas and coms else None,
        "etiquetas": (i.get("tags") or [])[:20], "descripcion": (i.get("description") or "")[:1500],
    }


def nombre_seguro(s, n=60):
    return re.sub(r"[^\w\-]+", "_", s or "video")[:n].strip("_")
