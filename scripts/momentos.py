"""Motor de momentos de Sombra: qué muestra la franja en cada foto. Puro: sin red, sin disco y sin reloj propio.
  paso(estado, foto, guion, ahora, aj) -> (estado, escena, anotaciones)
foto = companion.meta_fase (+ «proximo» y «avisos» del trabajador); guion = guion.armar; ahora = reloj local en s.
La escena tiene 3 zonas fijas (regla, sombra, marcas) y, a veces, un renglón o el panel al morir. Las anotaciones van a
la bitácora: cada marca, cada compra y cada interrupción, mostrada o no, con el motivo.
Solo datos, nunca órdenes (Riot: no dictar decisiones); todo lo que se muestra es tuyo o se ve con Tab."""
import copy

import errores, plan_rol

MARCAS = (6, 10, 14, 25)
ARRANQUE, LINEA, PELEAS = 90, 840, 1500  # s de juego: arranque, línea (0–14), peleas (14–25), tarde
SELLO_S, COMPRA_S, INTERRUPCION_S = 4, 8, 6  # cuánto dura cada renglón
LATIDO_CADA, LATIDO_S = 10, 0.5  # la próxima marca late una vez cada 10 s en su último minuto
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
            "ult_pelea": None, "items": None, "muerte": None, "cs": {}, "kp": {}, "t": None, "vistos": [], "errores": [], "nivel6": None, "fases": []}


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
    """Interrupciones que esta foto propone: [(id, dato, dibujo)]. Solo datos; cada id sale una vez por partida. dibujo: lo que
    lienzo pinta en el renglón en vez del texto (los niveles de esta foto, para que no contradiga al texto si espera)."""
    t, out = foto.get("t") or 0, []
    nv, nvr, rival = foto.get("nivel"), foto.get("nivel_rival"), foto.get("rival")
    if rival and nv is not None and nvr is not None and nvr > nv:
        dib = {"tipo": "nivel", "tu": nv, "rival": nvr, "campeon": rival}
        if 300 <= t <= 420: out.append(("nivel", f"Nivel {nv - nvr:+d} vs {rival}", dib))
        elif 600 <= t < LINEA: out.append(("regreso", f"Nivel {nv - nvr:+d} vs {rival} · min {int(t // 60)}", dib))
    for clave, corto in foto.get("avisos") or []:  # los del trabajador que siguen siendo datos (pico de ítems del rival)
        if clave.startswith("pico:"): out.append((clave, corto, None))
    vistos = set(e["vistos"]) | {p["id"] for p in e["pendientes"]}
    return [x for x in out if x[0] not in vistos]


def lista(g):
    """Las 4 marcas de la partida: las personales del guion (Fase 7: plan de rol y errores) o las fijas 6, 10, 14 y 25."""
    return (g or {}).get("marcas_p") or [{"id": str(m), "tipo": "fija", "etq": str(m), "min": m * 60} for m in MARCAS]


# Cómo se lee en vivo cada medida del plan de rol (plan_rol.MEDIDAS)
VIVO = {"muertes6": lambda f: f.get("muertes6"), "kp6": lambda f: f.get("participacion"), "kp25": lambda f: f.get("participacion"),
        "nivel3": lambda f: f["nivel"] - f["nivel_rival"] if f.get("nivel") is not None and f.get("nivel_rival") is not None else None,
        "cs10": lambda f: _cs(f), "muertes14": lambda f: f.get("muertes"),
        "dragones14": lambda f: ((f.get("objetivos") or {}).get("tuyos") or {}).get("dragones"),
        "muertes14_25": lambda f: f.get("muertes14_25")}
VIVO["nivel10"] = VIVO["nivel3"]
EXACTAS = ("muertes6", "muertes14_25")  # salen de los eventos: valen aunque la foto llegue tarde


def _fija(m, foto, g, tarde):
    """(ok, dato) de una marca fija (6, 10, 14, 25), o (None, None) sin dato."""
    meta = (((g or {}).get("marcas") or {}).get(str(m)) or {}).get("meta")
    if m == 6 and meta is not None and foto.get("muertes6") is not None:
        n = foto["muertes6"]
        return n <= meta, f"Marca 6 · {n} muerte{'' if n == 1 else 's'} · sombra {meta}"
    if m == 10 and meta is not None and _cs(foto) is not None and not tarde:
        return _cs(foto) >= meta, f"Marca 10 · ≈{_cs(foto)} CS · sombra {meta}"  # ≈: el CS en vivo llega de 10 en 10
    if m == 14 and not tarde and (o := foto.get("oro") or {}).get("tu") is not None and o.get("rival") is not None:
        d = round((o["tu"] - o["rival"]) / 50) * 50
        largo = f"{d:+d} oro en ítems vs {foto.get('rival')}"  # el «14» lo dice la moneda que lienzo dibuja delante
        return d >= 0, largo if foto.get("rival") and len(largo) <= RENGLON_MAX else f"{d:+d} oro en ítems"
    if m == 25 and foto.get("muertes14_25") is not None:
        tope = ((g or {}).get("regla") or {}).get("tope", 2)
        return foto["muertes14_25"] <= tope, f"Marca 25 · {foto['muertes14_25']} de {tope} · tu tope"
    return None, None


def _detectados(e, foto, t):
    """{error: [s, …]} de tus errores hasta ahora, con los eventos en vivo (errores.py: el mismo detector que la revisión)."""
    return errores.detectar(foto.get("eventos") or [], e.get("nivel6"), hasta=t)


def _sellar(e, foto, g, t, det):
    """Marcas que se deciden en esta foto: [(id, ok o None, dato, clase)]. None = sin dato (llegaste tarde a la partida).
    Un error se marca en cuanto pasa (sin interrumpir); evitado, al cerrar su ventana."""
    out = []
    for mk in lista(g):
        k = mk["id"]
        if k in e["marcas"]: continue
        if mk["tipo"] == "error":
            lo, hi = mk["ventana"]
            cae = [x for x in det.get(k) or [] if lo <= x < hi]
            if cae:
                out.append((k, False, f"{mk['nombre']} · min {int(cae[0] // 60)}", "error")); continue
            if t < mk["min"]: continue
            sin = k == "abajo_6" and e.get("nivel6") is None  # llegaste después del 6: no se sabe tu nivel
            out.append((k, None if sin else True, None if sin else f"{mk['nombre']}: evitado", "sello")); continue
        if t < mk["min"]: continue
        tarde = t >= mk["min"] + 60  # sin foto cerca del minuto: no se inventa
        if mk["tipo"] == "fija": ok, dato = _fija(int(k), foto, g, tarde)
        else:
            v = VIVO[k](foto) if k in VIVO and (not tarde or k in EXACTAS) else None
            ok = plan_rol.cumple(k, v, mk["meta"]) if v is not None else None
            dato = f"{mk['nombre']}: {'≈' if k == 'cs10' else ''}{plan_rol.valor(k, v)} · victorias {plan_rol.valor(k, mk['meta'])}" if v is not None else None
        if dato and len(x := dato + (" · cumplida" if ok else " · sin cumplir")) <= RENGLON_MAX: dato = x
        out.append((k, ok, dato, "sello"))
    for k, ok, _, _ in out: e["marcas"][k] = ok
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
        return {"num": f"{d:+d}" if d else "=", "etq": f"CS vs {de}", "color": "salvia" if d >= 0 else "oro", "trazo": trazo,
                "icono": "minion", "anillo": round(min(1.0, _cs(foto) / s), 3) if s else 1.0}  # el minion en un anillo que se llena hacia tu sombra
    s, kp = _curva(sb["kp"], t), foto.get("participacion")
    if s is None or kp is None: return {"num": "—", "etq": f"peleas vs {de}", "color": "gris", "trazo": None}
    d = round((kp - s) * 100)
    return {"num": f"{d:+d}%" if d else "=", "etq": f"peleas vs {de}", "color": "salvia" if d >= 0 else "oro", "trazo": trazo,
            "icono": "espadas", "anillo": round(min(1.0, kp / s), 3) if s else 1.0}


ROL = {"TOP": "top", "JUNGLE": "jungla", "MIDDLE": "mid", "BOTTOM": "bot", "UTILITY": "support"}


def _en(c, i): return c[i] if 0 <= i < len(c) else None


def _zona_regla(foto, g):
    tope = ((g or {}).get("regla") or {}).get("tope", 2)
    m = foto.get("muertes14") if (foto.get("t") or 0) < PELEAS else foto.get("muertes14_25")
    m = m or 0
    z = {"tope": tope, "apagadas": min(m, tope), "etq": "Tu tope", "color": "rosa" if m < tope else "oro" if m == tope else "rojo"}
    t, nv, nvr = foto.get("t") or 0, foto.get("nivel"), foto.get("nivel_rival")
    err = next((x for x in lista(g) if x["id"] == "abajo_6" and x["tipo"] == "error"), None)
    if err and 330 <= t < 420 and nv is not None and nvr is not None and nv < nvr and z["color"] != "rojo":  # antes de tu error: el dato, no la orden
        z.update(etq=f"Nivel {nv - nvr} · E{err['rango']}", color="oro")  # 3 palabras: la zona Sombra puede llevar 6
    return z


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
    return [x for x in (_linea_error(e, foto, g), l1, l2) if x][:2] or None


def _linea_error(e, foto, g):
    """Al morir, si esta muerte toca uno de tus errores vigilados: el dato (Fase 7). Si no, tu tipo de muerte más común si es gank."""
    m, err = e["muerte"], {x["id"]: x for x in lista(g) if x["tipo"] == "error"}
    nv, nvr = foto.get("nivel"), foto.get("nivel_rival")
    if (x := err.get("abajo_6")) and 330 <= m < 420 and nv is not None and nvr is not None and nv < nvr:
        return f"Nivel abajo al 6 · {x.get('veces', 0) + 1}.ª en 20 partidas"
    if (x := err.get("sin_objetivo")) and 840 <= m < 1500:
        obj = [ev["t"] for ev in foto.get("eventos") or [] if ev["k"] == "obj" and ev.get("nuestro") and m - errores.MARGEN_OBJ <= ev["t"]]
        return f"Objetivo de tu equipo · min {int(obj[0] // 60)}" if obj else f"Sin objetivo del equipo · error {x['rango']}"
    if (g or {}).get("muerte_comun") == "gank": return "Tu muerte más común: gank"
    return None


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

    if e.get("nivel6") is None and 360 <= t < 400 and foto.get("nivel") is not None and foto.get("nivel_rival") is not None:
        e["nivel6"] = [foto["nivel"], foto["nivel_rival"]]  # tu nivel y el de tu rival al minuto 6 (abajo_6)
    det = _detectados(e, foto, t)
    for k, ts in det.items():  # cada error que pasa queda en la bitácora (sin interrumpir), vigilado o no
        for x in ts:
            if [k, round(x)] not in e["errores"]:
                e["errores"].append([k, round(x)]); notas.append(dict(t=round(x), id=k, clase="error", dato=errores.NOMBRE[k], mostrado=False, motivo="sin interrumpir"))
    puesto = False  # dos sellos en la misma foto: el renglón es del primero; el otro se ve en su punto
    for k, ok, dato, clase in _sellar(e, foto, g, t, det):  # sellar no es interrupción: lugar y minuto conocidos
        nombre = f"marca{k}" if k.isdigit() else f"marca_{k}"
        if clase == "error": nota(nombre, "sello", dato, False, "sin interrumpir"); continue  # el punto se pone rojo y ya
        ver = bool(dato) and not foto.get("muerto") and not puesto
        nota(nombre, "sello", dato, ver, None if ver else "sin dato" if not dato else "muerto" if foto.get("muerto") else "otro sello")
        if ver:
            dib = {"tipo": "oro", "min": 14, "num": dato.split(" ")[0]} if k == "14" else None  # solo el valor de ítems (Tab)
            e["renglon"] = [dato, ahora + SELLO_S, "sello", dib]; e["brillo"] = [k, ahora + BRILLO_S]; puesto = True
    if not foto.get("muerto") and (not e["renglon"] or ahora >= e["renglon"][1]) and (f := _fase(e, g, t)):  # al empezar cada fase de tu plan
        e["renglon"] = [f, ahora + INTERRUPCION_S, "fase"]; nota("fase", "fase", f, True)

    items = [str(i[0]) for i in foto.get("items") or []]
    if e["items"] is not None and items != e["items"] and t >= ARRANQUE and not e.get("regreso"):  # tu primer regreso contra el de tu sombra
        e["regreso"] = True
        if (r := ((g.get("sombra") or {}).get("regreso"))) is not None:
            dato = f"Primer regreso · sombra: min {r:g}".replace(".", ",")
            nota("regreso1", "compra", f"{dato} (tú: min {t / 60:.1f})".replace(".", ","), True); e["renglon"] = [dato, ahora + COMPRA_S, "compra"]
    if e["items"] is not None and items != e["items"] and (p := foto.get("proximo")) and (aj.get("franja_build", True) is not False)             and not (e["renglon"] and e["renglon"][0].startswith("Primer regreso") and ahora < e["renglon"][1]):
        dato = f"{p['nombre']} · faltan {p['falta']}"[:RENGLON_MAX]
        nota("compra", "compra", dato, True); e["renglon"] = [dato, ahora + COMPRA_S, "compra"]
    e["items"] = items

    for i, dato, dib in candidatas(e, foto, g):
        if aj.get(f"momento_{i.split(':')[0]}", True) is False: e["vistos"].append(i); nota(i, "interrupcion", dato, False, "apagado"); continue
        e["pendientes"].append({"id": i, "dato": dato, "desde": ahora, "dibujo": dib})
    quedan = []
    for p in e["pendientes"]:
        ok, motivo = puede_tocar(e, foto, ahora, aj)
        renglon_libre = not e["renglon"] or ahora >= e["renglon"][1]
        if ok and renglon_libre:
            e["interrupciones"] += 1; e["ult_interrupcion"] = ahora; e["vistos"].append(p["id"])
            e["renglon"] = [p["dato"], ahora + INTERRUPCION_S, "interrupcion", p.get("dibujo")]; nota(p["id"], "interrupcion", p["dato"], True)
        elif ahora - p["desde"] >= ESPERA_MAX or motivo in ("sin presupuesto", "después del 25", "solo marcas"):
            e["vistos"].append(p["id"]); nota(p["id"], "interrupcion", p["dato"], False, motivo or "renglón ocupado")
        else: quedan.append(p)
    e["pendientes"] = quedan

    renglon = dibujo = None
    if e["renglon"] and ahora < e["renglon"][1]: renglon, dibujo = e["renglon"][0], (e["renglon"][3:] or [None])[0]
    elif t < ARRANQUE and (mu := g.get("matchup")):
        renglon = mu["nota"][:RENGLON_MAX] if mu.get("nota") else f"vs {g.get('rival')} · {mu['v']} de {mu['n']} tuyas" if mu.get("n") else None
    panel = _panel(e, foto, g, t)
    if panel and renglon: panel, renglon, dibujo = panel[:1] + [renglon], None, None  # muerto: el renglón pasa al panel (como texto)
    ms = lista(g)
    proxima = next((m["id"] for m in ms if m["id"] not in e["marcas"] and m["tipo"] != "error"), None)
    cerca = lambda m: m["id"] == proxima and m["min"] - 60 <= t < m["min"]
    escena = {"campeon": foto.get("campeon"), "regla": _zona_regla(foto, g), "sombra": _zona_sombra(e, foto, g, t),
              "marcas": [{"id": m["id"], "min": m["min"] // 60, "etq": m["etq"], "error": m["tipo"] == "error",
                          "estado": ("sin" if e["marcas"][m["id"]] is None else e["marcas"][m["id"]]) if m["id"] in e["marcas"] else None,
                          "proxima": cerca(m), "late": cerca(m) and ahora % LATIDO_CADA < LATIDO_S} for m in ms],
              "renglon": renglon, "dibujo": dibujo, "panel": panel, "brillo": b[0] if (b := e.get("brillo")) and ahora < b[1] else None, "opacidad": OPACIDAD_TARDE if t >= TARDE_S else 1.0}
    return e, escena, notas


FASES = {"1": (ARRANQUE, "0–6"), "2": (360, "6–14"), "3": (840, "14–25")}


def _fase(e, g, t):
    """El renglón al empezar cada fase de tu plan de rol (en sus primeros 20 s, una vez): «6–14 · CS al 10 · victorias 71»."""
    fs = (((g or {}).get("plan") or {}).get("fases")) or {}
    for k, (ini, nombre) in FASES.items():
        x = fs.get(k) or fs.get(int(k))  # en JSON las llaves son texto; recién armado, números
        if ini <= t < ini + 20 and k not in e["fases"] and x:
            e["fases"].append(k)
            v = plan_rol.valor(x["id"], x["v"])
            largo, corto = f"{nombre} · {x['etq']} · victorias {v}", f"{x['etq']} · victorias {v}"
            return largo if len(largo) <= RENGLON_MAX else corto[:RENGLON_MAX]
    return None


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
    ps = [m for m in g.get("marcas_p") or [] if m["tipo"] == "plan"]
    es = [m for m in g.get("marcas_p") or [] if m["tipo"] == "error"]
    l4 = None
    if ps or es:  # Fase 7: tu plan de rol y tus errores vigilados en lugar de las tasas de las marcas fijas
        l3 = ("Tu plan: " + " · ".join(f"{m['nombre']} {plan_rol.valor(m['id'], m['meta'])}" for m in ps)) if ps else None
        l4 = ("Vigilas: " + " · ".join(f"E{m['rango']} {m['nombre'].lower()}" for m in es)) if es else None
        if r.get("racha"): l2 = (l2 + " · " if l2 else "") + f"racha {r['racha']}"
    return [x for x in (l1, l2, l3, l4) if x]


def carta_fin(e, cumplida=None, racha=None):
    """La carta al terminar: marcas cumplidas de las que tienen dato (None = sin dato), tu tope 14–25 y tu racha (ciclo.py)."""
    ms = list(((e or {}).get("marcas") or {}).values()); con = [v for v in ms if v is not None]
    sin = f" · {len(ms) - len(con)} sin dato" if len(ms) > len(con) else ""  # esas no se evaluaron
    out = [f"{sum(con)} de {len(con)} marcas con dato{sin}"] if con else ["Sin marcas: la partida acabó antes"]
    if cumplida is not None: out.append(f"Tu tope 14–25: {'cumplido' if cumplida else 'sin cumplir'}" + (f" · racha {racha}" if racha else ""))
    return out


def textos(escena):
    """Los textos de la escena en orden de lectura (para validar palabras e imperativos)."""
    if not escena: return []
    out = [escena["regla"]["etq"], escena["sombra"]["num"], escena["sombra"]["etq"]] + [str(m.get("etq", m["min"])) for m in escena["marcas"]]
    return out + ([escena["renglon"]] if escena.get("renglon") else []) + (escena.get("panel") or [])


def palabras_vivo(escena):
    """Palabras de las 3 zonas (sin renglón ni panel): el límite con el campeón vivo es 9."""
    if not escena: return 0
    return sum(len([w for w in x.split() if w not in ("·", "—")]) for x in (escena["regla"]["etq"], escena["sombra"]["num"], escena["sombra"]["etq"]) if x)
