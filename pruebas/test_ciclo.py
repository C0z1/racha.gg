"""ciclo.py (racha y graduación de tu regla) y bitacora.py (lo que pasó en la franja, para la revisión)."""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import json, pathlib, tempfile, unittest

import bitacora, ciclo

R = {"muertes": ("m25", lambda x: x <= 2)}
gs = lambda *ms: [{"m25": m} for m in ms]


class Ciclo(unittest.TestCase):
    def test_racha_y_falta(self):
        e = ciclo.estado(gs(3, 1, None, 0, 2), R)["muertes"]
        self.assertEqual((e["ok"], e["n"], e["racha"], e["graduada"], e["falta"]), (3, 4, 3, False, 5))  # sin dato no corta la racha

    def test_se_gradua_con_8_de_10_y_regresa_bajo_5(self):
        ocho = gs(*([0] * 8 + [3] * 2))
        self.assertTrue(ciclo.estado(ocho, R)["muertes"]["graduada"])
        siete = gs(*([0] * 7 + [3] * 3))
        self.assertFalse(ciclo.estado(siete, R)["muertes"]["graduada"])
        self.assertTrue(ciclo.estado(siete, R, {"muertes"})["muertes"]["graduada"])  # ya graduada: aguanta hasta 5
        self.assertFalse(ciclo.estado(gs(*([0] * 4 + [3] * 6)), R, {"muertes"})["muertes"]["graduada"])
        self.assertFalse(ciclo.estado(gs(*[0] * 9), R)["muertes"]["graduada"])  # 9 partidas: aún no hay 10

    def test_actualizar_recuerda_lo_graduado(self):
        with tempfile.TemporaryDirectory() as d:
            orig, ciclo.ARCHIVO = ciclo.ARCHIVO, pathlib.Path(d) / "c" / "ciclo.json"
            try:
                ciclo.actualizar(gs(*([0] * 10)), R)
                self.assertEqual(ciclo.leer()["graduadas"], ["muertes"])
                self.assertTrue(ciclo.actualizar(gs(*([0] * 6 + [3] * 4)), R)["muertes"]["graduada"])
            finally: ciclo.ARCHIVO = orig

    def test_regla_hoy_salta_las_graduadas(self):
        try: import vistas
        except Exception as e: self.skipTest(f"vistas necesita datos: {e}")
        rs = [dict(metrica="muertes", texto="M", numero="x", ok=3, n=20), dict(metrica="nivel", texto="N", numero="y", ok=5, n=20)]
        self.assertEqual(vistas.regla_hoy(rs, {"muertes"})["metrica"], "nivel")
        self.assertIsNone(vistas.regla_hoy(rs, {"muertes", "nivel"}))


class Bitacora(unittest.TestCase):
    def test_guarda_y_lee_para_la_revision(self):
        with tempfile.TemporaryDirectory() as d:
            orig, bitacora.DIR = bitacora.DIR, pathlib.Path(d) / "b"
            try:
                notas = [dict(t=361, id="marca6", clase="sello", dato="Marca 6 · 0 muertes", mostrado=True, motivo=None),
                         dict(t=400, id="compra", clase="compra", dato="Sheen · faltan 300", mostrado=True, motivo=None),
                         dict(t=500, id="nivel", clase="interrupcion", dato="Nivel -1 vs Zed", mostrado=False, motivo="en pelea")]
                self.assertIsNone(bitacora.guardar({}, {}, []))
                f = bitacora.guardar({"campeon": "Sylas", "rival": "Zed", "regla": {"corta": "Tope 2"}}, {"marcas": {"6": True}}, notas, True, ahora=1000)
                b = bitacora.ultima(desde=900)
                self.assertEqual((b["campeon"], b["marcas"], b["cumplida"]), ("Sylas", {"6": True}, True))
                self.assertIsNone(bitacora.ultima(desde=2000))
                self.assertEqual(bitacora.para_revision(b), [dict(min="6:01", texto="Marca 6 · 0 muertes", mostrado=True, motivo=None),
                                                              dict(min="8:20", texto="Nivel -1 vs Zed", mostrado=False, motivo="en pelea")])
                f.write_text("{roto"); self.assertIsNone(bitacora.ultima())
            finally: bitacora.DIR = orig


if __name__ == "__main__":
    unittest.main()
