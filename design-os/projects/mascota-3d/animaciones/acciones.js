// Animaciones nuevas del minion, con la misma firma que las de docs/js/mascota.js: act(p, u) modifica la pose p, u va de 0 a 1.
// Todas empiezan y terminan en la pose de reposo (los valores de base() en mascota.js), así que se encadenan sin salto:
// después de cualquiera puede ir cualquier otra, y las marcadas "en bucle" se repiten sin costura (u=0 y u=1 dan la misma pose).
// Campos nuevos de p (sus valores de reposo van en base(); su soporte está en aplicar() de lab.js; ver INTEGRAR al final):
//   inclina   grados, cabeceo hacia adelante (+) o atrás (-) del cuerpo entero, pivote en los pies. Reposo 0.
//   sy        escala vertical (squash/stretch) con volumen conservado: x y z se escalan por 1/sqrt(sy). Pivote en los pies. Reposo 1.
//   ojos      brillo de los ojos: 0 = apagados (color ojos), 1 = normal (brillo-ojos), hasta 2 = destello (hacia cristal). Reposo 1.
//   chicosR   radio de la órbita de los 3 orbes chicos (unidades del dibujo). Reposo 14 (= el 14 fijo de aplicar()).
//   chicosY   altura extra de los orbes chicos sobre el cristal. Reposo 0.
// Campos existentes que usan: dy, tilt, rotY (se le suma, como la reacción al mouse), baston, bastonY, bastonZ, brillo, orbe, chicos, giro, cristalRot.

const clamp = x => Math.min(1, Math.max(0, x)), suave = x => (x = clamp(x), x * x * (3 - 2 * x)), env = u => Math.sin(Math.PI * clamp(u));
const tramo = (u, a, b) => clamp((u - a) / (b - a));                               // 0→1 dentro de [a, b]
const suave3 = x => (x = clamp(x), x < .5 ? 4 * x ** 3 : 1 - (-2 * x + 2) ** 3 / 2);  // ease-in-out cúbico: arranque y frenado más marcados
const sobrepasa = (x, s = 1.70158) => (x = clamp(x) - 1, 1 + (s + 1) * x ** 3 + s * x ** 2);  // back-out: pasa de 1 y vuelve
const rebote = (x, f = 2, z = 5) => (x = clamp(x), Math.exp(-z * x) * Math.sin(f * Math.PI * x));  // oscilación amortiguada, 0 en x=0 y ~0 en x=1
const ciclo = u => (1 - Math.cos(2 * Math.PI * u)) / 2;                             // 0→1→0 sin costura, para bucles

// 1. respira · en bucle · 3,2 s. Idle cuando no hay scroll: flota, respira (stretch leve), el bastón y el resplandor van con retraso.
export const respira = (p, u) => {
  const a = 2 * Math.PI * u;
  p.dy = 4 * ciclo(u);                          // flote de 4 px
  p.sy = 1 + .025 * Math.sin(a);                // inhala/exhala
  p.tilt = -1.5 * Math.sin(a);                  // vaivén: se ladea al bajar (un cuarto de ciclo detrás del flote)
  p.baston = 3 * Math.sin(a) ** 3;              // follow-through: el bastón se queda atrás y alcanza tarde
  p.orbe = 1 + .15 * ciclo(u - .1);
  p.brillo = .25 * ciclo(u - .1);
};

// 2. parpadea · 2 s. Mira de reojo, parpadeo doble y los ojos se reencienden con un destello. Para la pausa de lectura (FAQ, "qué es").
export const parpadea = (p, u) => {
  const mira = suave(tramo(u, .05, .25)) - suave(tramo(u, .7, .92));
  p.rotY += 14 * mira + 4 * rebote(tramo(u, .25, .6), 2, 6) - 3 * rebote(tramo(u, .92, 1), 1, 4);  // se pasa un poco y se asienta
  p.tilt = 3 * mira;
  const cierra = (a, b) => env(tramo(u, a, b));
  p.ojos = 1 - Math.max(cierra(.34, .42), cierra(.5, .58)) + .9 * env(tramo(u, .58, .8));
  p.brillo = .5 * env(tramo(u, .58, .85));
  p.dy = 2 * env(tramo(u, .55, .75));
};

// 3. molinete · 2,4 s. Saludo con giro completo del bastón: echa el bastón atrás (anticipación), lo alza y da una vuelta, lo frena con rebote. Hero o despedida.
export const molinete = (p, u) => {
  const g = tramo(u, .14, .72);
  p.baston = u < .14 ? -22 * suave(u / .14) : u < .72 ? -22 + 382 * suave3(g) : 360 + 14 * rebote(tramo(u, .72, 1), 2.5, 4);
  p.bastonY = 30 * suave(tramo(u, .08, .3)) * (1 - suave(tramo(u, .7, .95)));  // lo alza para que el cristal no pase por el suelo
  p.bastonZ = 14 * env(tramo(u, .1, .9));
  p.dy = 6 * env(tramo(u, .1, .3)) - 2 * env(tramo(u, .72, .85));               // salta al soltarlo, se agacha al frenarlo
  p.tilt = -5 * env(tramo(u, 0, .18)) + 6 * Math.sin(2 * Math.PI * g) * env(g);  // el cuerpo sigue al bastón
  p.chicos = env(tramo(u, .2, .8)); p.giro = 6 * Math.PI * u;
  p.brillo = env(tramo(u, .15, .85));
};

// 4. lee · 3,2 s. Se echa atrás, se inclina hacia adelante con el cristal como lámpara y "lee" de lado a lado. Junto a una captura (champ select, tier list).
export const lee = (p, u) => {
  const k = suave(tramo(u, .1, .3)) - suave3(tramo(u, .8, 1));
  p.inclina = -4 * env(tramo(u, 0, .15)) + 14 * k + 3 * rebote(tramo(u, .3, .6), 1.5, 5);
  p.rotY += 22 * k;                                         // gira hacia la captura (en la página: hacia el lado de la imagen)
  p.baston = -18 * k; p.bastonZ = 16 * k; p.bastonY = 6 * k; // acerca la lámpara
  p.orbe = 1 + .7 * k + .08 * Math.sin(10 * Math.PI * u) * k;
  p.brillo = .7 * k;
  p.tilt = 3 * Math.sin(5 * Math.PI * tramo(u, .3, .8)) * k;  // barre la línea con la cabeza
  p.ojos = 1 + .3 * k;
};

// 5. sorpresa · 1,6 s. Reacción al mouse: se agacha, salta estirado, aterriza aplastado y rebota. Sustituye la "reaccion" de poseC().
export const sorpresa = (p, u) => {
  const j = tramo(u, .2, .55), L = tramo(u, .55, 1);
  p.sy = u < .2 ? 1 - .16 * suave(u / .2) : u < .55 ? 1 + .14 * Math.cos(Math.PI * j) : 1 - .14 * Math.exp(-5 * L) * Math.cos(3 * Math.PI * L);
  p.dy = u < .2 ? 0 : 40 * 4 * j * (1 - j);
  p.rotY += 18 * env(tramo(u, .15, .85));
  p.tilt = -4 * env(tramo(u, .2, .55)) + 3 * rebote(L, 2, 5);
  p.baston = 32 * env(tramo(u, .26, .7)) - 8 * rebote(tramo(u, .55, 1), 2, 4);  // el bastón sube tarde y baja tarde
  p.ojos = 1 + env(tramo(u, .15, .6));
  p.brillo = env(tramo(u, .15, .75));
};

// 6. invoca · 3 s. Baja el bastón, alza el cristal que gira dos vueltas y suelta los 3 orbes chicos en espiral. Al terminar / descarga.
export const invoca = (p, u) => {
  const sube = sobrepasa(tramo(u, .14, .42), 2.2) * (1 - suave3(tramo(u, .8, 1)));
  p.bastonY = -7 * env(tramo(u, 0, .16)) + 20 * sube;
  p.dy = -2 * env(tramo(u, 0, .16)) + 5 * sube;
  p.baston = 8 * sube;
  p.cristalRot = -720 * suave3(tramo(u, .14, .82));
  p.brillo = Math.min(1, 1.3 * env(tramo(u, .14, 1)));
  p.orbe = 1 + .6 * sube;
  const s = tramo(u, .45, .95);
  p.chicos = env(tramo(u, .35, .98));
  p.chicosR = 10 + 40 * suave(s);
  p.chicosY = -34 * suave(s);                   // bajan del tope del cristal a su cintura mientras se abren
  p.giro = 8 * Math.PI * suave(tramo(u, .35, 1));
  p.ojos = 1 + .6 * env(tramo(u, .3, .8));
};

export const ACCIONES = {respira, parpadea, molinete, lee, sorpresa, invoca};
export const DURACION = {respira: 3.2, parpadea: 2, molinete: 2.4, lee: 3.2, sorpresa: 1.6, invoca: 3};  // segundos sugeridos por ciclo

/* INTEGRAR en docs/js/mascota.js
1. base() y el literal de pose(): agregar  inclina: 0, sy: 1, ojos: 1, chicosR: 14, chicosY: 0.
2. aplicar(), donde hoy está  o.rotation.set(0, ry, rad(p.tilt))  y  o.scale.setScalar(...):
     o.rotation.set(rad(p.inclina), ry, rad(p.tilt), "YXZ");   // con inclina=0 es idéntico al orden XYZ de ahora
     const k = Math.max(u, 1e-4); o.scale.set(k / Math.sqrt(p.sy), k * p.sy, k / Math.sqrt(p.sy));
3. aplicar(), en el bucle de los chicos: 14 → p.chicosR y 30 → 30 + p.chicosY.
4. ojos: modelo() ya crea un solo material `brillo` para las dos líneas; darle nombre a las líneas (l.name = "brilloOjo") y en dibujar():
     const ojo = yo.getObjectByName("brilloOjo").material;  // compartido por los dos ojos
     p.ojos <= 1 ? ojo.color.set(C.ojos).lerp(new THREE.Color(C.brillo), p.ojos) : ojo.color.set(C.brillo).lerp(new THREE.Color(C.cristal), p.ojos - 1);
   (en el clon las líneas están ocultas, no hace falta nada).
5. molinete termina con p.baston = 360 (= 0 a la vista); si un panel interpola el bastón hacia la pose siguiente, usar p.baston % 360.
6. respira en reposo: hoy el bucle se duerme sin scroll; para el idle haría falta un rAF de baja frecuencia (p. ej. 30 fps) mientras el panel está quieto,
   y cortarlo con document.hidden y reduced-motion. sorpresa puede sustituir el bloque `if (reaccion)` de poseC(): sorpresa(p, k) con k de 0 a 1 en 1600 ms.
*/
