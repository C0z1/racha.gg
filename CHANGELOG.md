# Cambios de Racha

Una línea por versión, en palabras de jugador. Lo más nuevo arriba.

## Sin publicar
- En partida, **Ctrl+Shift+Z** vuelve clicable la franja (se apaga sola con el mismo atajo, un clic fuera o 20 s sin el mouse encima): ocúltala, abre Ajustes, muévela o cambia de vista. **Stats**: tu oro, CS, peleas y visión por minuto y tu nivel, cada uno con su flecha contra tu sombra. **Build**: tu core con lo comprado apagado y el que sigue marcado. El renglón de tu plan ahora dice cuánto ganas cuando lo cumples («≥1 dragón al 14: ganas 69%»), y las compras salen una sola vez por ítem.
- Al terminar cada partida, «Tu partida» te dice qué hiciste bien y qué no (con el minuto de cada muerte y de cada error), por qué importa con tus propias partidas del rol («con 1 dragón o más al 14 ganas 69 %; sin él, 27 %») y un foco para la próxima. Sale al instante, sin esperar a Riot, y se afina con el CS y los niveles cuando llega la partida.
- Al terminar la partida, la carta de Sombra ya no sale vacía: cuenta solo las marcas con dato y dice si cumpliste tu tope del 14 al 25, también sin regla. Lo que vio Racha en vivo se queda en pantalla aunque el cliente tarde en publicar la partida, y la revisión ya no muestra por error una partida vieja. «¿Te sirvieron las notas?» sale también con Sombra, y en Ajustes eliges el tamaño de la franja.
- Franja nueva, **Sombra**: en partida juegas contra tu sombra, la mediana de tus victorias con ese campeón minuto a minuto. Tres zonas que nunca cambian de lugar: tu tope de muertes, tu CS (o tus peleas desde el 14) contra tu sombra y tus 4 marcas (minutos 6, 10, 14 y 25). Se actualiza cada segundo, habla 3 veces por partida como mucho y nunca en una pelea. Al terminar ves lo que mostró y por qué calló. La pastilla de antes sigue en Ajustes como «Clásica». La franja corre en su propio proceso: si se traba, Racha sigue. Al cargar la partida ves tu carta (tu récord en el matchup, tu regla y tus marcas). Los números ya no bailan (fuente incluida). En «Abajo» respeta la escala de tu HUD. Si dices «no» dos veces a «¿Te sirvieron?», Sombra habla solo una vez por partida. Inicio muestra la racha de tu regla y cuánto te falta para graduarla. En tu primer regreso a la tienda ves a qué minuto suele regresar tu sombra; tu próxima marca late en su último minuto. En Ajustes puedes apagar cada aviso de Sombra, prender un «tic» al sellar una marca, usar el modo ahorro (lee la partida cada 3 s) y la franja recuerda dónde la dejaste en cada resolución. Tus 4 marcas ahora son tuyas: 2 salen del plan de tu rol (los momentos en que más se separan tus victorias de tus derrotas) y 2 vigilan tus errores más repetidos (muerte sin objetivo, pelea perdida sin ti, nivel abajo al 6). Un error solo pone rojo su punto, sin interrumpir; al morir, el panel te dice si fue uno de ellos. Cuando evitas un error 8 de 10 veces queda corregido y entra el siguiente; Inicio muestra tus errores corregidos y cuánto te falta. La barra usa los renders del lienzo: tu retrato con el anillo partido en tramos (cada muerte apaga uno; sobre tu tope, el retrato se apaga) y el minion caster en un anillo que se llena hacia tu sombra (desde el 14, espadas para tus peleas). La barra ahora es casi negra como la pastilla del lienzo, con tus muertes en grande, su medalla bajo tu retrato y el anillo en degradado.
- En ranked, Racha se equivoca menos al adivinar a tu rival de línea antes de que se revelen los roles: con 386 de tus partidas, el ajuste nuevo baja los errores de 23 % a 22 % (prefiere esperar a que tu rival elija antes que señalar al equivocado).
- En partida, el nivel «10 · 10» ya no se parte en dos líneas cuando aparece «Puedes tradear».
- Un timeline dañado ya no tumba la selección de campeón ni la revisión post-partida, y «Tu última partida» se salta un archivo roto en vez de quedar vacía.
- Racha es mucho más rápida: la selección de campeón carga en 0.15 s (antes 4 s), tu perfil se arma en medio segundo (antes 7 s) y la revisión post-partida sale en 0.4 s (antes 5 s). Cada partida se procesa una sola vez.
- Un archivo de partida dañado ya no rompe la selección de campeón ni las builds: se salta.
- Las partidas que se guardaron desde el cliente de LoL se cambian por la versión completa de Riot, con compras de ítems y habilidades. Las de práctica se quedan como están.
- Más seguridad: una página web cualquiera ya no puede pedirle nada al Racha que corre en tu PC.
- Inicio más claro: tu regla de hoy arriba, tu racha y tu sesión lado a lado, y la versión junto a «Actualizar» en vez de tapar los atajos.
- En ranked, Racha ya no toma como tu rival al primer enemigo que elige: espera al que juega tu línea, según el rol de cada campeón en Master+.
- Arreglo: en la Herramienta de práctica salía «Error: AttributeError» por los muñecos sin ítems.
- Repo reorganizado: la app queda sola en `scripts/`, las pruebas en `pruebas/`, las herramientas de desarrollo en `herramientas/` y los planes terminados en `.equipo/archivo/`. Se quitó la ventana tkinter vieja, que ya no se usaba. Para quien juega no cambia nada.
- Limpieza del código: fuera imports sin uso, código muerto de la interfaz y las notas de quién pidió o revisó cada cosa en los comentarios. Para quien juega no cambia nada.

## 13 de noviembre de 2026
- **0.31**: solo baja tus Solo/Duo de la temporada actual, todas con su línea de tiempo. Gasta menos llamadas de la key compartida.
- **0.30**: una sola cola de descargas. Lo primero al abrir Racha es tu historial completo, también el de tu cuenta principal aunque juegues con otra.
- **0.29**: Partidas muestra todo lo descargado, de 50 en 50, con filtro por cola; «Ver» abre la revisión de esa partida.
- **0.28**: feedback que enseña: cada muerte se clasifica (trade, torre, pelea, gank, 1v1) y trae qué probar la próxima vez.
- **0.27**: vinculas tu Google a hasta 5 cuentas de LoL. Las runas se escriben aunque tengas el cliente lleno de páginas.
- **0.26**: historial completo, también de tu otra cuenta, sin mezclar las dos.
- **0.25**: builds Master+ de todos los campeones, sacadas de partidas del ladder (LA1, KR, EUW).
- **0.24**: en partida, los 10 jugadores con su rango, win rate de la temporada y runa clave. Runas desde que pasas el mouse por un campeón.
- **0.23**: al fijar campeón, Racha te muestra tus runas sin robarte el foco.
- **0.22**: los matchups reconocen bien nombres como Miss Fortune y Kai'Sa.

## 12 de noviembre de 2026
- **0.21**: botón «Actualizar» que baja e instala la versión nueva, nunca a mitad de partida. Si la key de Riot caduca, la partida se guarda igual desde el cliente.
- **0.20**: arreglo: el próximo ítem solo se calculaba en los primeros 2 minutos.
- **0.19**: la franja se acomoda encima del HUD y a la derecha del chat, sin tapar nada, en 5 resoluciones.
- **0.18**: lenguaje visual nuevo (Estela). Menos de 1 % de CPU en reposo.
- **0.17**: ventana rehecha desde cero; ya no falla en PCs ajenas. Encuentra LoL donde esté instalado.
- **0.16**: Racha comenta tu draft con 4 frases sacadas de tus datos, con voz opcional.
- **0.15**: ajustes de la quinta prueba real en partida.

## 10 y 11 de noviembre de 2026
- **0.14**: tus partidas llegan desde el cliente de LoL. Arreglo de las pruebas automáticas en Windows y Ubuntu.
- **0.13**: aviso si LoL está en pantalla completa, porque ahí la franja no se ve.
- **0.12**: el contador de muertes del 14 al 25 ya no aparece después del 25; un tag mal escrito ya no borra tu cuenta guardada.
- **0.11**: franja en partida con avisos.
- **0.8 a 0.10**: builds del top para todos, invitar amigos, reportes, revisión post-partida, logo propio y tabla del grupo.
- **0.7**: ventana propia, login con Google y cuenta en la nube, builds de los onetricks del top, rival probable en ranked.
- **0.6**: «Tu build» sin key, armada con tus partidas. Una partida dañada ya no vacía tu rendimiento.
- **0.5**: funciona sin key: tus últimas ~20 partidas salen del cliente. Soporte de ARAM y barra de título oscura.
- **0.4**: primera versión para amigos: funciona sin key ni historial.

## 9 de noviembre de 2026
- **0.1 a 0.3**: primera app (entonces se llamaba HTC): Perfil, Partidas, Selección con tus 3 reglas, En vivo con tu rival y los objetivos, paleta Vino, instalador y arranque al abrir LoL.
