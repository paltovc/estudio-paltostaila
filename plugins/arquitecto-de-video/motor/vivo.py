# Capa "viva": subtítulos dinámicos palabra por palabra y elementos animados que entran en la palabra exacta
# (íconos, tarjeta-lista, cadena de fichas, lluvia de billetes o confeti, texto grande). Todo sale como eventos ASS
# que se queman con ffmpeg (libass): sirve para videos largos, Shorts, música o cursos.
#
# En proyecto.json (todo opcional):
#   "subtitulos": {"estilo": "vivo", "preset": "finanzas", "palabras": 3, "posicion": "abajo",
#                  "palabras_clave": ["fondo de emergencia", "urgencia"], "fuente": "Arial Black"}
#   "elementos": [
#     {"tipo": "icono", "icono": "reloj", "en": {"frase": "dos semanas"}, "pos": "arriba-izq", "dura": 2},
#     {"tipo": "lista", "titulo": "Antes de invertir", "en": {"frase": "cinco preguntas"},
#      "items": [{"texto": "¿Tengo margen?", "frase": "margen en mi presupuesto"}, "…"], "pos": "derecha"},
#     {"tipo": "fichas", "items": ["Entender", "Evaluar", "Decidir"], "en": {"frase": "entender evaluar"}, "cada": 0.6},
#     {"tipo": "lluvia", "simbolo": "billetes", "en": {"frase": "ganó miles"}, "dura": 2.5},
#     {"tipo": "texto", "texto": "x2", "en": {"frase": "el precio se duplica"}, "dura": 1.5}]
# Presets de estilo: finanzas, rosa, bachata, curso, documental, reel (cada proyecto puede cambiar color, fuente y posición).
# 0.15 (references/motor-0150-camara.md): preset "reel"; sonidos con los subtítulos y los elementos ("sonido": "pop",
# los mezcla sonidos.py); "margen_caras"; la tarjeta-lista se mide girada; en Shorts los elementos pueden esquivar caras.
from pathlib import Path
import math, random, re, unicodedata
from estudio import buscar, ts, norm as tokens
try:
    from estudio import SIN_METADATOS          # T1: las entregas salen sin GPS, celular ni fecha del original
except Exception:
    SIN_METADATOS = ["-map_metadata", "-1", "-map_chapters", "-1"]

PRESETS = {
    "finanzas":   dict(fuente="Arial Black", tam=78, color="FFFFFF", clave="FFD23F", clave2="6AD15B", borde="101010", grosor=7,
                       sombra=3, caja=False, palabras=3, entrada="pop", destellos=True, mano="Ink Free"),
    "rosa":       dict(fuente="Segoe UI Black", tam=80, color="FFFFFF", clave="FF7AC6", clave2="FFD6F0", borde="1A1A1A", grosor=6,
                       sombra=4, caja=False, palabras=1, entrada="pop", destellos=True, mano="Ink Free"),
    "bachata":    dict(fuente="Segoe UI Black", tam=78, color="FFF4E6", clave="FFB347", clave2="FF5E5E", borde="2A0E05", grosor=6,
                       sombra=4, caja=False, palabras=2, entrada="sube", destellos=True, mano="Ink Free"),
    "curso":      dict(fuente="Segoe UI Semibold", tam=64, color="FFFFFF", clave="4FC3F7", clave2="FFFFFF", borde="000000", grosor=0,
                       sombra=0, caja=True, palabras=3, entrada="fundido", destellos=False, mano="Segoe Print"),
    "documental": dict(fuente="Georgia", tam=62, color="F3E9D2", clave="E9C46A", clave2="F3E9D2", borde="1B1B1B", grosor=4,
                       sombra=2, caja=False, palabras=4, entrada="fundido", destellos=False, mano="Segoe Print"),
    # 0.15: reel de una persona hablando: 1-2 palabras grandes, centro-bajo, entrada pop, palabra clave en color de acento
    "reel":       dict(fuente="Arial Black", tam=96, color="FFFFFF", clave="FFFFFF", clave2="FFE14D", borde="101010", grosor=9,
                       sombra=4, caja=False, palabras=2, entrada="pop", destellos=False, mano="Ink Free",
                       posicion=0.78, posicion_vertical=0.66),
}
# 0.15: nombres cortos de sonido para "subtitulos.sonido" y "sonido" de un elemento (archivos del banco CC0 del estudio,
# paquete Interfaz de Kenney). También se acepta el nombre de cualquier archivo del banco o de 05_SONIDOS.
SONIDOS = {"pop": "drop_002.ogg", "clic": "click_002.ogg", "click": "click_002.ogg", "tic": "tick_002.ogg",
           "suave": "select_002.ogg", "campana": "confirmation_002.ogg", "golpe": "bong_001.ogg", "cambio": "switch_002.ogg"}
PALETA = ["FFD23F", "6AD15B", "4FC3F7", "FF7AC6", "FF8C42", "FFFFFF"]


def bgr(hexrgb, alfa=0):
    h = hexrgb.lstrip("#")
    return f"&H{alfa:02X}{h[4:6]}{h[2:4]}{h[0:2]}"


def c(hexrgb):
    h = hexrgb.lstrip("#")
    return f"&H{h[4:6]}{h[2:4]}{h[0:2]}&"


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9ñ%$]", "", "".join(ch for ch in s if not unicodedata.combining(ch)))


def limpio(s):
    return s.replace("{", "(").replace("}", ")").replace("\\", "/")


def caja_girada(caja, grados, origen=None):
    """(0.15) Caja recta que contiene a `caja` girada `grados` (como \\frz de ASS: positivo = contra el reloj) alrededor
    de `origen` (por defecto su esquina de arriba a la izquierda, que es sobre lo que gira un dibujo \\an7\\pos)."""
    if not grados:
        return tuple(caja)
    x0, y0, x1, y1 = caja
    ox, oy = origen or (x0, y0)
    s, co = math.sin(math.radians(grados)), math.cos(math.radians(grados))
    pts = [(ox + (x - ox) * co + (y - oy) * s, oy - (x - ox) * s + (y - oy) * co) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


# ---------- dibujos vectoriales (modo \p1, coordenadas en píxeles, centradas en 0,0) ----------
def _poligono(puntos):
    p = [f"{round(x)} {round(y)}" for x, y in puntos]
    return "m " + p[0] + " l " + " ".join(p[1:])


def estrella(r, puntas=5, interior=0.45):
    pts = []
    for i in range(puntas * 2):
        a = -math.pi / 2 + i * math.pi / puntas
        rr = r if i % 2 == 0 else r * interior
        pts.append((r + rr * math.cos(a), r + rr * math.sin(a)))
    return _poligono(pts)


def destello(r):
    return estrella(r, 4, 0.22)


def circulo(r):
    k = 0.5523 * r
    return (f"m {r} 0 b {r + k} 0 {2 * r} {r - k} {2 * r} {r} b {2 * r} {r + k} {r + k} {2 * r} {r} {2 * r} "
            f"b {r - k} {2 * r} 0 {r + k} 0 {r} b 0 {r - k} {r - k} 0 {r} 0")


def rect(w, h, rad=0):
    if not rad:
        return f"m 0 0 l {w} 0 {w} {h} 0 {h}"
    r = min(rad, h / 2, w / 2)
    k = 0.5523 * r
    return (f"m {r} 0 l {w - r} 0 b {w - r + k} 0 {w} {r - k} {w} {r} l {w} {h - r} b {w} {h - r + k} {w - r + k} {h} {w - r} {h} "
            f"l {r} {h} b {r - k} {h} 0 {h - r + k} 0 {h - r} l 0 {r} b 0 {r - k} {r - k} 0 {r} 0")


def corazon(r):
    s = r / 50
    return (f"m {50 * s} {90 * s} b {10 * s} {60 * s} {-5 * s} {35 * s} {15 * s} {15 * s} b {30 * s} {0} {48 * s} {8 * s} {50 * s} {22 * s} "
            f"b {52 * s} {8 * s} {70 * s} {0} {85 * s} {15 * s} b {105 * s} {35 * s} {90 * s} {60 * s} {50 * s} {90 * s}")


def check(r):
    s = r / 50
    return _poligono([(8 * s, 52 * s), (22 * s, 38 * s), (42 * s, 58 * s), (80 * s, 18 * s), (94 * s, 32 * s), (42 * s, 86 * s)])


def flecha(r):
    s = r / 50
    return _poligono([(0, 38 * s), (60 * s, 38 * s), (60 * s, 18 * s), (100 * s, 50 * s), (60 * s, 82 * s), (60 * s, 62 * s), (0, 62 * s)])


def triangulo(r):
    s = r / 50
    return _poligono([(50 * s, 4 * s), (98 * s, 92 * s), (2 * s, 92 * s)])


def avion(r):
    s = r / 50
    return _poligono([(0, 45 * s), (100 * s, 5 * s), (62 * s, 95 * s), (48 * s, 58 * s)])


# ---------- biblioteca de animaciones de entrada ----------
# Aprendidas de las 20 animaciones de texto que describe la ayuda pública de Canva (Typewriter, Ascend, Rise, Pan...)
# y hechas con etiquetas ASS propias. Nombre en español; también se acepta el nombre en inglés.
ALIAS = {"fade": "fundido", "rise": "subir", "baseline": "base", "shift": "bajar", "pan": "panear", "skate": "patinar",
         "drift": "deriva", "tumble": "voltereta", "bounce": "rebote", "stomp": "pisoton", "tectonic": "tectonico",
         "scrapbook": "album", "breathe": "respirar", "typewriter": "maquina", "burst": "estallido", "roll": "rodar",
         "ascend": "ascender", "block": "bloque", "flicker": "neon", "sube": "subir"}
DE_LINEA = {"pop", "fundido", "subir", "base", "bajar", "panear", "patinar", "deriva", "voltereta", "rebote", "pisoton",
            "album", "neon", "respirar", "desliza", "sello", "brillo"}
POR_LETRA = {"maquina", "estallido", "rodar", "ascender"}
ESPECIALES = {"tectonico", "bloque"}
TODAS = sorted(DE_LINEA | POR_LETRA | ESPECIALES)


def nombre_animacion(n):
    n = (n or "pop").lower()
    return ALIAS.get(n, n)


def entrada_linea(n, x, y, tam, W, H, dura_ms=1600):
    """Etiquetas de entrada para toda la línea (incluye su \\pos o \\move)."""
    n = nombre_animacion(n)
    P = f"\\pos({x},{y})"
    m = lambda dx, dy, ms: f"\\move({x + dx},{y + dy},{x},{y},0,{ms})"
    t = {
        "pop": P + "\\fscx0\\fscy0\\t(0,150,\\fscx115\\fscy115)\\t(150,240,\\fscx100\\fscy100\\frz5)\\t(240,320,\\frz-3)\\t(320,400,\\frz0)",
        "fundido": P + "\\fad(250,0)",
        "subir": m(0, round(0.06 * H), 350) + "\\alpha&HFF&\\t(0,250,\\alpha&H00&)",
        "base": m(0, round(tam * 0.9), 180) + f"\\clip(0,0,{W},{y + round(tam * 0.55)})",
        "bajar": m(0, -round(0.06 * H), 350) + "\\alpha&HFF&\\t(0,250,\\alpha&H00&)",
        "panear": m(-round(0.08 * W), 0, 400) + "\\alpha&HFF&\\t(0,350,\\alpha&H00&)",
        "patinar": m(round(0.18 * W), 0, 300),
        "deriva": m(-round(0.05 * W), 0, 900) + "\\alpha&HFF&\\t(0,600,\\alpha&H00&)",
        "voltereta": m(-round(0.06 * W), -round(0.03 * H), 500) + "\\frz180\\fscx50\\fscy50\\t(0,500,\\frz0\\fscx100\\fscy100)",
        "rebote": m(0, -round(0.25 * H), 240) + "\\t(240,320,\\fscx112\\fscy88)\\t(320,420,\\fscx100\\fscy100)",
        "pisoton": P + "\\fscx300\\fscy300\\alpha&HFF&\\t(0,140,\\fscx100\\fscy100\\alpha&H00&)\\t(140,190,\\frz2)\\t(190,240,\\frz-1)\\t(240,280,\\frz0)",
        "album": P + "\\frz-10\\fad(80,0)\\t(0,180,\\frz5)\\t(180,260,\\frz3)",
        "neon": P + "\\alpha&HFF&\\t(0,60,\\alpha&H00&)\\t(60,120,\\alpha&HFF&)\\t(120,200,\\alpha&H00&)\\t(200,250,\\alpha&H90&)\\t(250,320,\\alpha&H00&)",
        "desliza": m(-round(0.5 * W), 0, 260),
        "sello": P + "\\frz-14\\fscx260\\fscy260\\alpha&HFF&\\t(0,160,\\fscx100\\fscy100\\alpha&H00&)",
        "brillo": P + "\\blur18\\alpha&HFF&\\t(0,260,\\blur0\\alpha&H00&)",
    }
    if n == "respirar":
        pulsos = "".join(f"\\t({k},{k + 400},\\fscx{106 if (k // 400) % 2 == 0 else 100}\\fscy{106 if (k // 400) % 2 == 0 else 100})"
                         for k in range(0, max(400, dura_ms - 400), 400))
        return P + "\\fad(150,0)" + pulsos
    return t.get(n, t["pop"])


def texto_por_letra(n, txt, ms_letra=55):
    """Texto con etiquetas dentro de la línea: cada letra (o palabra) entra en su momento."""
    n = nombre_animacion(n)
    if n == "ascender":
        out, k = [], 0
        for palabra in txt.split(" "):
            out.append(f"{{\\alpha&HFF&\\fscy40\\t({k},{k + 200},\\alpha&H00&\\fscy100)}}{palabra}")
            k += 180
        return " ".join(out)
    out = []
    for i, ch in enumerate(txt):
        t = i * ms_letra
        if n == "maquina":
            out.append(f"{{\\alpha&HFF&\\t({t},{t + 1},\\alpha&H00&)}}{ch}")
        elif n == "estallido":
            out.append(f"{{\\alpha&HFF&\\fscx170\\fscy170\\t({t},{t + 130},\\alpha&H00&\\fscx100\\fscy100)}}{ch}")
        elif n == "rodar":
            out.append(f"{{\\alpha&HFF&\\frx-90\\t({t},{t + 170},\\alpha&H00&\\frx0)}}{ch}")
        else:
            out.append(ch)
    return "".join(out)


# ---------- el generador ----------
class Vivo:
    def __init__(self, pr, pals, W, H, vertical=False):
        self.pr, self.pals, self.W, self.H, self.vertical = pr, pals, W, H, vertical
        sub = dict(pr.cfg.get("subtitulos", {}))
        base = PRESETS.get(sub.get("preset", "finanzas"), PRESETS["finanzas"])
        # "fuente" y "tamano" son de los subtítulos clásicos; para la capa viva se usa "fuente_viva" / "tamano_vivo"
        self.e = {**base, **{k: v for k, v in sub.items() if k in base and k not in ("fuente", "tam")}}
        self.e["fuente"] = sub.get("fuente_viva", self.e["fuente"])
        self.e["tam"] = float(sub.get("tamano_vivo", self.e["tam"])) * (1.25 if vertical else 1)   # en el celular, letra más grande
        for k in ("color", "clave", "clave2"):
            if sub.get(f"color_{k}" if k != "color" else "color_texto"):
                self.e[k] = sub[f"color_{k}" if k != "color" else "color_texto"].lstrip("#")
        self.esc = (W if vertical else H) / 1080
        self.claves = [norm(x) for x in sub.get("palabras_clave", [])]
        self.claves_frases = [[norm(t) for t in x.split()] for x in sub.get("palabras_clave", []) if " " in x]
        k_pos = "posicion_vertical" if vertical else "posicion"
        pos = sub.get(k_pos, base.get(k_pos, "abajo"))          # 0.15: un preset puede traer su posición (reel)
        self.y = {"arriba": 0.30, "medio": 0.50, "abajo": 0.70 if vertical else 0.84}.get(pos, pos if isinstance(pos, float) else 0.7)
        if vertical:   # zona segura de Reels/TikTok/Shorts: sin la franja de arriba, los botones de la derecha ni el texto de abajo
            self.y = min(max(self.y, 0.14), 0.76)
        self.x = 0.46 if vertical else 0.5
        self.rand = random.Random(7)
        self.mapa, self.movidos = None, []
        self.ocupado = []          # (desde, hasta, caja) de lo que ya está fijo en pantalla (contador): los demás lo evitan
        self._pos_progreso = None
        # 0.15: aire alrededor de caras y cabezas al medir (fracción de su tamaño; 0 = medir justo sobre la cabeza, como antes)
        self.margen_caras = float(sub.get("margen_caras", 0.08))
        self.ocultar_si_tapa = False   # 0.15, Shorts con «esquivar caras»: lo que no encuentra lugar libre no se muestra

    def usar_mapa(self, video, con_texto=True, mapa=None):
        """Activa "no tapar caras": cada elemento se corre a donde no cubra cabezas, caras, globos ni texto de la imagen.
        mapa (0.15): un mapa ya hecho, con las regiones en píxeles de ESTE cuadro (lo usa vertical.py en los Shorts)."""
        if mapa is not None:
            self.mapa = mapa
            return
        import caras
        if Path(video).exists() and not self.vertical:
            self.mapa = caras.Mapa(video, self.W, self.H, con_texto)

    def _regiones(self, a, b, muestras=8):
        """Lo que no hay que tapar entre a y b, con el margen alrededor de caras y cabezas."""
        if self.mapa is None:
            return []
        import caras
        return caras.con_margen(self.mapa.regiones(a, b, muestras), self.margen_caras)

    def _oculto(self, d, a, b, caja, muestras=8):
        """(0.15) En un Short con «esquivar caras»: True si el elemento, ya en su mejor lugar, todavía tapa una cara, una
        cabeza o texto de la imagen. Entonces no se muestra y queda anotado."""
        if not self.ocultar_si_tapa or self.mapa is None or d.get("fijo"):
            return False
        import caras
        if caras.tapa(caja, self._regiones(a, b, muestras)) < 1:
            return False
        self.movidos.append((round(a, 1), f"{d.get('tipo')} oculto", (round(caja[0]), round(caja[1])), None, 0, 0.0))
        return True

    def _lugar(self, d, defecto, a, b, caja, candidatos=None, muestras=8, pos=None):
        """Posición del elemento: la pedida si no tapa nada importante; si tapa, la mejor alternativa cercana.
        También evita lo que ya quedó fijo en pantalla en ese momento (el contador de progreso)."""
        x, y = pos if pos else self._pos(d.get("pos"), defecto)
        if d.get("fijo"):
            return x, y
        import caras
        occ = [o for oa, ob, o in self.ocupado if oa < b and ob > a]
        reg = self._regiones(a, b, muestras)
        if not reg and not occ:
            return x, y
        if candidatos is None and self.vertical and self.mapa is not None:
            # 0.15 (Shorts con «esquivar caras»): lugares dentro de la zona segura del 9:16, bajo el título y sin la columna de botones
            candidatos = [(round(fx * self.W), round(fy * self.H)) for fy in (0.34, 0.42, 0.50, 0.58, 0.66, 0.72)
                          for fx in (0.22, 0.46, 0.68)]
        def pen(p):                     # tapar algo importante o el contador, más salirse del cuadro (se cortaría el texto)
            c = caja(*p)
            area = max(1.0, (c[2] - c[0]) * (c[3] - c[1]))
            dentro = max(0, min(c[2], self.W) - max(c[0], 0)) * max(0, min(c[3], self.H) - max(c[1], 0))
            # tapar el contador se mide sobre el contador (una fila ancha de fichas que lo cruza en una punta igual lo tapa)
            return caras.castigo(c, reg, por_region=True) + sum(10 * caras.cruce(c, o) / max(1.0, (o[2] - o[0]) * (o[3] - o[1])) for o in occ) + 30 * (1 - dentro / area)
        p0 = pen((x, y))
        if p0 < 0.05:
            return x, y
        if candidatos is None:
            candidatos = [(round(fx * self.W), round(fy * self.H)) for fy in (0.16, 0.30, 0.45, 0.60)
                          for fx in (0.14, 0.30, 0.50, 0.70, 0.86)]
        diag = math.hypot(self.W, self.H)
        mejor = min(candidatos, key=lambda p: pen(p) + 0.6 * math.hypot(p[0] - x, p[1] - y) / diag)
        # lo que se anota como "ahora" es lo que sigue tapando caras, cabezas o texto de la imagen (≥ 1 = revisar a mano)
        en_caras = lambda p: round(caras.tapa(caja(*p), reg), 2)
        if pen(mejor) < p0 * 0.6:
            self.movidos.append((round(a, 1), d.get("tipo"), (x, y), mejor, round(p0, 2), en_caras(mejor)))
            return mejor
        if p0 >= 0.5:        # no hubo un lugar mejor: queda anotado para revisarlo a mano (terminado.py lo marca)
            self.movidos.append((round(a, 1), d.get("tipo"), (x, y), (x, y), round(p0, 2), en_caras((x, y))))
        return x, y

    # estilos que se agregan a la cabecera ASS
    def estilos(self):
        e, s = self.e, self.esc
        borde_estilo = 3 if e["caja"] else 1
        fondo = bgr("000000", 0x50) if e["caja"] else bgr("000000", 0x80)
        return [
            f"Style: Vivo,{e['fuente']},{round(e['tam'] * s)},{bgr(e['color'])},{bgr(e['color'])},{bgr(e['borde'])},{fondo},-1,0,0,0,100,100,0,0,"
            f"{borde_estilo},{round(e['grosor'] * s) if not e['caja'] else round(14 * s)},{round(e['sombra'] * s)},5,0,0,0,1",
            f"Style: VivoMano,{e['mano']},{round(46 * s)},{bgr('2B2118')},{bgr('2B2118')},{bgr('FFFFFF')},{bgr('000000', 0xFF)},-1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
            f"Style: VivoFicha,{e['fuente']},{round(40 * s)},{bgr('FFFFFF')},{bgr('FFFFFF')},{bgr('101010')},{bgr('000000', 0xFF)},-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
            f"Style: VivoDibujo,Arial,20,{bgr('FFFFFF')},{bgr('FFFFFF')},{bgr('101010')},{bgr('000000', 0xA0)},0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
        ]

    def _es_clave(self, i):
        w = norm(self.pals[i]["word"])
        if not w:
            return False
        if w in self.claves or re.search(r"\d", w) or "%" in w or "$" in w:
            return True
        for f in self.claves_frases:
            for k in range(len(f)):
                ini = i - k
                if ini >= 0 and [norm(p["word"]) for p in self.pals[ini:ini + len(f)]] == f:
                    return True
        return False

    def _grupos(self, t0, t1):
        n_max = int(self.e["palabras"])
        lim = 14 if self.vertical else 26
        grupos, g = [], []
        idx = [i for i, w in enumerate(self.pals) if "start" in w and w["end"] > t0 and w["start"] < t1]
        for k, i in enumerate(idx):
            w = self.pals[i]
            if g:
                ant = self.pals[g[-1]]
                texto = " ".join(self.pals[j]["word"] for j in g + [i])
                if (len(g) >= n_max or len(texto) > lim or w["start"] - ant["end"] > 0.35
                        or ant["word"].rstrip("»\"'”)").endswith((".", ",", "?", "!", ":", ";", "…"))):
                    grupos.append(g); g = []
            g.append(i)
        if g:
            grupos.append(g)
        return grupos

    def subtitulos(self, t0=0.0, t1=1e9):
        """Un evento por palabra: se ve el grupo y la palabra que suena va destacada."""
        e, s, out = self.e, self.esc, []
        X, Y = round(self.W * self.x), round(self.H * self.y)
        grupos = self._grupos(t0, t1)
        for gi, g in enumerate(grupos):
            fin_grupo = self.pals[g[-1]]["end"] + 0.25
            if gi + 1 < len(grupos):
                fin_grupo = min(fin_grupo, self.pals[grupos[gi + 1][0]]["start"] - 0.02)
            for k, i in enumerate(g):
                a = self.pals[i]["start"] if k else self.pals[g[0]]["start"]
                b = self.pals[g[k + 1]]["start"] if k + 1 < len(g) else fin_grupo
                a, b = max(a, t0), min(b, t1)
                if b - a < 0.04:
                    continue
                partes = []
                for j in g:
                    pal = limpio(self.pals[j]["word"])
                    if e["palabras"] > 1 and j != i:
                        partes.append(pal if j > i else f"{{\\c{c(e['color'])}}}{pal}")
                    else:
                        color = e["clave2"] if self._es_clave(j) else e["clave"]
                        if e["palabras"] == 1 and not self._es_clave(j):
                            color = e["color"]
                        grande = "\\fscx112\\fscy112" if self._es_clave(j) else ""
                        partes.append(f"{{\\c{c(color)}{grande}}}{pal}{{\\c{c(e['color'])}\\fscx100\\fscy100}}")
                anim = ""
                if k == 0 or e["palabras"] == 1:
                    ent = nombre_animacion(e["entrada"])
                    if ent == "pop":   # en subtítulos, un pop corto (cada pocas palabras)
                        anim = f"\\pos({X},{Y})\\fscx70\\fscy70\\t(0,90,\\fscx108\\fscy108)\\t(90,150,\\fscx100\\fscy100)"
                    else:
                        anim = entrada_linea(ent if ent in DE_LINEA else "fundido", X, Y, round(e["tam"] * s), self.W, self.H,
                                             int((b - a) * 1000))
                pos = "" if ("\\move" in anim or "\\pos" in anim) else f"\\pos({X},{Y})"
                txt = "".join(p + " " for p in partes).strip()
                out.append(f"Dialogue: 4,{ts(a - t0)},{ts(b - t0)},Vivo,,0,0,0,,{{\\an5{pos}{anim}}}{txt}")
                # destellos junto a las palabras clave (una vez por palabra)
                if e["destellos"] and self._es_clave(i):
                    ancho = len(" ".join(self.pals[j]["word"] for j in g)) * e["tam"] * s * 0.33
                    for lado in (-1, 1):
                        r = round(18 * s)
                        out.append(f"Dialogue: 5,{ts(a - t0)},{ts(min(b, a + 0.9) - t0)},VivoDibujo,,0,0,0,,"
                                   f"{{\\an5\\pos({round(X + lado * (ancho + 30 * s))},{round(Y - 28 * s)})\\1c{c(e['clave'])}\\bord0"
                                   f"\\fscx0\\fscy0\\t(0,150,\\fscx120\\fscy120)\\t(150,300,\\fscx90\\fscy90)\\frz{lado * 15}\\fad(0,200)\\p1}}{destello(r)}{{\\p0}}")
        return out

    # ---- elementos ----
    def buscar(self, frase, desde=0.0):
        """Como estudio.buscar, pero desde un segundo dado (para frases que se repiten en el guion)."""
        obj = tokens(frase)
        toks = [(tokens(w["word"]) or [""])[0] for w in self.pals]
        for i in range(len(toks) - len(obj) + 1):
            if toks[i:i + len(obj)] == obj and self.pals[i]["start"] >= desde - 0.01:
                return self.pals[i]["start"]
        raise ValueError(f"no encontré '{frase}' después del segundo {desde:.1f}")

    def _t(self, en, desde=0.0):
        if isinstance(en, (int, float)):
            return float(en)
        if isinstance(en, str):
            en = {"frase": en}
        if "frase" in en:
            if "despues" in en:
                d = en["despues"]
                desde = max(desde, float(d) if isinstance(d, (int, float)) else self.buscar(d))
            return self.buscar(en["frase"], desde) + float(en.get("desfase", 0))
        return float(en.get("segundo", 0))

    def _pos(self, p, defecto="arriba-izq"):
        p = p or defecto
        if isinstance(p, (list, tuple)):
            return round(p[0] * self.W), round(p[1] * self.H)
        v = self.vertical
        arriba = 0.34 if v else 0.20   # en vertical, debajo del título del Short
        tabla = {"arriba-izq": (0.18, arriba), "arriba-der": (0.70 if v else 0.82, arriba),
                 "centro": (0.46 if v else 0.5, 0.45), "izquierda": (0.20, 0.45), "derecha": (0.70 if v else 0.80, 0.45),
                 "abajo-izq": (0.18, 0.66 if v else 0.70), "abajo-der": (0.70 if v else 0.82, 0.66 if v else 0.70)}
        x, y = tabla.get(p, tabla[defecto])
        if v:
            x = min(x, 0.78)
        return round(x * self.W), round(y * self.H)

    def _pop(self, dura_ms):
        return f"\\fscx0\\fscy0\\t(0,160,\\fscx115\\fscy115)\\t(160,260,\\fscx100\\fscy100)\\fad(0,220)"

    def icono(self, d, t0):
        a = self._t(d["en"]) - t0
        b = a + float(d.get("dura", 2.0))
        r = round(float(d.get("tam", 0.07)) * (self.W if self.vertical else self.H * 1.1))
        x, y = self._lugar(d, "arriba-izq", t0 + a, t0 + b, lambda x, y: (x - r, y - r, x + r, y + r))
        if self._oculto(d, t0 + a, t0 + b, (x - r, y - r, x + r, y + r)):
            return []
        nombre, ev = d.get("icono", "estrella"), []
        col = d.get("color")
        base = f"Dialogue: 6,{ts(a)},{ts(b)},VivoDibujo,,0,0,0,,{{\\an5\\pos({x},{y}){self._pop(0)}"
        def dib(forma, relleno, borde="101010", bord=4, extra=""):
            ev.append(f"{base}\\1c{c(relleno)}\\3c{c(borde)}\\bord{round(bord * self.esc)}{extra}\\p1}}{forma}{{\\p0}}")
        def letra(txt, color="101010", tam=1.1):
            ev.append(f"Dialogue: 7,{ts(a)},{ts(b)},Vivo,,0,0,0,,{{\\an5\\pos({x},{y}){self._pop(0)}\\fs{round(r * tam)}\\c{c(color)}\\bord0\\shad0}}{txt}")
        if nombre == "reloj":
            dib(circulo(r), col or "FFFFFF", "101010", 6)
            ev.append(f"Dialogue: 7,{ts(a + 0.16)},{ts(b)},VivoDibujo,,0,0,0,,{{\\an7\\pos({x - 4},{y - round(r * 0.72)})\\org({x},{y})\\1c{c('101010')}\\bord0\\fad(80,220)\\t(0,{int((b - a) * 1000)},\\frz-330)\\p1}}{rect(round(8 * self.esc), round(r * 0.76))}{{\\p0}}")
            ev.append(f"Dialogue: 7,{ts(a + 0.16)},{ts(b)},VivoDibujo,,0,0,0,,{{\\an7\\pos({x - 4},{y - round(r * 0.45)})\\org({x},{y})\\frz-90\\1c{c('C23B3B')}\\bord0\\fad(80,220)\\p1}}{rect(round(8 * self.esc), round(r * 0.5))}{{\\p0}}")
        elif nombre == "dinero":
            dib(circulo(r), col or "FFC93C", "8A5A00", 5); letra("$", "7A4E00")
        elif nombre == "alerta":
            dib(triangulo(r), col or "FFD23F", "101010", 5); letra("!", "101010", 1.0)
        elif nombre == "check":
            dib(circulo(r), col or "6AD15B", "1E5E2B", 5)
            ev.append(f"{base}\\1c{c('FFFFFF')}\\bord0\\p1}}{check(r * 0.75)}{{\\p0}}")
        elif nombre == "corazon":
            dib(corazon(r), col or "FF5E7E", "7A1030", 4)
        elif nombre == "flecha":
            dib(flecha(r), col or "6AD15B", "1E5E2B", 4, f"\\frz{d.get('giro', 0)}")
        elif nombre == "avion":
            dib(avion(r), col or "FFFFFF", "101010", 4, "\\frz10")
        elif nombre == "lupa":
            dib(circulo(r * 0.7), "FFFFFF", "101010", 10, "\\1a&HB0&")
        elif nombre == "destello":
            dib(destello(r), col or "FFD23F", "FFFFFF", 0)
        else:
            dib(estrella(r), col or "FFD23F", "101010", 4)
        return ev

    def _tramos_escena(self, a_abs, b_abs, minimo=1.5, ultimo_item=None):
        """Divide [a_abs, b_abs] en tramos por los cortes de escena (para elementos largos que cruzan cortes).
        Un tramo de menos de `minimo` s se une al anterior; si el último corte cae a menos de `minimo` s del final,
        el elemento termina en ese corte (así no queda encima de la escena nueva). Devuelve (tramos, b_abs)."""
        ultimo_item = a_abs if ultimo_item is None else ultimo_item
        cortes = []
        try:
            cortes = sorted(float(r["t0"]) for r in self.pr.escenas() if a_abs + 0.2 < float(r["t0"]) < b_abs - 0.2)
        except Exception:
            return [(a_abs, b_abs)], b_abs
        if cortes and b_abs - cortes[-1] < minimo and cortes[-1] > ultimo_item + 0.5:
            b_abs = cortes.pop()
        bordes = [a_abs] + cortes + [b_abs]
        tramos = []
        for p, q in zip(bordes, bordes[1:]):
            if tramos and q - p < minimo:
                tramos[-1] = (tramos[-1][0], q)
            else:
                tramos.append((p, q))
        if len(tramos) > 1 and tramos[0][1] - tramos[0][0] < minimo:     # primer tramo muy corto: se une al siguiente
            tramos[1] = (tramos[0][0], tramos[1][1])
            tramos.pop(0)
        return tramos, b_abs

    def lista(self, d, t0):
        """Tarjeta de papel que se va escribiendo item por item. Si la tarjeta cruza cortes de escena (cada item con su
        imagen), su lugar se revisa en cada corte como el contador: se queda si no tapa caras ni texto de la imagen, se
        mueve con el corte si tapa, y si en una escena no hay lugar libre se oculta en esa escena antes que tapar. Vale
        también para una tarjeta de una sola escena: si no hay lugar libre, no se muestra (queda anotado «lista oculta»)."""
        a = self._t(d["en"]) - t0
        items = [i if isinstance(i, dict) else {"texto": i} for i in d.get("items") or []]
        if not items:
            return []
        cada = float(d.get("cada", 0.9))
        tiempos = []
        for k, it in enumerate(items):
            tiempos.append(self._t(it["frase"], a + t0 - 0.5) - t0 if "frase" in it else a + 0.4 + k * cada)
        b = max(tiempos) + float(d.get("dura", 2.5))
        s = self.esc
        ancho = round((0.56 if self.vertical else 0.34) * self.W)
        alto = round((110 + 62 * len(items)) * s)
        giro = d.get("giro", -3)
        def caja_recta(x, y):       # la tarjeta sin girar: su esquina (x0, y0) es donde se dibuja
            if self.vertical and self.mapa is not None:      # 0.15, Short con mapa: se mide la misma caja que se dibuja
                x0 = int(min(max(x - ancho // 2, 0.05 * self.W), 0.84 * self.W - ancho))
                y0 = int(min(max(y - alto // 2, 0.14 * self.H), 0.78 * self.H - alto))
                return (x0, y0, x0 + ancho, y0 + alto)
            x0 = int(min(max(x - ancho // 2, 0.03 * self.W), 0.97 * self.W - ancho))
            y0 = int(min(max(y - alto // 2, 0.04 * self.H), 0.74 * self.H - alto))
            return (x0, y0, x0 + ancho, y0 + alto)
        def caja_lista(x, y):       # 0.15: lo que la tarjeta ocupa de verdad: va girada (\frz) sobre su esquina
            return caja_girada(caja_recta(x, y), giro)
        cands = [(round(fx * self.W), round(fy * self.H)) for fy in (0.20, 0.32, 0.44, 0.56) for fx in (0.18, 0.34, 0.50, 0.66, 0.82)]
        defecto = "derecha" if not self.vertical else "centro"
        if self.mapa is None or self.vertical or d.get("fijo"):
            tramos = [(t0 + a, t0 + b)]
        else:
            tramos, b_abs = self._tramos_escena(t0 + a, t0 + b, ultimo_item=t0 + max(tiempos))
            b = b_abs - t0
        lugares = []                       # (desde, hasta, (x0, y0) o None si en ese tramo se oculta), en segundos absolutos
        if self.mapa is None or self.vertical or d.get("fijo"):
            x, y = self._lugar(d, defecto, t0 + a, t0 + b, caja_lista, cands)
            if self.vertical:   # dentro de la zona segura: sin tocar la columna de botones de la derecha
                x0 = int(min(max(x - ancho // 2, 0.05 * self.W), 0.84 * self.W - ancho))
                y0 = int(min(max(y - alto // 2, 0.14 * self.H), 0.78 * self.H - alto))
            else:
                x0, y0 = caja_recta(x, y)[:2]
            if self._oculto(d, t0 + a, t0 + b, caja_girada((x0, y0, x0 + ancho, y0 + alto), giro)):
                return []
            lugares.append((t0 + a, t0 + b, (x0, y0)))
        else:
            import caras
            pedido = None
            for p, q in tramos:
                m = max(3, min(8, int(q - p) + 1))
                reg_t = self._regiones(p, q, m)
                antes_mov = len(self.movidos)
                x, y = self._lugar(d, defecto, p, q, caja_lista, cands, muestras=m, pos=pedido)
                if caras.tapa(caja_lista(x, y), reg_t) >= 1:
                    # el mejor lugar «por costo» todavía tapa: antes de ocultar, probar cualquier candidato que no tape
                    # (ni el contador), el más cercano al lugar pedido
                    occ = [o for oa, ob, o in self.ocupado if oa < q and ob > p]
                    libres = [c_ for c_ in cands if caras.tapa(caja_lista(*c_), reg_t) < 1
                              and not any(caras.cruce(caja_lista(*c_), o) for o in occ)]
                    if libres:
                        x, y = min(libres, key=lambda c_: math.hypot(c_[0] - x, c_[1] - y))
                        del self.movidos[antes_mov:]
                        self.movidos.append((round(p, 1), d.get("tipo"), pedido or self._pos(d.get("pos"), defecto), (x, y), 0,
                                             round(caras.tapa(caja_lista(x, y), reg_t), 2)))
                # ningún lugar libre de caras ni de texto de la imagen en esta escena (aunque sea la única): se oculta
                if caras.tapa(caja_lista(x, y), reg_t) >= 1:
                    del self.movidos[antes_mov:]
                    self.movidos.append((round(p, 1), "lista oculta", (x, y), None, 0, 0.0))
                    lugares.append((p, q, None))
                    continue
                pedido = (x, y)
                lugares.append((p, q, caja_recta(x, y)[:2]))
            # lo que se pierde por ocultar queda anotado con «ahora 1.0» para que terminado.py pida revisarlo a mano
            visibles = [(p, q) for p, q, pos in lugares if pos is not None]
            if not visibles:
                self.movidos.append((round(t0 + a, 1), "lista_entera_oculta", None, None, 0, 1.0))
            else:
                for it, t in zip(items, tiempos):
                    if not any(q > t + t0 for p, q in visibles):      # ni en su escena ni en una posterior
                        self.movidos.append((round(t + t0, 1), "item_sin_mostrar", None, None, 0, 1.0))
        giro = d.get("giro", -3)
        color = c(d.get("color", "FFFDF5"))
        ev = []
        for n, (p, q, pos) in enumerate(lugares):
            if pos is None:
                continue
            x0, y0 = pos
            A, B = p - t0, q - t0
            if B <= A + 0.1:
                continue
            ant = lugares[n - 1][2] if n else None
            sig = lugares[n + 1][2] if n + 1 < len(lugares) else None
            fi = 200 if (n == 0 or ant is None) else 0       # entra con fundido al empezar o al volver; en los cortes salta con la imagen
            fo = 250 if (sig is None) else 0
            fad = f"\\fad({fi},{fo})"
            ev += [f"Dialogue: 2,{ts(A)},{ts(B)},VivoDibujo,,0,0,0,,{{\\an7\\pos({x0 + 8},{y0 + 10})\\frz{giro}\\1c{c('000000')}\\1a&HA0&\\bord0{fad}\\p1}}{rect(ancho, alto, 18)}{{\\p0}}",
                   f"Dialogue: 3,{ts(A)},{ts(B)},VivoDibujo,,0,0,0,,{{\\an7\\pos({x0},{y0})\\frz{giro}\\1c{color}\\3c{c('E0D6C2')}\\bord2{fad}\\p1}}{rect(ancho, alto, 18)}{{\\p0}}"]
            if d.get("titulo"):
                ev.append(f"Dialogue: 4,{ts(A)},{ts(B)},VivoMano,,0,0,0,,{{\\an7\\pos({x0 + round(30 * s)},{y0 + round(22 * s)})\\frz{giro}\\fs{round(52 * s)}\\c{c('C23B3B')}{fad}}}{limpio(d['titulo'])}")
            for k, (it, t) in enumerate(zip(items, tiempos)):
                if t >= B or ts(max(t, A)) == ts(B):     # no cabe en este tramo (o quedaría con duración cero al redondear)
                    continue
                yy = y0 + round((92 + 62 * k) * s)
                if t >= A:      # el item aparece en esta escena: se escribe
                    ev.append(f"Dialogue: 4,{ts(t)},{ts(B)},VivoMano,,0,0,0,,{{\\an7\\pos({x0 + round(36 * s)},{yy})\\frz{giro}\\fad(180,{fo})"
                              f"\\clip({x0},{yy - 10},{x0 + 20},{yy + 80})\\t(0,500,\\clip({x0},{yy - 10},{x0 + ancho},{yy + 80}))}}• {limpio(it['texto'])}")
                else:           # ya estaba escrito: sigue en la tarjeta, en su nuevo lugar
                    ev.append(f"Dialogue: 4,{ts(A)},{ts(B)},VivoMano,,0,0,0,,{{\\an7\\pos({x0 + round(36 * s)},{yy})\\frz{giro}{fad}}}• {limpio(it['texto'])}")
        return ev

    def fichas(self, d, t0):
        """Fichas que aparecen en cadena: A → B → C."""
        items = d["items"]
        a = self._t(d["en"]) - t0
        cada = float(d.get("cada", 0.6))
        tiempos = ([self._t(f, a + t0 - 0.5) - t0 for f in d["frases"]] if d.get("frases")
                   else [a + k * cada for k in range(len(items))])
        b = max(tiempos) + float(d.get("dura", 2.5))
        s, ev = self.esc, []
        fs = round(40 * s)
        anchos = [round((len(t) * 0.62 * 40 + 60) * s) for t in items]
        alto = round(70 * s)
        sep = round(70 * s)
        total_h = sum(anchos) + (len(items) - 1) * sep
        caja_f = lambda x, y: (self.W // 2 - total_h // 2, y - alto // 2, self.W // 2 + total_h // 2, y + alto // 2)
        cands = [(self.W // 2, round(fy * self.H)) for fy in (0.08, 0.16, 0.26, 0.38, 0.50, 0.62, 0.72)]
        if self.vertical and self.mapa is not None:      # 0.15, Short con mapa: en vertical las fichas van en columna
            col_w, col_h = max(anchos), len(items) * alto + (len(items) - 1) * sep
            caja_f = lambda x, y: (round(self.W * 0.46) - col_w // 2, y - col_h // 2, round(self.W * 0.46) + col_w // 2, y + col_h // 2)
            cands = [(self.W // 2, round(fy * self.H)) for fy in (0.38, 0.46, 0.54, 0.62)]
        cy = self._lugar(d, "centro", t0 + a, t0 + b, caja_f, cands)[1]
        if self._oculto(d, t0 + a, t0 + b, caja_f(self.W // 2, cy)):
            return []
        if self.vertical:   # en columna
            total = len(items) * alto + (len(items) - 1) * sep
            ys = [cy - total // 2 + k * (alto + sep) for k in range(len(items))]
            xs = [round(self.W * 0.46) - w // 2 for w in anchos]
        else:
            total = sum(anchos) + (len(items) - 1) * sep
            xs, acc = [], self.W // 2 - total // 2
            for w in anchos:
                xs.append(acc); acc += w + sep
            ys = [cy - alto // 2] * len(items)
        for k, (txt, t) in enumerate(zip(items, tiempos)):
            color = d.get("colores", PALETA)[k % len(PALETA)]
            oscuro = color.upper() in ("FFFFFF", "FFD23F", "6AD15B", "4FC3F7")
            ev.append(f"Dialogue: 3,{ts(t)},{ts(b)},VivoDibujo,,0,0,0,,{{\\an7\\pos({xs[k]},{ys[k]})\\1c{c(color)}\\3c{c('101010')}\\bord{round(3 * s)}"
                      f"\\shad{round(4 * s)}\\fad(150,250)\\p1}}{rect(anchos[k], alto, alto // 2)}{{\\p0}}")
            ev.append(f"Dialogue: 4,{ts(t)},{ts(b)},VivoFicha,,0,0,0,,{{\\an5\\pos({xs[k] + anchos[k] // 2},{ys[k] + alto // 2})\\fs{fs}"
                      f"\\c{c('101010' if oscuro else 'FFFFFF')}\\fad(150,250)}}{limpio(txt)}")
            if k:
                if self.vertical:
                    ax, ay, giro = round(self.W * 0.46), ys[k] - sep // 2, 90
                else:
                    ax, ay, giro = xs[k] - sep // 2, ys[k] + alto // 2, 0
                ev.append(f"Dialogue: 3,{ts(t - 0.15)},{ts(b)},VivoDibujo,,0,0,0,,{{\\an5\\pos({ax},{ay})\\frz{-giro}\\1c{c('FFFFFF')}\\3c{c('101010')}"
                          f"\\bord{round(2 * s)}\\fad(150,250)\\p1}}{flecha(round(22 * s))}{{\\p0}}")
        return ev

    def lluvia(self, d, t0):
        a = self._t(d["en"]) - t0
        dura = float(d.get("dura", 2.5))
        n = int(d.get("cantidad", 26))
        s, ev = self.esc, []
        simbolo = d.get("simbolo", "billetes")
        for k in range(n):
            x = self.rand.randint(0, self.W)
            dx = self.rand.randint(-120, 120)
            ini = a + self.rand.uniform(0, dura * 0.5)
            fin = ini + self.rand.uniform(1.2, 2.2)
            giro = self.rand.randint(-200, 200)
            if simbolo == "confeti":
                color = PALETA[k % len(PALETA)]
                forma = rect(round(18 * s), round(30 * s))
            else:
                color = "3FA34D"
                forma = rect(round(120 * s), round(58 * s), round(6 * s))
            ev.append(f"Dialogue: 8,{ts(ini)},{ts(fin)},VivoDibujo,,0,0,0,,{{\\an5\\move({x},{-80},{x + dx},{self.H + 80})\\1c{c(color)}\\3c{c('1E5E2B')}"
                      f"\\bord{round(2 * s)}\\t(\\frz{giro})\\p1}}{forma}{{\\p0}}")
            if simbolo != "confeti":
                ev.append(f"Dialogue: 9,{ts(ini)},{ts(fin)},VivoFicha,,0,0,0,,{{\\an5\\move({x},{-80},{x + dx},{self.H + 80})\\fs{round(40 * s)}"
                          f"\\c{c('DFF5D8')}\\t(\\frz{giro})}}$")
        return ev

    def texto(self, d, t0):
        """Texto grande con cualquiera de las 20 entradas (ver TODAS): pop, fundido, subir, base, bajar, panear, patinar,
        deriva, voltereta, rebote, pisoton, tectonico, album, neon, respirar, maquina, estallido, rodar, ascender, bloque
        (más desliza, sello y brillo)."""
        a = self._t(d["en"]) - t0
        b = a + float(d.get("dura", 1.6))
        tam, bord = round(d.get("tam", 150) * self.esc), round(10 * self.esc)
        txt = limpio(d["texto"])
        mw, mh = len(txt) * tam * 0.31 + bord, tam * 0.6 + bord
        x, y = self._lugar(d, "centro", t0 + a, t0 + b, lambda x, y: (x - mw, y - mh, x + mw, y + mh))
        if self._oculto(d, t0 + a, t0 + b, (x - mw, y - mh, x + mw, y + mh)):
            return []
        color = d.get("color", self.e["clave"])
        estilo = f"\\fs{tam}\\c{c(color)}\\bord{bord}"
        n = nombre_animacion(d.get("entrada", "pop"))
        linea = lambda ini, fin, tags, texto: f"Dialogue: 6,{ts(ini)},{ts(fin)},Vivo,,0,0,0,,{{\\an5{tags}{estilo}}}{texto}"
        if n in POR_LETRA:
            return [linea(a, b, f"\\pos({x},{y})\\fad(0,250)", texto_por_letra(n, txt))]
        if n == "tectonico":          # sacudida: izquierda, derecha, izquierda, al centro
            pasos, out, t = [(-40, 40), (40, -30), (-30, 15), (15, 0)], [], a
            for dx0, dx1 in pasos:
                out.append(linea(t, t + 0.09, f"\\move({x + round(dx0 * self.esc)},{y},{x + round(dx1 * self.esc)},{y})", txt))
                t += 0.09
            out.append(linea(t, b, f"\\pos({x},{y})\\fad(0,250)", txt))
            return out
        if n == "bloque":             # un bloque de color cruza y al irse deja el texto
            ancho = round(len(txt) * tam * 0.62) + round(30 * self.esc)
            x0, x1 = x - ancho // 2, x + ancho // 2
            rect_h = round(tam * 1.1)
            barra = lambda ini, fin, an, tags: (f"Dialogue: 7,{ts(ini)},{ts(fin)},VivoDibujo,,0,0,0,,{{\\{an}{tags}\\1c{c(color)}\\bord0"
                                                f"\\p1}}{rect(ancho, rect_h)}{{\\p0}}")
            return [barra(a, a + 0.25, "an4", f"\\pos({x0},{y})\\fscx0\\t(0,250,\\fscx100)"),
                    barra(a + 0.25, a + 0.5, "an6", f"\\pos({x1},{y})\\t(0,250,\\fscx0)"),
                    linea(a + 0.25, b, f"\\pos({x},{y})\\fad(0,250)", txt)]
        tags = entrada_linea(n, x, y, tam, self.W, self.H, int((b - a) * 1000))
        tags = re.sub(r"\\fad\((\d+),0\)", r"\\fad(\1,250)", tags) if "\\fad(" in tags else tags + "\\fad(0,250)"
        return [linea(a, b, tags, txt)]

    def _fin_progreso(self, d, a):
        if "hasta" in d:
            return self._t(d["hasta"], a) - float(d.get("antes", 0.3))   # se va un poco antes del bloque siguiente
        return a + float(d.get("dura", 8))

    def progreso(self, d, t0, t1=1e9):
        """Contador «N DE M» fijo en una esquina durante un bloque (ej. CREENCIA 2 DE 4), con puntos de avance.
        {"tipo": "progreso", "en": <frase o segundo>, "hasta": <frase siguiente>, "actual": 2, "total": 4,
         "etiqueta": "CREENCIA", "tarjeta": false, "pos": [0.87, 0.09], "pos_vertical": [0.30, 0.31]}. Con "tarjeta": true,
        al empezar muestra 1,2 s el número grande al centro (encima del video, sin agregar tiempo). Evita caras y texto de
        la imagen; queda en la misma esquina que el contador anterior si ahí no tapa nada; los demás elementos lo evitan."""
        actual, total = int(d.get("actual", 1)), int(d.get("total", 1))
        if not (1 <= actual <= total):
            raise ValueError(f"progreso: actual {actual} fuera de 1..{total}")
        a_abs = self._t(d["en"])
        b_abs = self._fin_progreso(d, a_abs)
        if b_abs <= a_abs + 0.3:
            raise ValueError(f"progreso {actual}/{total}: termina antes de empezar (revisa 'hasta')")
        if b_abs <= t0 or a_abs >= t1:
            return []
        s, ev = self.esc, []
        fin_tramo = min(b_abs, t1) - t0
        txt = f"{limpio(d.get('etiqueta', 'PASO')).upper()} {actual} DE {total}"
        clave = c(d.get("color", self.e["clave"]))
        if d.get("tarjeta") and a_abs >= t0:      # número grande al centro, 1,2 s, con velo oscuro detrás
            ta, tb = a_abs - t0, min(a_abs - t0 + 1.2, fin_tramo)
            if tb > ta + 0.2:
                ev.append(f"Dialogue: 8,{ts(ta)},{ts(tb)},VivoDibujo,,0,0,0,,{{\\an7\\pos(0,0)\\1c{c('000000')}\\1a&H60&\\bord0\\fad(150,200)\\p1}}{rect(self.W, self.H)}{{\\p0}}")
                ev.append(f"Dialogue: 9,{ts(ta)},{ts(tb)},Vivo,,0,0,0,,{{\\an5\\pos({self.W // 2},{self.H // 2})\\fs{round((90 if self.vertical else 120) * s)}\\c{clave}\\bord{round(8 * s)}"
                          f"{self._pop(1200)}}}{txt}")
            a_abs += 1.2
        tam = round(float(d.get("tam", 40)) * s)
        pad, sep = round(18 * s), round(10 * s)
        ancho = round(len(txt) * tam * 0.70) + 2 * pad
        punto = min(round(14 * s), max(4, (ancho - 2 * pad - (total - 1) * sep) // total))
        if total * punto + (total - 1) * sep > ancho - 2 * pad:
            sep = max(2, (ancho - 2 * pad - total * punto) // max(1, total - 1))
        alto = tam + punto + 3 * pad // 2 + round(6 * s)
        defecto = d.get("pos_vertical", [0.30, 0.31]) if self.vertical else d.get("pos", [0.87, 0.09])
        caja = lambda x, y: (x - ancho // 2, y - alto // 2, x + ancho // 2, y + alto // 2)
        if self.vertical:          # debajo del título del Short y fuera de la columna de botones
            cands = [(round(0.30 * self.W), round(0.31 * self.H)), (round(0.30 * self.W), round(0.62 * self.H))]
        else:
            cands = [(round(fx * self.W), round(fy * self.H)) for fy in (0.09, 0.20, 0.62) for fx in (0.13, 0.87)]
        pedido = (round(defecto[0] * self.W), round(defecto[1] * self.H))
        if self._pos_progreso and "pos" not in d and not self.vertical:
            pedido = self._pos_progreso                 # misma esquina que el contador anterior: el video se ve ordenado
        # el lugar se revisa en cada cambio de escena: se queda si no tapa nada y solo se mueve en un corte
        bordes = [a_abs, b_abs]
        try:
            bordes += [float(r["t0"]) for r in self.pr.escenas() if a_abs + 1.5 < float(r["t0"]) < b_abs - 1.5]
        except Exception:
            pass
        bordes = sorted(set(bordes))
        tramos = []
        for p, q in zip(bordes, bordes[1:]):
            if tramos and q - p < 1.5:                  # escenas muy cortas: siguen con el lugar del tramo anterior
                tramos[-1] = (tramos[-1][0], q)
            else:
                tramos.append((p, q))
        import caras
        ajustar = lambda x, y: (min(max(x, ancho // 2 + round(0.02 * self.W)), self.W - ancho // 2 - round(0.02 * self.W)),
                                min(max(y, alto // 2 + round(0.02 * self.H)), round(0.78 * self.H) - alto // 2))
        cands = [ajustar(*q) for q in cands]
        pedido = ajustar(*pedido)
        lugares = []
        for p, q in tramos:
            m = max(3, min(8, int(q - p)))
            reg_t = self._regiones(p, q, m)
            tapa = lambda pos: caras.tapa(caja(*pos), reg_t)
            if tapa(pedido) < 0.3:
                x, y = pedido                     # se queda: solo tapar una cara o un texto de la imagen obliga a moverlo (rozarlos no)
            else:
                antes_mov = len(self.movidos)
                x, y = ajustar(*self._lugar(d, "arriba-der", p, q, caja, cands, muestras=m, pos=pedido))
                if tapa((x, y)) >= 1:             # ningún lugar libre de caras en este tramo: se oculta antes que tapar
                    del self.movidos[antes_mov:]  # oculto no tapa nada: no queda anotado para revisar
                    lugares.append((p, q, None))
                    continue
            if lugares and lugares[-1][2] == (x, y):
                lugares[-1] = (lugares[-1][0], q, (x, y))
            else:
                lugares.append((p, q, (x, y)))
            pedido = (x, y)
            self.ocupado.append((p, q, caja(x, y)))
        visibles = [l for l in lugares if l[2] is not None]
        if not visibles:
            return ev
        lugares = visibles
        if not self.vertical:
            self._pos_progreso = lugares[-1][2]
        total_w = total * punto + (total - 1) * sep
        for n, (p, q, (x, y)) in enumerate(lugares):
            A, B = max(p, t0) - t0, min(q, t1) - t0
            if B <= A + 0.2:
                continue
            antes = lugares[n - 1][1] if n else None
            despues = lugares[n + 1][0] if n + 1 < len(lugares) else None
            fi = 250 if ((n == 0 and p >= t0) or (antes is not None and p - antes > 0.05)) else 0   # entra con fundido al empezar o al volver
            fo = 250 if (despues is None or despues - q > 0.05) else 0     # y se va con fundido al terminar u ocultarse; en los cortes salta con la imagen
            fad = f"\\fad({fi},{fo})"
            x0, y0 = x - ancho // 2, y - alto // 2
            ev.append(f"Dialogue: 5,{ts(A)},{ts(B)},VivoDibujo,,0,0,0,,{{\\an7\\pos({x0},{y0})\\1c{c('101010')}\\1a&H30&\\3c{clave}\\bord{max(2, round(3 * s))}{fad}\\p1}}{rect(ancho, alto, round(alto * 0.28))}{{\\p0}}")
            ev.append(f"Dialogue: 6,{ts(A)},{ts(B)},Vivo,,0,0,0,,{{\\an8\\pos({x},{y0 + pad // 2})\\fs{tam}\\c{c('FFFFFF')}\\bord0\\shad0{fad}}}{txt}")
            px0, py = x - total_w // 2, y0 + pad // 2 + tam + round(8 * s)
            for k in range(total):
                col = clave if k < actual else c("FFFFFF")
                alfa = "\\1a&H00&" if k < actual else "\\1a&HA0&"
                pop = "\\fscx0\\fscy0\\t(250,450,\\fscx130\\fscy130)\\t(450,600,\\fscx100\\fscy100)" if k == actual - 1 and fi else ""
                cx, cy = px0 + k * (punto + sep) + punto // 2, py + punto // 2      # \\an5: el punto crece desde su centro
                ev.append(f"Dialogue: 6,{ts(A)},{ts(B)},VivoDibujo,,0,0,0,,{{\\an5\\pos({cx},{cy})\\1c{col}{alfa}\\bord0{fad}{pop}\\p1}}{circulo(punto / 2)}{{\\p0}}")
        return ev

    def linea_de_tiempo(self):
        """Tiempos de cada elemento (para la sala de edición): inicio, fin y momentos de sus partes."""
        out = []
        for k, d in enumerate(self.pr.cfg.get("elementos", [])):
            try:
                a = self._t(d["en"])
            except (ValueError, KeyError) as ex:
                out.append({"n": k, "tipo": d.get("tipo"), "error": str(ex), "datos": d})
                continue
            partes = []
            tipo = d.get("tipo")
            if tipo == "lista":
                cada = float(d.get("cada", 0.9))
                for j, it in enumerate(d.get("items", [])):
                    it = it if isinstance(it, dict) else {"texto": it}
                    try:
                        partes.append(self._t(it["frase"], a - 0.5) if "frase" in it else a + 0.4 + j * cada)
                    except ValueError:
                        partes.append(a + 0.4 + j * cada)
                b = max(partes or [a]) + float(d.get("dura", 2.5))
            elif tipo == "fichas":
                cada = float(d.get("cada", 0.6))
                try:
                    partes = [self._t(f, a - 0.5) for f in d["frases"]] if d.get("frases") else [a + j * cada for j in range(len(d["items"]))]
                except ValueError:
                    partes = [a + j * cada for j in range(len(d["items"]))]
                b = max(partes) + float(d.get("dura", 2.5))
            elif tipo == "progreso":
                try:
                    b = self._fin_progreso(d, a)
                except ValueError as ex:          # igual que en el render: sin 'hasta' no se dibuja
                    out.append({"n": k, "tipo": tipo, "error": str(ex), "datos": d})
                    continue
            else:
                b = a + float(d.get("dura", {"lluvia": 2.5, "texto": 1.6}.get(tipo, 2.0)))
            out.append({"n": k, "tipo": tipo, "a": round(a, 3), "b": round(b, 3), "partes": [round(x, 3) for x in partes],
                        "pos": list(self._pos(d.get("pos", [0.87, 0.09] if tipo == "progreso" else None), "derecha" if tipo == "lista" and not self.vertical else "centro")), "datos": d})
        return out

    def elementos(self, t0=0.0, t1=1e9):
        out = []
        self.ocupado, self._pos_progreso = [], None
        todos = self.pr.cfg.get("elementos", [])
        for d in [e for e in todos if e.get("tipo") == "progreso"] + [e for e in todos if e.get("tipo") != "progreso"]:
            try:
                t = self._t(d["en"])
            except ValueError as ex:
                print("AVISO elemento sin frase:", ex)
                continue
            if d.get("tipo") == "progreso":     # dura todo un bloque: entra si se cruza con el tramo (también en un Short)
                try:
                    out += self.progreso(d, t0, t1)
                except ValueError as ex:
                    print("AVISO progreso:", ex)
                continue
            if not (t0 - 0.5 <= t <= t1):
                continue
            fn = {"icono": self.icono, "lista": self.lista, "fichas": self.fichas, "lluvia": self.lluvia, "texto": self.texto}.get(d.get("tipo"))
            if fn:
                out += [l for l in fn(d, t0) if not l.split(",")[1].startswith("-")]
        return out


def activo(pr):
    return pr.cfg.get("subtitulos", {}).get("estilo") == "vivo" or bool(pr.cfg.get("elementos"))


def cues_sonido(pr, pals):
    """(0.15) Sonidos que acompañan a la capa viva; apagado si no se pide. Devuelve [(segundo, nombre, volumen o None,
    etiqueta)] para que sonidos.py los mezcle bajo la voz (este archivo no toca audio).
      "subtitulos": {"sonido": "pop", "sonido_volumen": -14, "sonido_en": "claves" | "grupos", "sonido_cada": 1.5,
                     "sonido_max_por_min": 12}   un sonido corto en las palabras clave (o al entrar cada grupo)
      en un elemento: "sonido": "pop" (y "sonido_volumen" opcional)   suena cuando el elemento entra
    nombre: uno de SONIDOS (pop, clic, tic, suave, campana, golpe, cambio) o un archivo del banco de sonidos."""
    sub = pr.cfg.get("subtitulos", {})
    elementos = [d for d in pr.cfg.get("elementos", []) if d.get("sonido")]
    if not sub.get("sonido") and not elementos:
        return []
    W, H = getattr(pr, "ancho", 1920), getattr(pr, "alto", 1080)
    v = Vivo(pr, pals, W, H, vertical=H > W)
    out = []
    if sub.get("sonido"):
        cada, tope = float(sub.get("sonido_cada", 1.5)), int(sub.get("sonido_max_por_min", 12))
        por_grupo = sub.get("sonido_en", "claves") == "grupos"
        puestos = []
        for g in v._grupos(0.0, 1e9):
            i = g[0] if por_grupo else next((j for j in g if v._es_clave(j)), None)
            if i is None:
                continue
            t = pals[i]["start"]
            if (puestos and t - puestos[-1] < cada) or sum(1 for u in puestos if t - u < 60) >= tope:
                continue                               # con medida: nunca un sonido encima de otro ni una lluvia de pops
            puestos.append(t)
            out.append((t, sub["sonido"], sub.get("sonido_volumen"), f"subtítulo «{limpio(pals[i]['word'])}»"))
    for d in elementos:
        try:
            t = v._t(d["en"])
        except (ValueError, KeyError) as ex:
            print("AVISO sonido de elemento sin momento:", ex, flush=True)
            continue
        out.append((t, d["sonido"], d.get("sonido_volumen", sub.get("sonido_volumen")), f"elemento {d.get('tipo', '')}"))
    return sorted(out, key=lambda x: x[0])


def insertar(cabecera, estilos):
    """Agrega los estilos vivos a una cabecera ASS existente (antes de [Events])."""
    return cabecera.replace("\n[Events]", "\n" + "\n".join(estilos) + "\n\n[Events]", 1)


def zona_segura(W, H, t1):
    """Franjas rojas donde TikTok/Reels/Shorts ponen su interfaz (solo para revisar, nunca en el final)."""
    cajas = [(0, 0, W, 0.12 * H), (0, 0.80 * H, W, H), (0.86 * W, 0.38 * H, W, 0.80 * H)]
    return [f"Dialogue: 20,{ts(0)},{ts(t1)},VivoDibujo,,0,0,0,,{{\\an7\\pos({round(x0)},{round(y0)})\\1c&H3030FF&\\1a&HA0&\\bord0\\shad0\\p1}}"
            f"{rect(round(x1 - x0), round(y1 - y0))}{{\\p0}}" for x0, y0, x1, y1 in cajas]


CAB_PRUEBA = """[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def prueba():
    """python vivo.py "<proyecto>" --prueba 0-40 [--vertical] [--zona] [--fotos 3,10,20]
    Video corto con la capa viva sobre el armado (tmp/solo_video.mp4) o, si todavía no hay imágenes, sobre un fondo neutro."""
    import sys
    from estudio import Proyecto, FFMPEG, run, palabras
    pr = Proyecto()
    arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    a, b = (float(x) for x in arg("--prueba", "0-30").split("-"))
    vertical = "--vertical" in sys.argv
    W, H = (1080, 1920) if vertical else (pr.ancho, pr.alto)
    _, pals = palabras(pr)
    v = Vivo(pr, pals, W, H, vertical=vertical)
    lineas = v.subtitulos(a, b) + v.elementos(a, b)
    if "--zona" in sys.argv:
        lineas += zona_segura(W, H, b - a)
    sufijo = "-9x16" if vertical else ""
    ass = pr.tmp / f"vivo_prueba{sufijo}.ass"
    ass.write_text(insertar(CAB_PRUEBA.format(W=W, H=H), v.estilos()) + "\n".join(lineas) + "\n", encoding="utf-8-sig")
    solo = pr.tmp / "solo_video.mp4"
    dur = b - a
    if solo.exists():
        fondo = ["-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", str(solo)]
        vf = (f"[0:v]scale=-2:{H},crop={W}:{H}," if vertical else "[0:v]") + f"ass={ass.name}[v]"
    else:
        fondo = ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"color=c=0x22313f:s={W}x{H}:r={pr.fps}"]
        vf = f"[0:v]vignette=PI/4,noise=alls=6:allf=t,ass={ass.name}[v]"
    nombre = f"{pr.base_nombre}_vivo-prueba{sufijo}.mp4"
    run([FFMPEG, "-v", "error", "-y", *fondo, "-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", str(pr.audios()[0]),
         "-filter_complex", vf, "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", *SIN_METADATOS, "-movflags", "+faststart", f"../{nombre}"], cwd=pr.tmp)
    print("LISTO", pr.salida / nombre, f"({len(lineas)} eventos)", flush=True)
    for t in [float(x) for x in (arg("--fotos") or "").split(",") if x]:
        run([FFMPEG, "-v", "error", "-y", "-ss", f"{t - a:.3f}", "-i", str(pr.salida / nombre), "-frames:v", "1", "-q:v", "3", *SIN_METADATOS,
             str(pr.tmp / f"vivo{sufijo}_{t:.1f}s.jpg")])
    if arg("--fotos"):
        print("FOTOS en", pr.tmp, flush=True)


if __name__ == "__main__":
    prueba()
