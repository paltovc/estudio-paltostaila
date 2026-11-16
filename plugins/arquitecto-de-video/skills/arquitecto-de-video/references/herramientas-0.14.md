# Herramientas nuevas del motor 0.14 (14 al 16-11-2026)

Usarlas antes de leer salidas largas: ahorran uso y dan resultados comprobables.

## Al empezar una sesión
- `python motor\ficha.py tabla` → estado de todos los videos en una tabla corta (escrita desde los archivos de cada proyecto). Leer esto primero, no los documentos largos.
- En el PC hay un `EstudioPaltostaila\CLAUDE.md` con reglas, rutas y comandos en una página.

## Un comando por etapa: `cadena.py`
`python motor\cadena.py "<proyecto>" revisar|escuchar|shorts|final`
- `revisar`: evaluar → terminado → escuchar (sin transcribir) → ficha. Solo lee.
- `escuchar`: escucha completa (transcribe la mezcla; tarda 2-3 min por minuto de audio).
- `shorts`: vertical → terminado → ficha.
- `final`: terminar → vertical → evaluar → terminado → escuchar → ficha (arma la versión).
Deja `trabajo\cadenas\<base>_<etapa>_<fecha>.md` (resumen de ~15 líneas) y `.log` (todo). Leer el `.md`.
Lo largo se lanza con un `.cmd` y `Start-Process` (la terminal se corta a los ~58 s).

## El oído: `escuchar.py`
`python motor\escuchar.py "<proyecto>" [--video X] [--salida D] [--sin-transcribir] [--comparar otro.mp4]`
Solo lee. Mide lo que se puede medir del audio final:
- se entiende: vuelve a transcribir la mezcla (WhisperX local) y la compara con la voz; marca cada tramo distinto y si hay un efecto cerca;
- efectos: si cada efecto de la hoja de cues (o de su pista) suena en su momento, con qué desfase y cuántos dB queda bajo la voz;
- defectos: saturación, clics aislados, silencios largos, saltos en las uniones de audios de voz, pérdida en mono (parlante del celular), LUFS y pico real;
- comparación con otra versión segundo a segundo;
- imágenes del sonido (espectrograma) de cada tramo marcado, para mirarlas.
No juzga gusto: deja una lista corta de minutos para que la persona escuche.
Primera escucha real: FIN-002 v13, 99,4 % de 1.197 palabras igual en la mezcla, sin problemas medibles.

## Huellas y puertas
- `terminado.py` guarda `terminado_<base>.json` con el sha256 de cada video revisado (ruta relativa; `celu/<nombre>` para la copia del celular) y no firma si un video cambia mientras revisa. Punto 2: el video con subtítulos dura lo mismo que el de YouTube (±0,2 s).
- `evaluar.py` guarda el sha256 del video evaluado. Una evaluación sin huella no vale.
- Nota mínima para publicar (decisión de Patricio, 15-11-2026): **8 el largo, 7 los Shorts**, clase A o B.
- `vertical.py`: los Shorts salen en yuv420p rango de TV.

## Sonido (0.14)
- Efectos alineados por «ataque» o «pico» solo en proyectos nuevos (`nuevo_proyecto.py`); los existentes siguen con «inicio».
- Hoja de cues por video en `06_RECETA\hoja_cues_<base>.csv` (tiempo, archivo, volumen, alineado, fuente, licencia).
- Punto 13 de `terminado.py`: pico real -1 dBTP o menos en todos los videos de la versión.

## Reglas de movimiento, lectura y sonido
En el PC: `EstudioPaltostaila\referencias\reglas_movimiento_lectura_sonido.md` (curvas y tiempos, tiempo de lectura 0,5 s + 0,3 s por palabra, letra mínima 2,6 % del lado corto, tramos muertos, subtítulos, mezcla). Son propuestas: no cambian los videos hasta que Patricio apruebe cada comprobación.
