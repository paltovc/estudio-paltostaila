# Videos con material grabado (personas reales, viajes, baile, videos musicales)

Para cuando la persona trae tomas y fotos propias en vez de imágenes generadas. Se lee directo de su carpeta (también `G:\Mi unidad\...` de Google Drive para escritorio); no se copia ni se toca el original.

1. **Inventario:** `python inventario_tomas.py "<carpeta material>" "<proyecto>\05_REVISION\inventario"` → `inventario.csv` (resolución real con la rotación del celular, cuadros por segundo, duración, audio) y hojas con 6 fotogramas por video y miniaturas de fotos. Salta los duplicados "(1)". Mirar las hojas antes de proponer nada.
2. **Audio:** canción propia del canal con `yt-dlp -x --audio-format wav <enlace>` (solo canales de la persona) o el archivo original si lo tiene. Ritmo con librosa (golpes y BPM) y letra con los subtítulos del video (`yt-dlp --write-auto-subs --skip-download`). Elegir un tramo con principio, subida y final (normalmente el último coro).
3. **Color:** los videos de celulares recientes suelen venir en HDR10 o HLG y fuera del teléfono se ven grises. `color.py` lo detecta y lo pasa a SDR (reinhard, npl=100) y aplica un look (`natural`, `calido`, `atardecer`, `cine`). Mostrar siempre antes/después: `python color.py muestras "<salida>" "video.mp4@12" "foto.jpg" --look calido`.
4. **Montaje:** `montaje.json` en el proyecto (formato en el encabezado de `montaje_tomas.py`): cada tramo termina en un golpe del ritmo; fotos verticales llenan la pantalla con zoom suave, horizontales van completas sobre fondo desenfocado; videos con `desde_clip`, `velocidad` (0.8 = un poco lento) y `brillo`. `python montaje_tomas.py "<proyecto>"` (segundo plano con log) → `07_RENDER/<ID>_<v>_vertical.mp4` a -14 LUFS con hoja de revisión. `--tramo N` rehace solo uno.
5. **Revisar:** un fotograma al centro de cada tramo; confirmar que el final cae en un momento con sentido (abrazo, mirada) y que nadie quede cortado.

Avisos: grabaciones a 30 cuadros no dan cámara lenta real (solo suave); videos que pasaron por WhatsApp pierden mucha calidad (pedir el original). Si aparecen menores, la persona decide si van en un video público.

Extras aprendidos de CapCut para `montaje_tomas.py` (por tramo): `"rampa": [1.0, 0.35]` hace una curva de velocidad (la toma pasa a cámara lenta de a poco, ideal en el golpe de la música) y `"estabilizar": true` quita el temblor de la mano (filtro deshake). En `color.py` y en `"look"` se puede usar una LUT propia: `"look": "lut:C:\\ruta\\mi_look.cube"`. Efectos por tramo (`efectos.py`): `"efectos": ["brillo"]`, `"congelar": {"en": 1.2, "dura": 0.8}`, `"fluido": true`; voz más limpia en `grabado.py` con `"limpiar_voz": "media"` (o suave, fuerte, radio). Transiciones entre tramos (giro, golpe, barrido, glitch… las 68 de `transiciones.md`): `"transicion": ["golpe", 8]` en un tramo o `"variar_transiciones"` en la raíz; el tramo nuevo sigue entrando en su golpe.

# Personas hablando a cámara (cursos, clases, tutoriales, testimonios): grabado.py

Para cuando el material son tomas de alguien hablando y hay que elegir lo bueno y dejar los cortes suaves. El texto manda: se edita leyendo lo que se dijo, no mirando una forma de onda.

1. **Proyecto:** `nuevo_proyecto.py` como siempre; en `proyecto.json` → `"grabado": {"material": "<carpeta de tomas>", "look": "natural"}` y el formato en `video` (1920x1080 para el curso, 1080x1920 si es un reel). La carpeta se lee, nunca se toca.
2. **Transcribir:** `python grabado.py "<proyecto>" transcribir` (segundo plano con log; unos 2-3 min por minuto en CPU). Deja una transcripción por toma en `06_RECETA/tomas/` y `06_RECETA/tomas.md`: todas las frases en orden, marcando ✗ las que se vuelven a decir más adelante (tomas fallidas). Propone `orden_propuesto.json` quedándose con la última versión de cada frase.
3. **Elegir tomas:** leer `tomas.md`, compararlo con el guion o el índice del curso si existe y escribir `grabado.orden` con las piezas buenas (archivo, desde, hasta, nota). Mostrar a la persona la lista corta de qué se queda y qué se va antes de armar. Sin `orden`, se usa el propuesto.
4. **Cortar:** `python grabado.py "<proyecto>" cortar` quita muletillas (eh, em, mm… y las de `muletillas_extra`, por ejemplo "o sea"), trabas ("el el", palabras cortadas) y silencios de más de `pausa_max` (0,45 s), dejando `margen` (0,08 s) a cada lado. Escribe `06_RECETA/cortes.md` (qué se quitó y dónde) y la transcripción del video ya editado, lista para subtítulos. WhisperX a veces "limpia" las muletillas al transcribir: igual se cortan porque quedan como silencio.
5. **Armar:** `python grabado.py "<proyecto>" armar [--borrador 60]`:
   - mismo color en todas: `look` de `color.py` (incluye pasar HDR del celular a SDR) y brillo/saturación igualados a la toma de referencia (`referencia_color` o la más usada);
   - cortes que no se notan: micro-fundido de 12 ms en el audio de cada corte; en un corte dentro del mismo plano, el encuadre alterna entre normal y un acercamiento (`punch`, 1,08) para que no se vea el salto;
   - cortes J/L (`jl`, por ejemplo 0,15 s) solo entre planos distintos (otra cámara, otra toma, material de apoyo): la imagen cambia un poco antes que el sonido. En el mismo plano no se usa porque la boca no calzaría;
   - voz limpia (`limpiar_voz`): filtro de graves, reducción de ruido suave y compresión leve.
   Deja `tmp/solo_video.mp4` y `02_VOZ/<ID>_voz-grabado.wav`, y apunta `proyecto.json` a esa voz.
6. **Terminar:** `terminar.py` (volumen a -14 LUFS, subtítulos con el preset `curso` u otro, rótulos, capa viva) y `vertical.py` para los cortes. Revisar en la sala de edición (`sala-de-edicion.md`) con formato celular y zona segura para confirmar que los subtítulos no tapan la boca.


# Estilo reel y redes para persona a cámara (motor 0.15, pendiente de prueba)

Sobre el flujo de `grabado.py` de arriba, el motor 0.15 suma (detalle, campos y comandos en `motor-0150-camara.md`):
- **Luz automática** (`luz.py`): exposición, balance de blancos y realce suave de la cara, después del paso de HDR a SDR y antes del look.
- **Zooms de énfasis** en palabras clave o segundos marcados, distintos del punch que tapa cortes.
- **Ángulos virtuales** (plano general, medio y cerrado) desde una sola cámara, sin cortar la cabeza.
- **Material de apoyo** (`apoyo.py`): propone qué imagen o clip va cuando se nombra algo (`06_RECETA/apoyo_propuesto.json`, se aprueba) y lo inserta completo, en esquina o dividido.
- **Sonidos en subtítulos y elementos**, apagados por defecto.
La receta de edición del canal (`recetas-de-edicion.md`, receta 1 «Reel de persona hablando») dice cuánto de cada cosa usar. Revisar siempre en la sala con formato celular.
