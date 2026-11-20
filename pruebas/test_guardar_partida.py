"""Al salir de la partida se guarda sola: sin key o con otra cuenta, desde el cliente."""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import pathlib, queue, tempfile, unittest
from unittest import mock

import cliente_v5
import companion_gui as g
import companion_web as w


class GuardarDelCliente(unittest.TestCase):
    def test_reintenta_hasta_que_el_cliente_la_publica(self):
        q = queue.Queue()
        with mock.patch.object(cliente_v5, "descargar", side_effect=[(0, "ya"), (0, "ya"), (1, "1 nueva")]) as d:
            self.assertTrue(g.guardar_del_cliente(q, espera=0, intentos=5, dormir=lambda s: None))
        self.assertEqual(d.call_count, 3)

    def test_se_rinde_y_avisa(self):
        q = queue.Queue()
        with mock.patch.object(cliente_v5, "descargar", return_value=(0, "ya")):
            self.assertFalse(g.guardar_del_cliente(q, espera=0, intentos=3, dormir=lambda s: None))
        msgs = [q.get_nowait()[1] for _ in range(q.qsize())]
        self.assertTrue(any("lo que vio Racha" in m for m in msgs))

    def test_otra_partida_vieja_no_cuenta(self):  # 2026-11-19: el cliente publicó el Jhin de las 16:34 al terminar el Morde
        with tempfile.TemporaryDirectory() as d, mock.patch.object(g, "RAW", pathlib.Path(d)):
            def baja(gid=None):
                (pathlib.Path(d) / "LA1_111.json").write_text("{}"); return 1, "1 nueva"
            with mock.patch.object(cliente_v5, "descargar", side_effect=baja) as dl:
                self.assertFalse(g.guardar_del_cliente(queue.Queue(), 222, espera=0, intentos=2, dormir=lambda s: None))
            dl.assert_called_with(gid=222)
            (pathlib.Path(d) / "LA1_222.json").write_text("{}")
            with mock.patch.object(cliente_v5, "descargar", return_value=(1, "1 nueva")):
                self.assertTrue(g.guardar_del_cliente(queue.Queue(), 222, espera=0, intentos=2, dormir=lambda s: None))

    def test_id_partida_sin_cliente_es_none(self):
        for r in (None, "EndOfGame", {"gameData": {}}):
            with mock.patch.object(g.companion, "lcu", return_value=r): self.assertIsNone(g.id_partida())
        with mock.patch.object(g.companion, "lcu", side_effect=OSError): self.assertIsNone(g.id_partida())
        with mock.patch.object(g.companion, "lcu", return_value={"gameData": {"gameId": 9}}): self.assertEqual(g.id_partida(), 9)

    def test_cliente_que_falla_no_truena(self):
        with mock.patch.object(cliente_v5, "descargar", side_effect=[OSError("cerrándose"), (1, "ok")]):
            self.assertTrue(g.guardar_del_cliente(queue.Queue(), espera=0, intentos=3, dormir=lambda s: None))

    def test_post_partida_sin_key_usa_el_cliente(self):
        q = queue.Queue()
        with mock.patch.object(g, "puede_descargar", return_value=False), mock.patch.object(g, "guardar_del_cliente", return_value=True) as gc, \
                mock.patch.object(g, "script", return_value=(0, "")) as sc, mock.patch.object(g, "parsear_revision", return_value={"champ": "Ekko"}), \
                mock.patch.object(g, "ultima_partida", return_value={}):
            g._post_partida(q)
        gc.assert_called_once(); sc.assert_called_once_with("revision.py", "1")  # sin descargar.py; la revisión sí
        self.assertEqual(q.get_nowait()[0], "revision")

    def test_otra_cuenta_tambien_usa_el_cliente(self):
        with mock.patch.object(g, "puede_descargar", return_value=True), mock.patch.object(g, "es_base", return_value=False), \
                mock.patch.object(g, "guardar_del_cliente", return_value=False) as gc, mock.patch.object(g, "script") as sc:
            g._post_partida(queue.Queue())
        gc.assert_called_once(); sc.assert_not_called()  # no corre descargar.py con el Riot ID del dueño

    def test_key_caducada_guarda_desde_el_cliente(self):  # 2026-11-12: RIOT_KEY puesta pero Riot responde 401
        q = queue.Queue()
        with mock.patch.object(g, "puede_descargar", return_value=True), mock.patch.object(g, "es_base", return_value=True),                 mock.patch.object(g.time, "sleep"), mock.patch.object(g, "script", side_effect=[(2, ""), (0, "")]),                 mock.patch.object(g, "guardar_del_cliente", return_value=True) as gc, mock.patch.object(g, "parsear_revision", return_value={"champ": "Zeri"}),                 mock.patch.object(g, "ultima_partida", return_value={}):
            g._post_partida(q)
        gc.assert_called_once()
        tipos = [q.get_nowait()[0] for _ in range(q.qsize())]
        self.assertIn("revision", tipos)

    def test_al_dia_recalcula_si_entra_algo(self):
        with mock.patch.object(cliente_v5, "descargar", return_value=(2, "2 nuevas")), mock.patch.object(w, "refrescar") as r:
            w.al_dia()
        r.assert_called_once()
        with mock.patch.object(cliente_v5, "descargar", return_value=(0, "ya")), mock.patch.object(w, "refrescar") as r:
            w.al_dia()
        r.assert_not_called()


if __name__ == "__main__":
    unittest.main()
