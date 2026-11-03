# Videos con material grabado (personas reales, viajes, baile, videos musicales)

Para cuando la persona trae tomas y fotos propias en vez de imágenes generadas. Se lee directo de su carpeta (también `G:\Mi unidad\...` de Google Drive para escritorio); no se copia ni se toca el original.

1. **Inventario:** `python inventario_tomas.py "<carpeta material>" "<proyecto>\05_REVISION\inventario"` → `inventario.csv` (resolución real con la rotación del celular, cuadros por segundo, duración, audio) y hojas con 6 fotogramas por video y miniaturas de fotos. Salta los duplicados "(1)". Mirar las hojas antes de proponer nada.
2. **Audio:** canción propia del canal con `yt-dlp -x --audio-format wav <enlace>` (solo canales de la persona) o el archivo original si lo tiene. Ritmo con librosa (golpes y BPM) y letra con los subtítulos del video (`yt-dlp --write-auto-subs --skip-download`). Elegir un tramo con principio, subida y final (normalmente el último coro).
3. **Color:** los videos de celulares recientes suelen venir en HDR10 o HLG y fuera del teléfono se ven grises. `color.py` lo detecta y lo pasa a SDR (reinhard, npl=100) y aplica un look (`natural`, `calido`, `atardecer`, `cine`). Mostrar siempre antes/después: `python color.py muestras "<salida>" "video.mp4@12" "foto.jpg" --look calido`.
4. **Montaje:** `montaje.json` en el proyecto (formato en el encabezado de `montaje_tomas.py`): cada tramo termina en un golpe del ritmo; fotos verticales llenan la pantalla con zoom suave, horizontales van completas sobre fondo desenfocado; videos con `desde_clip`, `velocidad` (0.8 = un poco lento) y `brillo`. `python montaje_tomas.py "<proyecto>"` (segundo plano con log) → `07_RENDER/<ID>_<v>_vertical.mp4` a -14 LUFS con hoja de revisión. `--tramo N` rehace solo uno.
5. **Revisar:** un fotograma al centro de cada tramo; confirmar que el final cae en un momento con sentido (abrazo, mirada) y que nadie quede cortado.

Avisos: grabaciones a 30 cuadros no dan cámara lenta real (solo suave); videos que pasaron por WhatsApp pierden mucha calidad (pedir el original). Si aparecen menores, la persona decide si van en un video público.
