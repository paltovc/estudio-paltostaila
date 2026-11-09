# gerente-de-canales

Plugin compañero del **arquitecto-de-video**: el estudio hace los videos y el gerente los lleva a las plataformas.

- **Estrategia:** ronda 0 de preguntas al empezar un canal, una serie o un proyecto, con metas a 90 días.
- **Mercados:** reglas por país. La monetización depende de dónde vive el creador; el público cambia el idioma, la hora, cuánto paga cada vista y las reglas locales.
- **Publicación aprobada (nivel 2):**
  - YouTube con la API propia, gratis, que sube en privado y deja que YouTube publique a la hora (`publishAt`);
  - TikTok e Instagram por Metricool (plan gratis: 20 publicaciones al mes) o a mano.
- **Puertas automáticas:** terminado sin ✗, evaluación A/B, aprobación con huella del archivo, checklist de monetización, sin duplicados, cupo.
- **Métricas:** a las 48 h, a los 7 días y cada mes, más el avance hacia el Programa de Partners de YouTube.
- **Vigilancia mensual** de políticas y de mejores prácticas.

Instalación en el PC: `scripts\instalar_gerente.cmd` (deja todo en `%USERPROFILE%\EstudioPaltostaila\gerente` y corre la prueba). Primera configuración de cuentas: `skills/gerente-de-canales/references/configurar-cuentas.md`.

## Cambios

- **0.1.2 (08-11-2026):** antes de pedir la aprobación, el agente **juez** del estudio da su veredicto (con «rechazado» no se publica).
- **0.1.1 (08-11-2026, revisión de Codex):** la aprobación también cubre el canal, el idioma y la categoría de YouTube y muestra todo lo que se publica; YouTube sube privado y sin fecha, y solo programa si miniatura, subtítulos y lista salieron bien; solo sube al canal confirmado; los envíos cortados quedan «incierto» y bloquean reintentos; reservas antes de Metricool y vidIQ; el enlace de Metricool se compara por contenido (sha256); ventana horaria para vidIQ; fechas sin desfase y sin horas inexistentes o repetidas por el cambio de hora; `desprogramar` no toca lo que sale en menos de 10 minutos y actualiza el calendario; bloqueos con dueño; diario de operaciones; se quitó `--reemplaza`. Prueba: 63 puntos.
- **0.1.0 (08-11-2026):** primera versión.
