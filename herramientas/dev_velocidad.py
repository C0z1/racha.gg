"""Solo desarrollo: cuánto tarda cada lectura pesada de Racha con tus partidas reales, cada una en un proceso nuevo (en frío).
  python herramientas/dev_velocidad.py            (DATOS_DIR o datos/raw)
Sirve para medir antes y después de un cambio de rendimiento."""
import os, subprocess, sys, pathlib

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
PASOS = {
    "draft (champ select)": "import draft",
    "rendimiento + vistas (arranque)": "import companion_web as w; w.rendimiento()",
    "score.partidas": "import score; score.partidas()",
    "última partida (post-partida)": "import companion_gui as g; g.ultima_partida()",
    "revisión post-partida (revision.py)": "import subprocess; subprocess.run([sys.executable, sys.path[0] + '/revision.py', '1'], capture_output=True)",  # la app la corre como proceso aparte
    "import builds": "import builds",
}


def medir(codigo):
    prog = f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); t = time.perf_counter(); {codigo}; print(time.perf_counter() - t, file=sys.stderr)"
    r = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    try: return float(r.stderr.strip().splitlines()[-1])
    except (ValueError, IndexError): return None


if __name__ == "__main__":
    for nombre, codigo in PASOS.items():
        ts = [t for t in (medir(codigo) for _ in range(2)) if t is not None]
        print(f"{nombre:34} {min(ts):6.2f} s" if ts else f"{nombre:34}  falló")
