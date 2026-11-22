# Revisa un video terminado (del estudio o editado en CapCut) y avisa dónde aparece texto que parece de otro idioma
# (por defecto, inglés) dentro de la imagen: etiquetas, carteles, libros, boletas.
#   python revisar_idioma.py "<video.mp4>" [--destino es|en|pt] [--cada 1] [--desde 0] [--hasta 0]
#   (0.15) --destino = idioma en que debería estar el video (por defecto es): avisa el texto que no parece de ese idioma.
# Deja junto al video:  <video>_idioma.txt (minuto · texto · palabras sospechosas) y <video>_idioma.jpg (cuadros marcados).
# Lee cada segundo con RapidOCR (local, sin internet). No toca el video. Siguiente paso típico: traducir esas imágenes
# (texto_imagen.py o Codex/ChatGPT) y cambiarlas con reemplazar_imagen.py.
import io, json, re, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from estudio import FFMPEG, duracion_medio, nombre_libre

INGLES = set("""
THE AND FOR WITH YOUR YOU OUR FROM THIS THAT WHAT WHEN HOW WHY NOT ARE IS IT IN ON OF TO BY AT OR AS BE
BILL BILLS FEE FEES BANK BANKS PAYCHECK PAY PAID SALARY STOCK STOCKS STCK SHARES BOND BONDS FUND FUNDS SAVINGS SAVE
INCOME WEALTH RICH POOR DEBT DEBTS LOAN LOANS RENT TAX TAXES CASH MONEY BUDGET SPENDING EXPENSES EXPENSE COST COSTS
CREDIT CARD CARDS INTEREST RATE INVEST INVESTING INVESTMENT RETIREMENT EMERGENCY INSURANCE MORTGAGE PROFIT LOSS
PRICE SHOP STORE MARKET WALLET SUBSCRIPTION SUBSCRIPTIONS STATEMENT RECEIPT INVOICE GOAL GOALS
WORK WORKPLACE JOB OFFICE CLOSED OPEN EXIT STOP HELP HOME HOUSE CAR BOOK NEWS SALES FREE NEW OLD BIG SMALL
TODAY NOW TIME YEAR YEARS MONTH WEEK DAY LIFE FAMILY FUTURE STEP STEPS TIP TIPS RULE RULES WARNING ALERT
""".split())
ES_COMUNES = set("""
EL LA LOS LAS UN UNA DE DEL Y EN CON POR PARA ES SU SUS TU TUS MI MIS AL LO QUE NO SI YA MAS MÁS
""".split())


# 0.15: el idioma destino puede ser es (por defecto, como siempre), en o pt.
ES_PROPIAS = set("""
EL LOS LAS DEL UNA UNOS UNAS PARA CON POR PERO MUY HAY USTED USTEDES NOSOTROS ELLOS DINERO AHORRO AHORRAR GASTOS
CUENTA CUENTAS BANCO DEUDA DEUDAS PRECIO TIENDA TRABAJO SUELDO HOY AÑO AÑOS MES SEMANA VIDA FAMILIA CASA COSTO
""".split())
PT_PROPIAS = set("""
VOCÊ VOCE NÃO NAO UM UMA DOS DAS NOS NAS PARA COM POR MAS MUITO DINHEIRO POUPANÇA POUPAR GASTOS CONTA CONTAS BANCO
DÍVIDA DIVIDA PREÇO LOJA TRABALHO SALÁRIO SALARIO HOJE ANO ANOS MÊS SEMANA VIDA FAMÍLIA CASA CUSTO ISSO ESSE ESSA
""".split())
NOMBRE = {"es": "español", "en": "inglés", "pt": "portugués"}
PALABRA = r"[A-Za-zÁÉÍÓÚÑáéíóúñÜüÃÕÇÂÊÔÀãõçâêôà]{3,}"
ES_MARCA = r"Ñ|CIÓN$|CIONES$|IDAD$|IDADES$"


def _ingles(u):
    return u in INGLES or bool(re.search(r"(ING|TION|NESS|SHIP|IGHT|OUGH)$|TH|W|K|SH|OO", u))


def sospechosas(texto, destino="es"):
    """Palabras que no parecen del idioma destino. es: inglés (como siempre) y portugués (solo con marcas claras: ã, õ,
    ç, -ção); en: español y portugués (tildes, ñ, ç y palabras propias); pt: inglés y español."""
    out = []
    if destino == "es":
        for p in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñÜü]{3,}", texto):       # igual que antes del 0.15
            u = p.upper()
            if u in ES_COMUNES or re.search(r"[ÁÉÍÓÚÑÜ]", u):
                continue
            if _ingles(u):
                out.append(p)
        out += [p for p in re.findall(PALABRA, texto) if re.search(r"[ÃÕÇÂÊÔÀ]|ÇÃO$|ÇÕES$", p.upper())]
        return out
    for p in re.findall(PALABRA, texto):
        u = p.upper()
        if destino == "en":
            if re.search(r"[ÁÉÍÓÚÑÜÃÕÇÂÊÔÀ]", u) or u in ES_PROPIAS or u in PT_PROPIAS or re.search(ES_MARCA + "|ÇÃO$|MENTE$", u):
                out.append(p)
        elif destino == "pt":
            if re.search(r"[ÃÕÇÂÊÔ]", u) or u in PT_PROPIAS:
                continue                                          # tiene marcas o es palabra común del portugués
            if _ingles(u) or u in (ES_PROPIAS - PT_PROPIAS) or re.search(ES_MARCA, u):
                out.append(p)
    return out


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__ if __doc__ else "Uso: python revisar_idioma.py video.mp4")
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    v = Path(a[0])
    destino = (op("--destino") or op("--idioma") or "es").lower()[:2]
    if destino not in NOMBRE:
        sys.exit("--destino tiene que ser es, en o pt")
    cada, desde = float(op("--cada", 1)), float(op("--desde", 0))
    dur = duracion_medio(v)
    hasta = float(op("--hasta", 0)) or dur
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    hallazgos, leidos, fallidos = [], 0, 0
    t = desde
    while t < hasta:
        r = subprocess.run([str(FFMPEG), "-v", "error", "-ss", f"{t:.2f}", "-i", str(v), "-frames:v", "1", "-vf", "scale=1280:-2",
                            "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if r.returncode or not r.stdout:
            fallidos += 1
        else:
            leidos += 1
            im = Image.open(io.BytesIO(r.stdout)).convert("RGB")
            res, _ = ocr(np.array(im))
            malas = []
            for caja, txt, conf in res or []:
                if float(conf) < 0.6:
                    continue
                s = sospechosas(txt, destino)
                if s:
                    malas.append((txt, s, caja))
            if malas:
                hallazgos.append((t, malas, im))
                print(f"{int(t // 60)}:{t % 60:04.1f}  " + " | ".join(f"{x[0]} -> {', '.join(x[1])}" for x in malas), flush=True)
        t += cada
    if not leidos or fallidos > max(2, 0.05 * (leidos + fallidos)):
        sys.exit(f"ERROR: solo se pudieron leer {leidos} de {leidos + fallidos} cuadros; la revisión no es válida")
    txt = nombre_libre(v.with_name(v.stem + "_idioma.txt"))
    lineas = [f"# Texto que no parece {NOMBRE[destino]} (idioma destino) en {v.name} (revisado cada {cada:g} s, {leidos} cuadros leídos; confirmar a ojo: hay falsos positivos)", ""]
    for t, malas, _ in hallazgos:
        lineas.append(f"{int(t // 60)}:{t % 60:04.1f}\t" + " | ".join(f"{x[0]}  [{', '.join(x[1])}]" for x in malas))
    if not hallazgos:
        lineas.append("No se encontró texto sospechoso.")
    txt.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    if hallazgos:                                     # hoja con hasta 24 cuadros marcados
        sel = hallazgos[:: max(1, len(hallazgos) // 24)][:24]
        W, H, C = 480, 270, 4
        hoja = Image.new("RGB", (W * C, (H + 16) * ((len(sel) + C - 1) // C)), "white")
        d = ImageDraw.Draw(hoja)
        for i, (t, malas, im) in enumerate(sel):
            k = W / im.width
            m = im.resize((W, int(im.height * k)))
            dm = ImageDraw.Draw(m)
            for _, _, caja in malas:
                xs, ys = [p[0] * k for p in caja], [p[1] * k for p in caja]
                dm.rectangle([min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2], outline=(255, 0, 90), width=3)
            x, y = (i % C) * W, (i // C) * (H + 16)
            hoja.paste(m, (x, y + 16))
            d.text((x + 3, y + 2), f"{int(t // 60)}:{t % 60:04.1f}  " + ", ".join(w for x_ in malas for w in x_[1])[:60], fill="black")
        hoja.save(nombre_libre(v.with_name(v.stem + "_idioma.jpg")), quality=82)
    print(f"LISTO {len(hallazgos)} momentos con texto sospechoso -> {txt}", flush=True)


if __name__ == "__main__":
    main()
