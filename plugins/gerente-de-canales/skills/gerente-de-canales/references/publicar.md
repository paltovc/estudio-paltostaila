# Publicar: del paquete del estudio a las plataformas

Todos los comandos se corren en `%USERPROFILE%\EstudioPaltostaila\gerente`. `<P>` es la carpeta del proyecto del video.

## 1. publicacion.json (lo escribe el distribuidor)

Se arma con lo que dejó el estudio: los archivos de `07_RENDER` (o `07_RENDER_ESTUDIO`), y el título elegido, la descripción con capítulos y fuentes, las etiquetas, la miniatura y los textos de los Shorts que están en `08_PUBLICAR`.
- Se escribe primero como `<P>\08_PUBLICAR\publicacion_nueva.json` y se adopta con `python validar.py "<P>" --adoptar "<P>\08_PUBLICAR\publicacion_nueva.json"`.
- `--adoptar` respalda el anterior como `publicacion_<n>.json` y solo adopta un archivo válido.
- Las rutas de los archivos son relativas a la carpeta del proyecto.

```json
{"id": "FIN-002", "version": "v10", "canal": "finanzas",
 "piezas": [
  {"clave": "largo", "archivo": "07_RENDER_ESTUDIO/FIN-002_v10_youtube.mp4", "tipo": "largo",
   "titulo": "…", "descripcion": "…", "etiquetas": ["…"], "miniatura": "08_PUBLICAR/FIN-002_miniatura_1.png",
   "subtitulos": "07_RENDER_ESTUDIO/FIN-002_v10_subtitulos.srt", "lista": "<id de lista opcional>",
   "para_ninos": false, "ia_realista": false, "idioma": "es",
   "destinos": [{"red": "youtube", "ruta": "api", "fecha": "2026-11-12T19:00", "zona": "America/Santiago"}]},
  {"clave": "short1", "archivo": "07_RENDER_ESTUDIO/FIN-002_v10_short1_9x16.mp4", "tipo": "short",
   "titulo": "… #shorts", "texto": "… #ahorro", "texto_instagram": "(opcional, si cambia)",
   "para_ninos": false, "ia_realista": false,
   "destinos": [{"red": "youtube", "ruta": "api", "fecha": "2026-11-13T13:00", "zona": "America/Santiago"},
                {"red": "tiktok", "ruta": "metricool", "fecha": "2026-11-13T19:00", "zona": "America/Santiago", "enlace_publico": ""},
                {"red": "instagram", "ruta": "manual", "fecha": "2026-11-14T19:00", "zona": "America/Santiago"}]}]}
```

- `ia_realista` es true solo si hay escenas realistas que no ocurrieron, una persona real diciendo algo que no dijo o un lugar real alterado. El personaje dibujado no cuenta. Ante la duda, true: declararlo no baja el alcance.
- La descripción de finanzas lleva siempre el aviso «Contenido educativo, no es asesoría financiera».
- Para no repetir el mismo contenido el mismo día en todas las redes, conviene separar las fechas uno o dos días.
- `publicacion.json` es la única fuente de las fechas. El calendario se pone al día con `calendario.py importar`. Si cambia una fecha, la aprobación de esa pieza deja de valer y hay que preguntar de nuevo.
- Rutas por red: YouTube `api` o `manual`; TikTok `metricool` o `manual`; Instagram `metricool`, `vidiq` o `manual`.
- Checklist de monetización: el distribuidor lee las 7 respuestas del checklist del publicador y, si todas están bien, escribe un archivo nuevo, `checklist_publicacion_monetizacion_<v>.md`, con las respuestas y la línea `MONETIZACIÓN: OK`. Si alguna está mal, no escribe esa línea y se lo cuenta a Patricio.

## 2. Revisar, calendario y aprobación

```
python validar.py "<P>"
python calendario.py importar "<P>"
python calendario.py cupo --mes 2026-11
```

Antes de la aprobación, el agente **juez** del estudio (`arquitecto-de-video:juez`, modo video) revisa el video y este paquete y deja `08_PUBLICAR\juicio_<v>.md`. Con «rechazado» no se pide la aprobación; con «observado», sus observaciones van junto a la tabla.

Aprobación (detalle en `niveles-y-puertas.md`):

```
python aprobar.py "<P>" --tabla
```

Se le muestra la tabla a Patricio, con la nota del evaluador, y se pregunta. Con su sí:

```
python aprobar.py "<P>" --por "Patricio" --huellas largo:<huella8>,short1:<huella8>
```

Después se pasan a «aprobado» esas entradas del calendario (`calendario.py estado <id> aprobado`).

## 3. YouTube (ruta `api`)

```
python puertas.py "<P>" --pieza largo --red youtube
python yt_api.py subir "<P>" largo --simular      (muestra exactamente lo que se enviará)
```

La subida real de un video largo tarda más que el corte de la terminal, así que se lanza en segundo plano con un log, igual que los renders del estudio:
- se escribe `gerente\tmp\subir_<pieza>.cmd` con estas líneas (las dos primeras evitan problemas con tildes y con los signos ✓ ✗):
  ```
  chcp 65001>nul
  set PYTHONUTF8=1
  cd /d "%USERPROFILE%\EstudioPaltostaila\gerente"
  python yt_api.py subir "<P>" <pieza>
  ```
  El archivo se guarda en UTF-8;
- se lanza con `Start-Process cmd.exe` hacia `subir_<pieza>.log`, con las comillas dobles que indica el traspaso;
- después se lee el log.

Resultado esperado: «LISTO programado: https://youtu.be/…».
- Si el log dice «YA HAY UNA SUBIDA EN CURSO», **no** se lanza otra.
- Si dice «incierto» o «ERROR en la subida», primero se mira YouTube Studio; se anota lo que pasó y recién después se reintenta (el gerente no deja reintentar mientras esté incierto).
- Si dice «subido_privado», faltó la miniatura, los subtítulos o la lista, o YouTube no aceptó la fecha: queda privado y se avisa a Patricio. Se completa lo que falta y se programa en Studio (o con una aprobación nueva).
- Si dice que el canal conectado no es el confirmado, no se sube: revisar la cuenta autorizada.
- Si hay AVISO de miniatura, casi siempre el canal no está verificado por teléfono.

## 4. TikTok e Instagram por Metricool (ruta `metricool`)

1. Revisar que queda cupo: `calendario.py cupo`.
2. **Enlace público del video:** Metricool descarga el archivo desde una dirección https. Hay dos formas:
   - **Google Drive:** se deja el Short en la carpeta de Drive del estudio, compartida como «cualquier persona con el enlace». Claude busca el archivo con el conector de Google Drive y usa su enlace. Si en Metricool está vinculado Google Drive, se lo manda tal cual (Metricool lo importa); si no, se arma el enlace de descarga directa.
   - **YouTube primero (solo Instagram, ruta `vidiq`):** ver la sección 4b.
3. `python enlace.py "<url>" "<archivo aprobado>"` tiene que decir ENLACE OK: entrega un video con el mismo tamaño y el mismo contenido (huella sha256) que lo aprobado. Ese enlace se anota en `enlace_publico` del destino; no cambia la huella de la aprobación. Un enlace de Drive que muestra una página de aviso no sirve: las puertas lo rechazan, y en ese caso la pieza pasa a `manual`.
4. `python anotar.py "<P>" short1 tiktok --reservar` revisa las puertas y deja la reserva `en_curso` (si dice PUERTAS CERRADAS, no se sigue).
5. Programar con el conector de Metricool (`createScheduledPost`), con `blogId` sacado de `getBrandSettings` y **la fecha y zona de `publicacion.json`** (las mismas que revisaron las puertas). Campos:
   - `autoPublish: true`;
   - `providers [{"network":"tiktok"}]`;
   - `tiktokData: {"privacyOption":"PUBLIC_TO_EVERYONE","isAigc":<ia>,"title":"…"}`;
   - para Instagram, `instagramData: {"type":"REEL","isAiGenerated":<ia>,"showReelOnFeed":true}`;
   - `media: [enlace]`.
   Una red por publicación, para poder anotarla por separado.
6. `python anotar.py "<P>" short1 tiktok --estado programado --enlace "<plannerUrl>"`. Si el conector dio error o no respondió, `--estado incierto` y se revisa en Metricool (`getScheduledPosts`) antes de volver a intentar.

## 4b. Instagram desde el Short de YouTube (ruta `vidiq`)

Sirve cuando no hay forma de alojar el archivo. `vidiq_instagram_publish_reel` publica el Reel en el momento, desde el enlace del Short en YouTube, y no gasta créditos.
1. A la hora del calendario (entre 10 minutos antes y 60 después, en una sesión con Patricio o en una tarea programada que él aprobó) se corre `anotar.py "<P>" short1 instagram --reservar`. La puerta exige que el Short ya esté programado o publicado en YouTube con una hora que ya pasó.
2. Se llama a `vidiq_instagram_publish_reel` con el enlace de YouTube, el texto aprobado e `isAiGenerated` según `ia_realista`.
3. Se anota con `python anotar.py "<P>" short1 instagram --estado publicado --enlace <permalink>`.

## 5. A mano (ruta `manual`)

`python calendario.py hoja "<P>"` deja `08_PUBLICAR\hoja_de_publicacion_<v>.md` con el texto listo para copiar en cada red. Cuando Patricio avisa que lo subió: `anotar.py ... --estado publicado --enlace <url>`.

## 6. Después

`calendario.py pendientes` muestra qué falta medir a las 48 h y a los 7 días (ver `metricas.md`). Se actualiza el documento vivo con los enlaces.
