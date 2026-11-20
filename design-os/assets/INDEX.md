# Assets

Solo se usa lo que está aquí o lo que indexa esta página. No se duplican archivos de docs/.

## En esta carpeta
- `htc-icono.svg`, `htc-icono-256.png`, `htc-icono-1024.png`: el ícono publicado de la app (el mago vino, sin escudo ni runa desde el 20-nov-2026). Copiados de `racha.gg/.equipo/diseno/icono/`. `docs/img/icono.png` y `scripts/web/icono.png` son el mismo PNG de 256.

## En docs/img (portada)
- `icono-32.png` (favicon), `apple-touch-icon.png` (180), `og.jpg` (1200×630, para compartir), `icono.png` (256; lo usan privacidad.html y terminos.html).
- `docs/fonts/mulish.woff2`: Mulish variable (200–1000, OFL; licencia en `docs/fonts/OFL-Mulish.txt`). Es copia de `scripts/web/fonts/`.

## En docs/img/readme (capturas reales de la app)
- `hero-app-{800,1200}.{avif,webp}`: champ select con la franja Sombra encima. Se arma con `herramientas/composicion/armar.py hero-app`.
- `champ-select-recorte.webp`, `sombra-recorte.webp`, `errores-recorte.webp`, `tier-recorte.webp`: recortes legibles para la portada.
- `champ-select.webp`, `sombra.webp`, `errores.webp`, `tier.webp`, `campeones.webp`, `inicio.webp`, `en-vivo.webp`: ventanas completas (README).
- `hero.png`, `pasos.png`: README y origen de og.jpg.

## Mascota (portada)
- Póster: SVG inline en `docs/index.html` (del minion vino, sin escudo ni runa). 3D: `docs/js/mascota.js`.
- `docs/vendor/three/0.185.0/`: three.module.min.js y three.core.min.js de npm (`three@0.185.0`, la última con `.min.js`), con su LICENSE (MIT).

## TODO
- Capturas de «Tu partida» (al terminar) y de las runas de la app real: la fila de runas va sin imagen hasta tenerlas.
- `smartscreen.webp`: los 2 pasos de SmartScreen en español. Hay que capturarlo en una PC real; no se fabrica.
- Logo: el mago, sin escudo ni runa (decisión del usuario, 20-nov-2026). Las barras (`racha.svg`, `racha-mono.svg`, `racha-wordmark.svg`) se quedan sin publicar: ver memory/corrections.md.
- Set de íconos de UI: no hay.
