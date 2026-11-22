# Idiomas: español, inglés y portugués en cualquier dirección

Cada canal anota en su biblia su idioma principal, sus mercados y cómo maneja los otros idiomas. Un video puede nacer en un idioma y pasar a otro; el estudio no asume que todo es inglés → español.

## Decisión por canal: pistas de audio o canal aparte
| Opción | Cómo es | Conviene cuando | Cuidado |
|---|---|---|---|
| **Un canal con pistas de audio** | El mismo video lleva audio y títulos en varios idiomas (YouTube: pistas de audio y títulos traducidos; el doblaje automático de YouTube se deja en «publicar manualmente» para revisarlo) | El contenido sirve igual en los dos mercados y el canal ya tiene señales | Una pista mala baja el promedio de todo el video; cada pista se revisa a mano |
| **Canal aparte por idioma** | Otro canal, otra biblia (puede compartir personaje y estilo) | El contenido necesita ejemplos, datos o leyes locales distintas (finanzas por país, por ejemplo) | Cada canal parte de cero y necesita sus propias horas para monetizar; la regla de actividad desde 2027 exige subir seguido en cada uno |
| **Solo subtítulos** | Un archivo `.srt` traducido subido como pista | Prueba barata antes de decidir | No cuenta como versión en otro idioma para el buscador de la misma forma que una pista de audio |

Por defecto: probar primero con pistas o subtítulos en 3-4 videos, medir 60 días y recién ahí abrir un canal aparte.

## Qué se traduce en cada video
1. **Guion:** se adapta, no se traduce palabra por palabra. Cifras, monedas, leyes, instituciones y ejemplos se cambian por los del mercado nuevo (por ejemplo, Chile → Brasil: CMF → CVM/Banco Central do Brasil, pesos → reales), con fuente nueva en `investigacion.md`.
2. **Voz:** con la voz del canal en ese idioma (`voces.py` y el mapa de voces de `doblaje.py` desde el motor 0.15; voz local Kokoro si el canal la usa). La licencia de la voz se anota en `licencias\registro.md`. Nunca se clona una voz sin el pedido expreso de su dueño.
3. **Texto dentro de las imágenes:** `revisar_idioma.py` encuentra el texto que no está en el idioma destino; `texto_imagen.py` lo traduce o lo borra; `reemplazar_imagen.py` cambia la imagen en el video terminado.
4. **Subtítulos, rótulos, capítulos y capa viva:** desde la transcripción nueva.
5. **Título, descripción y miniatura:** se escriben para el buscador de ese idioma (no se traducen): la prueba de las 3 búsquedas del publicador se hace en el idioma destino.
6. **Ganchos:** la fórmula se mantiene; el ejemplo se reescribe para ese público.

## Doblar un video ya terminado
`doblaje.py` (desde el 0.15: `--origen` y `--destino` en es, en o pt; ver `motor-0150-general.md`):
1. `preparar` transcribe y deja los segmentos.
2. Claude llena la traducción con frases que se puedan decir en el mismo tiempo (unos 15 caracteres por segundo en español; ajustar por idioma).
3. `voz` calza cada frase; para publicar, las voces van mejor generadas en la página de voz con licencia y cargadas con `--desde-archivos`.
4. `mezclar` deja el video con la voz nueva (con o sin el audio original debajo) y `--quemar` para la versión con subtítulos.

## Portugués
- Brasil y Portugal son mercados distintos (vocabulario, ejemplos, voz). La biblia dice cuál.
- El portugués queda para cuando el canal en español tenga ritmo propio, salvo que la biblia diga otra cosa.

## Mercados y monetización
Dónde se puede cobrar depende de dónde viven ustedes, no de dónde está el público (`mercados.md` del gerente). Un público en otro país sí cambia cuánto paga cada vista y a qué hora publicar.
