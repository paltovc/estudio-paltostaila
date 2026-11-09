# Plataformas: cómo se publica y se mide (verificado el 08-11-2026)

Confirmar con una búsqueda antes de decidir algo importante; anotar aquí la fecha y la fuente de cada cambio (lo hace el agente vigía cada mes, con el sí de Patricio).

## YouTube: API propia del estudio (ruta `api`)

- Se sube con OAuth del canal (`yt_api.py autorizar`). La clave de `youtube.env` solo lee datos públicos.
- **02-11-2026:** Google levantó la restricción de 2020. Las subidas desde proyectos de Google Cloud **sin verificar ya no quedan forzadas a privado** (developers.google.com/youtube/v3/revision_history). El estudio igual sube siempre en privado y deja que YouTube publique a la hora con `publishAt`.
- **Cuota (desde el 01-06-2026):** las subidas tienen su propio cupo de 100 por día. Miniatura, subtítulos y listas usan el cupo general de 10.000 unidades.
- **`publishAt`** solo funciona en un video privado que nunca se publicó. Con una fecha pasada, YouTube puede rechazarlo o publicar de inmediato (no verificado). Por eso `puertas.py` exige un margen de 30 minutos más el tiempo de subida y lo vuelve a revisar justo antes de enviar.
- **Campos que el estudio siempre declara:** `selfDeclaredMadeForKids` (para niños) y `containsSyntheticMedia` (contenido alterado o sintético realista).
- **Miniatura personalizada y videos de más de 15 min** necesitan el canal verificado por teléfono (youtube.com/verify).
- **Shorts:** no existe una API aparte. YouTube decide solo si el video es un Short, según el formato vertical y la duración (hasta 3 min).
- **Métricas:** YouTube Analytics API (gratis): vistas, engagedViews, tiempo de visualización, retención, países y fuentes. Desde fines de agosto de 2026 (el 24-08 según la prensa especializada; por confirmar en la página oficial), «views» de los videos largos cuenta desde el primer cuadro; los Shorts ya contaban así desde 2025. Para comparar con fechas anteriores, usar engagedViews. Las impresiones y el CTR de la miniatura se miran en YouTube Studio.

## TikTok

- **API propia:** un cliente sin auditar publica solo como «solo yo» y la cuenta tiene que estar privada. La auditoría está pensada para apps con muchos usuarios. **No se usa.**
- **Metricool (ruta `metricool`):** su app ya está auditada y publica en público en automático (`autoPublish: true`). Necesita un **enlace público** al video. Campos: `privacyOption PUBLIC_TO_EVERYONE`, `isAigc` (contenido hecho con IA) y `title`.
- **Monetización:** Creator Rewards no está disponible para residentes en Chile (ver mercados.md).

## Instagram

- **Metricool (ruta `metricool`):** Reels con `instagramData.type REEL`, `isAiGenerated` y `showReelOnFeed`. Necesita cuenta profesional conectada y enlace público al video.
- **vidIQ (alternativa sin alojar el archivo):** `vidiq_instagram_publish_reel` publica un Reel a partir del enlace de YouTube de un Short ya público, sin costo de créditos. Publica en el momento, sin programar, y necesita el Instagram conectado en vidIQ.
- **API de Meta propia:** hasta 100 publicaciones por API cada 24 h, video en una dirección pública y token de 60 días. No se usa mientras sirvan Metricool o vidIQ.

## Metricool (cuenta del estudio: marca 7952517)

- **Plan gratis:** 20 publicaciones al mes **en total** (no 20 por red). Una misma publicación enviada a 2 redes gasta 2. Solo cuenta lo que se publica y el contador vuelve a cero el día 1. Analítica de 30 días.
- **El conector para Claude funciona en el plan gratis.**
- **Starter** desde ~16 €/mes anual y **Advanced** desde ~43 €/mes. Solo con el sí de Patricio.
- Estado al 08-11-2026: la marca existe pero no tiene redes conectadas.

## vidIQ

- **Plan gratis:** 150 créditos al mes (al 08-11-2026 quedaban 140; se renuevan el 22-11-2026).
- **Analítica del canal:** 5 créditos por consulta. Publicar un Reel: 0 créditos (lo dice la propia herramienta de vidIQ).
- Se gasta solo dentro del presupuesto autorizado (`config.json` → `vidiq.creditos_mes_autorizados`, hoy 0).
- Al 08-11-2026 no tenía canal de YouTube ni Instagram conectados.

## Monetización de YouTube (Programa de Partners)

- **Fan funding:** 500 suscriptores, 3 subidas públicas en 90 días y 3.000 h de visualización en 12 meses (o 3 M de vistas de Shorts en 90 días).
- **Anuncios:** 1.000 suscriptores y 4.000 h (o 10 M de vistas de Shorts en 90 días).
- **Desde el 01-02-2027**, quien postule nuevo necesitará 8.000 h o 20 M de vistas de Shorts, según varias fuentes de 2026. Confirmar en support.google.com/youtube/answer/72851 antes de planificar con eso.
- **Política de contenido no auténtico (aclarada el 16-07-2026):** no se monetiza el contenido genérico o de plantilla, el perturbador ni el de personajes de IA que dan consejo de finanzas, salud o leyes presentándose como expertos humanos. Se evalúa el canal completo: publicar más no compensa si los videos se parecen demasiado entre sí.
- **Voz:** usar una voz con licencia comercial clara. edge-tts no la da explícita.
