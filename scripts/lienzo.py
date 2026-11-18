"""El dibujo de la franja Sombra: una barra de 340×56 (a 1080p) con 3 zonas que nunca cambian de lugar ni de significado
(regla · sombra · marcas), más el renglón (340×28) o el panel al morir (340×76) pegados debajo. Pillow, a 2× y reducido.
Recibe la escena de momentos.paso y no decide nada: solo dibuja."""
from overlay import ROSA, ROSA2, ROJO, SALVIA, ORO, TXT, ETQ, COLORES, _fuente, _png, _retrato

ANCHO, ALTO, RENGLON, PANEL, SEP = 340, 56, 28, 50, 4
CARTA_W, CARTA_H = 420, 104  # la carta de la pantalla de carga: 3 renglones al centro abajo (4 con el plan de rol: +24)
CARTA_RENGLON = 24
Z1, Z2 = 104, 256  # bordes de las zonas: regla 0–104, sombra 104–256, marcas 256–340
FONDO = (11, 7, 9, 214)  # casi negro al 84 %, como la pastilla del lienzo «Overlay en partida»
GRIS = ETQ
COL = {"rosa": ROSA2, "oro": ORO, "rojo": ROJO, "salvia": SALVIA, "gris": GRIS}


def alto(escena):
    """Alto total (a 1080p) de lo que se dibuja: la barra y, si hay, el renglón o el panel."""
    if escena.get("panel"): return ALTO + SEP + PANEL
    return ALTO + SEP + RENGLON if escena.get("renglon") else ALTO


def pintar(escena, esc=1.0, icono=None):
    """RGBA de ANCHO×alto(escena) por esc. icono(tipo, nombre) -> PNG: los renders del lienzo «Base LOL» (tu retrato y el minion
    caster); sin él, la inicial del campeón y el anillo solo."""
    from PIL import Image, ImageDraw
    S = 2; k = lambda v: round(v * esc * S)
    W, H = round(ANCHO * esc), round(alto(escena) * esc)
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W * S - 1, k(ALTO) - 1), radius=k(14), fill=FONDO, outline=ROSA + (89,), width=max(1, k(1)))
    for x in (Z1, Z2): d.line((k(x), k(10), k(x), k(ALTO - 10)), fill=(255, 255, 255, 31), width=max(1, k(1)))
    f10 = _fuente(k(10))

    cy, R = k(ALTO / 2), k(17)
    r = escena["regla"]  # 1. Regla: tu retrato con el anillo partido en tramos (render «MIN 14–25»); cada muerte del tramo apaga uno
    cx, n = k(30), max(1, min(5, r["tope"]))
    caja = (cx - R, cy - R, cx + R, cy + R); paso = 360 / n
    d.ellipse(caja, outline=(255, 255, 255, 20), width=k(3))
    roja = r["color"] == "rojo"; c1, c2 = COLORES.get(r["color"], COLORES["rosa"])
    vivos = Image.new("L", im.size, 0); dv = ImageDraw.Draw(vivos)  # los tramos vivos, en degradado claro→oscuro como en el lienzo
    for i in range(n):
        a0, a1 = -90 + i * paso + (6 if n > 1 else 0), -90 + (i + 1) * paso - (6 if n > 1 else 0)
        if i < n - r["apagadas"] and not roja: dv.arc(caja, a0, a1, fill=255, width=k(3.5))
        else: d.arc(caja, a0, a1, fill=ROJO + (217,), width=k(3.5))
    g = _degradado(c1, c2, caja); im.paste(g, caja[:2], vivos.crop((*caja[:2], caja[0] + g.width, caja[1] + g.height)))
    im.alpha_composite(_retrato(escena.get("campeon"), k(28), icono, roja), (cx - k(14), cy - k(14)))  # sobre tu tope: el retrato se apaga
    _medalla(d, f"{r['apagadas']}/{r['tope']}", (cx, cy + k(26)), c1, k)  # pisa solo el borde del anillo  # la medalla bajo el retrato, como el nivel de En vivo
    lineas = r["etq"].split(" · ") if " · " in r["etq"] else [f"{r['apagadas']} / {r['tope']}", r["etq"].lower()]
    for j, t in enumerate(lineas[:2]):
        px = 15 if j == 0 else 10
        while px > 8 and d.textlength(t, font=_fuente(k(px))) > k(Z1 - 62): px -= 1  # «Nivel -1» no se mete en la zona de la sombra
        d.text((k(58), cy + k((j - 0.5) * 16)), t, font=_fuente(k(px)), fill=((ROJO if roja else TXT) if j == 0 else GRIS) + (255,), anchor="lm")

    s = escena["sombra"]  # 2. Sombra: el minion (o las espadas desde el 14) en un anillo que se llena hacia tu sombra; el número con signo
    x_txt = Z1 + 12
    if s.get("icono"):
        cx, R2 = k(Z1 + 30), k(19); caja = (cx - R2, cy - R2, cx + R2, cy + R2)
        d.ellipse(caja, outline=(255, 255, 255, 26), width=k(3))
        if s.get("anillo"): d.arc(caja, -90, -90 + 360 * max(0.0, min(1.0, s["anillo"])), fill=COL.get(s["color"], ROSA2) + (255,), width=k(3))
        if s["icono"] == "minion" and (ic := _png(icono, "minion", "caster", k(32))): im.alpha_composite(ic, (cx - k(16), cy - k(16)))
        elif s["icono"] == "espadas" or s["icono"] == "minion":  # sin el render: las espadas cruzadas del lienzo (ícono de 24 en 20 px)
            for tramo in ESPADAS: d.line([(cx + k((x - 12) * 20 / 24), cy + k((y - 12) * 20 / 24)) for x, y in tramo], fill=ROSA2 + (255,), width=k(1.8), joint="curve")
        x_txt = Z1 + 56
    d.text((k(x_txt), k(21)), s["num"], font=_fuente(k(20)), fill=COL.get(s["color"], TXT) + (255,), anchor="lm")
    px = 10
    while px > 8 and d.textlength(s["etq"], font=_fuente(k(px))) > k(Z2 - 6 - x_txt): px -= 1  # «peleas vs sombra de mid» cabe sin cortarse
    d.text((k(x_txt), k(40)), s["etq"], font=_fuente(k(px)), fill=GRIS + (255,), anchor="lm")
    if s.get("trazo") and not s.get("icono"): _trazo(d, s["trazo"], (k(Z1 + 72), k(13), k(Z2 - 10), k(29)), k)  # sin anillo, el trazo de antes

    # 3. Marcas: solo un elemento rojo a la vez en toda la barra
    for i, m in enumerate(escena["marcas"]):
        cx, cy, rr = k(Z2 + 13 + i * 19), k(21), k(6)
        caja = (cx - rr, cy - rr, cx + rr, cy + rr)
        if m.get("late"):  # tu próxima marca, en su último minuto: un latido suave
            h = rr * 1.7; d.ellipse((cx - h, cy - h, cx + h, cy + h), fill=ORO + (45,))
        figura = (lambda caja, **kw: d.rounded_rectangle(caja, radius=k(2.5), **kw)) if m.get("error") else d.ellipse  # tus errores: cuadros
        if escena.get("brillo") is not None and escena["brillo"] in (m.get("id"), m["min"]):  # recién sellada: un halo que se va a los 600 ms
            h = rr * 2; d.ellipse((cx - h, cy - h, cx + h, cy + h), fill=(SALVIA if m["estado"] is True else ORO) + (70,))
        if m["estado"] is True: figura(caja, fill=SALVIA + (255,))
        elif m["estado"] is False: figura(caja, outline=(GRIS if roja else ROJO) + (255,), width=k(2))
        elif m["estado"] == "sin": d.line((cx - rr / 2, cy, cx + rr / 2, cy), fill=GRIS + (200,), width=k(2))
        else: figura(caja, outline=(ORO if m.get("proxima") else GRIS) + (200 if m.get("proxima") else 110,), width=max(1, k(1.5)))
        d.text((cx, k(40)), str(m.get("etq", m["min"])), font=f10, fill=GRIS + (255,), anchor="mm")

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


ESPADAS = (((14.5, 17.5), (3, 6), (3, 3), (6, 3), (17.5, 14.5)), ((13, 19), (19, 13)), ((16, 16), (20, 20)),
           ((14.5, 6.5), (18, 3), (21, 3), (21, 6), (17.5, 9.5)), ((5, 14), (9, 18)))  # el ícono de espadas del lienzo, en su caja de 24


def _degradado(c1, c2, caja):
    """Imagen del tamaño de caja con un degradado diagonal c1→c2 (el linearGradient 0,0→1,1 del lienzo)."""
    from PIL import Image
    x0, y0, x1, y1 = caja; mid = tuple((a + b) // 2 for a, b in zip(c1, c2))
    g = Image.new("RGBA", (2, 2)); g.putdata([c1 + (255,), mid + (255,), mid + (255,), c2 + (255,)])
    return g.resize((x1 - x0, y1 - y0), Image.BILINEAR)


def _medalla(d, t, centro, c1, k):
    """La medalla de 13 de alto bajo el retrato: texto oscuro sobre el color claro del tramo."""
    f = _fuente(k(9)); cx, y = centro; w = max(k(18), d.textlength(t, font=f) + k(8)); x0, x1, y0, y1 = cx - w / 2, cx + w / 2, y - k(13), y
    d.rounded_rectangle((x0, y0, x1, y1), radius=k(7), fill=c1 + (255,))
    d.text((cx, (y0 + y1) / 2), t, font=f, fill=(36, 17, 26, 255), anchor="mm")


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


def pintar_carta(lineas, esc=1.0):
    """La carta de la pantalla de carga (momentos.carta_carga): el match, tu regla y la tasa de tus marcas."""
    from PIL import Image, ImageDraw
    S = 2; k = lambda v: round(v * esc * S)
    lineas = lineas[:4]
    W, H = round(CARTA_W * esc), round(carta_alto(lineas) * esc)
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W * S - 1, H * S - 1), radius=k(16), fill=FONDO, outline=ROSA + (90,), width=max(1, k(1)))
    for i, t in enumerate(lineas):
        px = 16 if i == 0 else 12
        while px > 9 and d.textlength(t, font=_fuente(k(px))) > k(CARTA_W - 28): px -= 1  # un renglón largo se achica antes que cortarse
        d.text((k(CARTA_W / 2), k(26 + i * CARTA_RENGLON)), t, font=_fuente(k(px)), fill=(TXT if i == 0 else GRIS) + (255,), anchor="mm")
    return im.resize((W, H), Image.LANCZOS)


def carta_alto(lineas):
    """Alto (a 1080p) de la carta: 3 renglones o hasta 4."""
    return CARTA_H + CARTA_RENGLON * max(0, min(4, len(lineas)) - 3)
