# Franja Sombra y las reglas de Riot

Sombra solo muestra datos tuyos o conteos que se ven con Tab. Lee el cliente (LCU) y la Live Client Data, nunca la memoria del juego, y no inyecta nada. Esta tabla une cada regla con la prueba que la cubre.

| Regla de Riot | Qué hace Sombra | Prueba |
| --- | --- | --- |
| Sin timers de enemigos (ultis, hechizos, jungla; desde el 13-03-2025) | No muestra ningún timer: solo tu tope de muertes, tu CS o tus peleas contra tu sombra y tus 4 marcas | `replay.py --momentos --validar` (lista negra: «cooldown», «flash», «respawn», «campamento»…) |
| No dictar decisiones ni automatizarlas (29-05-2025) | Datos, nunca órdenes: «faltan 350», nunca «compra»; la regla entra solo como `regla.corta` | `test_sombra.Guion.test_regla_corta_es_dato`, `test_momentos.Escena.test_zonas_fijas_y_pocas_palabras`, `IMPERATIVOS` en `replay.py` |
| Sin anuncios en overlays | Racha no tiene anuncios | — |
| Sin puntaje ni rango propio | 4 casillas y una regla, sin MMR ni nota | `LISTA_NEGRA` («mmr», «elo») |
| Sin lectura de memoria (Vanguard, 06-10-2026) | Solo HTTP local a `127.0.0.1:2999` (Live Client Data) y al LCU | `companion.vivo()` es la única lectura en partida |
| Información dinámica en tiempo real, con recelo | Comparación solo contra tu propio historial; máx. 3 interrupciones, nunca en pelea, nada después del 25; cada momento se apaga en Ajustes | `test_momentos.Contrato` (6 pruebas) |
| Scouting de los 10 jugadores | No hay: solo tú y, en el panel al morir, el marcador de objetivos que se ve con Tab | — |

Pendiente (Fase 0, del dueño de Racha): confirmar el estado del registro en el Developer Portal (`riot.txt`) y preguntar por escrito por 3 puntos: la comparación en vivo con el historial propio, la carta en la pantalla de carga y el uso de la vida propia para callar la franja. Plan B si Riot objeta la comparación en vivo: la sombra solo al morir, en la carga y al terminar.
