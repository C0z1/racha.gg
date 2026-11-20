# Brief: mascota 3D de la portada (docs/index.html)

- **Meta:** que la portada se sienta propia sin costarle nada a quien solo quiere el `.exe`. En PC grande, la mascota (el mago vino sin escudo) acompaña el scroll en los márgenes y hace una acción por sección; en el resto, nada cambia salvo que en celular el botón principal es «Enviarme el enlace».
- **Referencia:** el minion vino de `racha.gg/.equipo/diseno/canvas/project/Minions_Variantes.dc.html` (tercer SVG). Ver `taste/inspo.md`. El plan completo: `racha.gg/.equipo/diseno/mascota-3d-plan.md` (Fable, revisado por DeepSeek, decisiones del usuario del 20-nov-2026).
- **Vara** (de `rules/bar.md`):
  - 20/20 en web-20, con el punto 10 (reduced-motion: ni canvas ni request a /vendor/three) y el 14 (hex del SVG y de docs/js contra `colors` ∪ `mascota`) ampliados;
  - carga inicial y LCP sin cambios salvo ~6 KB (póster inline, CSS y arranque); three solo ≥1400 px, pointer fine, sin reduced-motion y con WebGL2;
  - CLS < 0.05 con la mascota en pantalla;
  - botón y confianza sin scroll a 390×844, también con pantalla táctil;
  - cero hex fuera de `colors` y `mascota`; DESIGN.md < 250 líneas y con sus 10 secciones.
- **Fijo:** el JS del botón de descarga; el script de tarjetas salvo la línea de `LUGARES`; la mascota nunca cruza texto (cambia de lado escalando a 0); máximo 3 cosas en movimiento (la mascota cuenta como 1).
- **Resumen de lo leído (6 líneas):**
  1. DESIGN.md manda: vino y rosa, plano, 11 tokens; un choque se reporta, no se decide.
  2. Solo se anima transform/opacity con la curva de la casa; nada con reduced-motion. La mascota será la única excepción, escrita en DESIGN.md.
  3. Una sola sombra (la tarjeta al elevarse): la luz y el flat shading de la mascota son del dibujo; sin elipse ni sombra proyectada.
  4. Sin emojis, sin íconos ni colores inventados; los del personaje van en la clave `mascota:` del YAML.
  5. Correcciones vigentes: la lista de confianza, el logo es el mago (ahora sin escudo), las curvas y el foco de 2px.
  6. preship en 20/20 a 390 y 1440; el botón de descarga y su JS no se tocan.
