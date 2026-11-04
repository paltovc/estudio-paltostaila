# Receta de miniatura (ingeniería inversa de una miniatura que funciona)

Se mide qué hace funcionar una miniatura y se escribe una receta propia: reglas + prompt con el personaje, la marca y el idioma del canal. Nunca se copia la imagen, sus personajes, su texto exacto ni logos.

1. **Elegir 3-6 miniaturas** de videos que superan por mucho a su canal (escáner de tendencias o `referente.py`; la miniatura queda como `video*.jpg`). Agregar la nuestra actual si existe.
2. **Medir:** `python receta_miniatura.py "mini1.jpg" "mini2.jpg" ... --nuestra "FIN-003_miniatura.png" --salida "<proyecto>\03_IMAGENES\receta_miniatura"` → `hoja_miniaturas.jpg` (tercios, peso visual, paleta con porcentajes) y `medidas.json` (brillo, contraste, saturación, zona muy contrastada).
3. **Mirar la hoja y anotar** lo que se repite en al menos el 70 %: cuántas palabras (casi siempre 2-4), tamaño del texto (ocupa 1/4 a 1/3 del alto), lado del texto y del personaje, expresión (sorpresa, duda, alerta), un objeto que cuenta la historia, colores de fondo y de acento, contraste entre texto y fondo, flechas o círculos.
4. **Escribir `receta.md`:**
   - Reglas (5-8 líneas, con los números medidos).
   - Prompt para ChatGPT o Nano Banana con la ficha maestra del personaje adjunta (ver `prompts.md`): escena, expresión, objeto, fondo y paleta en hex, espacio libre donde irá el texto. El texto se pone después (Canva o `miniatura.py`), no dentro del generador.
   - 3 variantes de texto (en el idioma del canal) para "Probar y comparar" de YouTube.
5. **Armar:** con `diseno.py` (plantilla `miniatura-lado` o `miniatura-centro` con el kit de marca del canal; ver `diseno-local.md`), con `miniatura.py`, o en una **copia** del diseño en Canva con el conector (nunca en el original de la pareja). Exportar 1280x720 y revisar a 160 px de ancho (como se ve en el celular): el texto se tiene que leer.
6. Entregar la receta al publicador para el paquete y guardarla en la biblia del canal si se repite en varios videos.
