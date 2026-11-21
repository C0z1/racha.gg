// Laboratorio de animaciones: modelo() copiado tal cual de docs/js/mascota.js (líneas 7-78) y aplicar() adaptado a un lienzo de 480×480.
// ?accion=nombre la reproduce en bucle; ?grabar=1 para el bucle y expone window.cuadro(t) (t en s) para capturar cuadro a cuadro.
import * as THREE from "../../../../docs/vendor/three/0.185.0/three.module.min.js";
import {ACCIONES, DURACION} from "./acciones.js";

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
  const anillo = malla(new THREE.RingGeometry(18, 22, 32), aditivo(C.brillo, 0), 0, 0, 0, "anillo"); raiz.add(anillo);
  return raiz;
}

// --- Lienzo propio: misma luz que la página, fondo = colors.fondo
const LADO = 480, ESC = 2.5;  // px por unidad a s = .75 (el póster)
const lienzo = document.querySelector("canvas");
const render = new THREE.WebGLRenderer({canvas: lienzo, antialias: true, preserveDrawingBuffer: true});
render.setPixelRatio(1); render.setSize(LADO, LADO, false); render.setClearColor(C.fondo, 1);
const mundo = new THREE.Scene(), camara = new THREE.OrthographicCamera(0, LADO, 0, -LADO, .1, 4000);
camara.position.z = 2000;
mundo.add(new THREE.HemisphereLight(C.rosa2, C.fondo, 2.2));
const sol = new THREE.DirectionalLight(C.texto, 2.4); sol.position.set(-1, 1.3, 1); mundo.add(sol);
const yo = modelo(); mundo.add(yo);
const vidrio = yo.getObjectByName("cristal").children[0].material;
const ojo = []; yo.traverse(o => { if (o.isLine && o.material.color.getHex() === new THREE.Color(C.brillo).getHex()) ojo.push(o.material); });
const cOjos = new THREE.Color(C.ojos), cBrillo = new THREE.Color(C.brillo), cCristal = new THREE.Color(C.cristal);

const base = o => Object.assign({m: 1, dy: 0, tilt: 0, baston: 0, bastonY: 0, bastonZ: 0, brillo: 0, orbe: 1, orbeX: 0, orbeO: 1, chicos: 0, giro: 0, placa: 0,
  anillo: {o: 0, s: 1}, clon: 0, cristalRot: 0, inclina: 0, sy: 1, ojos: 1, chicosR: 14, chicosY: 0}, o);

// = aplicar() de mascota.js sin carrusel/márgenes/clon; lo nuevo: inclina, sy, ojos, chicosR, chicosY
function aplicar(o, p) {
  const u = ESC * p.s / .75 * p.m, ry = rad(p.rotY), k = Math.max(u, 1e-4);
  o.position.set(LADO / 2 + CUERPO * u, -(LADO * .84 - p.dy), 0);
  o.scale.set(k / Math.sqrt(p.sy), k * p.sy, k / Math.sqrt(p.sy));
  o.rotation.set(rad(p.inclina), ry, rad(p.tilt), "YXZ");
  const b = o.getObjectByName("baston"); b.rotation.z = rad(p.baston); b.position.y = 42 + p.bastonY; b.position.z = 10 + p.bastonZ;
  o.getObjectByName("cristal").rotation.y = rad(p.cristalRot);
  const orbe = o.getObjectByName("orbe"); orbe.scale.setScalar(Math.max(p.orbe, 1e-4) * 46); orbe.position.x = p.orbeX; orbe.material.opacity = .35 * p.orbeO;
  for (let i = 0; i < 3; i++) { const ch = o.getObjectByName("chico" + i), t = p.giro + i * 2.094;
    ch.position.set(p.chicosR * Math.cos(t), 30 + p.chicosY + 4 * Math.sin(t * 1.5), p.chicosR * Math.sin(t)); ch.material.opacity = .8 * p.chicos; }
  o.getObjectByName("placa").rotation.z = rad(p.placa);
  const an = o.getObjectByName("anillo"); an.material.opacity = .7 * p.anillo.o; an.scale.setScalar(p.anillo.s);
  if (p.anillo.cristal) { an.position.set(-34, 100 + p.bastonY, 0); an.rotation.set(0, -ry, 0); } else { an.position.set(0, 1, 0); an.rotation.set(-Math.PI / 2 + .3, 0, 0); }
  vidrio.emissiveIntensity = .35 + .9 * p.brillo;
  const c = p.ojos <= 1 ? cOjos.clone().lerp(cBrillo, clamp(p.ojos)) : cBrillo.clone().lerp(cCristal, clamp(p.ojos - 1));
  ojo.forEach(m => m.color.copy(c));
}

const q = new URLSearchParams(location.search), nombre = q.get("accion") || "respira", act = ACCIONES[nombre], dur = DURACION[nombre];
console.assert(act, "acción desconocida: " + nombre, Object.keys(ACCIONES));
{ const p0 = base({rotY: -25, s: .75}), p1 = base({rotY: -25, s: .75}), r = base({rotY: -25, s: .75}); act(p0, 0); act(p1, 1);  // empieza y termina en reposo
  for (const c of ["dy", "tilt", "rotY", "bastonY", "brillo", "orbe", "sy", "ojos", "chicos", "inclina"])
    console.assert(Math.abs(p0[c] - r[c]) < .05 && Math.abs(p1[c] - r[c]) < .05, nombre + ": " + c + " no vuelve al reposo", p0[c], p1[c]); }
document.title = "lab · " + nombre;
window.cuadro = t => { const p = base({rotY: -25, s: .75}); act(p, (t / dur) % 1); aplicar(yo, p); render.render(mundo, camara); };
window.DUR = dur;
if (!q.has("grabar")) { const t0 = performance.now(); const bucle = t => { window.cuadro((t - t0) / 1000); requestAnimationFrame(bucle); }; requestAnimationFrame(bucle); }
else window.cuadro(0);
