# Calendario

El archivo es `gerente\calendario.json`. Cada cambio guarda un respaldo en `gerente\respaldos\`. Una entrada equivale a una pieza en una red: `<ID>_<versión>_<pieza>_<red>`.

## Estados

`por_aprobar` → `aprobado` → `programado` (o `subido_privado`) → `publicado` → `medido_48h` → `medido_7d`. También `cancelado` y `error`.

## Comandos

| Comando | Para qué |
|---|---|
| `calendario.py importar "<P>"` | agrega las piezas de `publicacion.json` sin duplicar |
| `calendario.py ver [--mes AAAA-MM]` | tabla con la hora en Santiago y en los mercados del público |
| `calendario.py pendientes [--dias 7]` | qué espera aprobación, qué hay que subir, qué hay que medir |
| `calendario.py estado <id> <estado> [--enlace] [--nota]` | cambia el estado a mano |
| `calendario.py cupo [--mes]` | publicaciones de Metricool usadas frente al límite del plan |
| `calendario.py hoja "<P>"` | hoja para publicar a mano |

## Tareas programadas (scheduled tasks)

Se crean con las herramientas de programación de Claude. Cada una parte en una sesión nueva, así que su instrucción tiene que bastarse sola.

- **Vigía mensual de políticas:** en la nube, no necesita el PC. Ver `vigilancia.md`.
- **Revisión semanal del calendario y de las métricas:** necesita el PC encendido con la app de Claude abierta, porque los permisos de YouTube viven en el PC. Se crea cuando `yt_api.py autorizar` ya funcione.
- **La publicación en sí no depende de una tarea programada.** Se sube con días de anticipación y la plataforma publica a la hora (YouTube con `publishAt`, TikTok e Instagram en Metricool). Si el PC está dormido ese día, igual sale.


## Varios canales (gerente 0.2.0)
- `calendario.py canales [--mes AAAA-MM]`: una fila por canal con lo que espera aprobación, lo aprobado, lo programado o publicado del mes, los próximos 7 días, el estado del modo lanzamiento y el cupo de Metricool. Es la vista para empezar cada sesión cuando hay más de un canal.
- `ver --canal X`, `pendientes --canal X`, `cupo --mes --canal X`; `ver` ya trae la columna «canal».
- Cada canal puede tener sus zonas del público, su YouTube y su cuenta de Metricool en `config.json` → `"canales"`; sin eso, comparten el cupo general.
