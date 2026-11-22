# El sistema que deja al estudio igual cada vez

Basado en "No es el modelo" (tododeia). Cada chat parte en blanco: lo que hace que el estudio trabaje igual de bien cada vez es lo que queda escrito y lo que se comprueba solo.

| capa | dónde vive en el estudio |
|---|---|
| Reglas escritas | instrucciones del Proyecto "Estudio Palto Style" + este plugin (SKILL.md y references) |
| Lo que no puede depender de la memoria | el motor: nunca sobrescribe versiones; `caras.py` evita tapar caras; `revisar.py` |
| Verificación | `terminado.py`: lista de sí o no, se entrega tal cual antes de decir "listo"; además `evaluar.py` |
| Examen | `examen` en el documento del Proyecto: 5 tareas fijas para comparar al cambiar de modelo |

## Correcciones que se convierten en reglas
Toda corrección queda escrita palabra por palabra, con fecha, quién y video, en "Correcciones de la persona" de la biblia del canal **del PC** (no se borra; única excepción: tapar como [omitido] una clave o un dato personal, anotando la fecha); lo técnico, en `aprendizajes.md` del canal. Así una corrección no depende de que el próximo chat la recuerde.
Cuando la persona corrige lo mismo dos veces:
1. escribir en una línea qué se hizo y qué quería;
2. proponer una regla corta que lo evite;
3. compararla con las instrucciones del Proyecto: nueva, repetida o contradictoria;
4. no agregar nada sin su sí.

## Si algo sale mal
1. ¿Hay un incidente abierto? Revisar status.claude.com.
2. ¿Cambió el modelo o el esfuerzo?
3. ¿El chat ya era muy largo? Abrir uno nuevo dentro del Proyecto: el documento vivo guarda el estado.
4. ¿Se dieron las reglas esta vez?
5. ¿Había cómo saber que terminó bien? Correr `terminado.py`.


## Perfil bajo en los archivos (T1, 08-11-2026)
Todo comando de ffmpeg que escribe un archivo lleva `*SIN_METADATOS` (de `estudio.py`) **antes** del archivo de salida. `prueba.py` falla si falta o si queda como último elemento del comando; no detecta todos los casos (por ejemplo, la lista después de la salida pero seguida de otras opciones, o comandos armados en variables), así que al escribir un comando nuevo hay que ponerla justo antes de la salida. Como red de seguridad, `prueba_camara.py` (corre dentro de `prueba.py`) pasa tomas con GPS por grabado, montaje y doblaje; `terminado.py` punto 11 (obligatorio) revisa con ffprobe todos los videos de la versión y las copias para el celular; `montaje_tomas.py` y `doblaje.py` terminan con error si su entrega queda con metadatos. Para lo que sale de otro camino (exporte de CapCut): `python estudio.py metadatos "<archivo o carpeta>"`.

## Formato para las plataformas (09-11-2026)
YouTube, TikTok e Instagram piden lo mismo: MP4, H.264 High 4:2:0 (yuv420p), AAC-LC 48 kHz estéreo, índice al principio (fast start), hasta 60 fps; vertical 1080×1920. El video YouTube, el con subtítulos y los Shorts ya salen así (comprobado en FIN-002 v13). Falta (lote siguiente): ffmpeg escribe listas de edición (edit lists) en los MP4, que la ayuda de YouTube pide evitar; el doblaje subtitulado sale sin fast start; el montaje sale mono si la canción es mono. `terminado.py` punto 12 (recomendado) comprueba códec, color, audio y fast start en cada entrega; para un archivo suelto: `python estudio.py formato "<archivo o carpeta>"`. Lo que entra puede venir en cualquier formato (MOV del iPhone, MKV, WEBM): el motor lo lee y lo entrega en MP4.

## Licencias (T8, 09-11-2026)
`%USERPROFILE%\EstudioPaltostaila\licencias\registro.md` lista cada recurso ajeno (sonidos, fuentes, voz, imágenes, clips, modelos, música) con su licencia y su estado (✓ claro, ⚠ dudoso, ? por confirmar). Antes de usar un recurso nuevo en un video, se agrega su fila; un recurso con ⚠ o ? se avisa antes de pedir la aprobación para publicar. Las huellas de los archivos registrados se rehacen con `python licencias\huellas.py`.

## Estados de terminado (0.12)

✓ aprobado · ✗ falla · ? no comprobado (falta el registro, el registro es de otra versión o ffmpeg falló: **cuenta como no terminado**) · – recomendado que falta. El registro de la capa viva (`tmp/capa_viva_lugares.txt`) se escribe siempre y lleva en la primera línea la versión a la que pertenece.


## Señales de que el chat se está degradando (0.15, guías «No es el modelo» y «el canario»)
- **El canario:** cada informe del director termina con la línea `— Estudio Palto Style · <canal> · <ID del video o "sistema">`. Si una respuesta larga deja de traerla, o empieza a contradecir reglas escritas, el chat ya está perdiendo las instrucciones del principio: dejar el estado en `00_ESTADO.md` (o el traspaso del Proyecto) y proponer abrir un chat nuevo. La persona puede poner su propio canario en las instrucciones del Proyecto.
- **Dos correcciones que no funcionan:** después de corregir dos veces lo mismo en un chat sin éxito, no intentar una tercera: escribir qué falló, qué regla faltó y proponer seguir en un chat nuevo con un mensaje mejor (el traspaso).
- **Reglas cortas:** el `SKILL.md` principal se mantiene bajo ~150 líneas; lo detallado va a `references/`. Si dos reglas se contradicen, se arregla el texto, no se agrega énfasis.
- **Diagnóstico de una tarea que salió mal** (sin rehacerla todavía): qué información faltó, qué se decidió por cuenta propia, qué parte del pedido se podía entender de dos formas, cómo se podía haber sabido que no era lo pedido, y máximo 5 reglas que lo habrían evitado. Se proponen; se agregan con el sí de la persona.

## Integrar una herramienta, skill o plugin nuevo
Ver `integrar-herramientas.md`: se lee la fuente original, se revisa qué ejecuta y qué datos envía, se compara con lo que el estudio ya tiene, se propone qué tomar y cómo adaptarlo, y solo con el sí se incorpora al estudio (con su licencia en `creditos-terceros.md` y en `licencias\registro.md`). Una skill guardada aparte no se integra sola: si sirve, sus ideas se escriben dentro del estudio.
