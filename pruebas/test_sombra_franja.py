"""Sombra en la app: ajustes y sondeo de 1 s, guion al empezar, bitácora y carta al terminar, y el dibujo de las 3 zonas."""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import pathlib, tempfile, unittest
from unittest import mock

import bitacora, companion_gui as gui, companion_web as w, lienzo, momentos

ESC = {"regla": {"tope": 2, "apagadas": 1, "etq": "Tu tope", "color": "oro"},
       "sombra": {"num": "+25%", "etq": "peleas vs sombra de mid", "color": "salvia", "trazo": [[0.3, 0.4], [0.5, 0.4], [None, 0.42], [0.6, 0.45]]},
       "marcas": [{"min": 6, "estado": True, "proxima": False}, {"min": 10, "estado": False, "proxima": False},
                  {"min": 14, "estado": "sin", "proxima": False}, {"min": 25, "estado": None, "proxima": True}],
       "renglon": None, "panel": None, "opacidad": 1.0}


def meta(t, **k): return {"campeon": "Sylas", "rival": "Zed", "pos": "MIDDLE", "t": t, "minuto": 0, "nivel": 1, "nivel_rival": 1, "cs": 0, "cs_meta": None, **k}


class Ajustes(unittest.TestCase):
    def test_sondeo_y_estilo(self):
        self.assertEqual(gui.sondeo({"franja_estilo": "sombra"}), 1)
        self.assertEqual(gui.sondeo({"franja_estilo": "clasica"}), gui.SONDEO_VIVO)
        self.assertEqual(gui.sondeo({"franja_estilo": "sombra", "overlay": False}), gui.SONDEO_VIVO)  # sin franja, sin prisa
        self.assertTrue(gui.valido("franja_estilo", "clasica")); self.assertFalse(gui.valido("franja_estilo", "neon"))
        self.assertEqual(gui.AJUSTES_DEF["franja_estilo"], "sombra"); self.assertIs(gui.AJUSTES_DEF["solo_marcas"], False)


class Ciclo(unittest.TestCase):
    def setUp(self):
        self.viejo = dict(w.ESTADO); self.tmp = tempfile.TemporaryDirectory()
        self.orig, bitacora.DIR = bitacora.DIR, pathlib.Path(self.tmp.name) / "b"

    def tearDown(self):
        w.ESTADO.clear(); w.ESTADO.update(self.viejo); bitacora.DIR = self.orig; self.tmp.cleanup()

    def test_meta_arma_el_guion_una_vez(self):
        w.ESTADO["ajustes"] = {**w.ESTADO["ajustes"], "franja_estilo": "sombra"}
        with mock.patch.object(w.threading, "Thread") as T:
            w.evento(("meta", meta(5)))
            self.assertEqual(T.call_args.kwargs["args"], ("Sylas", "Zed", "MIDDLE"))
            w.evento(("meta", meta(6)))  # ya hay un hilo armándolo
            self.assertEqual(T.call_count, 1)
        w.GUION[0] = False
        with mock.patch("guion.armar", return_value={"campeon": "Sylas", "regla": {"tope": 2}}), mock.patch.object(gui, "es_base", return_value=True):
            w.armar_guion("Sylas", "Zed", "MIDDLE")
        self.assertEqual(w.ESTADO["guion"]["campeon"], "Sylas")
        with mock.patch.object(w.threading, "Thread") as T:
            w.evento(("meta", meta(7))); T.assert_not_called()

    def test_fin_guarda_bitacora_y_carta(self):
        w.ESTADO.update(guion={"campeon": "Sylas", "rival": "Zed", "regla": {"metrica": "muertes", "tope": 2, "racha": 3, "corta": "Tope 2"}}, sombra=None)
        w.anotar([dict(t=361, id="marca6", clase="sello", dato="Marca 6 · 0 muertes", mostrado=True, motivo=None)], {"6": True})
        w.anotar([dict(t=500, id="nivel", clase="interrupcion", dato="Nivel -1 vs Zed", mostrado=False, motivo="en pelea")], {"6": True, "10": False})
        w.evento(("fin", {"minuto": 30, "campeon": "Sylas", "kda": "1/1/1", "rival": "Zed", "cs": 200, "muertes14_25": 1, "cotejo": True}))
        f = w.ESTADO["fin"]
        self.assertEqual(f["carta"], ["1 de 4 marcas", "Tu regla: cumplida · racha 4"])
        self.assertEqual([x["texto"] for x in f["bitacora"]], ["Marca 6 · 0 muertes", "Nivel -1 vs Zed"])
        self.assertEqual(bitacora.ultima()["marcas"], {"6": True, "10": False})
        w.evento(("revision", {"champ": "Sylas"}))
        self.assertEqual(len(w.ESTADO["revision"]["bitacora"]), 2)


class Dibujo(unittest.TestCase):
    def test_tamanos(self):
        self.assertEqual(lienzo.pintar(ESC).size, (340, 56))
        self.assertEqual(lienzo.pintar({**ESC, "renglon": "Marca 10 · 70 CS · sombra 74"}, 1.5).size, (510, round(88 * 1.5)))
        self.assertEqual(lienzo.pintar({**ESC, "panel": ["Muerte 2 de 2 · tu tope", "Dragones 1–2"]}).size, (340, 110))

    def test_tarde_mas_transparente(self):
        a = lienzo.pintar(ESC).getchannel("A").getextrema()[1]
        b = lienzo.pintar({**ESC, "opacidad": momentos.OPACIDAD_TARDE}).getchannel("A").getextrema()[1]
        self.assertLess(b, a)


if __name__ == "__main__":
    unittest.main()
