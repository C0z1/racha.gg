# web-20: los 20 puntos de toda página

P = lo comprueba `checks/preship.py` solo, a 390×844 y 1440×900.

| # | Punto | P |
|---|---|---|
| 1 | Contraste del texto ≥ 4.5:1, con estilos calculados y el fondo real | P |
| 2 | Texto de los botones ≥ 4.5:1, también en hover | P |
| 3 | Sin scroll horizontal a 390 ni a 1440 | P |
| 4 | CLS < 0.05 hasta el final del scroll | P |
| 5 | Recurso LCP < 80 KB transferidos y LCP < 2.5 s en local | P |
| 6 | Carga inicial < 400 KB | P |
| 7 | Cada `img` con alt y `width`/`height` | P |
| 8 | Un solo h1 y sin saltos de nivel | P |
| 9 | Foco visible al tabular: ≥ 2px y ≥ 3:1 contra el fondo | P |
| 10 | Con reduced-motion, ninguna animación ni transición tras el scroll, sin `.escena canvas` y sin requests a /vendor/three | P |
| 11 | Todo `[data-descarga]` termina en `Racha-Setup-x.y.z.exe` y su HEAD da 200 o 302 (sin red: SKIP, nunca PASS) | P |
| 12 | Sin JS, el href de respaldo es `/releases/latest` | P |
| 13 | El botón (y la confianza) se ven sin scroll a 390×844 y 1440×900 | P |
| 14 | Todos los hex del CSS están en `colors` de DESIGN.md (se permiten derivados con color-mix o rgba de tokens); los fill/stroke/stop-color del HTML y los de docs/js, en `colors` o `mascota` | P |
| 15 | Sin emojis en el texto visible (Extended_Pictographic) | P |
| 16 | Sin palabras prohibidas de `words.md` ni imperativos de juego | P |
| 17 | El aviso legal de Riot, literal | P |
| 18 | Imágenes de contenido en AVIF o WebP, y lazy salvo la del LCP | P |
| 19 | Consola sin errores y sin 404 | P |
| 20 | Hay title, description y og:image, y og:image responde 200 | P |
