---
name: ficha-personaje
description: Crea y mantiene la ficha maestra del personaje recurrente de un canal (imagen de referencia con frente, perfil, expresiones y poses, más su descripción exacta) para que todas las imágenes generadas lo mantengan igual. Usar cuando se diga "ficha del personaje", "imagen de referencia", "el personaje sale distinto", "mantener el mismo mono", o antes de producir videos en lote.
---

# Ficha maestra del personaje

Archivos: `%USERPROFILE%\EstudioPaltostaila\canales\<canal>\personaje\` con `ficha_maestra.png` (la referencia aprobada), `descripcion.md` y `prompt_ficha.md`.

## Crear la ficha
1. Partir de las imágenes que dé la persona: 2-3 imágenes o una carpeta ("este es el personaje"). Copiarlas sin tocar las originales con `python nuevo_proyecto.py ... --personaje "img1;img2"` o directamente a `personaje\referencias\`. Si las adjuntó en el chat, guardarlas primero en el PC. Si no hay ninguna, pedir 3-6 donde el personaje le guste más (o elegirlas de un video ya hecho y mostrarlas para que apruebe). Las referencias aprobadas mandan sobre cualquier otra descripción. Mirarlas y escribir `descripcion.md`: forma de la cabeza y cara, ojos, boca, contorno, proporciones, ropa con colores exactos, insignia, zapatillas, accesorios, lo que NUNCA lleva.
2. Escribir `prompt_ficha.md` para ChatGPT (la persona genera; adjuntar las imágenes elegidas): "Character reference sheet of the attached character, same exact 2D style and colors. White background. Row 1: front, three-quarter, side, back. Row 2: happy, worried, surprised, thinking. Row 3: walking, pointing, sitting at a desk, holding a phone. No text." + la descripción.
3. Revisar la ficha generada contra las imágenes originales (mismos colores, proporciones, insignia). Si hay diferencias, decir cuáles y pedir otra versión. Guardar la aprobada como `ficha_maestra.png` con la fecha en `descripcion.md`.
4. Anotar en la biblia del canal la ruta de la ficha.

## Usar la ficha
- `director-de-arte`: cada prompt de imagen empieza con la descripción y le dice a la persona que adjunte `ficha_maestra.png` en el chat de ChatGPT ("use the attached reference sheet; keep the character identical").
- `director-de-movimiento`: el texto para Flow describe al personaje igual que la ficha.
- `control-de-calidad`: compara cada imagen y cada clip con la ficha; anota escena por escena lo que se aparta (color de la sudadera, forma de la cabeza, insignia, estilo de secundarios).
