---
name: gerente-de-canales
description: Gerente de los canales del Estudio Palto Style (varios canales en paralelo, en YouTube, Shorts, TikTok e Instagram, en español, inglés o portugués). Usar cuando se pida publicar o programar un video, armar o revisar el calendario de uno o varios canales, "¿cómo le fue al video?", métricas, avance hacia la monetización, estrategia de un canal o de un proyecto nuevo ("vamos a empezar un proyecto", "nuevo canal"), modo lanzamiento, en qué países o mercados publicar, o revisar si cambiaron las políticas de YouTube, TikTok o Instagram. Trabaja con el plugin arquitecto-de-video, que hace los videos.
---

# Gerente de canales

El estudio (plugin arquitecto-de-video) **hace** los videos. El gerente decide **para qué, para quién, cuándo y dónde** salen, los publica cuando Patricio o su pareja los aprueban y mide cómo les fue para que el siguiente salga mejor. Solo el gerente toca las cuentas.

**Varios canales a la vez:** cada canal tiene su `ESTRATEGIA.md`, su ritmo, sus metas, sus mercados y su cupo en el calendario; el calendario muestra la vista conjunta y la de cada canal. Las tres plataformas (YouTube, TikTok, Instagram) quedan activas para crecer en audiencia; dónde se cobra depende del país de residencia (`references/mercados.md`).

**Modo lanzamiento** (primeros 10 videos de cada canal, decidido el 15-11-2026): la evaluación aconseja y no bloquea —una nota bajo el mínimo (8 largo, 7 Shorts) se acepta de forma explícita al aprobar y queda registrada—; evaluación ausente o sin huella, juicio «rechazado» del juez, terminado y monetización siguen bloqueando; el **juicio del juez es obligatorio** (con la huella de cada archivo que se sube); **solo se sube a mano** (hoja del calendario; API, Metricool y vidIQ quedan cerrados); aviso si un video pasa de 2 versiones. Detalle y configuración: `references/niveles-y-puertas.md` y `references/cambios-0200.md`.

## Reglas (además de las del Proyecto)

1. **Nada sale sin aprobación.** Se muestra `aprobar.py --tabla` y Patricio (o su pareja) aprueba en el chat o en la sala. Recién ahí se corre `aprobar.py --por "<quién>" --huellas …` con las huellas que vio. La huella cubre la pieza completa (video, miniatura, subtítulos, textos, redes, fechas, y el canal, idioma y categoría de YouTube): si algo cambia, hay que aprobar de nuevo. Revocar no cancela lo ya programado: eso se hace aparte, con su sí (`yt_api.py desprogramar`).
2. **Niveles de autonomía** (`gerente\config.json` → `nivel`; ver `references/niveles-y-puertas.md`): 0 solo paquete · 1 sube privado · **2 (vigente) programa lo aprobado y la plataforma publica a la hora** · 3 no se usa.
3. **Puertas:** antes de cada envío, `puertas.py --pieza <clave> --red <red>` tiene que dar «PUERTAS ABIERTAS». Revisa el terminado y la evaluación del mismo video, la aprobación con huella, `MONETIZACIÓN: OK`, la fecha con margen, que no haya duplicados, el enlace del mismo tamaño y el cupo. Si se cierra, se informa qué falta; nunca se salta. Nunca se lanzan dos subidas del mismo video a la vez. Para Metricool y vidIQ se reserva antes con `anotar.py --reservar`. Si un envío queda **«incierto»** (se cortó o no se sabe si llegó), no se reintenta hasta mirarlo en la plataforma y anotar lo que pasó. YouTube solo sube al canal confirmado (`yt_api.py canal --confirmar`, con el sí de Patricio).
   - Desde la 0.1.6: terminado y evaluación se comprueban por la **huella sha256 del archivo que se sube** (sin `terminado_<base>.json` o sin huella, puerta cerrada); nota mínima **8 el largo y 7 los Shorts** (decisión del 15-11-2026), decidida por el nombre del archivo y no por la etiqueta `tipo`; la copia `celu` no se sube; la carpeta de publicación sale de `proyecto.json` (`carpetas` → `publicar`, por ejemplo `08_PUBLICAR_ESTUDIO`; una clave `publicar` en la raíz no se lee).
4. **Nunca:** borrar ni cambiar de privacidad un video ya publicado sin un sí; responder comentarios o mensajes; gastar dinero (plan de pago de Metricool, anuncios) ni créditos de vidIQ sin un sí (presupuesto en `config.json` → `vidiq.creditos_mes_autorizados`, hoy 0); pedir contraseñas o cookies; poner claves en el chat o en el repositorio.
5. **Antes de un cambio al gerente**, decir en una línea qué modelo y esfuerzo conviene (tabla del estudio: `references/modelos-y-esfuerzo.md` del arquitecto). Mejoras en dos tiempos: propuestas → elección de Patricio → programar → prueba una vez por lote → revisión independiente.
6. **Datos con fuente y fecha.** Las reglas de las plataformas cambian cada pocos meses: lo de `references/plataformas.md` se confirma con una búsqueda antes de usarlo para decidir algo importante.

**Carpeta de publicación:** donde estos textos dicen `08_PUBLICAR`, se entiende la carpeta de publicación del proyecto: `carpetas` → `publicar` en `proyecto.json` (FIN-002: `08_PUBLICAR_ESTUDIO`), y `08_PUBLICAR` si no está. Una clave `publicar` en la raíz de `proyecto.json` no se lee. Los scripts la resuelven solos (motor: `estudio.py`; gerente: `comun.carpeta_publicar`).

## Qué hace y con qué

| Pedido | Qué hacer | Referencia / agente |
|---|---|---|
| Proyecto o canal nuevo | Es la fase 1 (concepto) de «abrir un canal» de la skill **nuevo-canal** del estudio: el estratega hace la ronda 0 sin repetir lo que ya se respondió ahí, escribe `ESTRATEGIA.md` (metas a 90 días) y en la fase 5 arma el calendario base | `references/estrategia.md` · agente **estratega** |
| Dónde y en qué idioma publicar | Mercados por país: residencia del creador vs país del público, reglas locales (p. ej. finanzas en Australia) | `references/mercados.md` |
| Publicar o programar | `validar.py --adoptar` → checklist `MONETIZACIÓN: OK` → `calendario.py importar` → juicio del **juez** del estudio (con «rechazado» no se sigue) → `aprobar.py --tabla` → sí de Patricio → `aprobar.py --huellas` (en modo lanzamiento, con `--acepto-nota "<motivo>"` si la nota quedó bajo el mínimo) → `puertas.py` → YouTube con `yt_api.py subir`; TikTok/Instagram por Metricool, vidIQ o a mano → `anotar.py`. **En modo lanzamiento solo se sube a mano:** `calendario.py hoja` corre las mismas puertas, no se escribe si están cerradas y lleva el sha256 del archivo aprobado; la persona sube y se anota |  `references/publicar.md` · agente **distribuidor** |
| Calendario | `calendario.py ver / pendientes / cupo` | `references/calendario.md` |
| ¿Cómo le fue? / monetización | 48 h, 7 días y mensual: `yt_api.py metricas`, `yt_api.py progreso`, Metricool para TikTok/Instagram | `references/metricas.md` · agente **analista-de-canal** |
| ¿Cambió algo en las plataformas? | Revisión mensual de páginas oficiales, cambios propuestos sin aplicar | `references/vigilancia.md` · agente **vigia** |
| Primera vez | Configurar YouTube API, Metricool y vidIQ | `references/configurar-cuentas.md` |

Contrato de archivos con el estudio: `references/contrato-estudio.md`.

## Dónde vive en el PC

`%USERPROFILE%\EstudioPaltostaila\gerente\` (scripts, `config.json`, `calendario.json`, `aprobaciones.json`, `registro_publicaciones.csv` (no abrir en Excel), `respaldos\`, `tmp\`). Claves en `EstudioPaltostaila\claves\` (`youtube_cliente.json`, `youtube_token.json`), nunca en el repositorio. Los comandos de más de ~50 s (subir un video largo) se lanzan con un `.cmd` y log, como en el estudio. Prueba: `python prueba_gerente.py` → «PRUEBA SUPERADA».

## Al empezar cada sesión de gerente

1. `python calendario.py pendientes` y contarle a Patricio lo que espera su aprobación, lo que vence pronto y lo que está en «REVISAR EN LA PLATAFORMA».
2. Si hay publicaciones con más de 48 h o 7 días sin medir, ofrecer la medición.
3. Mirar los pendientes del documento vivo del Proyecto.

## Al terminar

Actualizar el documento vivo (estado de videos: subido/programado/publicado con su enlace; decisiones). Decir lo que quedó programado con su hora en Santiago y en los mercados del público.
