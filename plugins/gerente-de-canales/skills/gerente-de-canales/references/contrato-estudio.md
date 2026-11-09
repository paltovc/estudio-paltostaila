# Contrato de archivos entre el estudio y el gerente

El estudio (arquitecto-de-video) y el gerente no comparten código: se comunican por archivos dentro de la carpeta de cada video. Así cada plugin se puede actualizar y revisar por separado.

## Lo que el gerente lee del estudio (nunca lo modifica)

| Archivo | Para qué |
|---|---|
| `07_RENDER*/<ID>_<v>_youtube.mp4`, `_con-subtitulos.mp4`, `_subtitulos.srt`, `_<nombre>_9x16.mp4` | las piezas que se publican |
| `07_RENDER*/terminado_<ID>_<v>.md` | puerta: filas 1 a 6 en ✓ |
| `06_RECETA/evaluacion_<video>.json` | puerta: clase A o B |
| `08_PUBLICAR/checklist_publicacion.md` | las 7 respuestas de monetización del publicador (el gerente las revisa) |
| `08_PUBLICAR/` títulos, descripción, capítulos, miniaturas y textos de Shorts | se pasan a `publicacion.json` |
| `canales/<canal>/canal.md` | voz, reglas y avisos del canal |

## Lo que el gerente escribe en la carpeta del video (archivos nuevos, nunca pisa)

| Archivo | Qué es |
|---|---|
| `08_PUBLICAR/publicacion.json` | qué se publica, dónde y cuándo; se cambia solo con `validar.py --adoptar`, que respalda el anterior como `publicacion_<n>.json` |
| `08_PUBLICAR/checklist_publicacion_monetizacion_<v>.md` | las 7 respuestas de monetización revisadas y la línea `MONETIZACIÓN: OK` |
| `08_PUBLICAR/aprobacion_<v>.md` | copia legible de la aprobación |
| `08_PUBLICAR/hoja_de_publicacion_<v>.md` | texto para subir a mano |
| `08_PUBLICAR/metricas/<videoId>_<fecha>.json` | mediciones |
| `08_PUBLICAR/aprendizajes_<fecha>.md` | lo que el estudio usa para el próximo video |

## Estado del gerente (fuera de las carpetas de video)

En `EstudioPaltostaila\gerente\`:
- `config.json`, `calendario.json` y `aprobaciones.json`, con respaldo automático en `respaldos\` en cada cambio;
- `registro_publicaciones.csv`, que solo se agrega, nunca se borra. **No se abre ni se guarda desde Excel**: lo bloquea o le cambia el separador. Para verlo, abrir una copia;
- `informes\`.

## Pendiente para una versión futura del estudio

En el arquitecto (próximo lote, con la regla de dos tiempos):
- que el publicador escriba también un `publicacion.json` borrador;
- que la entrevista del estudio llame primero a la ronda 0 del gerente cuando el canal no tiene `ESTRATEGIA.md`.
