// Mascota 3D de la portada: el mago vino (sin escudo ni runa) acompaña el scroll por los márgenes y hace una acción por sección.
// La carga el arranque de index.html solo con ≥1400 px, pointer fine, sin reduced-motion y con WebGL2. Dibuja cuando hay scroll
// (un cuadro por rAF como mucho, con 200 ms de suavizado); en reposo no hay bucle. Unidades del dibujo = las del SVG del póster.
import * as THREE from "../vendor/three/0.185.0/three.module.min.js";

const C = {tunica: "#C25A85", gema: "#7A2E52", costura: "#3A1426", piedra: "#E8EEF5", piedraMedia: "#AFC0D2", cuero: "#8A5A30",
  cristal: "#FFE6F0", cristalOscuro: "#A33A63", ojos: "#0B1630", brillo: "#F28DB0", rosa2: "#F8C3D6", fondo: "#24111A", texto: "#FBF2F6"};
const U = 1.8, MEDIO = 41, ALTO = 120, CUERPO = 7;  // px por unidad a escala 1; medio ancho y alto del dibujo; el eje del cuerpo, 7 a la derecha del centro
const POSTER = {lado: "Dh", rotY: -25, s: .75};     // = el SVG del póster (pies a .78 del alto)
const V2 = (x, y) => new THREE.Vector2(x, y), rad = THREE.MathUtils.degToRad;
const clamp = x => Math.min(1, Math.max(0, x)), suave = x => (x = clamp(x), x * x * (3 - 2 * x)), env = u => Math.sin(Math.PI * clamp(u));

// --- Modelo: low-poly procedural; x' = x - 62 e y = 114 - y del SVG ----------------------------------------------------------
const lambert = (color, extra) => new THREE.MeshLambertMaterial({color, flatShading: true, side: THREE.DoubleSide, ...extra});
const aditivo = (color, opacity) => new THREE.MeshBasicMaterial({color, transparent: true, opacity, blending: THREE.AdditiveBlending, premultipliedAlpha: true, depthWrite: false});  // el lienzo es transparente
const malla = (geo, mat, x = 0, y = 0, z = 0, nombre) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); if (nombre) m.name = nombre; return m; };

function modelo() {
  const raiz = new THREE.Group(), tela = lambert(C.tunica), piedra = lambert(C.piedra), cuero = lambert(C.cuero);
  const tunica = new THREE.CylinderGeometry(15, 31, 46, 9, 1, true), pos = tunica.attributes.position;
  for (let i = 0; i < pos.count; i++) if (pos.getY(i) < 0 && (i % 10) % 9 % 2) pos.setY(i, pos.getY(i) + 7);  // borde en zigzag
  raiz.add(malla(tunica, tela, 0, 27, 0));
  raiz.add(malla(new THREE.LatheGeometry([V2(20, 46), V2(23, 60), V2(19, 76), V2(11, 89), V2(3, 96), V2(0, 98)], 7), tela));  // capucha
  const cara = new THREE.Shape([V2(-15, 70), V2(15, 70), V2(17, 54), V2(1, 38), V2(-17, 54)]);
  raiz.add(malla(new THREE.ExtrudeGeometry(cara, {depth: 4, bevelEnabled: false}), piedra, 0, 0, 19));  // máscara
  const ojo = new THREE.ShapeGeometry(new THREE.Shape([V2(-12, 61), V2(-2, 57), V2(-11, 55)]));
  const ojoMat = new THREE.MeshBasicMaterial({color: C.ojos, side: THREE.DoubleSide}), brillo = new THREE.LineBasicMaterial({color: C.brillo});
  for (const k of [1, -1]) {
    const o = malla(ojo, ojoMat, 0, 0, 23.2); o.scale.x = k; raiz.add(o);
    const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-10 * k, 59, 23.4), new THREE.Vector3(-5 * k, 57, 23.4)]), brillo);
    raiz.add(l);
  }
  const placa = malla(new THREE.CylinderGeometry(14, 14, 3, 6), lambert(C.piedraMedia), 0, 26, 22, "placa");  // lisa
  placa.geometry.rotateX(Math.PI / 2); raiz.add(placa);

  const baston = new THREE.Group(); baston.name = "baston"; baston.position.set(-31, 42, 10); raiz.add(baston);
  const palo = malla(new THREE.CylinderGeometry(3, 3, 70, 5), cuero, .5, -6); palo.rotation.z = Math.atan(7 / 68); baston.add(palo);
  baston.add(malla(new THREE.IcosahedronGeometry(5), lambert(C.gema), 2, 6, 3));
  const cristal = new THREE.Group(); cristal.name = "cristal"; cristal.position.set(-3, 58, 0); baston.add(cristal);
  const vidrio = lambert(C.cristal, {emissive: C.cristalOscuro, emissiveIntensity: .35});
  cristal.add(malla(new THREE.LatheGeometry([V2(0, -20), V2(10, -12), V2(12, 10), V2(0, 20)], 6), vidrio));
  const esquirla = new THREE.LatheGeometry([V2(0, -6), V2(2.5, 0), V2(0, 6)], 6);
  cristal.add(malla(esquirla, vidrio, -12, -4, 0)).add(malla(esquirla, vidrio, 14, -5, 0));
  cristal.children[1].rotation.z = .3; cristal.children[2].rotation.z = -.3;
  cristal.add(malla(new THREE.IcosahedronGeometry(16, 1), aditivo(C.brillo, .35), 0, 0, 0, "orbe"));
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
}

// px por unidad: la escala pedida, sin salir del margen (ancho) ni subir a la barra (alto)
const margen = lado => (W - Math.min(W, lado === "Dh" ? 1200 : 960)) / 2 + 24;
const centro = lado => lado === "I" ? margen(lado) / 2 : W - margen(lado) / 2;
const escala = (lado, s) => Math.min(U * s, (margen(lado) / 2 - 8) / MEDIO, (.78 * H - 80) / ALTO);

function aplicar(o, p, esClon) {
  const x0 = centro(p.desde), x1 = centro(p.hasta), u = escala(p.lado, p.s) * p.m, ry = rad(p.rotY);
  let x = x0 + (x1 - x0) * p.k + CUERPO * u, y = .78 * H - p.dy;
  if (p.m < 1) { x += (1 - p.m) * escala(p.lado, p.s) * -34 * Math.cos(ry); y -= (1 - p.m) * escala(p.lado, p.s) * 100; }  // se hunde hacia el cristal
  if (esClon) { x += (p.lado === "I" ? -22 : 22) * u; o.position.z = -60 * u; }
  o.position.x = x; o.position.y = -y; o.scale.setScalar(Math.max(u, 1e-4)); o.rotation.set(0, ry, rad(p.tilt));
  const b = o.getObjectByName("baston"); b.rotation.z = rad(p.baston); b.position.y = 42 + p.bastonY; b.position.z = 10 + p.bastonZ;
  const cr = o.getObjectByName("cristal"); cr.rotation.y = rad(p.cristalRot);
  const orbe = o.getObjectByName("orbe"); orbe.scale.setScalar(Math.max(p.orbe, 1e-4)); orbe.position.x = p.orbeX; orbe.material.opacity = .35 * p.orbeO;
  for (let i = 0; i < 3; i++) { const ch = o.getObjectByName("chico" + i), t = p.giro + i * 2.094;
    ch.position.set(14 * Math.cos(t), 30 + 4 * Math.sin(t * 1.5), 14 * Math.sin(t)); ch.material.opacity = .8 * p.chicos; }
  o.getObjectByName("placa").rotation.z = rad(p.placa);
  const an = o.getObjectByName("anillo"); an.material.opacity = esClon ? 0 : .7 * p.anillo.o; an.scale.setScalar(p.anillo.s);
  if (p.anillo.cristal) { an.position.set(-34, 100 + p.bastonY, 0); an.rotation.set(0, -ry, 0); } else { an.position.set(0, 1, 0); an.rotation.set(-Math.PI / 2 + .3, 0, 0); }
}

const vista = matchMedia("(min-width:1400px) and (pointer:fine)");
function dibujar(y) {
  if (!vista.matches) return;
  const p = pose(y, H);
  aplicar(yo, p, false);
  clon.visible = p.clon > 0; if (clon.visible) { aplicar(clon, p, true); sombra.opacity = p.clon; }
  vidrio.emissiveIntensity = .35 + .9 * p.brillo;
  render.render(mundo, camara);
}

medir();
escena.append(lienzo);
{ const p = pose(0, H, anclas(H));  // la pose de arriba es la del póster
  console.assert(p.lado === POSTER.lado && p.rotY === POSTER.rotY && p.s === POSTER.s && p.dy === 0 && p.baston === 0, "pose(0) != póster", p); }

let objetivo = scrollY, actual = scrollY, raf = 0, previo = 0;
const pedir = () => { if (!raf && !document.hidden) raf = requestAnimationFrame(cuadro); };
function cuadro(t) {
  raf = 0; const dt = previo ? Math.min(t - previo, 100) : 16; previo = t;
  objetivo = scrollY; actual += (objetivo - actual) * (1 - Math.exp(-dt / 60));  // cola de ~200 ms tras el scroll
  if (Math.abs(objetivo - actual) < .5) { actual = objetivo; previo = 0; } else pedir();
  dibujar(actual);
}
addEventListener("scroll", pedir, {passive: true});
addEventListener("resize", () => { medir(); pedir(); dibujar(actual); });
document.addEventListener("visibilitychange", () => { if (document.hidden) { cancelAnimationFrame(raf); raf = 0; previo = 0; } else pedir(); });
dibujar(actual);
document.documentElement.classList.add("escena-lista");  // primer cuadro 3D: el póster se apaga
