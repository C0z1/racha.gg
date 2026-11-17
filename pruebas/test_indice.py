"""indice.py: lo calculado por partida se guarda en SQLite y vale mientras no cambien la partida, su timeline ni la versión."""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import json, os, pathlib, tempfile, unittest

import indice


class Indice(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); d = pathlib.Path(self.tmp.name)
        self.orig = indice.DB, list(indice._CON)
        indice.DB, indice._CON[:] = d / "cache" / "partidas.db", [None, False]
        (d / "raw" / "timeline").mkdir(parents=True)
        self.f = d / "raw" / "LA1_1.json"; self.f.write_text('{"info": {"participants": []}}')
        self.n = 0

    def tearDown(self):
        indice._apagar(); indice.DB, indice._CON[:] = self.orig[0], self.orig[1]; self.tmp.cleanup()

    def calc(self):
        self.n += 1; return {"n": self.n, "par": (1, 2)}

    def test_guarda_y_reusa(self):
        self.assertEqual(indice.derivado(self.f, "t", "v1", self.calc), {"n": 1, "par": [1, 2]})  # frío: ya como JSON
        self.assertEqual(indice.derivado(self.f, "t", "v1", self.calc), {"n": 1, "par": [1, 2]})  # caliente: sin calcular
        self.assertEqual(self.n, 1)
        self.assertEqual(indice.derivado(self.f, "otro", "v1", self.calc)["n"], 2)  # otro tipo, otra fila

    def test_recalcula_si_algo_cambia(self):
        indice.derivado(self.f, "t", "v1", self.calc)
        self.assertEqual(indice.derivado(self.f, "t", "v2", self.calc)["n"], 2)  # otra fórmula o cuenta
        (self.f.parent / "timeline" / self.f.name).write_text("{}")
        self.assertEqual(indice.derivado(self.f, "t", "v2", self.calc)["n"], 3)  # llegó el timeline
        self.f.write_text('{"info": {"participants": [1]}}')
        self.assertEqual(indice.derivado(self.f, "t", "v2", self.calc)["n"], 4)  # cambió la partida (Match-V5 encima)

    def test_db_dañada_se_rehace(self):
        indice.DB.parent.mkdir(parents=True); indice.DB.write_bytes(b"esto no es sqlite" * 100)
        self.assertEqual(indice.derivado(self.f, "t", "v1", self.calc)["n"], 1)
        self.assertEqual(indice.derivado(self.f, "t", "v1", self.calc)["n"], 1)  # ya funciona el índice nuevo

    def test_sin_db_calcula_directo(self):
        (pathlib.Path(self.tmp.name) / "archivo").write_text("x"); indice.DB = pathlib.Path(self.tmp.name) / "archivo" / "x.db"
        self.assertEqual(indice.derivado(self.f, "t", "v1", self.calc)["n"], 1)
        self.assertEqual(indice.derivado(self.f, "t", "v1", self.calc)["n"], 2)  # sin índice: siempre calcula
        self.assertEqual(indice.derivado(pathlib.Path(self.tmp.name) / "no_existe.json", "t", "v1", lambda: None), None)

    def test_sin_sqlite3(self):
        orig, indice.sqlite3 = indice.sqlite3, None
        try: self.assertEqual([indice.derivado(self.f, "t", "v1", self.calc)["n"] for _ in range(2)], [1, 2])
        finally: indice.sqlite3 = orig

    def test_borra_las_huerfanas(self):
        indice.derivado(self.f, "t", "v1", self.calc); indice._apagar(); indice._CON[:] = [None, False]
        self.f.unlink(); indice._conexion()
        self.assertEqual(indice._CON[0].execute("SELECT COUNT(*) FROM d").fetchone()[0], 0)

    def test_version_cambia_con_el_codigo(self):
        a = pathlib.Path(self.tmp.name) / "m.py"; a.write_text("x = 1")
        v1 = indice.version(a, "puuid"); a.write_text("x = 2")
        self.assertNotEqual(v1, indice.version(a, "puuid")); self.assertNotEqual(indice.version(a, "otro"), indice.version(a, "puuid"))


if __name__ == "__main__":
    unittest.main()
