# Métricas y avance hacia la monetización

## Fuentes, de la gratis a la que gasta

| Red | Fuente | Costo | Qué da |
|---|---|---|---|
| YouTube | `yt_api.py metricas <videoId> --proyecto "<P>"` | gratis | contadores, vistas y engagedViews, minutos, duración media, % visto, suscriptores, retención, países, fuentes de tráfico |
| YouTube | `yt_api.py progreso` | gratis | suscriptores, horas de largos en 365 días, vistas de Shorts en 90 días, frente a los umbrales de Partners |
| YouTube | YouTube Studio (Patricio) | — | impresiones y CTR de la miniatura, «Probar y comparar» títulos y miniaturas |
| TikTok, Instagram | conector de Metricool (`getAnalyticsDataByMetrics`) | gratis | alcance, vistas, interacciones; el plan gratis guarda 30 días, así que hay que medir dentro de ese plazo |
| Todas | vidIQ | créditos (5 por consulta de analítica) | solo dentro del presupuesto autorizado |

## Cuándo

1. **A las 48 h:** contadores del video frente a la mediana de los últimos videos del canal. Si quedó muy por debajo, ¿cambiar la miniatura o el título? Se propone; no se cambia sin un sí.
2. **A los 7 días:** retención leída como **tres problemas** (idea de youtube-agent-skill, MIT): **fuga del gancho** (lo que se pierde en los primeros 30 s; se arregla en el guion), **caídas** puntuales (un momento: cruzar con lo que se veía y decía en la receta del estudio) y **pendiente** del medio (pérdida lenta: ritmo; se arregla cortando). Si el gancho y la pendiente están bien y hay pocas vistas, el problema es el empaque (CTR). Más países y fuentes. Se escribe `<P>\08_PUBLICAR\aprendizajes_<fecha>.md`: primero el arreglo más grande, después 3 cosas que funcionaron, 3 que no y hasta 3 cambios. Eso lo lee el estudio (el `analista` del arquitecto lo convierte en reglas propuestas; guionista y editor de escenas lo aplican).
3. **Una vez al mes:** `yt_api.py progreso`, un resumen por red y un informe en `gerente\informes\informe_<AAAA-MM>.md`: avance hacia 500 y 1.000 suscriptores, qué formato y qué mercado funcionan, y la próxima meta. Recordar que el 01-02-2027 suben los umbrales para quien postule nuevo.

**Un solo analista de métricas:** el `analista-de-canal` del gerente mide (48 h, 7 días, mes) para todos los canales; el `analista` del arquitecto no vuelve a medir, solo saca aprendizajes creativos de lo medido. Con varios canales, un informe por canal y una línea conjunta.

## Reglas

- Separar el dato (lo medido) de la hipótesis (lo supuesto). Con pocos datos, decirlo.
- Nunca inventar cifras. Si una fuente no responde, se anota «sin datos».
- Para comparar videos de antes y después de fines de agosto de 2026 (cambio en cómo se cuentan las vistas de los largos), usar engagedViews.

Créditos: la lectura de la retención en tres problemas viene de youtube-agent-skill (Jake Schincariol, MIT); aviso completo en `creditos/` del plugin arquitecto-de-video y en su `references/creditos-terceros.md`.
