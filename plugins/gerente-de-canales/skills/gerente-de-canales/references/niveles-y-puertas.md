# Niveles de autonomía y puertas

## Niveles (`gerente\config.json` → `nivel`, un número entero)

| Nivel | Qué hace Claude | Qué hace Patricio |
|---|---|---|
| 0 | Solo deja el paquete en `08_PUBLICAR` | Sube todo |
| 1 | Sube a YouTube en **privado**, sin fecha, con todo listo. No programa TikTok ni Instagram: los deja en una hoja manual | Programa o publica en YouTube Studio y en las apps |
| **2 (vigente desde el 08-11-2026)** | Con su aprobación, sube a YouTube en privado con fecha (`publishAt`) y programa TikTok e Instagram (Metricool o vidIQ). Las plataformas publican a la hora | Aprueba cada pieza |
| 3 o cualquier otro valor | No es válido: las puertas se cierran | — |

Para cambiar de nivel hace falta el sí de Patricio; el cambio se anota en el documento vivo.

## Puertas (`puertas.py --pieza <clave> [--red <red>]`)

Basta que una falle para que no salga nada.

1. `publicacion.json` es válido y las rutas de los archivos quedan dentro de la carpeta del proyecto.
2. La pieza existe y tiene destino en la red pedida.
3. El nivel es válido (1 o 2). Para Metricool y vidIQ tiene que ser 2.
4. Existe `terminado_<ID>_<versión>.md` en `07_RENDER*`, con **las filas 1 a 6 presentes y en ✓** (si falta una, se cierra), sin filas raras, y es **más nuevo que el video**.
5. Existe exactamente `08_PUBLICAR/checklist_publicacion_monetizacion_<versión>.md` (de la **misma versión**) con la línea **`MONETIZACIÓN: OK`** y sin «corregir antes de publicar». Esa línea la escribe el distribuidor después de revisar las 7 respuestas de `monetizacion.md` del estudio. El checklist del publicador no se toca.
6. Evaluación en clase A o B **del mismo video**: nombre exacto en `06_RECETA`, campo `video` coincidente y más nueva que el render. Para el largo vale la evaluación de `_youtube` o de `_con-subtitulos` de la misma versión.
7. Aprobación vigente con la **misma huella de la pieza completa**: video, miniatura, subtítulos, título, textos, IA, niños, redes, rutas, fechas y zonas, **más el contexto heredado** (canal confirmado, idioma, categoría y avisos de YouTube de `config.json`). Si cambia cualquiera de esas cosas, hay que aprobar de nuevo. Una aprobación revocada, o anterior a una cancelación de esa pieza, ya no vale.
8. No se envió antes: ni el mismo archivo ni otra versión de la misma pieza a esa red. Cuentan como enviados `en_curso`, `incierto`, `subido_privado`, `programado` y `publicado`; anotar una medición (`medido_48h`, `medido_7d`) no los olvida. Para reemplazar una versión hay que cancelar primero la anterior (en la plataforma y con `anotar.py --estado cancelado` o `yt_api.py desprogramar`) y aprobar la nueva.
9. Fecha futura, con 30 minutos de margen más 1 minuto por cada 60 MB del archivo. Se vuelve a revisar justo antes de subir y otra vez antes de poner la fecha. Las fechas van sin desfase (`2026-11-13T19:00` + zona): se rechazan las horas que no existen o se repiten por el cambio de hora.
10. Metricool: el enlace público entrega **el mismo contenido** que el archivo aprobado (tipo video, mismo tamaño y misma huella sha256 del archivo descargado), y queda cupo en el mes (cuentan `en_curso`, `incierto`, `programado` y `publicado`).
11. vidIQ (Instagram): solo entre 10 minutos antes y 60 minutos después de la hora del calendario, y con el Short ya programado o publicado en YouTube con una hora que ya pasó.

Al subir a YouTube, además:
- se exige que el canal conectado sea el **canal confirmado** (`yt_api.py canal --confirmar`); si es otro, no se sube;
- se usa un candado por archivo: no puede haber dos subidas a la vez;
- se sube una **copia verificada** del archivo aprobado, para que un render que corre justo en ese momento no pueda colarse;
- antes de enviar se anota la fila `en_curso` en el registro (si el registro está bloqueado, se detiene ahí);
- el video se sube **privado y sin fecha**; después se ponen miniatura, subtítulos y lista, y **solo si todo eso salió bien** (y la aprobación sigue vigente y hay margen) se le pone la fecha con `publishAt`. Si algo de eso falla, queda `subido_privado` y se avisa;
- si la subida se corta o da error, queda **`incierto`**: no se reintenta hasta mirar YouTube Studio y anotar lo que pasó (`anotar.py --estado error --nota …` si no quedó nada, o el estado real si quedó). `calendario.py pendientes` lo muestra en «REVISAR EN LA PLATAFORMA»;
- cada paso queda en `gerente\diario\` (un archivo por evento).

Para Metricool y vidIQ (que se llaman desde el chat, no desde un script), primero se reserva: `anotar.py "<P>" <pieza> <red> --reservar` revisa las puertas y deja `en_curso`; recién ahí se llama al conector, y después se anota el estado real con `anotar.py --estado`. Si la llamada falla o no se sabe qué pasó, se anota `incierto`. `anotar.py --estado` guarda la huella del archivo y marca IRREGULAR si no coincide con la aprobación vigente.

## Cómo se pide la aprobación

1. `python aprobar.py "<P>" --tabla [--piezas …]` muestra, por pieza, **todo lo que se va a publicar**: archivo y su huella, título, descripción completa, texto de cada red, etiquetas, miniatura, subtítulos, lista, IA, niños, canal e idioma, cada red con su hora en Santiago y en los mercados del público, y la **huella de 8 letras**. Claude agrega la nota del evaluador.
2. Claude pregunta «¿apruebas?». Solo con un sí explícito corre `aprobar.py "<P>" --por "<nombre>" --huellas largo:<huella8>,short1:<huella8>`, con las huellas que vio Patricio. La huella tiene que ser exactamente de 8 letras (0-9, a-f) y coincidir; si algo cambió entre medio, `aprobar.py` se niega.
3. Si Patricio se arrepiente: `aprobar.py --revocar --piezas … --por …`. Ese comando avisa si algo **ya quedó programado**. Eso no se cancela solo: con su sí, `yt_api.py desprogramar "<P>" <pieza> --confirmado-por "<nombre>"` lo deja privado y sin fecha, y lo de Metricool se cancela allá y se anota con `anotar.py --estado cancelado`.

## Lo que el gerente nunca hace

- Publicar algo sin aprobar.
- Borrar un video publicado o cambiar la privacidad de uno ya público.
- Responder comentarios.
- Gastar dinero o créditos fuera del presupuesto.
- Pedir contraseñas.

`desprogramar` se niega a tocar un video que ya es público o cuya hora de publicación está a menos de 10 minutos (o ya pasó): en ese caso se hace en YouTube Studio. Conserva los demás campos del video, y anota la cancelación en el registro, el diario y el calendario.


## Modo lanzamiento por canal y puerta del juez (gerente 0.2.0; prueba superada el 21-11-2026 en la 0.2.1)
- Se activa por canal en `gerente\config.json` → `"canales": {"<canal>": {"modo_lanzamiento": {"activo": true, "hasta_videos": 10}}}` (cambiarlo necesita el sí de Patricio). No se activa solo; mal escrito queda apagado.
- Con el modo activo: una evaluación bajo 8 (largo) / 7 (Short) o clase C pasa como **AVISO** solo si la aprobación guarda la aceptación explícita de esa misma evaluación (`aprobar.py … --acepto-nota "<motivo>"`); el juicio del juez (`juicio_<v>.md` APROBADO u OBSERVADO, posterior al video) es **obligatorio**; versión mayor que v2 = aviso. Evaluación ausente, ilegible o sin huella sigue bloqueando.
- **En los dos modos:** un juicio RECHAZADO del juez cierra las puertas (antes estaba escrito en las reglas pero ninguna puerta lo revisaba).
- El modo termina solo al llegar a `hasta_videos` videos programados o publicados del canal.
- Detalle completo, registro de la aceptación y pruebas sugeridas: `cambios-0200.md`.
- **Solo a mano en el lanzamiento (M4):** con el modo activo, los destinos `api`, `metricool` y `vidiq` quedan cerrados («modo lanzamiento: subida a mano (hoja de calendario)»). `calendario.py hoja` corre las mismas puertas, no se escribe si alguna está cerrada y lleva el sha256 del archivo aprobado.
- **Formato del juicio:** primera línea solo APROBADO, OBSERVADO o RECHAZADO; después una línea `sha256: <hex>` por cada archivo revisado. Un veredicto que no se reconoce, un sha de otro video o un archivo que no se puede leer cierran la puerta en los dos modos. El gerente busca el juicio en la carpeta de publicación del proyecto y en `08_PUBLICAR`, y toma el más reciente.
