# Nombres y orden de los archivos

Un nombre debe decir, sin abrir el archivo, **de qué video es, qué es, en qué orden va y qué versión es**. Así la persona, quien edite después y cada agente entienden lo mismo.

## 1. Código del video (ID)
`<CANAL>-<NNN>` — prefijo de 3 letras del canal + número correlativo de 3 cifras. Ejemplos: `FIN-002`, `FIN-003`, `MUS-001`.
- El prefijo va en la biblia del canal (`codigo: FIN`). El número: el siguiente libre mirando las carpetas del canal (`proyectos\<canal>\`).
- Carpeta del video: `<ID>_<tema-corto>` → `FIN-003_fondo-de-emergencia`. Tema en minúsculas, con guiones, sin tildes.
- Va en `proyecto.json` como `"id"` (lo crea `nuevo_proyecto.py --id FIN-003` o `--codigo FIN --numero 3`).

## 2. Imágenes (orden del guion)
`<ID>_img-<NNN>_<tema>.<ext>` → `FIN-003_img-001_dos-personas.png`, `FIN-003_img-002_puerta-abierta.png` …
- El número es el orden en que aparecen en el guion (lo fija `prompts_imagenes.md`). Una imagen que se repite en el video conserva su número.
- Variante de una misma imagen: `FIN-003_img-004b_...`. Imagen agregada después entre dos: `img-004a` (no renumerar todo).
- **Quien genera con nombre (Codex, Claude Code, un script):** guardar directo con el nombre de la tabla de prompts.
- **Quien descarga de ChatGPT (nombres al azar):** dejar las descargas en `03_IMAGENES\_entrantes` en el mismo orden de la tabla y correr `python ordenar_imagenes.py "<video>"` → muestra el plan y una hoja de control con los números; con `--aplicar` las copia con su nombre y deja `orden_imagenes.csv` (número, nombre nuevo, original). Los originales no se tocan. Revisar la hoja de control antes de aplicar: si una imagen quedó fuera de lugar, corregir con `--inicio` o renombrar esa copia.

## 3. Clips de Flow
- Pedir a Flow el título exacto `escena_NNN` (NNN = número de escena de la receta). Si bajan con otro nombre, `asignar_clips.py` los reconoce por su primer cuadro y crea `escena_NNN.mp4` dentro de `04_CLIPS_FLOW` (la carpeta ya dice de qué video es).

## 4. Voz
`02_VOZ\<ID>_voz-parte1.mp3`, `..._voz-parte2.mp3` (se unen en orden de nombre). La voz sin pausas que crea el motor: `02_VOZ_RECORTADA\voz_recortada.wav`.

## 5. Lo que sale del estudio (siempre con ID y versión)
| Archivo | Nombre |
|---|---|
| Video YouTube (subtítulos aparte) | `FIN-003_v1_youtube.mp4` |
| Video con subtítulos grabados (TikTok, subida directa) | `FIN-003_v1_con-subtitulos.mp4` |
| Subtítulos para subir a YouTube | `FIN-003_v1_subtitulos.srt` |
| Capítulos para la descripción | `FIN-003_v1_capitulos.txt` |
| Shorts / TikTok / Reels | `FIN-003_v1_short-1_9x16.mp4`, `..._short-2_9x16.mp4` |
| Miniaturas | `08_PUBLICAR\FIN-003_v1_miniatura-1.jpg` |
| Borrador para aprobar | `FIN-003_v1_borrador-60s.mp4` |

## 6. Versiones
- `v1` es el primer render completo. **Sube la versión** (`"version": "v2"` en `proyecto.json`) cada vez que cambia lo que se ve u oye en el video final: imágenes, orden, clips, voz, efectos, subtítulos. Así nunca se pisa una versión que alguien ya vio.
- Arreglos que no cambian el contenido (volver a exportar igual) no suben versión.
- Cada versión se anota en `00_ESTADO.md` → tabla **Versiones**: versión, fecha, qué cambió, quién la aprobó. La versión publicada se marca "PUBLICADA".
- Las versiones viejas no se borran sin permiso; cuando el video se publicó, se puede ofrecer moverlas a `07_RENDER\anteriores`.
