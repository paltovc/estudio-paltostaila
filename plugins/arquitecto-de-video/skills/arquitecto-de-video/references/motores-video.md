# Motores de video: cuál usar en cada escena (motor 0.16)

El estudio no fabrica modelos: elige el mejor motor para cada escena quieta y arma con eso. Lo hace el `director-de-movimiento` en el plan (`PLAN_MOVIMIENTO.md`).

## Los tres motores
| Motor | Quién genera | Costo | Calidad | Cuándo |
|---|---|---|---|---|
| **Flow (Veo)** | Patricio, a mano en su plan de Google | créditos de Flow | 720p o 1080p según la descarga | Por defecto: ya está pagado |
| **Higgsfield** (Kling 4.0, Seedance 2.0) | Claude, por el conector, **solo con el tope aprobado** | créditos de Higgsfield (ver tabla) | 720p o 1080p | Escenas clave (gancho, cierre) o cuando Flow falló dos veces |
| **Local** (WanGP en NVIDIA) | Quien tenga el computador con NVIDIA | gratis | hasta 720p (8 GB+) o 480p (6-8 GB) | Muchas escenas, material privado, sin gastar |

`python motor\equipo.py` dice qué motor local hay en ESTE computador (`equipo.json`: `ruta` = `nvidia_wangp`, `intel_experimental` o `ninguna`). En `intel_experimental` el modelo es solo de texto a video: **no sirve para animar la imagen del personaje**; para esas escenas se usa Flow o Higgsfield.

## Precios de referencia en Higgsfield (consultados el 21-11-2026, clip de 5 s)
| Modelo | Resolución | Créditos |
|---|---|---|
| Seedance 2.0 rápido, sin audio | 720p | 12,5 |
| Kling 4.0, imagen a video | 1080p | 18,75 |
| Seedance 2.0 estándar, sin audio | 1080p | 60 |
Siempre cotizar antes (`estimate_video_cost`); los precios cambian.

## Regla de resolución (Patricio, 21-11-2026)
Un video **no mezcla resoluciones**. Si todas las fuentes de movimiento de ese video alcanzan 1080p, todo va en 1080p (también lo de Higgsfield). Si alguna queda bajo 1080p (por ejemplo, un clip local en 720p), **todo el video va en 720p**, incluido Higgsfield. `python motor\equipo.py resolucion <res1> <res2> ...` devuelve la que corresponde, y el director de movimiento la **escribe en `proyecto.json`** (`ancho`/`alto`: 1920×1080 o 1280×720; en vertical, 1080×1920 o 720×1280) antes del render; la anota en `PLAN_MOVIMIENTO.md`. Ojo: casi todas las descargas de Flow vienen en 720p, así que muchos videos con clips de Flow terminarán en 720p.

## Regla de créditos (Patricio, 21-11-2026)
- Hasta **100 créditos de Higgsfield por video**: se puede gastar sin preguntar, pero se informa al final cuánto se usó.
- **Más de 100:** antes de generar, decir cuánto se va a usar en total y esperar el sí de Patricio para ESE video.
- **Cuenta todo:** clips, reintentos, imágenes, mejorar resolución (`upscale_video`), audio y cualquier otra herramienta de Higgsfield. Los Shorts que salen de un video largo cuentan dentro de los 100 de ese video (hasta que Patricio diga otra cosa) y usan la libreta del video largo de origen, aunque tengan su propia carpeta.
- **Libreta de gasto:** `04_CLIPS_FLOW\PLAN_MOVIMIENTO.md` lleva al final una línea `Créditos Higgsfield: usados X / cotizados Y / tope 100`. Se lee **antes** de cada generación (también en otra sesión o después de un resumen del chat) y se actualiza después de cada una con lo que muestre `balance` (lo cobrado de verdad, no la cotización). Si con la próxima generación se pasaría de 100, se para y se pregunta.
- Cuando la herramienta acepta un tope (`max_credits` u otro), se pasa el saldo que queda hasta 100.
- Flow lo genera la persona; nunca gastar créditos de Flow ni de otros servicios sin su sí.
- No subir a Higgsfield material privado (caras reales, tomas de la pareja, voces): sus términos permiten usar lo subido para entrenar fuera del plan Enterprise. Eso va al motor local.

## Recetas (lo que salió bien o mal)
Se anotan en la biblia del canal, sección «Recetas de movimiento». Primera, de la prueba del 21-11 (escena 28 de FIN-002, Kling 4.0): el estilo 2D se mantuvo, pero pedir que el personaje «se suba» a la escalera rompió la escala de los bloques y la cámara le cortó la cabeza. Indicar acciones que no cambien la escala del entorno, cámara fija o con poco movimiento, sin audio (`generate_audio: false` cuando el modelo lo permite) y duración igual a la escena (8 s si la escena dura más de 6 s).
