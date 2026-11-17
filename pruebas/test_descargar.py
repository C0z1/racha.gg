"""descargar.py no trae una cuenta por defecto: sin RIOT_ID ni cliente abierto, sale con un mensaje y sin red."""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import os, pathlib, subprocess, sys, unittest

DIR = pathlib.Path(__file__).resolve().parent.parent / "scripts"


class TestSinCuenta(unittest.TestCase):
    def test_sin_riot_id_ni_cliente_sale(self):
        env = {k: v for k, v in os.environ.items() if k != "RIOT_ID"}
        env.update(RIOT_KEY="x", LOL_LOCKFILE=str(DIR / "no-existe.lockfile"), DATOS_DIR=str(DIR / "fixtures" / "no-crear"))
        r = subprocess.run([sys.executable, str(DIR / "descargar.py"), "1"], env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Falta tu cuenta", r.stderr)
        self.assertNotIn("cozi", (DIR / "descargar.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
