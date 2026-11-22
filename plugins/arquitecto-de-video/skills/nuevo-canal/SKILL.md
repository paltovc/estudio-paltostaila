---
name: nuevo-canal
description: Abre un canal nuevo (o completa uno existente) en cinco fases conversadas con la persona —concepto, referentes, identidad visual, pruebas y plan— y deja su biblia, su estrategia, su kit de marca y su plan de qué se hace, cómo y cuándo. Sirve para cualquier nicho, formato e idioma (animado, narrado, musical, persona a cámara, curso). Usar cuando se diga "nuevo canal", "abrir un canal", "vamos a abrir un canal", "configurar mi canal", "completar la biblia", "cambiar el personaje", "reglas del canal", "colores o tipografía del canal", o cuando el arquitecto no encuentre la biblia del canal de un video.
---

# Abrir un canal (o completarlo)

Archivos del canal en el PC: `%USERPROFILE%\EstudioPaltostaila\canales\<canal>\` → `canal.md` (biblia), `ESTRATEGIA.md` (la escribe el estratega del gerente), `marca.json` (kit de marca), `personaje\` (ficha, si hay personaje), `aprendizajes.md`. Sin computador vinculado: entregar la biblia como documento y guardarla después.

## Cómo se conversa
- Cinco fases, en orden. En cada fase, preguntas con opciones (máximo 4 por vez, siempre con opción de escribir otra respuesta) y explicando lo que hay que decidir con ejemplos simples. Saltar lo que ya está respondido (mensaje de la persona, biblia existente, `ESTRATEGIA.md`).
- Al cerrar cada fase: resumen de 4-6 líneas y un sí antes de pasar a la siguiente. Si la persona no está o dice «decide tú», tomar lo recomendado y anotarlo como supuesto en «Decisiones abiertas».
- Las dos personas del estudio (Patricio y su pareja) pueden responder; se anota quién decidió qué.
- Banco de preguntas por fase: `references/fases.md`.

## Las cinco fases
1. **Concepto.** Nicho y promesa del canal, público (edad, país, nivel, qué busca), idiomas y mercados, objetivo (audiencia, monetizar, vender, marca, arte), quién aparece (personaje animado, persona real, voz sin rostro, mezcla), líneas de producción (`../arquitecto-de-video/references/lineas-de-produccion.md`), formatos y plataformas (YouTube, Shorts, TikTok, Instagram), ritmo sostenible, reglas de contenido del nicho. En esta fase se lanza al **estratega** del gerente (ronda 0 de `estrategia.md` del gerente) con lo ya respondido, para no repetir preguntas: escribe `ESTRATEGIA.md`.
2. **Referentes.** 3-5 canales o videos que les gusten (o que el estudio encuentre). **canal-viral** para el canal completo y **analizar-referente** para los videos clave: qué se toma (forma) y qué se deja (`../arquitecto-de-video/references/adaptar.md`).
3. **Identidad.** Estilo visual (2D plano, 2D con textura, 3D, collage, foto real, mixto), tipo de animación (imágenes con movimiento de cámara, clips de Flow, gráficos animados, ninguna), paleta (4-6 colores con su papel), tipografías con licencia libre para uso comercial (título y texto; máximo 2), preset de subtítulos, 1-2 entradas de texto y 3-4 transiciones fijas, receta de edición (`../arquitecto-de-video/references/recetas-de-edicion.md`), sonido (música sí/no con licencia, efectos), miniatura base, logo y banner. Kit de marca con `python diseno.py marca <canal>` y la guía de `diseno-local.md`.
4. **Pruebas.** Personaje con **ficha-personaje** (si hay). Prompts de imágenes de prueba para ChatGPT, Nano Banana Pro en Flow o Codex (la persona genera; el estudio prepara los textos con `../arquitecto-de-video/references/direccion-de-arte.md`), más las imágenes que la persona traiga. Una **prueba de estilo** de 15-30 s: `vivo.py --prueba` sobre un fondo o un armado corto, y una miniatura de prueba. La persona aprueba o corrige; las correcciones se anotan en la biblia.
5. **Plan.** Series y primeros 10 temas (con **buscar-tendencias** y **canal-viral**), calendario base de 4 semanas (lo arma el gerente con su cupo), quién hace qué y cuándo (guion, voz, imágenes, grabación, revisión, publicación), costos (créditos de Flow, planes, voces), lista de lanzamiento del canal (cuenta, nombre, banner, foto, «Acerca de» que diga quién hace el canal y cómo se investiga, listas de reproducción por serie) y modo lanzamiento de los primeros 10 videos.

## Al terminar
- Escribir `canal.md` con `${CLAUDE_PLUGIN_ROOT}/canales/plantilla.md`, mostrar el resumen y guardar con un sí. Un canal nuevo parte con **Estado: en prueba**.
- Crear `aprendizajes.md` desde `${CLAUDE_PLUGIN_ROOT}/canales/plantilla_aprendizajes.md`.
- Prefijo de los códigos de video del canal (`references/nombres.md` del arquitecto: tres letras, por ejemplo `FIN`, `NDF`, `DOC`).
- Dejar en «Decisiones abiertas» todo lo que quedó como supuesto.
- **Canal existente** (por ejemplo finanzas): leer la biblia y `ESTRATEGIA.md`, marcar qué falta de cada fase y preguntar solo eso.

## Ficha de estilo viva (desde el 08-11-2026)
- **Correcciones de la persona:** cada corrección de Patricio o de su pareja se anota palabra por palabra, con fecha, quién y video, **solo en la biblia del PC** (`%USERPROFILE%\EstudioPaltostaila\canales\<canal>\canal.md`). La copia del plugin es la base para un equipo nuevo, va al repositorio y no lleva correcciones. No se borra ni se reescribe; única excepción: tapar una clave o un dato personal que quedó escrito, cambiándolo por [omitido] y anotando la fecha en que se tapó. Anotarla no necesita un sí (son sus palabras); cambiar una regla de la biblia por esa corrección, sí: el del dueño del canal.
- **Lo que NO va** es una regla más: un rechazo puntual queda primero en Correcciones y entra a "Lo que NO va" solo con el sí de la persona. **Falta herramienta** se mantiene al día con lo que el motor todavía no sabe hacer.
- **Claves y datos personales:** si una nota trae una clave, una contraseña o un dato personal, se anota tapado ("[omitido]") y se deja constancia de que se omitió. Nunca se copia a la biblia ni a aprendizajes.md.
- **Procedencia:** cada línea lleva fecha, autor, video y versión, y de dónde salió (chat, `08_SALA/notas.md`, archivo de evaluación). Las cifras de aprendizajes.md citan el archivo exacto.
- **Estado:** en prueba → aprobado (solo con el sí de la persona sobre un video concreto: se anota cuál y se sube la versión del estilo) → descartado (si se abandona; la biblia queda como historial).
- **aprendizajes.md:** una fila por versión de video (qué cambió, nota del evaluador con su fuente, qué dijo la persona), cómo se hace cada cosa, qué no funcionó y los gastos con su sí.

Cambios a las reglas propuestos por el analista o por la experiencia de un video se agregan solo con un sí, anotando la fecha en "Historial".
