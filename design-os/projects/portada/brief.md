# Brief: portada de descargas (docs/index.html)

- **Meta:** más descargas del `.exe` de Windows por parte de jugadores de LoL, sobre todo de LAN/LAS.
- **Referencia a superar:** Mobalytics, la página de su app de escritorio (https://mobalytics.gg/download). Ver `taste/inspo.md`.
- **Vara** (de `rules/bar.md`):
  - 20/20 en web-20;
  - igual o mejor que Mobalytics en LCP, peso y CLS (`preship.py --ref https://mobalytics.gg/download`);
  - botón y confianza sin scroll a 390×844;
  - cada afirmación con su fuente;
  - cero valores fuera de tokens.
- **Fijo:** el JS del botón de descarga (regex `^Racha-Setup-[\d.]+\.exe$`, `[data-descarga]`, `localStorage`), el aviso legal de Riot en el pie, sin logos de LoL ni de Riot, y la lista de confianza aprobada.
- **Cambios de esta vuelta:**
  - Mulish servida desde la página (sin Google Fonts);
  - `rosa2` pasa a #F8C3D6;
  - sin la marca duplicada en el hero;
  - el `backdrop-filter` de la barra se decide midiendo.
