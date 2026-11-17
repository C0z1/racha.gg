# Cambios de Racha

Una línea por versión, en palabras de jugador. Lo más nuevo arriba.

## Sin publicar
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
