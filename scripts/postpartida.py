"""Revisión post-partida: los 3 momentos clave de una partida, tus muertes sin objetivo (la guardia de tilt ya es score.tilt).
Todo son funciones puras sobre el JSON de match-v5 y su timeline (como los guarda scripts/descargar.py); nada toca el cliente.
(El nombre no es revision.py porque ese ya es la revisión semanal.)
Uso: python scripts/postpartida.py [match_id]   (por defecto la última de datos/raw; DATOS_DIR cambia la carpeta)"""
import json, os, pathlib, sys

VENTANA_OBJ = 60_000  # ms: un objetivo rival tras tu muerte se atribuye a ella si cae dentro de este margen (igual que errores())
SALTO_ORO = 400  # oro en 1 min contra tu rival de línea para contar como vuelco; menos es ruido normal de farmeo
ORO_POR_PUNTO = 200  # el vuelco vale 1 punto de impacto por cada 200 oro de cambio
BASE_MUERTE = 2  # una muerte ya cuesta algo aunque no caiga nada
VALOR = {"BARON_NASHOR": 6, "ELDER_DRAGON": 5, "DRAGON": 4, "RIFTHERALD": 3, "HORDE": 2, "TOWER_BUILDING": 3, "INHIBITOR_BUILDING": 4}
NOMBRE = {"BARON_NASHOR": "el barón", "ELDER_DRAGON": "el dragón anciano", "DRAGON": "el dragón", "RIFTHERALD": "el heraldo",
          "HORDE": "las larvas del vacío", "TOWER_BUILDING": "una torre", "INHIBITOR_BUILDING": "un inhibidor"}



def _mm(ms): return f"{int(ms) // 60000}:{int(ms) // 1000 % 60:02d}"


def zona(x, y, team):  # revision.py la importa de aquí
    own = (x + y < 14800) == (team == 100)
    if x + y < 5600 or x + y > 24000: return "base propia" if own else "base rival"
    if abs(x - y) < 1600: z = "mid"
    elif x < 2300 or y > 12500: z = "top"
    elif y < 2300 or x > 12500: z = "bot"
    elif abs(x + y - 14800) < 1500: return "río"
    else: z = "jungla"
    return f"{z} ({'lado propio' if own else 'lado rival'})"


def EN_ZONA(z):  # «río», «mid (lado rival)» → «el río», «su lado de mid»
    if z in ("río", "base propia", "base rival"): return {"río": "el río", "base propia": "tu base", "base rival": "su base"}[z]
    lugar, _, lado = z.partition(" (")
    return f"{'tu' if lado.startswith('lado propio') else 'su'} lado de {'la jungla' if lugar == 'jungla' else lugar}"
VENTANA_PELEA, VENTANA_WARD = 15_000, 90_000  # ms: kills de aliados alrededor = pelea; tu ward en el minuto y medio previo


def clasificar_muerte(e, me, ps, fr, ev, objs):
    """Por qué probablemente caíste (para enseñar, no culpar). {t, tipo, n, jungla, zona, dnivel, ward, obj_tuyo,
    obj_rival, texto}. tipo: trade (tu equipo tomó un objetivo en ±60 s), torre (no te mató un campeón), pelea (2+ rivales y tus
    aliados metidos), gank (su jungla entre 2+), varios (2+ rivales sin su jungla: roam o 2v2) o 1v1. Riot no da la posición de
    los wards ni la oleada: la causa es probable, y así se dice."""
    t, pid, eq = e["timestamp"], me["participantId"], me["teamId"]
    equipo = {p.get("participantId"): p.get("teamId") for p in ps}
    rivales = {i for i in [e.get("killerId")] + list(e.get("assistingParticipantIds") or []) if equipo.get(i) not in (None, eq)}
    jg = next((p.get("participantId") for p in ps if p.get("teamId") != eq and p.get("teamPosition") == "JUNGLE"), None)
    pos = e.get("position") or {}
    z = zona(pos["x"], pos["y"], eq) if "x" in pos and "y" in pos else None
    aliados = {i for x in ev if x.get("type") == "CHAMPION_KILL" and abs((x.get("timestamp") or 0) - t) <= VENTANA_PELEA
               for i in [x.get("killerId"), x.get("victimId")] + list(x.get("assistingParticipantIds") or []) if equipo.get(i) == eq and i != pid}
    tuyo = [(t2, ty) for t2, ty, q in objs if q == eq and ty != "TOWER_BUILDING" and t - 30_000 <= t2 <= t + VENTANA_OBJ]  # un objetivo grande; las torres caen solas
    suyo = [(t2, ty) for t2, ty, q in objs if q != eq and t <= t2 <= t + VENTANA_OBJ]
    ward = any(x.get("type") == "WARD_PLACED" and x.get("creatorId") == pid and t - VENTANA_WARD <= (x.get("timestamp") or 0) <= t for x in ev)
    dnivel = None
    try:
        f = fr[min(len(fr) - 1, t // 60000)]["participantFrames"]
        k = e.get("killerId")
        if equipo.get(k) not in (None, eq): dnivel = f[str(pid)]["level"] - f[str(k)]["level"]
    except (KeyError, TypeError, IndexError): pass
    n = len(rivales)
    tipo = ("trade" if tuyo else "torre" if not rivales else "pelea" if n >= 2 and aliados else
            "gank" if n >= 2 and jg in rivales else "varios" if n >= 2 else "1v1")
    en = f" en {EN_ZONA(z)}" if z else ""
    nom = lambda o: NOMBRE[max(o, key=lambda x: VALOR[x[1]])[1]]
    sin_ward = " No vimos un ward tuyo en el minuto y medio anterior: uno antes de avanzar cubre esa ventana." if not ward else \
        " Tenías un ward reciente: probablemente entraron por otro camino."
    if tipo == "trade": texto = f"Min {_mm(t)}: caíste, pero tu equipo se llevó {nom(tuyo)}. Buen cambio."
    elif tipo == "torre": texto = f"Min {_mm(t)}: te remató la torre o los súbditos{en}. Con poca vida, salir un poco antes evita estas."
    elif tipo == "pelea": texto = f"Min {_mm(t)}: caíste en una pelea contra {n}{en}. Para el replay: quién entró primero y si llegaron todos."
    elif tipo == "gank": texto = f"Min {_mm(t)}: te alcanzaron entre {n} con su jungla{en}.{sin_ward}"
    elif tipo == "varios": texto = f"Min {_mm(t)}: te alcanzaron entre {n}{en}.{sin_ward}"
    else:
        rival = next((p.get("championName") for p in ps if p.get("participantId") == e.get("killerId")), "tu rival")
        if dnivel and dnivel < 0: texto = f"Min {_mm(t)}: 1 contra 1 con {rival}, con {-dnivel} nivel{'es' if dnivel < -1 else ''} abajo. Igualar el nivel antes de tradear suele salvar estas."
        else: texto = f"Min {_mm(t)}: 1 contra 1 con {rival}{en}. Para el replay: qué habilidad clave tenía él y tú no."
    if suyo and tipo != "trade": texto += f" Después el rival tomó {nom(suyo)}."
    return dict(t=t, tipo=tipo, n=n, jungla=jg in rivales, zona=z, dnivel=dnivel, ward=ward, obj_tuyo=bool(tuyo), obj_rival=suyo, texto=texto)


def _ctx(match, timeline, puuid):
    """(yo, rival, eventos, frames) o None si falta algo; nunca lanza."""
    try:
        ps = match["info"]["participants"]
        me = next(p for p in ps if p["puuid"] == puuid)
        opp = next((p for p in ps if p.get("teamPosition") and p["teamPosition"] == me.get("teamPosition") and p["teamId"] != me["teamId"]), None)
        fr = timeline["info"]["frames"]
        return me, opp, [e for f in fr for e in f.get("events", ())], fr
    except (KeyError, TypeError, StopIteration, AttributeError):
        return None


def _objetivos(ev):
    """[(t, tipo, equipo_que_lo_toma)]: dragones, heraldo, larvas, barón, torres e inhibidores (el equipo es el que NO perdió el edificio)."""
    out = []
    for e in ev:
        t, ty = e.get("timestamp"), e.get("type")
        if t is None: continue
        if ty == "ELITE_MONSTER_KILL" and e.get("monsterType") in VALOR and e.get("killerTeamId"):
            out.append((t, e["monsterType"], e["killerTeamId"]))
        elif ty == "BUILDING_KILL" and e.get("buildingType") in VALOR and e.get("teamId") in (100, 200):
            out.append((t, e["buildingType"], 300 - e["teamId"]))
    return out


def _muertes(me, ev, objs):
    """[(t, objetivos_rivales_en_60s)] de tus muertes."""
    pid, eq = me["participantId"], me["teamId"]
    return [(e["timestamp"], [(t, ty) for t, ty, q in objs if q != eq and e["timestamp"] <= t <= e["timestamp"] + VENTANA_OBJ])
            for e in ev if e.get("type") == "CHAMPION_KILL" and e.get("victimId") == pid and "timestamp" in e]


def muertes(match, timeline, puuid):
    """[clasificar_muerte(...)] de todas tus muertes; [] sin datos."""
    c = _ctx(match, timeline, puuid)
    if not c: return []
    me, _, ev, fr = c
    ps, objs = match["info"]["participants"], _objetivos(ev)
    try: return [clasificar_muerte(e, me, ps, fr, ev, objs) for e in ev if e.get("type") == "CHAMPION_KILL" and e.get("victimId") == me["participantId"] and "timestamp" in e]
    except (KeyError, TypeError): return []


def muertes_sin_objetivo(match, timeline, puuid):
    """{n, total, ratio, por_tipo {tipo: n}, lista: [{t, tipo, texto}]}: tus muertes que tu equipo NO cambió por un objetivo,
    cada una con su causa probable. Vacío si faltan datos."""
    ms = muertes(match, timeline, puuid)
    libres = [dict(t=m["t"] // 1000, tipo=m["tipo"], texto=m["texto"]) for m in ms if m["tipo"] != "trade"]
    por = {}
    for m in ms: por[m["tipo"]] = por.get(m["tipo"], 0) + 1
    return dict(n=len(libres), total=len(ms), ratio=round(len(libres) / len(ms), 2) if ms else None, por_tipo=por, lista=libres)


def momentos(match, timeline, puuid):
    """Hasta 3 momentos clave en orden cronológico: [{t (s), tipo, texto, impacto}]. [] si faltan datos.
    Impacto (más alto = más importante): muerte = 2 + valor del objetivo rival que cae en los 60 s siguientes (barón 6, anciano 5,
    dragón 4, inhibidor 4, heraldo 3, torre 3, larvas 2); objetivo suelto = su valor (+1 si lo perdiste, porque regala ventaja);
    vuelco de oro contra tu rival de línea = cambio por minuto / 200 (desde 400). Se evita contar dos veces lo que ya va dentro de una muerte."""
    c = _ctx(match, timeline, puuid)
    if not c: return []
    me, opp, ev, fr = c
    eq, objs = me["teamId"], _objetivos(ev)
    ms = muertes(match, timeline, puuid)
    cand = _candidatos(_muertes(me, ev, objs), objs, eq, {m["t"]: m for m in ms})
    if opp:
        try:
            dif = [(f["timestamp"], f["participantFrames"][str(me["participantId"])]["totalGold"] - f["participantFrames"][str(opp["participantId"])]["totalGold"]) for f in fr]
            for (_, a), (t, b) in zip(dif, dif[1:]):
                if abs(b - a) >= SALTO_ORO:
                    cand.append(dict(t=t // 1000, tipo="oro", impacto=round(abs(b - a) / ORO_POR_PUNTO, 1),
                                     texto=f"Min {_mm(t)}: la diferencia de oro con tu rival de línea pasó de {a:+d} a {b:+d}."))
        except (KeyError, TypeError):
            pass
    return _tres(cand)


def estela(match, timeline, puuid):
    """La partida como una estela: {dur (s), win, oro: [tu oro − el de tu rival de línea, por minuto], momentos:
    [{t, tipo, texto}]}; None sin datos o fuera de la Grieta (sin rival de línea el oro va vacío y la estela queda plana)."""
    c = _ctx(match, timeline, puuid)
    if not c or (match.get("info") or {}).get("gameMode", "CLASSIC") != "CLASSIC": return None
    me, opp, _, fr = c
    oro = []
    if opp:
        try: oro = [f["participantFrames"][str(me["participantId"])]["totalGold"] - f["participantFrames"][str(opp["participantId"])]["totalGold"] for f in fr]
        except (KeyError, TypeError): oro = []
    return {"dur": (match["info"].get("gameDuration") or 0), "win": bool(me.get("win")), "oro": oro,
            "momentos": [{k: m.get(k) for k in ("t", "tipo", "texto", "tuyo")} for m in momentos(match, timeline, puuid)]}


def estela_vivo(d):
    """La estela al instante desde la última foto en vivo: sin oro (en vivo solo se ve el de los ítems), con los momentos."""
    try:
        import companion
        if not companion.grieta(d): return None
        ms = momentos_vivo(d)
        return {"dur": int(((d or {}).get("gameData") or {}).get("gameTime") or 0), "win": None, "oro": [],
                "momentos": [{k: m.get(k) for k in ("t", "tipo", "texto", "tuyo")} for m in ms]} if ms else None  # sin momentos ni oro: nada que dibujar
    except Exception: return None


def _tres(cand):
    """Los 3 de más impacto, en orden cronológico."""
    top = sorted(cand, key=lambda m: (-m["impacto"], m["t"]))[:3]
    return sorted(top, key=lambda m: m["t"])


def _candidatos(muertes, objs, eq, clasif=None):
    """Momentos posibles de tus muertes (con el objetivo rival que cayó después) y de los objetivos sueltos; t en ms.
    clasif {t: clasificar_muerte}: el texto con la causa probable (sin él, en vivo, solo lo que se ve)."""
    cand, ligados = [], set()
    for t, o in muertes:
        c = (clasif or {}).get(t)
        if o:
            ligados.update(o)
            t2, ty = max(o, key=lambda x: VALOR[x[1]])
            texto = f"Min {_mm(t)}: caíste y {(t2 - t) // 1000} s después el rival tomó {NOMBRE[ty]}."
            imp = BASE_MUERTE + VALOR[ty]
        else:
            texto, imp = f"Min {_mm(t)}: caíste; el rival no sacó un objetivo de esa muerte.", BASE_MUERTE
        if c: texto, imp = c["texto"], (0.5 if c["tipo"] == "trade" else imp)  # un buen cambio no es un momento a corregir
        cand.append(dict(t=t // 1000, tipo="muerte", texto=texto, impacto=imp))
    for t, ty, q in objs:
        if (t, ty) in ligados: continue
        mio = q == eq
        cand.append(dict(t=t // 1000, tipo="objetivo", tuyo=mio, impacto=VALOR[ty] + (0 if mio else 1),
                         texto=f"Min {_mm(t)}: tu equipo tomó {NOMBRE[ty]}." if mio else f"Min {_mm(t)}: el rival tomó {NOMBRE[ty]}."))
    return cand


VIVO_TIPO = {"BaronKill": "BARON_NASHOR", "HeraldKill": "RIFTHERALD", "HordeKill": "HORDE"}


def _equipos(d, me):
    """(eventos, {nombre: equipo} de cada jugador y de los minions, tus nombres) de una foto en vivo."""
    ps, ev = (d or {}).get("allPlayers") or [], ((d or {}).get("events") or {}).get("Events") or []
    eq = {n: p.get("team") for p in ps for n in (p.get("riotIdGameName"), p.get("summonerName"), (p.get("riotId") or "").split("#")[0]) if n}
    eq.update({"Minion_T100": "ORDER", "Minion_T200": "CHAOS"})
    return ev, eq, {me.get("riotIdGameName"), me.get("summonerName"), (me.get("riotId") or "").split("#")[0]} - {None, ""}


def momentos_vivo(d):
    """F11: los 3 momentos clave AL INSTANTE, desde la última foto en vivo (sus eventos traen toda la partida), sin key ni
    esperar a que Riot publique la partida. Sin vuelcos de oro: en vivo solo se ve el oro en ítems, que salta con cada compra."""
    try:
        import companion
        me, _ = companion.yo_rival(d)
        if not me or not companion.grieta(d): return []  # ARAM y otros modos: sin la lógica de la Grieta
        ev, eq, mios = _equipos(d, me)
        otro = {"ORDER": "CHAOS", "CHAOS": "ORDER"}
        objs = []
        for e in ev:
            n, t, k = e.get("EventName"), int((e.get("EventTime") or 0) * 1000), str(e.get("KillerName") or "")
            if n == "DragonKill": ty, q = ("ELDER_DRAGON" if e.get("DragonType") == "Elder" else "DRAGON"), eq.get(k)
            elif n in VIVO_TIPO: ty, q = VIVO_TIPO[n], eq.get(k)
            elif n in ("TurretKilled", "InhibKilled"):  # el dueño va en el nombre del edificio; lo toma el otro equipo
                s = str(e.get(n) or ""); dueno = "ORDER" if "_TOrder_" in s else "CHAOS" if "_TChaos_" in s else None
                ty, q = ("TOWER_BUILDING" if n == "TurretKilled" else "INHIBITOR_BUILDING"), otro.get(dueno)
            else: continue
            if q: objs.append((t, ty, q))
        yo = me.get("team")
        muertes = [(t, [(t2, ty) for t2, ty, q in objs if q != yo and t <= t2 <= t + VENTANA_OBJ])
                   for t, e in ((int((e.get("EventTime") or 0) * 1000), e) for e in ev)
                   if e.get("EventName") == "ChampionKill" and e.get("VictimName") in mios]
        return _tres(_candidatos(muertes, objs, yo))
    except (TypeError, ValueError, AttributeError): return []


# --- Feedback al terminar: qué hiciste bien, qué no, por qué importa (tu WR en tus partidas del rol) y un foco ---
MIN_LADO, MIN_DIF = 15, 0.08  # partidas de cada lado (cumple / no) y puntos de WR entre ellos: con menos, es ruido
ROL = {"TOP": "top", "JUNGLE": "jungla", "MIDDLE": "mid", "BOTTOM": "bot", "UTILITY": "support"}
UMBRAL = {"muertes6": "{} muertes o menos al 6", "kp6": "{} o más de las kills al 6", "nivel3": "nivel {} o más contra tu rival al 3",
          "cs10": "{} CS o más al 10", "muertes14": "{} muertes o menos al 14", "dragones14": "{} dragones o más al 14",
          "nivel10": "nivel {} o más contra tu rival al 10", "muertes14_25": "{} muertes o menos del 14 al 25", "kp25": "{} o más de las kills al 25"}
COMO = {"muertes6": "cambiar vida solo cuando ganas el intercambio hasta tu nivel 6", "kp6": "estar cerca cuando tu jungla pelea en tu lado",
        "nivel3": "farmear completas las 3 primeras oleadas", "cs10": "no perder oleadas al regresar a base ni al pelear",
        "muertes14": "regresar a base con poca vida en vez de quedarte en línea", "dragones14": "tener tu línea empujada cuando sale el dragón, para llegar antes que tu rival",
        "nivel10": "no perder oleadas por roams o muertes", "muertes14_25": "jugar cerca de tu equipo y pelear solo por un objetivo",
        "kp25": "agruparte con tu equipo para los objetivos"}
PROPIAS = ("muertes6", "muertes14", "muertes14_25", "cs10", "nivel3", "nivel10")  # el foco, primero lo que depende solo de ti
POR_QUE_ERROR = {"sin_objetivo": "moriste sin que tu equipo tomara un objetivo cerca", "sin_pelea": "tu equipo peleó y perdió sin ti",
                 "abajo_6": "peleaste con menos nivel que tu rival al 6"}


def anotar_niveles(nv, mf):
    """Guarda en nv tu nivel y el de tu rival en el primer minuto de juego tras el 3, el 6 y el 10 (la foto en vivo de ese
    momento: la última foto ya no los tiene). mf = companion.meta_fase. Una foto antes del 1:00 es otra partida: limpia."""
    t = (mf or {}).get("t") or 0
    if t < 60: nv.clear()
    if (mf or {}).get("nivel") and mf.get("nivel_rival"):
        for m in (3, 6, 10):
            if m * 60 <= t < m * 60 + 60: nv.setdefault(m, (mf["nivel"], mf["nivel_rival"]))
    return nv


def medidas_vivo(d, niveles=None):
    """{id de plan_rol.MEDIDAS: valor} que se cuentan con los eventos de la última foto (traen toda la partida): muertes al 6
    y al 14, del 14 al 25, dragones de tu equipo al 14 y tu parte de las kills al 6 y al 25. Solo los minutos a los que llegó.
    niveles = {3|6|10: (tu nivel, el de tu rival)} que vio el trabajador en ese minuto: nivel3, nivel10 y el error abajo_6.
    Más «minutos»: {id: ["mm:ss"]} de cada muerte (y de los dragones del rival), y «errores»: [{t, id}] (errores.py)."""
    try:
        import companion
        me, _ = companion.yo_rival(d)
        if not me or not companion.grieta(d): return {}
        ev, eq, mios = _equipos(d, me)
        fin, yo = ((d.get("gameData") or {}).get("gameTime") or 0), me.get("team")
        ks = [e for e in ev if e.get("EventName") == "ChampionKill"]
        mm = lambda t: f"{int(t) // 60}:{int(t) % 60:02d}"
        tus = [e.get("EventTime") or 0 for e in ks if e.get("VictimName") in mios]
        drag = [(e.get("EventTime") or 0, eq.get(str(e.get("KillerName"))) == yo) for e in ev if e.get("EventName") == "DragonKill" and (e.get("EventTime") or 0) <= 840]
        out, mins = {}, {}
        for k, a, b in (("muertes6", 0, 360), ("muertes14", 0, 840), ("muertes14_25", 840, 1500)):
            if fin >= b: ts = [mm(t) for t in tus if a <= t < b]; out[k], mins[k] = len(ts), ts
        if fin >= 840: out["dragones14"], mins["dragones14"] = sum(m for _, m in drag), [mm(t) for t, m in drag if not m]
        nv = {int(k): x for k, x in (niveles or {}).items()}  # del JSON llegan con llave de texto
        out.update({f"nivel{m}": nv[m][0] - nv[m][1] for m in (3, 10) if m in nv})
        import errores
        out["errores"] = [{"t": round(t), "id": k} for k, ts in errores.detectar(errores.de_vivo(d), nv.get(6)).items() for t in ts]
        for k, hasta in (("kp6", 360), ("kp25", 1500)):
            nuestras = [e for e in ks if (e.get("EventTime") or 0) <= hasta and eq.get(str(e.get("KillerName"))) == yo]
            if fin >= hasta and nuestras:
                out[k] = round(sum(e.get("KillerName") in mios or bool(mios & set(e.get("Assisters") or [])) for e in nuestras) / len(nuestras), 2)
        return {**out, "minutos": mins}
    except (TypeError, ValueError, AttributeError): return {}


def impacto(ss, pos, k):
    """Por qué importa la medida k en TUS partidas del rol (las 100 más recientes): el umbral es la mediana de todas (no solo de
    las victorias, para no inflarlo) y se compara tu WR de un lado y del otro. None con menos de MIN_LADO de algún lado."""
    import math, statistics as st, plan_rol
    _, _, sentido, leer, _, _ = plan_rol.MEDIDAS[k]
    vs = [(v, s["win"]) for s in [s for s in ss if s.get("pos") == pos][-plan_rol.ULTIMAS:] if (v := leer(s)) is not None]
    if len(vs) < 2 * MIN_LADO: return None
    u = st.median(v for v, _ in vs)
    if not k.startswith("kp"): u = math.ceil(u) if sentido == "+" else math.floor(u)  # medidas enteras: «2 o menos», no «2,5»
    si = [w for v, w in vs if plan_rol.cumple(k, v, u)]; no = [w for v, w in vs if not plan_rol.cumple(k, v, u)]
    if min(len(si), len(no)) < MIN_LADO: return None
    return dict(umbral=u, si=sum(si) / len(si), n_si=len(si), no=sum(no) / len(no), n_no=len(no))


def _umbral(k, u):
    import plan_rol
    return UMBRAL[k].format(plan_rol.valor(k, u)).replace("0 muertes o menos", "0 muertes").replace("1 dragones o más", "1 dragón o más")


def feedback(medidas, ss, pos):
    """Al terminar: {bien: [..], mal: [..], foco: str|None, nota: str|None}. medidas = {id: valor} de esta partida (medidas_vivo o
    medidas_partida, con sus «minutos» y «errores»); ss = tus series (sombra.series) SIN esta partida. Lo bueno: 1 medida; lo malo: 2 medidas y tus errores con su minuto; el foco: la que más te cambia el WR
    de las que dependen solo de ti (si no fallaste ninguna, de las demás)."""
    import plan_rol
    rol, xs = ROL.get(pos, pos or "tu rol"), []
    for k, v in (medidas or {}).items():
        if k not in plan_rol.MEDIDAS or v is None or not (x := impacto(ss, pos, k)) or x["si"] - x["no"] < MIN_DIF: continue
        xs.append(dict(k=k, v=v, ok=plan_rol.cumple(k, v, x["umbral"]), **x))
    xs.sort(key=lambda x: x["no"] - x["si"])  # la que más te cambia el WR, primero
    mins = (medidas or {}).get("minutos") or {}
    cuando = lambda k: f" ({'dragones del rival' if k == 'dragones14' else 'min'} {', '.join(mins[k])})" if mins.get(k) else ""
    tu = lambda x: f"{plan_rol.MEDIDAS[x['k']][4].capitalize()}: {plan_rol.valor(x['k'], x['v'])}{cuando(x['k'])}"
    wr = lambda x: f"con {_umbral(x['k'], x['umbral'])} ganas {x['si']:.0%} de {x['n_si']} partidas de {rol}; si no, {x['no']:.0%} de {x['n_no']}"
    bien = [f"{tu(x)}. En tus partidas, {wr(x)}." for x in xs if x["ok"]][:1]
    mal = [f"{tu(x)}. En tus partidas, {wr(x)}." for x in xs if not x["ok"]][:2]
    vistos = {}
    for n in sorted((medidas or {}).get("errores") or [], key=lambda n: n["t"]): vistos.setdefault(n["id"], []).append(f"{n['t'] // 60}:{n['t'] % 60:02d}")
    mal = (mal + [f"Min {' y '.join(ts[:3])}: {POR_QUE_ERROR.get(k, k)}." for k, ts in vistos.items()])[:4]  # más, ya no se lee
    m = next((x for x in xs if not x["ok"] and x["k"] in PROPIAS), None) or next((x for x in xs if not x["ok"]), None)
    foco = (f"Para la próxima: {_umbral(m['k'], m['umbral'])}. Ayuda {COMO[m['k']]}." if m else
            f"Para la próxima: repetir {_umbral(xs[0]['k'], xs[0]['umbral'])}." if xs else None)
    nota = None if xs else f"Aún no hay partidas suficientes de {rol} para comparar ({MIN_LADO} de cada lado)."
    return dict(bien=bien, mal=mal, foco=foco, nota=nota)


def medidas_partida(f, puuid):
    """Las medidas de feedback() desde la partida de Riot y su timeline (exactas, con CS y niveles), o {} sin timeline."""
    import errores, plan_rol, sombra
    if not (s := sombra.serie(f, puuid)): return {}
    out = {k: v for k, x in plan_rol.MEDIDAS.items() if (v := x[3](s)) is not None}
    try:
        m, fr = _cargar(f), _cargar(pathlib.Path(f).parent / "timeline" / pathlib.Path(f).name)["info"]["frames"]
        ps = m["info"]["participants"]; me = next(p for p in ps if p["puuid"] == puuid)
        nv6 = (s["nivel"][6], s["nivel_rival"][6]) if len(s["nivel"]) > 6 and len(s.get("nivel_rival") or []) > 6 else None
        det = errores.detectar(errores.de_timeline(fr, me["participantId"], {p["participantId"]: p["teamId"] for p in ps}), nv6)
        out["errores"] = [{"t": round(t), "id": k} for k, ts in det.items() for t in ts]
        ev, pid = [e for x in fr for e in x["events"]], me["participantId"]
        tus = [e["timestamp"] for e in ev if e.get("type") == "CHAMPION_KILL" and e.get("victimId") == pid]
        out["minutos"] = {k: [_mm(t) for t in tus if a <= t < b] for k, a, b in (("muertes6", 0, 360_000), ("muertes14", 0, 840_000), ("muertes14_25", 840_000, 1_500_000)) if k in out}
        out["minutos"]["dragones14"] = [_mm(e["timestamp"]) for e in ev if e.get("type") == "ELITE_MONSTER_KILL" and e.get("monsterType") == "DRAGON"
                                        and e["timestamp"] <= 840_000 and e.get("killerTeamId") != me["teamId"]]
    except (TypeError, KeyError, StopIteration): pass
    return {**out, "t": s["t"]}


def _cargar(path):
    try: return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError): return None


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:] if argv is None else argv
    raw = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
    puuid = ((_cargar(raw / "perfil.json") or {}).get("account") or {}).get("puuid")
    fs = list(raw.glob("*_*.json"))
    if argv: fs = [f for f in fs if f.stem == argv[0] or f.stem.endswith("_" + argv[0])]
    import score
    ms = [(m, f) for f in fs if (m := score.cargar_partida(f)) and m["info"].get("gameCreation")]
    if not puuid or not ms:
        print("Sin partida que revisar."); return 1
    m, f = max(ms, key=lambda x: x[0]["info"]["gameCreation"])
    tl = _cargar(raw / "timeline" / f.name)
    print(f"Partida {f.stem}")
    if tl is None:
        print("Sin timeline: no hay momentos que mostrar."); return 0
    mo = momentos(m, tl, puuid)
    print("Momentos clave:" if mo else "Sin momentos clave.")
    for x in mo: print(f"  - {x['texto']}")
    s = muertes_sin_objetivo(m, tl, puuid)
    if s["total"]: print(f"Muertes que tu equipo no cambió por un objetivo: {s['n']} de {s['total']} ({s['ratio']:.0%})")
    for x in s["lista"]: print(f"  - {x['texto']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
