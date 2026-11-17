"""franja.py: la franja en su propio proceso. Protocolo por socket con token, relanzar una vez, sin franja tras dos caídas."""
import pathlib as _p, sys as _s; _s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import threading, time, unittest
from unittest import mock

import franja, overlay


class Partes(unittest.TestCase):
    def test_compacto_y_hace_falta(self):
        e = {"fase": "InProgress", "meta": {"t": 1}, "ajustes": {}, "rendimiento": {"vistas": {"regla_hoy": {"tope": 2}, "otra": 1}, "resumen": {"partidas": [1] * 100}}, "draft": "x"}
        c = franja.compacto(e)
        self.assertNotIn("draft", c); self.assertEqual(c["rendimiento"]["vistas"], {"regla_hoy": {"tope": 2}})
        self.assertTrue(franja.hace_falta(e)); self.assertTrue(franja.hace_falta({"mover_franja": True}))
        self.assertFalse(franja.hace_falta({**e, "ajustes": {"overlay": False}})); self.assertFalse(franja.hace_falta({"fase": "Lobby"}))

    def test_comando_en_desarrollo(self):
        c = franja.comando(1234, "tok")
        self.assertEqual(c[-3:], ["--franja", "1234", "tok"]); self.assertTrue(c[1].endswith("companion_web.py"))


class Falso:
    """Un hijo de mentira: arranca o no, y se cae cuando se le dice."""
    def __init__(self, guion): self.guion = guion
    def __call__(self, al_recibir): return self
    def arrancar(self): return self.guion.pop(0) if self.guion else False
    def enviar(self, e): return not getattr(self, "caer", False)
    def vivo(self): return True
    def cerrar(self): pass


class Vigilar(unittest.TestCase):
    def correr(self, nuevo, segundos=0.3, estado=None):
        log, caidas, fin = [], [], time.time() + segundos
        franja.vigilar(lambda: estado or {"fase": "InProgress"}, lambda m: None, lambda: time.time() < fin, log.append, lambda: caidas.append(1), nuevo, paso=0.01)
        return log, caidas

    def test_si_no_arranca_dos_veces_no_insiste(self):
        log, _ = self.correr(Falso([False, False, True]))
        self.assertEqual(log, ["franja: no arrancó (intento 1)", "franja: no arrancó (intento 2)"])

    def test_se_cae_se_relanza_una_vez_y_luego_sin_franja(self):
        h = Falso([True, True]); h.caer = True
        log, caidas = self.correr(h)
        self.assertEqual(log, ["franja: se cayó (vez 1)", "franja: se cayó (vez 2)"]); self.assertEqual(caidas, [1])

    def test_fuera_de_partida_no_arranca(self):
        h = Falso([True]); log, _ = self.correr(h, estado={"fase": "Lobby"})
        self.assertEqual(h.guion, [True])


class Protocolo(unittest.TestCase):
    def test_token_estado_y_respuesta(self):
        """El hijo real (franja.main en un hilo) con overlay.correr de mentira: recibe el estado y devuelve una anotación."""
        recibidos, vistos = [], []

        def correr_falso(leer, seguir, anotar=None, **k):
            fin = time.time() + 5
            while seguir() and time.time() < fin and not leer().get("meta"): time.sleep(0.01)
            vistos.append(leer()); anotar([{"id": "marca6"}], {"6": True})
            while seguir() and time.time() < fin: time.sleep(0.01)

        def lanzar(cmd):
            threading.Thread(target=franja.main, args=(cmd[-2:],), daemon=True).start(); return None

        with mock.patch.object(overlay, "correr", correr_falso):
            h = franja.Hijo(recibidos.append, lanzar=lanzar)
            self.assertTrue(h.arrancar())
            self.assertTrue(h.enviar({"fase": "InProgress", "meta": {"t": 361}}))
            fin = time.time() + 5
            while not recibidos and time.time() < fin: time.sleep(0.01)
            h.cerrar()
        self.assertEqual(vistos[0]["meta"], {"t": 361})
        self.assertEqual(recibidos, [["anotar", [{"id": "marca6"}], {"6": True}]])

    def test_otro_programa_sin_token_no_entra(self):
        import socket
        def lanzar(cmd):
            def intruso():
                c = socket.create_connection(("127.0.0.1", int(cmd[-2]))); c.sendall(b"otro\n"); time.sleep(0.5); c.close()
            threading.Thread(target=intruso, daemon=True).start(); return None
        with mock.patch.object(franja, "ESPERA_CONEXION", 1):
            self.assertFalse(franja.Hijo(lambda m: None, lanzar=lanzar).arrancar())


if __name__ == "__main__":
    unittest.main()
