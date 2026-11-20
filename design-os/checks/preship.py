"""preship: los 20 puntos de design-os/rules/web-20.md y los chequeos estáticos de DESIGN.md.
Sirve docs/ con http.server en un puerto libre y abre la página con Edge (Playwright, channel="msedge") a 390×844 y 1440×900.
  python design-os/checks/preship.py                       la portada (docs/index.html)
  python design-os/checks/preship.py --ref https://...     además, la referencia lado a lado (si la bloquean: SKIP)
Imprime los FAIL primero, luego SKIP, TODO y PASS, y al final n/20. Sale con 1 si algo falla."""
import argparse, ast, functools, http.server, pathlib, re, sys, threading, urllib.error, urllib.request

import yaml
from playwright.sync_api import sync_playwright

RAIZ = pathlib.Path(__file__).resolve().parents[2]
DOS, DOCS = RAIZ / "design-os", RAIZ / "docs"
VISTAS = [(390, 844), (1440, 900)]
SECCIONES = ["Overview", "Colors", "Typography", "Layout", "Elevation & Depth", "Shapes", "Components", "Do's and Don'ts",
             "Iconography", "Voice"]
EXE = re.compile(r"/Racha-Setup-[\d.]+\.exe$")
API = "https://api.github.com/repos/C0z1/racha.gg/releases/latest"


# Contraste: la misma fórmula que pruebas/test_ds_estela.py
def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def contraste(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)


# --- Lo que corre dentro de la página -------------------------------------------------------------------------------
JS = r"""
window.__ps = (() => {
  const parse = s => { let m = s.match(/rgba?\(([^)]+)\)/);
    if (m) { const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; }
    m = s.match(/color\(srgb ([^)]+)\)/);
    if (m) { const p = m[1].split(/[\s\/]+/).filter(Boolean).map(Number); return [p[0] * 255, p[1] * 255, p[2] * 255, p.length > 3 ? p[3] : 1]; }
    return [0, 0, 0, 0]; };
  const sobre = (c, f) => [0, 1, 2].map(i => c[i] * c[3] + f[i] * (1 - c[3])).concat(1);
  const hex = c => "#" + c.slice(0, 3).map(x => Math.round(Math.max(0, Math.min(255, x))).toString(16).padStart(2, "0")).join("");
  const fondo = el => { const capas = [];  // del elemento hacia arriba, hasta un fondo opaco
    for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c[3] > 0) capas.push(c); if (c[3] >= 1) break; }
    let f = [255, 255, 255, 1]; for (const c of capas.reverse()) f = sobre(c, f); return f; };
  const opacidad = el => { let o = 1; for (let e = el; e; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
  const corto = el => { let s = el.tagName.toLowerCase(); if (el.id) s += "#" + el.id; else if (el.classList.length) s += "." + [...el.classList].join("."); return s; };
  const sel = el => (el.parentElement && el.parentElement !== document.body ? corto(el.parentElement) + " > " : "") + corto(el);
  const visible = el => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== "hidden"; };
  return {
    textos() { const out = [], vistos = new Set();
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      for (let n; (n = w.nextNode());) { const el = n.parentElement; if (!n.textContent.trim() || vistos.has(el) || !visible(el) || /^(SCRIPT|STYLE|NOSCRIPT)$/.test(el.tagName)) continue;
        vistos.add(el); const cs = getComputedStyle(el), f = fondo(el), c = parse(cs.color); c[3] *= opacidad(el);
        out.push({sel: sel(el), txt: n.textContent.trim().slice(0, 40), fg: hex(sobre(c, f)), bg: hex(f)}); }
      return out; },
    color(el) { const cs = getComputedStyle(el), f = fondo(el), c = parse(cs.color); c[3] *= opacidad(el); return {fg: hex(sobre(c, f)), bg: hex(f)}; },
    foco() { const el = document.activeElement; if (!el || el === document.body) return null; const cs = getComputedStyle(el);
      const c = parse(cs.outlineColor), f = fondo(el.parentElement || el);
      return {sel: sel(el), estilo: cs.outlineStyle, ancho: parseFloat(cs.outlineWidth), color: c[3] ? hex(sobre(c, f)) : null, bg: hex(f),
              radio: cs.borderRadius, clase: el.className}; },
    sel,
  };
})();
"""

MEDIR = r"""async () => {
  const lcp = await new Promise(ok => { let u = null; new PerformanceObserver(l => { const e = l.getEntries(); u = e[e.length - 1]; })
    .observe({type: "largest-contentful-paint", buffered: true}); setTimeout(() => ok(u && {t: u.startTime, url: u.url, sel: u.element ? __ps.sel(u.element) : "",
      img: u.element && u.element.tagName === "IMG" ? u.element : null}), 400); });
  if (lcp) { lcp.esImg = !!lcp.img; lcp.img && (lcp.img.dataset.psLcp = "1"); delete lcp.img; }
  const imgs = [...document.images].map(i => ({sel: __ps.sel(i), alt: i.hasAttribute("alt"), w: i.hasAttribute("width"), h: i.hasAttribute("height"),
    src: (i.currentSrc || i.src).split("?")[0], lazy: i.loading === "lazy", lcp: i.dataset.psLcp === "1"}));
  const hs = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].map(h => ({n: +h.tagName[1], t: h.textContent.trim().slice(0, 40)}));
  const q = s => { const e = document.querySelector(s); return e && e.getAttribute("content"); };
  const caja = s => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return {top: r.top, bottom: r.bottom, h: innerHeight}; };
  return {lcp, imgs, hs, title: document.title, desc: q('meta[name="description"]'), og: q('meta[property="og:image"]'),
          ancho: document.documentElement.scrollWidth, vw: innerWidth,
          boton: caja("header [data-descarga], main [data-descarga]"), confianza: caja(".confianza"),
          descargas: [...document.querySelectorAll("[data-descarga]")].map(a => a.href)};
}"""

BAJAR = r"""async () => { const cls = []; new PerformanceObserver(l => l.getEntries().forEach(e => { if (!e.hadRecentInput) cls.push(e.value); }))
    .observe({type: "layout-shift", buffered: true});
  const vivas = [];
  for (let y = 0; y <= document.documentElement.scrollHeight; y += Math.round(innerHeight * .6)) {
    scrollTo({top: y, behavior: "instant"}); await new Promise(r => setTimeout(r, 220));
    document.getAnimations().forEach(a => vivas.push((a.animationName || a.transitionProperty || a.constructor.name) + " en " + (a.effect && a.effect.target ? __ps.sel(a.effect.target) : "?")));
  }
  await new Promise(r => setTimeout(r, 900)); scrollTo({top: 0, behavior: "instant"}); await new Promise(r => setTimeout(r, 200));
  return {cls: cls.reduce((a, b) => a + b, 0), vivas: [...new Set(vivas)]};
}"""

TEXTO = r"""() => { const out = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = w.nextNode());) if (!/^(SCRIPT|STYLE|NOSCRIPT)$/.test(n.parentElement.tagName)) out.push(n.textContent);
  const bloques = [...document.querySelectorAll("p,li,h1,h2,h3,h4,summary,figcaption,td,th,a,button,dt,dd")].map(e => e.textContent.replace(/\s+/g, " ").trim());
  const emojis = (out.join(" ").match(/\p{Extended_Pictographic}/gu) || []);
  const pie = (document.querySelector("footer") || document.body).textContent.replace(/\s+/g, " ");
  return {bloques, emojis, pie}; }"""


# --- Utilidades ------------------------------------------------------------------------------------------------------
class Res:
    def __init__(self): self.p = {n: [] for n in range(1, 21)}; self.extra = []
    def add(self, n, estado, detalle=""): self.p[n].append((estado, detalle))
    def estado(self, n):
        es = [e for e, _ in self.p[n]]
        return "FAIL" if "FAIL" in es else "SKIP" if "SKIP" in es else "PASS" if es else "SKIP"


class Callado(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


def servir(carpeta):
    H = functools.partial(Callado, directory=str(carpeta))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


class SinRedirigir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a): return None


def head(url):
    try:
        return urllib.request.build_opener(SinRedirigir).open(urllib.request.Request(url, method="HEAD", headers={"User-Agent": "preship"}), timeout=8).status
    except urllib.error.HTTPError as e:
        return e.code


def palabras():
    """Los términos prohibidos de rules/words.md y los IMPERATIVOS de herramientas/replay.py."""
    txt = (DOS / "rules" / "words.md").read_text(encoding="utf-8")
    nunca = txt.split("## Nunca se dice", 1)[1]
    reglas = []
    for t in re.findall(r"^- `([^`]+)`\s*$", nunca, re.M):
        reglas.append((t, re.compile(t[3:] if t.startswith("re:") else rf"(?<!\w){re.escape(t)}(?!\w)", re.I)))
    rep = (RAIZ / "herramientas" / "replay.py").read_text(encoding="utf-8")
    imps = ast.literal_eval(re.search(r"^IMPERATIVOS = (\(.*?\))", rep, re.M | re.S).group(1))
    # imperativo = al empezar una frase o una cláusula; «nunca en una pelea» es sustantivo, «Juega.» es orden
    for i in imps:
        reglas.append((f"imperativo «{i}»", re.compile(rf"(?:^|[.:;!?¡¿«—]\s*){re.escape(i)}(?!\w)", re.I)))
    return reglas


def legal():
    m = re.search(r"Racha isn't endorsed.*?Riot Games, Inc\.", (RAIZ / "README.md").read_text(encoding="utf-8"))
    return m.group(0)


# --- Chequeos estáticos ------------------------------------------------------------------------------------------------
def estaticos(r):
    d = (DOS / "DESIGN.md").read_text(encoding="utf-8")
    lineas = d.splitlines()
    fallas = []
    if len(lineas) >= 250: fallas.append(f"DESIGN.md tiene {len(lineas)} líneas (máx. 249)")
    secs = re.findall(r"^## (.+?)\s*$", d, re.M)
    if secs != SECCIONES: fallas.append(f"DESIGN.md: secciones {secs} (esperadas {SECCIONES})")
    y = yaml.safe_load(d.split("---", 2)[1])
    for k in ("version", "name", "description", "colors", "typography", "rounded", "spacing", "components"):
        if k not in y: fallas.append(f"DESIGN.md: falta «{k}» en el YAML")
    for ref in re.findall(r"\{([a-z0-9-]+\.[a-z0-9-]+)\}", d):
        a, b = ref.split(".")
        if b not in (y.get(a) or {}): fallas.append(f"DESIGN.md: {{{ref}}} no existe en el YAML")
    colores = {}
    for k, v in (y.get("colors") or {}).items():
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(v)): fallas.append(f"DESIGN.md: color {k}={v} no es un hex válido")
        else: colores[v.upper()] = k
    todos = [f"L{i}: {l.strip()[:110]}" for i, l in enumerate(lineas, 1) if "TODO" in l]
    for f in fallas: r.extra.append(("FAIL", "[DESIGN] " + f))
    # punto 14: todo hex del CSS de la portada es un token
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    css = "\n".join(re.findall(r"<style>(.*?)</style>", html, re.S) + re.findall(r'style="([^"]*)"', html))
    malos = sorted({h for h in re.findall(r"#[0-9A-Fa-f]{3,8}\b", css)
                    if (h if len(h) != 4 else "#" + "".join(c * 2 for c in h[1:])).upper() not in colores})
    for m in re.findall(r"rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)", css):
        if "#%02X%02X%02X" % tuple(map(int, m)) not in colores: malos.append("rgb(" + ",".join(m) + ")")
    r.add(14, "FAIL" if malos else "PASS", ("fuera de tokens: " + ", ".join(malos)) if malos else f"{len(colores)} tokens; todo hex del CSS es token")
    return todos


# --- Chequeos en el navegador ------------------------------------------------------------------------------------------
def medir_vista(nav, url, w, h, r, propia, reglas=None, texto_legal=None):
    """Una vista: carga, mide y devuelve las cifras para la tabla. r=None para la referencia (solo mide)."""
    ctx = nav.new_context(viewport={"width": w, "height": h})
    ctx.add_init_script(JS)
    pg = ctx.new_page()
    errores, malos = [], []
    pg.on("console", lambda m: m.type == "error" and errores.append(m.text[:140]))
    pg.on("pageerror", lambda e: errores.append(str(e)[:140]))
    pg.on("response", lambda res: res.status >= 400 and malos.append((res.status, res.url[:120])))
    cdp = ctx.new_cdp_session(pg); cdp.send("Network.enable")
    bytes_ = {"n": 0}; urls = {}; tam = {}
    cdp.on("Network.responseReceived", lambda e: urls.__setitem__(e["requestId"], e["response"]["url"]))
    cdp.on("Network.loadingFinished", lambda e: (bytes_.__setitem__("n", bytes_["n"] + e["encodedDataLength"]),
                                                 tam.__setitem__(urls.get(e["requestId"], ""), e["encodedDataLength"])))
    resp = pg.goto(url, wait_until="load", timeout=45000)
    titulo = pg.title()
    if resp is None or resp.status in (403, 429, 503) or re.search(r"just a moment|attention required|access denied|captcha", titulo, re.I):
        ctx.close(); return {"bloqueada": f"HTTP {resp and resp.status} · «{titulo}»"}
    pg.wait_for_timeout(1500 if propia else 4000)
    m = pg.evaluate(MEDIR)
    inicial = bytes_["n"]
    v = f"{w}"
    lcp = m["lcp"] or {}
    lcp_kb = tam.get(lcp.get("url") or "", 0) / 1024 if lcp.get("url") else 0
    datos = {"lcp_ms": round(lcp.get("t", 0)), "lcp_kb": round(lcp_kb, 1), "inicial_kb": round(inicial / 1024), "ancho": m["ancho"], "vw": m["vw"]}
    if r is not None:
        # 3 · scroll horizontal
        r.add(3, "PASS" if m["ancho"] <= m["vw"] else "FAIL", f"{v}: scrollWidth {m['ancho']} / {m['vw']}")
        # 5 · LCP
        ok5 = lcp_kb < 80 and lcp.get("t", 9e9) < 2500
        r.add(5, "PASS" if ok5 else "FAIL", f"{v}: LCP {datos['lcp_ms']} ms, {datos['lcp_kb']} KB ({lcp.get('sel') or 'sin LCP'})")
        # 6 · carga inicial
        r.add(6, "PASS" if inicial < 400 * 1024 else "FAIL", f"{v}: carga inicial {datos['inicial_kb']} KB")
        # 7 · alt y medidas
        sin = [i["sel"] for i in m["imgs"] if not (i["alt"] and i["w"] and i["h"])]
        r.add(7, "FAIL" if sin else "PASS", f"{v}: " + (("sin alt o width/height: " + ", ".join(sin)) if sin else f"{len(m['imgs'])} img con alt y medidas"))
        # 8 · encabezados
        hs = m["hs"]; saltos = [f"h{a['n']}→h{b['n']} «{b['t']}»" for a, b in zip(hs, hs[1:]) if b["n"] > a["n"] + 1]
        n1 = sum(1 for x in hs if x["n"] == 1)
        r.add(8, "PASS" if n1 == 1 and not saltos and hs and hs[0]["n"] == 1 else "FAIL", f"{v}: {n1} h1" + (f"; saltos: {', '.join(saltos)}" if saltos else ""))
        # 13 · botón y confianza sin scroll
        fuera = [k for k in ("boton", "confianza") if propia and (not m[k] or m[k]["top"] < 0 or m[k]["bottom"] > m[k]["h"])]
        r.add(13, "FAIL" if fuera else "PASS", f"{v}: " + (("fuera del primer pantallazo: " + ", ".join(fuera)) if fuera else
              f"botón abajo en {round(m['boton']['bottom'])}px, confianza en {round(m['confianza']['bottom'])}px de {h}"))
        # 18 · formatos y lazy
        mal18 = [f"{i['sel']} ({i['src'].rsplit('.', 1)[-1]}{'' if i['lazy'] or i['lcp'] else ', sin lazy'})" for i in m["imgs"]
                 if not re.search(r"\.(avif|webp)$", i["src"]) or not (i["lazy"] or i["lcp"])]
        r.add(18, "FAIL" if mal18 else "PASS", f"{v}: " + (", ".join(mal18) if mal18 else "AVIF/WebP y lazy salvo el LCP"))
        # 11 · descargas al .exe (el HEAD se hace una vez, afuera)
        r.descargas = m["descargas"]
        no_exe = [d for d in m["descargas"] if not EXE.search(d)]
        r.add(11, "SKIP" if (no_exe and r.sin_api) else "FAIL" if no_exe or not m["descargas"] else "PASS",
              f"{v}: " + (f"sin .exe: {no_exe} ({r.sin_api})" if no_exe and r.sin_api else f"no terminan en .exe: {no_exe}" if no_exe else f"{len(m['descargas'])} botones al .exe"))
        # 15, 16, 17 · texto
        t = pg.evaluate(TEXTO)
        r.add(15, "FAIL" if t["emojis"] else "PASS", f"{v}: " + (f"emojis: {t['emojis']}" if t["emojis"] else "sin emojis"))
        hits = sorted({f"{nombre} en «{b[:60]}»" for b in t["bloques"] for nombre, rx in reglas
                       if rx.search(re.sub(r"«[^»]*»", "«»", b) if nombre.startswith("imperativo") else b)})
        r.add(16, "FAIL" if hits else "PASS", f"{v}: " + ("; ".join(hits[:6]) if hits else f"{len(reglas)} términos, ninguno"))
        r.add(17, "PASS" if texto_legal in t["pie"] else "FAIL", f"{v}: aviso legal de Riot " + ("literal" if texto_legal in t["pie"] else "ausente o distinto"))
        # 20 · title, description y og:image (la imagen se pide al servidor local si es de nuestro dominio)
        og = m["og"] or ""
        local = re.sub(r"^https://racha-gg\.vercel\.app/", url, og)
        st = head(local) if og else None
        ok20 = bool(m["title"] and m["desc"] and og and st == 200)
        r.add(20, "PASS" if ok20 else "FAIL", f"{v}: title {'sí' if m['title'] else 'NO'}, description {'sí' if m['desc'] else 'NO'}, og:image {og or 'NO'} → {st}")
    # 4 · CLS hasta el final del scroll (y para 10, las animaciones vivas no importan aquí)
    b = pg.evaluate(BAJAR)
    datos["cls"] = round(b["cls"], 3)
    if r is not None:
        r.add(4, "PASS" if b["cls"] < .05 else "FAIL", f"{v}: CLS {datos['cls']}")
        # 19 · consola y 404 (la API de GitHub sin cuota es del entorno: va a 11)
        propios = [f"{s} {u}" for s, u in malos if "api.github.com" not in u]
        errs = [e for e in errores if not (r.sin_api and "403" in e)]
        r.add(19, "FAIL" if propios or errs else "PASS", f"{v}: " + ("; ".join(propios + errs)[:300] if propios or errs else "consola limpia, sin 404"))
        # 1 · contraste del texto
        bajos = sorted({f"{t['sel']} «{t['txt']}» {contraste(t['fg'], t['bg']):.2f}:1 ({t['fg']} sobre {t['bg']})"
                        for t in pg.evaluate("() => __ps.textos()") if contraste(t["fg"], t["bg"]) < 4.5})
        r.add(1, "FAIL" if bajos else "PASS", f"{v}: " + ("; ".join(bajos[:8]) if bajos else "todo el texto ≥ 4.5:1"))
        # 2 · botones, normal y en hover
        mal2 = []
        for i, b in enumerate(pg.query_selector_all(".btn, button")):
            if not b.is_visible(): continue
            for modo in ("normal", "hover"):
                if modo == "hover": b.hover(); pg.wait_for_timeout(250)
                c = b.evaluate("e => __ps.color(e)"); k = contraste(c["fg"], c["bg"])
                if k < 4.5: mal2.append(f"{b.evaluate('e => __ps.sel(e)')} {modo} {k:.2f}:1")
        pg.mouse.move(0, 0)
        r.add(2, "FAIL" if mal2 else "PASS", f"{v}: " + (", ".join(mal2) if mal2 else "botones ≥ 4.5:1, también en hover"))
        # 9 · foco al tabular
        pg.evaluate("() => { scrollTo(0, 0); document.activeElement && document.activeElement.blur(); }")
        mal9, vistos, primero = [], 0, None
        for _ in range(80):
            pg.keyboard.press("Tab"); pg.wait_for_timeout(260)
            f = pg.evaluate("() => __ps.foco()")
            if not f or f["sel"] == primero: break
            primero = primero or f["sel"]; vistos += 1
            k = contraste(f["color"], f["bg"]) if f["color"] else 0
            if f["estilo"] == "none" or f["ancho"] < 3 or k < 3: mal9.append(f"{f['sel']} ({f['estilo']} {f['ancho']}px, {k:.2f}:1)")
            if "btn" in (f["clase"] or "") and f["radio"] != "999px": mal9.append(f"{f['sel']} pierde la píldora con foco ({f['radio']})")
        r.add(9, "FAIL" if mal9 or not vistos else "PASS", f"{v}: " + (", ".join(mal9[:6]) if mal9 else f"{vistos} elementos con foco ≥ 3px y ≥ 3:1"))
    else:
        datos["errores"] = len(errores) + len(malos)
        datos["sin_alt"] = sum(1 for i in m["imgs"] if not (i["alt"] and i["w"] and i["h"]))
        datos["h1"] = sum(1 for x in m["hs"] if x["n"] == 1)
    ctx.close()
    return datos


def reducido(nav, url, w, h, r):
    """10 · con prefers-reduced-motion nada se anima tras el scroll."""
    ctx = nav.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce")
    ctx.add_init_script(JS)
    pg = ctx.new_page(); pg.goto(url, wait_until="load"); pg.wait_for_timeout(800)
    b = pg.evaluate(BAJAR)
    r.add(10, "FAIL" if b["vivas"] else "PASS", f"{w}: " + (("se animan: " + ", ".join(b["vivas"][:6])) if b["vivas"] else "nada se anima con reduced-motion"))
    ctx.close()


def sin_js(nav, url, r):
    """12 · sin JS, todo [data-descarga] queda en /releases/latest."""
    ctx = nav.new_context(java_script_enabled=False); pg = ctx.new_page(); pg.goto(url)
    hrefs = pg.eval_on_selector_all("[data-descarga]", "as => as.map(a => a.getAttribute('href'))")
    mal = [x for x in hrefs if not x.endswith("/releases/latest")]
    r.add(12, "FAIL" if mal or not hrefs else "PASS", ("no van a /releases/latest: " + ", ".join(mal)) if mal else f"{len(hrefs)} botones a /releases/latest sin JS")
    ctx.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", help="URL de la referencia a comparar lado a lado")
    ap.add_argument("--docs", help="otra carpeta a servir en vez de docs/ (para comparar una variante)")
    a = ap.parse_args()
    global DOCS
    if a.docs: DOCS = pathlib.Path(a.docs).resolve()
    r = Res()
    todos = estaticos(r)
    try:  # sin red o sin cuota de la API de GitHub, el punto 11 no puede pasar: queda SKIP, nunca PASS
        st = head(API); r.sin_api = None if st == 200 else f"API de GitHub respondió {st}"
    except Exception as e:
        r.sin_api = f"sin red ({type(e).__name__})"
    reglas, texto_legal = palabras(), legal()
    srv, url = servir(DOCS)
    tabla = {}
    try:
        with sync_playwright() as p:
            nav = p.chromium.launch(channel="msedge")
            for w, h in VISTAS:
                tabla[("Racha", w)] = medir_vista(nav, url, w, h, r, True, reglas, texto_legal)
                reducido(nav, url, w, h, r)
            sin_js(nav, url, r)
            # 11 · HEAD de cada .exe (200 o 302)
            if not r.sin_api:
                for d in sorted({d for d in r.descargas if EXE.search(d)}):
                    try:
                        st = head(d); r.add(11, "PASS" if st in (200, 302) else "FAIL", f"HEAD {d.rsplit('/', 1)[-1]} → {st}")
                    except Exception as e:
                        r.add(11, "SKIP", f"HEAD sin red ({type(e).__name__})")
            if a.ref:
                for w, h in VISTAS:
                    try:
                        tabla[("Ref", w)] = medir_vista(nav, a.ref, w, h, None, False)
                    except Exception as e:
                        tabla[("Ref", w)] = {"bloqueada": f"{type(e).__name__}: {str(e)[:100]}"}
            nav.close()
    finally:
        srv.shutdown()

    # --- Salida: FAIL primero ---
    print(f"preship · {DOCS.name}/index.html · {', '.join(f'{w}×{h}' for w, h in VISTAS)}\n")
    for titulo, cual in (("FAIL", "FAIL"), ("SKIP", "SKIP")):
        filas = [(n, d) for n in range(1, 21) if r.estado(n) == cual for e, d in r.p[n] if e == cual or (cual == "SKIP" and not r.p[n])]
        filas += [(0, d) for e, d in r.extra if e == cual]
        if filas:
            print(titulo)
            for n, d in filas: print(f"  [{n or '-'}] {d}")
            print()
    if todos:
        print("TODO en DESIGN.md (aviso, no falla)")
        for t in todos: print("  " + t)
        print()
    print("PASS")
    for n in range(1, 21):
        if r.estado(n) == "PASS": print(f"  [{n}] " + " · ".join(d for _, d in r.p[n]))
    if a.ref:
        print(f"\nLado a lado con la referencia: {a.ref}")
        print(f"  {'':10}{'LCP ms':>8}{'LCP KB':>8}{'inicial KB':>12}{'CLS':>7}{'scroll-x':>10}")
        for (q, w), d in tabla.items():
            if "bloqueada" in d: print(f"  {q} {w:<5} SKIP: bloqueada ({d['bloqueada']})"); continue
            print(f"  {q} {w:<5}{d['lcp_ms']:>8}{d['lcp_kb']:>8}{d['inicial_kb']:>12}{d['cls']:>7}{'sí' if d['ancho'] > d['vw'] else 'no':>10}"
                  + (f"   errores {d['errores']}, img sin alt/medidas {d['sin_alt']}, h1 {d['h1']}" if q == "Ref" else ""))
    n_pass = sum(r.estado(n) == "PASS" for n in range(1, 21))
    n_fail = sum(r.estado(n) == "FAIL" for n in range(1, 21)) + sum(e == "FAIL" for e, _ in r.extra)
    n_skip = sum(r.estado(n) == "SKIP" for n in range(1, 21))
    print(f"\n{n_pass}/20 PASS · {n_fail} FAIL · {n_skip} SKIP")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
