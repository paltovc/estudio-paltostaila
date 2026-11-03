---
name: buscar-tendencias
description: Busca qué videos de un tema o nicho están superando por mucho a su propio canal en YouTube y Shorts y propone ideas priorizadas con respaldo de datos para el calendario. Usar cuando se pregunte "sobre qué hago los próximos videos", "qué está funcionando en mi nicho", "tendencias", "ideas para el canal", "revisión semanal de tendencias".
---

# Buscar tendencias

1. Lanzar al agente **cazador-de-tendencias** con el canal (biblia) y, si hay, el calendario de videos.
2. El agente corre en el PC `scanner_youtube.py` (API oficial de YouTube, si hay clave en `claves\youtube.env`) con 10-16 búsquedas escritas como las escribiría el público; sin clave, `tendencias.py` con 3-5. La nota de cada video es vistas / mediana de los últimos 10 videos de su canal. Si el conector de vidIQ está disponible, lo usa para complementar.
3. Revisar las ideas propuestas: cada una con título tentativo, ángulo propio fiel a la biblia, referente que la respalda ("x canal" y enlace), formato y prioridad.
4. Ofrecer: analizar a fondo los 2-3 mejores referentes (skill **analizar-referente**) y, con un sí, sumar las ideas al calendario en Notion o Google Sheets.

Una búsqueda en la nube (sin PC) puede orientar, pero los números confiables salen de `tendencias.py` o de vidIQ. Decirlo si se trabaja sin computador.
