"""El trabajador de fondo de Racha: sondea el cliente de LoL (solo lectura), baja partidas y arma el perfil.
Lo usa companion_web.py (la app); no se corre solo."""
import contextlib, importlib, io, json, os, pathlib, runpy, sys, threading, time, traceback
# PyInstaller solo empaqueta lo que ve importado: estos los usan los scripts que el .exe carga del disco
import argparse, base64, collections, datetime, math, random, sqlite3, ssl, statistics, subprocess, webbrowser  # noqa: F401
import urllib.error, urllib.parse, urllib.request  # noqa: F401
try: import winreg  # noqa: F401
except ImportError: winreg = None

if getattr(sys, "frozen", False):  # el .exe trae solo Python: carga los scripts del repo junto a él (se actualizan sin recompilar)
    _exe = pathlib.Path(sys.executable).resolve().parent  # instalado: scripts/ junto al exe; build en dist/HTC/: el repo dos arriba
    REPO = next((p for p in (_exe, *_exe.parents) if (p / "scripts").is_dir()), _exe)
    sys.path.insert(0, str(REPO / "scripts"))
else:
    REPO = pathlib.Path(__file__).resolve().parent.parent
for _s in ("stdout", "stderr"):  # el .exe no tiene consola: los scripts hacen sys.stdout.reconfigure
    if getattr(sys, _s) is None: setattr(sys, _s, io.TextIOWrapper(io.BytesIO(), encoding="utf-8"))

import companion  # noqa: E402

RAW = pathlib.Path(os.environ.get("DATOS_DIR") or REPO / "datos" / "raw")
BASE = RAW  # la carpeta del dueño de Racha en esta PC; otra cuenta del cliente usa datos/cuentas/<puuid>/raw


def dueno_de(raw):
    try: a = json.loads((raw / "perfil.json").read_text())["account"]; return f"{a['gameName']}#{a['tagLine']}"
    except (OSError, ValueError, KeyError, TypeError): return None


def carpeta_de(cuenta, puuid):
    """Dónde van las partidas de la cuenta con sesión en el cliente: la del dueño (o la base sin dueño todavía, como un
    amigo recién instalado) o una carpeta propia por puuid (estable ante cambios de nombre)."""
    import re
    d = dueno_de(BASE)
    if not cuenta or not d or d.casefold() == cuenta.casefold() or not re.fullmatch(r"[A-Za-z0-9_-]{20,100}", str(puuid or "")): return BASE
    return BASE.parent / "cuentas" / puuid / "raw"


def usar_cuenta(cuenta, puuid):
    """Cambia la carpeta de partidas a la de esa cuenta (multi-cuenta, 2026-11-12: el usuario probó con otra cuenta suya y
    Racha no mostraba nada). True si cambió."""
    global RAW
    if not puuid: return False  # sin puuid no se sabe de quién es: no se toca la carpeta (vigilar_cuenta siempre lo manda)
    nueva = carpeta_de(cuenta, puuid)
    if nueva == RAW: return False
    RAW = nueva; os.environ["DATOS_DIR"] = str(nueva)
    import builds; builds.RAW = nueva
    with DRAFT:
        for m in ("vistas", "draft", "revision"): sys.modules.pop(m, None)  # leen la carpeta al importarse
    return True


def es_base(): return RAW == BASE
FIN = ("PreEndOfGame", "EndOfGame")
FASES = {None: "Cliente cerrado", "None": "Sin actividad", "Lobby": "En lobby", "Matchmaking": "Buscando partida",
         "ReadyCheck": "Partida encontrada", "ChampSelect": "Champ select", "InProgress": "En partida",
         "PreEndOfGame": "Fin de partida", "EndOfGame": "Fin de partida"}


def script(nombre, *args):
    """Corre scripts/<nombre> en este proceso (el .exe no tiene python.exe para un subproceso): (código, salida)."""
    buf, argv = io.TextIOWrapper(io.BytesIO(), encoding="utf-8"), sys.argv
    sys.argv = [nombre, *args]
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            runpy.run_path(str(REPO / "scripts" / nombre), run_name="__main__"); code = 0
    except SystemExit as e: code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except Exception: code = 1; buf.write(traceback.format_exc())
    finally: sys.argv = argv
    buf.flush(); return code, buf.buffer.getvalue().decode("utf-8", "replace")


def descargar(n="todo", raw=None, riot_id=None, eco=None):
    """Corre descargar.py en este proceso para esa carpeta y esa cuenta, sin tocar sys.argv, stdout ni os.environ (con
    gui.script se mezclaba con revision.py corriendo a la vez). eco(línea) recibe el progreso. Devuelve (código, salida)."""
    lineas = []
    def e(l):
        lineas.append(l)
        if eco: eco(l)
    try:
        runpy.run_path(str(REPO / "scripts" / "descargar.py"), run_name="__main__",
                       init_globals=dict(ARGV=[str(n)], RAW_DIR=str(raw) if raw else None, RIOT_ID_G=riot_id, ECO=e)); code = 0
    except SystemExit as x:
        code = x.code if isinstance(x.code, int) else (0 if x.code is None else 1)
        if isinstance(x.code, str): lineas.append(x.code)
    except Exception as x: code = 1; lineas.append(f"falló: {x!r}")
    return code, "\n".join(lineas)


def parsear_revision(salida):
    """Primera fila de «Partida por partida» de revision.py: dict con las metas de la partida más reciente."""
    filas = [l for l in salida.split("## Partida por partida")[-1].splitlines() if l.startswith("| ") and not l.startswith("| Fecha")]
    if not filas: return None
    _, camp, vd, oro, cs, m14, m25, cw, *sc = [c.strip() for c in filas[0].strip().strip("|").split("|")]
    racha = salida.split("## Racha de oro bajo al 14")[1].split("## ")[0].strip().splitlines() if "## Racha de oro bajo al 14" in salida else []
    return dict(champ=camp.replace(" (fuera del pool)", ""), pool="fuera del pool" not in camp, win=vd == "V",
                oro=oro, cs=cs, m14=m14, m25=m25, cw=cw, score=sc[0] if sc else "-", racha=[l.removeprefix("- ") for l in racha if l.strip()])


def ultima_partida(archivo=None):
    """KDA, rival, duración y revisión (estela, momentos, muertes con su causa probable) de la partida más nueva en datos/raw
    (los id de partida crecen con el tiempo) o de `archivo` («LA1_123», la que elegiste en Partidas)."""
    try:
        puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
        import score
        f = RAW / f"{archivo}.json" if archivo else next((p for p in sorted(RAW.glob("*_*.json"), key=lambda p: int(p.stem.split("_")[1]), reverse=True)
                                                           if score.cargar_partida(p)), RAW / "-.json")  # la más nueva que se pueda leer
        info = (score.cargar_partida(f) or {})["info"]; ps = info["participants"]  # sin partida legible: KeyError → {}
        me = next(p for p in ps if p["puuid"] == puuid)
        opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
        out = dict(kda=f"{me['kills']}/{me['deaths']}/{me['assists']}", min=info["gameDuration"] // 60,
                   rival=opp["championName"] if opp else None)
    except (OSError, ValueError, KeyError, StopIteration): return {}
    try:  # revisión post-partida (postpartida.py): 3 momentos clave y muertes sin objetivo, si hay timeline
        import postpartida
        m, tl = score.cargar_partida(f), json.loads((RAW / "timeline" / f.name).read_text())
        libres = postpartida.muertes_sin_objetivo(m, tl, puuid)
        out.update(momentos=[x["texto"] for x in postpartida.momentos(m, tl, puuid)], estela=postpartida.estela(m, tl, puuid),
                   muertes=[x["texto"] for x in postpartida.muertes(m, tl, puuid)],
                   libres=[libres["n"], libres["total"]] if libres["total"] else None, por_tipo=libres.get("por_tipo"))
    except (OSError, ValueError): pass
    try:  # el feedback exacto (con CS y niveles del timeline), contra tus otras partidas del rol
        import sombra
        md = postpartida.medidas_partida(f, puuid)
        if md: out["feedback"] = postpartida.feedback(md, [s for s in sombra.series() if s["t"] != md["t"]], me.get("teamPosition"))
    except Exception: pass
    return out


AJUSTES_F = REPO / "datos" / "cache" / "ajustes.json"
AJUSTES_DEF = {"overlay": True, "aviso_nivel": True, "aviso_minions": True, "aviso_muertes": True, "aviso_regreso": True, "aviso_pico": True,  # Ajustes_Vino
               "metricas": False,  # métricas anónimas: solo si el amigo las prende
               "grupo": False,  # aparecer en la tabla del grupo (Riot ID y win rate a los demás): solo si lo prende
               "franja_linea": True, "franja_regla": True,  # piezas de la franja en partida
               "voz": False,
               "franja_plan": True,  # la franja muestra el match, tu regla y tu nota los primeros 90 s
               "franja_muerto": True,  # al morir la franja se expande con el marcador de objetivos y tu regla
               "franja_build": True,  # la franja muestra tu próximo ítem al morir o al comprar
               "franja_estilo": "sombra",  # Sombra (3 zonas: regla, sombra, marcas) o la pastilla clásica, una versión más
               "solo_marcas": False,  # Sombra sin interrupciones: solo las marcas y el panel al morir
               "momento_nivel": True, "momento_regreso": True, "momento_pico": True,  # Sombra: cada interrupción se apaga sola
               "sonido_sello": False,
               "sondeo_ahorro": False,  # Sombra en PCs modestas: la partida se lee cada 3 s en vez de cada 1 s  # Sombra: un «tic» de 120 ms al sellar una marca (apagado por defecto)
               "franja_poco": False,  # Sombra: 1 interrupción por partida (se prende sola tras dos «no» a «¿Te sirvieron?»)
               "franja_por_res": {},  # posición libre por resolución: {"1920x1080": [fx, fy]}
               "franja_tam": "grande",  # Sombra: tamaño de la franja (overlay.py: ×1, ×1.25, ×1.5)
               "franja_pos": "arriba", "franja_x": 0.22, "franja_y": 0.0}  # esquina de la franja: único ajuste que no es booleano
OPCIONES = {"franja_pos": ("arriba", "abajo", "libre"), "franja_estilo": ("sombra", "clasica"), "franja_tam": ("normal", "grande", "muy_grande")}  # lista blanca de los ajustes de texto
FRACCIONES = ("franja_x", "franja_y")  # posición libre de la franja: fracción del juego (0–1), la eligió el usuario arrastrándola


def valido(clave, v):
    if clave == "franja_por_res":
        import re
        frac = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and 0 <= x <= 1
        return isinstance(v, dict) and len(v) <= 8 and all(isinstance(k, str) and re.fullmatch(r"\d{3,5}x\d{3,5}", k) and isinstance(p, list) and len(p) == 2 and all(map(frac, p)) for k, p in v.items())
    if clave in FRACCIONES: return isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 1
    return v in OPCIONES[clave] if clave in OPCIONES else isinstance(v, bool)


SIRVIO_F = REPO / "datos" / "cache" / "sirvio.json"


def contar_sirvio(v):
    """Guarda la respuesta a «¿Te sirvieron?» y dice si Sombra debe hablar menos: True tras dos «no» seguidos, False con
    un «sí», None si no cambia (no los vi)."""
    try: ult = json.loads(SIRVIO_F.read_text(encoding="utf-8"))[-1:]
    except (OSError, ValueError, TypeError, KeyError): ult = []
    ult = [x for x in ult if x in ("si", "no", "no_vi")] + [v]
    try: SIRVIO_F.parent.mkdir(parents=True, exist_ok=True); SIRVIO_F.write_text(json.dumps(ult), encoding="utf-8")
    except OSError: pass
    return True if ult == ["no", "no"] else False if v == "si" else None


def ajustes():
    """Ajustes guardados (los que faltan, por defecto); un archivo roto no tumba nada."""
    try: d = json.loads(AJUSTES_F.read_text(encoding="utf-8"))
    except (OSError, ValueError): d = {}
    return {k: d[k] if k in d and valido(k, d[k]) else v for k, v in AJUSTES_DEF.items()}


def guardar_ajuste(clave, on):
    """Guarda un ajuste conocido; devuelve todos. Clave desconocida: ValueError (lista blanca)."""
    if clave not in AJUSTES_DEF or not valido(clave, on): raise ValueError(clave)
    a = {**ajustes(), clave: on}
    AJUSTES_F.parent.mkdir(parents=True, exist_ok=True); AJUSTES_F.write_text(json.dumps(a), encoding="utf-8")
    return a


def rescatar_anidadas():
    """Copia a su carpeta las partidas que quedaron anidadas en datos/cuentas/<a>/cuentas/<b>/raw (una actualización
    reabría Racha con la carpeta de otra cuenta como base). Solo copia lo que falta: nunca pisa ni borra. Cuántas copió."""
    import shutil
    raiz = BASE.parent / "cuentas"
    try: yo = json.loads((BASE / "perfil.json").read_text(encoding="utf-8"))["account"]["puuid"]
    except (OSError, ValueError, KeyError, TypeError): yo = None
    n = 0
    for raw in raiz.glob("*/cuentas/**/raw"):
        try: puuid = json.loads((raw / "perfil.json").read_text(encoding="utf-8"))["account"]["puuid"]
        except (OSError, ValueError, KeyError, TypeError): continue  # sin dueño claro no se mueve nada
        destino = BASE if puuid == yo else raiz / puuid / "raw"
        if destino.resolve() == raw.resolve(): continue
        for sub in ("", "timeline"):
            (destino / sub).mkdir(parents=True, exist_ok=True)
            for f in (raw / sub).glob("*_*.json"):
                if not (destino / sub / f.name).exists():
                    try: shutil.copy2(f, destino / sub / f.name); n += 1
                    except OSError: pass
    return n


NOMBRES = {}  # championId -> nombre del cliente (companion_web.vigilar_cuenta), para quien no tiene partidas descargadas
CUENTA = [None]  # «gameName#tag» con sesión en el cliente (la pone companion_web.vigilar_cuenta)


def dueno():
    """«gameName#tag» de la cuenta cuyas partidas están en disco (perfil.json), o None."""
    return dueno_de(RAW)


def ajeno(cuenta):
    """True si el cliente tiene otra cuenta que la de las partidas en disco: ese historial no es de quien juega."""
    d = dueno()
    return bool(cuenta and d and cuenta.casefold() != d.casefold())


def perfil(r=None, cuenta=None):
    """«gameName#tag · Master 15 LP · 120-100 (55%)». La cuenta con sesión en el cliente manda; el rango r (fresco del
    cliente) gana al de perfil.json, que solo se usa si es de esa misma cuenta."""
    tx = lambda x: " ".join(y for y in (x["tier"].title(), x["division"], f"{x['lp']} LP") if y) + (f" · {x['wins']}-{x['losses']} ({x['wr']}%)" if x["n"] else "")
    if cuenta and ajeno(cuenta): return f"{cuenta} · {tx(r)}" if r else cuenta
    try:
        d = json.loads((RAW / "perfil.json").read_text()); a = d["account"]
        solo = next((e for e in d["league"] if e["queueType"] == "RANKED_SOLO_5x5"), None)
        rango = f"{solo['tier'].title()} {solo.get('rank', '') if solo['tier'] not in ('MASTER', 'GRANDMASTER', 'CHALLENGER') else ''} {solo['leaguePoints']} LP".replace("  ", " ") if solo else "sin rango"
        return f"{a['gameName']}#{a['tagLine']} · {tx(r) if r else rango}"
    except (OSError, ValueError, KeyError, TypeError):
        if cuenta: return f"{cuenta} · {tx(r)}" if r else cuenta  # amigo sin partidas descargadas: su cuenta y rango, del cliente
        return tx(r) if r else "sin historial todavía"  # sin perfil.json ni cuenta todavía: al menos el rango del cliente


def puede_descargar():
    """Tu RIOT_KEY o tu código de acceso al backend de Racha: con cualquiera de los dos se bajan tus partidas."""
    return hay_key() or companion.acceso(REPO) is not None


RUTAS = {"na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas", "euw1": "europe", "eun1": "europe",
         "tr1": "europe", "ru": "europe", "me1": "europe", "kr": "asia", "jp1": "asia", "oc1": "sea", "sg2": "sea", "tw2": "sea", "vn2": "sea"}
CUENTA_F = REPO / "datos" / "cache" / "cuenta.json"  # tu Riot ID guardado: para bajar tus partidas con el cliente cerrado


def validar_cuenta(riot_id, region):
    """{riot_id, region} limpios, o ValueError si el formato no es «Nombre#TAG» o la región no existe. No guarda nada."""
    import re
    riot_id, region = str(riot_id or "").strip(), str(region or "").strip().lower()
    if not re.fullmatch(r"[^#]{3,16}#[^#\s]{2,5}", riot_id) or region not in RUTAS: raise ValueError("Riot ID o región inválidos")
    return {"riot_id": riot_id, "region": region}


def guardar_cuenta(riot_id, region):
    """Guarda «Nombre#TAG» y la región (la1, euw1…) para usar Racha sin el cliente abierto. ValueError si no es válido."""
    c = validar_cuenta(riot_id, region); riot_id, region = c["riot_id"], c["region"]
    CUENTA_F.parent.mkdir(parents=True, exist_ok=True)
    CUENTA_F.write_text(json.dumps({"riot_id": riot_id, "region": region}, ensure_ascii=False), encoding="utf-8")
    return {"riot_id": riot_id, "region": region}


def cuenta_guardada():
    """{riot_id, region} guardados en Ajustes, o None."""
    try: d = json.loads(CUENTA_F.read_text(encoding="utf-8"))
    except (OSError, ValueError): return None
    return d if isinstance(d, dict) and d.get("riot_id") and d.get("region") in RUTAS else None


COACH_F = REPO / "datos" / "cache" / "coach.json"  # F12: la regla que te puso tu coach (prototipo, todo local)
COACH_PREFIJO, COACH_MAX = "RACHA1.", 600  # 80 caracteres de texto con emojis caben (~475)


def codigo_coach(texto, tope):
    """El código que el coach le pasa a su alumno: «≤ tope muertes del 14 al 25» con su texto. ValueError si no es válido."""
    import base64
    texto = " ".join(str(texto or "").split())
    if not 3 <= len(texto) <= 80 or type(tope) is not int or not 0 <= tope <= 5: raise ValueError("regla inválida")  # bool no vale
    crudo = json.dumps({"t": texto, "m": "muertes", "tope": tope}, ensure_ascii=False, separators=(",", ":")).encode()
    codigo = COACH_PREFIJO + base64.urlsafe_b64encode(crudo).decode().rstrip("=")
    if len(codigo) > COACH_MAX: raise ValueError("regla demasiado larga")  # mismo tope al crear que al leer (texto con emojis)
    return codigo


def leer_codigo_coach(codigo):
    """{texto, metrica, tope} de un código de coach; ValueError si está mal o trae otra cosa."""
    import base64, binascii
    c = str(codigo or "").strip()
    if not c.startswith(COACH_PREFIJO) or len(c) > COACH_MAX: raise ValueError("código de coach inválido")
    b = c[len(COACH_PREFIJO):]
    try: d = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
    except (binascii.Error, ValueError, UnicodeDecodeError): raise ValueError("código de coach inválido")
    if not isinstance(d, dict) or d.get("m") != "muertes": raise ValueError("código de coach inválido")
    codigo_coach(d.get("t"), d.get("tope"))  # mismas reglas que al crearlo
    return {"texto": " ".join(str(d["t"]).split()), "metrica": "muertes", "tope": d["tope"]}


def guardar_coach(codigo):
    r = leer_codigo_coach(codigo)
    COACH_F.parent.mkdir(parents=True, exist_ok=True); COACH_F.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
    return r


def coach():
    """La regla de tu coach guardada, o None."""
    try: return leer_codigo_coach(codigo_coach((d := json.loads(COACH_F.read_text(encoding="utf-8")))["texto"], d["tope"]))
    except (OSError, ValueError, KeyError, TypeError): return None


def guardar_acceso(token):
    """Guarda tu código de acceso (lo da quien administra el backend). Solo letras, números y guiones: ValueError si no."""
    import re
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9-]{6,64}", token): raise ValueError("código inválido")
    f = REPO / "datos" / "cache" / "acceso.json"
    try: d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError): d = {}
    f.parent.mkdir(parents=True, exist_ok=True); f.write_text(json.dumps({**d, "token": token}), encoding="utf-8")


def hay_key():
    if os.environ.get("RIOT_KEY"): return True
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k: return bool(winreg.QueryValueEx(k, "RIOT_KEY")[0])
    except (AttributeError, OSError): return False


def rivales_linea(pos, nombres, umbral=0.25):
    """En ranked Riot oculta el rol de los enemigos: de los ya elegidos, el que más juega tu posición según las builds
    Master+ (datos/meta/builds.json, cuota de partidas en ese rol ≥ 25 %, elegido con herramientas/dev_umbral.py); empate, tu historial. [] si ninguno la juega:
    tu rival aún no elige. Sin ese archivo, como antes: el que más fue tu rival en tus partidas, o todos."""
    nombres = [n for n in nombres if n]
    try: import draft; hist = collections.Counter(g["opp"] for g in draft.games if g.get("pos") == pos)
    except Exception: hist = collections.Counter()
    try:
        import builds; d = json.loads((builds.META / "builds.json").read_text(encoding="utf-8"))
        tot, mio = collections.Counter(), collections.Counter()
        for k, v in d.items():
            if k.count("|") == 1 and isinstance(v, dict) and v.get("n"):
                c, p = k.split("|"); tot[builds.norm(c)] += v["n"]; mio[builds.norm(c)] += v["n"] if p == pos else 0
    except (OSError, ValueError, AttributeError):  # sin builds.json (instalación nueva) o cortado
        mejor = max(nombres, key=hist.__getitem__, default=None)
        return nombres if len(nombres) < 2 or not hist[mejor] else [mejor]
    cuota = lambda n: mio[builds.norm(n)] / tot[builds.norm(n)] if tot[builds.norm(n)] else None
    if cand := [n for n in nombres if (cuota(n) or 0) >= umbral]: return [max(cand, key=lambda n: (cuota(n), hist[n]))]
    sin = [n for n in nombres if cuota(n) is None and hist[n]]  # campeón sin builds del ladder: tu historial decide
    return [max(sin, key=hist.__getitem__)] if sin else []


def recomendaciones(pos, rivales):
    """[(rival, datos_draft | None)] usando draft.py (lo recarga si hay partidas nuevas)."""
    if ajeno(CUENTA[0]): return [(r, None) for r in rivales]  # tus partidas en disco son de otra cuenta: no recomendar con ellas
    try: import draft
    except (AssertionError, OSError, ValueError, KeyError): return [(r, None) for r in rivales]  # sin partidas ni perfil.json (beta sin key): rival «sin datos», no un error
    with DRAFT: return [(r, dict(draft.datos_draft(r, pos), ficha=draft.ficha(r, pos)) if r else None) for r in rivales]


def comentario(tab, pos, rival=None):
    """draft.comentario con los mismos guardas que recomendaciones(): cuenta ajena o sin partidas, nada."""
    if ajeno(CUENTA[0]): return []
    try: import draft
    except (AssertionError, OSError, ValueError, KeyError): return []
    with DRAFT: return draft.comentario(tab, pos, rival)


def registrar_franja(txt):
    """Un error de la franja queda en datos/salud/franja.log en vez de tragarse en silencio."""
    try:
        f = REPO / "datos" / "salud" / "franja.log"; f.parent.mkdir(parents=True, exist_ok=True)
        with f.open("a", encoding="utf-8") as h: h.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {txt}" + chr(10))
    except OSError: pass


def calentar_sombra():
    try: import sombra; sombra.series()
    except Exception: pass  # sin partidas o sin disco: el guion saldrá «Sin sombra aún»


def plan_partida(campeon, rival, pos):
    """Lo de la franja al empezar, una vez por partida y con tu historial: tu récord y WR contra
    ese rival con ese campeón, tu regla con su meta y tu dato, y tu nota del matchup. None si no hay datos o cuenta ajena."""
    if ajeno(CUENTA[0]) or not campeon or not rival: return None
    try: import draft
    except (AssertionError, OSError, ValueError, KeyError): return None
    try:
        with DRAFT: f = draft.ficha(rival, pos or "MIDDLE", champ=campeon)
        if not f or draft.key(f["champ"]) != draft.key(campeon):  # tu campeón no está en tu pool del rol: solo lo de muchas partidas
            import matchups; mu = matchups.para_ficha(campeon, pos or "MIDDLE", rival)
            return {"rival": rival, "v": 0, "n": 0, "wr": None, "n_rol": 0, "regla": None, "tu": None, "nota": None, "m6": None, "m6_ref": None,
                    "m6_pocas": True, "dato": (mu.get("frases") or [None])[0]} if mu and mu.get("frases") else None
        pq, c = f["por_que"], f["cuidado"]
        r0 = next((r for r in f["reglas"] if r.get("meta")), None)
        return {"rival": f["rival"], "v": pq["v"], "n": pq["n"], "wr": pq["wr_rol"], "n_rol": pq["n_rol"],
                "regla": r0["meta"] if r0 else None, "tu": (r0 or {}).get("tu"), "nota": (c.get("notas") or [None])[0],
                "m6": c.get("muertes6"), "m6_ref": (c.get("ref") or {}).get("muertes6"), "m6_pocas": c.get("pocas"),
                "dato": ((f.get("matchup") or {}).get("frases") or [None])[0]}  # la frase top del matchup (muchas partidas)
    except Exception: return None


DRAFT = threading.Lock()  # el reload de draft (hilo post-partida) no debe pisar un datos_draft a medias
POST = []  # el hilo post-partida vivo, si hay


SONDEO_VIVO = 10  # s entre fotos en vivo con la franja clásica: < 1 ms de cálculo por foto (medido)
SONDEO_SOMBRA = 1  # con Sombra: una muerte o una compra en pantalla en ≤ 1,5 s, y la vida propia para no hablar en una pelea
SONDEO_AHORRO = 3  # Sombra con «Ahorro»: menos peticiones al juego; la pelea se detecta sobre todo por las kills (la vida se ve menos)


FRANJA_CAIDA = [False]  # el proceso de la franja cayó dos veces: sin franja, sin prisa


def sondeo(aj):
    if aj.get("overlay", True) is False or aj.get("franja_estilo") != "sombra" or FRANJA_CAIDA[0]: return SONDEO_VIVO
    return SONDEO_AHORRO if aj.get("sondeo_ahorro") else SONDEO_SOMBRA


def aviso(texto, tipo="error", minuto=None):
    """Evento de aviso para la cola: {texto, tipo: consejo (en partida) | error, minuto de juego o None}."""
    return ("aviso", {"texto": str(texto), "tipo": tipo, "minuto": minuto, "corto": getattr(texto, "corto", None)})  # corto: para la franja (F1)


def post_partida(q):
    """Lanza la descarga y revisión en otro hilo: tarda hasta ~7 min y el sondeo debe ver el próximo champ select."""
    if POST and POST[0].is_alive(): return
    POST[:] = [threading.Thread(target=_post_partida, args=(q,), daemon=True)]; POST[0].start()


CLIENTE_ESPERA, CLIENTE_INTENTOS = 20, 15  # s entre intentos y cuántos (5 min): el cliente publica la partida al rato de terminar


def id_partida():
    """El gameId de la partida que acaba de terminar (gameflow sigue en EndOfGame), o None si el cliente no responde."""
    try: s = companion.lcu("/lol-gameflow/v1/session")
    except Exception: return None
    return ((s.get("gameData") or {}).get("gameId") if isinstance(s, dict) else None) or None


def guardar_del_cliente(q, gid=None, espera=None, intentos=None, dormir=None):
    """Guarda la partida recién jugada desde tu propio cliente (sin key): cliente_v5 la baja a la carpeta de la cuenta
    activa con su timeline. True si ya está en disco la partida gid (sin gid: si entró alguna nueva). El cliente publica
    tarde y fuera de orden: otra partida vieja no cuenta, o la revisión saldría de esa."""
    import cliente_v5
    q.put(("post_espera", "Guardando tu partida desde el cliente…"))
    for _ in range(CLIENTE_INTENTOS if intentos is None else intentos):
        (dormir or time.sleep)(CLIENTE_ESPERA if espera is None else espera)  # time.sleep al llamar: las pruebas lo cambian
        try: nuevas, _ = cliente_v5.descargar(gid=gid)
        except Exception: nuevas = 0  # cliente cerrándose o a medias: se reintenta
        if any(RAW.glob(f"*_{gid}.json")) if gid else nuevas: return True
    q.put(("post_espera", "El cliente aún no publica la partida: lo de arriba es lo que vio Racha; la revisión de Riot sale cuando se guarde."))
    return False


def _post_partida(q):
    # la partida recién jugada llega primero desde tu cliente (al instante y sin gastar la key, aunque la cola esté
    # bajando tu historial); si el cliente no la da, la cola de descargas la pide a Riot con prioridad.
    if not guardar_del_cliente(q, id_partida()):
        if puede_descargar(): q.put(("bajar", 5))
        return
    if "draft" in sys.modules:
        with DRAFT: importlib.reload(sys.modules["draft"])  # partidas nuevas para el próximo champ select
    code, out = script("revision.py", "1")
    rev = parsear_revision(out)
    q.put(("revision", {**rev, **ultima_partida()}) if rev else aviso("revision.py no devolvió la partida."))


def texto_meta(mf):
    """«Min 7 · Nv 6 contra 7 (Zed) · CS 52 (meta 69 al 10)» desde companion.meta_fase(); en ARAM, kills y la amenaza."""
    if mf.get("modo") == "ARAM":
        a = (mf.get("amenazas") or [{}])[0]
        return " · ".join([f"Min {mf['minuto']}", f"Kills {mf['kills'][0]}–{mf['kills'][1]}", f"Tu KDA {mf['kda']}"]
                          + ([f"Cuidado con {a['campeon']} {a['kda']}"] if a.get("campeon") else []))
    t = [f"Min {mf['minuto']}", f"Nv {mf['nivel'] or '?'}"]
    if mf["rival"]: t[-1] += f" contra {mf['nivel_rival'] or '?'} ({mf['rival']})"
    t.append(f"CS {mf['cs'] if mf['cs'] is not None else '?'}" + (f" (meta {mf['cs_meta']} al 10)" if mf["cs_meta"] and mf["minuto"] < 11 else ""))
    if mf.get("muertes14") is not None and mf["minuto"] < 25: t.append(f"Muertes desde el 14: {mf['muertes14']} (meta ≤ 2)")
    return " · ".join(t)


def _dif(m, ref, k, nombre, fmt):
    """«CS al 14 −17 (tu media −3)» o None si no hay medida."""
    def f(v):
        s = format(v, fmt)
        return format(0.0, fmt) if float(s) == 0 else s  # sin «−0»
    if m.get(k) is None: return None
    r = f" (tu media {f(ref[k])})" if ref.get(k) is not None else ""
    return f"{nombre} {f(m[k])}{r}".replace("-", "−")


def lineas_ficha(fi):
    """(cuidado, counters): renglones de texto de draft.ficha() para la ventana.
    Solo lo medido; [] si no hay nada que decir."""
    if not fi: return [], []
    c, ref = fi["cuidado"], fi["cuidado"]["ref"]
    cuidado = []
    if c["n"]:
        ant = c.get("anticipa") or ()  # las que anticipan la próxima partida (anticipa.py) van solas; el resto, juntas y marcadas
        difs = [(k in ant, _dif(c, ref, k, n, f)) for k, n, f in [("muertes6", "Muertes antes del 6", ".1f"), ("oro14", "Oro al 14", "+.0f"),
                                                                ("cs14", "CS al 14", "+.0f"), ("nivel6", "Nivel al 6", "+.1f")]]
        resto = " · ".join(d for a, d in difs if d and not a)
        cuidado = ([f"Tú contra {c['rival']} (cualquier campeón): {c['v']}-{c['n'] - c['v']} (Wilson {c['ic'][0]:.0%}–{c['ic'][1]:.0%})"
                    + ("; pocas partidas, pista" if c["pocas"] else "")] + [f"{d}; esta sí tiende a repetirse contra él" for a, d in difs if d and a]
                   + ([f"{resto}; no se repite de una partida a la siguiente"] if resto else []))
    cuidado += [f"Tu nota: {n}" for n in c["notas"]]
    ref = fi["counters"]["ref"]
    counters = [f"{x['rival']} {x['v']}-{x['n'] - x['v']} (Wilson {x['ic'][0]:.0%}–{x['ic'][1]:.0%})"
                + "".join(f" · {d}" for d in [_dif(x, ref, "cs14", "CS al 14", "+.0f"), _dif(x, ref, "oro14", "oro", "+.0f")] if d)
                + ("; pista" if x["pocas"] else "") for x in fi["counters"]["lista"]]
    return cuidado, counters


def trabajador(q):
    """El mismo bucle que companion.main, pero manda eventos a la ventana en vez de imprimir."""
    m, visto, fase_ant, real, archivo, ult, estado, fallos = None, None, "inicio", None, None, 0, {"avisado": set()}, 0
    ult_disco = 0  # la foto se lee cada SONDEO_VIVO s (F4: ver la muerte a tiempo) pero al disco va cada 30 s
    error = foto = nl = tab_ant = None  # nl: championId -> alias del cliente, para el tablero de Draft
    while True:
        fase, jugando = None, False  # si lcu() lanza, cuenta como cliente caído
        try:
            fase = companion.lcu("/lol-gameflow/v1/gameflow-phase")
            if fase != fase_ant and fase == "ChampSelect":  # metas de CS (F9): ~4 s la primera vez; en selección no frena la partida
                threading.Thread(target=companion.metas_auto, daemon=True).start()
                threading.Thread(target=calentar_sombra, daemon=True).start()  # las series de Sombra al índice: el guion sale en ~50 ms
            if fase != fase_ant and fase == "ChampSelect":  # LP fresco del cliente (sin key); ya asentado tras la partida anterior
                q.put(("rango", companion.rango(companion.lcu("/lol-ranked/v1/current-ranked-stats"))))
            if fase != fase_ant: q.put(("fase", fase))
            jugando = (fase or real) == "InProgress"  # cliente reiniciándose a media partida: la partida sigue
            if fase == "ChampSelect" and (s := companion.lcu("/lol-champ-select/v1/session")):
                pos, ids = companion.rivales(s)
                tm = s.get("timer") or {}  # cronómetro de la fase (solo lectura), para el reloj de Draft_Vino
                if isinstance(tm.get("adjustedTimeLeftInPhase"), (int, float)):
                    q.put(("crono", {"fase": tm.get("phase"), "ms": tm["adjustedTimeLeftInPhase"], "t": time.time()}))
                tab = companion.tablero(s, nl := nl or companion.nombres_lcu() or companion.nombres() or dict(NOMBRES))
                ocultos = not any(p.get("assignedPosition") for p in s.get("theirTeam") or [])  # ranked: ids son todos sus picks
                if tab != tab_ant:
                    q.put(("tablero", tab)); tab_ant = tab
                    rv = [nl.get(i) for i in ids]  # tu rival de línea: el único de tu rol, o el más probable por rol
                    if ocultos: rv = rivales_linea(pos, rv)
                    q.put(("comentario", comentario(tab, pos, rv[0] if len(rv) == 1 else None)))
                if ids and (pos, ids) != visto:
                    m = m or companion.nombres() or dict(NOMBRES); visto = (pos, ids)
                    nombres = [m.get(i) for i in ids]
                    if ocultos: nombres = rivales_linea(pos, nombres)
                    q.put(("draft", pos, recomendaciones(pos, nombres), ocultos) if nombres else ("pos", pos))  # [] : su jungla o support, no tu rival
                elif not ids and pos and visto != pos: q.put(("pos", pos)); visto = pos  # bans y picks antes del rival
            elif fase != "ChampSelect": visto = tab_ant = None
            if jugando and time.time() - ult >= sondeo(aj := ajustes()) - 0.05:
                d = companion.unir_eventos(companion.vivo(), foto if archivo else None); ult = time.time(); foto = d or foto  # Reconnect reinicia los eventos; sin archivo es otra partida (revisión del asistente, 12)
                if ult - ult_disco >= 30: archivo, ult_disco = companion.capturar(archivo, d), ult
                mf, avs = companion.paso_vivo(d, estado, ajustes())  # Ajustes_Vino: cada aviso se puede apagar
                if mf and mf.get("modo") != "ARAM" and ajustes().get("franja_build", True) is not False:  # tu próximo ítem en la franja
                    if estado.get("build") is None and time.time() - estado.get("build_t", 0) > 30:  # falló: se reintenta cada 30 s (False = no hay)
                        estado["build"], estado["build_t"] = companion.build_partida(mf.get("campeon"), mf.get("pos")), time.time()
                    try: import builds; mf["proximo"] = companion.proximo(estado["build"], mf.get("items"), mf.get("oro_actual"), builds.ddragon()[0])
                    except Exception as e: mf["proximo"] = None; registrar_franja(f"próximo ítem: {e!r}")
                if mf and mf.get("modo") != "ARAM" and ajustes().get("franja_plan", True) is not False:  # MATCH, PLAN, CUIDADO (90 s) y el dato del matchup
                    if not estado.get("plan") and time.time() - estado.get("plan_t", 0) > 30 and ((mf.get("t") or 0) < 120 or "plan" not in estado):
                        estado["plan"], estado["plan_t"] = plan_partida(mf.get("campeon"), mf.get("rival"), mf.get("pos")), time.time()
                    if (mf.get("t") or 0) < 120: mf["plan"] = estado["plan"]
                    mf["dato"] = (estado.get("plan") or {}).get("dato")  # la frase top del matchup, para la expandida al morir
                if mf: mf["avisos"] = [(c, getattr(x, "corto", x)) for c, x, _ in avs]; q.put(("meta", mf))  # Sombra los vuelve datos (momentos.py)
                if mf: import postpartida; postpartida.anotar_niveles(estado.setdefault("niveles", {}), mf)  # para el feedback al terminar
                for _, txt, minuto in avs: q.put(aviso(txt, "consejo", minuto))
            elif not jugando and fase != "Reconnect": archivo = None; estado["avisado"] = set(); [estado.pop(k, None) for k in ("build", "build_t", "plan", "plan_t")]  # al reconectar es la misma partida
            if fase in FIN and real not in FIN:
                if r := companion.resumen_fin(foto):  # sin key, esto es lo que hay al terminar
                    try: import postpartida; r = {**r, "momentos": [m["texto"] for m in postpartida.momentos_vivo(foto)], "estela": postpartida.estela_vivo(foto),
                                                  "medidas": postpartida.medidas_vivo(foto, estado.pop("niveles", None))}  # F11: al instante; medidas: el feedback
                    except Exception: pass
                    q.put(("fin", r))
                foto = None; post_partida(q); m = None
            error = None
        except Exception:
            txt = "Error: " + traceback.format_exc(limit=1).strip().splitlines()[-1]
            if txt != error: q.put(aviso(txt)); error = txt  # el mismo error cada 3 s no inunda la ventana
        # fuera del try (como companion.main): una excepción no deja la fase vieja ni repite el evento de fase cada 3 s
        fase_ant, real, fallos = fase, fase or real, 0 if fase else fallos + 1
        time.sleep(1 if fase == "ChampSelect" or (jugando and sondeo(ajustes()) < SONDEO_VIVO) else companion.espera(fallos))  # en selección, el tablero sigue los hovers al segundo
