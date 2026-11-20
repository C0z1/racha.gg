---
version: 1
name: Racha
description: Coach gratis de League of Legends para Windows, hecho con tus propias partidas. Vino y rosa, plano, datos con su base.
colors:
  fondo: "#24111A"        # docs/index.html :root --fondo; meta theme-color
  fondo2: "#2E1622"       # tarjetas, details
  borde: "#4A2436"        # bordes de 1px, solo decorativo
  rosa: "#F28DB0"         # EL acento: botón, marca, viñetas, foco (= app --acc = franja ROSA)
  sombra: "#000000"       # solo la sombra de la tarjeta al pasar el mouse, al 25 % (usuario, 20-nov-2026)
  rosa2: "#F8C3D6"        # tinte del acento: enlaces, h2, hover del botón (= app --acc2, overlay.py L11 ROSA2)
  texto: "#FBF2F6"        # texto principal de la portada
  suave: "#D9B8C6"        # texto secundario, 9.9:1 sobre fondo
  estado-bien: "#A8D8C0"  # app --teal, SALVIA overlay.py L12
  estado-mal: "#FF8A8A"   # app --red, ROJO overlay.py L11
  estado-oro: "#F2C46B"   # app --oro, ORO overlay.py L12
typography:
  familia: Mulish          # portada, OFL; servida desde docs/fonts/
  familia-franja: Roboto   # franja en partida, Bold, OFL
  familia-app: Inter       # solo en la app
  h1: {size: "clamp(2.2rem,5vw,3.4rem)", weight: 800, line-height: 1.05, tracking: "-.02em"}
  h2: {size: 1.75rem, color: "{colors.rosa2}"}
  h3: {size: 1.3rem, color: "{colors.rosa}"}
  cuerpo: {size: 1rem, weight: 400, line-height: 1.6}
  tagline: {size: 1.2rem, color: "{colors.suave}"}
  nota: {size: .9rem}
  legal: {size: .82rem}
  cifras: tabular-nums
rounded:
  pildora: 999px   # solo botones
  hero: 18px
  tarjeta: 14px
  faq: 12px
  paso: 32px       # círculo de los pasos (diámetro)
  vineta: 8px      # viñeta de confianza (diámetro)
spacing:
  escala: [8, 12, 16, 20, 24, 32, 40, 48]
  contenedor: 960px
  contenedor-padding: 24px
  hero-max: 1200px
  quiebres: [800px, 900px]
components:
  boton-primario: {bg: "{colors.rosa}", fg: "{colors.fondo}", hover-bg: "{colors.rosa2}", radius: "{rounded.pildora}", padding: "14px 28px", weight: 800}
  boton-chico: {bg: "{colors.rosa}", fg: "{colors.fondo}", radius: "{rounded.pildora}", padding: "8px 18px"}
  tarjeta: {bg: "{colors.fondo2}", border: "1px {colors.borde}", radius: "{rounded.tarjeta}", padding: 20px}
  faq: {bg: "{colors.fondo2}", border: "1px {colors.borde}", radius: "{rounded.faq}", padding: "14px 18px", summary: "{colors.rosa2}"}
  barra: {position: sticky, padding: "10px 24px", border-bottom: "1px {colors.borde}"}
  foco: {outline: "2px currentColor; en botones {colors.rosa}", offset: 3px}
  vineta-confianza: {size: "{rounded.vineta}", color: "{colors.rosa}"}
---

## Overview
Racha es la portada de descargas y la app de un coach de LoL que usa tus propias partidas. La página tiene un solo trabajo: que un jugador de Windows descargue el `.exe` y confíe en él. Es plana, oscura, en vino y rosa, y cada afirmación tiene fuente en `README.md` o `docs/CUMPLIMIENTO.md`. Los datos se escriben con su base («55 % en 108 partidas»). La portada no imita a la competencia; ver `taste/inspo.md`.

## Colors
- Un solo acento: `rosa` #F28DB0. Es el mismo en la portada (`--rosa`), la app (`--acc`) y la franja (ROSA). Va en el botón, la marca, las viñetas y el foco.
- `rosa2` #F8C3D6 es el tinte del acento: enlaces, h2 y hover del botón. Nunca va como fondo de un bloque grande.
- `texto` #FBF2F6 sobre `fondo` #24111A. Secundario: `suave` #D9B8C6 (9.9:1).
- `borde` #4A2436 es decorativo (1.36:1): nunca separa información por sí solo.
- Los estados (`estado-bien`, `estado-mal`, `estado-oro`) solo aparecen dentro de capturas de la app. En la portada nunca son decoración. Un solo rojo por pantalla (lienzo.py L28); el oro se usa cuando el rojo ya está ocupado.
- La estela (degradado #A33A63 → #A8D8C0) es solo de la app, nunca de la portada.
- Se permiten derivados de tokens (`color-mix` con `var()`, rgba de un token). Cualquier otro hex es un error (web-20 punto 14).
- Contraste: texto ≥ 4.5:1 y foco ≥ 3:1 contra su fondo real.

## Typography
- La portada usa Mulish (400, 600 y 800), servida desde `docs/fonts/`, sin Google Fonts. La franja usa Roboto Bold; Inter va solo en la app.
- h1: clamp(2.2rem, 5vw, 3.4rem), peso 800, line-height 1.05, tracking -.02em. Hay uno solo por página.
- h2: 1.75rem (28px) en `rosa2`. h3: 1.3rem (20.8px) en `rosa`. Los dos con peso 700 y line-height 1.6 heredado del cuerpo (medido con getComputedStyle, 20-nov-2026).
- Cuerpo: 1rem, peso 400, line-height 1.6. Tagline: 1.2rem en `suave`. Nota: .9rem. Legal: .82rem.
- Las cifras que cambian usan `tabular-nums`.
- Sustituto libre si falta Mulish o Roboto: TODO. Hoy cae a system-ui y Segoe UI.

## Layout
- Contenedor de 960px con padding de 24px; el hero llega hasta 1200px.
- Quiebres: 800px (las filas pasan a zigzag) y 900px (el hero pasa a dos columnas).
- Espaciado solo de la escala: 8, 12, 16, 20, 24, 32, 40 y 48.
- Anchos de lectura: 520px (nota), 560px (tagline) y 720px (texto de una fila sola). La marca de la barra mide 1.4rem. `scroll-padding-top` de 72px para que la barra fija no tape el destino de un ancla (valores en uso en docs/index.html).
- Orden: barra, hero (mensaje, botón y confianza; UI real a la derecha), 3 pasos, qué es, antes/durante/después, FAQ, botón final y pie.
- El botón principal y la lista de confianza se ven sin scroll a 390×844 y a 1440×900.

## Elevation & Depth
- Es plana. La profundidad viene del paso `fondo` → `fondo2` más un borde de 1px en `borde`.
- La única excepción es la barra fija, con `color-mix` de `fondo` al 88 % y `blur(8px)`. Se mide con preship: si empeora el LCP, el CLS o el contraste, va con fondo sólido.
- Una sola sombra: la de la tarjeta al pasar el mouse, `0 14px 30px -12px rgb(0 0 0 / .25)` (decisión del usuario, 20-nov-2026). Fuera de eso, sin sombras; las de `hero-app` vienen horneadas en la composición.

## Shapes
- La píldora (999px) es solo para botones. Radios de 18 (hero), 14 (tarjeta) y 12 (FAQ).
- Círculos de los pasos de 32px; viñetas de confianza de 8px en `rosa`.
- El foco no cambia la forma del elemento: la píldora sigue siendo píldora.

## Components
- **Botón primario**: fondo `rosa`, texto `fondo` (7.87:1), hover `rosa2`, píldora, 14px 28px, peso 800. Al presionar, `scale(.97)`.
- **Botón chico**: el de la barra, con padding de 8px 18px.
- **Tarjeta**: fondo `fondo2`, borde de 1px, radio 14 y padding de 20.
- **FAQ**: `details` con fondo `fondo2`, radio 12, padding de 14px 18px y `summary` en `rosa2`.
- **Barra**: sticky, padding de 10px 24px y borde inferior de 1px.
- **Foco**: outline de 2px del color del texto (`currentColor`), offset de 3px, en `a`, `button` y `summary`. En `.btn` es `rosa`, porque su texto es `fondo` y el anillo no se vería. Entra en 180 ms.
- **Viñeta de confianza**: punto de 8px en `rosa`, nunca un emoji ni un ícono.
- Todo `[data-descarga]` apunta a `/releases/latest` en el HTML; el JS lo cambia al `.exe`. La regex `^Racha-Setup-[\d.]+\.exe$` no se toca.

## Do's and Don'ts
- Do: escribir cada dato con su base y su parche o número de partidas («55 % en 108 partidas»).
- Do: usar capturas reales de la app, en AVIF o WebP, con `width`/`height` y `loading="lazy"` salvo el LCP.
- Do: animar solo `transform`, `opacity`, el outline del foco y la sombra de la tarjeta, con `cubic-bezier(.2,.7,.2,1)` en 180 ms (botón, foco) o 260 ms (tarjeta), la cuenta en 700 ms, y nada con `prefers-reduced-motion`.
- Don't: decir «aprobada por Riot» ni «Riot Approved». Fuente: CUMPLIMIENTO L19 (preguntas abiertas con Riot).
- Don't: poner contadores de usuarios o descargas ni prueba social inventada. Fuente: portada-propuesta §1 (1 estrella y 0 descargas en la API).
- Don't: dar órdenes de juego. Fuente: CUMPLIMIENTO L8 e `IMPERATIVOS` en herramientas/replay.py L112.
- Don't: usar emojis. Fuente: el usuario, nov-2026.
- Don't: usar splash art ni logos de LoL o Riot. Fuente: portada-propuesta P2.
- Don't: animar otra cosa que `transform`/`opacity`, ni animar con reduced-motion. Fuente: docs/index.html y pruebas/test_ds_estela.py.
- Don't: usar los estados como decoración. Fuente: esta guía, sección Colors.
- Don't: poner cifras de RAM o FPS sin medir. Fuente: portada-propuesta §2 (COMPETENCIA: «Medir RAM de Edge antes de presumir»).
- Don't: agregar «Código abierto» a la lista de confianza. Fuente: memory/corrections.md, 2026-11-20.

## Iconography
- Ícono de la app: `assets/htc-icono.svg` (el publicado; `docs/img/icono.png` es el mismo PNG). Favicon: `docs/img/icono-32.png`; además `docs/img/apple-touch-icon.png`.
- La marca va en texto: `Ra<span>cha</span>`, «cha» en `rosa`, peso 800.
- No hay set de íconos de UI: TODO. Hasta que lo haya, sin íconos (las viñetas son puntos).
- La captura de SmartScreen (`smartscreen.webp`) está en TODO: no se fabrica.

## Voice
- Español neutro, de tú, de jugador. Los términos de LoL van en inglés: champ select, win rate, tier list, CS, build, replay.
- Los datos van con su base, y el parche y el número de partidas siempre.
- «beta», dicho con honestidad. Junto al botón: «Windows 10 y 11 · 16 MB · beta».
- El aviso legal de Riot va literal en el pie (README L157).
- Vocabulario permitido y prohibido: `rules/words.md`.
