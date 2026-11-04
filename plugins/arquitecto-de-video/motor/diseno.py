# Diseño local (funciones tipo Canva hechas con código propio, sin usar nada de Canva):
# kit de marca del canal, plantillas con campos (autofill local), efectos de texto (contorno, sombra, neón,
# degradado, curva, caja), imágenes con máscara (círculo, redondeado) y marco, formas y flechas,
# redimensionado inteligente a 16:9, 9:16, 1:1 y 4:5, y quitar fondo (opcional, con rembg y un modelo de uso comercial).
#
#   python diseno.py plantilla "<plantilla.json>" --datos "<datos.json>" [--campo titulo="NO INVIERTAS"] [--salida out.png] [--formatos 16x9,9x16]
#   python diseno.py redimensionar "<imagen>" [--formatos 16x9,9x16,1x1,4x5] [--modo inteligente|relleno] [--salida carpeta]
#   python diseno.py marca "<canal>"                      muestra el kit de marca del canal (y crea uno base si no existe)
#
# Kit de marca: %USERPROFILE%\EstudioPaltostaila\canales\<canal>\marca.json (colores, fuentes, logo). Las plantillas
# nombran colores y fuentes por su papel ("acento", "titulo"), así un mismo diseño sirve para cualquier canal.
# Prohibido: copiar plantillas, kits o diseños de Canva a este motor (términos de Canva y de su conector).
import json, math, os, re, sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

ESTUDIO = Path.home() / "EstudioPaltostaila"
FUENTES_SISTEMA = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts", Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
                   Path("/usr/share/fonts/truetype/dejavu"), Path("/System/Library/Fonts/Supplemental")]
MARCA_BASE = {"colores": {"texto": "#FFFFFF", "acento": "#FFD23F", "acento2": "#6AD15B", "borde": "#0A162D", "fondo": "#22313F", "alerta": "#FF5E5E"},
              "fuentes": {"titulo": "ariblk.ttf", "texto": "arialbd.ttf", "mano": "Inkfree.ttf"},
              "logo": "", "sello": ""}
FORMATOS = {"16x9": (1280, 720), "9x16": (1080, 1920), "1x1": (1080, 1080), "4x5": (1080, 1350), "yt": (1280, 720)}
RESPALDO_FUENTE = ["ariblk.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Black.ttf"]
REGISTRO = []      # lo que se dibujó en cada texto, para la revisión de legibilidad


def luminancia(rgb):
    def canal(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(c1, c2):
    a, b = sorted((luminancia(c1), luminancia(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


# ---------- marca y fuentes ----------
def marca(canal=None, proyecto=None):
    for p in ([Path(proyecto) / "marca.json"] if proyecto else []) + ([ESTUDIO / "canales" / canal / "marca.json"] if canal else []):
        if p.exists():
            m = json.loads(p.read_text(encoding="utf-8-sig"))
            return {**MARCA_BASE, **m, "colores": {**MARCA_BASE["colores"], **m.get("colores", {})},
                    "fuentes": {**MARCA_BASE["fuentes"], **m.get("fuentes", {})}, "_ruta": str(p.parent)}
    return dict(MARCA_BASE, _ruta="")


def color(c, mk, alfa=255):
    c = mk["colores"].get(c, c) if isinstance(c, str) else c
    if isinstance(c, str):
        h = c.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (alfa,)
    return tuple(c[:3]) + (alfa,)


def fuente(nombre, tam, mk):
    nombre = mk["fuentes"].get(nombre, nombre)
    for n in [nombre] + RESPALDO_FUENTE:
        p = Path(n)
        for cand in ([p] if p.is_absolute() else [Path(mk.get("_ruta") or ".") / n] + [d / n for d in FUENTES_SISTEMA]):
            if cand.exists():
                return ImageFont.truetype(str(cand), int(tam))
    return ImageFont.load_default()


# ---------- imagen: ajustar, máscara, marco, quitar fondo ----------
def energia(im):
    g = im.convert("L").resize((min(320, im.width), max(1, round(min(320, im.width) * im.height / im.width))))
    return g.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(3)), im.width / g.width


def recorte_inteligente(im, W, H):
    """Elige la ventana W:H con más detalle (bordes): el sujeto queda dentro aunque no esté al centro."""
    esc = max(W / im.width, H / im.height)
    im = im.resize((max(W, round(im.width * esc)), max(H, round(im.height * esc))))
    if im.size == (W, H):
        return im
    e, k = energia(im)
    ew, eh = round(W / k), round(H / k)
    px = e.load()
    col = [sum(px[x, y] for y in range(e.height)) for x in range(e.width)]
    fil = [sum(px[x, y] for x in range(e.width)) for y in range(e.height)]
    def mejor(v, n):
        if n >= len(v):
            return 0
        s = sum(v[:n]); best, pos = s, 0
        for i in range(1, len(v) - n + 1):
            s += v[i + n - 1] - v[i - 1]
            if s > best:
                best, pos = s, i
        centro = (len(v) - n) / 2          # empate o casi: preferir el centro
        return pos if best > 1.05 * sum(v[int(centro):int(centro) + n]) else int(centro)
    x0, y0 = round(mejor(col, ew) * k), round(mejor(fil, eh) * k)
    return im.crop((x0, y0, x0 + W, y0 + H))


def con_relleno(im, W, H):
    """La imagen completa sobre una copia desenfocada (no corta nada)."""
    fondo = ImageOps.fit(im, (W, H)).filter(ImageFilter.GaussianBlur(40))
    fondo = Image.blend(fondo, Image.new("RGB", (W, H), (0, 0, 0)), 0.25)
    frente = ImageOps.contain(im, (W, H))
    fondo.paste(frente, ((W - frente.width) // 2, (H - frente.height) // 2))
    return fondo


def quitar_fondo(im):
    try:
        from rembg import new_session, remove
    except ImportError:
        raise SystemExit("Para quitar el fondo en el PC falta rembg (pip install \"rembg[cpu]\", baja un modelo de ~170 MB la "
                         "primera vez; pedir permiso antes). Alternativa: la herramienta remove-background del conector de Canva.")
    # isnet-general-use: licencia de uso comercial. Nunca el modelo por defecto bria-rmbg (CC BY-NC, no comercial).
    return remove(im, session=new_session(os.environ.get("ESTUDIO_REMBG_MODELO", "isnet-general-use")))


def mascara(w, h, forma, radio=40):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    if forma == "circulo":
        d.ellipse([0, 0, w - 1, h - 1], fill=255)
    elif forma == "redondeado":
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radio, fill=255)
    else:
        d.rectangle([0, 0, w, h], fill=255)
    return m


def capa_imagen(lienzo, c, mk, base):
    ruta = Path(c["archivo"]) if Path(c["archivo"]).is_absolute() else Path(base) / c["archivo"]
    im = Image.open(ruta)
    im = ImageOps.exif_transpose(im).convert("RGBA")
    x, y = c.get("x", 0), c.get("y", 0)
    w, h = c.get("w", lienzo.width), c.get("h", lienzo.height)
    if c.get("sin_fondo"):
        im = quitar_fondo(im)
        caja = im.split()[3].point(lambda v: 255 if v > 128 else 0).getbbox()   # solo lo sólido
        if caja:
            im = im.crop(caja)          # solo el sujeto, sin aire transparente alrededor
    ajuste = c.get("ajuste", "cubrir")
    if c.get("sin_fondo") or ajuste == "contener":
        im = ImageOps.contain(im, (w, h))
        x += (w - im.width) // 2
        y += (h - im.height) if c.get("sin_fondo") else (h - im.height) // 2
    elif ajuste == "inteligente":
        im = recorte_inteligente(im.convert("RGB"), w, h).convert("RGBA")
    elif ajuste == "relleno":
        im = con_relleno(im.convert("RGB"), w, h).convert("RGBA")
    else:
        im = ImageOps.fit(im, (w, h))
    if c.get("sombra"):
        alfa = im.split()[3]
        s = Image.new("RGBA", im.size, (0, 0, 0, 0))
        s.putalpha(alfa.point(lambda v: int(v * 0.6)))
        s = s.filter(ImageFilter.GaussianBlur(14))
        lienzo.alpha_composite(s, (x + 14, y + 16))
    forma = c.get("mascara")
    if forma and not c.get("sin_fondo"):
        im.putalpha(ImageChops.multiply(im.split()[3], mascara(im.width, im.height, forma, c.get("radio", 40))))
    lienzo.alpha_composite(im, (x, y))
    if c.get("marco") and not c.get("sin_fondo"):
        g = c["marco"].get("grosor", 8)
        d = ImageDraw.Draw(lienzo)
        caja = [x - g // 2, y - g // 2, x + im.width + g // 2, y + im.height + g // 2]
        col = color(c["marco"].get("color", "acento"), mk)
        if forma == "circulo":
            d.ellipse(caja, outline=col, width=g)
        else:
            d.rounded_rectangle(caja, radius=c.get("radio", 40) if forma == "redondeado" else 0, outline=col, width=g)


# ---------- texto ----------
def partir(texto, f, w, max_lineas, d):
    """Respeta los saltos de línea pedidos y además parte lo que no cabe en el ancho."""
    lineas = []
    for trozo in texto.split("\n"):
        actual = ""
        for p in trozo.split():
            prueba = (actual + " " + p).strip()
            if d.textlength(prueba, font=f) <= w or not actual:
                actual = prueba
            else:
                lineas.append(actual); actual = p
        lineas.append(actual)
    return lineas if len(lineas) <= max_lineas else None


def ajustar_tam(texto, c, mk, d):
    """Tamaño más grande que entra en el ancho y en el máximo de líneas."""
    tam = c.get("tam", 110)
    while tam > 18:
        f = fuente(c.get("fuente", "titulo"), tam, mk)
        lineas = partir(texto, f, c.get("w", 1000), c.get("max_lineas", 3), d)
        if lineas and all(d.textlength(l, font=f) <= c.get("w", 1000) for l in lineas):
            return f, lineas, tam
        tam -= 4
    f = fuente(c.get("fuente", "titulo"), tam, mk)
    return f, partir(texto, f, c.get("w", 1000), 99, d), tam


def capa_texto(lienzo, c, mk, datos):
    texto = re.sub(r"\{\{(\w+)\}\}", lambda m: str(datos.get(m.group(1), "")), c["texto"])
    if c.get("mayusculas", True):
        texto = texto.upper()
    if not texto.strip():
        return
    capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    f, lineas, tam = ajustar_tam(texto, c, mk, d)
    x0, y0, w = c.get("x", 0), c.get("y", 0), c.get("w", 1000)
    alto_l = round(tam * c.get("interlineado", 1.05))
    efecto = c.get("efecto", "contorno")
    col = color(c.get("color", "texto"), mk)
    acento = c.get("color_ultima")          # la última línea en otro color (como las miniaturas del canal)
    borde = color(c.get("borde", "borde"), mk)
    grosor = c.get("grosor", max(4, tam // 9))
    if efecto == "curva":
        curva(capa, lineas[0], f, (x0 + w / 2, y0 + c.get("radio_curva", 600)), c.get("radio_curva", 600), col, borde, grosor)
        lienzo.alpha_composite(capa.rotate(c.get("giro", 0), center=(x0 + w / 2, y0), resample=Image.BICUBIC))
        return
    pos = []
    for i, l in enumerate(lineas):
        lw = d.textlength(l, font=f)
        al = c.get("alinear", "izq")
        x = x0 + (w - lw) / 2 if al == "centro" else (x0 + w - lw if al == "der" else x0)
        pos.append((x, y0 + i * alto_l, l, lw))
    caja = (min(p[0] for p in pos), y0, max(p[0] + p[3] for p in pos), y0 + alto_l * len(pos))
    zona = lienzo.crop(tuple(int(max(0, v)) for v in caja)).convert("RGB")
    fondo_prom = tuple(int(v) for v in zona.resize((1, 1), Image.BOX).getpixel((0, 0))) if zona.width and zona.height else (0, 0, 0)
    REGISTRO.append({"texto": texto, "tam": tam, "lineas": len(pos), "fuente": getattr(f, "path", "?"), "caja": caja,
                     "contraste": round(contraste(col, fondo_prom), 1), "apoyo": efecto in ("contorno", "caja", "sombra", "neon", "empalme", "glitch")})
    if efecto == "caja":
        for x, y, l, lw in pos:
            pad = tam * 0.22
            d.rounded_rectangle([x - pad, y - pad * 0.5, x + lw + pad, y + tam * 1.02 + pad * 0.3], radius=tam * 0.18,
                                fill=color(c.get("fondo", "borde"), mk, c.get("fondo_alfa", 230)))
    if efecto in ("eco", "glitch", "empalme"):     # copias detrás del texto, desplazadas
        ang = math.radians(c.get("direccion", -45))
        dist = c.get("desplazamiento", tam * (0.05 if efecto == "glitch" else 0.08))
        if efecto == "glitch":
            copias = [(-1, color(c.get("color_glitch1", "#00E5FF"), mk)), (1, color(c.get("color_glitch2", "#FF3DA8"), mk))]
        elif efecto == "eco":
            copias = [(2, col[:3] + (70,)), (1, col[:3] + (140,))]
        else:
            copias = [(1, color(c.get("color2", "acento"), mk))]
        for k, tinte in copias:
            for x, y, l, _ in pos:
                d.text((x + k * dist * math.cos(ang), y - k * dist * math.sin(ang)), l, font=f, fill=tinte)
    if efecto == "elevar":                           # sombra suave y difusa justo debajo: el texto "flota"
        sombra = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        ds = ImageDraw.Draw(sombra)
        for x, y, l, _ in pos:
            ds.text((x, y + tam * 0.04), l, font=f, fill=(0, 0, 0, round(255 * c.get("intensidad", 0.55))))
        capa.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(tam * 0.09)))
    if efecto in ("sombra", "neon"):
        glow = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        dg = ImageDraw.Draw(glow)
        tinte = col if efecto == "neon" else (0, 0, 0, 200)
        dx, dy = (0, 0) if efecto == "neon" else (tam * 0.06, tam * 0.08)
        for x, y, l, _ in pos:
            dg.text((x + dx, y + dy), l, font=f, fill=tinte, stroke_width=grosor if efecto == "neon" else 0, stroke_fill=tinte)
        radio = tam * (0.18 if efecto == "neon" else 0.06)
        glow = glow.filter(ImageFilter.GaussianBlur(radio))
        capa.alpha_composite(glow)
        if efecto == "neon":
            capa.alpha_composite(glow)
    for i, (x, y, l, _) in enumerate(pos):
        relleno = color(acento, mk) if acento and i == len(pos) - 1 else col
        if efecto == "neon":
            d.text((x, y), l, font=f, fill=(255, 255, 255, 255), stroke_width=max(2, grosor // 3), stroke_fill=relleno)
        elif efecto in ("hueco", "empalme"):       # solo el contorno: el centro de la letra queda transparente
            hueco = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))     # en su propia capa, para no borrar lo que está detrás
            ImageDraw.Draw(hueco).text((x, y), l, font=f, fill=(0, 0, 0, 0), stroke_width=c.get("grosor", max(3, tam // 18)), stroke_fill=relleno)
            capa.alpha_composite(hueco)
        elif efecto == "degradado":
            d.text((x, y), l, font=f, fill=(0, 0, 0, 0), stroke_width=grosor, stroke_fill=borde)
            m = Image.new("L", lienzo.size, 0)
            ImageDraw.Draw(m).text((x, y), l, font=f, fill=255)
            grad = Image.linear_gradient("L").resize((lienzo.width, round(tam * 1.1)))
            c1, c2 = color(c.get("color", "acento"), mk), color(c.get("color2", "acento2"), mk)
            g = Image.composite(Image.new("RGBA", grad.size, c2), Image.new("RGBA", grad.size, c1), grad)
            full = Image.new("RGBA", lienzo.size, (0, 0, 0, 0)); full.paste(g, (0, int(y)))
            capa.paste(full, (0, 0), m)
        else:
            d.text((x, y), l, font=f, fill=relleno, stroke_width=grosor if efecto in ("contorno", "sombra") else 0, stroke_fill=borde)
    if c.get("giro"):
        capa = capa.rotate(c["giro"], center=(x0 + w / 2, y0 + alto_l * len(pos) / 2), resample=Image.BICUBIC)
    lienzo.alpha_composite(capa)


def curva(capa, texto, f, centro, radio, col, borde, grosor):
    """Texto en arco: letra por letra, cada una girada según su lugar en el círculo."""
    d = ImageDraw.Draw(capa)
    largo = d.textlength(texto, font=f)
    ang = -largo / radio / 2
    for ch in texto:
        cw = d.textlength(ch, font=f)
        a = ang + cw / radio / 2
        letra = Image.new("RGBA", (int(cw + grosor * 4 + 4), int(f.size * 1.4 + grosor * 4)), (0, 0, 0, 0))
        ImageDraw.Draw(letra).text((grosor * 2, grosor), ch, font=f, fill=col, stroke_width=grosor, stroke_fill=borde)
        letra = letra.rotate(-math.degrees(a), resample=Image.BICUBIC, expand=True)
        x = centro[0] + radio * math.sin(a) - letra.width / 2
        y = centro[1] - radio * math.cos(a) - letra.height / 2
        capa.alpha_composite(letra, (int(x), int(y)))
        ang += cw / radio


# ---------- formas ----------
def capa_forma(lienzo, c, mk):
    capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    x, y, w, h = c.get("x", 0), c.get("y", 0), c.get("w", 200), c.get("h", 200)
    col = color(c.get("color", "acento"), mk, round(255 * c.get("opacidad", 1)))
    forma = c.get("forma", "rect")
    if forma == "circulo":
        d.ellipse([x, y, x + w, y + h], fill=None if c.get("solo_borde") else col, outline=col, width=c.get("grosor", 10))
    elif forma == "flecha":
        g = c.get("grosor", 26)
        d.line([(x, y + h), (x + w, y)], fill=col, width=g)
        ang = math.atan2(-h, w)
        L = g * 2.6
        for s in (-1, 1):
            d.line([(x + w, y), (x + w - L * math.cos(ang + s * 0.5), y - L * math.sin(ang + s * 0.5))], fill=col, width=g)
    elif forma == "degradado":         # franja que oscurece un lado para que el texto se lea
        lado = c.get("desde", "izq")
        giro = {"der": Image.Transpose.ROTATE_90, "izq": Image.Transpose.ROTATE_270, "abajo": None, "arriba": Image.Transpose.ROTATE_180}[lado]
        grad = Image.linear_gradient("L")
        grad = (grad.transpose(giro) if giro else grad).resize((w, h))
        bloque = Image.new("RGBA", (w, h), col)
        op = c.get("opacidad", 0.8)
        bloque.putalpha(grad.point(lambda v: int(255 * op * (v / 255) ** 1.6)))   # suave: transparente en un borde, oscuro en el otro
        capa.alpha_composite(bloque, (x, y))
    else:
        d.rounded_rectangle([x, y, x + w, y + h], radius=c.get("radio", 0), fill=col)
    lienzo.alpha_composite(capa)


def capa_logo(lienzo, c, mk):
    if not mk.get("logo"):
        return
    ruta = Path(mk["logo"]) if Path(mk["logo"]).is_absolute() else Path(mk["_ruta"]) / mk["logo"]
    if ruta.exists():
        logo = ImageOps.contain(Image.open(ruta).convert("RGBA"), (c.get("w", 160), c.get("h", 160)))
        lienzo.alpha_composite(logo, (c.get("x", 24), c.get("y", 24)))


# ---------- plantillas ----------
def revisar(lienzo):
    """Reglas de legibilidad para miniaturas y portadas (las mismas que se miran a ojo, ahora medidas)."""
    W, H = lienzo.size
    avisos, info = [], []
    palabras = sum(len(r["texto"].split()) for r in REGISTRO)
    fuentes = {Path(str(r["fuente"])).name for r in REGISTRO}
    info.append(f"{palabras} palabras, {len(fuentes)} fuente(s): {', '.join(sorted(fuentes))}")
    if palabras > 6:
        avisos.append(f"{palabras} palabras: en una miniatura se leen 2-4 de un vistazo; dejar el resto para el título")
    if len(fuentes) > 2:
        avisos.append(f"{len(fuentes)} fuentes distintas: usar 1 o 2 (una para el título, otra para lo secundario)")
    tams = sorted({r["tam"] for r in REGISTRO}, reverse=True)
    if len(tams) > 1 and tams[0] < tams[1] * 1.5:
        avisos.append("el texto principal y el secundario tienen tamaños parecidos: la jerarquía no se nota (el principal ~2 veces más grande)")
    for r in REGISTRO:
        en_cel = r["tam"] * 160 / W
        info.append(f"«{r['texto'][:30]}»: {r['tam']} px ({en_cel:.1f} px a 160 de ancho), contraste {r['contraste']}:1")
        if en_cel < 8 and r is REGISTRO[0]:
            avisos.append(f"«{r['texto'][:30]}» queda de {en_cel:.1f} px en el celular: no se lee; agrandar o acortar")
        if r["contraste"] < 3 and not r["apoyo"]:
            avisos.append(f"«{r['texto'][:30]}» contrasta {r['contraste']}:1 con su fondo (mínimo 3:1 para texto grande): agregar contorno, caja o cambiar el color")
        if H > W:          # vertical: zona segura de Reels/Shorts/TikTok
            x0, y0, x1, y1 = r["caja"]
            if y0 < 0.12 * H or y1 > 0.80 * H or x1 > 0.86 * W:
                avisos.append(f"«{r['texto'][:30]}» toca la zona de botones o de texto de la app: moverlo hacia el centro")
    return avisos, info


def render(plantilla, datos=None, base=".", canal=None):
    datos = datos or {}
    REGISTRO.clear()
    mk = marca(canal or plantilla.get("canal") or datos.get("canal"), datos.get("proyecto"))
    W, H = plantilla.get("tamano", [1280, 720])
    lienzo = Image.new("RGBA", (W, H), color(plantilla.get("fondo", "fondo"), mk))
    for c in plantilla["capas"]:
        c = {k: (re.sub(r"\{\{(\w+)\}\}", lambda m: str(datos.get(m.group(1), "")), v) if isinstance(v, str) and k != "texto" else v)
             for k, v in c.items()}
        if c.get("si") and not datos.get(c["si"]):
            continue
        {"imagen": lambda: capa_imagen(lienzo, c, mk, base), "texto": lambda: capa_texto(lienzo, c, mk, datos),
         "forma": lambda: capa_forma(lienzo, c, mk), "logo": lambda: capa_logo(lienzo, c, mk)}[c["tipo"]]()
    return lienzo.convert("RGB")


def escalar_plantilla(p, W, H):
    """Misma plantilla en otro formato. Mismo sentido (horizontal->horizontal): escala. Si cambia de horizontal a vertical o
    cuadrado: recompone — la imagen de fondo llena la pantalla con recorte inteligente, las franjas pasan a oscurecer
    abajo, y los textos se apilan centrados dentro de la zona segura de Reels/Shorts. Una plantilla vertical propia
    (por ejemplo portada-short) siempre queda mejor que la adaptación."""
    W0, H0 = p.get("tamano", [1280, 720])
    if (W0 > H0) and (H >= W):
        capas, y, zona_x, zona_w = [], 0.20 * H, round(0.08 * W), round(0.76 * W)
        for c in p["capas"]:
            c2 = dict(c)
            if c.get("tipo") == "imagen" and c.get("w", W0) >= W0 * 0.95:
                c2.update(x=0, y=0, w=W, h=H, ajuste="inteligente")
            elif c.get("tipo") == "imagen":
                lado = round(0.6 * W)
                c2.update(x=(W - lado) // 2, y=round(0.42 * H), w=lado, h=lado)
            elif c.get("forma") == "degradado":
                c2.update(x=0, y=0, w=W, h=round(0.62 * H), desde="arriba", opacidad=c.get("opacidad", 0.8))
            elif c.get("tipo") == "texto":
                tam = round(c.get("tam", 100) * W / W0 * 1.25)
                c2.update(x=zona_x, y=round(y), w=zona_w, tam=tam, alinear="centro", max_lineas=max(3, c.get("max_lineas", 3)))
                y += tam * 1.1 * c2["max_lineas"] * 0.75 + 30
            elif c.get("tipo") == "logo":
                c2.update(x=round(0.06 * W), y=round(0.80 * H) - 120)
            else:
                for a in ("x", "w"):
                    if a in c:
                        c2[a] = round(c[a] * W / W0)
                for a in ("y", "h"):
                    if a in c:
                        c2[a] = round(c[a] * H / H0)
            capas.append(c2)
        return dict(p, tamano=[W, H], capas=capas)
    k = min(W / W0, H / H0)
    nueva = dict(p, tamano=[W, H], capas=[])
    dx, dy = (W - W0 * k) / 2, (H - H0 * k) / 2
    for c in p["capas"]:
        c2 = dict(c)
        if c.get("tipo") == "imagen" and c.get("w", W0) >= W0 * 0.95 and c.get("h", H0) >= H0 * 0.95:
            c2.update(x=0, y=0, w=W, h=H, ajuste=c.get("ajuste_otros", "inteligente"))     # fondo a pantalla completa
        else:
            for a in ("x", "w", "y", "h", "tam", "grosor", "radio"):
                if a in c:
                    c2[a] = round(c[a] * k + (dx if a == "x" else dy if a == "y" else 0))
        nueva["capas"].append(c2)
    return nueva


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit("uso: python diseno.py plantilla|redimensionar|marca ...  (ver encabezado)")
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    paso = a[0]
    if paso == "marca":
        canal = a[1] if len(a) > 1 else "finanzas"
        f = ESTUDIO / "canales" / canal / "marca.json"
        if not f.exists():
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(MARCA_BASE, ensure_ascii=False, indent=2), encoding="utf-8")
            print("creado kit base (editar colores, fuentes y logo):", f)
        print(json.dumps(marca(canal), ensure_ascii=False, indent=2))
        return
    if paso == "redimensionar":
        ruta = Path(a[1])
        im = ImageOps.exif_transpose(Image.open(ruta)).convert("RGB")
        salida = Path(opt("--salida") or ruta.parent / "formatos")
        salida.mkdir(parents=True, exist_ok=True)
        for fm in opt("--formatos", "16x9,9x16,1x1,4x5").split(","):
            W, H = FORMATOS[fm]
            out = recorte_inteligente(im, W, H) if opt("--modo", "inteligente") == "inteligente" else con_relleno(im, W, H)
            destino = salida / f"{ruta.stem}_{fm}.jpg"
            out.save(destino, quality=92)
            print("listo:", destino)
        return
    if paso == "plantilla":
        pl_ruta = Path(a[1]) if Path(a[1]).exists() else Path(__file__).with_name("plantillas") / f"{a[1]}.json"
        plantilla = json.loads(pl_ruta.read_text(encoding="utf-8-sig"))
        datos = json.loads(Path(opt("--datos")).read_text(encoding="utf-8-sig")) if opt("--datos") else {}
        for x in [a[i + 1] for i, v in enumerate(a) if v == "--campo"]:
            k, v = x.split("=", 1)
            datos[k] = v.replace("\\n", "\n")
        base = Path(opt("--base") or (Path(opt("--datos")).parent if opt("--datos") else Path.cwd()))
        salida = Path(opt("--salida") or base / f"{pl_ruta.stem}.png")
        salida.parent.mkdir(parents=True, exist_ok=True)
        img = render(plantilla, datos, base, opt("--canal"))
        img.save(salida, quality=93)
        print("listo:", salida)
        avisos, info = revisar(img)
        texto_rev = "\n".join(["Revisión de legibilidad", *info, "", *(f"AVISO: {a}" for a in avisos)] or [])
        salida.with_name(salida.stem + "_revision.txt").write_text(texto_rev + ("\nOK: sin avisos" if not avisos else "") + "\n", encoding="utf-8")
        print(texto_rev + ("\nOK: sin avisos" if not avisos else ""))
        for fm in [f for f in (opt("--formatos") or "").split(",") if f]:
            W, H = FORMATOS[fm]
            destino = salida.with_name(f"{salida.stem}_{fm}{salida.suffix}")
            img2 = render(escalar_plantilla(plantilla, W, H), datos, base, opt("--canal"))
            img2.save(destino, quality=93)
            avisos2, _ = revisar(img2)
            print("listo:", destino, *(f"\n  AVISO {fm}: {a}" for a in avisos2))
        # vista de cómo se ve en el celular (160 px de ancho, como en la lista de YouTube)
        prev = Image.open(salida)
        prev.resize((160, round(160 * prev.height / prev.width))).save(salida.with_name(salida.stem + "_160px.png"))
        return
    sys.exit("paso desconocido: " + paso)


if __name__ == "__main__":
    main()
