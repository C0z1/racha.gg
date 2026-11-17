"""Motor de momentos de Sombra: qué muestra la franja en cada foto. Puro: sin red, sin disco y sin reloj propio.
  paso(estado, foto, guion, ahora, aj) -> (estado, escena, anotaciones)
foto = companion.meta_fase (+ «proximo» y «avisos» del trabajador); guion = guion.armar; ahora = reloj local en s.
La escena tiene 3 zonas fijas (regla, sombra, marcas) y, a veces, un renglón o el panel al morir. Las anotaciones van a
la bitácora: cada marca, cada compra y cada interrupción, mostrada o no, con el motivo.
Solo datos, nunca órdenes (Riot: no dictar decisiones); todo lo que se muestra es tuyo o se ve con Tab."""
import copy

MARCAS = (6, 10, 14, 25)
ARRANQUE, LINEA, PELEAS = 90, 840, 1500  # s de juego: arranque, línea (0–14), peleas (14–25), tarde
SELLO_S, COMPRA_S, INTERRUPCION_S = 4, 8, 6  # cuánto dura cada renglón
BRILLO_S = 0.6  # sellar una marca: un brillo de 600 ms en su punto (nada parpadea más de una vez)
MAX_INTERRUPCIONES, ENTRE_INTERRUPCIONES = 3, 120  # contrato de atención: por partida y s entre una y otra
CAIDA_VIDA, CAIDA_S, KILL_S = 0.08, 3, 8  # pelea: tu vida bajó 8 % en 3 s, o hubo un ChampionKill hace menos de 8 s
CALMA_S, ESPERA_MAX = 6, 45  # una interrupción espera hasta 45 s a tener 6 s seguidos de calma
MUERTO_DESDE, MUERTO_ANTES = 2, 3  # el panel al morir: 2 s después de morir hasta 3 s antes de revivir
OPACIDAD_TARDE = 0.6
TARDE_S = PELEAS
TRAZO_MIN = 5  # minutos del trazo de la zona Sombra
RENGLON_MAX = 34  # caracteres del renglón (6 palabras)


def nuevo():
    return {"marcas": {}, "interrupciones": 0, "ult_interrupcion": None, "pendientes": [], "renglon": None, "vidas": [],
            "ult_pelea": None, "items": None, "muerte": None, "cs": {}, "kp": {}, "t": None, "vistos": []}


def _cs(foto):
    """Tu CS estimado: el creepScore en vivo sube de 10 en 10 (medido en 18 836 fotos), así que el real está ~5 arriba."""
    return foto["cs"] + 5 if foto.get("cs") is not None else None  # shortcut: ±5 CS de error; si Riot da el CS exacto, quitar el +5


def _curva(c, t):
    """La curva de la sombra a los t s, interpolada entre minutos; None si la sombra no llega a ese minuto."""
    i = int(t // 60)
    if i + 1 >= len(c) or c[i] is None or c[i + 1] is None: return c[i] if i < len(c) else None
    return c[i] + (c[i + 1] - c[i]) * (t % 60) / 60


def en_pelea(e, foto, ahora):
    """Tu vida bajó CAIDA_VIDA o más en los últimos CAIDA_S s, o hubo un ChampionKill hace menos de KILL_S s de juego."""
    t, k = foto.get("t") or 0, foto.get("ult_kill")
    if k is not None and 0 <= t - k < KILL_S: return True
    vs = [v for a, v in e["vidas"] if ahora - a <= CAIDA_S]
    return bool(vs) and max(vs) - vs[-1] >= CAIDA_VIDA


def calma(e, ahora):
    """s seguidos sin pelea (desde la última vez que lo fue)."""
    return float("inf") if e["ult_pelea"] is None else ahora - e["ult_pelea"]


def puede_tocar(e, foto, ahora, aj):
    """(sí/no, motivo): todo el contrato de atención. El motivo va a la bitácora cuando no se muestra."""
    tope = 1 if (aj or {}).get("franja_poco") else MAX_INTERRUPCIONES  # «no» dos veces a «¿Te sirvieron?»
    if (aj or {}).get("solo_marcas"): return False, "solo marcas"
    if e["interrupciones"] >= tope: return False, "sin presupuesto"
    if (foto.get("t") or 0) >= TARDE_S: return False, "después del 25"
    if e["ult_interrupcion"] is not None and ahora - e["ult_interrupcion"] < ENTRE_INTERRUPCIONES: return False, "muy seguido"
    if foto.get("muerto"): return True, None  # la mejor ventana: muerto no hay pelea que estorbar
    if en_pelea(e, foto, ahora): return False, "en pelea"
    if calma(e, ahora) < CALMA_S: return False, "sin calma"
    return True, None


def candidatas(e, foto, g):
    """Interrupciones que esta foto propone: [(id, dato)]. Solo datos; cada id sale una vez por partida."""
    t, out = foto.get("t") or 0, []
    nv, nvr, rival = foto.get("nivel"), foto.get("nivel_rival"), foto.get("rival")
    if rival and nv is not None and nvr is not None and nvr > nv:
        if 300 <= t <= 420: out.append(("nivel", f"Nivel {nv - nvr:+d} vs {rival}"))
        elif 600 <= t < LINEA: out.append(("regreso", f"Nivel {nv - nvr:+d} vs {rival} · min {int(t // 60)}"))
    for clave, corto in foto.get("avisos") or []:  # los del trabajador que siguen siendo datos (pico de ítems del rival)
        if clave.startswith("pico:"): out.append((clave, corto))
    vistos = set(e["vistos"]) | {p["id"] for p in e["pendientes"]}
    return [(i, d) for i, d in out if i not in vistos]


def _sellar(e, foto, g, t):
    """Marcas que cruzaron su minuto en esta foto: [(minuto, ok o None, dato)]. None = sin dato (llegaste tarde a la partida)."""
    mk, out = (g or {}).get("marcas") or {}, []
    for m in MARCAS:
        if str(m) in e["marcas"] or t < m * 60: continue
        meta, tarde = (mk.get(str(m)) or {}).get("meta"), t >= m * 60 + 60  # sin foto cerca del minuto: no se inventa
        ok = dato = None
        if m == 6 and meta is not None and foto.get("muertes6") is not None:
            ok, dato = foto["muertes6"] <= meta, f"Marca 6 · {foto['muertes6']} muerte{'' if foto['muertes6'] == 1 else 's'} · sombra {meta}"
        elif m == 10 and meta is not None and _cs(foto) is not None and not tarde:
            ok, dato = _cs(foto) >= meta, f"Marca 10 · {foto['cs']} CS · sombra {meta}"
        elif m == 14 and not tarde and (o := foto.get("oro") or {}).get("tu") is not None and o.get("rival") is not None:
            d = round((o["tu"] - o["rival"]) / 50) * 50
            ok, dato = d >= 0, f"Marca 14 · {d:+d} de oro en ítems"
        elif m == 25 and foto.get("muertes14_25") is not None:
            tope = ((g or {}).get("regla") or {}).get("tope", 2)
            ok, dato = foto["muertes14_25"] <= tope, f"Marca 25 · {foto['muertes14_25']} de {tope} · tu tope"
        if dato and len(x := dato + (" · cumplida" if ok else " · sin cumplir")) <= RENGLON_MAX: dato = x
        e["marcas"][str(m)] = ok; out.append((m, ok, dato))
    return out


def _zona_sombra(e, foto, g, t):
    sb = (g or {}).get("sombra") or {}
    if not sb.get("alcance"): return {"num": "—", "etq": f"Sin sombra aún · {sb.get('n', 0)} de 8", "color": "gris", "trazo": None}
    de = "sombra" if sb["alcance"] == "campeon" else f"sombra de {ROL.get((g or {}).get('pos'), 'tu rol')}"
    if t < ARRANQUE: return {"num": str(sb["n"]), "etq": f"victorias · tu {de}", "color": "gris", "trazo": None}
    m = int(t // 60); trazo = [[e["cs" if t < LINEA else "kp"].get(str(i)), _en(sb["cs" if t < LINEA else "kp"], i)] for i in range(max(0, m - TRAZO_MIN + 1), m + 1)]
    if t < LINEA:
        s = _curva(sb["cs"], t)
        if s is None or _cs(foto) is None: return {"num": "—", "etq": f"CS vs {de}", "color": "gris", "trazo": None}
        d = round((_cs(foto) - s) / 5) * 5  # en pasos de 5: el CS en vivo no da más precisión
        return {"num": f"{d:+d}" if d else "=", "etq": f"CS vs {de}", "color": "salvia" if d >= 0 else "oro", "trazo": trazo}
    s, kp = _curva(sb["kp"], t), foto.get("participacion")
    if s is None or kp is None: return {"num": "—", "etq": f"peleas vs {de}", "color": "gris", "trazo": None}
    d = round((kp - s) * 100)
    return {"num": f"{d:+d}%" if d else "=", "etq": f"peleas vs {de}", "color": "salvia" if d >= 0 else "oro", "trazo": trazo}


ROL = {"TOP": "top", "JUNGLE": "jungla", "MIDDLE": "mid", "BOTTOM": "bot", "UTILITY": "support"}


def _en(c, i): return c[i] if 0 <= i < len(c) else None


def _zona_regla(foto, g):
    tope = ((g or {}).get("regla") or {}).get("tope", 2)
    m = foto.get("muertes14") if (foto.get("t") or 0) < PELEAS else foto.get("muertes14_25")
    m = m or 0
    return {"tope": tope, "apagadas": min(m, tope), "etq": "Tu tope", "color": "rosa" if m < tope else "oro" if m == tope else "rojo"}


def _panel(e, foto, g, t):
    """Los 2 renglones al morir; None si no toca."""
    if not foto.get("muerto") or e["muerte"] is None: return None
    tope = ((g or {}).get("regla") or {}).get("tope", 2)
    rev = foto.get("revive")
    if (foto.get("t") or 0) - e["muerte"] < MUERTO_DESDE or (rev is not None and rev <= MUERTO_ANTES): return None
    if LINEA <= t < PELEAS: l1 = f"Muerte {foto.get('muertes14') or 0} de {tope} · tu tope"
    else:
        s = _en(((g or {}).get("sombra") or {}).get("muertes") or [], int(t // 60))
        l1 = f"Muertes {foto.get('muertes', '?')} · tu sombra {s}" if s is not None else None
    o = foto.get("objetivos") or {}
    tu, el = o.get("tuyos") or {}, o.get("rival") or {}
    l2 = f"Dragones {tu.get('dragones', 0)}–{el.get('dragones', 0)} · Torres {tu.get('torres', 0)}–{el.get('torres', 0)}" if "tuyos" in o else None
    return [x for x in (l1, l2) if x] or None


def paso(estado, foto, guion, ahora, aj=None):
    """Un paso del motor. estado None = partida nueva. Devuelve (estado, escena o None, anotaciones [{t, id, clase, dato, mostrado, motivo}])."""
    e = copy.deepcopy(estado) if estado else nuevo()
    if not foto or foto.get("modo") == "ARAM": return e, None, []  # shortcut: ARAM sin Sombra (no hay series de ARAM); queda la franja clásica
    t, g, aj, notas = foto.get("t") or 0, guion or {}, aj or {}, []
    if e["t"] is not None and t < e["t"] - 30: e = nuevo()  # otra partida
    e["t"] = t
    if foto.get("vida") is not None: e["vidas"] = [x for x in e["vidas"] if ahora - x[0] <= CAIDA_S] + [[ahora, foto["vida"]]]
    if en_pelea(e, foto, ahora): e["ult_pelea"] = ahora
    if foto.get("cs") is not None: e["cs"][str(int(t // 60))] = _cs(foto)
    if foto.get("participacion") is not None: e["kp"][str(int(t // 60))] = foto["participacion"]
    if foto.get("muerto") and e["muerte"] is None: e["muerte"] = t
    if not foto.get("muerto"): e["muerte"] = None
    nota = lambda i, clase, dato, mostrado, motivo=None: notas.append(dict(t=round(t), id=i, clase=clase, dato=dato, mostrado=mostrado, motivo=motivo))

    for m, ok, dato in _sellar(e, foto, g, t):  # sellar no es interrupción: lugar y minuto conocidos
        nota(f"marca{m}", "sello", dato, bool(dato) and not foto.get("muerto"), None if dato else "sin dato")
        if dato and not foto.get("muerto"): e["renglon"] = [dato, ahora + SELLO_S, "sello"]; e["brillo"] = [m, ahora + BRILLO_S]

    items = [str(i[0]) for i in foto.get("items") or []]
    if e["items"] is not None and items != e["items"] and (p := foto.get("proximo")) and (aj.get("franja_build", True) is not False):
        dato = f"{p['nombre']} · faltan {p['falta']}"[:RENGLON_MAX]
        nota("compra", "compra", dato, True); e["renglon"] = [dato, ahora + COMPRA_S, "compra"]
    e["items"] = items

    for i, dato in candidatas(e, foto, g):
        if aj.get(f"momento_{i.split(':')[0]}", True) is False: e["vistos"].append(i); nota(i, "interrupcion", dato, False, "apagado"); continue
        e["pendientes"].append({"id": i, "dato": dato, "desde": ahora})
    quedan = []
    for p in e["pendientes"]:
        ok, motivo = puede_tocar(e, foto, ahora, aj)
        renglon_libre = not e["renglon"] or ahora >= e["renglon"][1]
        if ok and renglon_libre:
            e["interrupciones"] += 1; e["ult_interrupcion"] = ahora; e["vistos"].append(p["id"])
            e["renglon"] = [p["dato"], ahora + INTERRUPCION_S, "interrupcion"]; nota(p["id"], "interrupcion", p["dato"], True)
        elif ahora - p["desde"] >= ESPERA_MAX or motivo in ("sin presupuesto", "después del 25", "solo marcas"):
            e["vistos"].append(p["id"]); nota(p["id"], "interrupcion", p["dato"], False, motivo or "renglón ocupado")
        else: quedan.append(p)
    e["pendientes"] = quedan

    renglon = None
    if e["renglon"] and ahora < e["renglon"][1]: renglon = e["renglon"][0]
    elif t < ARRANQUE and (mu := g.get("matchup")):
        renglon = mu["nota"][:RENGLON_MAX] if mu.get("nota") else f"vs {g.get('rival')} · {mu['v']} de {mu['n']} tuyas" if mu.get("n") else None
    panel = _panel(e, foto, g, t)
    if panel and renglon: panel, renglon = panel[:1] + [renglon], None  # muerto: el renglón pasa al panel
    proxima = next((m for m in MARCAS if str(m) not in e["marcas"]), None)
    escena = {"regla": _zona_regla(foto, g), "sombra": _zona_sombra(e, foto, g, t),
              "marcas": [{"min": m, "estado": ("sin" if e["marcas"][str(m)] is None else e["marcas"][str(m)]) if str(m) in e["marcas"] else None,
                          "proxima": m == proxima and m * 60 - 60 <= t < m * 60} for m in MARCAS],
              "renglon": renglon, "panel": panel, "brillo": b[0] if (b := e.get("brillo")) and ahora < b[1] else None, "opacidad": OPACIDAD_TARDE if t >= TARDE_S else 1.0}
    return e, escena, notas


def carta_carga(g):
    """La carta de la pantalla de carga (antes de que responda la Live Client Data): 3 renglones o None sin guion."""
    if not g: return None
    mu, r, mk = g.get("matchup") or {}, g.get("regla") or {}, g.get("marcas") or {}
    l1 = f"{g['campeon']} vs {g['rival']} · {mu['v']} de {mu['n']} tuyas" if mu.get("n") else f"{g['campeon']} vs {g.get('rival') or '?'}"
    l2 = (f"{r['corta']} · la cumples {r['ok']} de {r['n']}" if r.get("n") else r["corta"]) if r.get("corta") else None
    xs = [(m, x) for m, x in mk.items() if x.get("n")]
    if xs and len({x["n"] for _, x in xs}) == 1: l3 = f"Marcas {'/'.join(m for m, _ in xs)}: {' · '.join(str(x['ok']) for _, x in xs)} de {xs[0][1]['n']}"
    else: l3 = " · ".join(f"marca {m}: {x['ok']} de {x['n']}" for m, x in xs) or None
    if r.get("racha"): l3 = (l3 + " · " if l3 else "") + f"racha {r['racha']}"
    return [x for x in (l1, l2, l3) if x]


def carta_fin(e, cumplida=None, racha=None):
    """La carta al terminar: marcas cumplidas, tu regla y tu racha (ciclo.py)."""
    ok = sum(v is True for v in (e or {}).get("marcas", {}).values())
    out = [f"{ok} de {len(MARCAS)} marcas"]
    if cumplida is not None: out.append(f"Tu regla: {'cumplida' if cumplida else 'sin cumplir'}" + (f" · racha {racha}" if racha else ""))
    return out


def textos(escena):
    """Los textos de la escena en orden de lectura (para validar palabras e imperativos)."""
    if not escena: return []
    out = [escena["regla"]["etq"], escena["sombra"]["num"], escena["sombra"]["etq"]] + [str(m["min"]) for m in escena["marcas"]]
    return out + ([escena["renglon"]] if escena.get("renglon") else []) + (escena.get("panel") or [])


def palabras_vivo(escena):
    """Palabras de las 3 zonas (sin renglón ni panel): el límite con el campeón vivo es 9."""
    if not escena: return 0
    return sum(len([w for w in x.split() if w not in ("·", "—")]) for x in (escena["regla"]["etq"], escena["sombra"]["num"], escena["sombra"]["etq"]) if x)
