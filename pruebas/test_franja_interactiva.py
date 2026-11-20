import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
"""La franja interactiva (Ctrl+Shift+Z): la barra de botones, las vistas Stats y Build y la píldora minimizada."""
import unittest

import momentos, overlay, sombra

G = {"sombra": {"alcance": "campeon", "cs": [0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80], "nivel": [1, 2, 3, 4, 5, 6, 6, 7, 7, 8, 8],
                "kp": [None, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5], "oro": [500 + 400 * i for i in range(11)], "vision_min": 0.6}}
FOTO = {"t": 600, "cs": 65, "nivel": 9, "participacion": 0.4, "vision": 7.0, "oro_actual": 300, "oro": {"tu": 3500},
        "items": [[1055, "Espada"], [3006, "Botas"]], "proximo": {"id": "6672", "nombre": "Matakrakens", "falta": 1250}}


class Stats(unittest.TestCase):
    def test_filas_contra_tu_sombra(self):
        f = {x["etq"]: x for x in momentos.stats(FOTO, G, 600)}
        self.assertEqual((f["CS / min"]["num"], f["CS / min"]["mejor"]), ("7,0", False))  # 70/10 contra 80/10
        self.assertEqual((f["Nivel"]["num"], f["Nivel"]["dif"], f["Nivel"]["mejor"]), ("9", "1", True))
        self.assertEqual((f["Peleas"]["num"], f["Peleas"]["dif"]), ("40%", "10%"))
        self.assertEqual((f["Oro / min"]["num"], f["Oro / min"]["mejor"]), ("380", False))  # (300 + 3500)/10 contra 4500/10
        self.assertEqual((f["Visión / min"]["num"], f["Visión / min"]["mejor"]), ("0,7", True))

    def test_sin_referencia_y_antes_del_2(self):
        f = {x["etq"]: x for x in momentos.stats({**FOTO, "t": 90}, {"sombra": {}}, 90)}
        self.assertEqual(f["Oro / min"]["num"], "—")  # antes del 2:00 no hay oro por minuto
        self.assertTrue(all(x["dif"] is None for x in f.values()))  # sin sombra: «—»

    def test_build_marca_comprado_y_actual(self):
        b = momentos.build(FOTO, {"core": [("Espada", "1055"), ("Matakrakens", "6672"), ("Filo", "3031")], "fuente": "mejores"})
        self.assertEqual([(i["comprado"], i["actual"]) for i in b["items"]], [(True, False), (False, True), (False, False)])
        self.assertEqual((b["etq"], b["falta"]), ("build de los mejores", "faltan 1250"))
        self.assertIsNone(momentos.build(FOTO, None))


class Dibujo(unittest.TestCase):
    def setUp(self):
        try: import PIL  # noqa: F401
        except ImportError: self.skipTest("sin Pillow")
        import lienzo; self.L = lienzo

    def test_tamanos_y_botones(self):
        L = self.L
        self.assertEqual(L.pintar_barra("stats", False, 1.25).size, (425, round(L.BARRA * 1.25)))
        self.assertEqual(L.pintar_stats(momentos.stats(FOTO, G, 600), "sombra").size, (L.ANCHO, L.STATS_H))
        self.assertEqual(L.pintar_build(None).size, (L.ANCHO, L.BUILD_H))
        self.assertEqual(L.pintar_mini().size, (L.MINI_W, L.MINI_H))
        self.assertEqual([L.boton_en(x, 10) for x in (1, 60, 120, 180, 240, 339)], ["min", "sombra", "stats", "build", "ajustes", "mover"])
        self.assertIsNone(L.boton_en(100, L.BARRA)); self.assertIsNone(L.boton_en(-1, 5))

    def test_vistas_envuelve_solo_si_hace_falta(self):
        e = {"regla": {}}
        self.assertIs(overlay.vistas(e, {}, {}, FOTO, True, False), e)  # Sombra sin atajo: igual que antes
        v = overlay.vistas(e, {"guion": G}, {"franja_vista": "stats"}, FOTO, True, True)
        self.assertEqual((v["vista"], v["barra"], v["de"], len(v["stats"])), ("stats", True, "sombra", 5))
        self.assertIs(overlay.vistas(e, {}, {"franja_vista": "stats"}, FOTO, False, False), e)  # clásica: sin vistas
        self.assertEqual(overlay.vistas(e, {}, {"franja_vista": "stats"}, FOTO, False, True)["vista"], "sombra")  # clásica con atajo: solo la barra
        im = overlay.componer(v, 1.0, None, True)
        self.assertEqual(im.size, (self.L.ANCHO, self.L.BARRA + self.L.SEP + self.L.STATS_H))


class Sombra(unittest.TestCase):
    def test_curva_de_oro_y_vision(self):
        xs = [{"cs": [1], "nivel": [1], "muertes": [0], "kp": [None], "oro": [500 + i]} for i in range(10)]
        self.assertEqual(sombra.curvas(xs)["oro"], [504])
        self.assertEqual(sombra.sombra([], "Zed", "MIDDLE")["oro"], [])


if __name__ == "__main__":
    unittest.main()
