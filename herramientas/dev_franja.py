"""Solo desarrollo (no va en el .exe): dibuja la franja real con una partida grabada, para verla encima del juego o el escritorio.
  python herramientas/dev_franja.py datos/vivo/20261109-175517.jsonl                 recorre la partida (cada foto, 1 s)
  python herramientas/dev_franja.py <archivo> --minuto 18:58 [--aviso "texto"]       se queda en ese minuto (peor ancho)
  python herramientas/dev_franja.py <archivo> --segundos 30                          cuánto dura abierta (por defecto, toda la partida)
  python herramientas/dev_franja.py <archivo> --sombra [--minuto 18:23]               la franja Sombra (guion con tus partidas de DATOS_DIR)
  python herramientas/dev_franja.py <archivo> --momento marca10                      Sombra desde una foto antes de ese momento (marca6…25,
                                                                                     nivel, regreso, regreso1, compra, pico, muerto)"""
import argparse, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import overlay, replay


def cuadro(rs, minuto):
    """La foto más cercana al minuto «MM:SS»."""
    m, s = (int(x) for x in minuto.split(":"))
    return min(rs, key=lambda r: abs(r["t"] - (m * 60 + s)))


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("archivo"); a.add_argument("--minuto"); a.add_argument("--aviso"); a.add_argument("--segundos", type=float); a.add_argument("--sombra", action="store_true"); a.add_argument("--momento")
    a = a.parse_args(argv)
    fotos = replay.cargar(a.archivo)
    rs = [r for r in replay.repetir(fotos) if r["meta"]]
    a.sombra = a.sombra or bool(a.momento)
    g = replay.guion_de(fotos) if a.sombra else None
    desde = 0
    if a.momento:  # la primera foto donde pasa ese momento (por la bitácora del motor), y se arranca una antes
        ms = [r for r in replay.repetir_momentos(fotos, g) if r["meta"]]
        i = next((i for i, r in enumerate(ms) if (r["escena"] or {}).get("panel")) if a.momento == "muerto"
                 else (i for i, r in enumerate(ms) if any(n["id"].split(":")[0] == a.momento and n["mostrado"] for n in r["notas"])), None)
        if i is None: sys.exit(f"«{a.momento}» no se muestra en esta partida")
        desde = max(0, i - 1); print(f"{a.momento} a los {replay.reloj(ms[i]['t'])}")
    fijo, inicio = cuadro(rs, a.minuto) if a.minuto else None, time.time()
    fin = inicio + (a.segundos or (30 if fijo else 10 if a.momento else len(rs)))

    def leer():
        r = fijo or rs[min(len(rs) - 1, desde + int(time.time() - inicio))]
        aviso = {"corto": a.aviso, "franja": inicio} if a.aviso else None
        return {"fase": "InProgress", "meta": {**r["meta"], "recibido": time.time()}, "ajustes": {"franja_estilo": "sombra" if a.sombra else "clasica"},
                "aviso": aviso, "guion": g}

    import companion_web
    overlay.correr(leer, lambda: time.time() < fin, icono=companion_web.imagen)


if __name__ == "__main__": main()
