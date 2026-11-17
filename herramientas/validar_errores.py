"""Solo desarrollo: ¿la detección de errores en vivo (errores.de_vivo) coincide con la del timeline (errores.de_timeline)?
Empareja cada partida grabada (datos/vivo/*.jsonl) con su partida descargada (datos/raw o datos/cuentas/*/raw) por hora y
campeón, corre el mismo detector con las dos fuentes y compara cuántas veces cae cada error. Meta del plan: 90 % o más.
  python herramientas/validar_errores.py [carpeta_datos]   (por defecto, la de DATOS_DIR/..)"""
import datetime, json, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import companion, errores

META = 0.9


def partidas(datos):
    """[(inicio_ms, fin_ms, archivo, puuid)] de todas las carpetas raw con timeline."""
    out = []
    for raw in [datos / "raw", *(datos / "cuentas").glob("*/raw")]:
        try: yo = json.loads((raw / "perfil.json").read_text(encoding="utf-8"))["account"]["puuid"]
        except (OSError, ValueError, KeyError): yo = None
        for f in raw.glob("*_*.json"):
            if not (raw / "timeline" / f.name).exists(): continue
            try: info = json.loads(f.read_text(encoding="utf-8"))["info"]
            except (OSError, ValueError, KeyError): continue
            ini = info.get("gameStartTimestamp") or info.get("gameCreation")
            out.append((ini, info.get("gameEndTimestamp") or ini + (info.get("gameDuration") or 0) * 1000, f, yo))
    return out


def emparejar(grab, todas):
    """La partida descargada de una grabación: empezó como mucho 10 min antes del primer archivo y terminó después, con tu campeón."""
    fotos = [json.loads(l) for l in grab.read_text(encoding="utf-8").splitlines() if l.strip()]
    me = companion.yo_rival(fotos[-1])[0]
    if not me: return None, fotos
    t = datetime.datetime.strptime(grab.stem, "%Y%m%d-%H%M%S").timestamp() * 1000
    for ini, fin, f, yo in todas:
        if ini - 60_000 <= t <= fin and ini >= t - 600_000 - (fotos[0].get("gameData") or {}).get("gameTime", 0) * 1000:
            info = json.loads(f.read_text(encoding="utf-8"))["info"]
            p = next((p for p in info["participants"] if p.get("championName") == me.get("championName") and (yo is None or p.get("puuid") == yo)), None)
            if p: return (f, info, p), fotos
    return None, fotos


def nivel6_vivo(fotos):
    """(tú, rival) en la foto más cercana al minuto 6 (±40 s); None si no hay."""
    d = min(fotos, key=lambda d: abs(((d.get("gameData") or {}).get("gameTime") or 0) - 360))
    if abs(((d.get("gameData") or {}).get("gameTime") or 0) - 360) > 40: return None
    me, riv = companion.yo_rival(d)
    return (me.get("level"), riv.get("level")) if me and riv else None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    datos = pathlib.Path(argv[0]) if argv else pathlib.Path(os.environ.get("DATOS_DIR") or "datos/raw").parent
    todas, filas = partidas(datos), []
    for grab in sorted((datos / "vivo").glob("*.jsonl")):
        par, fotos = emparejar(grab, todas)
        if not par: print(f"{grab.name}: sin partida descargada"); continue
        f, info, p = par
        fr = json.loads((f.parent / "timeline" / f.name).read_text(encoding="utf-8"))["info"]["frames"]
        equipo = {x["participantId"]: x["teamId"] for x in info["participants"]}
        opp = next((x for x in info["participants"] if x["teamPosition"] == p["teamPosition"] and x["teamId"] != p["teamId"] and p["teamPosition"]), None)
        pf = (fr[6].get("participantFrames") or {}) if len(fr) > 6 else {}
        n6 = ((pf.get(str(p["participantId"])) or {}).get("level"), (pf.get(str(opp["participantId"])) or {}).get("level")) if opp and pf else None
        tl = errores.detectar(errores.de_timeline(fr, p["participantId"], equipo), n6)
        vv = errores.detectar(errores.de_vivo(fotos[-1]), nivel6_vivo(fotos))
        fila = {k: (len(tl[k]), len(vv[k])) for k in errores.ERRORES}
        filas.append(fila)
        print(f"{grab.name} {p['championName']:>12} → {f.stem}: " + "  ".join(f"{k} {a}/{b}{'' if a == b else ' ✗'}" for k, (a, b) in fila.items()))
    if not filas: print("sin partidas emparejadas"); return 1
    print()
    total = 0
    for k in errores.ERRORES:
        ok = sum(f[k][0] == f[k][1] for f in filas); total += ok
        print(f"{k:>13}: coincide en {ok}/{len(filas)} partidas ({ok / len(filas):.0%})")
    r = total / (len(filas) * len(errores.ERRORES))
    print(f"{'total':>13}: {r:.1%} (meta {META:.0%}) · {len(filas)} partidas emparejadas")
    return 0 if r >= META else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8"); sys.exit(main())
