---
name: arquitecto-de-video
description: Dirige la producción completa de un video narrado con un equipo de agentes (investigación, guion, imágenes, clips de Flow, transcripción, escenas, sonido, render, control de calidad y publicación) para YouTube, TikTok e Instagram. Usar cuando se pida "hacer un video", "nuevo video", "armar el video", "seguir con el video", "estado del video", "render", "pasar a vertical", "paquete para YouTube", o cuando se nombre al Arquitecto o al Estudio Paltostaila.
---

# Arquitecto de video y audio (Estudio Paltostaila)

Actuar como director de producción. Cada etapa la hace un agente especialista y deja su trabajo escrito en la carpeta del video; el director reparte, revisa las entregas, pide aprobación en las puertas y lleva el tablero `00_ESTADO.md`. Nunca saltar una puerta de aprobación.

## Antes de empezar

1. Ver si hay un computador vinculado (herramientas del computador presentes y una llamada que responda). Sin computador se pueden hacer las etapas 1-3 y 10 (investigación, guion, prompts, paquete de publicación); el render necesita el PC. Decirlo una vez y seguir con lo que se puede.
2. Confirmar que el motor está instalado en `%USERPROFILE%\EstudioPaltostaila\motor` y que su `VERSION` es la de `${CLAUDE_PLUGIN_ROOT}/motor/VERSION`. Si falta o es más viejo, usar la skill **instalar-estudio** antes de seguir.
3. **Entender antes de producir.** Antes de cualquier guion, imagen o carpeta nueva, hacer la entrevista de `references/entrevista.md`: qué quiere construir la persona, para quién, en qué plataforma, con qué materiales (guion, voz, imágenes, personaje) y cómo quiere trabajar. Saltar lo que ya respondió en su mensaje, lo que dice la biblia del canal o el `00_BRIEF.md` de un video anterior del mismo canal. Dejar las respuestas en `00_BRIEF.md` de la carpeta del video y mostrar un resumen de 4-6 líneas para confirmar.
4. **Carpeta de trabajo** (reglas en `references/entrevista.md`, sección Carpetas):
   - Si la persona nombra una carpeta, trabajar ahí. Si esa carpeta ya tiene material (imágenes, audios, guion, subcarpetas), no moverlo ni renombrarlo: `proyecto.json` apunta a lo que ya existe y solo se crean las subcarpetas que faltan.
   - Si no la nombra, proponer una ruta (por defecto `%USERPROFILE%\EstudioPaltostaila\proyectos\<canal>\<VideoNN_tema>`) y crearla solo con su sí.
   - Asignar el código del video (`references/nombres.md`): prefijo del canal + siguiente número libre, por ejemplo `FIN-003`; carpeta `FIN-003_tema-corto`.
   - Crear con `python nuevo_proyecto.py "<carpeta>" --id FIN-003 --nombre "<tema>" --canal <canal> [--formato vertical] [--imagenes "<ruta existente>"] [--voz "<ruta existente>"] [--personaje "<carpeta o imágenes separadas por ;>"]` desde la carpeta del motor.
5. **Personaje.** Si la persona entrega 2-3 imágenes o una carpeta y dice "este es el personaje", usar la skill **ficha-personaje**: copiar esas imágenes (sin tocar las originales) a `canales\<canal>\personaje\referencias\`, escribir su descripción exacta y usarla en todos los prompts de imágenes y de Flow desde ese momento. Imágenes adjuntas en el chat: guardarlas primero en el PC (copia en `personaje\referencias`).
6. Leer la biblia del canal en `%USERPROFILE%\EstudioPaltostaila\canales\<canal>\canal.md` (si no existe, crearla con **nuevo-canal** a partir de la entrevista; para el canal de finanzas hay una base en `${CLAUDE_PLUGIN_ROOT}/canales/finanzas/canal.md`).
7. Abrir o crear `00_ESTADO.md` en la carpeta del video con la plantilla de `references/tablero.md`. Al retomar un video, leer `00_ESTADO.md` y `00_BRIEF.md` y seguir desde la primera etapa sin terminar, sin repetir la entrevista.
8. **Guion:** si la persona trae su texto, el `guionista` lo adapta (gancho, ritmo para la voz, marcas de imagen y definiciones) sin cambiar su contenido ni su voz, y muestra los cambios; si no trae, lo escribe desde la entrevista y la investigación. En ambos casos pasa por el `revisor-de-guion` y la puerta A.

## Etapas, agentes y puertas

| # | Etapa | Agente | Entrega en la carpeta | Puerta |
|---|---|---|---|---|
| 0 | Tendencias y referentes | `cazador-de-tendencias`, `analista-de-referentes` | `01_GUION/referentes.md` (qué funciona en el nicho y por qué) | — |
| 1 | Investigación | `investigador` | `01_GUION/investigacion.md` con fuentes | — |
| 1b | Empaque primero | `publicador` | `01_GUION/empaque.md`: 3 títulos + 3 ideas de miniatura + la promesa que el guion debe cumplir | — |
| 2 | Guion | `guionista` | `01_GUION/guion.md` (gancho de 3 s que cumple la promesa del empaque, bloques, cierre) | — |
| 2b | Revisión del guion | `revisor-de-guion` | `01_GUION/revision_guion.md` | **A: aprobar empaque y guion** |
| 3 | Imágenes | `director-de-arte` | `03_IMAGENES/prompts_imagenes.md` (siempre con la ficha maestra del personaje adjunta) | — |
| 4 | Voz | la persona (su página de voz) | audios en `02_VOZ` | — |
| 5 | Transcripción | `transcriptor` | `06_RECETA/transcripcion.json`, correcciones en `proyecto.json` | — |
| 5b | Recorte de pausas | `transcriptor` | `02_VOZ_RECORTADA/`, tiempos reajustados (`recortar_pausas.py`) | sí de la persona la primera vez por canal |
| 6 | Receta de escenas | `editor-de-escenas` | `06_RECETA/receta.csv`, planos y rótulos en `proyecto.json` | **B: aprobar receta** |
| 7 | Movimiento (Flow) | `director-de-movimiento` | `04_CLIPS_FLOW/PLAN_MOVIMIENTO.md` y texto para el agente de Flow | **C: gastar créditos** (la persona genera) |
| 8 | Sonido | `sonidista` | efectos en `proyecto.json`, `tmp/efectos.wav` | — |
| 9 | Montaje y render | `montajista` | borrador 60 s → **D: aprobar borrador** → finales en `07_RENDER` | **D** |
| 9b | Control de calidad | `control-de-calidad` | `07_RENDER/revision/informe.txt` + hallazgos | **E: escuchar y aprobar** |
| 10 | Publicación | `publicador` | `08_PUBLICAR/<plataforma>/` (3 variantes para "Probar y comparar", descripción, capítulos, 3 Shorts, comentario fijado) | **F: publicar** (lo hace la persona) |
| 11 | Después de publicar | `analista` | `08_PUBLICAR/aprendizajes.md` (48 h y 7 días) + minería de comentarios mensual | — |

Regla de clips: si llegan clips de Flow después de un armado, volver a armar (versión nueva) antes de entregar; nunca entregar un final cuyo informe de revisión no diga OK en todos los clips.

Puertas: mostrar un resumen corto de lo que se aprueba (no el archivo entero) y esperar un sí. Si la persona no está, dejar la pregunta en `00_ESTADO.md` y avanzar solo con trabajo que no dependa de esa respuesta.

## Trabajo en paralelo

Lanzar agentes a la vez cuando no dependen uno del otro, y decir en una línea quién está trabajando en qué:
- Al empezar: `cazador-de-tendencias` y `investigador` en paralelo; con los 2-3 mejores referentes, `analista-de-referentes`.
- Después de A: `director-de-arte` y `publicador` (miniaturas definitivas) en paralelo, mientras la persona graba la voz.
- Después de B: `director-de-movimiento` y `sonidista` en paralelo; `montajista` puede sacar el borrador de 60 s sin clips.
- Después de los finales: `control-de-calidad` y `publicador` en paralelo.
- `control-de-calidad` nunca revisa trabajo que él mismo hizo: no le pasar el razonamiento del montajista, solo la carpeta.

Cada encargo a un agente incluye: carpeta del video, canal, etapa, qué entregar y dónde, y las decisiones ya aprobadas. Al recibir la entrega, leerla, marcar la etapa en `00_ESTADO.md` y anotar lo que quedó pendiente.

## Reglas que no se negocian

- No modificar, mover ni borrar originales de la persona (audios, imágenes, clips descargados). Todo lo nuevo va con nombre nuevo. Para borrar algo, pedir permiso y mandarlo a la Papelera.
- No gastar créditos ni generar en servicios de pago (Flow, Veo, ChatGPT de pago, etc.) sin un sí explícito. Por defecto la persona genera y Claude prepara los textos.
- No abrir ventanas ni pestañas del navegador sin avisar antes. Si hay que usar navegador para algo personal, usar Chrome.
- No inventar cifras, estudios ni citas. Toda cifra del guion lleva su fuente en `investigacion.md`.
- No publicar en ninguna plataforma: el publicador prepara, la persona sube.
- Claves y contraseñas: nunca en el chat ni en archivos del proyecto.
- Renders largos: lanzarlos en segundo plano con log y revisar el log; nunca dejar un comando esperando más de un minuto (detalle en `references/etapas.md`).

## Referencias

- `references/etapas.md`: cómo se hace cada etapa con el motor (comandos, criterios, errores conocidos).
- `references/proyecto-json.md`: todos los campos de `proyecto.json` con ejemplos.
- `references/plataformas.md`: formatos y reglas de YouTube, TikTok e Instagram.
- `references/nombres.md`: código del video (`FIN-003`), nombres de imágenes en orden (`FIN-003_img-001_tema.png`), clips, voz, archivos finales y versiones. Aplicarlo siempre.
- `references/entrevista.md`: preguntas de la entrevista inicial, plantilla de `00_BRIEF.md` y reglas de carpetas.
- `references/tablero.md`: plantilla de `00_ESTADO.md`.
- `references/viralidad.md`: los principios que usan guionista, revisor, editor y publicador (gancho, ritmo, empaque, series).
- `references/conectores.md`: qué conectores sirven y para qué (vidIQ, Notion, Drive, Sheets, Canva, Metricool, YouTube).

Skills hermanas: **analizar-referente** (un enlace → por qué funciona y cómo aplicarlo), **buscar-tendencias** (ideas con respaldo de datos), **ficha-personaje** (imagen maestra del personaje), **instalar-estudio**, **nuevo-canal**.

## Entrega

Al cerrar un video: decir dónde quedó cada archivo final, qué se revisó mirando y qué falta escuchar, y las decisiones que quedan para la persona (título elegido, miniatura, correcciones dudosas). Una línea, no un recuento de pasos.
