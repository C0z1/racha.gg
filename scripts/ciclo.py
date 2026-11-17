"""El ciclo de tu regla (plan Sombra): la racha (partidas seguidas en que la cumples) y la graduación. Una regla cumplida 8 de
tus últimas 10 se gradúa y tu regla de hoy pasa a la siguiente que más fallas; una graduada que baja de 5 de 10 regresa
(histéresis: no oscila entre 7 y 8). Lo graduado se guarda en datos/cache/ciclo.json."""
import json, os, pathlib

ARCHIVO = pathlib.Path(os.environ.get("RACHA_CICLO") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "cache" / "ciclo.json")
VENTANA, GRADUA, REGRESA = 10, 8, 5


def estado(gs, reglas, graduadas=()):
    """{metrica: {ok, n, racha, graduada, falta}} con gs de la más vieja a la más reciente y reglas = {metrica: (campo, ok)}.
    Solo cuentan las partidas con dato. falta = cuántas más de las últimas 10 hacen falta para graduarla."""
    out = {}
    for m, (campo, ok) in reglas.items():
        v = [bool(ok(g[campo])) for g in gs if g.get(campo) is not None]
        ult, racha = v[-VENTANA:], 0
        for x in reversed(v):
            if not x: break
            racha += 1
        k = sum(ult)
        grad = len(ult) == VENTANA and (k >= GRADUA or (m in graduadas and k >= REGRESA))
        out[m] = dict(ok=k, n=len(ult), racha=racha, graduada=grad, falta=0 if grad else max(0, GRADUA - k))
    return out


def leer():
    try: d = json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except (OSError, ValueError): return {}
    return d if isinstance(d, dict) else {}


def actualizar(gs, reglas):
    """estado() con lo graduado antes (de disco), y lo guarda. Sin disco, igual devuelve el estado."""
    e = estado(gs, reglas, set(leer().get("graduadas") or []))
    try:
        ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVO.write_text(json.dumps({"graduadas": sorted(m for m, x in e.items() if x["graduada"]), "reglas": e}, ensure_ascii=False), encoding="utf-8")
    except OSError: pass
    return e
