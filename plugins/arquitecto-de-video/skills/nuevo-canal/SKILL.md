---
name: nuevo-canal
description: Crea o actualiza la biblia de un canal de video (público, voz, tono, personaje, estilo visual, reglas de contenido, plataformas, formato de video) que usan todos los agentes del estudio. Usar cuando se diga "nuevo canal", "configurar mi canal", "cambiar el personaje", "reglas del canal", o cuando el arquitecto no encuentre la biblia del canal de un video.
---

# Biblia del canal

Archivo: `%USERPROFILE%\EstudioPaltostaila\canales\<canal>\canal.md` (en el PC). Sin computador vinculado, entregarla como documento y guardarla después.

## Pasos

1. Si ya existe, leerla y preguntar qué cambia. Si es nueva, partir de `${CLAUDE_PLUGIN_ROOT}/canales/plantilla.md`.
2. Preguntar en una sola tanda (con opciones cuando se pueda): tema y público (edad, país, nivel), plataformas y formato principal (horizontal largo, vertical corto, ambos), voz (herramienta y nombre de la voz), personaje (si hay uno: aspecto exacto, ropa, colores, personalidad), estilo visual, cosas prohibidas, frecuencia de publicación.
3. Si la persona tiene imágenes del personaje, mirarlas y describirlo con precisión (forma de la cabeza, ropa, colores, accesorios) para que los prompts lo repitan igual.
4. Reglas de contenido según el tema: finanzas (sin promesas de ganancia, sin recomendar productos específicos como consejo personal, educativo), salud (sin diagnósticos), niños (cuidado extra con datos e imágenes), etc.
5. Escribir la biblia con la plantilla. Mostrar un resumen y guardar con un sí. Un canal nuevo parte con **Estado: en prueba**.
6. Crear al lado `aprendizajes.md` desde `${CLAUDE_PLUGIN_ROOT}/canales/plantilla_aprendizajes.md`.

## Ficha de estilo viva (desde el 08-11-2026)
- **Correcciones de la persona:** cada corrección de Patricio o de su pareja se anota palabra por palabra, con fecha, quién y video, **solo en la biblia del PC** (`%USERPROFILE%\EstudioPaltostaila\canales\<canal>\canal.md`). La copia del plugin es la base para un equipo nuevo, va al repositorio y no lleva correcciones. No se borra ni se reescribe; única excepción: tapar una clave o un dato personal que quedó escrito, cambiándolo por [omitido] y anotando la fecha en que se tapó. Anotarla no necesita un sí (son sus palabras); cambiar una regla de la biblia por esa corrección, sí: el del dueño del canal (en finanzas, Patricio).
- **Lo que NO va** es una regla más: un rechazo puntual queda primero en Correcciones y entra a "Lo que NO va" solo con el sí de la persona. **Falta herramienta** se mantiene al día con lo que el motor todavía no sabe hacer.
- **Claves y datos personales:** si una nota trae una clave, una contraseña o un dato personal, se anota tapado ("[omitido]") y se deja constancia de que se omitió. Nunca se copia a la biblia ni a aprendizajes.md.
- **Procedencia:** cada línea lleva fecha, autor, video y versión, y de dónde salió (chat, `08_SALA/notas.md`, archivo de evaluación). Las cifras de aprendizajes.md citan el archivo exacto.
- **Estado:** en prueba → aprobado (solo con el sí de la persona sobre un video concreto: se anota cuál y se sube la versión del estilo) → descartado (si se abandona; la biblia queda como historial).
- **aprendizajes.md:** una fila por versión de video (qué cambió, nota del evaluador con su fuente, qué dijo la persona), cómo se hace cada cosa, qué no funcionó y los gastos con su sí.

Cambios a las reglas propuestos por el analista o por la experiencia de un video se agregan solo con un sí, anotando la fecha en "Historial".
