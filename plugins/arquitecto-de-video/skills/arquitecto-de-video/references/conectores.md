# Conectores útiles

Cada persona conecta sus propias cuentas en la configuración de Claude (Conectores). El estudio funciona sin ninguno; cada uno agrega algo. Antes de usar uno, ver si está conectado; si no, decir en una línea qué ganaría la persona y seguir sin él.

| Conector | Para qué en el estudio | Quién lo usa |
|---|---|---|
| vidIQ | Videos fuera de lo normal en el nicho, palabras clave, tendencias, miniaturas parecidas, estadísticas de canales | cazador-de-tendencias, analista-de-referentes, publicador |
| Google Drive | Compartir carpetas de video, biblias de canal y entregas entre la pareja | todos |
| Notion o Google Sheets | Calendario de los videos (estado de cada uno, fechas, enlaces) e ideas priorizadas | director, cazador-de-tendencias |
| Google Calendar | Fechas de publicación y recordatorios de revisión a las 48 h y 7 días | director, analista |
| Canva | Miniaturas editables y adaptar piezas a cada red | publicador |
| HyperFrames | Gráficos animados (rótulos, listas, cifras) como clips para insertar | director-de-movimiento |
| Metricool | Estadísticas de YouTube, TikTok e Instagram en un lugar y programación de publicaciones (solo con un sí explícito) | analista, publicador |
| YouTube Data API (clave gratuita de Google Cloud, sin facturación) | `scanner_youtube.py`: búsqueda de nichos con nota = vistas / mediana del canal, con la cuota contada (100 búsquedas al día) | cazador-de-tendencias |
| Cuenta del canal en YouTube (OAuth) | Solo para leer la curva de retención propia; no hace falta para nada más, mejor no conectarla si no se usa | analista |

Sin conectores, `tendencias.py` y `referente.py` (yt-dlp en el PC) ya leen vistas, likes, comentarios, subtítulos y el video de enlaces públicos de YouTube y TikTok. Instagram suele pedir sesión: en ese caso pedir a la persona el video y capturas de los comentarios. Nunca usar contraseñas ni cookies de la persona.

Las claves (por ejemplo la de YouTube) van en un archivo en `%USERPROFILE%\EstudioPaltostaila\claves\` y nunca en el chat ni en el repositorio.
