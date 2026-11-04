# Sala de edición: una página local para mirar el video en formato celular o YouTube, con línea de tiempo
# (escenas, subtítulos, elementos, rótulos, capítulos, cortes verticales) y panel de estilo de subtítulos.
# Los cambios de estilo se ven al instante sobre el video (vista aproximada en el navegador) y, al guardar,
# quedan en proyecto.json (con respaldo) y las notas en 08_SALA/notas.md para que Claude las aplique.
#
#   python sala.py "<proyecto>" [--puerto 8765] [--abrir]
# Solo escucha en este computador (127.0.0.1). Se cierra con Ctrl+C o cerrando la ventana.
# --abrir abre Chrome en la dirección; sin --abrir, la persona la abre cuando quiera.
import json, mimetypes, re, shutil, subprocess, sys, threading, time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from estudio import Proyecto, palabras, buscar
import vivo

pr = Proyecto()
ARG = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
PUERTO = int(ARG("--puerto", 8765))
HTML = Path(__file__).with_name("sala.html")
SALA = pr.dir / "08_SALA"
CLAVES_ESTILO = {"estilo", "preset", "palabras", "posicion", "posicion_vertical", "palabras_clave", "fuente_viva",
                 "tamano_vivo", "color_texto", "color_clave", "color_clave2", "entrada", "destellos", "caja"}


def medios():
    out = []
    for f in sorted(pr.salida.glob("*.mp4"), key=lambda x: -x.stat().st_mtime):
        if ".parcial" not in f.name:
            out.append({"nombre": f.name, "ruta": str(f.relative_to(pr.dir)).replace("\\", "/"), "tipo": "video",
                        "con_subtitulos": "con-subtitulos" in f.name or "9x16" in f.name or "vivo-prueba" in f.name})
    solo = pr.tmp / "solo_video.mp4"
    narr = pr.tmp / "narracion.m4a"
    try:
        voz = pr.audios()[0]
    except SystemExit:
        voz = None
    audio = narr if narr.exists() else voz
    if solo.exists() and audio:
        out.insert(0, {"nombre": "Armado sin subtítulos + voz (recomendado para probar estilos)", "tipo": "video+audio",
                       "ruta": str(solo.relative_to(pr.dir)).replace("\\", "/"),
                       "audio": str(Path(audio).relative_to(pr.dir)).replace("\\", "/")})
    if audio:
        out.append({"nombre": "Solo la voz (todavía sin imágenes)", "tipo": "audio",
                    "ruta": str(Path(audio).relative_to(pr.dir)).replace("\\", "/")})
    return out


def datos():
    segs, pals = palabras(pr)
    vertical = pr.alto > pr.ancho
    v = vivo.Vivo(pr, pals, pr.ancho, pr.alto, vertical=vertical)
    escenas = []
    if pr.receta.exists():
        try:
            for r in pr.escenas():
                escenas.append({"n": r["n"], "a": r["t0"], "b": r["t1"], "imagen": r.get("imagen") or r.get("archivo") or ""})
        except Exception as ex:
            print("AVISO receta:", ex)
    def t(frase):
        try:
            return buscar(pals, frase)
        except ValueError:
            return None
    rotulos = [{"a": t(r["frase"]), "dura": float(r.get("segundos", 5)), "texto": f"{r.get('chico', '')}: {r.get('grande', '')}"}
               for r in pr["rotulos"]]
    capitulos = [{"a": 0.0 if i == 0 else t(c["frase"]), "texto": c["titulo"]} for i, c in enumerate(pr["capitulos"])]
    cortes = []
    for c in pr["vertical"]:
        a = float(c["desde_s"]) if "desde_s" in c else t(c.get("desde", ""))
        b = float(c["hasta_s"]) if "hasta_s" in c else (t(c["hasta"]) if c.get("hasta") else pr.duracion())
        cortes.append({"nombre": c["nombre"], "a": a, "b": b})
    notas = json.loads((SALA / "notas.json").read_text(encoding="utf-8")) if (SALA / "notas.json").exists() else []
    return {"id": pr.id, "nombre": pr.cfg.get("nombre", pr.id), "version": pr.version, "ancho": pr.ancho, "alto": pr.alto,
            "vertical": vertical, "duracion": pr.duracion(), "medios": medios(),
            "palabras": [{"w": w["word"], "a": round(w["start"], 3), "b": round(w["end"], 3)} for w in pals if "start" in w],
            "subtitulos": {k: v for k, v in pr["subtitulos"].items()}, "estilo_actual": v.e, "presets": vivo.PRESETS,
            "elementos": v.linea_de_tiempo(), "escenas": escenas, "rotulos": rotulos, "capitulos": capitulos,
            "cortes": cortes, "notas": notas}


def guardar(cuerpo):
    SALA.mkdir(exist_ok=True)
    marca = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    archivo = pr.dir / "proyecto.json"
    shutil.copy(archivo, SALA / f"proyecto_{marca}.json")          # respaldo: nunca se pisa una versión
    cfg = json.loads(archivo.read_text(encoding="utf-8"))
    estilo = {k: v for k, v in (cuerpo.get("subtitulos") or {}).items() if k in CLAVES_ESTILO}
    cfg.setdefault("subtitulos", {}).update(estilo)
    archivo.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    notas = cuerpo.get("notas") or []
    (SALA / "notas.json").write_text(json.dumps(notas, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [f"# Notas de la sala de edición — {pr.id} {pr.version}", "",
          f"Guardado {marca}. Medio mirado: {cuerpo.get('medio', '?')}. Formato: {cuerpo.get('formato', '?')}.", ""]
    for n in notas:
        estado = "hecho" if n.get("hecho") else "pendiente"
        md.append(f"- [{estado}] **{int(n['t'] // 60)}:{n['t'] % 60:04.1f}** — {n['texto']}")
    md += ["", "Estilo guardado en proyecto.json → subtitulos:", "```json", json.dumps(estilo, ensure_ascii=False, indent=2), "```"]
    (SALA / "notas.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"guardado {marca}: {len(estilo)} ajustes de estilo, {len(notas)} notas", flush=True)
    return {"ok": True, "respaldo": f"08_SALA/proyecto_{marca}.json", "notas": len(notas)}


class Sala(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def _archivo(self, ruta):
        f = (pr.dir / unquote(ruta).split("?")[0]).resolve()
        if pr.dir not in f.parents or not f.is_file():      # solo archivos dentro del proyecto
            return self._json({"error": "no permitido"}, 404)
        tam = f.stat().st_size
        ini, fin = 0, tam - 1
        rango = self.headers.get("Range")
        m = re.match(r"bytes=(\d*)-(\d*)", rango or "")
        if m:
            if m.group(1):
                ini = int(m.group(1))
                fin = int(m.group(2)) if m.group(2) else tam - 1
            else:
                ini = tam - int(m.group(2))
            fin = min(fin, tam - 1)
        self.send_response(206 if m else 200)
        self.send_header("Content-Type", mimetypes.guess_type(f.name)[0] or "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(fin - ini + 1))
        if m:
            self.send_header("Content-Range", f"bytes {ini}-{fin}/{tam}")
        self.end_headers()
        with open(f, "rb") as h:
            h.seek(ini)
            falta = fin - ini + 1
            try:
                while falta > 0:
                    trozo = h.read(min(1 << 20, falta))
                    if not trozo:
                        break
                    self.wfile.write(trozo)
                    falta -= len(trozo)
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
                pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            b = HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)
        elif u.path == "/datos":
            try:
                global pr
                pr = Proyecto(pr.dir)        # relee proyecto.json por si Claude lo cambió
                self._json(datos())
            except (Exception, SystemExit) as ex:
                self._json({"error": str(ex)}, 500)
        elif u.path == "/medio":
            self._archivo(parse_qs(u.query).get("r", [""])[0])
        else:
            self._json({"error": "no existe"}, 404)

    def do_POST(self):
        ruta = urlparse(self.path).path
        largo = int(self.headers.get("Content-Length", 0))
        try:
            cuerpo = json.loads(self.rfile.read(largo).decode("utf-8") or "{}")
            if ruta == "/guardar":
                return self._json(guardar(cuerpo))
            if ruta == "/prueba":
                return self._json(prueba_real(cuerpo))
            self._json({"error": "no existe"}, 404)
        except Exception as ex:
            self._json({"error": str(ex)}, 500)


def prueba_real(cuerpo):
    """Render real (el mismo que el final) de unos segundos alrededor del momento que se está mirando."""
    t = float(cuerpo.get("t", 0))
    a, b = max(0.0, t - 2), min(pr.duracion(), t + float(cuerpo.get("segundos", 10)))
    cmd = [sys.executable, str(Path(__file__).with_name("vivo.py")), str(pr.dir), "--prueba", f"{a:.2f}-{b:.2f}"]
    if cuerpo.get("formato") == "celular":
        cmd.append("--vertical")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=Path(__file__).parent)
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout)[-600:])
    nombre = f"{pr.base_nombre}_vivo-prueba{'-9x16' if cuerpo.get('formato') == 'celular' else ''}.mp4"
    return {"ok": True, "ruta": str((pr.salida / nombre).relative_to(pr.dir)).replace("\\", "/"), "desde": a}


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PUERTO), Sala)
    url = f"http://127.0.0.1:{PUERTO}/"
    print(f"SALA DE EDICIÓN de {pr.id} lista en {url}  (Ctrl+C para cerrar)", flush=True)
    if "--abrir" in sys.argv:
        threading.Timer(0.8, lambda: subprocess.Popen(["cmd", "/c", "start", "chrome", url])).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
