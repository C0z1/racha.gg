"""sombra.py y guion.py: series por minuto desde el timeline, la mediana de tus victorias y el guion de champ select."""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import json, os, pathlib, re, tempfile, time, unittest

import indice, sombra, guion


def partida(d, n, win, champ="Sylas", pos="MIDDLE", cs_min=8, muertes=(), t=0):
    """Una partida Match-V5 mínima con su timeline: yo (pid 1, equipo 100) contra Zed (pid 6); muertes = minutos en que muero."""
    ps = [dict(puuid="yo" if i == 1 else f"p{i}", participantId=i, teamId=100 if i <= 5 else 200, championName=champ if i == 1 else "Zed" if i == 6 else "X",
               teamPosition=pos if i in (1, 6) else "TOP", win=win if i <= 5 else not win) for i in range(1, 11)]
    (d / f"LA1_{n}.json").write_text(json.dumps({"info": {"gameDuration": 1800, "gameCreation": t or n, "participants": ps}}))
    ev = [dict(type="CHAMPION_KILL", timestamp=m * 60000 - 1000, killerId=6, victimId=1, assistingParticipantIds=[]) for m in muertes]
    ev.append(dict(type="CHAMPION_KILL", timestamp=4 * 60000, killerId=2, victimId=7, assistingParticipantIds=[1]))  # una asistencia mía
    fr = [{"participantFrames": {str(i): dict(minionsKilled=cs_min * m if i == 1 else 7 * m, jungleMinionsKilled=0, level=1 + m // 2,
                                             totalGold=500 + 400 * m + (100 if i == 1 else 0)) for i in range(1, 11)},
           "events": [e for e in ev if (m - 1) * 60000 < e["timestamp"] <= m * 60000]} for m in range(31)]
    (d / "timeline" / f"LA1_{n}.json").write_text(json.dumps({"info": {"frames": fr}}))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = pathlib.Path(self.tmp.name) / "raw"
        (self.d / "timeline").mkdir(parents=True)
        (self.d / "perfil.json").write_text(json.dumps({"account": {"puuid": "yo"}}))
        self.orig = indice.DB, list(indice._CON); indice.DB, indice._CON[:] = pathlib.Path(self.tmp.name) / "i.db", [None, False]

    def tearDown(self):
        indice._apagar(); indice.DB, indice._CON[:] = self.orig[0], self.orig[1]; self.tmp.cleanup()


class Sombra(Base):
    def test_serie_de_una_partida(self):
        partida(self.d, 1, True, muertes=(3, 20))
        s = sombra.serie(self.d / "LA1_1.json", "yo")
        self.assertEqual((s["champ"], s["pos"], s["rival"], s["win"]), ("Sylas", "MIDDLE", "Zed", True))
        self.assertEqual(s["cs"][10], 80); self.assertEqual(s["nivel"][6], 4)
        self.assertEqual((s["muertes"][2], s["muertes"][3], s["muertes"][25]), (0, 1, 2))
        self.assertEqual((s["kp"][3], s["kp"][4]), (None, 1.0))  # sin kills del equipo, None; luego 1 de 1
        self.assertEqual(s["oro14"], 100)

    def test_sin_timeline_o_roto_no_hay_serie(self):
        partida(self.d, 1, True); (self.d / "timeline" / "LA1_1.json").write_text("{roto")
        self.assertIsNone(sombra.serie(self.d / "LA1_1.json", "yo"))
        self.assertIsNone(sombra.serie(self.d / "LA1_1.json", "otro"))

    def test_mediana_del_campeon_rol_o_nada(self):
        for i in range(8): partida(self.d, i + 1, True, cs_min=6 + i)
        ss = sombra.series(self.d)
        sb = sombra.sombra(ss, "Sylas", "MIDDLE")
        self.assertEqual((sb["alcance"], sb["n"]), ("campeon", 8))
        self.assertEqual(sb["cs"][10], 95)  # mediana de 60..130 de 10 en 10 = 95
        self.assertEqual(sombra.sombra(ss, "Ahri", "MIDDLE")["alcance"], "rol")  # sin victorias con Ahri: la de mid
        x = sombra.sombra(ss, "Sylas", "TOP")
        self.assertEqual((x["alcance"], x["n"], x["falta"], x["cs"]), (None, 0, 8, []))

    def test_solo_victorias_y_las_30_mas_recientes(self):
        for i in range(8): partida(self.d, i + 1, False, cs_min=20)
        self.assertIsNone(sombra.sombra(sombra.series(self.d), "Sylas", "MIDDLE")["alcance"])
        ss = [dict(win=True, pos="MIDDLE", champ="Sylas", t=i, cs=[i] * 36, nivel=[1] * 36, muertes=[0] * 36, kp=[None] * 36) for i in range(40)]
        sb = sombra.sombra(ss, "Sylas", "MIDDLE")
        self.assertEqual((sb["n"], sb["cs"][0]), (30, 24))  # 10..39: mediana 24,5 a la baja

    def test_minuto_con_pocas_partidas_corta_la_curva(self):
        ss = [dict(win=True, pos="MIDDLE", champ="Sylas", t=i, cs=[1] * (n := 20 if i < 5 else 30), nivel=[1] * n, muertes=[0] * n, kp=[None] * n) for i in range(8)]
        c = sombra.curvas(ss)
        self.assertEqual(len(c["cs"]), 20)  # solo 3 partidas pasan del 20
        self.assertEqual(c["kp"], [None] * 20)


class Guion(Base):
    def test_arma_guarda_y_lee_rapido(self):
        for i in range(10): partida(self.d, i + 1, i % 3 != 0, muertes=(3, 16, 18, 20) if i < 4 else (3,))
        os.environ["DATOS_DIR"] = str(self.d); orig = guion.ARCHIVO; guion.ARCHIVO = pathlib.Path(self.tmp.name) / "guion.json"
        try:
            sombra.series(self.d)  # índice caliente, como al fijar campeón tras la primera vez
            t = time.perf_counter(); g = guion.armar("Sylas", "Zed", "MIDDLE", regla={"metrica": "muertes", "ok": 6, "n": 10}, racha=2)
            self.assertLess(time.perf_counter() - t, 0.3)
            self.assertEqual(guion.leer("Sylas")["marcas"], g["marcas"]); self.assertIsNone(guion.leer("Ahri"))
        finally: guion.ARCHIVO = orig; os.environ.pop("DATOS_DIR", None)
        self.assertEqual(g["matchup"]["n"], 10); self.assertEqual(g["regla"]["corta"], "Tope 2 muertes · 14 a 25")
        self.assertEqual(g["marcas"]["25"], {"meta": 2, "ok": 6, "n": 10})  # 4 con 3 muertes del 14 al 25
        self.assertEqual(g["marcas"]["14"], {"meta": 0, "ok": 10, "n": 10})
        self.assertEqual(g["sombra"]["alcance"], None)  # 6 victorias: menos de 8

    def test_regla_corta_es_dato(self):
        verbos = re.compile(r"\b(juega|únete|pelea|no pelear|farmea|tradea|evita|busca|cuida|compra)\b")
        for m in list(guion.CORTA) + ["otra"]:
            c = guion.corta({"metrica": m}); self.assertFalse(verbos.search(c.lower()), c); self.assertLessEqual(len(c), 34)
        self.assertIsNone(guion.corta(None))


if __name__ == "__main__":
    unittest.main()
