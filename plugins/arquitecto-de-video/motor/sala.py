# Sala de edición: una página local para mirar el video en formato celular o YouTube, con línea de tiempo
# (escenas, subtítulos, elementos, rótulos, capítulos, cortes verticales) y panel de estilo de subtítulos.
# Los cambios de estilo se ven al instante sobre el video (vista aproximada en el navegador) y, al guardar,
# quedan en proyecto.json (con respaldo) y las notas en 08_SALA/notas.md para que Claude las aplique.
# La pueden usar varias personas: cada nota lleva el nombre de quien la escribió y las notas no se pisan.
#
#   doble clic en sala.cmd (o el acceso "Sala de edición" del escritorio)  -> abre Chrome con el último proyecto
#   python sala.py ["<proyecto>"] [--puerto 8765] [--abrir] [--red]
# Sin --red solo responde en este computador (127.0.0.1). Con --red también en la red de la casa, con una clave
# en el enlace (para abrirla desde otro notebook o el celular conectado al mismo wifi).
# Se apaga cerrando su ventana.
import json, mimetypes, re, secrets, shutil, socket, subprocess, sys, threading, time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from estudio import Proyecto, palabras, buscar
import vivo

ESTUDIO = Path.home() / "EstudioPaltostaila"
ARG = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
PUERTO = int(ARG("--puerto", 8765))
HTML = Path(__file__).with_name("sala.html")
RED = "--red" in sys.argv
CLAVE = secrets.token_urlsafe(9) if RED else ""
CANDADO = threading.Lock()
CLAVES_ESTILO = {"estilo", "preset", "palabras", "posicion", "posicion_vertical", "palabras_clave", "fuente_viva",
                 "tamano_vivo", "color_texto", "color_clave", "color_clave2", "entrada", "destellos", "caja"}


def proyectos():
    """Proyectos con proyecto.json: los de EstudioPaltostaila/proyectos y las carpetas de proyectos_externos.txt."""
    raices = [ESTUDIO / "proyectos"]
    extra = ESTUDIO / "proyectos_externos.txt"
    if extra.exists():
        raices += [Path(l.strip().strip('"')) for l in extra.read_text(encoding="utf-8-sig").splitlines()
                   if l.strip() and not l.startswith("#")]
    vistos = {}
    for r in raices:
        if not r.exists():
            continue
        for f in [r / "proyecto.json", *r.glob("*/proyecto.json"), *r.glob("*/*/proyecto.json")]:
            if f.exists() and f.parent not in vistos:
                try:
                    c = json.loads(f.read_text(encoding="utf-8"))
                except Exception:
                    continue
                vistos[f.parent] = {"ruta": str(f.parent), "id": c.get("id") or f.parent.name, "nombre": c.get("nombre", ""),
                                    "canal": c.get("canal", ""), "version": c.get("version", ""), "fecha": f.stat().st_mtime}
    return sorted(vistos.values(), key=lambda x: -x["fecha"])


def elegir_inicial():
    pedido = next((a for a in sys.argv[1:] if not a.startswith("-") and Path(a).is_dir() and a not in (ARG("--puerto"),)), None)
    if pedido:
        return Proyecto(pedido)
    lista = proyectos()
    if not lista:
        sys.exit("No encontré proyectos con proyecto.json en EstudioPaltostaila\\proyectos ni en proyectos_externos.txt.")
    return Proyecto(lista[0]["ruta"])


pr = elegir_inicial()


def sala_dir():
    return pr.dir / "08_SALA"


def leer_notas():
    f = sala_dir() / "notas.json"
    notas = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    for k, n in enumerate(notas):          # notas viejas sin id
        n.setdefault("id", f"n{k}-{n.get('t', 0)}")
    return notas


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
    notas = leer_notas()
    return {"id": pr.id, "ruta": str(pr.dir), "nombre": pr.cfg.get("nombre", pr.id), "version": pr.version, "ancho": pr.ancho, "alto": pr.alto,
            "vertical": vertical, "duracion": pr.duracion(), "medios": medios(),
            "palabras": [{"w": w["word"], "a": round(w["start"], 3), "b": round(w["end"], 3)} for w in pals if "start" in w],
            "subtitulos": {k: v for k, v in pr["subtitulos"].items()}, "estilo_actual": v.e, "presets": vivo.PRESETS,
            "elementos": v.linea_de_tiempo(), "escenas": escenas, "rotulos": rotulos, "capitulos": capitulos,
            "cortes": cortes, "notas": notas}


def guardar(cuerpo):
    with CANDADO:
        SALA = sala_dir()
        SALA.mkdir(exist_ok=True)
        marca = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        autor = str(cuerpo.get("autor") or "sin nombre")[:40]
        archivo = pr.dir / "proyecto.json"
        estilo = {k: v for k, v in (cuerpo.get("subtitulos") or {}).items() if k in CLAVES_ESTILO}
        cfg = json.loads(archivo.read_text(encoding="utf-8"))
        if cuerpo.get("estilo_cambiado") and estilo:
            shutil.copy(archivo, SALA / f"proyecto_{marca}.json")      # respaldo: nunca se pisa una versión
            cfg.setdefault("subtitulos", {}).update(estilo)
            archivo.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
            with open(SALA / "historial.txt", "a", encoding="utf-8") as h:
                h.write(f"{marca}  {autor} cambió el estilo: {json.dumps(estilo, ensure_ascii=False)}\n")
        # notas: se juntan con las que ya estaban (de la otra persona), sin pisarlas
        actuales = {n["id"]: n for n in leer_notas()}
        for n in cuerpo.get("notas") or []:
            if "id" in n:
                actuales[n["id"]] = n
        for i in cuerpo.get("borradas") or []:
            actuales.pop(i, None)
        notas = sorted(actuales.values(), key=lambda n: n.get("t", 0))
        (SALA / "notas.json").write_text(json.dumps(notas, ensure_ascii=False, indent=2), encoding="utf-8")
        md = [f"# Notas de la sala de edición — {pr.id} {pr.version}", "",
              f"Último guardado {marca} por {autor}. Medio mirado: {cuerpo.get('medio', '?')}. Formato: {cuerpo.get('formato', '?')}.", ""]
        for n in notas:
            estado = "hecho" if n.get("hecho") else "pendiente"
            md.append(f"- [{estado}] **{int(n['t'] // 60)}:{n['t'] % 60:04.1f}** ({n.get('autor', '?')}, {n.get('formato', '?')}) — {n['texto']}")
        md += ["", "Estilo actual en proyecto.json → subtitulos:", "```json",
               json.dumps({k: v for k, v in cfg.get("subtitulos", {}).items() if k in CLAVES_ESTILO}, ensure_ascii=False, indent=2), "```"]
        (SALA / "notas.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"{marca} {autor}: guardó {'estilo y ' if cuerpo.get('estilo_cambiado') else ''}{len(notas)} notas", flush=True)
        return {"ok": True, "respaldo": f"08_SALA/proyecto_{marca}.json" if cuerpo.get("estilo_cambiado") else "", "notas": notas}


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

    def _permitido(self):
        if not RED or self.client_address[0] in ("127.0.0.1", "::1"):
            return True
        q = parse_qs(urlparse(self.path).query).get("clave", [""])[0]
        galleta = re.search(r"sala_clave=([\w-]+)", self.headers.get("Cookie", ""))
        return secrets.compare_digest(q or (galleta.group(1) if galleta else ""), CLAVE)

    def do_GET(self):
        global pr
        u = urlparse(self.path)
        if not self._permitido():
            return self._json({"error": "falta la clave del enlace"}, 403)
        if u.path == "/":
            b = HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            if RED:
                self.send_header("Set-Cookie", f"sala_clave={CLAVE}; Path=/; SameSite=Strict; HttpOnly")
            self.end_headers()
            self.wfile.write(b)
        elif u.path == "/proyectos":
            self._json({"actual": str(pr.dir), "lista": proyectos()})
        elif u.path == "/datos":
            try:
                pr = Proyecto(pr.dir)        # relee proyecto.json por si Claude lo cambió
                self._json(datos())
            except (Exception, SystemExit) as ex:
                self._json({"error": str(ex)}, 500)
        elif u.path == "/medio":
            self._archivo(parse_qs(u.query).get("r", [""])[0])
        else:
            self._json({"error": "no existe"}, 404)

    def do_POST(self):
        global pr
        if not self._permitido():
            return self._json({"error": "falta la clave del enlace"}, 403)
        ruta = urlparse(self.path).path
        largo = int(self.headers.get("Content-Length", 0))
        try:
            cuerpo = json.loads(self.rfile.read(largo).decode("utf-8") or "{}")
            if ruta == "/guardar":
                return self._json(guardar(cuerpo))
            if ruta == "/prueba":
                with CANDADO:
                    return self._json(prueba_real(cuerpo))
            if ruta == "/abrir":
                validas = {p["ruta"] for p in proyectos()}
                if cuerpo.get("ruta") not in validas:
                    return self._json({"error": "ese proyecto no está en la lista"}, 400)
                pr = Proyecto(cuerpo["ruta"])
                return self._json({"ok": True, "id": pr.id})
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


def ips_locales():
    ips = set()
    try:
        ips |= {i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)}
    except OSError:
        pass
    try:   # la dirección con la que este equipo sale a la red (no envía nada)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as u:
            u.connect(("10.255.255.255", 1))
            ips.add(u.getsockname()[0])
    except OSError:
        pass
    return sorted(i for i in ips if not i.startswith(("127.", "169.254.")))


def main():
    url = f"http://127.0.0.1:{PUERTO}/"
    try:
        srv = ThreadingHTTPServer(("0.0.0.0" if RED else "127.0.0.1", PUERTO), Sala)
    except OSError:          # ya hay una sala abierta en este puerto: solo se abre el navegador
        print(f"La sala ya estaba abierta en {url}", flush=True)
        if "--abrir" in sys.argv:
            subprocess.Popen(["cmd", "/c", "start", "chrome", url])
        return
    print(f"SALA DE EDICIÓN lista en {url}   (proyecto inicial: {pr.id}; se cambia arriba en la página)", flush=True)
    if RED:
        for ip in ips_locales():
            print(f"  desde otro aparato en el mismo wifi: http://{ip}:{PUERTO}/?clave={CLAVE}", flush=True)
        print("  (la clave cambia cada vez que se abre la sala; Windows puede preguntar si permite el acceso a la red privada)", flush=True)
    print("Para apagarla, cierra esta ventana.", flush=True)
    if "--abrir" in sys.argv:
        threading.Timer(0.8, lambda: subprocess.Popen(["cmd", "/c", "start", "chrome", url])).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
