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
        with mock.patch("guion.armar", return_value={"campeon": "Sylas", "rival": "Zed", "regla": {"tope": 2}}), mock.patch.object(gui, "ajeno", return_value=False):
            w.armar_guion("Sylas", "Zed", "MIDDLE")
        self.assertEqual(w.ESTADO["guion"]["campeon"], "Sylas")
        self.assertEqual(w.ESTADO["guion"]["regla"], {"tope": 2})
        with mock.patch.object(w.threading, "Thread") as T:
            w.evento(("meta", meta(7))); T.assert_not_called()

    def test_tu_otra_cuenta_arma_su_guion_y_una_ajena_no(self):
        with mock.patch("guion.armar", return_value={"campeon": "Zeri", "regla": {"tope": 2}}) as arma,                 mock.patch.object(gui, "es_base", return_value=False), mock.patch.object(gui, "ajeno", return_value=False):
            w.armar_guion("Zeri", "Aphelios", "BOTTOM")  # Zeriously con su carpeta propia (2026-11-18: la franja salía vacía)
        arma.assert_called_once(); self.assertEqual(w.ESTADO["guion"]["regla"], {"tope": 2})
        with mock.patch("guion.armar") as arma, mock.patch.object(gui, "ajeno", return_value=True):
            w.armar_guion("Zeri", "Aphelios", "BOTTOM")  # historial de otra persona en disco: solo lo básico
        arma.assert_not_called(); self.assertEqual(w.ESTADO["guion"], {"campeon": "Zeri", "rival": "Aphelios", "pos": "BOTTOM"})

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


class Etapa2(unittest.TestCase):
    def test_dos_no_bajan_a_una_interrupcion(self):
        with tempfile.TemporaryDirectory() as d:
            orig, gui.SIRVIO_F = gui.SIRVIO_F, pathlib.Path(d) / "s.json"
            try: self.assertEqual([gui.contar_sirvio(v) for v in ("no", "no_vi", "no", "no", "si")], [None, None, None, True, False])
            finally: gui.SIRVIO_F = orig
        e = momentos.nuevo(); e["interrupciones"] = 1
        self.assertEqual(momentos.puede_tocar(e, {"t": 400}, 1000, {"franja_poco": True}), (False, "sin presupuesto"))

    def test_escala_de_hud(self):
        import json, overlay
        self.assertEqual(overlay.hud_y(None), overlay.HUD_Y); self.assertAlmostEqual(overlay.hud_y(0.4), overlay.HUD_Y)
        self.assertLess(overlay.hud_y(1.0), overlay.hud_y(0.4)); self.assertGreater(overlay.hud_y(0.0), overlay.hud_y(0.4))  # HUD más grande: la franja sube
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "p.json"
            f.write_text(json.dumps({"files": [{"name": "Game.cfg", "sections": [{"name": "HUD", "settings": [{"name": "GlobalScale", "value": "0.7500"}]}]}]}))
            self.assertEqual(overlay.escala_hud(f), 0.75)
            f.write_text("{roto"); self.assertIsNone(overlay.escala_hud(f))

    def test_brillo_dura_600_ms(self):
        g = {"marcas": {"6": {"meta": 1}}, "regla": {"tope": 2}, "sombra": {}}
        f = {"t": 361, "muertes6": 0, "cs": 40, "items": []}
        e, esc, _ = momentos.paso(None, f, g, 100.0)
        self.assertEqual(esc["brillo"], "6")
        self.assertIsNone(momentos.paso(e, {**f, "t": 362}, g, 100.7)[1]["brillo"])
        self.assertEqual(lienzo.pintar(esc).size, (340, 88))

    def test_carta_de_carga(self):
        self.assertEqual(lienzo.pintar_carta(["Sylas vs Zed · 6 de 11 tuyas", "Tope 2", "Marcas 6/10: 8 · 5 de 10"]).size, (lienzo.CARTA_W, lienzo.CARTA_H))

    def test_guion_al_fijar_campeon(self):
        viejo = dict(w.ESTADO)
        try:
            w.ESTADO.update(ajustes={**w.ESTADO["ajustes"], "franja_estilo": "sombra"}, guion=None); w.GUION[0] = False
            with mock.patch.object(w.threading, "Thread") as T:
                w.quizas_guion("Sylas", None, "MIDDLE"); self.assertEqual(T.call_args.kwargs["args"], ("Sylas", None, "MIDDLE"))
            w.GUION[0] = False; w.ESTADO["guion"] = {"campeon": "Sylas", "rival": None}
            with mock.patch.object(w.threading, "Thread") as T:
                w.quizas_guion("Sylas", None, "MIDDLE"); T.assert_not_called()  # nada nuevo
                w.quizas_guion("Sylas", "Zed", "MIDDLE"); T.assert_called_once()  # llegó el rival
        finally: w.ESTADO.clear(); w.ESTADO.update(viejo); w.GUION[0] = False


class PorResolucion(unittest.TestCase):
    def test_cada_resolucion_recuerda_su_lugar(self):
        import overlay
        self.assertTrue(gui.valido("franja_por_res", {"1920x1080": [0.3, 0.1], "2560x1440": [0, 1]}))
        for malo in ({"1920": [0.3, 0.1]}, {"1920x1080": [1.5, 0]}, {"1920x1080": [0.1]}, [], {f"{1000 + i}x900": [0, 0] for i in range(9)}):
            self.assertFalse(gui.valido("franja_por_res", malo))
        self.assertEqual(overlay.resolucion((100, 0, 2020, 1080), None), "1920x1080")
        self.assertEqual(overlay.resolucion(None, (1280, 720)), "1280x720")


class AhorroYLatido(unittest.TestCase):
    def test_ahorro_lee_cada_3_s(self):
        self.assertEqual(gui.sondeo({"franja_estilo": "sombra", "sondeo_ahorro": True}), gui.SONDEO_AHORRO)
        self.assertEqual(gui.sondeo({"franja_estilo": "clasica", "sondeo_ahorro": True}), gui.SONDEO_VIVO)

    def test_la_proxima_marca_late_en_su_ultimo_minuto(self):
        g = {"marcas": {}, "regla": {"tope": 2}, "sombra": {}}
        late = lambda t, ahora: [m for m in momentos.paso(None, {"t": t}, g, ahora)[1]["marcas"] if m["late"]]
        self.assertEqual([m["min"] for m in late(330, 100.2)], [6])  # 5:30, en el latido
        self.assertEqual(late(330, 105.0), [])  # entre latidos
        self.assertEqual(late(200, 100.2), [])  # falta más de un minuto
