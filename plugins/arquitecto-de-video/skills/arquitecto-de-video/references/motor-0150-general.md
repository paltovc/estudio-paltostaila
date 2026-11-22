# Motor 0.15: idiomas en cualquier dirección, varios canales, historia de canales y pendientes de la semana

Lote 0150, parte general (la parte de cámara está en `motor-0150-camara.md`). Estado: **compila; pendiente de prueba en el PC**. Nada de esto se probó con medios ni contra internet todavía.

## 1. Idiomas: es, en y pt en cualquier dirección

### doblaje.py
| Antes (0.14) | Ahora (0.15) |
|---|---|
| `preparar video.mp4 --idioma en` (solo inglés → español) | `preparar video.mp4 --origen en --destino es` (cualquier par entre es, en y pt; `--idioma` sigue sirviendo como `--origen`) |
| `voz <carpeta> --voz es-CL-LorenzoNeural` | `voz <carpeta>` usa la voz del idioma destino; `--voz` la cambia |
| `<video>_ES.mp4` | `<video>_ES.mp4`, `_EN.mp4` o `_PT.mp4` según el destino |

- Voces por defecto (edge-tts): es `es-CL-LorenzoNeural`, en `en-US-GuyNeural`, pt `pt-BR-AntonioNeural`. Otras sugeridas: `en-AU-WilliamNeural`, `en-AU-NatashaNeural` (Oceanía), `pt-BR-FranciscaNeural`, `es-CL-CatalinaNeural`. **Confirmar los nombres con `python voces.py listar --idioma en` (o pt) antes de la primera prueba**: no se pudieron comprobar sin internet.
- Si la voz no es del idioma destino (ni multilingüe), `voz` se detiene.
- Ritmo: `segmentos.json` trae `"origen"`, `"destino"`, `"cps"` y, por frase, `"max_caracteres"` (duración × caracteres por segundo del destino: es 15, en 14, pt 15; `--cps` lo cambia en `preparar`). Al generar la voz, las frases que pasan ese largo en más de 15 % quedan en `avisos.txt` («acortarla»).
- Licencia: cada corrida con edge-tts deja en `avisos.txt` el aviso de que no trae licencia comercial explícita. Para publicar: voces de la página con licencia (o voz local con licencia, como Kokoro cuando se pruebe) cargadas con `--desde-archivos`. Kokoro **no** está integrado: `voces.py` no tiene `voz_local`; sus audios entran como archivos.
- `mezclar --quemar`: la versión subtitulada ahora sale con `+faststart` (antes no) y las dos salidas sin listas de edición.
- Carpetas de doblaje hechas antes del 0.15 (sin `destino`) siguen siendo inglés → español con los mismos nombres.

Ejemplo (video en español de un canal → versión en inglés para Oceanía):
```
python doblaje.py preparar "FIN-002_v13_youtube.mp4" --origen es --destino en
(Claude llena "traduccion" en inglés respetando "max_caracteres")
python doblaje.py voz "FIN-002_v13_youtube_doblaje" --voz en-AU-WilliamNeural
python doblaje.py mezclar "FIN-002_v13_youtube_doblaje" --original sin --quemar
```

### revisar_idioma.py
`python revisar_idioma.py "<video>" --destino es|en|pt` (por defecto es, como siempre). Avisa el texto dentro de la imagen que no parece del idioma destino:
- **es:** inglés (igual que antes) y, además, portugués con marcas claras (ã, õ, ç, -ção);
- **en:** palabras con tildes, ñ o ç y palabras propias del español o del portugués;
- **pt:** inglés y español (ñ, -ción, palabras propias del español).

Hay falsos positivos: se confirma a ojo, como siempre.

### texto_imagen.py
`detectar` y `reemplazar` aceptan `--destino es|en|pt`. El destino queda en `_textos\<imagen>.json` (`"destino"`) y el sufijo por defecto pasa a `_<destino>` (`_es` si no se dice nada). Al recorrer una carpeta se saltan también las imágenes que terminan en `_en`, `_pt` y `_es_2`.

## 2. Varios canales (lo del motor)
- `proyecto.json` puede llevar `"idioma": "en"` y `"tipo_video": "persona"`. `estudio.Proyecto` expone `pr.canal` y `pr.idioma`.
- `nuevo_proyecto.py`:
  - sin `--codigo`, el código del ID sale de la biblia del canal (`canales\<canal>\canal.md`, línea «Código de los videos: \`FIN\`»); si no lo dice, las tres primeras letras, como antes;
  - `--idioma es|en|pt` escribe `"idioma"` y `whisperx.idioma`;
  - `--tipo-video narrado|animado|persona|musical|curso`;
  - avisa si falta `--canal`.
- `ficha.py`: cada ficha dice `idioma` y `tipo_video`. `python ficha.py tabla --canal <nombre>` muestra solo ese canal.
- Lo que sigue con «finanzas» por defecto y no se tocó: el preset de la capa viva (`vivo.py`, del otro agente) y `diseno.py marca` sin canal (ver «Pendientes»).

## 3. Historia de un canal: canal.py (nuevo)
```
python canal.py "https://www.youtube.com/@canal" [--max 400] [--exactas] [--comparar "https://www.youtube.com/@otro"] [--dest carpeta]
```
- Con yt-dlp, **sin cookies ni sesión**, y sin bajar videos. Lee las pestañas de videos largos y de Shorts (hasta `--max` de cada una, los más recientes).
- Deja en `%USERPROFILE%\EstudioPaltostaila\referentes\canal_<id>\` (o `canal_<id>_2` si ya existe; nunca encima):
  - `datos.json`: cada video con fecha, si la fecha es aproximada, vistas, duración, título, su número en orden de publicación, el múltiplo sobre la mediana del formato y el múltiplo sobre la mediana de sus 10 anteriores;
  - `informe_base.md`: mediana; despegue (primer video ≥3x y ≥10x la mediana) con una tabla de los 10 videos anteriores frente a los 10 siguientes (vistas, duración, frecuencia, largo del título, % con número, pregunta y MAYÚSCULAS, y ejemplos de títulos); videos por mes; tramos de duración; patrones de títulos (largo, números, preguntas, exclamaciones, mayúsculas, emojis, separadores, palabras repetidas e idioma estimado); los 10 con más vistas y los 10 que más superaron a sus anteriores;
  - `vistas.png`: vistas de cada video en el tiempo (escala logarítmica) con la mediana de cada formato y la marca del despegue.
- `--comparar` analiza el segundo canal en su propia carpeta y deja `comparacion.md` en la del primero (p. ej. el mismo nicho en inglés y en español).
- **Límites** (van escritos en el informe):
  - en la lista rápida YouTube no da la fecha exacta: se usa la que yt-dlp estima desde «hace 3 semanas» (`youtubetab:approximate_date`, `fecha_aproximada: true`). `--exactas` pide la real video por video: lento, con una pausa entre pedidos;
  - si una versión de yt-dlp no entrega ninguna fecha, se usa el orden de la lista y el gráfico va «por orden de publicación»;
  - las vistas de los Shorts vienen redondeadas y casi siempre sin duración;
  - solo aparece lo público de hoy, con las vistas acumuladas a hoy.
- Para aprender y entender, no para reutilizar material de otros.

## 4. Brecha de idioma: tendencias.py --idiomas
```
python tendencias.py "finanzas para principiantes" --idiomas en,es,pt --consultas "personal finance for beginners|finanzas para principiantes|finanças para iniciantes" [--shorts] [--n 40] [--dias 30] [--top 5]
```
- Claude entrega la consulta traducida (el script no traduce), en el mismo orden que `--idiomas`.
- Por idioma mide:
  - **oferta:** de una búsqueda por fecha, cuántos salieron en los últimos `--dias`;
  - **demanda:** mediana y percentil 90 de las vistas de los más relevantes;
  - **outliers:** de los `--top` más vistos, cuántos hacen 3x o más la mediana de su canal.
- Marca «POSIBLE BRECHA A → B» (en A hay 2 o más outliers y B tiene un tercio o menos de oferta reciente) y «DEMANDA SIN OFERTA» (B tiene igual o más demanda con la mitad o menos de oferta).
- Deja `tendencias\brecha_<tema>_<fecha>.md` y `.json`, con nombre nuevo si ya existe. Sin `--idiomas`, `tendencias.py` funciona igual que antes.
- Límites: los resultados dependen de la región de la conexión (Chile) aunque se pida el idioma (`youtube:lang=<xx>`), y las fechas son aproximadas. Es una señal para investigar con `canal.py` y `referente.py`.

## 5. Pendientes de la semana (archivos propios)
| Pendiente | Qué se hizo |
|---|---|
| `ritmo.py --salida` no debe pisar | ya iba en una subcarpeta nueva; ahora la carpeta se crea en exclusiva (si aparece otra con el mismo nombre entre medio, usa `_2`) y `--salida` tiene que ser una carpeta, no un archivo |
| Listas de edición en los MP4 | `estudio.SIN_LISTAS = ["-use_editlist", "0"]` en las entregas de `terminar.py` (finales, `--solo-audio` y borrador), `doblaje.py mezclar` (las dos) y `montaje_tomas.py`. ffmpeg corre audio y video juntos hasta cero: la sincronía no cambia. Se oyen los ~21 ms de arranque del AAC (silencio) y el video puede durar unos cuadros más |
| Detectar listas de edición | `estudio.listas_de_edicion(p)` y el punto 15 de `terminado.py` (recomendado: no bloquea) |
| Doblaje subtitulado sin fast start | `+faststart` en `_<DESTINO>_subtitulado.mp4` |
| `montaje_tomas.py` y la canción mono | **Decisión: siempre estéreo a 48 kHz.** Una canción mono se duplica en los dos canales (`aformat=channel_layouts=stereo`, más `-ac 2` en la salida). Así lo piden las plataformas y `formato_plataformas` ya no lo marca. El volumen se mide después, así que sigue a -14 LUFS |
| Origen común de los dos finales | `terminar.py` deja `07_RENDER\<ID>_<v>_origen.json` con la huella de `tmp/solo_video.mp4`, de la narración y de cada final (el sello anterior queda como `_anterior-<fecha>`). Si el armado cambia mientras se hacen los finales, no sella. `--solo-audio` mantiene el armado del sello anterior si los finales todavía calzaban con él; si no había sello que calzara, no escribe sello (corrección B1). `terminado.py` punto 14: **obligatorio** cuando hay sello (un final rehecho por separado ya no calza); **recomendado** sin sello (finales anteriores al 0.15), para no invalidar lo ya firmado. El gerente exige ✓ en cualquier fila que no diga «(recomendado)», así que con sello el punto 14 también cuenta para publicar |

## 6. evaluar.py por tipo de video
`"tipo_video"` en `proyecto.json` (narrado, animado, persona, musical o curso; sin él, narrado) cambia solo los pesos de los ejes. La escala 0-10, los ejes, las clases y la huella del video no cambian. Narrado = los pesos de siempre: los proyectos de finanzas dan la misma nota.

| tipo | gancho | ritmo | voz y audio | capa viva | estructura | empaque | riesgos |
|---|---|---|---|---|---|---|---|
| narrado | 25 | 15 | 10 | 10 | 15 | 15 | 10 |
| animado | 25 | 20 | 10 | 5 | 15 | 15 | 10 |
| persona | 25 | 10 | 20 | 10 | 15 | 10 | 10 |
| musical | 20 | 30 | 15 | 5 | 10 | 15 | 5 |
| curso | 15 | 10 | 20 | 10 | 25 | 10 | 10 |

El json de la evaluación agrega `"tipo_video"`. **Corrección tras el juicio:** el peso de «riesgos» tiene un piso de 10 %, así que `musical` no se usa con 5 % (ver «Correcciones tras el juicio del juez»). Ojo: `evaluar.py` sigue necesitando `proyecto.json` y una transcripción, así que un montaje musical sin voz (`montaje.json`) todavía no se puede evaluar con él.

## Compatibilidad
- Todos los comandos de antes siguen iguales; lo nuevo son opciones.
- Los nombres de salida de siempre no cambian (`_ES`, `_es.png`, `ritmo_<video>`).
- `segmentos.json` y la ficha solo agregan campos.
- Los `terminado_*.md` ya firmados siguen valiendo para el gerente: sus puntos obligatorios no cambiaron.

## Correcciones tras el juicio del juez (16-11-2026)
Estado: **compila; pendiente de prueba en el PC** (las comprobaciones nuevas están en `prueba.py`, sin correr).
- **B1 · `terminar.py --solo-audio` sobre finales sin sello:** si no hay un sello previo que calce con los finales (finales anteriores al 0.15), ya no escribe un `_origen.json` «sin origen»: avisa y el punto 14 de `terminado.py` sigue como recomendado. Si queda un sello sin origen escrito antes de esta corrección (`"solo_video": null`), `terminado.py` lo trata igual que «sin sello» (recomendado, no bloquea). Con un sello que calza, todo sigue igual (obligatorio).
- **M3 · `tipo_video` y la nota:** `evaluar.py` tiene un piso para el eje «riesgos de monetización»: su peso nunca queda bajo el de siempre (10 %, el de narrado). Si un tipo lo trae más bajo (hoy solo `musical`, 5 %), se sube a 10 % y los demás ejes se reparten el 90 % en la misma proporción (`pesos_de_tipo`). Con `tipo_video` en `proyecto.json`, la evaluación deja escritos el tipo y los pesos usados: el `.json` agrega `tipo_video_declarado`, `piso_riesgos` y `piso_riesgos_aplicado` (además de `tipo_video` y `pesos`, que ya estaban), y el `.md` una línea «Pesos usados (tipo_video …)». Sin `tipo_video`, nada cambia. El gerente muestra el tipo y los pesos en la fila de la evaluación (`puertas.py`) y en `aprobar.py --tabla`.

Tabla de pesos que se usa de verdad desde esta corrección (musical cambia; los demás quedan igual):

| tipo | gancho | ritmo | voz y audio | capa viva | estructura | empaque | riesgos |
|---|---|---|---|---|---|---|---|
| musical | 18,9 | 28,4 | 14,2 | 4,7 | 9,5 | 14,2 | 10 |

## Pendientes para integrar (archivos del otro agente)
- `vertical.py`: ya tiene `SIN_LISTAS` en la salida de los Shorts (`*_9x16.mp4`, `vertical.py:205`); no queda pendiente.
- `grabado.py`: `SIN_LISTAS` en sus entregas.
- `vivo.py`: el preset por defecto de la capa viva es «finanzas»; para varios canales convendría leerlo de la marca del canal.
- `diseno.py marca` sin canal muestra «finanzas». Es mío, pero no se tocó: no estaba en el pedido y cambiarlo podía romper el uso de siempre.

## Pruebas sugeridas en el PC (después, una por una)
1. `python -m py_compile` de todo el motor y `python prueba.py`: trae las comprobaciones nuevas de `revisar_idioma`. Revisar en la salida de `terminado.py` los puntos 14 (✓ con sello) y 15.
2. `ffprobe` o `python -c "import estudio; print(estudio.listas_de_edicion(r'<final>.mp4'))"` sobre un final nuevo: tiene que dar `[]`. Sobre uno del 0.14, alguna pista con listas.
3. Mirar un final nuevo en el celular y en CapCut: sincronía de labios (en un video con persona) y primer cuadro.
4. `terminar.py --rehacer` en una copia de FIN-002: aparece `_origen.json` y `terminado.py` da el 14 en ✓. Rehacer a mano solo uno de los finales (copiarlo encima en la copia): el 14 tiene que salir ✗.
5. `doblaje.py preparar <video en español> --origen es --destino en` → revisar `max_caracteres`. `voz` sin `--voz` (en-US-GuyNeural) → `avisos.txt` con el aviso de licencia. `voz --voz es-CL-LorenzoNeural` sobre esa carpeta tiene que detenerse. `mezclar --quemar` → `_EN.mp4` y `_EN_subtitulado.mp4`, las dos con fast start (`python estudio.py formato <carpeta>`).
6. `python voces.py listar --idioma en` y `--idioma pt` para confirmar los nombres de VOCES.
7. `montaje_tomas.py` con una canción mono: el final sale estéreo y a -14 LUFS (`python estudio.py formato`).
8. `revisar_idioma.py <video> --destino en` sobre un video en inglés con algún cartel en español.
9. `canal.py` con un canal chico (pocos videos) y luego `--comparar` con uno del mismo nicho en otro idioma. Mirar si llegan las fechas aproximadas y probar `--exactas` con `--max 30`.
10. `tendencias.py "<tema>" --idiomas en,es --consultas "…|…" --n 20 --top 3`. Confirmar que la búsqueda trae fechas (si no, la oferta sale «?»).
11. `evaluar.py` en un proyecto con `"tipo_video": "persona"`: el md muestra los pesos de persona. Sin `tipo_video`, la misma nota que antes.
12. `nuevo_proyecto.py <carpeta de prueba> --canal finanzas --numero 99 --idioma en`: ID `FIN-099` y `whisperx.idioma = en`.
13. (Correcciones tras el juicio) `prueba.py` trae dos comprobaciones nuevas: `terminar.py --solo-audio` sin sello previo no deja `_origen.json` y el 14 sale «(recomendado)»; y los pesos de `evaluar.py` nunca dejan «riesgos» bajo 10 %. A mano: en una copia de FIN-002 (sin sello), `terminar.py --solo-audio` y luego `terminado.py`: tiene que firmar. Y `evaluar.py` en un proyecto con `"tipo_video": "musical"`: el md trae la línea «Pesos usados … (aplicado: el tipo lo traía en 5 %)».
