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
5. Escribir la biblia con la plantilla. Mostrar un resumen y guardar con un sí.

Cambios propuestos por el analista o por la experiencia de un video se agregan solo con un sí, anotando la fecha en "Historial".
