"""Solo desarrollo: arma docs/img/readme/hero.png, pasos.png y hero-app-*.avif/webp desde las páginas de esta carpeta con Edge sin ventana.
Usa las capturas reales de docs/img/readme/*.webp: recapturarlas primero si cambió la app.
  python herramientas/composicion/armar.py [hero hero-app pasos]"""
import pathlib, subprocess, sys, tempfile
AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent.parent / "scripts"))
import ventana  # noqa: E402
SALIDA = AQUI.parent.parent / "docs" / "img" / "readme"
PAGINAS = {"hero": (1600, 800), "pasos": (1600, 460), "hero-app": (1200, 900)}
for nombre, (w, h) in PAGINAS.items():
    if sys.argv[1:] and nombre not in sys.argv[1:]: continue
    with tempfile.TemporaryDirectory() as perfil:
        subprocess.run([ventana.edge(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files", f"--user-data-dir={perfil}",
                        f"--window-size={w},{h}", "--virtual-time-budget=4000", f"--screenshot={SALIDA / (nombre + '.png')}", (AQUI / f"{nombre}.html").as_uri()],
                       capture_output=True, timeout=120)
    print(nombre, (SALIDA / f"{nombre}.png").stat().st_size // 1024, "KB")
    if nombre == "hero-app":  # la portada lo sirve en AVIF y WebP, a 800 y 1200 de ancho; el PNG no se publica
        from PIL import Image
        png = SALIDA / "hero-app.png"
        with Image.open(png) as im:
            for ancho in (800, 1200):
                r = im.convert("RGB").resize((ancho, ancho * h // w), Image.LANCZOS)
                r.save(SALIDA / f"hero-app-{ancho}.avif", quality=55)
                r.save(SALIDA / f"hero-app-{ancho}.webp", quality=80)
                print(f"hero-app-{ancho}", *(f"{(SALIDA / f'hero-app-{ancho}.{x}').stat().st_size // 1024} KB {x}" for x in ("avif", "webp")))
        png.unlink()
