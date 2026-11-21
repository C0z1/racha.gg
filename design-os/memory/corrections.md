# Correcciones del usuario

Formato: `AAAA-MM-DD · regla`. La más nueva, abajo. Cada una es una regla que se cumple siempre.

- 2026-11-20 · La lista de confianza junto al botón no lleva "Código abierto"; son Gratis y sin anuncios, Tus partidas viven en tu PC, Sin Overwolf.
2026-11-20 · El logo es el mago (htc-icono). El logo de barras (racha.svg, racha-wordmark.svg) no se usa en la portada: lleva los colores de la Estela, que solo van en la app.
- 2026-11-20 · Movimiento con cubic-bezier(.2,.7,.2,1): 180 ms en botones y foco, 260 ms en tarjetas.
- 2026-11-20 · La tarjeta lleva sombra al elevarse (0 14px 30px -12px rgb(0 0 0 / .25)); es la única sombra de la página.
- 2026-11-20 · El anillo de foco es de 2px del color del texto; en los botones va en rosa para que se vea.
- 2026-11-20 · La mascota es el minion vino SIN escudo ni runa: placa del pecho lisa y paleta vino propia (sin el azul ni el cian del modelo de Riot). En la página, el alt y los archivos se llama «mascota», nunca «minion» ni «caster».
- 2026-11-20 · El logo publicado también va sin escudo ni runa (htc-icono.svg, sus PNG, htc.ico, og.jpg y hero.png). El ícono del exe cambia en el próximo release; no se publica un release solo por esto.
- 2026-11-20 · La mascota 3D solo aparece en PC grande: ≥1400 px, pointer fine, sin reduced-motion y con WebGL2. En laptop chica, tablet y celular no aparece y no se descarga nada.
- 2026-11-20 · En celular el botón principal es «Enviarme el enlace» (navigator.share o portapapeles); el del .exe queda como secundario, con contorno rosa y texto rosa2, y sigue enlazado.
- 2026-11-20 · La mascota es el mago original (docs/js/mascota.js, modelo()), mejorado un poco (degradado, collar de cuero, costuras, grieta, amarres); el personaje nuevo de la rama `hechizos` se descartó.
- 2026-11-20 · En PC grande la página es un carrusel 3D que gira alrededor de la mascota: ella al centro, cada sección un panel que pasa al frente al bajar (maqueta aprobada por el usuario por Discord).
- 2026-11-20 · Cambia la de «solo PC grande»: el carrusel sale desde 1280×580 (laptops) y en celular vertical táctil la mascota vive en un balcón fijo bajo la barra, con secciones que entran girando; three se baja tras el primer gesto, en un momento libre, y nunca con ahorro de datos. «Enviarme el enlace» sigue de principal en celular.
