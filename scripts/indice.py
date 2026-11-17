"""Índice en SQLite de lo que Racha calcula por partida (datos/cache/partidas.db). Los JSON de datos/raw siguen siendo la
fuente: esto solo evita releerlos y recalcular. Cada fila vale mientras no cambien la partida, su timeline ni la versión
(el sha1 del código que calcula): no hay que acordarse de invalidar nada. Si la db se daña se borra y se rehace; si no se
puede (sin sqlite3, carpeta de solo lectura, otra instancia la tiene tomada), se calcula directo, como antes."""
import hashlib, json, os, pathlib, threading

try: import sqlite3
except ImportError: sqlite3 = None  # un .exe viejo sin sqlite3 con scripts nuevos (autoactualización): sin índice

DB = pathlib.Path(os.environ.get("RACHA_INDICE") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "cache" / "partidas.db")
_LOCK = threading.Lock()
_CON = [None, False]  # [conexión, apagado en este proceso]


def version(*partes):
    """sha1 corto de archivos de código (Path) y textos (puuid...): cambia si cambia la fórmula o la cuenta."""
    h = hashlib.sha1()
    for p in partes: h.update(p.read_bytes() if isinstance(p, pathlib.Path) else str(p).encode())
    return h.hexdigest()[:16]


def _firma(f, ver):
    tl = f.parent / "timeline" / f.name
    s = f.stat()
    try: t = tl.stat(); t = f"{t.st_mtime_ns}:{t.st_size}"
    except OSError: t = "0"  # sin timeline: cuando llegue, la firma cambia y se recalcula
    return f"{s.st_mtime_ns}:{s.st_size}:{t}:{ver}"


def _apagar():
    con, _CON[:] = _CON[0], [None, True]
    try: con and con.close()
    except Exception: pass


def _abrir():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB), timeout=5, isolation_level=None, check_same_thread=False)
    try:
        con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA synchronous=NORMAL")
        con.execute("CREATE TABLE IF NOT EXISTS d (ruta TEXT, tipo TEXT, firma TEXT, valor TEXT, PRIMARY KEY (ruta, tipo))")
        huerfanas = [(r,) for (r,) in con.execute("SELECT DISTINCT ruta FROM d") if not os.path.exists(r)]  # partidas borradas, tempdirs
        if huerfanas: con.executemany("DELETE FROM d WHERE ruta = ?", huerfanas)
        return con
    except BaseException:
        con.close(); raise  # cerrada: si no, Windows no deja borrar la db dañada


def _conexion():
    if _CON[0] or _CON[1] or sqlite3 is None: return _CON[0]
    for intento in (1, 2):
        try: _CON[0] = _abrir(); return _CON[0]
        except sqlite3.DatabaseError:  # dañada: se borra y se rehace una vez (es caché)
            if intento == 2: break
            for x in (DB, DB.with_name(DB.name + "-wal"), DB.with_name(DB.name + "-shm")):
                try: x.unlink(missing_ok=True)
                except OSError: break  # otra instancia la tiene abierta: sin índice en este proceso
        except OSError: break  # carpeta de solo lectura o ruta imposible
    _apagar(); return None


def derivado(f, tipo, ver, calc):
    """calc() de la partida f (debe dar algo serializable a JSON), desde el índice si nada cambió. Siempre devuelve lo
    que daría el JSON (tuplas → listas, sets no), esté o no en el índice, para que frío y caliente den lo mismo."""
    f = pathlib.Path(f)
    try: firma = _firma(f, ver)
    except OSError: return json.loads(json.dumps(calc()))
    with _LOCK:
        con = _conexion()
        if con:
            try:
                fila = con.execute("SELECT firma, valor FROM d WHERE ruta = ? AND tipo = ?", (str(f), tipo)).fetchone()
                if fila and fila[0] == firma: return json.loads(fila[1])
            except (sqlite3.Error, ValueError): _apagar(); con = None
    texto = json.dumps(calc())
    with _LOCK:
        if (con := _CON[0]):
            try: con.execute("INSERT OR REPLACE INTO d VALUES (?, ?, ?, ?)", (str(f), tipo, firma, texto))
            except sqlite3.Error: _apagar()
    return json.loads(texto)
