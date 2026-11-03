# Arquitecto de video — Estudio Paltostaila

Un equipo de 14 agentes que lleva un video narrado desde la idea hasta el paquete listo para subir a YouTube, Shorts y TikTok (Instagram queda preparado). Tú pones la voz, las imágenes y los clips; el equipo investiga, escribe, organiza, arma, revisa y empaqueta. Nada se publica ni se gasta sin tu sí.

## Cómo se usa

Escribe algo como:
- "Hagamos un video nuevo sobre el fondo de emergencia para el canal de finanzas"
- "Sigamos con el Video 03" (lee el tablero y sigue donde quedó)
- "¿En qué va el video?"
- "Configura un canal nuevo" (crea la biblia del canal: público, voz, personaje, reglas)
- "Instala el estudio en mi computador"
- "Este es el personaje" + 2-3 imágenes o una carpeta (lo copia y lo mantiene igual en todo)
- "Trabaja en esta carpeta: C:\..." (respeta lo que ya hay; si no das carpeta, propone una y pregunta)
- "Analiza este video" + un enlace de YouTube, TikTok o Instagram (por qué funciona y cómo aplicarlo)
- "¿Qué está funcionando en mi nicho?" (tendencias con respaldo de datos)
- "Crea la ficha del personaje" (imagen de referencia para que siempre salga igual)
- "Tengo estas tomas y fotos en tal carpeta, arma un video con esta canción" (inventario, color, montaje al ritmo)
- "Busca nichos que estén funcionando" (escáner con la API oficial de YouTube, si creas la clave gratuita)
- "¿Qué voces hay?" o "Dame opciones de voz para este guion" (muestras de las voces de Microsoft para escucharlas aquí, y la voz completa con tiempos por palabra con `voces.py generar`)

Antes de producir, el arquitecto te hace una entrevista corta (qué quieres lograr, para qué plataforma, qué material tienes, si traes guion o lo escribe) y la deja en `00_BRIEF.md`.

## El equipo

| Agente | Qué hace |
|---|---|
| cazador-de-tendencias | Videos del nicho que superan por mucho a su propio canal, e ideas priorizadas |
| analista-de-referentes | Disecciona un video exitoso: números, gancho, ritmo, empaque, comentarios; y cómo aplicarlo |
| investigador | Datos con fuente y las preguntas reales del público |
| guionista | Guion con gancho en los primeros 5 s, listo para la voz |
| revisor-de-guion | Revisión independiente: datos, reglas del canal, claridad |
| director-de-arte | Prompts de imágenes con el personaje siempre igual |
| director-de-movimiento | Qué animar con Flow y el texto para su agente; revisa los clips |
| transcriptor | Subtítulos exactos palabra por palabra y correcciones |
| editor-de-escenas | Qué imagen va en cada segundo, planos, rótulos y capítulos |
| sonidista | Efectos suaves bajo la voz |
| montajista | Borrador de 60 s y render final |
| control-de-calidad | Revisión independiente antes de publicar |
| publicador | Títulos, descripción, miniaturas, cortes verticales y checklist |
| analista | Qué aprender de cada video publicado |

Puertas en las que te pide aprobación: empaque y guion · receta de escenas · créditos de Flow · borrador · versión final · publicación.

## Qué necesitas

- **Para todo el video:** la app de escritorio de Claude en un computador con Windows, con el computador vinculado a la conversación. La primera vez, di "instala el estudio": instala Python, ffmpeg, un banco de sonidos libres y (si quieres) WhisperX para transcribir sin sacar el audio del computador.
- **Solo desde la web o el celular:** puedes hacer investigación, guion, prompts de imágenes y el paquete de publicación. El armado del video necesita el computador.

## Conectores que suman (opcionales, cada persona conecta los suyos)

vidIQ (tendencias y palabras clave), Google Drive (compartir carpetas), Notion o Google Sheets (calendario de videos), Google Calendar (fechas y revisiones), Canva (miniaturas), Metricool (estadísticas de todas las redes). Sin ninguno, el estudio igual lee videos públicos de YouTube y TikTok desde el computador.

## Nombres y orden

Cada video tiene un código (`FIN-003`) y todo lo que sale lleva código y versión: `FIN-003_v2_youtube.mp4`, `FIN-003_v2_short-1_9x16.mp4`, `FIN-003_v2_miniatura-1.jpg`. Las imágenes van en el orden del guion: `FIN-003_img-001_tema.png`. Si descargas de ChatGPT con nombres al azar, déjalas en `03_IMAGENES\_entrantes` y el estudio las numera en orden (sin tocar los originales).

## Dónde queda cada cosa

En el computador: `Documentos o donde elijas\<Video>` con carpetas numeradas (`01_GUION` … `08_PUBLICAR`) y `00_ESTADO.md`, el tablero del video. El motor y los sonidos quedan en `%USERPROFILE%\EstudioPaltostaila`.

Sonidos: paquetes de Kenney (opengameart.org), licencia CC0, uso libre sin atribución.
