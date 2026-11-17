"""La bitácora de cada partida (plan Sombra): cada marca, cada compra y cada interrupción de la franja, mostrada o no y por
qué («en pelea», «sin presupuesto»). Un archivo por partida en datos/bitacora/; la revisión la muestra como
«Lo que viste en partida»."""
import json, os, pathlib, time

DIR = pathlib.Path(os.environ.get("RACHA_BITACORA") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "bitacora")
GUARDAR = 200  # las más recientes; las viejas se borran (cada una pesa ~2 KB)


def guardar(guion, estado, notas, cumplida=None, ahora=None):
    """Escribe la bitácora de la partida que acaba de terminar; devuelve el archivo o None (sin notas o sin disco)."""
    if not notas and not (estado or {}).get("marcas"): return None
    g = guion or {}
    d = dict(t=int(ahora or time.time()), campeon=g.get("campeon"), rival=g.get("rival"), pos=g.get("pos"),
             marcas=(estado or {}).get("marcas") or {}, regla=(g.get("regla") or {}).get("corta"), cumplida=cumplida, notas=notas)
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        f = DIR / f"{time.strftime('%Y%m%d-%H%M%S', time.localtime(d['t']))}.json"
        f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        for viejo in sorted(DIR.glob("*.json"))[:-GUARDAR]: viejo.unlink(missing_ok=True)
        return f
    except OSError: return None


def ultima(desde=None):
    """La bitácora más reciente (dict), o None. desde = epoch: solo si es de esa partida o posterior."""
    try: fs = sorted(DIR.glob("*.json"))
    except OSError: return None
    for f in reversed(fs):
        try: d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError): continue
        return d if desde is None or d.get("t", 0) >= desde else None
    return None


def para_revision(b):
    """La fila «Lo que viste en partida»: [{min, texto, mostrado, motivo}] en orden, sin las compras."""
    if not b: return []
    return [dict(min=f"{n['t'] // 60}:{n['t'] % 60:02d}", texto=n.get("dato") or n["id"], mostrado=bool(n.get("mostrado")), motivo=n.get("motivo"))
            for n in b.get("notas") or [] if n.get("clase") != "compra"]
