"""Lo que ves al terminar una partida grabada (datos/vivo/*.jsonl), sin LoL ni la revisión de Riot: la línea final, la carta
de Sombra, los 3 momentos, «Lo que viste en partida» y el feedback. Para revisar el texto con partidas reales.
Uso: DATOS_DIR=…/datos/raw python herramientas/dev_feedback.py <archivo.jsonl> [más archivos]"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bitacora, companion, momentos, postpartida, replay


def cerrar(ruta):
    """(fotos, guion, bitácora de Sombra {notas, marcas}) de una grabación, como al terminar en la app."""
    fotos = replay.cargar(ruta); g = replay.guion_de(fotos)
    est, e, notas, nv = {"avisado": set()}, None, [], {}
    with replay.sin_precios():
        for d in fotos:
            t = d["gameData"]["gameTime"]; meta, av = companion.paso_vivo(d, est, {})
            if meta: meta = {**meta, "avisos": [(c, getattr(x, "corto", x)) for c, x, _ in av]}; postpartida.anotar_niveles(nv, meta)
            e, _, n = momentos.paso(e, meta, g, t, {}); notas += n
    return fotos, g, {"notas": notas, "marcas": (e or {}).get("marcas", {})}, nv


def riot(mid):
    """El feedback «con los datos de Riot» de una partida de DATOS_DIR («LA1_123»), como lo arma ultima_partida."""
    import companion_gui as gui, json
    puuid = json.loads((gui.RAW / "perfil.json").read_text())["account"]["puuid"]
    fb = gui.ultima_partida(mid).get("feedback") or {}
    print(f"== {mid} (Riot)"); [print(f"{k}:", fb.get(k)) for k in ("bien", "mal", "foco", "nota")]; print()


def main(rutas):
    for ruta in rutas:
        if not ruta.endswith(".jsonl"): riot(ruta); continue
        fotos, g, sb, nv = cerrar(ruta)
        r = companion.resumen_fin(fotos[-1])
        if not r: print(f"== {pathlib.Path(ruta).name}: sin foto final de la Grieta"); continue
        rg = (g or {}).get("regla") or {}
        cumplida = r["muertes14_25"] <= rg.get("tope", 2) if rg.get("metrica") in ("muertes", None) and r.get("muertes14_25") is not None else None
        print(f"== {pathlib.Path(ruta).name} · {(g or {}).get('campeon')} vs {(g or {}).get('rival')} · {(g or {}).get('pos')}")
        print("Línea:", companion.linea_fin(r))
        print("Carta:", " · ".join(momentos.carta_fin(sb, cumplida)))
        print("3 momentos:"); [print("  -", m["texto"]) for m in postpartida.momentos_vivo(fotos[-1])]
        print("Lo que viste en partida:")
        for x in bitacora.para_revision({"notas": sb["notas"]}): print(f"  {x['min']} {x['texto']}" + ("" if x["mostrado"] else f" (no se mostró: {x['motivo']})"))
        import sombra
        ss = sombra.series()  # incluye esta partida si ya está en raw: para revisar textos da igual
        md = postpartida.medidas_vivo(fotos[-1], nv)
        fb = postpartida.feedback(md, ss, r.get("pos"))
        print("Medidas:", md)
        for k in ("bien", "mal"): print(f"{k.capitalize()}:"); [print("  -", x) for x in fb[k]]
        print("Foco:", fb["foco"] or fb["nota"])
        print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8"); main(sys.argv[1:])
