# Modelo y esfuerzo para cada trabajo

Regla pedida por Patricio el 7-11-2026. Antes de cualquier cambio al estudio (motor, plugin, instrucciones, sala) y antes de un trabajo grande (un video completo, un lote de imágenes, una revisión), elegir con qué modelo y con qué esfuerzo conviene hacerlo. Decirlo en una línea al empezar («Para esto conviene X con esfuerzo Y, porque…») y aplicarlo donde se pueda. El objetivo es aprovechar mejor el plan: lo caro para lo que importa, lo liviano para lo repetitivo.

## Qué se puede elegir y quién lo elige

| Dónde | Cómo se elige | Quién |
|---|---|---|
| Esta conversación con Claude | selector de modelo de la app | **la persona**: Claude no puede cambiarlo solo. Si conviene otro, lo recomienda al empezar y sigue con el actual si no lo cambian |
| Agentes del plugin (guionista, evaluador, etc.) | `model` (haiku · sonnet · opus · fable) y `effort` (low · medium · high · xhigh · max) en cada encargo | Claude, siguiendo esta tabla (esta regla es la autorización escrita para fijarlos) |
| Codex (`codex exec`) | `-m <modelo>` y `-c model_reasoning_effort=low\|medium\|high\|xhigh` | Claude, **solo con el sí de la persona**: gasta la cuota de su plan de ChatGPT |

Más modelo y más esfuerzo = mejor razonamiento, pero más uso del plan y más espera. No subir por subir.

## Tabla por tipo de trabajo

| Trabajo | Modelo | Esfuerzo | Por qué |
|---|---|---|---|
| Cambios al motor o al plugin (código, protecciones, render, sala) | el más capaz de la cuenta (Fable 5.1 u Opus 5.5) | alto | un error cuesta caro: pisar archivos, desfasar la voz, entregar algo roto |
| Revisión independiente de esos cambios | Codex en solo lectura (`-s read-only`), o un agente que no hizo el trabajo | alto (medio si el cambio es chico) | quien no escribió el código ve lo que el autor no ve: el 7-11 la revisión de Codex encontró 7 fallas reales en la 0.12.0 |
| Guion, gancho, títulos, dirección del video | Opus | alto | criterio editorial y la voz del canal |
| Revisar cuadros, capa viva, imágenes traducidas | Opus (mira imágenes) | medio | hay que mirar con cuidado, no razonar largo |
| Investigación con cifras y fuentes | Opus o Sonnet con búsqueda | alto | nunca inventar datos; buscar más de una vez |
| Evaluación de un video (evaluador) | Opus | medio | ejes y minutos ya están definidos |
| Repetitivo: listas, renombrar, pasar a plantilla, resúmenes cortos, transcribir | Sonnet o Haiku | bajo o medio | rápido y barato; no necesita más |
| Imágenes nuevas (prompts listos) | Codex o ChatGPT con su herramienta de imágenes | — | gasta el plan de la persona: pedir el sí y decir cuántas son |

## Cómo dejarlo registrado

- En el mensaje al empezar: modelo y esfuerzo elegidos y por qué, en una línea.
- En la tabla Versiones del documento vivo, junto a cada versión del motor: con qué se hizo y con qué se revisó (por ejemplo «Opus alto + revisión Codex alto»).
- Si una tarea salió mal y el modelo pudo ser la causa, anotarlo en `00_ESTADO.md` y probar con el siguiente nivel antes de cambiar el sistema (ver `sistema.md`: primero descartar que falló el sistema).
