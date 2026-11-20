"""Tu sombra (plan Sombra): la mediana, minuto a minuto, de tus últimas victorias con ese campeón en ese rol. Sigue cuatro
curvas: CS (minions + monstruos, como el creepScore en vivo), nivel, muertes acumuladas y participación en kills.
Las series por minuto salen del timeline de cada partida y van al índice (indice.py): no se releen los timelines.
  python scripts/sombra.py <campeón> <ROL>   imprime la sombra (para revisar)"""
import json, os, pathlib, statistics as st, sys

import indice, score

MIN_VICTORIAS = 8  # con menos, la mediana es ruido: se usa la del rol, o «Sin sombra aún»
MAX_VICTORIAS = 30  # las más recientes: tu sombra cambia contigo
MINUTOS = 36  # curvas del 0 al 35
SALIDA_MS = 90_000  # las compras de antes son las de inicio; la primera después, tu primer regreso
MIN_POR_MINUTO = 5  # un minuto con menos victorias que lleguen hasta él no entra en la curva (las partidas largas son pocas)


def raw():
    return pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")


def serie(f, yo):
    """Lo de una partida que necesita la sombra, o None (remake, sin timeline, sin tu puuid, timeline roto):
    {win, champ, pos, rival, t, cs[], nivel[], muertes[], kp[], oro14}. kp[i] None mientras tu equipo no tenga kills."""
    m = score.cargar_partida(f)
    if not m or (m["info"].get("gameDuration") or 0) < 300: return None
    ps = m["info"]["participants"]
    me = next((p for p in ps if p.get("puuid") == yo), None)
    if not me: return None
    try:
        fr = json.loads((pathlib.Path(f).parent / "timeline" / pathlib.Path(f).name).read_text(encoding="utf-8"))["info"]["frames"]
        pid, aliados = me["participantId"], {p["participantId"] for p in ps if p["teamId"] == me["teamId"]}
        opp = next((p for p in ps if me.get("teamPosition") and p.get("teamPosition") == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
        kills = [e for x in fr for e in x["events"] if e.get("type") == "CHAMPION_KILL"]
        compras = [e["timestamp"] for x in fr for e in x["events"] if e.get("type") == "ITEM_PURCHASED" and e.get("participantId") == pid and e["timestamp"] > SALIDA_MS]
        out = dict(win=me["win"], champ=me["championName"], pos=me.get("teamPosition") or "", rival=opp["championName"] if opp else None,
                   t=m["info"]["gameCreation"], cs=[], nivel=[], muertes=[], kp=[], oro=[], oro14=None, nivel_rival=[],
                   vision_min=round(me["visionScore"] / (m["info"]["gameDuration"] / 60), 2) if me.get("visionScore") is not None and m["info"].get("gameDuration") else None,
                   dragones14=sum(e.get("type") == "ELITE_MONSTER_KILL" and e.get("monsterType") == "DRAGON" and e.get("killerTeamId") == me["teamId"]
                                  and e["timestamp"] <= 14 * 60000 for x in fr for e in x["events"]),  # plan de rol (plan_rol.py)
                   regreso=round(min(compras) / 60000, 1) if compras else None)  # minuto de tu primer regreso a la tienda
        for i, x in enumerate(fr[:MINUTOS]):
            p = x["participantFrames"][str(pid)]
            ks = [e for e in kills if e["timestamp"] <= i * 60000]
            eq = [e for e in ks if e.get("killerId") in aliados]
            out["cs"].append(p["minionsKilled"] + p["jungleMinionsKilled"]); out["nivel"].append(p["level"]); out["oro"].append(p["totalGold"])
            if opp: out["nivel_rival"].append(x["participantFrames"][str(opp["participantId"])]["level"])
            out["muertes"].append(sum(e.get("victimId") == pid for e in ks))
            out["kp"].append(round(sum(e["killerId"] == pid or pid in (e.get("assistingParticipantIds") or []) for e in eq) / len(eq), 2) if eq else None)
        if opp and len(fr) > 14:
            pf = fr[14]["participantFrames"]; out["oro14"] = pf[str(pid)]["totalGold"] - pf[str(opp["participantId"])]["totalGold"]
        return out
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError): return None  # timeline roto: sin serie, no tumba el guion


def series(carpeta=None):
    """Las series de todas tus partidas, de la más vieja a la más reciente (desde el índice si nada cambió)."""
    carpeta = pathlib.Path(carpeta or raw())
    try: yo = json.loads((carpeta / "perfil.json").read_text(encoding="utf-8"))["account"]["puuid"]
    except (OSError, ValueError, KeyError, TypeError): return []
    ver = indice.version(pathlib.Path(__file__), pathlib.Path(score.__file__), yo)
    out = [s for f in carpeta.glob("*_*.json") if (s := indice.derivado(f, "serie", ver, lambda f=f: serie(f, yo)))]
    return sorted(out, key=lambda s: s["t"])


def _mediana(vs, entero):
    m = st.median(vs)
    return int(m) if entero else round(m, 2)  # CS y nivel a la baja: la sombra no exige de más


def curvas(xs):
    """Mediana por minuto de cada curva, mientras haya MIN_POR_MINUTO partidas que lleguen a ese minuto."""
    out = {}
    for k in ("cs", "nivel", "muertes", "kp", "oro"):
        c = []
        for i in range(MINUTOS):
            vs = [s[k][i] for s in xs if len(s.get(k) or []) > i and s[k][i] is not None]
            if len(vs) < MIN_POR_MINUTO:
                if k == "kp" and len([s for s in xs if len(s[k]) > i]) >= MIN_POR_MINUTO: c.append(None); continue  # aún sin kills del equipo
                break
            c.append(_mediana(vs, k != "kp"))
        out[k] = c
    return out


def sombra(ss, campeon, pos):
    """{alcance: "campeon" | "rol" | None, n, falta, cs, nivel, muertes, kp}. Con menos de MIN_VICTORIAS con el campeón, la del
    rol («sombra de mid»); con menos en el rol, alcance None y las curvas vacías («Sin sombra aún · n de 8»)."""
    rol = [s for s in ss if s["win"] and s["pos"] == pos]
    for alcance, xs in (("campeon", [s for s in rol if s["champ"] == campeon]), ("rol", rol)):
        if len(xs) >= MIN_VICTORIAS:
            xs = xs[-MAX_VICTORIAS:]
            rg = [s["regreso"] for s in xs if s.get("regreso") is not None]
            vi = [s["vision_min"] for s in xs if s.get("vision_min") is not None]
            return dict(alcance=alcance, n=len(xs), falta=0, regreso=round(st.median(rg), 1) if len(rg) >= MIN_POR_MINUTO else None,
                        vision_min=round(st.median(vi), 2) if len(vi) >= MIN_POR_MINUTO else None, **curvas(xs))
    return dict(alcance=None, n=len(rol), falta=MIN_VICTORIAS - len(rol), regreso=None, vision_min=None, cs=[], nivel=[], muertes=[], kp=[], oro=[])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(sombra(series(), sys.argv[1], sys.argv[2].upper()), ensure_ascii=False))
