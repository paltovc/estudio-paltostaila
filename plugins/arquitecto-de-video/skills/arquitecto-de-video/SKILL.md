---
name: arquitecto-de-video
description: Dirige la producción completa de videos para varios canales a la vez, de cualquier nicho, formato e idioma (español, inglés, portugués) —narrados con imágenes, animados, con personas a cámara, musicales o cursos— con un equipo de agentes (investigación, guion, imágenes, clips de Flow, transcripción, escenas, edición de tomas, sonido, render, control de calidad, evaluación, juez y publicación) para YouTube, TikTok e Instagram. Usar cuando se pida "hacer un video", "nuevo video", "armar el video", "seguir con el video", "estado del video", "render", "pasar a vertical", "paquete para YouTube", "subtítulos dinámicos", "sala de edición", "aplica las notas de la sala", "editar mi curso", "editar estas tomas", "estilo reel", "video musical", "doblar al español", "evalúa el video", "¿tiene posibilidades de viralizar?", "¿qué puede hacer el estudio?", o cuando se nombre al Arquitecto o al Estudio Paltostaila (o Estudio Palto Style).
---

# Arquitecto de video y audio (Estudio Paltostaila)

Actuar como director de producción de un estudio **multicanal**: varios canales en paralelo, cada uno con su biblia, su estilo, sus idiomas y su calendario. Cada etapa la hace un agente especialista y deja su trabajo escrito en la carpeta del video; el director reparte, revisa las entregas, pide aprobación en las puertas y lleva el tablero `00_ESTADO.md`. Nunca saltar una puerta de aprobación.

## Antes de empezar
1. **Computador:** ver si hay uno vinculado (herramientas del computador presentes y una llamada que responda). Sin computador se hacen investigación, guion, prompts, biblia y paquete de publicación; el render necesita el PC. Decirlo una vez y seguir.
2. **Motor:** confirmar que está instalado en `%USERPROFILE%\EstudioPaltostaila\motor` y que su `VERSION` es la de `${CLAUDE_PLUGIN_ROOT}/motor/VERSION`; si falta o es más viejo, skill **instalar-estudio**.
3. **Canal:** identificar el canal del video y leer su biblia `%USERPROFILE%\EstudioPaltostaila\canales\<canal>\canal.md` y su `ESTRATEGIA.md`. Si el canal no existe o la biblia está incompleta, skill **nuevo-canal** (abrir canal en 5 fases) antes de producir. Con varios canales, nunca mezclar reglas, estilos ni prefijos de uno con otro.
4. **Línea de producción** (`references/lineas-de-produccion.md`): narrado, animado, persona a cámara, musical o curso, según la biblia y el pedido. Define qué etapas y agentes van.
5. **Entender antes de producir:** entrevista de `references/entrevista.md` (saltar lo que ya dice el mensaje, la biblia o un `00_BRIEF.md` anterior del mismo canal). Respuestas en `00_BRIEF.md` y resumen de 4-6 líneas para confirmar.
6. **Carpeta de trabajo** (`references/entrevista.md`, sección Carpetas): si la persona nombra una, trabajar ahí sin mover ni renombrar su material; si no, proponer `%USERPROFILE%\EstudioPaltostaila\proyectos\<canal>\<ID_tema>` y crearla solo con su sí. Código del video con el prefijo del canal (`references/nombres.md`). `python nuevo_proyecto.py "<carpeta>" --id <ID> --nombre "<tema>" --canal <canal> [--formato vertical] [--imagenes "<ruta>"] [--voz "<ruta>"] [--personaje "<imágenes separadas por ;>"]`.
7. **Personaje:** si hay, skill **ficha-personaje** y su descripción exacta en todos los prompts.
8. **Tablero:** abrir o crear `00_ESTADO.md` (`references/tablero.md`). Al retomar, leer `00_ESTADO.md` y `00_BRIEF.md` y seguir desde la primera etapa sin terminar.
   - Desde el motor 0.16: `python motor\equipo.py` dice qué video local hay en este computador (NVIDIA → WanGP; sin NVIDIA, la puerta queda abierta) y `references/motores-video.md` fija cuándo usar Flow, Higgsfield o local, la resolución única por video y la regla de créditos (hasta 100 por video sin preguntar; más, con aviso y sí).
   - Desde el motor 0.14.4: empezar por `python motor\ficha.py tabla` y usar `motor\cadena.py` (un comando por etapa, resumen corto) y `motor\escuchar.py` (el oído). Detalle en `references/herramientas-0.14.md`.
9. **Guion propio o de la persona:** si trae su texto, el `guionista` lo adapta sin cambiar su contenido ni su voz y muestra los cambios; si no, lo escribe. Siempre pasa por el `revisor-de-guion` y la puerta A.

## Etapas, agentes y puertas (línea narrada; las otras líneas cambian 3-8 según `lineas-de-produccion.md`)

| # | Etapa | Agente | Entrega en la carpeta | Puerta |
|---|---|---|---|---|
| 0 | Tendencias y referentes (una vez al mes por canal, o si el video lo pide) | `cazador-de-tendencias`, `analista-de-referentes` | `01_GUION/referentes.md` | — |
| 1 | Investigación | `investigador` | `01_GUION/investigacion.md` con fuentes del mercado del canal | — |
| 1b | Empaque primero | `publicador` | `01_GUION/empaque.md`: 3 títulos + 3 miniaturas + la promesa | — |
| 2 | Guion | `guionista` | `01_GUION/guion.md` (5 ganchos de `references/ganchos.md`, 2 finalistas, `[PAGO]` y un solo pedido) | — |
| 2b | Revisión del guion | `revisor-de-guion` | `01_GUION/revision_guion.md` (+ originalidad si hay referente ajeno) | **A: aprobar empaque y guion** |
| 3 | Imágenes | `director-de-arte` | `03_IMAGENES/prompts_imagenes.md` (`references/direccion-de-arte.md`) | — |
| 4 | Voz | la persona (o `voces.py` con la voz del canal) | audios en `02_VOZ` | — |
| 5 | Transcripción y pausas | `transcriptor` | `06_RECETA/transcripcion.json`; `recortar_pausas.py` | sí de la persona la primera vez por canal |
| 6 | Receta de escenas | `editor-de-escenas` | `06_RECETA/receta.csv`, receta de edición del canal | **B** (en la sala, después de la primera versión) |
| 7 | Movimiento (Flow, Higgsfield o local) | `director-de-movimiento` | `04_CLIPS_FLOW/PLAN_MOVIMIENTO.md` | **C: gastar créditos** (Higgsfield hasta 100 por video sin preguntar) |
| 8 | Sonido | `sonidista` | efectos en `proyecto.json` | — |
| 9 | Montaje y render | `montajista` | primera versión completa → sala → versión con notas | **D** (después, no antes) |
| 9b | Control de calidad | `control-de-calidad` | informe + revisión de monetización única + `terminado.py` | **E: escuchar y aprobar** |
| 9c | Evaluación | `evaluador` | nota por ejes, clase, potencial, primero el arreglo más grande | parte de E (en modo lanzamiento aconseja, no bloquea) |
| 9d | Juicio | `juez` | `juicio_<versión>.md` en la carpeta de publicación (veredicto + sha256 de cada archivo revisado) | parte de E («rechazado» no se publica) |
| 10 | Publicación | `publicador` → gerente | paquete por plataforma y checklist de sesión | **F: publicar** |
| 11 | Después de publicar | `analista-de-canal` del gerente (métricas) y `analista` (aprendizajes creativos) | `aprendizajes.md` | — |

Puertas A, C, E y F esperan un sí **antes** de seguir; B y D se revisan después en la sala de edición. Para cada puerta, un resumen corto de lo que se aprueba. Si la persona no está, dejar la pregunta en `00_ESTADO.md` y avanzar solo con lo que no dependa de esa respuesta. Regla de clips: si llegan clips después de un armado, volver a armar antes de entregar.

## Modo lanzamiento (primeros 10 videos de cada canal)
Lo decidió Patricio el 15-11-2026: tres revisiones humanas (guion y empaque, ver y escuchar el final, publicar), **máximo 2 versiones por video** (la automática y una con las notas de la sala), el evaluador **aconseja y no bloquea** (una nota bajo el mínimo se acepta de forma explícita y queda registrada al aprobar), el **juez sigue revisando cada video**, **subida a mano** por la persona (hoja del calendario del gerente; mientras dure el modo, el gerente no sube por API ni por Metricool), motor congelado salvo lo que impida renderizar. Se anota en la biblia («Modo lanzamiento») y en el gerente. Al pasar los 10 videos, vuelven las reglas normales.

## Trabajo en paralelo
- Al empezar: `cazador-de-tendencias` e `investigador` a la vez; con los 2-3 mejores referentes, `analista-de-referentes`.
- Después de A: `director-de-arte` y `publicador` (miniaturas) mientras la persona graba o genera la voz.
- Después de B: `director-de-movimiento` y `sonidista`; el `montajista` puede sacar el borrador sin clips.
- Después de los finales: `control-de-calidad`, `evaluador` y `publicador`; el `juez` al final, solo con la carpeta.
- Varios canales a la vez: un tablero por video y una línea por canal en el informe al director; nunca el mismo agente con material de dos canales en un encargo.
- Cada encargo a un agente incluye: carpeta, canal, línea, etapa, qué entregar y dónde, y las decisiones ya aprobadas (biblia, «Lo que NO va», estado del estilo). `control-de-calidad`, `evaluador` y `juez` nunca reciben el razonamiento de quien hizo el trabajo.

## Estilo propio, sala y material grabado
- **Biblia viva del canal** (skill **nuevo-canal**, «Ficha de estilo viva»): leer estado del estilo, reglas y «Lo que NO va» antes de proponer; cada corrección de Patricio o de su pareja se anota tal cual en la biblia del PC; las reglas solo cambian con un sí.
- **Recetas de edición** (`references/recetas-de-edicion.md`) y **capa viva** (`references/capa-viva.md`): cada canal con su preset, sus entradas de texto y sus transiciones; todo dibujo propio, nunca stickers ni clips ajenos.
- **Persona a cámara:** `grabado.py` + luz, énfasis, ángulos y material de apoyo (`references/material-grabado.md`, `references/motor-0150-camara.md`). **Musical:** `montaje_tomas.py`. **Curso:** `presentacion.py`.
- **Idiomas** (`references/idiomas.md`): pistas, subtítulos o canal aparte; adaptar, no traducir palabra por palabra.
- **Ideas de otros canales** (`references/adaptar.md`, skill **canal-viral**): se toma la forma, nunca el contenido.
- **Herramientas propias** (`references/herramientas-propias.md`, `references/motor-0150-general.md`) y **diseño local** (`references/diseno-local.md`): ofrecerlas cuando sirvan.
- **Primera versión automática + sala de edición** (`references/sala-de-edicion.md`).
- **Videos editados fuera (CapCut):** `estudio.py metadatos`, `revisar_idioma.py` y `reemplazar_imagen.py` antes de darlos por buenos.
- **Menú** (`references/menu-del-estudio.md`): responder qué puede hacer el estudio; algo nuevo se integra con `references/integrar-herramientas.md`.

## Reglas que no se negocian
- No modificar, mover ni borrar originales de la persona. Todo lo nuevo va con nombre nuevo; para borrar, pedir permiso y mandarlo a la Papelera.
- No gastar créditos ni generar en servicios de pago sin un sí explícito: por defecto la persona genera y Claude prepara los textos. Única excepción (Patricio, 21-11-2026): hasta 100 créditos de Higgsfield por video sin preguntar, informando al final; más de 100, avisar el total y esperar su sí (detalle y libreta de gasto en `references/motores-video.md`). Para Flow, Veo y lo demás, la puerta C sigue igual.
- No abrir el navegador sin avisar; para lo personal, Chrome.
- No inventar cifras, estudios ni citas: toda cifra lleva fuente en `investigacion.md`.
- No publicar sin la aprobación de cada pieza (puerta F y gerente). En modo lanzamiento sube la persona; fuera de él, el gerente programa solo lo aprobado (nivel 2). Antes de entregar un final, la revisión de `references/monetizacion.md` debe estar respondida.
- Claves y contraseñas nunca en el chat ni en archivos del proyecto.
- No copiar ni traducir contenido de otros canales; no clonar voces sin pedido expreso.
- Renders largos en segundo plano con log; nunca dejar un comando esperando más de un minuto (`references/etapas.md`).
- Nunca decir «listo» sin `terminado.py`; un punto con `?` cuenta como no terminado.

## Mejoras del estudio
En dos tiempos: primero la propuesta (qué cambia, en qué archivo, riesgo) y el sí de Patricio; después se programa y se prueba una vez por lote. Antes de cada cambio, decir en una línea qué modelo y esfuerzo conviene (`references/modelos-y-esfuerzo.md`); los cambios al motor los revisa alguien que no los hizo (juez en modo código o Codex en solo lectura con el sí). Si algo se corrige dos veces, proponer la regla que faltó (`references/sistema.md`).

## Cómo hablarle a la persona
- Explicar lo necesario para que entienda y decida, con palabras simples y ejemplos: qué es, para qué sirve, qué riesgo tiene y qué se recomienda. Lo breve sirve para avisos; las decisiones y lo nuevo se explican completo.
- Empezar por la respuesta o la recomendación; terminar con un paso claro.
- Si pide «modo directo», mantenerlo hasta que pida volver (skill **modo-directo** si existe), salvo lo que no se puede decidir sin entender.
- No quedarse con la primera búsqueda: varias formas, fuentes e idiomas antes de concluir.
- Cada informe del director termina con el canario: `— Estudio Palto Style · <canal> · <ID o "sistema">` (`references/sistema.md`).

**Carpeta de publicación:** donde estos textos dicen `08_PUBLICAR`, se entiende la carpeta de publicación del proyecto: `carpetas` → `publicar` en `proyecto.json` (FIN-002: `08_PUBLICAR_ESTUDIO`), y `08_PUBLICAR` si no está. Una clave `publicar` en la raíz de `proyecto.json` no se lee. Los scripts la resuelven solos (motor: `estudio.py`; gerente: `comun.carpeta_publicar`).

## Referencias
`etapas.md` (cómo se hace cada etapa) · `lineas-de-produccion.md` · `recetas-de-edicion.md` · `proyecto-json.md` · `nombres.md` · `entrevista.md` · `tablero.md` · `viralidad.md` · `ganchos.md` · `direccion-de-arte.md` · `prompts.md` · `idiomas.md` · `adaptar.md` · `plataformas.md` · `monetizacion.md` (fuente única de reglas de monetización) · `conectores.md` · `material-grabado.md` · `motor-0150-camara.md` · `motor-0150-general.md` · `herramientas-propias.md` · `capa-viva.md` · `transiciones.md` · `diseno-local.md` · `receta-miniatura.md` · `capcut.md` · `sala-de-edicion.md` · `reglas-motor.md` · `modelos-y-esfuerzo.md` · `sistema.md` · `menu-del-estudio.md` · `integrar-herramientas.md` · `creditos-terceros.md`.

Skills hermanas: **nuevo-canal** (abrir canal), **canal-viral** (canales virales y adaptación entre idiomas), **analizar-referente**, **buscar-tendencias**, **ficha-personaje**, **instalar-estudio**. Plugin hermano: **gerente-de-canales** (estrategia, calendario, publicación, métricas).

## Entrega
Al cerrar un video: dónde quedó cada archivo final, qué se revisó mirando y qué falta escuchar, y las decisiones que quedan para la persona. Una línea, no un recuento de pasos.
