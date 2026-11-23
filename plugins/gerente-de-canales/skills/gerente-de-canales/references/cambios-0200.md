# Gerente 0.2.0: modo lanzamiento por canal y varios canales

Estado: **compila; pendiente de prueba en el PC**. Las comprobaciones nuevas están en `prueba_gerente.py`, pero todavía no se corrieron.

## 1. Modo lanzamiento por canal (decisión de Patricio, 15-11-2026)
En los primeros 10 videos de cada canal:
- el evaluador aconseja y no bloquea;
- el juez revisa cada video antes de publicar;
- se hacen como máximo 2 versiones por video;
- la subida es a mano.

Los mínimos 8 (largo) y 7 (Short) siguen como referencia.

### Configuración (`gerente\config.json`; cambiarla necesita el sí de Patricio, igual que el nivel)
```json
"canales": {
  "finanzas": {"modo_lanzamiento": {"activo": true, "hasta_videos": 10, "ya_publicados": 0}}
}
```
- El canal se identifica por `publicacion.json` → `"canal"`, el mismo nombre de siempre.
- `ya_publicados` (opcional) suma los videos que el canal publicó antes de que existiera el gerente.
- Si la configuración está mal escrita (`hasta_videos` que no es un número de 1 a 100, `activo` que no es `true`), el modo queda **apagado**: rige la regla normal, la más estricta.
- El modo **no se activa solo**: hay que escribir esa línea para cada canal en que se quiera.

### Qué cambia y qué no
| | Regla normal | Modo lanzamiento activo |
|---|---|---|
| Evaluación con nota bajo 8/7 (o clase C) | ✗ bloquea | ⚠ AVISO: pasa **solo si** la aprobación vigente guarda la aceptación explícita de **esa** nota (misma huella del video evaluado, misma nota y clase) |
| Evaluación que falta, ilegible, sin huella o de otro video | ✗ | ✗ (igual) |
| Juicio del juez | si hay `juicio_<v>.md` y dice RECHAZADO: ✗ | obligatorio: el último `juicio_<v>.md` (o `_2`, `_3`…) tiene que decir APROBADO u OBSERVADO y ser posterior al video (o citar su sha256). Desde las correcciones (M2, B3): se busca también en `08_PUBLICAR`, la palabra va sola en la primera línea y un veredicto que no se reconoce cierra en los dos modos |
| Versión mayor que v2 | — | ⚠ AVISO (no bloquea) |
| Todo lo demás (terminado con huella, checklist de monetización, aprobación con huella, fechas, duplicados, enlace, cupo, canal confirmado) | igual | igual |

- **Cuándo termina:** cuando el canal ya tiene `hasta_videos` videos programados o publicados (sin contar el que se revisa) vuelve sola la regla normal, aunque la aprobación vieja guarde una aceptación.
- **Cómo se cuenta:** un «video» es un ID (LAN-001), con su largo y sus Shorts. Se cuentan los del calendario de ese canal en programado, publicado o medido, más los del registro en programado o publicado (el canal sale del calendario o del `publicacion.json` del proyecto).
- **Nueva regla en los dos modos:** un juicio RECHAZADO del juez cierra las puertas. Antes la regla («con rechazado no se sigue») estaba escrita, pero ninguna puerta la revisaba.

### Aprobación con la nota aceptada
```
python aprobar.py "<P>" --tabla
python aprobar.py "<P>" --por "Patricio" --huellas largo:<huella8> --acepto-nota "<motivo con palabras>"
```
- La tabla muestra el modo («modo lanzamiento: video 3 de 10 del canal …»), la evaluación de cada pieza con ⚠ si está bajo el mínimo, y el aviso de versión mayor que 2.
- Con el modo activo y una nota bajo el mínimo, `aprobar.py` **se niega** sin `--acepto-nota`. El motivo tiene que tener al menos 8 letras.
- Un solo `--acepto-nota` vale para todas las piezas de esa aprobación que estén bajo el mínimo, y la tabla dice cuáles son.
- Queda registrado en tres lugares:
  - `aprobaciones.json`, en la entrada de la pieza: `"aceptacion_nota": {"motivo", "por", "fecha", "nota", "clase", "minimo", "evaluacion", "sha256_evaluado", "evaluado", "huella_pieza", "modo": {"video", "hasta"}}`, junto a la huella y a quién aprobó;
  - `08_PUBLICAR\aprobacion_<v>.md`, con la línea «AVISO aceptado …»;
  - `gerente\diario\…_nota_aceptada.json`.
- Si después se evalúa otra vez y la nota cambia, la aceptación vieja no sirve: hay que aprobar de nuevo.
- Sin el modo activo, `--acepto-nota` no hace nada (se avisa y no se registra).

### Subida a mano
Durante el modo lanzamiento las piezas van con `"ruta": "manual"` en `publicacion.json`. Patricio sube y avisa, y se anota con `anotar.py --estado publicado --enlace <url>`. **Corregido tras el juicio (M4):** las puertas sí obligan la ruta manual en el modo lanzamiento; las rutas api, metricool y vidiq quedan cerradas (ver la sección «Correcciones tras el juicio del juez»).

## 2. Varios canales en paralelo
- `config.json` → `"canales"` → `<canal>` acepta, además del modo lanzamiento:
  - `"youtube"`: `canal_id`, `idioma`, `categoria`, `notificar` o `forzar_privado` propios. Lo que falte se toma del `"youtube"` general;
  - `"zonas_publico"`: las zonas del público de ese canal, para la tabla de aprobación y `calendario.py ver --canal`;
  - `"metricool"`: `limite_mes` y `blog_id`, si ese canal tiene su propia marca o cuenta. Sin esto, todos los canales comparten el cupo general, como hasta ahora.
- **Compatibilidad:** un canal sin configuración propia (finanzas hoy) da exactamente el mismo contexto en la huella de la aprobación, así que las aprobaciones vigentes no cambian. Si se le agrega `"youtube"` propio a un canal, sus aprobaciones vigentes dejan de valer (la huella incluye el contexto) y hay que aprobar de nuevo. Eso es a propósito.
- `yt_api.py canal --confirmar --canal <nombre>` fija el `canal_id` solo para ese canal. `yt_api.py subir` lee el canal confirmado, el idioma y los avisos del canal del proyecto. La pista de subtítulos va con el idioma de la pieza o del canal y su nombre (Español, English, Português). El flujo de la subida no cambió.
- **Límite:** el permiso de YouTube (`claves\youtube_token.json`) sigue siendo uno solo. Si el canal confirmado de un proyecto no es el del permiso, `subir` se niega («el permiso de YouTube es de otro canal»). Para un segundo canal de YouTube: ruta manual (la del modo lanzamiento) hasta que se haga un permiso por canal (pendiente; toca la subida).
- `calendario.py`:
  - `ver --canal X` y `pendientes --canal X`;
  - `ver` ahora lleva la columna «canal» (vista conjunta);
  - `cupo --mes --canal X` usa el cupo propio si el canal tiene cuenta de Metricool, y si no, avisa que el cupo es compartido;
  - **`calendario.py canales [--mes]`**: una fila por canal con lo que espera aprobación, lo aprobado, lo programado o publicado del mes, los próximos 7 días, el estado del modo lanzamiento y el cupo de Metricool.
- `validar.py` agrega avisos, sin errores nuevos: el canal de `publicacion.json` no coincide con el de `proyecto.json`, o el canal no tiene configuración propia cuando ya hay otros configurados.
- La puerta del cupo de Metricool cuenta por canal cuando el canal tiene cuenta propia.
- No había prefijo FIN fijo en el gerente: los nombres salen de `id` y `version` de `publicacion.json`.

## Archivos
`comun.py` (nuevas: `canal_cfg`, `youtube_de`, `zonas_de`, `videos_publicados`, `modo_lanzamiento`, `numero_version`; `contexto` usa `youtube_de`), `puertas.py`, `aprobar.py`, `calendario.py`, `validar.py`, `yt_api.py` (solo lectura de la configuración), `prueba_gerente.py` y `VERSION` = 0.2.0.

## Documentos
- `niveles-y-puertas.md`, `publicar.md` y `calendario.md` **sí se tocaron en este lote** (modo lanzamiento, puerta del juez, `--acepto-nota`, subida a mano, `calendario.py canales` y `--canal`). Antes este punto decía que no se habían tocado: era un error.
- `agents/distribuidor.md` ya nombra `--acepto-nota`, el tipo de video y la subida a mano con `calendario.py hoja` en el modo lanzamiento. La fila «Publicar» del `SKILL.md` del gerente ya nombra `--acepto-nota` y que en lanzamiento la subida es solo a mano: en el SKILL ya no falta nada. Queda solo `publicar.md` (línea de `calendario.py hoja`), que no dice que la hoja corre las puertas y lleva el sha256 (M1). Es seguro igual: los scripts se niegan con un mensaje claro.
- `agents/juez.md` del estudio: la primera línea del juicio es solo la palabra del veredicto y la segunda `sha256: <hex del video revisado>`. Desde las correcciones el gerente lee exactamente ese formato (ya no busca en las tres primeras líneas).

## Correcciones tras el juicio del juez (16-11-2026, `juicio_0150_g020.md`)
Estado: **compila (`py_compile`); pendiente de prueba en el PC.** Las comprobaciones nuevas están en `prueba_gerente.py` (y dos del motor en `prueba.py`), sin correr. Decisiones de Patricio: en lanzamiento, solo a mano (M4); el tipo de video puede cambiar la nota, con un piso para «riesgos» (M3).

| Hallazgo | Qué cambió | Archivo |
|---|---|---|
| **M1** ruta manual sin puertas | `calendario.py hoja` corre `puertas.revisar` por cada destino manual (las mismas puertas que la ruta api: terminado con huella, monetización, evaluación o nota aceptada en modo lanzamiento, juicio del juez, aprobación vigente con huella…). Si alguna está cerrada **no escribe la hoja**, muestra la tabla y lista lo que falta (sale con 1). La hoja lleva el **sha256 completo** del archivo aprobado (y sus 8 primeras letras), cómo comprobarlo (`Get-FileHash`), quién aprobó y con qué huella de la pieza, y los AVISOS (⚠) del modo lanzamiento. `anotar.py --estado programado/publicado/subido_privado` ya no exime a la ruta manual: sin aprobación vigente con la huella del archivo **y** la de la pieza, la nota queda «IRREGULAR … (ruta manual)». | `calendario.py`, `anotar.py` |
| **M2** carpeta del juicio | El juicio se busca en la carpeta de publicación del proyecto (`proyecto.json` → `carpetas` → `publicar`, p. ej. `08_PUBLICAR_ESTUDIO`) **y** en `08_PUBLICAR`; manda el más reciente de las dos. Así un RECHAZADO cierra y un APROBADO/OBSERVADO abre en ambos casos. | `puertas.py` (`carpetas_juicio`, `revisar_juicio`) |
| **B3** lectura del veredicto | El veredicto es la **primera línea con texto** y tiene que ser exactamente APROBADO, OBSERVADO o RECHAZADO (sin importar mayúsculas). «NO APROBADO», «Veredicto: …», un título antes o texto después de la palabra = «?», que **cierra en los dos modos**. Si la segunda línea es `sha256: <hex>` (8 a 64 letras), tiene que coincidir con el archivo que se sube (o con un video de la misma corrida de `terminado.py`, p. ej. el largo cuando se sube su Short); si no coincide, o el sha256 no se puede leer, cierra en los dos modos. Sin sha256 se mantiene el criterio de fecha (en modo lanzamiento el juicio tiene que ser posterior al video). | `puertas.py` (`leer_juicio`) |
| **M4** subida a mano en el lanzamiento | Con el modo lanzamiento activo en el canal, cada destino con ruta `api`, `metricool` o `vidiq` queda cerrado: «modo lanzamiento: subida a mano (hoja de calendario)». Eso cierra `yt_api.py subir` (subida y programación) y `anotar.py --reservar` (Metricool, vidIQ). La tabla de `aprobar.py` lo marca ✗ en esos destinos. Fuera del modo, todo igual. | `puertas.py`, `aprobar.py` |
| **M3** tipo de video y nota | Motor: piso del eje «riesgos» (10 %, el de siempre) en `evaluar.py`; con `tipo_video`, el tipo y los pesos usados quedan escritos en la evaluación (.md y .json). Gerente: la fila de la evaluación de `puertas.py` y `aprobar.py --tabla` muestran «tipo de video «x» (pesos …)» o «tipo de video no registrado (pesos de siempre)». La aceptación de la nota guarda también `tipo_video` y `pesos`. Sin `tipo_video`, nada cambia. | `evaluar.py` (motor), `puertas.py`, `aprobar.py` |
| **B1** sello sin origen | `terminar.py --solo-audio` sin sello previo que calce no escribe sello; `terminado.py` trata un sello sin origen como «sin sello» (punto 14 recomendado). | `terminar.py`, `terminado.py` (motor; ver `motor-0150-general.md`) |
| **B2** contador del lanzamiento | `calendario.py canales` avisa, por canal en modo lanzamiento, las piezas con la fecha pasada que siguen sin anotar como publicadas (por aprobar, aprobadas, en curso, inciertas o subidas en privado): «(⚠ N sin anotar)» en la tabla y una línea AVISO con los ids y qué hacer. | `calendario.py` |

**Compatibilidad:** las huellas de las aprobaciones no cambian (no se tocó `contexto` ni `huella_pieza`). `revisar_juicio` ahora devuelve cuatro valores (solo lo usa `puertas.py`). Lo que cambia de comportamiento: (1) la hoja manual ya no se escribe con las puertas cerradas; (2) en modo normal, un juicio con veredicto que no se reconoce o de otro video ahora cierra (antes solo RECHAZADO); (3) un juicio con un título antes del veredicto ya no vale (el formato de `agents/juez.md` es la palabra sola en la primera línea).

**Pruebas nuevas en `prueba_gerente.py`:** hoja con puertas cerradas (no escribe) y abiertas (lleva el sha256); «NO APROBADO», texto tras la palabra y título antes = «?»; sha256 de otro video o ilegible; juicio anterior al video sin sha256; juicio en `08_PUBLICAR` con `"publicar": "08_PUBLICAR_ESTUDIO"` (abre) y RECHAZADO más reciente en `08_PUBLICAR_ESTUDIO` (cierra); ruta api cerrada en lanzamiento y `yt_api.subir(..., simular=True)` que se niega; tipo de video en puertas y en la tabla; aviso de piezas sin anotar en `calendario.py canales`; `anotar.py` manual sin IRREGULAR con aprobación vigente y con IRREGULAR cuando la huella de la pieza cambió. Se ajustaron dos pruebas viejas al formato exacto del juez («OBSERVADO: se puede seguir» y «**Veredicto: RECHAZADO**» ya no son veredictos válidos).

## Correcciones de la verificación (N1-N3, N6)
Según `juicio_0150_g020_verificacion.md` (16-11-2026). Estado: **compila (`py_compile`); pendiente de prueba.**

| Hallazgo | Qué cambió | Archivo |
|---|---|---|
| **N1** sha del «hermano» (estricto, decisión de Patricio) | El juicio puede traer varias líneas `sha256: <hex>` seguidas después de la primera (una por video revisado). Vale si una es la del archivo que se sube o la de su par `_youtube` / `_con-subtitulos` sellado en la misma corrida de `terminado.py`. Nunca un borrador, la copia del celular, un Short u otra prueba: un Short necesita su propio sha256. Sin ningún sha256 se mantiene el criterio de fecha. Esto reemplaza lo que decía B3 sobre «un video de la misma corrida». | `puertas.py` (`leer_juicio`, `pareja_del_largo`, `revisar_juicio`) |
| **N2** duplicados en la ruta manual | La ruta manual corre también `ya_enviado`: una segunda hoja de algo ya publicado o programado sale cerrada («no se envió antes» ✗). | `puertas.py` |
| **N3** `anotar.py` manual | Al anotar programado, publicado o subido_privado por la ruta manual, corre `puertas.revisar` y, si la puerta del juicio o de la evaluación está cerrada (p. ej. un RECHAZADO que llegó después de aprobar), la nota queda «IRREGULAR: puerta cerrada al anotar: …». No bloquea: anota igual. | `anotar.py`, `puertas.py` (`cerradas_juicio_evaluacion`) |
| **N6** codificación del juicio | Se lee en UTF-8 con o sin BOM y en UTF-16 con BOM. Si no se puede decodificar, cierra con «no se pudo leer el juicio (codificación)». | `puertas.py` (`_texto_juicio`) |

**Pruebas nuevas en `prueba_gerente.py`, sin correr:** el sha256 de un borrador o de un Short no abre el largo; el par `_con-subtitulos` sí abre el `_youtube`; el sha256 del largo solo no abre el Short; un juicio con dos sha256 abre el largo y el Short; juicio en UTF-16 y en UTF-8 con BOM; juicio que no se puede decodificar; segunda hoja de algo ya publicado cerrada; RECHAZADO después de aprobar deja IRREGULAR lo anotado a mano.

## Pruebas sugeridas en el PC
1. `python prueba_gerente.py`: tiene que terminar en «PRUEBA SUPERADA», con los puntos nuevos de «0.2.0» (canal LAN-001 de prueba).
2. En la copia de trabajo, sin tocar el gerente instalado: `calendario.py canales` con el calendario real copiado.
3. Con FIN-002, sin configuración propia: `aprobar.py --tabla` tiene que dar **las mismas huellas de 8 letras** que antes del cambio.
4. Agregar `"canales": {"finanzas": {"modo_lanzamiento": {"activo": true, "hasta_videos": 10}}}` en una copia de `config.json` (con `ESTUDIO_BASE` apuntando a una carpeta de prueba). Revisar la tabla, `puertas.py` sin juicio (cerrada), con `juicio_v<n>.md` OBSERVADO (abierta si la nota pasa o fue aceptada) y con RECHAZADO (cerrada).
5. `yt_api.py subir --simular` en un proyecto con `"youtube": {"idioma": "en"}` en su canal: `defaultLanguage` tiene que salir «en».
