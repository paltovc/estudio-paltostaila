# Mercados: países, idiomas y reglas

Revisado el 08-11-2026. Las listas de países cambian: confirmar en la página oficial antes de decidir.

## La idea que ordena todo

- **Lo que se puede monetizar depende de dónde vive el creador** (país del canal y de la cuenta de pagos: AdSense en YouTube, TikTok Studio, panel profesional de Instagram). Tiene que ser el país real de residencia.
- **El país del público no habilita ni bloquea la monetización.** Las vistas de cualquier país suman. Lo que cambia según el público es:
  - cuánto paga cada vista: los anuncios suelen pagar más en Australia, Nueva Zelanda, EE. UU. y España que en la mayor parte de Latinoamérica;
  - el idioma;
  - la hora a la que conviene publicar;
  - las leyes del país del público sobre ciertos temas, como la publicidad de productos financieros (ver más abajo).
- Si algún día cambia el país de residencia, se rehace la tabla de abajo para el país nuevo antes de mover el canal.

## Monetización por plataforma según el país de residencia

✓ disponible · ✗ no disponible · ? las fuentes no coinciden: verificar en la app.

| Programa | Chile (hoy) | México | Brasil | Australia | Nueva Zelanda | Fuente |
|---|---|---|---|---|---|---|
| YouTube Partners (anuncios y fan funding) | ✓ | ✓ | ✓ | ✓ | ✓ | support.google.com/youtube/answer/7101720 y 13429240 |
| TikTok Creator Rewards (pago por vistas) | ✗ | ✓ | ✓ | ? | ✗ | listas de 8 países; verificar en TikTok Studio → Herramientas para creadores |
| Instagram Gifts | ✓ (5.000 seguidores) | ✓ | ✓ | ? | ? | creators.facebook.com |
| Instagram Subscriptions | ✓ (10.000 seguidores) | ✓ | ✓ | ? | ? | guías de 2026; verificar en el panel profesional |

Conclusión para un canal con residencia en Chile:
- El ingreso directo sale casi todo de **YouTube**.
- **TikTok** sirve para crecer y llevar gente a YouTube, a marcas o a afiliados, pero no paga por vistas.
- En **Instagram** hay regalos y suscripciones cuando el canal crezca.

## Idioma y mercados del público

| Mercado | Idioma | Cómo llegar | Nota |
|---|---|---|---|
| Chile, México, Colombia, Argentina, Perú, resto de Latinoamérica | español | canal en español (hoy) | ejemplos locales y moneda de cada país, con fuente |
| España, EE. UU. hispano | español | el mismo canal | dejar claro de qué país son las cifras |
| Australia, Nueva Zelanda | inglés | versión en inglés del video: pista de audio extra en YouTube o canal aparte | el público hispanohablante en Oceanía es chico; para crecer allá hace falta inglés. La línea de localización del estudio hoy va de inglés a español; de español a inglés sería trabajo nuevo |
| Brasil (más adelante) | portugués | localización al final de la hoja de ruta | — |

## Reglas del país del público para el canal de finanzas

- **Australia (ASIC, INFO 269):** un finfluencer sin licencia AFS no puede dar asesoría sobre productos financieros a australianos. ASIC está fiscalizando activamente (abril de 2026, junto con 16 reguladores). Se puede dar información factual sobre cómo funciona un producto. Recomendar qué comprar, prometer rentabilidad o llevar a la gente a contratar algo sí es un riesgo. Un aviso de «no es asesoría» no basta si el contenido recomienda.
- **Chile y el resto:** la asesoría de inversión también está regulada en varios países. Regla del canal: el canal **educa, no recomienda** productos, acciones ni monedas concretas, no promete resultados y lleva siempre el aviso «no es asesoría financiera». El revisor de guion del estudio ya marca las frases riesgosas.
- **YouTube (todas partes):** no monetizan los personajes de IA que se presentan como expertos humanos dando consejo de finanzas. El personaje del canal es un dibujo y no debe presentarse como asesor.

## Horas de publicación

- Cada pieza tiene una sola hora de salida. El calendario la muestra en Santiago y en las zonas de `config.json` → `zonas_publico` (CDMX, Bogotá, Buenos Aires, Madrid, Sídney, Auckland).
- En noviembre, las 19:00 de Santiago son las 09:00 del día siguiente en Sídney y las 11:00 en Auckland. Una misma hora no sirve bien a Latinoamérica y a Oceanía a la vez: las versiones en inglés para Oceanía se programan aparte.
- Para elegir la hora se mira dónde está el público real: YouTube Analytics por país (`yt_api.py metricas`) y las mejores horas de Metricool (`getBestTimeToPostByNetwork`) cuando las redes estén conectadas. Sin datos todavía, la hora se elige para el mercado principal del canal.
