// Mascota 3D de la portada: el mago vino (sin escudo ni runa). En el carrusel (≥1400 px y ≥760 de alto) se queda al centro y la página gira
// a su alrededor; si no, acompaña el scroll por los márgenes. En los dos casos hace una acción por sección.
// La carga el arranque de index.html solo con ≥1400 px, pointer fine, sin reduced-motion y con WebGL2. Dibuja cuando hay scroll
// (un cuadro por rAF como mucho, con 200 ms de suavizado); en reposo no hay bucle. Unidades del dibujo = las del SVG del póster.
import * as THREE from "../vendor/three/0.185.0/three.module.min.js";

const C = {tunica: "#C25A85", tunicaOscura: "#5E2440", gema: "#7A2E52", costura: "#3A1426", piedra: "#E8EEF5", piedraMedia: "#AFC0D2", piedraOscura: "#6F8296",
  cuero: "#8A5A30", cueroClaro: "#C98E5A", cueroOscuro: "#5E3A1C",
  cristal: "#FFE6F0", cristalOscuro: "#A33A63", ojos: "#0B1630", brillo: "#F28DB0", rosa2: "#F8C3D6", fondo: "#24111A", texto: "#FBF2F6"};
const U = 1.8, MEDIO = 41, ALTO = 120, CUERPO = 7;  // px por unidad a escala 1; medio ancho y alto del dibujo; el eje del cuerpo, 7 a la derecha del centro
const POSTER = {lado: "Dh", rotY: -25, s: .75};     // = el SVG del póster (pies a .78 del alto)
const V2 = (x, y) => new THREE.Vector2(x, y), rad = THREE.MathUtils.degToRad;
const clamp = x => Math.min(1, Math.max(0, x)), suave = x => (x = clamp(x), x * x * (3 - 2 * x)), env = u => Math.sin(Math.PI * clamp(u));

// --- Modelo: low-poly procedural; x' = x - 62 e y = 114 - y del SVG ----------------------------------------------------------
const lambert = (color, extra) => new THREE.MeshLambertMaterial({color, flatShading: true, side: THREE.DoubleSide, ...extra});
// luz que suma color sin tocar el alfa del lienzo transparente (si sumara alfa, el brillo se vería como un disco opaco sobre la página)
const SUMA = {transparent: true, depthWrite: false, premultipliedAlpha: true, blending: THREE.CustomBlending,
  blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor, blendSrcAlpha: THREE.ZeroFactor, blendDstAlpha: THREE.OneFactor};
const aditivo = (color, opacity) => new THREE.MeshBasicMaterial({color, opacity, ...SUMA});
const RESPLANDOR = (() => { const c = document.createElement("canvas"); c.width = c.height = 64; const g = c.getContext("2d"), r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  r.addColorStop(0, "rgb(255,255,255)"); r.addColorStop(.45, "rgb(110,110,110)"); r.addColorStop(1, "rgb(0,0,0)");  // la caída va en el color: al sumar, negro = nada
  g.fillStyle = r; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
const malla = (geo, mat, x = 0, y = 0, z = 0, nombre) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); if (nombre) m.name = nombre; return m; };

// Degradado de la tela como en el póster (tunica arriba, tunica-oscura abajo): color por vértice según la altura
function degradado(geo, y0, y1, arriba = C.tunica, abajo = C.tunicaOscura) {
  const p = geo.attributes.position, a = new THREE.Color(arriba), b = new THREE.Color(abajo), c = new THREE.Color(), col = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) { c.copy(b).lerp(a, clamp((p.getY(i) - y0) / (y1 - y0))); col.set([c.r, c.g, c.b], i * 3); }
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3)); return geo;
}

function modelo() {
  const raiz = new THREE.Group(), tela = lambert(C.piedra, {vertexColors: true}), piedra = lambert(C.piedra), cuero = lambert(C.cuero);
  tela.color.setRGB(1, 1, 1);  // el color va en los vértices
  const tunica = new THREE.CylinderGeometry(15, 31, 46, 9, 4, true), pos = tunica.attributes.position;
  for (let i = 0; i < pos.count; i++) if (pos.getY(i) < -22.9 && (i % 10) % 9 % 2) pos.setY(i, pos.getY(i) + 7);  // borde en zigzag (fila de abajo)
  raiz.add(malla(degradado(tunica, -23, 23, C.tunica, C.tunicaOscura), tela, 0, 27, 0));
  raiz.add(malla(degradado(new THREE.LatheGeometry([V2(20, 46), V2(23, 60), V2(19, 76), V2(11, 89), V2(3, 96), V2(0, 98)], 8), 46, 98, C.tunica, C.tunicaOscura), tela));  // capucha
  // collar de cuero sobre los hombros y costuras en X de la capucha (del póster)
  raiz.add(malla(new THREE.CylinderGeometry(21, 27, 8, 10, 1, true), lambert(C.cueroClaro), 0, 47, 0));
  const hilo = lambert(C.costura);
  for (const [x, y] of [[-10, 79], [10, 83]]) {
    const z = Math.sqrt(Math.max(0, 18.5 ** 2 - x * x)) + .6, x0 = new THREE.Group(); x0.position.set(x, y, z); x0.rotation.y = Math.atan2(x, z);
    for (const a of [.8, -.8]) { const b = new THREE.Mesh(new THREE.BoxGeometry(6, 1.3, 1), hilo); b.rotation.z = a; x0.add(b); }
    raiz.add(x0);
  }
  const cara = new THREE.Shape([V2(-15, 70), V2(15, 70), V2(17, 54), V2(1, 38), V2(-17, 54)]);
  raiz.add(malla(new THREE.ExtrudeGeometry(cara, {depth: 3, bevelEnabled: true, bevelThickness: 1, bevelSize: 1, bevelSegments: 1}), piedra, 0, 0, 19));  // máscara
  raiz.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 69, 24.2), new THREE.Vector3(-2, 64, 24.2), new THREE.Vector3(1, 61, 24.2)]),
    new THREE.LineBasicMaterial({color: C.piedraOscura})));  // grieta de la máscara
  const ojo = new THREE.ShapeGeometry(new THREE.Shape([V2(-12, 61), V2(-2, 57), V2(-11, 55)]));
  const ojoMat = new THREE.MeshBasicMaterial({color: C.ojos, side: THREE.DoubleSide}), brillo = new THREE.LineBasicMaterial({color: C.brillo});
  for (const k of [1, -1]) {
    const o = malla(ojo, ojoMat, 0, 0, 23.2); o.scale.x = k; raiz.add(o);
    const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-10 * k, 59, 23.4), new THREE.Vector3(-5 * k, 57, 23.4)]), brillo);
    raiz.add(l);
  }
  const placa = malla(new THREE.CylinderGeometry(14, 13, 3.5, 6), lambert(C.piedraMedia), 0, 26, 22, "placa");  // lisa, con el borde biselado
  placa.geometry.rotateX(Math.PI / 2); raiz.add(placa);

  const baston = new THREE.Group(); baston.name = "baston"; baston.position.set(-31, 42, 10); raiz.add(baston);
  const palo = malla(new THREE.CylinderGeometry(3, 3, 70, 5), cuero, .5, -6); palo.rotation.z = Math.atan(7 / 68); baston.add(palo);
  for (const t of [-.14, -.02, .1]) { const a = malla(new THREE.CylinderGeometry(3.6, 3.6, 1.8, 5), lambert(C.cueroOscuro), 0, t * 70, 0); palo.add(a); }  // amarres de cuero
  baston.add(malla(new THREE.IcosahedronGeometry(5), lambert(C.gema), 2, 6, 3));
  const cristal = new THREE.Group(); cristal.name = "cristal"; cristal.position.set(-3, 58, 0); baston.add(cristal);
  const vidrio = lambert(C.cristal, {emissive: C.cristalOscuro, emissiveIntensity: .35});
  cristal.add(malla(new THREE.LatheGeometry([V2(0, -20), V2(10, -12), V2(12, 10), V2(0, 20)], 6), vidrio));
  const esquirla = new THREE.LatheGeometry([V2(0, -6), V2(2.5, 0), V2(0, 6)], 6);
  cristal.add(malla(esquirla, vidrio, -12, -4, 0)).add(malla(esquirla, vidrio, 14, -5, 0));
  cristal.children[1].rotation.z = .3; cristal.children[2].rotation.z = -.3;
  const orbe = new THREE.Sprite(new THREE.SpriteMaterial({map: RESPLANDOR, color: C.brillo, opacity: .35, ...SUMA}));  // resplandor suave, como el radialGradient del póster
  orbe.name = "orbe"; cristal.add(orbe);
  const chico = new THREE.IcosahedronGeometry(3);
  for (let i = 0; i < 3; i++) cristal.add(malla(chico, aditivo(C.brillo, 0), 0, 0, 0, "chico" + i));
  const anillo = malla(new THREE.RingGeometry(18, 22, 9), aditivo(C.brillo, 0), 0, 0, 0, "anillo"); raiz.add(anillo);
  return raiz;
}

// --- Guion: cada clave se ancla a un selector; la acción corre en el 70 % de su tramo y el 30 % final lleva a la siguiente pose
const q = (s, i = 0) => () => document.querySelectorAll(s)[i];
const saluda = (p, u) => { p.baston = 15 * Math.sin(4 * Math.PI * u); p.brillo = env(u); };
const camina = (p, u) => { p.dy = 6 * Math.abs(Math.sin(3 * Math.PI * u)); p.tilt = 4 * Math.sin(3 * Math.PI * u); p.brillo = Math.sin(3 * Math.PI * u) ** 2; };
const orbeCrece = (p, u) => { p.orbe = 1 + 1.3 * env(u); };
const apunta = (p, u) => { p.baston = 35 * env(u); p.chicos = env(u); p.giro = u * 4 * Math.PI; };
const golpe = (p, u) => { const k = clamp((u - .35) / .5); p.bastonY = -8 * env(u / .35); p.anillo = {o: env(k), s: 1 + 2 * k}; p.placa = 60 * suave((u - .35) / .2); };
const hundirse = (p, u, sig) => { p.m = u < .5 ? 1 - suave(u * 2) : suave(u * 2 - 1); p.brillo = 1;
  if (u >= .5) Object.assign(p, {lado: sig.lado, rotY: sig.rotY, s: sig.s}); };
const corre = (p, u) => { camina(p, (u * 8 / 3) % 1); p.clon = .6 * suave(u / .15) * (1 - suave((u - .75) / .25)); };
const giraCristal = (p, u) => { p.cristalRot = -360 * u; };
const dispara = (p, u) => { p.orbeX = -220 * suave(u / .6); p.orbe = u < .8 ? 1 : suave((u - .8) / .2); p.orbeO = u < .6 ? 1 : u < .8 ? 1 - suave((u - .6) / .2) : 1; };
const guardia = (p, u) => { p.baston = -48 * env(u); p.bastonZ = 14 * env(u); };
const celebra = (p, u) => { p.dy = 24 * env(u / .5); const k = clamp((u - .3) / .6); p.anillo = {o: env(k), s: .6 + 1.4 * k, cristal: true}; p.brillo = env(u); };
const GUION = [
  {el: null, ...POSTER},                                                 // 0 hero arriba = póster
  {el: q(".hero"), at: .7, ...POSTER, act: saluda},                       // 1 hero salida: saluda
  {el: q('[aria-labelledby="t-pasos"]'), lado: "D", rotY: -90, s: .85, act: camina},  // 2 tres pasos
  {el: q(".que-es"), lado: "D", rotY: -60, s: .85, act: orbeCrece},     // 3 qué es: mira a las tarjetas
  {el: q(".fila", 0), lado: "D", rotY: -40, s: .9, act: apunta},       // 4 champ select
  {el: q(".fila", 1), lado: "D", rotY: -25, s: .9, act: golpe},        // 5 runas
  {el: q(".fila", 2), at: -.15, lado: "D", rotY: -25, s: .9, act: hundirse},  // 6 D→I
  {el: q(".fila", 2), at: .2, lado: "I", rotY: 90, s: .9, act: corre}, // 7 Sombra, con el clon
  {el: q(".fila", 3), lado: "I", rotY: 35, s: .9, act: giraCristal},   // 8 al terminar
  {el: q(".fila", 4), at: -.15, lado: "I", rotY: 35, s: .9, act: hundirse},   // 9 I→D
  {el: q(".fila", 4), at: .15, lado: "D", rotY: -40, s: .9, act: dispara},   // 10 tier list
  {el: q(".faq"), at: -.3, lado: "D", rotY: -15, s: .9, act: guardia},          // 11 FAQ
  {el: q(".descarga"), lado: "D", rotY: 0, s: 1.1, act: celebra},      // 12 descarga
];

// --- Carrusel (html.con-carrusel): la página es un anillo de paneles y la mascota se queda al centro, en el hueco del panel del frente.
// Cada panel ocupa 100vh de scroll: en el 70 % quieto hace su acción; en el 30 % de giro se voltea hacia el panel que entra por la derecha.
const CARRUSEL = document.documentElement.classList.contains("con-carrusel");
let UC = 190 / 82, X0C = 0, PIESC = 0;  // carrusel: px por unidad, centro del dibujo y pies, medidos del póster SVG (el CSS manda el tamaño)
const disparaC = (p, u) => { dispara(p, u); p.orbeX *= -.5; };  // dispara hacia la imagen (derecha), nunca sobre el texto
const GUION_C = [
  {rotY: -25, s: .75, act: saluda, fx: "chispas"},      // hero (= póster)
  {rotY: -60, s: .75, act: camina, fx: "polvo"},      // en tres pasos
  {rotY: 0, s: .75, act: orbeCrece, fx: "chispas"},     // qué es
  {rotY: 30, s: .75, act: apunta, fx: "chispas"},       // champ select: apunta a la captura
  {rotY: -25, s: .75, act: golpe, fx: "polvo"},       // runas
  {rotY: 90, s: .75, act: corre, fx: "polvo"},        // sombra: corre con su clon
  {rotY: -35, s: .75, act: giraCristal, fx: "chispas"}, // al terminar
  {rotY: 40, s: .75, act: disparaC, fx: "chispas"},     // tier list
  {rotY: 0, s: .75, act: guardia},       // FAQ
  {rotY: 0, s: .82, act: celebra, fx: "confeti"},       // descarga
];
const base = o => Object.assign({m: 1, dy: 0, tilt: 0, baston: 0, bastonY: 0, bastonZ: 0, brillo: 0, orbe: 1, orbeX: 0, orbeO: 1, chicos: 0, giro: 0, placa: 0,
  anillo: {o: 0, s: 1}, clon: 0, cristalRot: 0}, o);
function poseC(y) {
  const car = document.querySelector(".carrusel"), n = GUION_C.length, r = Math.max(0, (y - car.offsetTop) / innerHeight);
  const i = Math.min(Math.floor(r), n - 1), f = i === n - 1 ? Math.min(r - i, .7) : r - i, g = GUION_C[i], sig = GUION_C[Math.min(i + 1, n - 1)];
  const t = suave((f - .7) / .3);
  const p = base({lado: "C", desde: "C", hasta: "C", k: 0, rotY: g.rotY + (sig.rotY - g.rotY) * t + 50 * env(t), s: g.s + (sig.s - g.s) * t});
  g.act(p, clamp(f / .7), sig);
  p.m = 1 - suave(env(t) * 1.6);  // en el giro se hunde en su cristal: el texto que pasa por el centro nunca queda detrás de él
  p.panel = i; p.f = f;
  if (reaccion) { const k = clamp((performance.now() - reaccion.t0) / 900);  // reacción al mouse, sumada a la pose
    p.dy += 16 * env(k); p.rotY += 20 * reaccion.dir * env(k); p.brillo = Math.max(p.brillo, env(k)); if (k >= 1) reaccion = null; }
  return p;
}

// Centro de la vista (scrollY + alto/2) de cada clave, creciente y sin pasar del máximo alcanzable
function anclas(H) {
  const fin = document.documentElement.scrollHeight - H / 2, a = GUION.map(g => {
    if (!g.el) return H / 2; const r = g.el().getBoundingClientRect(); return r.top + scrollY + (g.at || 0) * r.height; });
  a[a.length - 1] = Math.min(a[a.length - 1], fin - H * .3);
  for (let i = a.length - 2; i >= 0; i--) a[i] = Math.min(a[i], a[i + 1] - 40);
  a[0] = H / 2; for (let i = 1; i < a.length; i++) a[i] = Math.max(a[i], a[i - 1] + 1);
  a.push(Math.max(fin, a[a.length - 1] + 1));
  return a;
}

function pose(y, H, a = anclas(H)) {
  const c = y + H / 2; let i = 0; while (i < GUION.length - 1 && c >= a[i + 1]) i++;
  const g = GUION[i], sig = GUION[i + 1] || g, u = clamp((c - a[i]) / (a[i + 1] - a[i]));
  const k = g.lado === sig.lado ? suave((u - .7) / .3) : 0;  // si cambia de lado, lo hace la acción (escala a 0), nunca cruzando el texto
  const p = {lado: k < .5 ? g.lado : sig.lado, desde: g.lado, hasta: sig.lado, k, rotY: g.rotY + (sig.rotY - g.rotY) * k, s: g.s + (sig.s - g.s) * k,
    m: 1, dy: 0, tilt: 0, baston: 0, bastonY: 0, bastonZ: 0, brillo: 0, orbe: 1, orbeX: 0, orbeO: 1, chicos: 0, giro: 0, placa: 0,
    anillo: {o: 0, s: 1}, clon: 0, cristalRot: 0};
  if (g.act) g.act(p, g.act === hundirse ? u : clamp(u / .7), sig);
  if (g.act === hundirse) p.desde = p.hasta = p.lado, p.k = 0;
  return p;
}

// --- Escena ---------------------------------------------------------------------------------------------------------------
const escena = document.querySelector(".escena"), lienzo = document.createElement("canvas");
const render = new THREE.WebGLRenderer({canvas: lienzo, alpha: true, antialias: true});
const mundo = new THREE.Scene(), camara = new THREE.OrthographicCamera(0, 1, 0, -1, .1, 4000);
camara.position.z = 2000;
mundo.add(new THREE.HemisphereLight(C.rosa2, C.fondo, 2.2));
const sol = new THREE.DirectionalLight(C.texto, 2.4); sol.position.set(-1, 1.3, 1); mundo.add(sol);
const yo = modelo(), clon = yo.clone(true), sombra = new THREE.MeshBasicMaterial({color: C.costura, transparent: true, opacity: .6, depthWrite: false});
clon.traverse(o => { if (o.isLine) o.visible = false; else if (o.material) o.material = o.name === "orbe" || o.name === "anillo" || o.name.startsWith("chico") ? o.material.clone() : sombra; });
clon.getObjectByName("orbe").visible = false;
mundo.add(clon, yo);
const vidrio = yo.getObjectByName("cristal").children[0].material;

let W = 0, H = 0;
function medir() {
  W = document.documentElement.clientWidth; H = innerHeight;
  render.setPixelRatio(Math.min(devicePixelRatio, 2)); render.setSize(W, H, false);
  Object.assign(camara, {right: W, bottom: -H}); camara.updateProjectionMatrix();
  if (CARRUSEL) {  // el póster sigue maquetado aunque esté apagado: de él salen tamaño y lugar en cualquier escalón de CSS
    const r = escena.querySelector("svg").getBoundingClientRect(), e = escena.getBoundingClientRect();
    UC = r.width / 82; X0C = r.left - e.left + MEDIO * UC; PIESC = r.bottom - e.top;
  }
}

// px por unidad: la escala pedida, sin salir del margen (ancho) ni subir a la barra (alto)
const margen = lado => (W - Math.min(W, lado === "Dh" ? 1200 : 960)) / 2 + 24;
const centro = lado => lado === "I" ? margen(lado) / 2 : W - margen(lado) / 2;
const escala = (lado, s) => Math.min(U * s, (margen(lado) / 2 - 8) / MEDIO, (.78 * H - 80) / ALTO);

function aplicar(o, p, esClon) {
  const x0 = CARRUSEL ? X0C : centro(p.desde), x1 = CARRUSEL ? x0 : centro(p.hasta);
  const u = (CARRUSEL ? UC * p.s / POSTER.s : escala(p.lado, p.s)) * p.m, ry = rad(p.rotY);
  let x = x0 + (x1 - x0) * p.k + CUERPO * u, y = (CARRUSEL ? PIESC : .78 * H) - p.dy;  // carrusel: pies donde los del póster
  if (p.m < 1) { const u0 = CARRUSEL ? UC * p.s / POSTER.s : escala(p.lado, p.s); x += (1 - p.m) * u0 * -34 * Math.cos(ry); y -= (1 - p.m) * u0 * 100; }  // se hunde hacia el cristal
  if (esClon) { x += (p.lado === "I" ? -22 : 22) * u; o.position.z = -60 * u; }
  o.position.x = x; o.position.y = -y; o.scale.setScalar(Math.max(u, 1e-4)); o.rotation.set(0, ry, rad(p.tilt));
  const b = o.getObjectByName("baston"); b.rotation.z = rad(p.baston); b.position.y = 42 + p.bastonY; b.position.z = 10 + p.bastonZ;
  const cr = o.getObjectByName("cristal"); cr.rotation.y = rad(p.cristalRot);
  const orbe = o.getObjectByName("orbe"); orbe.scale.setScalar(Math.max(p.orbe, 1e-4) * 46);  // sprite: 46 unidades de diámetro = el orbe de 16 de radio con su halo orbe.position.x = p.orbeX; orbe.material.opacity = .35 * p.orbeO;
  for (let i = 0; i < 3; i++) { const ch = o.getObjectByName("chico" + i), t = p.giro + i * 2.094;
    ch.position.set(14 * Math.cos(t), 30 + 4 * Math.sin(t * 1.5), 14 * Math.sin(t)); ch.material.opacity = .8 * p.chicos; }
  o.getObjectByName("placa").rotation.z = rad(p.placa);
  const an = o.getObjectByName("anillo"); an.material.opacity = esClon ? 0 : .7 * p.anillo.o; an.scale.setScalar(p.anillo.s);
  if (p.anillo.cristal) { an.position.set(-34, 100 + p.bastonY, 0); an.rotation.set(0, -ry, 0); } else { an.position.set(0, 1, 0); an.rotation.set(-Math.PI / 2 + .3, 0, 0); }
}

const vista = matchMedia("(min-width:1400px) and (pointer:fine)"), activa = () => CARRUSEL || vista.matches;
// --- Partículas (carrusel): un solo Points que suma luz; una ráfaga al empezar la acción de cada panel; unidades = px de pantalla
const NP = 300, pp = new Float32Array(NP * 3).fill(-9999), pc = new Float32Array(NP * 3), pv = new Float32Array(NP * 3), pb = new Float32Array(NP * 3);
const pvida = new Float32Array(NP), pdura = new Float32Array(NP), pgrav = new Float32Array(NP);
const geoP = new THREE.BufferGeometry();
geoP.setAttribute("position", new THREE.BufferAttribute(pp, 3).setUsage(THREE.DynamicDrawUsage));
geoP.setAttribute("color", new THREE.BufferAttribute(pc, 3).setUsage(THREE.DynamicDrawUsage));
const puntos = new THREE.Points(geoP, new THREE.PointsMaterial({size: 9, sizeAttenuation: false, map: RESPLANDOR, vertexColors: true, ...SUMA}));
puntos.frustumCulled = false; mundo.add(puntos);
let pcur = 0, vivas = 0, reaccion = null, enfriado = 0;
const disparadas = new Set();
function emitir(n, x, y, f) {  // f(i) -> [vx, vy, color, duración s, gravedad]
  const c = new THREE.Color();
  vivas = Math.max(vivas, n);  // que el bucle no se duerma justo después de emitir
  for (let i = 0; i < n; i++) { const j = pcur; pcur = (pcur + 1) % NP; const [vx, vy, col, d, g] = f(i); c.set(col);
    pp.set([x, y, 10], j * 3); pv.set([vx, vy, 0], j * 3); pb.set([c.r, c.g, c.b], j * 3); pvida[j] = pdura[j] = d; pgrav[j] = g || 0; }
}
const azar = (a, b) => a + Math.random() * (b - a);
const FX = {
  chispas: (x, y, u) => emitir(26, x, y, i => { const a = azar(0, 6.283), v = azar(40, 140) * u / 2; return [Math.cos(a) * v, Math.sin(a) * v, i % 3 ? C.brillo : C.cristal, azar(.5, .9)]; }),
  polvo: (x, y, u) => emitir(22, x, y, i => [azar(-90, 90) * u / 2, azar(10, 60) * u / 2, i % 2 ? C.rosa2 : C.cristal, azar(.4, .7), -60]),
  confeti: (x, y, u) => emitir(90, x, y, i => [azar(-160, 160) * u / 2, azar(120, 300) * u / 2, [C.brillo, C.rosa2, C.cristal][i % 3], azar(1, 1.6), -260 * u / 2]),
};
function moverParticulas(dt) {
  vivas = 0;
  for (let j = 0; j < NP; j++) { const b = j * 3;
    if (pvida[j] <= 0) { if (pc[b] || pc[b + 1] || pc[b + 2]) pc.fill(0, b, b + 3); continue; }
    vivas++; pvida[j] -= dt; const k = Math.max(0, pvida[j] / pdura[j]);
    pv[b + 1] += pgrav[j] * dt; pp[b] += pv[b] * dt; pp[b + 1] += pv[b + 1] * dt;
    for (let e = 0; e < 3; e++) pc[b + e] = pb[b + e] * k * 1.4;
  }
  geoP.attributes.position.needsUpdate = geoP.attributes.color.needsUpdate = true;
}
const cristalEn = v => yo.getObjectByName("cristal").getWorldPosition(v);
function fxPanel(p) {  // una ráfaga al empezar la acción del panel; se rearma al alejarse 2 paneles
  disparadas.forEach(i => { if (Math.abs(i - p.panel) >= 2) disparadas.delete(i); });
  const g = GUION_C[p.panel]; if (!g.fx || disparadas.has(p.panel) || p.f < .05 || p.f > .7) return;
  disparadas.add(p.panel); const u = UC * p.s / POSTER.s;
  if (g.fx === "chispas") { const v = cristalEn(new THREE.Vector3()); FX.chispas(v.x, v.y, u); }
  else FX[g.fx](X0C + CUERPO * u, -PIESC, u);
}

function dibujar(y) {
  if (!activa()) return;
  const p = CARRUSEL ? poseC(y) : pose(y, H);
  aplicar(yo, p, false);
  clon.visible = p.clon > 0; if (clon.visible) { aplicar(clon, p, true); sombra.opacity = p.clon; }
  vidrio.emissiveIntensity = .35 + .9 * p.brillo;
  if (CARRUSEL) { yo.updateMatrixWorld(true); fxPanel(p); }
  render.render(mundo, camara);
}

medir();
escena.append(lienzo);
{ const p = CARRUSEL ? poseC(0) : pose(0, H, anclas(H));  // la pose de arriba es la del póster
  console.assert((CARRUSEL || p.lado === POSTER.lado) && p.rotY === POSTER.rotY && p.s === POSTER.s && p.dy === 0 && p.baston === 0, "pose(0) != póster", p); }

let objetivo = scrollY, actual = scrollY, raf = 0, previo = 0;
const pedir = () => { if (!raf && !document.hidden) raf = requestAnimationFrame(cuadro); };
function cuadro(t) {
  raf = 0; const dt = previo ? Math.min(t - previo, 100) : 16; previo = t;
  objetivo = scrollY; actual += (objetivo - actual) * (1 - Math.exp(-dt / 60));  // cola de ~200 ms tras el scroll
  const quieto = Math.abs(objetivo - actual) < .5; if (quieto) actual = objetivo;
  if (CARRUSEL) moverParticulas(dt / 1000);
  dibujar(actual);
  if (!quieto || vivas || reaccion) pedir(); else previo = 0;  // sin scroll, partículas ni reacción, el bucle se duerme
}
addEventListener("scroll", pedir, {passive: true});
// Carrusel: si el mouse pasa sobre la cabeza con el panel quieto, salta y voltea hacia él (una vez cada 3 s)
if (CARRUSEL) addEventListener("pointermove", e => {
  if (e.pointerType !== "mouse" || reaccion || performance.now() < enfriado) return;
  const pz = poseC(actual); if (pz.f > .7) return;
  const u = UC * pz.s / POSTER.s, rc = lienzo.getBoundingClientRect(), hx = rc.left + X0C + CUERPO * u, hy = rc.top + PIESC - 70 * u;
  if (Math.hypot(e.clientX - hx, e.clientY - hy) > 40 * u) return;
  reaccion = {t0: performance.now(), dir: e.clientX < hx ? -1 : 1}; enfriado = reaccion.t0 + 3000;
  const v = cristalEn(new THREE.Vector3()); FX.chispas(v.x, v.y, u * .6); pedir();
}, {passive: true});
addEventListener("resize", () => { medir(); pedir(); dibujar(actual); });
document.addEventListener("visibilitychange", () => { if (document.hidden) { cancelAnimationFrame(raf); raf = 0; previo = 0; } else pedir(); });
dibujar(actual);
document.documentElement.classList.add("escena-lista");  // primer cuadro 3D: el póster se apaga
