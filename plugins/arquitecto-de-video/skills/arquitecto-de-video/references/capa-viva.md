# Capa viva: subtítulos dinámicos y elementos animados (vivo.py)

Lo que hace que un video no se vea "editado igual que todos": subtítulos que entran palabra por palabra con el estilo propio del canal y elementos que aparecen justo en la palabra que los nombra. Todo sale del motor como dibujo vectorial ASS (libass): no se usan stickers, clips ni memes de terceros (contenido reutilizado y derechos, ver `monetizacion.md`).

## Cuándo se activa
- `"subtitulos": {"estilo": "vivo"}` en `proyecto.json` → `_con-subtitulos.mp4` y los Shorts llevan subtítulos dinámicos (el `.srt` para subir a YouTube sigue saliendo igual).
- `"elementos": [...]` → los elementos salen en **las dos** versiones (`_youtube.mp4` y `_con-subtitulos.mp4`) y en los Shorts que los incluyan (en un corte vertical `"elementos": false` los apaga).
- Sin ninguno de los dos, el motor hace lo mismo de antes.

## Estilo de subtítulos
```json
"subtitulos": {"estilo": "vivo", "preset": "finanzas", "palabras": 3,
               "palabras_clave": ["urgencia", "fondo de emergencia"],
               "posicion": 0.84, "posicion_vertical": 0.70,
               "fuente_viva": "Arial Black", "tamano_vivo": 78,
               "color_texto": "FFFFFF", "color_clave": "FFD23F", "color_clave2": "6AD15B",
               "entrada": "pop", "destellos": true, "caja": false}
```
- Presets: `finanzas` (blanco, palabra activa amarilla, clave verde con destellos, 3 palabras), `rosa` (1 palabra, rosa, estilo reel), `bachata` (cálido, sube), `curso` (caja de fondo, celeste, sobrio), `documental` (serif, 4 palabras, fundido). Cualquier campo de arriba pisa el preset.
- `palabras`: 1 a 4 a la vez. Los grupos se cortan también en la puntuación y en pausas de más de 0,35 s; en vertical como máximo 14 caracteres por grupo.
- Palabras clave: las de la lista (también frases de varias palabras) y todo número, % o $ salen en `color_clave2`, un poco más grandes y con destellos.
- Posición: fracción del alto (0 = arriba). En vertical se fuerza la zona segura (entre 0,14 y 0,76) y el tamaño se multiplica por 1,25. En cursos con la cara al centro, subir o bajar para no tapar la boca.
- Cada canal debería tener su preset en la biblia (`nuevo-canal`); no usar el mismo estilo en todos.

## Elementos
Cada elemento entra en una frase de la transcripción (`"en": "texto exacto"`; si la frase se repite en el guion: `{"frase": "...", "despues": "otra frase anterior"}`; también `{"segundo": 42.5}` o `"desfase": 0.4`).

| tipo | campos | uso |
|---|---|---|
| `icono` | `icono`: reloj, dinero, alerta, check, corazon, flecha (`giro` en grados), avion, lupa, destello, estrella; `pos`, `dura`, `tam`, `color` | subrayar una idea en 1-2 s |
| `lista` | `titulo`, `items` (texto o `{"texto", "frase"}` para que cada línea se escriba cuando se dice), `pos`, `dura` | tarjeta de papel escrita a mano, línea por línea |
| `fichas` | `items`, `frases` (o `cada` en segundos), `colores` | cadena A → B → C (en vertical, en columna) |
| `lluvia` | `simbolo`: billetes o confeti; `cantidad`, `dura` | ganancias, celebración |
| `progreso` | `actual`, `total`, `etiqueta` (CREENCIA, PREGUNTA, PASO), `en` y `hasta` (frases: dura todo el bloque), `tarjeta` (true: 1,2 s el número grande al centro, encima del video), `pos` | videos con lista o pasos: «CREENCIA 2 DE 4» chico en una esquina con puntos de avance. Evita caras y texto como los demás; en los Shorts aparece aunque el bloque haya empezado antes del corte. Si un rótulo ya dice «CREENCIA 2», que el contador entre después (`"en": {"frase": …, "desfase": 5.2}`): no repetir un texto que ya está en pantalla |
| `texto` | `texto`, `color`, `dura`, `pos`, `tam`, `entrada` (ver abajo) | un número o palabra enorme: "x2", "-30%", "FOMO" |

Entradas (`entrada` en elementos `texto`; las de línea también en `subtitulos.entrada`). Aprendidas de las 20 animaciones de texto que describe la ayuda pública de Canva y hechas con etiquetas ASS propias; se acepta el nombre en español o en inglés:

| entrada | inglés | movimiento | sirve en subtítulos |
|---|---|---|---|
| `pop` | Pop | crece, rebota y se mueve un poco | sí |
| `fundido` | Fade | aparece de a poco | sí |
| `subir` / `bajar` | Rise / Shift | sube (o baja) a su lugar | sí |
| `base` | Baseline | sale desde una línea invisible, rápido | sí |
| `panear` / `patinar` / `deriva` | Pan / Skate / Drift | entra desde la izquierda, desde la derecha, o lento con el viento | sí |
| `voltereta` | Tumble | gira desde cabeza abajo | sí |
| `rebote` | Bounce | cae y rebota | sí |
| `pisoton` | Stomp | llega gigante y golpea la pantalla | sí |
| `album` | Scrapbook | aparece inclinado y se tuerce al otro lado | sí |
| `neon` | Neon / Flicker | parpadea como un letrero | sí |
| `respirar` | Breathe | late suave todo el tiempo | sí |
| `maquina` | Typewriter | letra por letra | no |
| `estallido` | Burst | letra por letra con un golpe | no |
| `rodar` | Roll | letras que caen como tragamonedas | no |
| `ascender` | Ascend | palabra por palabra hacia arriba | no |
| `tectonico` | Tectonic | sacudida izquierda-derecha | no |
| `bloque` | Block | un bloque de color cruza y deja el texto | no |
| `desliza`, `sello`, `brillo` | — | propias del estudio | sí |

Regla de uso (de las guías de Canva y de la práctica): animar las palabras clave, no todo; una o dos entradas por canal, siempre las mismas, para que el video tenga identidad.

Posiciones: `arriba-izq`, `arriba-der`, `centro`, `izquierda`, `derecha`, `abajo-izq`, `abajo-der` o `[x, y]` en fracciones. En vertical todo queda fuera de la columna de botones de la derecha.

Ritmo: un elemento cada 15-40 s en videos largos (más seguido en el gancho y en los cierres de bloque); en Shorts y reels, algo nuevo cada 2-4 s. No poner un elemento donde ya hay un rótulo.

## Probar sin renderizar todo
`python vivo.py "<proyecto>" --prueba 90-140 [--vertical] [--zona] [--fotos 97,101]` → `07_RENDER/<ID>_<v>_vivo-prueba(-9x16).mp4` con la voz, sobre el armado si existe o sobre un fondo neutro si todavía no hay imágenes. Sirve para elegir el estilo antes de tener las imágenes. Si una frase no se encuentra, sale `AVISO elemento sin frase` y ese elemento se salta.

## No tapar caras (0.11.1)
`terminar.py` mira el video armado (`tmp/solo_video.mp4`) al inicio, a la mitad y al final de cada elemento con `caras.py`. Busca tres cosas:
- caras reales;
- cabezas del personaje dibujado (círculos blancos);
- globos y texto de la imagen.

Si la posición pedida tapa algo de eso, el elemento se corre a la zona libre más cercana. Lo que se movió queda en `tmp/capa_viva_lugares.txt`.
- **Fijar un elemento:** `"fijo": true` lo deja exactamente donde se pidió.
- **Apagarlo todo:** `"subtitulos": {"evitar_caras": false}`.
- **Ignorar el texto de la imagen:** `"evitar_texto": false` hace que solo se eviten caras y cabezas.
- **Revisar a mano un cuadro:** `python caras.py "<video>" 12.5` deja una imagen con lo que encontró marcado.

Por ahora se aplica en el video 16:9. En los Shorts, los elementos van en la columna central de la zona segura; revisar los cuadros igual.
