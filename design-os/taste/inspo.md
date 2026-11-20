# Referencias

## Mobalytics: la página de su app de escritorio (referencia a superar)
URL: https://mobalytics.gg/download (redirige a /lol/glp/app-download). Revisada el 2026-11-20.

Qué se toma (el patrón, no la forma):
- Botón de descarga fijo en la barra, siempre a mano.
- La confianza pegada al botón (ellos: «Mobalytics is Riot Approved»; nosotros: la lista aprobada por el usuario).
- Funciones ordenadas por antes, durante y después de la partida.
- 3 pasos: descarga, instala y la app aparece sola.
- UI real grande a la derecha del hero.
- «¿Me pueden banear?» respondido con enlace a la postura de Riot (nosotros: a `docs/CUMPLIMIENTO.md`).

Qué no se toma:
- Su violeta, su amarillo ni su tipografía condensada.
- Splash art de campeones.
- Contadores de usuarios o partidas.
- Videos que se reproducen solos.
- Sello de aprobación de Riot.

Dónde gana Racha:
- Cifras propias del jugador («con 2 muertes o menos del 14 al 25 ganas el 65 %, con 3 o más, el 44 %»).
- Instalador de 16 MB, sin Overwolf, sin anuncios.
- Una página más liviana y más accesible. Se mide con `checks/preship.py --ref`, no se presume.

## La mascota: el minion vino (referencia del personaje)
Fuente: `racha.gg/.equipo/diseno/canvas/project/Minions_Variantes.dc.html`, tercer SVG («Vino»). Revisada el 2026-11-20.

Qué se toma:
- La silueta: túnica con borde en zigzag, capucha alta, máscara de piedra con ojos, placa hexagonal, bastón de cuero con cristal y orbe.
- La paleta vino (clave `mascota` de DESIGN.md) y el cristal rosa.
- La pose de frente como póster.

Qué no se toma:
- El escudo de piedra ni las runas (de Order): placa lisa (decisión del usuario).
- La elipse de sombra bajo los pies y el drop-shadow cian.
- Las animaciones CSS del lienzo (respira, partículas): la mascota solo se mueve con el scroll.
- El nombre: en la página es «mascota».

## Otras vistas (solo patrones; ver racha.gg/.equipo/diseno/portada-propuesta.md)
- Blitz: botón en la barra y en el hero, prueba social en números (Racha no la tiene y no la inventa).
- U.GG: «¿No baja? Haz clic aquí» como respaldo del botón.
