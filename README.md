<p align="center">
  <img src="docs/img/readme/hero.png" alt="Racha (racha.gg). Deja de adivinar por qué pierdes. Tu coach de League of Legends, hecho con tus propias partidas.">
</p>

<p align="center">
  <a href="https://github.com/C0z1/racha.gg/releases/latest"><img src="https://img.shields.io/badge/Descargar_para_Windows-gratis-F28DB0?style=for-the-badge&logo=windows&logoColor=white&labelColor=44203A" alt="Descargar para Windows, gratis"></a>
</p>

<p align="center">
  Las guías te dicen cómo juega un Challenger.<br>
  <b>Racha te dice qué te hace perder <i>a ti</i></b>, y te lo recuerda justo cuando importa.
</p>

<p align="center">
  <a href="https://c0z1.github.io/racha.gg/">Página del proyecto</a> ·
  <a href="CHANGELOG.md">Novedades</a> ·
  <a href="https://c0z1.github.io/racha.gg/privacidad.html">Privacidad</a> ·
  <a href="https://c0z1.github.io/racha.gg/terminos.html">Términos</a>
</p>

<p align="center">
  <img src="docs/img/readme/pasos.png" alt="1. Descarga. 2. Abre LoL. 3. Juega.">
</p>

## En champ select

<p align="center">
  <img src="docs/img/readme/champ-select.webp" alt="Selección de campeón: tu récord contra el rival con ese campeón, tu win rate, tus muertes antes del 6, tu plan de 3 reglas y los counters">
</p>

Tu récord contra ese rival, tu win rate con el campeón, el estimado contra él y **3 reglas para esa partida**, sacadas de tus números. Si aún no sabes contra quién vas, Racha espera a que tu rival de línea elija.

## Después de jugar

<p align="center">
  <img src="docs/img/readme/errores.webp" alt="Para trabajar: los errores que se repiten en tus últimas 20 partidas, con el minuto exacto de cada uno">
</p>

Los errores que repites, **con el minuto exacto** para buscarlos en el replay, y qué probar la próxima vez. Nada de ver la partida entera.

## Tus campeones

<p align="center">
  <img src="docs/img/readme/campeones.webp" alt="Campeones: win rate y últimas 5 de cada campeón, mejores y peores rivales, su regla y sus counters">
</p>

Con quién ganas de verdad, contra quién sufres y **qué cuidar con cada campeón**.

## Al abrir LoL

<p align="center">
  <img src="docs/img/readme/inicio.webp" alt="Inicio: tu regla de hoy, tu racha, tu sesión, tu pick de hoy y tu win rate contra tu meta">
</p>

Tu regla de hoy, tu racha, tu sesión y **el campeón que más te conviene hoy**. En partida, una franja discreta sobre el HUD te avisa de tu nivel contra tu rival, tus minions y los objetivos.

## Por qué Racha

| | |
|---|---|
| **Hecho con tus partidas** | Nada de «farmea más». Racha descubre, por ejemplo, que *con 2 muertes o menos del minuto 14 al 25 ganas el 65 %, y con 3 o más, el 44 %*. |
| **Aparece sola** | Se abre cuando abres LoL y cambia de pantalla según la fase: champ select, partida y final. Cero clics. |
| **Juego limpio** | Lee lo que el cliente ofrece a las apps y solo escribe tu página de runas cuando pulsas «Poner las runas». No juega por ti ni toca el juego. |
| **Tus datos son tuyos** | Tus partidas viven en tu computadora. La cuenta en la nube es opcional y la borras con un botón. |

## Qué más trae

- **Revisión al terminar**: hasta 3 momentos clave de la partida con su minuto.
- **Tu semana**: tu récord frente a la semana anterior, tu mejor campeón y tu peor rival.
- **Builds de Master+** para todos los campeones, y tu build contra la de los onetricks del top.
- **Runas con un clic**: la página de la build o la del matchup, cuando tú lo pides.
- **Se actualiza sola**, nunca a mitad de partida, y comprueba que el instalador sea el original.
- **Cuenta en la nube y tabla del grupo**, opcionales: tus ajustes en otra PC y tu win rate junto al de tus amigos.

## Preguntas frecuentes

<details>
<summary><b>¿Me pueden banear por usarla?</b></summary>
<br>
Racha solo <b>lee</b> la información que el propio cliente de LoL ofrece a las apps, la misma que ya ves en tu pantalla. No pickea, no banea, no acepta partidas y no modifica el juego.
</details>

<details>
<summary><b>¿Cuánto cuesta?</b></summary>
<br>
Es gratis y de código abierto.
</details>

<details>
<summary><b>¿Funciona en mi servidor?</b></summary>
<br>
Sí: LAN, LAS, NA, EUW, KR y el resto de servidores de Riot.
</details>

<details>
<summary><b>Windows dice «Windows protegió su PC». ¿Es seguro?</b></summary>
<br>
Pasa con las apps nuevas que todavía no tienen firma digital. Dale a <b>Más información → Ejecutar de todas formas</b>. El código está aquí mismo, a la vista de todos.
</details>

<details>
<summary><b>¿Qué datos guarda?</b></summary>
<br>
Tus partidas y tus ajustes viven en tu computadora. Si activas la cuenta en la nube, guarda tu Riot ID, tus ajustes y un resumen de tus partidas (no la partida completa); los borras con un botón. Nada de MMR ni ELO. Los detalles están en la <a href="https://c0z1.github.io/racha.gg/privacidad.html">política de privacidad</a>.
</details>

<br>

<p align="center">
  <a href="https://github.com/C0z1/racha.gg/releases/latest"><img src="https://img.shields.io/badge/Descargar_Racha-F28DB0?style=for-the-badge&logo=windows&logoColor=white&labelColor=44203A" alt="Descargar Racha"></a>
</p>

---

## Cómo está hecho

Racha está hecha en Python. Corre un servidor local y muestra la ventana con Edge en modo app; la franja en partida se dibuja con Pillow. Lee de tres fuentes: la Riot API (con tu key o tu código de acceso), la API local del cliente (LCU) y la Live Client Data API. Solo escribe en el cliente tu página de runas, cuando pulsas el botón. Los datos de matchup salen de partidas Master+ agregadas, sin nombres de jugadores.

| Carpeta | Qué hay |
|---|---|
| [`scripts/`](scripts) | La app. `companion_web.py` la arranca; `web/` son las pantallas. |
| [`pruebas/`](pruebas) | Las pruebas automáticas; corren en cada cambio en Windows y Ubuntu. |
| [`backend/`](backend) | El servidor pequeño en Cloudflare: guarda la key de Riot y las cuentas. |
| [`instalador/`](instalador) | Cómo se arma el `.exe` y el instalador de Windows. |
| [`herramientas/`](herramientas) | Utilidades de desarrollo que no van en la app. |
| [`docs/`](docs) | La página web, la [guía de uso](docs/USO.md), privacidad y términos. |

```bash
python scripts/companion_web.py --demo      # la app con datos de ejemplo, sin cliente
python -m unittest discover pruebas         # pruebas: sin red, sin key, sin partidas
```

Por dentro, la app y el instalador se siguen llamando HTC (su nombre viejo): cambiarlo rompería la actualización de quien ya la tiene instalada. Los PRs son bienvenidos. Licencia [MIT](LICENSE).

<sub>Racha isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.</sub>
