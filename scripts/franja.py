"""La franja en su propio proceso (plan Sombra, fase 1): HTC.exe --franja <puerto> <token>, el mismo binario.
Si la franja se traba o se cae, HTC sigue. Habla con HTC por un socket local (127.0.0.1), un JSON por línea:
  HTC → franja: el estado que la franja necesita (fase, foto, ajustes, guion, modo mover), cuando cambia.
  franja → HTC: ["anotar", notas, marcas] (bitácora), ["guardar", clave, valor] (posición), ["registrar", texto] (errores).
Un socket y no stdin/stdout: el .exe es --windowed y ahí las tuberías estándar pueden no existir. Si HTC muere o cierra el
socket, la franja se cierra sola (nunca queda huérfana)."""
import json, socket, subprocess, sys, threading, time

ESPERA_CONEXION = 15  # s para que el hijo se conecte
VIDA_TRAS_PARTIDA = 15  # s que vive el hijo después de salir de partida (y del modo mover)
SIN_VENTANA = 0x08000000  # CREATE_NO_WINDOW: sin consola en Windows


def compacto(e):
    """Lo del estado de HTC que la franja usa (overlay.correr), sin el rendimiento entero."""
    r = e.get("rendimiento") or {}
    return {"fase": e.get("fase"), "meta": e.get("meta"), "ajustes": e.get("ajustes"), "guion": e.get("guion"), "aviso": e.get("aviso"),
            "mover_franja": e.get("mover_franja"),
            "rendimiento": {"vistas": {"regla_hoy": (r.get("vistas") or {}).get("regla_hoy")}, "resumen": {"racha_oro14": (r.get("resumen") or {}).get("racha_oro14")}}}


def hace_falta(e):
    """¿Debe vivir la franja? En partida (o reconectando) con la franja prendida, o en modo mover."""
    return bool(e.get("mover_franja")) or ((e.get("ajustes") or {}).get("overlay", True) is not False and e.get("fase") in ("InProgress", "Reconnect"))


def comando(puerto, token):
    """Cómo lanzar el hijo: el mismo .exe, o este Python con companion_web.py en desarrollo."""
    import pathlib
    if getattr(sys, "frozen", False): return [sys.executable, "--franja", str(puerto), token]
    return [sys.executable, str(pathlib.Path(__file__).resolve().parent / "companion_web.py"), "--franja", str(puerto), token]


class Hijo:
    """El lado de HTC: lanza el proceso, le manda el estado y recibe lo que la franja devuelve."""

    def __init__(self, al_recibir, lanzar=None):
        import secrets
        self.al_recibir, self.lanzar = al_recibir, lanzar or (lambda cmd: subprocess.Popen(cmd, creationflags=SIN_VENTANA if sys.platform == "win32" else 0,
                                                                                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        self.token, self.proc, self.con, self.ultimo = secrets.token_hex(16), None, None, None

    def arrancar(self):
        """Lanza el hijo y espera a que se conecte con el token; True si quedó conectado."""
        srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1); srv.settimeout(ESPERA_CONEXION)
        try:
            self.proc = self.lanzar(comando(srv.getsockname()[1], self.token))
            fin = time.time() + ESPERA_CONEXION
            while time.time() < fin:
                c, _ = srv.accept(); c.settimeout(5)
                r = c.makefile("r", encoding="utf-8", newline="\n")  # uno para leer y otro para escribir: compartido entre hilos se traba
                if r.readline().strip() == self.token:  # otro programa local no puede hacerse pasar por la franja
                    c.settimeout(None); self.con, self.r, self.f = c, r, c.makefile("w", encoding="utf-8", newline="\n")
                    threading.Thread(target=self._leer, daemon=True).start(); return True
                c.close()
        except OSError: pass
        finally: srv.close()
        self.cerrar(); return False

    def _leer(self):
        try:
            for linea in self.r:
                try: m = json.loads(linea)
                except ValueError: continue
                if isinstance(m, list) and m: self.al_recibir(m)
        except (OSError, ValueError): pass

    def enviar(self, estado):
        """Manda el estado si cambió; False si el hijo ya no está."""
        txt = json.dumps(estado, ensure_ascii=False, default=str)
        if txt == self.ultimo: return self.vivo()
        try: self.f.write(txt + "\n"); self.f.flush(); self.ultimo = txt; return True
        except (OSError, ValueError, AttributeError): return False

    def vivo(self):
        return self.con is not None and (self.proc is None or self.proc.poll() is None)

    def cerrar(self):
        """Cierra el socket (el hijo se cierra solo al notarlo) y, si en 3 s no salió, lo termina."""
        try: self.con and self.con.shutdown(socket.SHUT_RDWR)  # despierta al hilo que lee
        except OSError: pass
        for x in (getattr(self, "f", None), getattr(self, "r", None), self.con):
            try: x and x.close()
            except OSError: pass
        self.con = None
        if self.proc and self.proc.poll() is None:
            try: self.proc.wait(3)
            except subprocess.TimeoutExpired: self.proc.kill()


def vigilar(leer_estado, al_recibir, seguir, registrar=lambda t: None, caida=lambda: None, nuevo=Hijo, paso=0.1):
    """Hilo de HTC: lanza la franja al entrar en partida, le pasa el estado al instante y la cierra 15 s después de salir.
    Si se cae, la relanza una vez; si vuelve a caer, HTC sigue sin franja (caida())."""
    hijo, fallos, desde = None, 0, None
    while seguir():
        e = leer_estado()
        if hace_falta(e): desde = time.time()
        quiere = desde is not None and time.time() - desde < VIDA_TRAS_PARTIDA
        if quiere and hijo is None and fallos < 2:
            hijo = nuevo(al_recibir)
            if not hijo.arrancar(): fallos += 1; registrar(f"franja: no arrancó (intento {fallos})"); hijo = None
        if hijo is not None:
            if not quiere: hijo.cerrar(); hijo = None
            elif not hijo.enviar(compacto(e)) or not hijo.vivo():
                fallos += 1; registrar(f"franja: se cayó (vez {fallos})"); hijo.cerrar(); hijo = None
                if fallos >= 2: caida()
        time.sleep(paso)
    if hijo: hijo.cerrar()


def main(argv):
    """El proceso hijo: se conecta a HTC y corre la franja (overlay.correr) con el estado que llega por el socket."""
    puerto, token = int(argv[0]), argv[1]
    con = socket.create_connection(("127.0.0.1", puerto), timeout=10); con.settimeout(None)
    r, f = con.makefile("r", encoding="utf-8", newline="\n"), con.makefile("w", encoding="utf-8", newline="\n")
    f.write(token + "\n"); f.flush()
    estado, vivo, lock = [{}], [True], threading.Lock()

    def leer_socket():
        try:
            for linea in r:
                try: d = json.loads(linea)
                except ValueError: continue
                if isinstance(d, dict): estado[0] = d
        except (OSError, ValueError): pass
        vivo[0] = False  # HTC cerró o murió: la franja se cierra en el siguiente tick

    def mandar(*m):
        with lock:
            try: f.write(json.dumps(list(m), ensure_ascii=False) + "\n"); f.flush()
            except (OSError, ValueError): vivo[0] = False

    def icono(tipo, nombre):  # retratos de la pastilla clásica, de la misma caché de imágenes de HTC
        try: import companion_web; return companion_web.imagen(tipo, nombre)
        except Exception: return None

    threading.Thread(target=leer_socket, daemon=True).start()
    import overlay
    overlay.correr(lambda: estado[0], lambda: vivo[0], registrar=lambda t: mandar("registrar", t), icono=icono,
                   guardar=lambda k, v: mandar("guardar", k, v), anotar=lambda n, m: mandar("anotar", n, m))
    try: con.close()
    except OSError: pass
    return 0
