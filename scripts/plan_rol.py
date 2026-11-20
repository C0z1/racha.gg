"""El plan de partida de tu rol (Fase 7 de Sombra): compara tus victorias con tus derrotas en ese rol, medida por medida, y elige
las 2 fases (0–6, 6–14, 14–25) donde más se separan. Cada medida se puede comprobar en vivo y se escribe como dato
(«en tus victorias, 2; en tus derrotas, 0,8»), nunca como orden.
  python scripts/plan_rol.py <ROL>   imprime el plan (para revisar)"""
import json, statistics as st, sys

MIN_PARTIDAS = 8  # victorias y derrotas en el rol: con menos, no hay plan (quedan las marcas fijas)
ULTIMAS = 100  # tus partidas más recientes en el rol


def _en(c, i): return c[i] if c and len(c) > i else None


def _dif(a, b, i):
    x, y = _en(a, i), _en(b, i)
    return x - y if x is not None and y is not None else None


# id: (fase, minuto en que se sella, mejor si «+» sube / «-» baja, cómo se lee de la serie, etiqueta corta, formato del valor)
MEDIDAS = {
    "muertes6": (1, 6, "-", lambda s: _en(s["muertes"], 6), "muertes al 6", "{:g}"),
    "kp6": (1, 6, "+", lambda s: _en(s["kp"], 6), "peleas al 6", "{:.0%}"),
    "nivel3": (1, 3, "+", lambda s: _dif(s["nivel"], s.get("nivel_rival"), 3), "nivel al 3", "{:+g}"),
    "cs10": (2, 10, "+", lambda s: _en(s["cs"], 10), "CS al 10", "{:g}"),
    "muertes14": (2, 14, "-", lambda s: _en(s["muertes"], 14), "muertes al 14", "{:g}"),
    "dragones14": (2, 14, "+", lambda s: s.get("dragones14"), "dragones al 14", "{:g}"),
    "nivel10": (2, 10, "+", lambda s: _dif(s["nivel"], s.get("nivel_rival"), 10), "nivel al 10", "{:+g}"),
    "muertes14_25": (3, 25, "-", lambda s: _en(s["muertes"], 25) - s["muertes"][14] if _en(s["muertes"], 25) is not None else None, "muertes 14–25", "{:g}"),
    "kp25": (3, 25, "+", lambda s: _en(s["kp"], 25), "peleas al 25", "{:.0%}"),
}
FASES = {1: "0–6", 2: "6–14", 3: "14–25"}


def _coma(t): return t.replace(".", ",")


def medir(ss, pos):
    """Cada medida en el rol: {id: {fase, minuto, dir, v (mediana de victorias), d (de derrotas), n_v, n_d, efecto}}.
    efecto = diferencia de medianas a favor de las victorias, en desviaciones (comparable entre medidas)."""
    xs = [s for s in ss if s.get("pos") == pos][-ULTIMAS:]
    out = {}
    for k, (fase, minuto, sentido, leer, etq, frase) in MEDIDAS.items():
        v = [x for s in xs if s["win"] and (x := leer(s)) is not None]
        d = [x for s in xs if not s["win"] and (x := leer(s)) is not None]
        if len(v) < MIN_PARTIDAS or len(d) < MIN_PARTIDAS: continue
        mv, md, sd = st.median(v), st.median(d), st.pstdev(v + d) or 1
        out[k] = dict(fase=fase, minuto=minuto, dir=sentido, v=round(mv, 2), d=round(md, 2), n_v=len(v), n_d=len(d),
                      efecto=round((mv - md if sentido == "+" else md - mv) / sd, 3))
    return out


def plan(ss, pos):
    """{pos, fases: {1|2|3: medida o None}, marcas: [las 2 de más efecto, en fases distintas]} o None sin partidas suficientes.
    Una medida entra si tus victorias van mejor que tus derrotas (efecto > 0)."""
    m = medir(ss, pos)
    if not m: return None
    import postpartida  # con 15+ partidas de cada lado, la medida se elige por cuánto te cambia el WR (no por la mediana)
    for k in list(m):
        if (x := postpartida.impacto(ss, pos, k)) is None: continue
        if x["si"] - x["no"] < postpartida.MIN_DIF: del m[k]; continue  # no te cambia el WR: es ruido (kp6 en mid)
        m[k].update(v=x["umbral"], wr=round(x["si"], 3), n_wr=x["n_si"], wr_no=round(x["no"], 3), efecto=round(10 + x["si"] - x["no"], 3))  # 10+: antes que las sin WR
    fases = {}
    for f in FASES:
        mejor = max(((k, x) for k, x in m.items() if x["fase"] == f and x["efecto"] > 0), key=lambda kx: kx[1]["efecto"], default=None)
        fases[f] = {"id": mejor[0], **mejor[1], "etq": MEDIDAS[mejor[0]][4], "dato": dato(mejor[0], mejor[1])} if mejor else None
    marcas = sorted((x for x in fases.values() if x), key=lambda x: -x["efecto"])[:2]
    return dict(pos=pos, fases=fases, marcas=sorted(marcas, key=lambda x: x["minuto"])) if marcas else None


def valor(k, v): return _coma(MEDIDAS[k][5].format(v))


FRASE = {"muertes6": "{} muertes al 6", "kp6": "{} en kills al 6", "nivel3": "nivel {} al 3", "cs10": "{} CS al 10",
         "muertes14": "{} muertes al 14", "dragones14": "{} dragones al 14", "nivel10": "nivel {} al 10",
         "muertes14_25": "{} muertes 14–25", "kp25": "{} en kills al 25"}


def frase(k, v):
    """El valor con su unidad, para leerse solo: «1 dragón al 14», «25% en kills al 6»."""
    t = FRASE[k].format(valor(k, v))
    return t.replace("muertes", "muerte").replace("dragones", "dragón") if v == 1 else t


def umbral(k, u):
    """La meta como umbral: «≥1 dragón al 14», «≤2 muertes 14–25», «0 muertes al 6»."""
    if k.startswith("nivel") and u == 0: return f"sin nivel abajo al {k[5:]}"  # «≥+0» no se lee
    t = FRASE[k].replace("{}", ("≥" if MEDIDAS[k][2] == "+" else "≤") + "{}").format(valor(k, u)).replace("≤0 ", "0 ")
    return t.replace("muertes", "muerte").replace("dragones", "dragón") if u == 1 else t


def renglon(m):
    """El renglón de una medida del plan: con tu WR al cumplirla («≥1 dragón al 14: ganas 69%») o, con pocas partidas, la
    mediana de tus victorias («Tus victorias: 1 dragón al 14»). Dato, nunca orden."""
    return f"{umbral(m['id'], m['v'])}: ganas {m['wr']:.0%}" if m.get("wr") is not None else "Tus victorias: " + frase(m["id"], m["v"])


def dato(k, x):
    """«CS al 10: victorias 71 · derrotas 68», como dato."""
    return f"{MEDIDAS[k][4]}: victorias {valor(k, x['v'])} · derrotas {valor(k, x['d'])}"


def cumple(k, valor, meta):
    """¿El valor en vivo cumple la medida contra la meta (la mediana de tus victorias)?"""
    return valor <= meta if MEDIDAS[k][2] == "-" else valor >= meta


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8"); import sombra
    print(json.dumps(plan(sombra.series(), sys.argv[1].upper()), ensure_ascii=False, indent=1))
