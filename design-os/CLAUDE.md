# design-os: cómo diseñar para Racha

`DESIGN.md` manda sobre el gusto, el tuyo y el de cualquier agente. Si un pedido choca con DESIGN.md, para y pregunta; no decidas tú.

## Proceso (6 pasos, siempre en este orden)
1. Lee `DESIGN.md`, `rules/`, `memory/corrections.md` y el `brief.md` del proyecto. Resume lo leído en 6 líneas.
2. Pide (o confirma) la referencia a superar y anótala en `taste/inspo.md`: qué se toma y qué no.
3. Escribe `projects/<pieza>/brief.md` (meta, referencia y vara) y revisa la vara contra `rules/bar.md`.
4. Construye solo con tokens de DESIGN.md y archivos de `assets/` (o los que indexa `assets/INDEX.md`).
5. Corre `python design-os/checks/preship.py` (y `--ref URL` contra la referencia) y repasa `rules/web-20.md`. Lee los FAIL primero.
6. Arregla y repite hasta pasar. Lo que no depende de nosotros queda como SKIP, con su motivo.

## Reglas
- Nunca inventes un color, una fuente, un logo ni un ícono. Si falta, va TODO en DESIGN.md y preguntas.
- Cada corrección del usuario se anota en `memory/corrections.md` como una regla, con el formato `AAAA-MM-DD · regla`.
- Los textos siguen `rules/words.md`: cada afirmación con su fuente en `README.md` o `docs/CUMPLIMIENTO.md`.
- Sin emojis. Sin «aprobada por Riot». Sin cifras de RAM ni FPS sin medir.
- El JS de descarga de `docs/index.html` (regex `^Racha-Setup-[\d.]+\.exe$`, `[data-descarga]`, caché en `localStorage`) no se toca.
