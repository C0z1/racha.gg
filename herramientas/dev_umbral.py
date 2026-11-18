"""Solo desarrollo: ¿qué umbral de cuota de rol adivina mejor a tu rival de línea en ranked (companion_gui.rivales_linea)?
Con tus partidas reales: por cada Solo/Duo o Flex, tu posición y los 5 enemigos; el rival verdadero es el de tu posición.
Riot oculta los roles y los enemigos fijan en un orden que no se guarda: con un orden al azar, lo visible en cada momento
es un subconjunto al azar de los 5, así que se prueban los 31 subconjuntos (exacto, sin azar). Tu historial (el desempate)
se arma sin la partida que se evalúa. Se elige con las partidas de id par y se confirma con las de id impar.
  python herramientas/dev_umbral.py [carpeta datos]   (por defecto %LOCALAPPDATA%/Programs/HTC/datos)"""
import collections, itertools, json, os, pathlib, sys, tempfile

DATOS = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(os.environ["LOCALAPPDATA"]) / "Programs" / "HTC" / "datos")
os.environ.update(DATOS_DIR=str(DATOS / "raw"), RACHA_INDICE=str(pathlib.Path(tempfile.gettempdir()) / "racha-umbral.db"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import builds, companion_gui as g, draft, score  # noqa: E402
builds.META = DATOS / "meta"
UMBRALES = (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4)

yo = json.loads((DATOS / "raw" / "perfil.json").read_text())["account"]["puuid"]
casos = []  # (id, pos, rival verdadero, [5 enemigos], t)
for f in sorted((DATOS / "raw").glob("*_*.json")):
    m = score.cargar_partida(f)
    if not m or m["info"].get("queueId") not in (420, 440): continue
    ps = m["info"]["participants"]; me = next((p for p in ps if p["puuid"] == yo), None)
    if not me or not me.get("teamPosition"): continue
    en = [p for p in ps if p["teamId"] != me["teamId"]]
    rv = next((p["championName"] for p in en if p["teamPosition"] == me["teamPosition"]), None)
    if rv and len(en) == 5: casos.append((int(f.stem.split("_")[1]), me["teamPosition"], rv, [p["championName"] for p in en], m["info"]["gameCreation"]))

todos = draft.games
def evaluar(sub):
    r = {u: collections.Counter() for u in UMBRALES}
    for _, pos, rv, en, t in sub:
        draft.games = [x for x in todos if x["t"] != t]  # el desempate no ve la partida que se evalúa
        n = 0
        for k in range(1, 6):
            for vis in itertools.combinations(en, k):
                n += 1
                for u in UMBRALES:
                    out = g.rivales_linea(pos, list(vis), umbral=u)
                    r[u]["acierto" if out == [rv] else "espera bien" if not out and rv not in vis else "espera de más" if not out else "equivocado"] += 1
        assert n == 31, n
    draft.games = todos
    return r

def tabla(nombre, r):
    print(f"\n{nombre}  (casos = partidas × 31 subconjuntos)\numbral  acierto  espera bien  espera de más  equivocado")
    for u, c in r.items():
        tot = sum(c.values()) or 1
        print(f"{u:6.2f}  " + "  ".join(f"{100 * c[x] / tot:6.1f} %" for x in ("acierto", "espera bien", "espera de más", "equivocado")))

if __name__ == "__main__":
    pares, impares = [c for c in casos if c[0] % 2 == 0], [c for c in casos if c[0] % 2]
    print(f"{len(casos)} partidas ranked ({len(pares)} para elegir, {len(impares)} para confirmar)")
    rp, ri = evaluar(pares), evaluar(impares)
    tabla("Elegir (id par)", rp); tabla("Confirmar (id impar)", ri)
    malo = lambda c: (c["equivocado"] + c["espera de más"]) / (sum(c.values()) or 1)
    mejor = min(UMBRALES, key=lambda u: (malo(rp[u]), u))
    print(f"\nmejor umbral con las pares: {mejor}  (errores {100 * malo(rp[mejor]):.1f} %; con las impares {100 * malo(ri[mejor]):.1f} %, "
          f"el 0.25 actual {100 * malo(ri[0.25]):.1f} %)")
