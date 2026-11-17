"""El guion de la partida (plan Sombra): todo lo que la franja necesita de tu historial, calculado en champ select y guardado
en datos/cache/guion.json. En partida la franja solo compara cada foto con esto: no lee datos/raw ni importa draft.
  python scripts/guion.py <campeón> <rival> <ROL>   arma el guion y lo imprime"""
import json, os, pathlib, sys, time

import sombra

ARCHIVO = pathlib.Path(os.environ.get("RACHA_GUION") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "cache" / "guion.json")
MARCAS = (6, 10, 14, 25)
TOPE = 2  # muertes del 14 al 25 (draft.R_MUERTES): 0–2 → 68 %, 3+ → 43 %
ULTIMAS = 10  # la tasa de cada marca: tus últimas 10 partidas con el campeón en el rol (o en el rol)
VERSION = 1

# La regla de hoy, como dato y no como orden (Riot: no dictar decisiones). Solo esto entra a la franja.
CORTA = {"muertes": "Tope {tope} muertes · 14 a 25", "nivel": "Nivel al 6 · igual o arriba", "cs": "CS al 10 · tu meta",
         "kp": "Peleas del 14 · tu media"}


def corta(regla, tope=TOPE):
    """regla.corta de una regla de vistas.regla_hoy ({metrica, ...}); None si no hay regla."""
    if not regla: return None
    return CORTA.get(regla.get("metrica"), "Tu regla de hoy").format(tope=tope)


def _en(c, i): return c[i] if len(c) > i else None


def marcas(sb, mias, tope=TOPE):
    """{minuto: {meta, ok, n}}: la meta de cada marca y cuántas de tus últimas partidas la cumplen. meta None = sin dato.
    6: muertes al 6 ≤ las de tu sombra · 10: CS al 10 ≥ el de tu sombra · 14: oro ≥ tu rival de línea · 25: muertes 14–25 ≤ tope."""
    m6, m10 = _en(sb["muertes"], 6), _en(sb["cs"], 10)
    prueba = {6: (m6, lambda s: _en(s["muertes"], 6) is not None and m6 is not None and s["muertes"][6] <= m6, lambda s: len(s["muertes"]) > 6),
              10: (m10, lambda s: m10 is not None and s["cs"][10] >= m10, lambda s: len(s["cs"]) > 10),
              14: (0, lambda s: s["oro14"] >= 0, lambda s: s.get("oro14") is not None),
              25: (tope, lambda s: s["muertes"][25] - s["muertes"][14] <= tope, lambda s: len(s["muertes"]) > 25)}
    out = {}
    for k, (meta, ok, hay) in prueba.items():
        xs = [s for s in mias if hay(s)][-ULTIMAS:] if meta is not None else []
        out[str(k)] = dict(meta=meta, ok=sum(map(ok, xs)), n=len(xs))
    return out


def _notas(rival):
    """Tu nota del matchup (datos/matchups-notas.json, a mano), la primera; None si no hay."""
    try: n = json.loads((sombra.raw().parent / "matchups-notas.json").read_text(encoding="utf-8")).get(rival)
    except (OSError, ValueError, AttributeError): return None
    return (n[0] if isinstance(n, list) and n else n) or None


def armar(campeon, rival, pos, regla=None, racha=0, ss=None, guardar=True):
    """El guion de la partida. regla = vistas.regla_hoy (o None); racha = partidas seguidas cumpliendo tu regla (ciclo.py)."""
    t0 = time.perf_counter()
    ss = sombra.series() if ss is None else ss
    sb = sombra.sombra(ss, campeon, pos)
    mias = [s for s in ss if s["pos"] == pos and s["champ"] == campeon]
    if len(mias) < ULTIMAS: mias = [s for s in ss if s["pos"] == pos]  # pocas con el campeón: la tasa de tu rol
    vs = [s for s in ss if s["champ"] == campeon and rival and s["rival"] == rival]
    tope = TOPE
    g = dict(v=VERSION, campeon=campeon, rival=rival, pos=pos, creado=int(time.time()), sombra=sb, marcas=marcas(sb, mias, tope),
             regla=dict(corta=corta(regla, tope), metrica=(regla or {}).get("metrica"), tope=tope, ok=(regla or {}).get("ok"),
                        n=(regla or {}).get("n"), racha=racha),
             matchup=dict(v=sum(s["win"] for s in vs), n=len(vs), nota=_notas(rival)) if rival else None)
    g["ms"] = round((time.perf_counter() - t0) * 1000)
    if guardar:
        try:
            ARCHIVO.parent.mkdir(parents=True, exist_ok=True); tmp = ARCHIVO.with_suffix(".tmp")
            tmp.write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8"); os.replace(tmp, ARCHIVO)  # la franja nunca lee uno a medias
        except OSError: pass  # sin disco: la franja usa el que reciba por la tubería
    return g


def leer(campeon=None):
    """El guion guardado, o None si no hay, está roto o es de otro campeón."""
    try: g = json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except (OSError, ValueError): return None
    return g if isinstance(g, dict) and g.get("v") == VERSION and (campeon is None or g.get("campeon") == campeon) else None


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(armar(sys.argv[1], sys.argv[2], sys.argv[3].upper(), guardar=False), ensure_ascii=False))
