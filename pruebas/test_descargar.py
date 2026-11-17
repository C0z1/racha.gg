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


class TestDelClienteAV5(unittest.TestCase):
    """Lo guardado desde el cliente (sin dataVersion) se cambia por Match-V5; si Riot no la tiene (404), se queda y no se pide más."""
    def correr(self, raw, pedidas):
        import io, json, runpy, urllib.error
        from unittest import mock
        def urlopen(req, timeout=None, **_):
            url = getattr(req, "full_url", req)
            if "127.0.0.1" in url: raise urllib.error.URLError("cliente cerrado")
            pedidas.append(url)
            if "/accounts/by-riot-id/" in url: r = {"puuid": "P", "gameName": "a", "tagLine": "b"}
            elif "/entries/by-puuid/" in url or "/ids?" in url: r = []
            elif url.endswith("/LA1_3") or url.endswith("/LA1_3/timeline"): raise urllib.error.HTTPError(url, 404, "no", {}, None)
            elif url.endswith("/timeline"): r = {"info": {"frames": []}, "riot": True}
            else: r = {"metadata": {"dataVersion": "2", "matchId": url.rsplit("/", 1)[1]}, "info": {"participants": []}}
            return io.BytesIO(json.dumps(r).encode())
        with mock.patch.dict(os.environ, {"RIOT_KEY": "x", "RIOT_REGION": "la1"}), mock.patch("urllib.request.urlopen", urlopen):
            with self.assertRaises(SystemExit) as e:
                runpy.run_path(str(DIR / "descargar.py"), init_globals={"RAW_DIR": str(raw), "RIOT_ID_G": "a#b", "ARGV": ["1"], "ECO": lambda s: None})
        return e.exception.code

    def test_cambia_la_del_cliente_y_respeta_el_404(self):
        import json, tempfile
        with tempfile.TemporaryDirectory() as d:
            raw = pathlib.Path(d); (raw / "timeline").mkdir()
            for mid in ("LA1_2", "LA1_3"):  # como las escribe cliente_v5.a_v5: sin dataVersion
                (raw / f"{mid}.json").write_text(json.dumps({"metadata": {"matchId": mid}, "info": {"participants": []}}))
                (raw / "timeline" / f"{mid}.json").write_text(json.dumps({"info": {"frames": []}}))
            pedidas = []
            self.assertEqual(self.correr(raw, pedidas), 0)
            self.assertEqual(json.loads((raw / "LA1_2.json").read_text())["metadata"]["dataVersion"], "2")
            self.assertTrue(json.loads((raw / "timeline" / "LA1_2.json").read_text())["riot"])
            self.assertNotIn("dataVersion", (raw / "LA1_3.json").read_text())  # práctica: Riot no la tiene, se queda
            self.assertEqual(sorted(f.name for f in raw.glob("*_*.json")), ["LA1_2.json", "LA1_3.json"])  # una por partida
            pedidas.clear(); self.correr(raw, pedidas)
            self.assertFalse([u for u in pedidas if "LA1_" in u])  # la 2.ª corrida no vuelve a pedir ninguna


if __name__ == "__main__":
    unittest.main()
