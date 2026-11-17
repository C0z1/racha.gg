"""momentos.py: el motor de Sombra. Contrato de atención (máx. 3, nunca en pelea, nada después del 25), marcas y textos."""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import re, unittest

import momentos as M

G = {"campeon": "Sylas", "rival": "Zed", "pos": "MIDDLE",
     "sombra": {"alcance": "campeon", "n": 20, "cs": [8 * i for i in range(36)], "nivel": [1] * 36, "muertes": [0] * 6 + [1] * 30, "kp": [0.4] * 36},
     "marcas": {"6": {"meta": 1, "ok": 7, "n": 10}, "10": {"meta": 80, "ok": 5, "n": 10}, "14": {"meta": 0, "ok": 6, "n": 10}, "25": {"meta": 2, "ok": 4, "n": 10}},
     "regla": {"corta": "Tope 2 muertes · 14 a 25", "tope": 2, "ok": 6, "n": 10, "racha": 3}, "matchup": {"v": 4, "n": 7, "nota": None}}


def foto(t, **k):
    f = dict(t=t, campeon="Sylas", rival="Zed", nivel=5, nivel_rival=5, cs=int(8 * t / 60) // 10 * 10, vida=1.0, ult_kill=None, muertes=0,
             muertes6=0, muertes14=0 if t >= 840 else None, muertes14_25=0 if t >= 840 else None, participacion=0.5, muerto=False, items=[], oro={"tu": 5000, "rival": 4800})
    f.update(k); return f


def correr(fotos, g=G, aj=None, cada=1):
    """[(escena, notas)] con el reloj local = el de juego."""
    e, out = None, []
    for f in fotos:
        e, esc, n = M.paso(e, f, g, f["t"], aj); out.append((esc, n))
    return e, out


def mostradas(out): return [a for _, ns in out for a in ns if a["clase"] == "interrupcion" and a["mostrado"]]


class Contrato(unittest.TestCase):
    def test_nivel_abajo_sale_una_vez_y_con_calma(self):
        e, out = correr([foto(t, nivel=5, nivel_rival=6) for t in range(300, 330)])
        self.assertEqual([a["dato"] for a in mostradas(out)], ["Nivel -1 vs Zed"])

    def test_nunca_en_pelea_espera_la_calma(self):
        fs = [foto(t, nivel=5, nivel_rival=6, vida=1.0 - 0.05 * (t - 296)) for t in range(296, 306)]  # perdiendo vida: pelea
        fs += [foto(t, nivel=5, nivel_rival=6, vida=0.7) for t in range(306, 320)]
        e, out = correr(fs)
        a = mostradas(out); self.assertEqual(len(a), 1)
        self.assertGreaterEqual(a[0]["t"], 305 + M.CALMA_S)  # 6 s después de la última caída

    def test_kill_reciente_es_pelea(self):
        e = M.nuevo(); f = foto(400, ult_kill=395)
        self.assertTrue(M.en_pelea(e, f, 400)); self.assertFalse(M.en_pelea(e, foto(400, ult_kill=380), 400))

    def test_sin_calma_en_45_s_no_se_muestra_y_queda_el_motivo(self):
        fs = [foto(t, nivel=5, nivel_rival=6, ult_kill=t - 1) for t in range(300, 360)]
        e, out = correr(fs)
        self.assertEqual(mostradas(out), [])
        self.assertIn("en pelea", [a["motivo"] for _, ns in out for a in ns if a["clase"] == "interrupcion"])

    def test_maximo_3_y_120_s_entre_ellas(self):
        e = M.nuevo(); vistas = []
        for i in range(6):
            f = foto(300 + i * 130, avisos=[(f"pico:{i}:x", f"Zed {i} ítems vs 0 tuyos")])
            e, esc, ns = M.paso(e, f, G, f["t"]); vistas += [a for a in ns if a["mostrado"] and a["clase"] == "interrupcion"]
        self.assertEqual(len(vistas), 3)
        self.assertEqual(e["interrupciones"], 3)

    def test_nada_despues_del_25_ni_con_solo_marcas(self):
        _, out = correr([foto(t, avisos=[("pico:1:x", "Zed 1 ítem vs 0 tuyos")]) for t in range(1500, 1520)])
        self.assertEqual(mostradas(out), [])
        _, out = correr([foto(t, nivel=5, nivel_rival=6) for t in range(300, 330)], aj={"solo_marcas": True})
        self.assertEqual(mostradas(out), [])
        _, out = correr([foto(t, nivel=5, nivel_rival=6) for t in range(300, 330)], aj={"momento_nivel": False})
        self.assertEqual(mostradas(out), [])

    def test_muerto_es_buena_ventana_y_va_al_panel(self):
        fs = [foto(t, muerto=True, revive=20, ult_kill=299) for t in range(300, 310)]
        for f in fs: f["nivel_rival"] = 7  # nivel abajo al morir
        e, out = correr(fs)
        self.assertEqual(len(mostradas(out)), 1)
        self.assertIn("Nivel -2 vs Zed", out[3][0]["panel"])  # 2 s después de morir: el panel lo lleva
        self.assertIsNone(out[3][0]["renglon"])


class Marcas(unittest.TestCase):
    def test_se_sellan_en_su_minuto(self):
        e, out = correr([foto(t) for t in range(355, 365)])
        sellos = [a for _, ns in out for a in ns if a["clase"] == "sello"]
        self.assertEqual([(a["id"], a["mostrado"]) for a in sellos], [("marca6", True)])
        self.assertIs(e["marcas"]["6"], True)
        self.assertEqual(out[-1][0]["marcas"][0]["estado"], True)
        self.assertTrue(out[5][0]["renglon"].startswith("Marca 6"))  # 4 s, luego se va
        self.assertIsNone(out[-1][0]["renglon"])

    def test_marca_10_sin_foto_cerca_queda_sin_dato(self):
        e, _ = correr([foto(500), foto(700)])
        self.assertIsNone(e["marcas"]["10"]); self.assertIs(e["marcas"]["6"], True)

    def test_marca_25_contra_tu_tope(self):
        e, out = correr([foto(1490, muertes14=3, muertes14_25=3), foto(1501, muertes14=3, muertes14_25=3)])
        self.assertIs(e["marcas"]["25"], False)
        self.assertEqual(out[-1][0]["regla"]["color"], "rojo")
        self.assertEqual(out[-1][0]["opacidad"], M.OPACIDAD_TARDE)


class Escena(unittest.TestCase):
    def test_zonas_fijas_y_pocas_palabras(self):
        _, out = correr([foto(t) for t in range(0, 2400, 7)])
        for esc, _ in out:
            self.assertEqual([m["min"] for m in esc["marcas"]], [6, 10, 14, 25])
            self.assertLessEqual(M.palabras_vivo(esc), 9)
            if esc["renglon"]: self.assertLessEqual(len(esc["renglon"]), M.RENGLON_MAX)
        verbos = re.compile(r"\b(juega|únete|pelea|farmea|tradea|evita|busca|cuida|compra)\b")
        self.assertFalse([x for esc, _ in out for x in M.textos(esc) if verbos.search(x.lower())])

    def test_sombra_cs_y_peleas(self):
        _, out = correr([foto(600, cs=70)])  # sombra 80 al 10; tu CS ~75
        self.assertEqual((out[0][0]["sombra"]["num"], out[0][0]["sombra"]["color"]), ("-5", "oro"))
        _, out = correr([foto(1000, participacion=0.5)])
        self.assertEqual(out[0][0]["sombra"]["num"], "+10%")

    def test_sin_sombra_y_arranque(self):
        g = {**G, "sombra": {"alcance": None, "n": 3, "falta": 5, "cs": [], "nivel": [], "muertes": [], "kp": []}}
        _, out = correr([foto(30)], g=g)
        self.assertEqual(out[0][0]["sombra"]["etq"], "Sin sombra aún · 3 de 8")
        _, out = correr([foto(30)])
        self.assertEqual(out[0][0]["renglon"], "vs Zed · 4 de 7 tuyas")

    def test_aram_y_partida_nueva(self):
        e, esc, _ = M.paso(None, {"modo": "ARAM", "t": 100}, G, 0)
        self.assertIsNone(esc)
        e, _ = correr([foto(400)]); e2, _, _ = M.paso(e, foto(10), G, 1000)
        self.assertEqual(e2["marcas"], {})

    def test_cartas(self):
        c = M.carta_carga(G)
        self.assertEqual(c[0], "Sylas vs Zed · 4 de 7 tuyas"); self.assertIn("la cumples 6 de 10", c[1]); self.assertIn("racha 3", c[2])
        self.assertEqual(M.carta_fin({"marcas": {"6": True, "10": False, "14": True, "25": None}}, True, 4), ["2 de 4 marcas", "Tu regla: cumplida · racha 4"])


if __name__ == "__main__":
    unittest.main()
