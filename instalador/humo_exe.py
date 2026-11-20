"""Humo de la build: arranca Companion.exe --demo --no-abrir, busca su puerto y pide /api/estado.
  python instalador/humo_exe.py [ruta.exe]   sale con 0 si responde JSON con 'fase'."""
import json, pathlib, re, subprocess, sys, time, urllib.request

exe = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent / "dist" / "HTC" / "HTC.exe")
faltan = [m for m in ("_sqlite3.pyd", "_tkinter.pyd") if not list(exe.parent.rglob(m))]  # los scripts del disco los importan (indice.py, overlay)
if faltan: print("falta en la build:", ", ".join(faltan)); sys.exit(1)
def franja_ok():
    """La franja en su proceso (HTC.exe --franja): se conecta con el token, sigue viva con la ventana creada (no le faltó
    ningún módulo a la build) y se cierra sola al cerrarle el socket."""
    import socket, secrets
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1); srv.settimeout(20); tok = secrets.token_hex(8)
    h = subprocess.Popen([str(exe), "--franja", str(srv.getsockname()[1]), tok])
    try:
        c, _ = srv.accept(); c.settimeout(10)
        ok = c.makefile("r", encoding="utf-8").readline().strip() == tok
        time.sleep(3); vivo = h.poll() is None  # importó overlay y abrió tkinter sin tronar
        c.close(); h.wait(10)
        print("franja:", "OK" if ok and vivo else "FALLA", f"(token {ok}, viva tras 3 s {vivo}, salió sola con {h.returncode})"); return ok and vivo
    except (OSError, subprocess.TimeoutExpired) as x: print("franja: FALLA", x); return False
    finally:
        srv.close()
        if h.poll() is None: h.kill()


LISTEN = r"127\.0\.0\.1:(\d+)\s+\S+\s+LISTENING\s+(\d+)"
netstat = lambda: subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True).stdout
antes = {port for port, _ in re.findall(LISTEN, netstat())}  # puertos de un Companion.exe ya abierto no cuentan
t0 = time.time(); p = subprocess.Popen([str(exe), "--demo", "--no-abrir"])
try:
    while time.time() - t0 < 30:  # onefile desempaca y el server corre en un proceso hijo: se buscan todos los Companion.exe
        time.sleep(0.1)
        tl = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {exe.name}", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
        pids = set(re.findall(r'^"[^"]+","(\d+)"', tl, re.M))
        ports = [port for port, pid in re.findall(LISTEN, netstat()) if pid in pids and port not in antes]
        if ports:
            d = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{ports[0]}/api/estado", timeout=5).read())
            print(f"OK en {time.time() - t0:.2f} s · puerto", ports[0], "fase =", d.get("fase"), "| claves:", sorted(d))
            sys.exit(0 if "fase" in d and franja_ok() else 1)
    print("sin puerto tras 30 s"); sys.exit(1)
finally:
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
