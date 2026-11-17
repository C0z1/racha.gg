"""El dibujo de la franja Sombra: una barra de 340×56 (a 1080p) con 3 zonas que nunca cambian de lugar ni de significado
(regla · sombra · marcas), más el renglón (340×28) o el panel al morir (340×76) pegados debajo. Pillow, a 2× y reducido.
Recibe la escena de momentos.paso y no decide nada: solo dibuja."""
from overlay import ROSA, ROSA2, ROJO, SALVIA, ORO, TXT, ETQ, _fuente

ANCHO, ALTO, RENGLON, PANEL, SEP = 340, 56, 28, 50, 4
Z1, Z2 = 104, 256  # bordes de las zonas: regla 0–104, sombra 104–256, marcas 256–340
FONDO = (36, 12, 22, 224)  # vino oscuro al 88 %
GRIS = ETQ
COL = {"rosa": ROSA2, "oro": ORO, "rojo": ROJO, "salvia": SALVIA, "gris": GRIS}


def alto(escena):
    """Alto total (a 1080p) de lo que se dibuja: la barra y, si hay, el renglón o el panel."""
    if escena.get("panel"): return ALTO + SEP + PANEL
    return ALTO + SEP + RENGLON if escena.get("renglon") else ALTO


def pintar(escena, esc=1.0):
    """RGBA de ANCHO×alto(escena) por esc."""
    from PIL import Image, ImageDraw
    S = 2; k = lambda v: round(v * esc * S)
    W, H = round(ANCHO * esc), round(alto(escena) * esc)
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W * S - 1, k(ALTO) - 1), radius=k(14), fill=FONDO, outline=ROSA + (60,), width=max(1, k(1)))
    for x in (Z1, Z2): d.line((k(x), k(12), k(x), k(ALTO - 12)), fill=(255, 255, 255, 28), width=max(1, k(1)))
    f11, f10 = _fuente(k(11)), _fuente(k(10))

    r = escena["regla"]  # 1. Regla: una ficha por muerte de tu tope; se apaga una con cada muerte del tramo
    n, fx = max(1, min(5, r["tope"])), k(10)
    x0 = k(Z1 / 2) - (n * fx + (n - 1) * k(6)) / 2
    for i in range(n):
        x = x0 + i * (fx + k(6)); caja = (x, k(14), x + fx, k(14) + fx)
        if i < n - r["apagadas"]: d.ellipse(caja, fill=COL.get(r["color"], ROSA2) + (255,))
        else: d.ellipse(caja, outline=(COL["rojo"] if r["color"] == "rojo" else GRIS) + (200,), width=max(1, k(1.5)))
    d.text((k(Z1 / 2), k(40)), r["etq"], font=f11, fill=GRIS + (255,), anchor="mm")

    s = escena["sombra"]  # 2. Sombra: número grande con signo, etiqueta y el trazo de los últimos minutos
    f22 = _fuente(k(22))
    d.text((k(Z1 + 12), k(21)), s["num"], font=f22, fill=COL.get(s["color"], TXT) + (255,), anchor="lm")
    d.text((k(Z1 + 12), k(43)), s["etq"], font=f10, fill=GRIS + (255,), anchor="lm")
    x_tr = max(k(Z1 + 64), k(Z1 + 12) + d.textlength(s["num"], font=f22) + k(10))  # el trazo nunca pisa el número
    if s.get("trazo") and x_tr < k(Z2 - 40): _trazo(d, s["trazo"], (x_tr, k(13), k(Z2 - 10), k(29)), k)

    roja = r["color"] == "rojo"  # 3. Marcas: solo un elemento rojo a la vez en toda la barra
    for i, m in enumerate(escena["marcas"]):
        cx, cy, rr = k(Z2 + 13 + i * 19), k(21), k(6)
        caja = (cx - rr, cy - rr, cx + rr, cy + rr)
        if m["estado"] is True: d.ellipse(caja, fill=SALVIA + (255,))
        elif m["estado"] is False: d.ellipse(caja, outline=(GRIS if roja else ROJO) + (255,), width=k(2))
        elif m["estado"] == "sin": d.line((cx - rr / 2, cy, cx + rr / 2, cy), fill=GRIS + (200,), width=k(2))
        else: d.ellipse(caja, outline=(ORO if m.get("proxima") else GRIS) + (200 if m.get("proxima") else 110,), width=max(1, k(1.5)))
        d.text((cx, k(40)), str(m["min"]), font=f10, fill=GRIS + (255,), anchor="mm")

    y = k(ALTO + SEP)
    if escena.get("panel"):
        d.rounded_rectangle((0, y, W * S - 1, y + k(PANEL) - 1), radius=k(12), fill=FONDO)
        for i, t in enumerate(escena["panel"][:2]):
            d.text((k(14), y + k(16 + i * 18)), t, font=_fuente(k(13 if i == 0 else 11)), fill=(TXT if i == 0 else GRIS) + (255,), anchor="lm")
    elif escena.get("renglon"):
        d.rounded_rectangle((0, y, W * S - 1, y + k(RENGLON) - 1), radius=k(12), fill=FONDO)
        d.text((k(14), y + k(RENGLON / 2)), escena["renglon"], font=_fuente(k(12)), fill=TXT + (255,), anchor="lm")
    im = im.resize((W, H), Image.LANCZOS)
    if (o := escena.get("opacidad", 1.0)) < 1: im.putalpha(im.getchannel("A").point(lambda a: int(a * o)))
    return im


def _trazo(d, puntos, caja, k):
    """Tu línea (rosa) sobre la de tu sombra (gris), escaladas juntas en la caja. Los puntos sin dato se saltan."""
    x0, y0, x1, y1 = caja
    vs = [v for p in puntos for v in p if v is not None]
    if len(puntos) < 2 or not vs: return
    lo, hi = min(vs), max(vs); hi = hi if hi > lo else lo + 1
    paso = (x1 - x0) / (len(puntos) - 1)
    for j, col in ((1, GRIS), (0, ROSA2)):
        xy = [(x0 + i * paso, y1 - (p[j] - lo) / (hi - lo) * (y1 - y0)) for i, p in enumerate(puntos) if p[j] is not None]
        if len(xy) >= 2: d.line(xy, fill=col + (255,), width=k(2 if j == 0 else 1.5), joint="curve")
