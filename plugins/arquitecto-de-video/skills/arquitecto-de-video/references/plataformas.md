# Plataformas

Los límites cambian seguido. Antes de entregar un paquete, el `publicador` confirma con una búsqueda web los límites que use (largo de texto, duración, hashtags) y anota la fecha y la fuente al final del paquete. Lo de abajo es la base revisada en noviembre de 2026.

## YouTube (video largo)
- Archivo: `..._YouTube_sin_subtitulos.mp4` + `.srt` corregido subido aparte (YouTube lo usa como subtítulos editables y para búsqueda). Si la persona prefiere subtítulos grabados, `..._con_subtitulos.mp4`.
- Título: hasta 100 caracteres; lo importante en los primeros ~60 (se corta en móvil). 3 opciones finales.
- Descripción: hasta 5.000 caracteres. Las dos primeras líneas dicen qué gana quien mira, con las palabras que buscaría. Después: capítulos, fuentes de los datos, aviso si es contenido educativo ("no es asesoría financiera" en el canal de finanzas).
- Capítulos: el primero en 0:00, al menos 3, cada uno de 10 s o más.
- Etiquetas: hasta 500 caracteres en total; pesan poco, 5-10 bastan.
- Miniatura: 1280×720, menos de 2 MB, máximo 3 palabras que no repitan el título.
- "Probar y comparar" (YouTube Studio en computador, con funciones avanzadas activadas): hasta 3 títulos, 3 miniaturas o 3 combinaciones; gana la que logra más tiempo de visualización (no la de más clics). No sirve para Shorts, videos para niños ni privados. Dejar siempre 3 combinaciones listas.
- Comentario fijado: la pregunta del video y, en finanzas, aviso contra estafas (en los comentarios de canales de inversión abundan falsos testimonios y "asesores").
- Marcar "contenido alterado o sintético" cuando haya clips o imágenes realistas generadas con IA que puedan confundirse con algo real (para dibujos claramente animados normalmente no hace falta; revisar la regla vigente).

## YouTube Shorts
- 9:16, hasta 3 minutos. Lo que funciona mejor: 45-90 s, autocontenido, que parta en una frase con gancho.
- Título corto con la pregunta del corte; 1-3 hashtags.

## TikTok
- 9:16, 1080×1920. Subtítulos grabados (`vertical.py` ya los pone) y dejar libre la franja de abajo y la derecha (botones de la app).
- Texto de la publicación: gancho en la primera línea, 3-5 hashtags específicos. Confirmar el largo máximo vigente.
- Si se sube el video largo: confirmar el largo máximo de subida vigente en la app.
- Activar la etiqueta de contenido generado con IA cuando corresponda.

## Instagram Reels (preparado, sin uso aún)
- 9:16, 1080×1920; el mismo corte vertical sirve. Portada 1080×1920 con lo importante en el centro 1080×1350 (así se ve en la cuadrícula del perfil).
- Desde diciembre de 2025 Instagram permite como máximo 5 hashtags por publicación.
- Texto: gancho en la primera línea; el resto se oculta tras "más".

## Estructura de `08_PUBLICAR`
```
08_PUBLICAR/
  youtube/   titulos.md, descripcion.md, capitulos.txt, etiquetas.txt, miniatura(s)
  shorts/    por cada corte: titulo y texto
  tiktok/    por cada corte: texto, hashtags
  instagram/ por cada corte: texto, hashtags, portada
  checklist_publicacion.md
```
`checklist_publicacion.md`: qué archivo sube a cada plataforma, en qué orden, y casillas para marcar (subido, subtítulos cargados, miniatura, etiqueta IA, comentario fijado).
