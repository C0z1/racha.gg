"""Solo desarrollo (no va en el .exe): capturas de cada vista con Edge headless y el tiempo del primer pintado de Inicio.
Levanta un Racha propio sin ventana ni franja (--no-abrir) sobre tus datos.
  python herramientas/dev_medir.py [carpeta]   (por defecto datos/salud/estela)
  python herramientas/dev_medir.py --franja [carpeta]   la salud de la franja Sombra por forma de sondeo (1 s o 3 s, modo
    ahorro) contra las metas de la Fase 1; sale con 1 si alguna falla. Por defecto, la carpeta de salud de HTC instalado."""
import json, pathlib, re, subprocess, sys, time, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))  # la app vive en scripts/
import ventana

VISTAS = ("inicio", "draft", "companion", "envivo", "perfil", "partidas", "campeones", "errores", "ajustes")
TAMANOS = ((1440, 1024), (1100, 720))


def edge(*args, timeout=60):
    return subprocess.run([ventana.edge(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


META_FRANJA = {"lat_p95": 1.5, "cpu": 1.0, "ram": 60}  # Fase 1 del plan Sombra: s, % de un núcleo (estricto <), MB


def franja(carpeta):
    """{sondeo: {n, lat_p95, cpu, ram, fallas}} con lo peor de los renglones de franja-*.jsonl (uno cada 30 s de partida)."""
    filas = []
    for f in sorted(pathlib.Path(carpeta).glob("franja-*.jsonl")):
        for x in f.read_text(encoding="utf-8").splitlines():
            try: filas.append(json.loads(x))
            except ValueError: pass  # un renglón cortado si HTC se cerró escribiendo
    out = {}
    for s in sorted({r.get("sondeo") for r in filas}, key=str):
        rs = [r for r in filas if r.get("sondeo") == s]
        peor = {k: max((r[k] for r in rs if r.get(k) is not None), default=None) for k in META_FRANJA}
        fallas = [f"{k} {v} (meta {'<' if k == 'cpu' else '≤'} {META_FRANJA[k]})" for k, v in peor.items()
                  if v is not None and (v >= META_FRANJA[k] if k == "cpu" else v > META_FRANJA[k])]
        out[s] = {"n": len(rs), **peor, "fallas": fallas}
    return out


def main_franja(carpeta=None):
    import os
    sys.stdout.reconfigure(encoding="utf-8")
    carpeta = carpeta or pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "HTC" / "datos" / "salud"
    r = franja(carpeta)
    if not r: print(f"sin renglones de salud de la franja en {carpeta}"); return 1
    for s, x in r.items():
        print(f"sondeo {s} s · {x['n']} renglones ({x['n'] / 2:.0f} min) · peor p95 {x['lat_p95']} s · CPU máx {x['cpu']} % · RAM máx {x['ram']} MB"
              f" · {'FALLA: ' + ', '.join(x['fallas']) if x['fallas'] else 'OK'}")
    return 1 if any(x["fallas"] for x in r.values()) else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--franja"]: sys.exit(main_franja(argv[1] if len(argv) > 1 else None))
    out = pathlib.Path(argv[0] if argv else pathlib.Path(__file__).resolve().parent.parent / "datos" / "salud" / "estela").resolve(); out.mkdir(parents=True, exist_ok=True)  # absoluta: Edge resuelve otra carpeta
    srv = subprocess.Popen([sys.executable, str(pathlib.Path(__file__).resolve().parent.parent / "scripts" / "companion_web.py"), "--no-abrir"], stdout=subprocess.PIPE, text=True)
    try:
        url = srv.stdout.readline().strip()
        for _ in range(120):  # que refrescar() termine de calcular el rendimiento (con la caché vieja puede tardar)
            try:
                if json.load(urllib.request.urlopen(url + "api/estado", timeout=5)).get("rendimiento"): break
            except (OSError, ValueError): pass
            time.sleep(1)
        for w, h in TAMANOS:
            for v in VISTAS:
                edge(f"--window-size={w},{h}", f"--screenshot={out / f'{v}-{w}.png'}", "--virtual-time-budget=4000", f"{url}#{v}")
        ms = []
        for _ in range(3):
            dom = edge("--window-size=1440,1024", "--virtual-time-budget=8000", "--dump-dom", f"{url}#inicio&medir").stdout
            if m := re.search(r'data-medida="(\d+)"', dom): ms.append(int(m[1]))
        print(f"capturas en {out}; primer pintado de Inicio (ms): {ms}")
        return ms
    finally: srv.terminate()


if __name__ == "__main__": main()
