"""Repite una partida grabada (datos/vivo/*.jsonl) por companion.paso_vivo y la pastilla (overlay.estado), sin LoL ni red.
Uso: python herramientas/replay.py <archivo.jsonl> [--validar] [--precios] [--momentos]
--momentos: la franja Sombra (momentos.paso con el guion de tus partidas): «mm:ss | regla | sombra | marcas | renglón».
Cada foto: «mm:ss | franja: … | aviso: …». --validar comprueba invariantes y sale con 1 si alguna falla.
Por defecto no usa Data Dragon (sin pieza de Oro ni aviso de pico) para que la salida sea idéntica en cualquier máquina; --precios lo activa."""
import argparse, contextlib, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import companion, overlay, momentos

MAX_PIEZAS = 9  # textos de la pastilla: número y etiqueta ×2, flecha, chip, y al morir el marcador y tu regla
AVISO_CORTO = 48  # plan F1: caracteres del aviso en la franja
LISTA_NEGRA = (  # lo que la franja y los avisos nunca dicen; se busca como palabra completa
    "cooldown", "enfriamiento", "flash", "destello", "ultimate", "definitiva", "smite", "castigo",  # timers que no se ven
    "respawn", "reaparece", "mmr", "elo", "probabilidad", "campamento",  # reaparición rival, rating, conclusiones, jungla
    "el jungla está", "el jungla va", "troll", "inting", "afk",
    "compra", "cómpralo", "vuelve a base", "backea", "recall")  # la franja dice el dato del ítem, nunca la orden  # posiciones que no ves y juicios de compañeros
VENTANAS = {"aviso_nivel": (5, 7), "aviso_regreso": (10, 14), "aviso_muertes": (14, 24), "aviso_minions": (10, 11)}  # minuto de juego; el pico no tiene ventana
PIEZAS_LINEA = re.compile(r"^(ritmo|CS vs|Nivel |[+-]\d+$)")  # textos de la pastilla que solo existen en la Grieta
BORRAR = {"rawDescription", "rawDisplayName", "rawChampionName", "rawSkinName", "skinID", "skinName", "fullRunes", "runes",
          "abilities", "championStats", "summonerSpells", "teamRelativeColors"}  # pesan y no los usa nada del replay


def cargar(ruta):
    """Fotos en orden; acepta {"foto": …} y descarta fotos repetidas (mismo gameTime) o sin reloj."""
    out, vistos = [], set()
    for l in pathlib.Path(ruta).read_text(encoding="utf-8").splitlines():
        if not l.strip(): continue
        d = json.loads(l); d = d.get("foto", d) if isinstance(d, dict) else d
        t = ((d or {}).get("gameData") or {}).get("gameTime")
        if t is None or t in vistos: continue
        vistos.add(t); out.append(companion.limpia(d))  # como vivo(): la práctica trae "items": {"error": …}
    return out


def anonimizar(fotos):
    """Copia de las fotos con la identidad de cada jugador cambiada por J1.. (tú por Yo#TEST) en todo texto exacto, y sin campos pesados."""
    ap = fotos[0].get("activePlayer") or {}
    mios = {ap.get(k) for k in ("riotId", "summonerName", "riotIdGameName")} - {None, ""}
    mapa, n = {}, 0
    for p in [p for d in fotos for p in d.get("allPlayers") or []]:
        nombres = {p.get(k) for k in ("riotId", "riotIdGameName", "summonerName")} - {None, ""}
        if not nombres or nombres <= set(mapa): continue
        if nombres & mios: g = "Yo"
        else: n += 1; g = f"J{n}"
        for k in ("riotId", "summonerName"):
            if p.get(k): mapa[p[k]] = g + "#TEST"
        if p.get("riotIdGameName"): mapa[p["riotIdGameName"]] = g
        if p.get("riotIdTagLine"): mapa.setdefault(p["riotIdTagLine"], "TEST")
    def rec(x):
        if isinstance(x, dict): return {k: rec(v) for k, v in x.items() if k not in BORRAR}
        if isinstance(x, list): return [rec(v) for v in x]
        return mapa.get(x, x) if isinstance(x, str) else x
    return [rec(d) for d in fotos]


@contextlib.contextmanager
def sin_precios():
    """Sin Data Dragon (ni oro ni ítems completos): la salida no depende de la caché de la máquina; restaura al salir."""
    p, l = companion.precios, companion.LEGENDARIOS
    companion.precios, companion.LEGENDARIOS = (lambda: {}), set()
    try: yield
    finally: companion.precios, companion.LEGENDARIOS = p, l


def reloj(t): return f"{int(t) // 60:02d}:{int(t) % 60:02d}"


def repetir(fotos, aj=None):
    """[{t, d, meta, franja:[(texto,color)], avisos:[(clave,texto,minuto)]}] por foto; el reloj local = gameTime (edad 0)."""
    estado, out = {"avisado": set()}, []
    for d in fotos:
        t = d["gameData"]["gameTime"]
        meta, avisos = companion.paso_vivo(d, estado, aj or {})
        if meta: meta = {**meta, "recibido": t}
        out.append({"t": t, "d": d, "meta": meta, "franja": [(x, None) for x in overlay.textos(overlay.estado(meta, t, aj))], "avisos": avisos})
    return out


def texto(r):
    return f"{reloj(r['t'])} | franja: {' · '.join(x[0] for x in r['franja'])} | aviso: {' / '.join(getattr(a[1], 'corto', a[1]) for a in r['avisos'])}"


def _eventos(d): return ((d or {}).get("events") or {}).get("Events") or []


def validar(rs):
    """Lista de fallos (texto); vacía si todo cuadra."""
    f = []
    for r in rs:
        t = reloj(r["t"])
        if len(r["franja"]) > MAX_PIEZAS: f.append(f"{t}: {len(r['franja'])} piezas en la franja (máx. {MAX_PIEZAS})")  # (a)
        if len(r["avisos"]) > 1: f.append(f"{t}: {len(r['avisos'])} avisos a la vez (máx. 1)")
        for clave, txt, _ in r["avisos"]:  # F1: lo que sale en la franja cabe de reojo
            if len(getattr(txt, "corto", "") or "") > AVISO_CORTO or not getattr(txt, "corto", None): f.append(f"{t}: aviso {clave} sin corto de ≤ {AVISO_CORTO} caracteres")
        for clave, _, minuto in r["avisos"]:  # (d)
            lo, hi = VENTANAS.get(clave, (0, 10 ** 6))
            if not lo <= minuto <= hi: f.append(f"{t}: aviso {clave} fuera de su ventana {lo}-{hi} (min {minuto})")
        if r["d"]["gameData"].get("gameMode", "CLASSIC") != "CLASSIC":  # (e)
            f += [f"{t}: pieza de línea «{x[0]}» fuera de CLASSIC" for x in r["franja"] if PIEZAS_LINEA.match(x[0])]
        for txt in [x[0] for x in r["franja"]] + [a[1] for a in r["avisos"]] + [getattr(a[1], "corto", "") or "" for a in r["avisos"]]:  # (f)
            if mal := [w for w in LISTA_NEGRA if re.search(r"\b" + re.escape(w) + r"\b", txt.lower())]: f.append(f"{t}: palabra prohibida {mal} en «{txt}»")
    if rs:  # (c)
        d = rs[-1]["d"]; me, _ = companion.yo_rival(d)
        if me:
            ids = {me.get("riotIdGameName"), me.get("summonerName"), me.get("riotId"), (me.get("riotId") or "").split("#")[0]} - {None, ""}
            ev = sum(1 for e in _eventos(d) if e.get("EventName") == "ChampionKill" and e.get("VictimName") in ids)
            marc = (me.get("scores") or {}).get("deaths")
            if ev != marc: f.append(f"final: el marcador dice {marc} muertes tuyas y los eventos {ev}")
    return f


IMPERATIVOS = ("juega", "únete", "pelea", "pelees", "farmea", "tradea", "tradees", "roamea", "roamees", "evita", "busca", "cuida",
               "castiga", "empuja", "vuelve", "haz", "salgas", "escala", "quédate", "no tradear", "jugar seguro", "no pelear")  # Sombra: ningún imperativo


def repetir_momentos(fotos, g, aj=None):
    """[{t, meta, escena, notas, pelea}] por foto, con el reloj local = gameTime."""
    est, e, out = {"avisado": set()}, None, []
    for d in fotos:
        t = d["gameData"]["gameTime"]
        meta, avisos = companion.paso_vivo(d, est, aj or {})
        if meta: meta = {**meta, "avisos": [(c, getattr(x, "corto", x)) for c, x, _ in avisos]}
        e, esc, notas = momentos.paso(e, meta, g, t, aj)
        out.append({"t": t, "meta": meta, "escena": esc, "notas": notas, "pelea": bool(meta) and momentos.en_pelea(e, meta, t)})
    return out


def texto_momentos(r):
    x = r["escena"]
    if not x: return f"{reloj(r['t'])} | (sin franja)"
    mk = " ".join(f"{m.get('etq', m['min'])}{ {None: '·', True: '●', False: '○', 'sin': '-'}[m['estado']] }" for m in x["marcas"])
    return (f"{reloj(r['t'])} | {x['regla']['apagadas']}/{x['regla']['tope']} | {x['sombra']['num']} {x['sombra']['etq']} | {mk} | "
            f"{x.get('renglon') or ''}{' | panel: ' + ' / '.join(x['panel']) if x.get('panel') else ''}")


def validar_momentos(rs):
    """Fallos del contrato de atención y del texto de Sombra; vacía si todo cuadra."""
    f, n = [], 0
    for r in rs:
        t, x = reloj(r["t"]), r["escena"]
        for a in r["notas"]:
            if a["clase"] != "interrupcion" or not a["mostrado"]: continue
            n += 1
            if r["pelea"] and not (r["meta"] or {}).get("muerto"): f.append(f"{t}: interrupción en pelea «{a['dato']}»")
            if r["t"] >= momentos.TARDE_S: f.append(f"{t}: interrupción después del 25 «{a['dato']}»")
        if not x: continue
        if not (r["meta"] or {}).get("muerto") and (p := momentos.palabras_vivo(x)) > 9: f.append(f"{t}: {p} palabras con el campeón vivo (máx. 9)")
        if x.get("renglon") and len(x["renglon"]) > 34: f.append(f"{t}: renglón de {len(x['renglon'])} caracteres (máx. 34)")
        for txt in momentos.textos(x):
            if mal := [w for w in LISTA_NEGRA + IMPERATIVOS if re.search(r"" + re.escape(w) + r"", txt.lower())]: f.append(f"{t}: palabra prohibida {mal} en «{txt}»")
    if n > momentos.MAX_INTERRUPCIONES: f.append(f"{n} interrupciones en la partida (máx. {momentos.MAX_INTERRUPCIONES})")
    return f


def guion_de(fotos):
    """El guion con tus partidas (DATOS_DIR) para el campeón, rival y rol de la partida grabada; None si no se puede."""
    meta = next((m for d in fotos if (m := companion.meta_fase(d)) and m.get("modo") != "ARAM"), None)
    if not meta: return None
    try:
        import guion
        er = None
        try:  # tus errores vigilados (Fase 7), como en la app; sin partidas suficientes, solo el plan de rol
            import ciclo, score, vistas
            e = vistas.errores(score.partidas()[0]); er = {"ciclo": ciclo.errores(e), "tipos": e.get("tipos")}
        except Exception: pass
        return guion.armar(meta["campeon"], meta.get("rival"), meta.get("pos"), guardar=False, errores=er)
    except Exception: return None


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("archivo"); ap.add_argument("--validar", action="store_true"); ap.add_argument("--precios", action="store_true")
    ap.add_argument("--momentos", action="store_true")
    a = ap.parse_args(argv)
    if a.momentos:
        fotos = cargar(a.archivo)
        with contextlib.nullcontext() if a.precios else sin_precios(): rs = repetir_momentos(fotos, guion_de(fotos))
        for r in rs: print(texto_momentos(r))
        fallos = validar_momentos(rs) if a.validar else []
        for x in fallos: print("FALLO", x, file=sys.stderr)
        if a.validar: print(f"{len(fallos)} fallo(s)", file=sys.stderr)
        return 1 if fallos else 0
    with contextlib.nullcontext() if a.precios else sin_precios(): rs = repetir(cargar(a.archivo))
    for r in rs: print(texto(r))
    if a.validar:
        fallos = validar(rs)
        for x in fallos: print("FALLO", x, file=sys.stderr)
        print(f"{len(fallos)} fallo(s)", file=sys.stderr)
        return 1 if fallos else 0
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8"); sys.exit(main())
