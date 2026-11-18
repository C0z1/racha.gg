"""Solo desarrollo: arma docs/img/readme/hero.png y pasos.png desde las páginas de esta carpeta con Edge sin ventana.
Usa las capturas reales de docs/img/readme/*.webp: recapturarlas primero si cambió la app.
  python herramientas/composicion/armar.py"""
import pathlib, subprocess, sys, tempfile
AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent.parent / "scripts"))
import ventana  # noqa: E402
SALIDA = AQUI.parent.parent / "docs" / "img" / "readme"
for nombre, (w, h) in {"hero": (1600, 800), "pasos": (1600, 460)}.items():
    with tempfile.TemporaryDirectory() as perfil:
        subprocess.run([ventana.edge(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files", f"--user-data-dir={perfil}",
                        f"--window-size={w},{h}", "--virtual-time-budget=4000", f"--screenshot={SALIDA / (nombre + '.png')}", (AQUI / f"{nombre}.html").as_uri()],
                       capture_output=True, timeout=120)
    print(nombre, (SALIDA / f"{nombre}.png").stat().st_size // 1024, "KB")
