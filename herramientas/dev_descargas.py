"""Foto de las descargas del instalador para medir la portada sin rastreadores.

GitHub da `download_count` acumulado por archivo; este script anota la suma de los .exe de todos los releases con la fecha,
en design-os/medicion/descargas.csv. Correrlo una vez por semana (y el día que se publica un cambio de la portada):
la diferencia entre dos fotos son las descargas de ese periodo.
Uso: python herramientas/dev_descargas.py [nota]   — la nota marca el cambio publicado ese día (p. ej. "carrusel").
"""
import csv, datetime, json, pathlib, sys, urllib.request

REPO = "C0z1/racha.gg"
CSV = pathlib.Path(__file__).resolve().parents[1] / "design-os" / "medicion" / "descargas.csv"


def total_exe(releases):
    return sum(a["download_count"] for r in releases for a in r.get("assets", []) if a["name"].endswith(".exe"))


def leer_releases():
    todos, pagina = [], 1
    while True:
        req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases?per_page=100&page={pagina}",
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": "racha-dev"})
        with urllib.request.urlopen(req, timeout=20) as r:
            lote = json.load(r)
        todos += lote
        if len(lote) < 100:
            return todos
        pagina += 1


def main():
    assert total_exe([{"assets": [{"name": "a.exe", "download_count": 3}, {"name": "b.zip", "download_count": 9}]},
                      {"assets": [{"name": "c.exe", "download_count": 2}]}]) == 5
    releases = leer_releases()
    total, ultimo = total_exe(releases), (releases[0]["tag_name"] if releases else "")
    CSV.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not CSV.exists()
    previo = None
    if not nuevo:
        filas = list(csv.DictReader(CSV.open(encoding="utf-8")))
        previo = int(filas[-1]["total_exe"]) if filas else None
    with CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["fecha", "total_exe", "ultimo_release", "nota"])
        w.writerow([datetime.date.today().isoformat(), total, ultimo, " ".join(sys.argv[1:])])
    print(f"{total} descargas acumuladas del .exe" + (f" (+{total - previo} desde la foto anterior)" if previo is not None else " (primera foto)"))


if __name__ == "__main__":
    main()
