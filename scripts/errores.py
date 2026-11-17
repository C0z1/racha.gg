"""Tus 3 errores repetidos (Fase 7 de Sombra), con UN solo detector para el timeline (revisión) y la partida en vivo (franja).
Las dos fuentes se traducen a eventos comunes {t (s), k: "kill" | "obj", victima: "yo" | "aliado" | "rival", mio, nuestro}:
  sin_objetivo: tu muerte del 14 al 25 sin dragón/heraldo/barón/larvas/torre/inhibidor de tu equipo 60 s antes ni después.
  abajo_6: kill en la que participas (o mueres) del 5:30 al 7:00 con menos nivel que tu rival al minuto 6.
  sin_pelea: pelea del 14 en adelante (3+ muertes encadenadas a ≤ 30 s) que tu equipo pierde, sin kill, asistencia ni muerte tuya.
Sin posiciones (la Live Client Data no las da): nada aquí adivina dónde estabas."""
ERRORES = ("sin_objetivo", "abajo_6", "sin_pelea")
NOMBRE = {"sin_objetivo": "Muerte sin objetivo", "abajo_6": "Nivel abajo al 6", "sin_pelea": "Pelea perdida sin ti"}
VENTANA = {"sin_objetivo": (840, 1500), "abajo_6": (330, 420), "sin_pelea": (840, None)}  # s de juego en que se vigila cada error
MARGEN_OBJ, PELEA_S, PELEA_MIN = 60, 30, 3


def sin_objetivo(ev, hasta=None):
    """Minutos (s) de tus muertes sin objetivo. hasta = reloj actual: una muerte de hace < 60 s aún no se decide."""
    obj = [e["t"] for e in ev if e["k"] == "obj" and e.get("nuestro")]
    lo, hi = VENTANA["sin_objetivo"]
    return [e["t"] for e in ev if e["k"] == "kill" and e["victima"] == "yo" and lo <= e["t"] < hi
            and (hasta is None or hasta - e["t"] >= MARGEN_OBJ) and not any(abs(t - e["t"]) <= MARGEN_OBJ for t in obj)]


def abajo_6(ev, nivel6):
    """El momento (s) de la primera kill tuya del 5:30 al 7:00 si al minuto 6 ibas abajo de nivel; [] si no. nivel6 = (tú, rival)."""
    if not nivel6 or None in nivel6 or nivel6[0] >= nivel6[1]: return []
    lo, hi = VENTANA["abajo_6"]
    return next(([e["t"]] for e in ev if e["k"] == "kill" and e["mio"] and lo <= e["t"] < hi), [])


def peleas(ev, desde=840):
    """Las peleas desde el 14: grupos de kills encadenadas a ≤ 30 s."""
    ks, out = [e for e in ev if e["k"] == "kill" and e["t"] >= desde], []
    for e in ks:
        if out and e["t"] - out[-1][-1]["t"] <= PELEA_S: out[-1].append(e)
        else: out.append([e])
    return out


def sin_pelea(ev, hasta=None):
    """El inicio (s) de cada pelea perdida sin ti. hasta = reloj actual: una pelea de hace < 30 s puede seguir."""
    out = []
    for p in peleas(ev):
        if hasta is not None and hasta - p[-1]["t"] <= PELEA_S: continue
        caen = sum(e["victima"] in ("yo", "aliado") for e in p)
        if len(p) >= PELEA_MIN and caen > len(p) - caen and not any(e["mio"] for e in p): out.append(p[0]["t"])
    return out


def detectar(ev, nivel6=None, hasta=None):
    """{error: [s, …]} con los tres detectores."""
    return {"sin_objetivo": sin_objetivo(ev, hasta), "abajo_6": abajo_6(ev, nivel6), "sin_pelea": sin_pelea(ev, hasta)}


# ---------- traductores ----------

def de_timeline(fr, pid, equipo):
    """Eventos comunes desde los frames de Match-V5. equipo = {participantId: teamId}."""
    eq, out = equipo.get(pid), []
    for f in fr:
        for e in f.get("events") or []:
            t = e.get("timestamp", 0) / 1000
            if e.get("type") == "CHAMPION_KILL":
                v = e.get("victimId")
                out.append({"t": t, "k": "kill", "victima": "yo" if v == pid else "aliado" if equipo.get(v) == eq else "rival",
                            "mio": pid in (e.get("killerId"), v) or pid in (e.get("assistingParticipantIds") or [])})
            elif e.get("type") == "ELITE_MONSTER_KILL":
                out.append({"t": t, "k": "obj", "nuestro": e.get("killerTeamId") == eq})
            elif e.get("type") == "BUILDING_KILL":
                out.append({"t": t, "k": "obj", "nuestro": e.get("teamId") not in (None, eq)})  # teamId = el dueño del edificio
    return out


MONSTRUOS = ("DragonKill", "HeraldKill", "BaronKill", "HordeKill", "AtakhanKill")
EQUIPO = {"ORDER": 100, "CHAOS": 200}


def de_vivo(d):
    """Eventos comunes desde una foto de /allgamedata (sus Events son los de toda la partida). [] sin tu jugador.
    KillerName puede ser el nombre del jugador o el de su campeón (se ve con monstruos); torres y súbditos no son de nadie."""
    ps, ap = (d or {}).get("allPlayers") or [], (d or {}).get("activePlayer") or {}
    mios = {ap.get(k) for k in ("riotId", "riotIdGameName", "summonerName")} - {None, ""}
    nombres = lambda p: {p.get("riotId"), p.get("riotIdGameName"), p.get("summonerName"), (p.get("riotId") or "").split("#")[0]} - {None, ""}
    yo = next((p for p in ps if nombres(p) & mios), None)
    if not yo: return []
    eq, de = yo.get("team"), {}
    for p in ps:
        for n in nombres(p) | {p.get("championName")} - {None, ""}: de.setdefault(n, p.get("team"))
    nyo = nombres(yo)
    out = []
    for e in ((d.get("events") or {}).get("Events")) or []:
        t, n = e.get("EventTime") or 0, e.get("EventName")
        if n == "ChampionKill":
            v = e.get("VictimName")
            out.append({"t": t, "k": "kill", "victima": "yo" if v in nyo else "aliado" if de.get(v) == eq else "rival",
                        "mio": bool(nyo & ({e.get("KillerName"), v} | set(e.get("Assisters") or [])))})
        elif n in MONSTRUOS:
            out.append({"t": t, "k": "obj", "nuestro": de.get(e.get("KillerName")) == eq or bool(set(e.get("Assisters") or []) & {k for k, x in de.items() if x == eq})})
        elif n in ("TurretKilled", "InhibKilled"):
            edificio = str(e.get(n) or "")
            dueño = "CHAOS" if "_TChaos_" in edificio else "ORDER" if "_TOrder_" in edificio else None
            out.append({"t": t, "k": "obj", "nuestro": dueño is not None and dueño != eq})
    return sorted(out, key=lambda e: e["t"])
