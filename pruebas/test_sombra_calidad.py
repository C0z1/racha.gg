"""Calidad de Sombra (fases 2–4 del plan): imágenes de referencia por momento, la barra no pisa el HUD ni el marcador,
la franja no lee tu historial en partida, S11 de salud.py y el primer regreso.
  python pruebas/test_sombra_calidad.py --rehacer   vuelve a dibujar las referencias (solo si cambiaste el diseño a propósito)"""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import pathlib, subprocess, sys, unittest

import lienzo, momentos, overlay

REF = pathlib.Path(__file__).resolve().parent / "referencias"


def M(*est):
    """Las 4 marcas con su estado; la primera por venir es la próxima."""
    prox = next((m for m, e in zip((6, 10, 14, 25), est) if e is None), None)
    return [{"min": m, "estado": e, "proxima": m == prox} for m, e in zip((6, 10, 14, 25), est)]


def R(ap, col): return {"tope": 2, "apagadas": ap, "etq": "Tu tope", "color": col}


TR = [[40, 44], [52, 52], [60, 59], [70, 66], [75, 74]]
MOMENTOS = {  # una escena fija por momento del plan (las capturas de la Fase 4, sin la carta)
    "arranque": {"regla": R(0, "rosa"), "sombra": {"num": "30", "etq": "victorias · tu sombra", "color": "gris", "trazo": None}, "marcas": M(None, None, None, None),
                 "renglon": "vs Zed · 6 de 11 tuyas"},
    "linea": {"regla": R(0, "rosa"), "sombra": {"num": "+5", "etq": "CS vs sombra", "color": "salvia", "trazo": TR, "icono": "minion", "anillo": 0.9}, "marcas": M(True, None, None, None)},
    "sello": {"regla": R(0, "rosa"), "sombra": {"num": "-5", "etq": "CS vs sombra", "color": "oro", "trazo": TR, "icono": "minion", "anillo": 0.95}, "marcas": M(True, False, None, None),
              "renglon": "Marca 10 · 70 CS · sombra 74", "brillo": 10},
    "compra": {"regla": R(0, "rosa"), "sombra": {"num": "=", "etq": "CS vs sombra", "color": "salvia", "trazo": TR}, "marcas": M(True, None, None, None),
               "renglon": "Primer regreso · sombra: min 3,8"},
    "peleas": {"regla": R(1, "rosa"), "sombra": {"num": "+12%", "etq": "peleas vs sombra", "color": "salvia", "trazo": [[0.3, 0.35], [0.4, 0.36], [0.45, 0.38]], "icono": "espadas", "anillo": 1.0},
               "marcas": M(True, True, True, None)},
    "muerto": {"regla": R(2, "oro"), "sombra": {"num": "-8%", "etq": "peleas vs sombra", "color": "oro", "trazo": None}, "marcas": M(True, "sin", True, None),
               "panel": ["Muerte 2 de 2 · tu tope", "Dragones 1–2 · Torres 3–4"]},
    "errores": {"regla": {**R(0, "oro"), "etq": "Nivel -1 · E2"}, "sombra": {"num": "+5", "etq": "CS vs sombra", "color": "salvia", "trazo": TR},
                "marcas": [{"id": "cs10", "min": 10, "etq": "10", "estado": True, "proxima": False}, {"id": "muertes14_25", "min": 25, "etq": "25", "estado": None, "proxima": False},
                           {"id": "sin_objetivo", "min": 26, "etq": "E1", "error": True, "estado": False, "proxima": False},
                           {"id": "abajo_6", "min": 7, "etq": "E2", "error": True, "estado": None, "proxima": False}]},
    "nivel": {"regla": R(0, "rosa"), "sombra": {"num": "+5", "etq": "CS vs sombra", "color": "salvia", "trazo": TR}, "marcas": M(True, None, None, None),
              "renglon": "Nivel -1 vs Zed · min 10", "dibujo": {"tipo": "nivel", "tu": 5, "rival": 6, "campeon": "Zed"}},
    "oro14": {"regla": R(1, "rosa"), "sombra": {"num": "+12%", "etq": "peleas vs sombra", "color": "salvia", "trazo": None}, "marcas": M(True, True, True, None),
              "renglon": "-1300 oro en ítems vs Zed", "dibujo": {"tipo": "oro", "min": 14, "num": "-1300"}, "brillo": 14},
    "tarde": {"regla": R(2, "rojo"), "sombra": {"num": "+20%", "etq": "peleas vs sombra", "color": "salvia", "trazo": None}, "marcas": M(True, False, True, False),
              "opacidad": momentos.OPACIDAD_TARDE},
}


def dibujar(k):
    return lienzo.pintar({"renglon": None, "panel": None, "opacidad": 1.0, **MOMENTOS[k]})


class Referencias(unittest.TestCase):
    def test_cada_momento_se_ve_como_su_referencia(self):
        from PIL import Image, ImageChops, ImageStat
        for k in MOMENTOS:
            with self.subTest(momento=k):
                ref = REF / f"sombra-{k}.png"
                self.assertTrue(ref.exists(), f"falta {ref.name}: python pruebas/test_sombra_calidad.py --rehacer")
                a, b = dibujar(k), Image.open(ref).convert("RGBA")
                self.assertEqual(a.size, b.size)
                d = max(ImageStat.Stat(ImageChops.difference(a, b)).mean)  # el antialias del texto cambia un poco entre Pillow/FreeType
                self.assertLess(d, 6, f"{k}: la franja cambió (diferencia media {d:.1f}); si fue a propósito, --rehacer")

    def test_la_fuente_incluida_se_usa(self):
        self.assertTrue(overlay.FUENTES[0].exists())
        self.assertEqual(overlay._fuente(20).getname()[0], "Roboto")


def es_rojo(p): return p[3] > 100 and p[0] > 200 and p[0] - p[1] > 80 and abs(p[1] - p[2]) < 12  # el tono de ROJO, con antialias y opacidad


class Rojo(unittest.TestCase):
    def test_borde_rojo_fijo_solo_sobre_el_tope(self):
        borde = lambda k: es_rojo(dibujar(k).getpixel((lienzo.ANCHO // 2, 0)))
        self.assertTrue(borde("tarde"))  # pasaste tu tope
        for k in ("muerto", "linea"): self.assertFalse(borde(k))  # en el tope (oro) o debajo: sin borde rojo

    def test_flecha_de_nivel_en_oro_si_tu_regla_ya_es_roja(self):
        rojo = lambda reg: sum(1 for p in lienzo.pintar({**MOMENTOS["nivel"], "regla": reg, "panel": None, "opacidad": 1.0}).crop(
            (40, lienzo.ALTO + lienzo.SEP, 80, lienzo.ALTO + lienzo.SEP + lienzo.RENGLON)).getdata() if es_rojo(p))
        self.assertGreater(rojo(R(0, "rosa")), 10)
        self.assertEqual(rojo(R(2, "rojo")), 0)


class Geometria(unittest.TestCase):
    RES = ((1280, 720), (1600, 900), (1920, 1080), (2560, 1440), (3840, 2160))

    def test_no_pisa_marcador_ni_hud(self):
        for w, h in self.RES:
            juego = (0, 0, w, h); esc = overlay.escala(juego)
            ancho, alto = round(lienzo.ANCHO * esc), round(lienzo.ALTO * esc)
            for hud in (0.0, 0.4, 1.0):
                with self.subTest(res=(w, h), hud=hud):
                    x, y = overlay.colocar(juego, (w, h), alto, 0.22, "arriba", 6, 1.0, ancho, hud)
                    self.assertLessEqual(x + ancho, overlay.TOPE_DERECHO * w)  # el marcador empieza en ~0,78
                    x, y = overlay.colocar(juego, (w, h), alto, 0.22, "abajo", 6, 1.0, ancho, hud)
                    self.assertLessEqual(y + alto, overlay.hud_y(hud) * h)  # la barra, encima del HUD
                    self.assertGreaterEqual(x, overlay.ABAJO_X * w)  # a la derecha del chat
                    self.assertLessEqual(x + ancho, overlay.TOPE_DERECHO * w)


CODIGO_SIN_HISTORIAL = r"""
import sys, builtins
sys.path.insert(0, 'scripts'); abiertos = []; o = builtins.open
builtins.open = lambda f, *a, **k: (abiertos.append(str(f)), o(f, *a, **k))[1]
import franja, overlay, momentos, lienzo
g = {'campeon': 'Sylas', 'rival': 'Zed', 'marcas': {'6': {'meta': 1}}, 'regla': {'tope': 2},
     'sombra': {'alcance': 'campeon', 'n': 9, 'cs': list(range(36)), 'nivel': [1] * 36, 'muertes': [0] * 36, 'kp': [0.4] * 36, 'regreso': 4.0}}
e = None
for t in range(0, 1600, 37):
    e, esc, _ = momentos.paso(e, {'t': t, 'cs': t // 10, 'muertes6': 0, 'items': [[t // 300, 'x']], 'participacion': 0.5}, g, t)
    if esc: lienzo.pintar(esc)
malos = [m for m in ('draft', 'vistas', 'score', 'sombra', 'guion', 'indice') if m in sys.modules]
raw = [f for f in abiertos if 'raw' in f.replace(chr(92), '/').split('/')]
print(malos, raw); sys.exit(1 if malos or raw else 0)
"""


class SinHistorial(unittest.TestCase):
    def test_la_franja_no_importa_draft_ni_lee_datos_raw(self):
        r = subprocess.run([sys.executable, "-c", CODIGO_SIN_HISTORIAL], cwd=pathlib.Path(__file__).resolve().parent.parent, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class Salud(unittest.TestCase):
    def test_s11(self):
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "herramientas"))
        import salud
        base = {"estado": {"codigo": 200, "json": {"fase": "InProgress", "meta": {}}}, "fase_lcu": "InProgress", "vivo": [100, 102]}
        s11 = lambda fs: [x for x in salud.evaluar({**base, "franja_salud": fs}, 1000) if x["id"] == "S11"]
        self.assertEqual(s11({"t": 990, "lat_p95": 1.2, "cpu": 0.4, "ram": 40})[0]["nivel"], "OK")
        self.assertEqual(s11({"t": 990, "lat_p95": 2.0, "cpu": 0.4, "ram": 40})[0]["nivel"], "FALLA")
        self.assertEqual(s11({"t": 990, "lat_p95": 1.0, "cpu": 1.5, "ram": 40})[0]["nivel"], "AVISO")
        self.assertEqual(s11({"t": 100, "lat_p95": 9, "cpu": 9, "ram": 99}), [])  # viejo: de otra partida


class MedirFranja(unittest.TestCase):
    def test_peor_por_sondeo_contra_las_metas(self):
        import json, tempfile
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "herramientas"))
        import dev_medir
        with tempfile.TemporaryDirectory() as d:
            filas = [{"sondeo": 1, "lat_p95": 0.9, "cpu": 0.4, "ram": 41}, {"sondeo": 1, "lat_p95": 1.7, "cpu": 0.6, "ram": 42},
                     {"sondeo": 3, "lat_p95": 3.1, "cpu": 1.0, "ram": 40}]
            (pathlib.Path(d) / "franja-20261117.jsonl").write_text("\n".join(map(json.dumps, filas)) + "\n{cortado", encoding="utf-8")
            r = dev_medir.franja(d)
            self.assertEqual((r[1]["n"], r[1]["lat_p95"], r[1]["cpu"]), (2, 1.7, 0.6))
            self.assertEqual(r[1]["fallas"], ["lat_p95 1.7 (meta ≤ 1.5)"])
            self.assertEqual(len(r[3]["fallas"]), 2)  # 3,1 s y CPU 1,0 (la meta es estrictamente < 1 %)
            self.assertEqual(dev_medir.main_franja(d), 1)
            self.assertEqual(dev_medir.franja(pathlib.Path(d) / "no-existe"), {})


class PrimerRegreso(unittest.TestCase):
    def test_se_muestra_una_vez_al_primer_cambio_de_items(self):
        g = {"sombra": {"alcance": "campeon", "n": 9, "cs": [], "nivel": [], "muertes": [], "kp": [], "regreso": 3.8}, "marcas": {}, "regla": {"tope": 2}}
        e, _, _ = momentos.paso(None, {"t": 30, "items": [[1055, "Espada"]]}, g, 30)
        e, esc, n = momentos.paso(e, {"t": 250, "items": [[1055, "Espada"], [1036, "Daga"]]}, g, 250)
        self.assertEqual(esc["renglon"], "Primer regreso · sombra: min 3,8")
        self.assertEqual(n[0]["dato"], "Primer regreso · sombra: min 3,8 (tú: min 4,2)")
        e, esc, n = momentos.paso(e, {"t": 600, "items": [[1055, "Espada"], [1036, "Daga"], [1037, "Pico"]]}, g, 600)
        self.assertFalse([x for x in n if x["id"] == "regreso1"])


if __name__ == "__main__":
    if "--rehacer" in sys.argv:
        REF.mkdir(exist_ok=True)
        for k in MOMENTOS: dibujar(k).save(REF / f"sombra-{k}.png"); print("rehecha", k)
    else: unittest.main()


class Renders(unittest.TestCase):
    def test_usa_tu_retrato_y_el_minion(self):
        """Los renders del lienzo «Base LOL»: con icono(), tu retrato va en el medallón y el minion en el anillo de la sombra."""
        import io
        from PIL import Image
        png = lambda col: (lambda b: (Image.new("RGBA", (64, 64), col).save(b, "PNG"), b.getvalue())[1])(io.BytesIO())
        icono = lambda tipo, nombre: png((0, 0, 255, 255)) if tipo == "champion" else png((0, 255, 0, 255))
        esc = {"campeon": "Prueba", "regla": R(0, "rosa"), "marcas": M(None, None, None, None),
               "sombra": {"num": "+5", "etq": "CS vs sombra", "color": "salvia", "icono": "minion", "anillo": 0.8}}
        im = lienzo.pintar(esc, 1.0, icono)
        self.assertEqual(im.getpixel((30, 28))[:3], (0, 0, 255))  # el retrato, al centro del medallón de la zona Regla
        self.assertEqual(im.getpixel((lienzo.Z1 + 30, 28))[:3], (0, 255, 0))  # el minion, al centro del anillo de la zona Sombra
