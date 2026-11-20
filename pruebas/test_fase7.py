"""Fase 7 de Sombra: tus errores con un solo detector (timeline y en vivo), el plan de tu rol, las marcas personales, el panel
al morir y el ciclo de corrección de errores."""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import copy, pathlib, tempfile, unittest

import ciclo, errores, guion, momentos as M, plan_rol

K = lambda t, victima="rival", mio=False: {"t": t, "k": "kill", "victima": victima, "mio": mio}
O = lambda t, nuestro=True: {"t": t, "k": "obj", "nuestro": nuestro}


class Detector(unittest.TestCase):
    def test_sin_objetivo(self):
        ev = [K(900, "yo", True), K(1000, "yo", True), O(1030), K(1600, "yo", True)]
        self.assertEqual(errores.sin_objetivo(ev), [900])  # la de 1000 tuvo objetivo; la de 1600, fuera de ventana
        self.assertEqual(errores.sin_objetivo(ev, hasta=930), [])  # hace < 60 s: aún puede caer un objetivo
        self.assertEqual(errores.sin_objetivo([K(900, "yo", True), O(890, nuestro=False)]), [900])  # el del rival no cuenta

    def test_abajo_6(self):
        ev = [K(320, mio=True), K(350, mio=True), K(380, mio=True)]
        self.assertEqual(errores.abajo_6(ev, (5, 6)), [350]); self.assertEqual(errores.abajo_6(ev, (6, 6)), []); self.assertEqual(errores.abajo_6(ev, None), [])

    def test_sin_pelea(self):
        pelea = [K(900, "aliado"), K(910, "aliado"), K(920, "rival")]
        self.assertEqual(errores.sin_pelea(pelea), [900])
        self.assertEqual(errores.sin_pelea(pelea[:2] + [K(920, "rival", mio=True)]), [])  # estuviste
        self.assertEqual(errores.sin_pelea(pelea, hasta=940), [])  # puede seguir
        self.assertEqual(errores.sin_pelea([K(900, "aliado"), K(905, "rival"), K(911, "rival")]), [])  # la ganaron

    def test_las_dos_fuentes_dan_lo_mismo(self):
        """La misma partida contada por el timeline y por la Live Client Data: mismos eventos comunes."""
        fr = [{"events": [{"type": "CHAMPION_KILL", "timestamp": 900000, "killerId": 6, "victimId": 1, "assistingParticipantIds": [7]},
                          {"type": "ELITE_MONSTER_KILL", "timestamp": 950000, "killerTeamId": 200},
                          {"type": "BUILDING_KILL", "timestamp": 960000, "teamId": 100},  # cayó una torre tuya
                          {"type": "CHAMPION_KILL", "timestamp": 970000, "killerId": 2, "victimId": 8, "assistingParticipantIds": [1]}]}]
        tl = errores.de_timeline(fr, 1, {i: 100 if i <= 5 else 200 for i in range(1, 11)})
        jug = lambda n, eq, c: {"riotId": f"{n}#LA1", "riotIdGameName": n, "summonerName": n, "team": eq, "championName": c}
        d = {"activePlayer": {"riotId": "Yo#LA1", "riotIdGameName": "Yo"},
             "allPlayers": [jug("Yo", "ORDER", "Sylas"), jug("Ami", "ORDER", "Lee Sin"), jug("Riv", "CHAOS", "Zed"), jug("Otro", "CHAOS", "Kayn"), jug("Tres", "CHAOS", "Lux")],
             "events": {"Events": [{"EventName": "ChampionKill", "EventTime": 900.0, "KillerName": "Riv", "VictimName": "Yo", "Assisters": ["Otro"]},
                                   {"EventName": "DragonKill", "EventTime": 950.0, "KillerName": "Kayn", "Assisters": []},  # a veces el campeón
                                   {"EventName": "TurretKilled", "EventTime": 960.0, "KillerName": "Minion_T200", "TurretKilled": "Turret_TOrder_L1_P3_1_0"},
                                   {"EventName": "ChampionKill", "EventTime": 970.0, "KillerName": "Ami", "VictimName": "Tres", "Assisters": ["Yo"]}]}}
        self.assertEqual(errores.de_vivo(d), tl)


class Plan(unittest.TestCase):
    def serie(self, win, muertes6, cs10):
        return {"win": win, "pos": "MIDDLE", "muertes": [0] * 6 + [muertes6] * 30, "cs": [8 * i for i in range(10)] + [cs10] * 26,
                "kp": [0.3] * 36, "nivel": [1] * 36, "nivel_rival": [1] * 36, "dragones14": 1}

    def test_elige_las_fases_que_separan(self):
        ss = [self.serie(True, 0, 80) for _ in range(10)] + [self.serie(False, 2, 80) for _ in range(10)]
        p = plan_rol.plan(ss, "MIDDLE")
        self.assertEqual([m["id"] for m in p["marcas"]], ["muertes6", "muertes14"])  # el CS no separa: no entra
        self.assertEqual(p["fases"][1]["dato"], "muertes al 6: victorias 0 · derrotas 2")
        self.assertIsNone(plan_rol.plan(ss[:12], "MIDDLE"))  # menos de 8 derrotas
        self.assertTrue(plan_rol.cumple("muertes6", 0, 0.5)); self.assertFalse(plan_rol.cumple("cs10", 60, 71))

    def test_con_15_por_lado_elige_por_tu_wr(self):  # el renglón dice el umbral y tu WR al cumplirlo
        ss = [self.serie(True, 0, 80) for _ in range(20)] + [self.serie(False, 2, 80) for _ in range(20)]
        p = plan_rol.plan(ss, "MIDDLE"); m = p["fases"][1]
        self.assertEqual((m["id"], m["v"], m["wr"]), ("muertes6", 1, 1.0))
        self.assertEqual(plan_rol.renglon(m), "≤1 muerte al 6: ganas 100%")
        self.assertEqual(plan_rol.umbral("dragones14", 1), "≥1 dragón al 14"); self.assertEqual(plan_rol.umbral("muertes6", 0), "0 muertes al 6"); self.assertEqual(plan_rol.umbral("nivel3", 0), "sin nivel abajo al 3")

    def test_marcas_personales(self):
        plan = {"marcas": [{"id": "cs10", "minuto": 10, "v": 71, "etq": "CS al 10", "dato": "x"}]}
        er = {"ciclo": {"vigilados": ["sin_objetivo"], "errores": {"sin_objetivo": {"veces": 13, "ok": 2, "n": 10}}}}
        ms = guion.personales(plan, er, {"6": {"meta": 1}}, [{"cs": [70] * 12}] * 3)
        self.assertEqual([(m["tipo"], m["etq"]) for m in ms], [("fija", "6"), ("plan", "10"), ("fija", "14"), ("error", "E1")])
        self.assertEqual(ms[1]["corto"], "Tus victorias: 71 CS al 10"); self.assertEqual((ms[1]["ok"], ms[1]["n"]), (0, 3))
        self.assertEqual(guion.personales(None, None, {}, []), sorted(guion.personales(None, None, {}, []), key=lambda m: m["min"]))  # sin nada: las 4 fijas


G = {"campeon": "Sylas", "rival": "Zed", "regla": {"tope": 2}, "sombra": {}, "marcas": {}, "muerte_comun": "gank",
     "plan": {"fases": {"2": {"id": "cs10", "etq": "CS al 10", "v": 71}}},
     "marcas_p": [{"id": "cs10", "tipo": "plan", "etq": "10", "min": 600, "meta": 71, "nombre": "CS al 10"},
                  {"id": "6", "tipo": "fija", "etq": "6", "min": 360},
                  {"id": "sin_objetivo", "tipo": "error", "etq": "E1", "rango": 1, "ventana": [840, 1500], "min": 1560, "nombre": "Muerte sin objetivo", "veces": 13},
                  {"id": "abajo_6", "tipo": "error", "etq": "E2", "rango": 2, "ventana": [330, 420], "min": 420, "nombre": "Nivel abajo al 6", "veces": 2}]}


def foto(t, **k): return {"t": t, "nivel": 6, "nivel_rival": 6, "cs": 70, "items": [], "eventos": [], **k}


class Motor(unittest.TestCase):
    def test_frases_caben_y_se_leen(self):
        extremos = {"kp6": 1.0, "kp25": 1.0, "muertes6": 10, "muertes14": 10, "muertes14_25": 10, "cs10": 175, "dragones14": 4, "nivel3": -1.5, "nivel10": -1.5}
        for k, v in extremos.items():
            self.assertLessEqual(len("Tus victorias: " + plan_rol.frase(k, v)), M.RENGLON_MAX, k)
            self.assertLessEqual(len("≈" + plan_rol.frase(k, v) + " · sin cumplir"), M.RENGLON_MAX, k)
        self.assertEqual(plan_rol.frase("dragones14", 1), "1 dragón al 14"); self.assertEqual(plan_rol.frase("kp6", .25), "25% en kills al 6")

    def test_plan_y_fase(self):
        e, esc, n = M.paso(None, foto(361), G, 361)
        self.assertEqual(esc["renglon"], "Tus victorias: 71 CS al 10")
        e, esc, n = M.paso(e, foto(601, cs=70), G, 601)
        self.assertIs(e["marcas"]["cs10"], True)  # 70 en vivo ≈ 75 reales ≥ 71
        self.assertTrue(esc["renglon"].startswith("≈75 CS al 10 · cumplida"))
        self.assertEqual([x["motivo"] for x in n if x["clase"] == "sello"], [None, "otro sello"])  # abajo_6 evitado en la misma foto
        self.assertEqual([m["etq"] for m in esc["marcas"]], ["10", "6", "E1", "E2"])

    def test_error_se_marca_sin_interrumpir_y_el_evitado_al_cerrar(self):
        e, esc, n = M.paso(None, foto(365, nivel=5, nivel_rival=6), G, 365)
        self.assertEqual(e["nivel6"], [5, 6])
        e, esc, n = M.paso(e, foto(380, nivel=5, nivel_rival=6, eventos=[K(375, "rival", True)]), G, 380)
        self.assertIs(e["marcas"]["abajo_6"], False)
        self.assertEqual([(x["clase"], x["mostrado"]) for x in n], [("error", False), ("sello", False)])
        self.assertIsNone(esc["renglon"])  # sin interrumpir: el punto se pone rojo y ya
        e2, _, n2 = M.paso(copy.deepcopy(e), foto(1561, muerto=True), G, 1561)
        self.assertNotIn("sin_objetivo", e2["marcas"]); self.assertFalse([x for x in n2 if "evitado" in (x["dato"] or "")])  # muerto: el «evitado» espera
        e, esc, n = M.paso(e, foto(1561), G, 1561)
        self.assertIs(e["marcas"]["sin_objetivo"], True); self.assertEqual(esc["renglon"], "Muerte sin objetivo: evitado")

    def test_zona_regla_antes_del_error(self):
        _, esc, _ = M.paso(None, foto(340, nivel=5, nivel_rival=6), G, 340)
        self.assertEqual((esc["regla"]["etq"], esc["regla"]["color"]), ("Nivel -1 · E2", "oro"))
        self.assertLessEqual(M.palabras_vivo(esc), 9)

    def test_panel_al_morir(self):
        e, _, _ = M.paso(None, foto(900, muerto=True, revive=20), G, 900)
        _, esc, _ = M.paso(e, foto(903, muerto=True, revive=17), G, 903)
        self.assertEqual(esc["panel"][0], "Sin objetivo del equipo · error 1")
        _, esc, _ = M.paso(e, foto(903, muerto=True, revive=17, eventos=[O(880)]), G, 903)
        self.assertEqual(esc["panel"][0], "Objetivo de tu equipo · min 14")
        e, _, _ = M.paso(None, foto(700, muerto=True, revive=20), G, 700)
        _, esc, _ = M.paso(e, foto(703, muerto=True, revive=17), G, 703)
        self.assertEqual(esc["panel"][0], "Tu muerte más común: gank")

    def test_la_bitacora_anota_todos_los_errores(self):
        ev = [K(900, "aliado"), K(910, "aliado"), K(920, "rival")]
        _, _, n = M.paso(None, foto(960, eventos=ev), G, 960)
        self.assertIn(("sin_pelea", "error"), [(x["id"], x["clase"]) for x in n])  # no vigilado, pero queda para la revisión

    def test_carta_con_plan_y_errores(self):
        c = M.carta_carga({**G, "matchup": {"v": 4, "n": 7}, "regla": {"tope": 2, "racha": 2}})
        self.assertEqual(c[-2:], ["Tu plan: 71 CS al 10", "Vigilas: E1 muerte sin objetivo · E2 nivel abajo al 6"])
        import lienzo
        self.assertEqual(lienzo.pintar_carta(c).size, (lienzo.CARTA_W, lienzo.CARTA_H + lienzo.CARTA_RENGLON))


class CicloErrores(unittest.TestCase):
    def test_vigilados_y_corregidos(self):
        e = {"revisadas": [f"p{i}" for i in range(10)], "partidas": {"sin_objetivo": 6, "abajo_6": 1, "sin_pelea": 3},
             "momentos": {"sin_objetivo": [{"archivo": f"p{i}"} for i in range(6)], "abajo_6": [{"archivo": "p9"}], "sin_pelea": [{"archivo": f"p{i}"} for i in (0, 4, 8)]}}
        with tempfile.TemporaryDirectory() as d:
            orig, ciclo.ARCHIVO = ciclo.ARCHIVO, pathlib.Path(d) / "c.json"
            try:
                c = ciclo.errores(e)
                self.assertEqual(c["corregidos"], ["abajo_6"])  # lo evitaste 9 de 10
                self.assertEqual(c["vigilados"], ["sin_objetivo", "sin_pelea"])
                self.assertEqual((c["errores"]["sin_objetivo"]["ok"], c["errores"]["sin_objetivo"]["racha"]), (4, 0))  # p0, la más reciente, lo tuvo
                self.assertEqual(ciclo.leer()["errores_corregidos"], ["abajo_6"])
                ciclo.actualizar([], {})  # la regla no borra lo de los errores
                self.assertEqual(ciclo.leer()["errores_corregidos"], ["abajo_6"])
            finally: ciclo.ARCHIVO = orig
        self.assertEqual(ciclo.errores({}), {"errores": {}, "vigilados": [], "corregidos": []})


if __name__ == "__main__":
    unittest.main()
