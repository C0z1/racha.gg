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
        ARCHIVO.write_text(json.dumps({**leer(), "graduadas": sorted(m for m, x in e.items() if x["graduada"]), "reglas": e}, ensure_ascii=False), encoding="utf-8")
    except OSError: pass
    return e


VIGILADOS = 2  # errores que la franja vigila a la vez


def errores(e, graduados=None):
    """El ciclo de tus errores (vistas.errores): por error, en tus últimas 10 partidas revisadas, cuántas lo evitaste, tu racha
    sin él y si ya está corregido (8 de 10; vuelve bajo 5). vigilados = los 2 más repetidos sin corregir, el n.º 1 primero.
    {"errores": {id: {ok, n, racha, graduada, falta, veces}}, "vigilados": [id, id], "corregidos": [id]}. Guarda los corregidos."""
    if not e or not e.get("revisadas"): return {"errores": {}, "vigilados": [], "corregidos": []}
    previo = leer()
    graduados = set(previo.get("errores_corregidos") or []) if graduados is None else set(graduados)
    orden = list(reversed(e["revisadas"]))  # de la más vieja a la más reciente
    out = {}
    for k, ms in (e.get("momentos") or {}).items():
        con = {m["archivo"] for m in ms}
        x = estado([{"evitado": a not in con} for a in orden], {k: ("evitado", bool)}, graduados)[k]
        out[k] = {**x, "veces": e["partidas"].get(k, 0)}
    corregidos = sorted(k for k, x in out.items() if x["graduada"])
    vig = [k for k in sorted(out, key=lambda k: -out[k]["veces"]) if k not in corregidos and out[k]["veces"]][:VIGILADOS]
    try:
        ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVO.write_text(json.dumps({**previo, "errores_corregidos": corregidos}, ensure_ascii=False), encoding="utf-8")
    except OSError: pass
    return {"errores": out, "vigilados": vig, "corregidos": corregidos}
