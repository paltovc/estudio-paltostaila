# Etapas con el motor

Motor: `%USERPROFILE%\EstudioPaltostaila\motor` (scripts de Python + ffmpeg). Todos reciben la carpeta del video como primer argumento y leen su `proyecto.json`. Ejecutarlos desde la carpeta del motor.

## Cómo ejecutar en el PC sin quedarse esperando

Las herramientas del computador cortan la espera a los ~60 s. Para todo lo que tarda más (transcribir, render, vertical):

```powershell
cd "$env:USERPROFILE\EstudioPaltostaila\motor"
Start-Process cmd -ArgumentList '/c', 'render.cmd "C:\ruta\video" > "C:\ruta\video\07_RENDER\log_render.txt" 2>&1' -WindowStyle Hidden
```

Los scripts sueltos lanzados así necesitan `set PYTHONIOENCODING=utf-8` antes (render.cmd ya lo trae) para que el log muestre bien las tildes. Después leer el log cada tanto (`Get-Content ... -Tail 15`). En PowerShell usar `npm.cmd`/`npx.cmd` (la política de scripts bloquea `npm`). Si una llamada se corta por tiempo, no repetirla a ciegas: revisar primero si el proceso sigue (`Get-Process python`) o si ya dejó sus archivos.

Tiempos de referencia (notebook i7 de 11.ª gen.): render completo de 8 min ≈ 20 min; borrador de 60 s ≈ 3 min; transcripción de 8 min con large-v3 en CPU ≈ 15-25 min.

## 0. Tendencias y referentes (`cazador-de-tendencias`, `analista-de-referentes`)
- `python tendencias.py "<búsqueda>"` (`--shorts`, `--recientes`, `--top N`): videos que superan la mediana de su propio canal ("x canal"). Deja la tabla en `EstudioPaltostaila\tendencias\`. Tarda 1-3 min: segundo plano con log.
- `python referente.py "<enlace>"` (`--sin-video` para solo datos y comentarios; `--transcribir` si no hay subtítulos): números, comparación con el canal, cortes por minuto, gancho (6 cuadros de 0-3 s), hoja de 24 cuadros, miniatura, subtítulos con tiempos y los 200 comentarios con más likes. Deja todo en `EstudioPaltostaila\referentes\<plataforma>_<id>\`.
- Error 429 de YouTube (demasiadas solicitudes): esperar unos minutos y repetir; no insistir en bucle.
- Resumen para el video en curso: `01_GUION/referentes.md` (qué tomar y qué no, con enlaces).

## 1. Investigación (`investigador`)
Tema, público, 3-5 preguntas que la persona espectadora se hace, datos con fuente (organismo oficial, regulador, estudio con fecha). Separar "dato verificado" de "idea u opinión". Nada de cifras sin fuente.

## 1b. Empaque primero (`publicador`)
Antes del guion: `01_GUION/empaque.md` con 3 títulos (frase de búsqueda + beneficio o curiosidad), 3 ideas de miniatura (máximo 3 palabras, emoción del personaje, objeto) y "la promesa": lo que quien hace clic espera ver en los primeros 3 s. Se aprueba junto con el guion en la puerta A.

## 2. Guion (`guionista`)
- Gancho en los primeros 5 s: una situación concreta o una pregunta, nunca "hola, bienvenidos".
- Bloques de 60-90 s con una idea cada uno; cada bloque abre con una frase que se pueda usar de rótulo y de capítulo.
- Frases cortas y para el oído: la voz sintética lee mejor frases de 8-20 palabras. Escribir números como se dicen.
- Cierre con una acción concreta y pequeña (no "suscríbete" como única idea).
- Marcar en el guion `[IMAGEN: ...]` lo que debería verse y `[MOVIMIENTO]` donde una acción explica la frase.
- Si el texto es largo para la página de voz, partirlo en 2-3 partes en cortes de bloque; nombrar `parte1`, `parte2`...

## 3. Imágenes (`director-de-arte`)
Herramienta recomendada: Nano Banana Pro en Google Flow, con la ficha y las referencias del personaje adjuntas como ingredientes (hasta 10); así imagen y clip viven en el mismo proyecto. Para corregir una imagen con un personaje fuera de estilo, se sube esa imagen + la ficha a Nano Banana Pro y se pide redibujar solo ese personaje en el estilo de la ficha.
Un prompt por imagen en `03_IMAGENES/prompts_imagenes.md` (tabla `| n.º | archivo | frase | prompt |`, con el nombre final de cada imagen según `nombres.md`: `FIN-003_img-001_tema.png`): número, frase del guion, prompt completo (personaje exacto de la biblia del canal, estilo, encuadre 16:9 o 3:2 horizontal, fondo, sin texto o con texto en español solamente). Una imagen por idea, no por frase; se pueden repetir imágenes cuando vuelve la idea. Dejar aire en los bordes para el movimiento de cámara y para los rótulos (arriba a la izquierda) y subtítulos (abajo).

Por defecto, imágenes propias (generadas para el canal). Imágenes de banco o de archivo (Pexels, NASA, Wikimedia Commons, Internet Archive) solo si Patricio o la pareja lo piden para ese video, y siempre: anotar cada una en `03_IMAGENES/licencias.csv` (archivo; fuente; licencia; pide crédito; enlace) en el momento de bajarla. Nunca usar trozos de video de otros canales. Reglas en `monetizacion.md`.

Imágenes recibidas: si vienen con su nombre, copiarlas a `03_IMAGENES`; si vienen con nombres al azar, a `03_IMAGENES\_entrantes` y `python ordenar_imagenes.py "<video>"` (plan + hoja de control) → revisar → `--aplicar`.

## 4. Voz
Dos caminos; la biblia del canal dice cuál es el habitual.

**A. Página de voz de la persona** (finanzas: voicertool.com, voz Lorenzo, máximo 5.000 caracteres por conversión; el guionista deja las partes listas en `01_GUION/voz_parteN.txt`). Es el camino por defecto para videos que se publican, porque la página declara licencia de uso.

**B. Voz directo desde el estudio** con `voces.py` (mismas voces neuronales de Microsoft que usan voicertool y páginas parecidas, vía edge-tts):
- `python voces.py listar --idioma es [--multilingues]`: las voces disponibles (45 en español de 22 países + 12 multilingües).
- `python voces.py muestras "frase del guion" [--voces id1,id2] [--velocidad +5%] [--tono +0Hz]`: una muestra por voz en `EstudioPaltostaila\voces\muestras_<fecha>\` con `escuchar.html`. Para que la persona elija sin entrar a ninguna página, publicar esas muestras como página para escuchar (audio incrustado, filtros por país y género, botón para copiar el comando).
- `python voces.py generar "<video>" --voz es-CL-LorenzoNeural [--velocidad +5%] [--tono +0Hz] [--volumen +0%]`: lee `01_GUION/voz_parte*.txt` o `guion_para_voz.txt`, genera `02_VOZ/<ID>_voz-<nombre>.mp3` y además `06_RECETA/transcripcion.json` con el tiempo exacto de cada palabra (no hace falta WhisperX; pasar directo a la etapa 6 o al recorte de pausas). Si `02_VOZ` ya tiene audios no los toca: deja la voz en `02_VOZ_GENERADA` y avisa cómo usarla (`--reemplazar` solo con un sí).
- Aviso que se dice una vez por canal: edge-tts usa el servicio de lectura en voz alta de Edge de forma no oficial; puede dejar de funcionar y no trae una licencia comercial explícita. Sirve sin dudas para probar voces, borradores y animáticas; para publicar, la persona decide (si prefiere la licencia de su página, generar ahí con la misma voz elegida).
- No cambiar ni clonar la voz de un canal sin que la persona lo pida.

**C. Kokoro-82M (por probar):** modelo de voz local con licencia Apache 2.0 (uso comercial claro), con voces en español, portugués de Brasil e inglés (`pip install kokoro soundfile`; español `lang_code="e"`, portugués `"p"`). Puede ser la opción con licencia limpia para doblajes; probar calidad en español antes de usarlo en un canal.

Al recibir audios de la página (camino A): Al recibir los audios: medir duraciones (`ffprobe`), confirmar el orden por nombre y que no haya cortes ni repeticiones en las uniones (escuchar o revisar la transcripción en ese segundo).

## 5. Transcripción (`transcriptor`)
Si la voz salió de `voces.py generar`, la transcripción ya existe con tiempos exactos y el texto del guion: saltar WhisperX y revisar solo las pausas.
`python transcribir.py "<video>"` → `06_RECETA/transcripcion.json` (por palabra), informe de pausas y `07_RENDER/tmp/diferencias_con_guion.txt` si hay guion en `01_GUION`. Revisar cada diferencia: las que son error de reconocimiento se anotan en `correcciones` como `["texto oído exacto", "texto correcto"]` (el texto oído debe coincidir palabra por palabra con la transcripción, incluyendo signos). Las dudosas se dejan anotadas para que la persona escuche. Avisar si las pausas suman mucho (la voz Lorenzo de voicertool deja ~1 s tras cada frase): proponer recortarlas a ~0,35 s, sin hacerlo sin un sí.
Sin WhisperX instalado: avisar y ofrecer instalarlo (instalar.cmd, opción de transcripción).

## 5b. Recorte de pausas (`transcriptor`)
`python recortar_pausas.py "<video>"` muestra cuántas pausas largas hay y cuánto se ahorra; `--aplicar` (opciones `--umbral 0.6 --deja 0.35`) crea `02_VOZ_RECORTADA/voz_recortada.wav` y reajusta solos transcripción, receta, planos, efectos con segundo fijo y `recorte_clip`. Respaldo en `proyecto_antes_de_recortar.json`. Mejor hacerlo antes de la receta; si la receta ya existe, igual queda alineada. Revisar las escenas que avisa como muy cortas.

## 6. Receta de escenas (`editor-de-escenas`)
`python frases.py "<video>"` deja `06_RECETA/receta_borrador.csv` con tramos de 3-12 s que empiezan en una frase. Mirar cada imagen y asignarla en `archivo`; unir o partir tramos para que el corte caiga donde cambia la idea. Guardar como `receta.csv` y validar con `python frases.py "<video>" --validar` (sin huecos, sin solapes, imágenes existentes).
En `proyecto.json`:
- `escenas_capitulo`: escenas que abren un bloque (transición de deslizamiento y whoosh).
- `planos`: en escenas largas o con varios elementos, planos cerrados que sigan la narración. Formato `"n": [[segundo_global, [zoom, x, y], [zoom, x, y]], ...]`, x/y de 0 a 1. Elegir coordenadas mirando la imagen; no acercar al centro a ciegas (corta personajes en el borde). La escena 1 siempre lleva planos.
- `rotulos` (chico + grande, frase que lo dispara) y `capitulos` (el primero en 0:00, mínimo 3, cada uno de 10 s o más). No poner un rótulo que repita un texto que ya está dibujado en la imagen. Tarjetas de definición (marca `[DEFINICION]` del guion): rótulo con `"estilo": "definicion"` (caja clara arriba a la derecha, término en verde y definición corta). Ritmo objetivo: algo cambia cada 3-5 s.
Mostrar a la persona el resumen (n.º de escenas, qué imagen va en el gancho, rótulos) en la puerta B.

## 7. Movimiento con Flow (`director-de-movimiento`)
Prioridad de clips: (1) los primeros 4-5 s, siempre; (2) el cierre; (3) uno cada 1-2 min donde una acción explica la frase. No para un simple zoom (eso ya lo hace la cámara).
Preparar `04_CLIPS_FLOW/SUBIR_A_FLOW/` con las imágenes numeradas en orden (`1_escena_001.png`...) y `TEXTO_PARA_EL_AGENTE_DE_FLOW.txt` en inglés:
"I attached N images. Each image is the FIRST FRAME of its clip. Title each clip exactly 'escena_NNN'. Veo 3.1 Fast, 16:9, 8 seconds, one variant. No text, no subtitles, no voice, no music. Keep the 2D style and characters exactly as drawn (<personaje de la biblia>). One gentle action. End on a stable pose." + una línea por clip con su acción.
Costo de referencia: ~20 créditos por clip en Veo 3.1 Fast; la persona revisa el costo que muestra Flow y decide. Descargar en 1080p (es gratis) a `04_CLIPS_FLOW` sin renombrar; luego `python asignar_clips.py "<video>"` los reconoce por su primer cuadro y crea `escena_NNN.mp4`. Revisar cada clip con una tira de 1 cuadro por segundo: rechazar caras o manos deformadas, texto inventado, personaje distinto.
Después de asignar clips **siempre se vuelve a armar** el video (versión nueva): `armar.py` registra qué clips quedaron dentro, `terminar.py` se detiene si hay clips nuevos sin armar y `revisar.py` comprueba cuadro a cuadro que cada clip esté en su escena. Cambiar solo el audio (`--solo-audio`) nunca agrega clips.
Planos y clips: en una escena con `planos`, el clip cubre el primer plano y **sigue corriendo en los planos siguientes** (el plano cerrado se hace sobre el clip en movimiento, no sobre la imagen quieta; se apaga con `"planos_sobre_clip": false`). Un plano puede tener su propio clip: `escena_NNN_p2.mp4` (su imagen de partida es el recorte del plano, que se sube a Flow como `N_escena_NNN_p2.png`; `asignar_clips.py` lo reconoce por esa imagen).
El render inserta el clip solo: si dura hasta 1,5 s menos que la escena se sostiene su último cuadro; si falta más, sigue la imagen con movimiento; con planos, el clip reemplaza el primer plano. `alias_clips` reutiliza un clip en otra escena con la misma imagen.

## 8. Sonido (`sonidista`)
Sin música de fondo salvo que la persona lo pida. Efectos puntuales cuando aparece algo que suena en la imagen (monedas, puerta, libro, ropa, lápiz, máquina, auto, campana), whoosh en cada cambio de bloque y el audio propio de los clips de Flow (`clips_con_sonido`, recortado con `recorte_clip` si el clip ocupa solo parte de la escena). Banco CC0 de Kenney en `EstudioPaltostaila\sonidos` (listar con `Get-ChildItem -Recurse -Filter *.ogg`). `python sonidos.py "<video>"` deja `tmp/efectos.wav` y la lista de momentos.
Niveles probados: `vol_efectos` -19, `vol_clips` -16, `whoosh_db` -25, `limite_capa` 0,3 → picos de efectos 12-14 dB bajo la voz. Medir con `volumedetect` en los segundos de cada efecto. Error conocido: `alimiter` sube el nivel solo si no lleva `level=0` (el motor ya lo trae).
Para comparar con y sin efectos: `SIN_EFECTOS=1` antes de `terminar.py`.

## 9. Montaje y render (`montajista`)
1. `render.cmd "<video>" borrador` → `07_RENDER/<ID>_<v>_borrador-60s.mp4`. Sacar 6-8 fotogramas (`ffmpeg -ss T -i ... -frames:v 1`) y mirarlos. Puerta D.
2. `render.cmd "<video>"` → armado, sonidos, terminación, verticales, miniaturas y revisión automática.
3. Verificar `cuadros: N (esperados N) OK` en el log.
Solo cambió el audio: `python sonidos.py` + `python terminar.py "<video>" --solo-audio` (no recodifica la imagen). Una versión nueva sin pisar la anterior: cambiar `"version"` en `proyecto.json` (v2, v3...).
Transiciones por defecto: fundido 0,4 s entre escenas, deslizamiento 0,6 s al abrir bloque, fundido 0,2 s entre planos. Hay 68 para elegir (`references/transiciones.md`; catálogo en video con `python transiciones.py --catalogo`), también en `montaje_tomas.py` para videos sobre música.

## 9b. Control de calidad (`control-de-calidad`)
`python revisar.py "<video>"` + mirar las hojas de contacto y fotogramas en `07_RENDER/revision`. Revisar: imagen acorde a la frase, sin saltos ni negros en las transiciones, planos que no corten personajes, subtítulo que no tape lo importante, rótulos legibles, sin texto duplicado, clips en su escena, estilo del personaje igual en todas las imágenes, textos de imágenes en el idioma del canal, duración = voz, volumen ≈ -14 LUFS. Decir con claridad qué se miró y qué falta escuchar.

## 10. Publicación (`publicador`)
Ver `plataformas.md`. Cortos verticales: `python cortos.py "<video>"` (propuesta; `--n 3 --min 40 --max 80 --modo marco|recorte`), `--aplicar` y `python vertical.py`; `render.cmd` ya los saca solos si `vertical` está vacío. Títulos: escribir 10 y elegir 3 con las reglas del publicador y la prueba de las 3 búsquedas en el idioma del canal. Miniatura de máximo 3 palabras que no repitan el título (`miniaturas` en `proyecto.json` + `python miniatura.py`). Cortes verticales autocontenidos de 45-90 s que partan en una frase con gancho (`vertical` en `proyecto.json` + `python vertical.py`).

## 11. Después de publicar (`analista-de-canal` del gerente mide; `analista` saca los aprendizajes)
Con las métricas del gerente (`yt_api.py metricas`) o los datos que la persona comparta (capturas de YouTube Studio, TikTok Analytics): retención en tres problemas (fuga del gancho, caídas, pendiente), qué gancho funcionó, el arreglo más grande y qué repetir. Guardar en `08_PUBLICAR/aprendizajes.md` y proponer cambios a la biblia del canal (no cambiarla sin un sí).

## Capa viva, sala de edición y material grabado (motor 0.6)

| Qué | Comando | Notas |
|---|---|---|
| Probar subtítulos y elementos | `python vivo.py "<video>" --prueba 0-30 [--vertical] [--zona] [--fotos 3,10]` | sin imágenes usa un fondo neutro; `AVISO elemento sin frase` = frase mal copiada |
| Sala de edición | `python sala.py "<video>"` (segundo plano) → `http://127.0.0.1:8765/` | la persona abre Chrome; guardar deja respaldo en `08_SALA/` |
| Copia para el celular | `python celu.py "<video>" [archivo] [--zona]` | 720p en `07_RENDER/celu` y en Drive si existe |
| Tomas a cámara | `python grabado.py "<video>" transcribir` → `cortar` → `armar [--borrador 60]` | luego `terminar.py` y `vertical.py` |
| Evaluar antes de terminar | `python evaluar.py "<video>" [--video "<final o exportado>.mp4"]` | nota por ejes, clase A/B/C, mejoras con minuto, momentos para Shorts; luego el agente `evaluador` |
| Paquete para CapCut | `python capcut_paquete.py "<video>"` | `09_CAPCUT`: video limpio, imagen, voz, .srt, rótulos con minuto |
| Vertical que sigue al sujeto | `"modo": "seguir"` en un corte de `vertical` | reencuadre automático (cara con OpenCV o movimiento) |
| Ritmo medido | `python ritmo.py "<video>" [--comparar "<otro>"]` | cortes, saltos, tramos quietos, volumen, hoja de cortes; `referente.py` lo corre solo |
| Receta de miniatura | `python receta_miniatura.py mini1.jpg mini2.jpg --nuestra mia.png` | paleta, brillo, contraste, peso visual; después `receta-miniatura.md` |

Errores conocidos: una fuente que no está instalada en Windows hace que libass use otra parecida (revisar las fotos de prueba); los elementos de una frase que se repite en el guion necesitan `"despues"` para caer en la segunda vez.
