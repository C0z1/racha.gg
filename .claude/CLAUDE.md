# Trabajo en equipo: Opus + DeepSeek

**Lee `.equipo/PIZARRON.md` primero**: tiene la meta, el estado de cada agente, el mapa del repo y los hallazgos. Al empezar y al terminar cada turno, actualiza tu sección.

Dos sesiones de Claude Code trabajan en esta carpeta. Cada una es dueña de sus archivos; no edites los de la otra.

| | Opus (construye y decide) | DeepSeek (asistente barato) |
|---|---|---|
| Dueño de | `scripts/`, `.equipo/PLAN.md`, `.claude/`, `datos/analisis-*.md` y todo lo demás | `.equipo/BITACORA.md`, `.equipo/deepseek-*.md` (las viejas, en `.equipo/archivo/`) |
| Hace | Análisis nuevos (timeline, matchups), cambios al plan, decisiones | Correr `scripts/descargar.py`, `scripts/revision.py` y `scripts/score.py`, registrar sesiones en la bitácora, resúmenes, dudas rápidas |

- Para pasarse trabajo: anota pedidos y hallazgos en `.equipo/notas-equipo.md` (fecha, quién, qué). Léelo al empezar.
- Opus, además, consulta a DeepSeek-Pro con `& $HOME\ask-deepseek.ps1` (ver CLAUDE.md global): manda resúmenes en `datos/*.md`, nunca los JSON de `datos/raw/` (son ~85 KB cada uno).
- La key de Riot está en la variable de entorno `RIOT_KEY`: nunca la escribas en archivos, logs ni commits, y nunca leas ni mandes `.env`.
- Solo Opus hace commits (nunca push).

## Dónde va cada cosa
- `scripts/`: solo la app (lo que instala el instalador). Un módulo nuevo de la app va aquí.
- `pruebas/`: todas las `test_*.py`; cada una agrega `scripts/` al path en su primera línea. Correr: `python -m unittest discover pruebas`.
- `herramientas/`: utilidades de desarrollo que no van en la app (replay, salud, dev_*).
- `instalador/`: `build.ps1`, `htc.iss`, `humo_exe.py`. Si un archivo sale de `scripts/`, agrégalo al `[InstallDelete]` de `htc.iss`.
- `.equipo/`: notas vivas; cuando un plan se termina, va a `.equipo/archivo/`. Es local: está en `.gitignore` y no se sube a GitHub (nada de la app ni del build la lee). En otra PC con un clon viejo, el pull la borra del disco; se recupera con `git checkout bdcf694~1 -- .equipo && git rm -r -q --cached .equipo` (lo editado después en esta PC se copia a mano).

## Commits y versiones
- Título del commit de 72 caracteres o menos; el detalle va en el cuerpo.
- Cada versión agrega una línea en `CHANGELOG.md`, en palabras de jugador (qué cambia para quien usa Racha).
