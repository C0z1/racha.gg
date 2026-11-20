"""El feedback al terminar (postpartida.feedback): qué hiciste bien, qué no con su minuto, por qué importa (tu WR) y un foco."""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import unittest
from unittest import mock

import companion_gui as gui, companion_web as w, postpartida as P


def foto(t, eventos):
    ps = [{"riotId": "Yo#1", "riotIdGameName": "Yo", "summonerName": "Yo", "team": "ORDER", "position": "BOTTOM", "championName": "Zeri", "level": 9},
          {"riotId": "Rival#1", "riotIdGameName": "Rival", "summonerName": "Rival", "team": "CHAOS", "position": "BOTTOM", "championName": "Draven", "level": 10},
          {"riotId": "Ami#1", "riotIdGameName": "Ami", "summonerName": "Ami", "team": "ORDER", "position": "JUNGLE", "championName": "Vi"}]
    return {"activePlayer": {"riotId": "Yo#1"}, "allPlayers": ps, "gameData": {"gameTime": t, "gameMode": "CLASSIC"},
            "events": {"Events": eventos}}


KILL = lambda t, k, v, a=(): {"EventName": "ChampionKill", "EventTime": t, "KillerName": k, "VictimName": v, "Assisters": list(a)}
DRAGON = lambda t, k: {"EventName": "DragonKill", "EventTime": t, "KillerName": k}


def series(n=40):
    """Partidas de bot donde morir antes del 6 y no tener dragón al 14 se pagan, y kp6 no cambia nada."""
    return [dict(pos="BOTTOM", win=i % 4 != 0 if i < n // 2 else i % 4 == 0, muertes=[0] * 7 if i < n // 2 else [1] * 7,
                 dragones14=1 if i < n // 2 else 0, kp=[0.5] * 7, cs=[], nivel=[], nivel_rival=[]) for i in range(n)]


class Medidas(unittest.TestCase):
    def test_de_la_ultima_foto(self):
        d = foto(1000, [KILL(100, "Rival", "Yo"), KILL(200, "Yo", "Rival", ["Ami"]), KILL(300, "Ami", "Rival"), DRAGON(400, "Rival"),
                        DRAGON(700, "Ami"), KILL(900, "Rival", "Yo")])
        m = P.medidas_vivo(d, {"6": (5, 6), 10: (9, 10)})
        self.assertEqual((m["muertes6"], m["muertes14"], m["dragones14"], m["kp6"], m["nivel10"]), (1, 1, 1, 0.5, -1))
        self.assertNotIn("muertes14_25", m)  # la partida no llegó al 25
        self.assertEqual(m["minutos"]["muertes6"], ["1:40"]); self.assertEqual(m["minutos"]["dragones14"], ["6:40"])
        self.assertEqual(P.medidas_vivo({"gameData": {"gameMode": "ARAM"}}), {})

    def test_de_la_partida_de_riot(self):  # exactas, con CS y niveles del timeline, y los mismos errores que la franja
        import json, pathlib, tempfile, cliente_v5
        from test_cliente_v5 import FX, CAMPEONES
        d = json.loads(FX.read_text(encoding="utf-8")); m, t = cliente_v5.a_v5(d["game"], d["timeline"], "la1", CAMPEONES)
        yone = next(p for p in m["info"]["participants"] if p["championName"] == "Yone")
        with tempfile.TemporaryDirectory() as x:
            x = pathlib.Path(x); (x / "timeline").mkdir(); f = x / "LA1_1.json"
            f.write_text(json.dumps(m)); (x / "timeline" / f.name).write_text(json.dumps(t))
            r = P.medidas_partida(f, yone["puuid"])
        self.assertEqual((r["cs10"], r["muertes14"], r["muertes14_25"], r["nivel10"]), (74, 2, 3, 0))
        self.assertEqual(r["minutos"]["muertes14_25"], ["17:27", "20:02", "23:31"])
        self.assertIn({"t": 1202, "id": "sin_objetivo"}, r["errores"])

    def test_niveles_de_su_minuto(self):
        nv = {}
        for t, a, b in ((150, 2, 3), (185, 3, 3), (230, 4, 3), (600, 9, 10), (1000, 12, 12)): P.anotar_niveles(nv, {"t": t, "nivel": a, "nivel_rival": b})
        self.assertEqual(nv, {3: (3, 3), 10: (9, 10)})
        P.anotar_niveles(nv, {"t": 20, "nivel": 1, "nivel_rival": 1}); self.assertEqual(nv, {})  # otra partida


class Feedback(unittest.TestCase):
    def test_por_que_importa_con_tu_wr(self):
        x = P.impacto(series(), "BOTTOM", "muertes6")
        self.assertEqual((x["umbral"], x["n_si"], x["n_no"]), (0, 20, 20)); self.assertGreater(x["si"], x["no"])
        self.assertIsNone(P.impacto(series(20), "BOTTOM", "muertes6"))  # 10 de cada lado: ruido
        self.assertIsNone(P.impacto(series(), "TOP", "muertes6"))

    def test_bien_mal_y_foco(self):
        fb = P.feedback({"muertes6": 2, "dragones14": 1, "kp6": 0.5, "minutos": {"muertes6": ["3:09", "5:50"]},
                         "errores": [{"t": 913, "id": "sin_objetivo"}, {"t": 1100, "id": "sin_objetivo"}]}, series(), "BOTTOM")
        self.assertEqual(fb["bien"], ["Dragones al 14: 1. En tus partidas, con 1 dragón o más al 14 ganas 75% de 20 partidas de bot; si no, 25% de 20."])
        self.assertEqual(fb["mal"][0], "Muertes al 6: 2 (min 3:09, 5:50). En tus partidas, con 0 muertes al 6 ganas 75% de 20 partidas de bot; si no, 25% de 20.")
        self.assertEqual(fb["mal"][1], "Min 15:13 y 18:20: moriste sin que tu equipo tomara un objetivo cerca.")
        self.assertTrue(fb["foco"].startswith("Para la próxima: 0 muertes al 6.")); self.assertIsNone(fb["nota"])
        self.assertFalse(any("peleas" in x.lower() for x in fb["bien"] + fb["mal"]))  # kp6 no cambia tu WR: no sale

    def test_sin_historial(self):
        fb = P.feedback({"muertes6": 2}, [], "BOTTOM")
        self.assertEqual((fb["bien"], fb["mal"], fb["foco"]), ([], [], None)); self.assertIn("bot", fb["nota"])

    def test_al_terminar_sale_en_fin(self):
        viejo = dict(w.ESTADO)
        try:
            w.ESTADO.update(guion=None, sombra=None)
            with mock.patch("sombra.series", return_value=series()), mock.patch.object(gui, "ajeno", return_value=False):
                w.evento(("fin", {"minuto": 20, "campeon": "Zeri", "kda": "1/3/0", "rival": "Draven", "cs": 160, "muertes14_25": None,
                                  "cotejo": True, "pos": "BOTTOM", "medidas": {"muertes6": 2}}))
            self.assertTrue(w.ESTADO["fin"]["feedback"]["foco"].startswith("Para la próxima"))
            with mock.patch.object(gui, "ajeno", return_value=True): self.assertIsNone(w.feedback_fin({"medidas": {"muertes6": 2}}))
        finally: w.ESTADO.clear(); w.ESTADO.update(viejo)


if __name__ == "__main__":
    unittest.main()
