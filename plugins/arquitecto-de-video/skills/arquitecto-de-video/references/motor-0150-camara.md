# Motor 0.15 — persona a cámara: luz, énfasis, ángulos, apoyo, sonidos y Shorts

Estado al 15-11-2026: **todo compila (`py_compile`) y nada se ha probado todavía** con tomas reales. La lista de pruebas está al final. Todo lo nuevo se enciende solo con campos nuevos de `proyecto.json`; sin ellos el armado es el de la 0.14.3 (las únicas excepciones son los arreglos de `caras.py`/`vivo.py` de la sección 7, que cambian un poco dónde quedan las tarjetas en 16:9).

Archivos: nuevos `luz.py` y `apoyo.py`; cambiados `grabado.py`, `color.py`, `caras.py`, `vivo.py`, `sonidos.py`, `vertical.py`.

## Ejemplo completo
```json
{
  "video": {"ancho": 1080, "alto": 1920, "fps": 30},
  "grabado": {
    "material": "C:\\tomas", "look": "natural", "punch": 1.08,
    "luz": {"auto": true, "realce_cara": 0.15, "balance": "auto"},
    "enfasis": {"zoom": 1.12, "dura": 0.6, "max_por_min": 6, "palabras": ["gratis", "tres pasos"], "marcas": [{"segundo": 41.2}]},
    "angulos": {"modo": "alternar", "planos": ["general", "medio", "cerrado"], "cambio_cada": [4, 9]}
  },
  "apoyo": [{"en": "abrí la cuenta", "archivo": "00_APOYO/cuenta.png", "dura": 3, "modo": "completo"}],
  "subtitulos": {"estilo": "vivo", "preset": "reel", "palabras_clave": ["gratis"], "sonido": "pop", "sonido_volumen": -14},
  "elementos": [{"tipo": "texto", "texto": "x2", "en": "se duplica", "sonido": "golpe"}],
  "vertical_esquivar_caras": true
}
```
Flujo: `grabado.py transcribir` → `cortar` → (opcional `apoyo.py proponer`) → `armar` → `sonidos.py` (solo si hay sonidos) → `terminar.py` → `vertical.py`.

## 1. Iluminación automática — `luz.py`
Orden fijo del color: **HDR→SDR → luz → LUT/look** (`color.cadena(ruta, look, luz=filtro)`). Después `grabado.py` sigue igualando brillo y saturación con la toma de referencia, como antes.

Campo: `"grabado": {"luz": {"auto": true, "realce_cara": 0.15, "balance": "auto"}}`. Opcionales: `"fuerza"` (1.0; 0.5 = mitad de corrección), `"cuadros"` (5), `"exposicion": false`, `"contraste": false`. `balance`: `"auto"`, `false`/`"no"` o `[r, g, b]` a mano.

| Función | Qué hace |
|---|---|
| `medir(ruta, n, desde, hasta)` | Saca n cuadros chicos ya en SDR y mide: luminancia mediana y percentiles 5/95, grilla 3×3, la cara (con `caras.cara_principal`; su centro, tamaño y luminancia), y el promedio de lo casi gris fuera de la cara (para el balance). Medianas entre cuadros. |
| `proponer(medida, cfg)` | Exposición: mitad lo general y mitad la cara; solo corrige si queda fuera de la banda 0,38–0,55 y hasta el borde de la banda (gamma entre 0,80 y 1,40; no lleva todas las pieles al mismo valor). Contraste: hasta +12 % si la toma está plana. Balance: lo gris vuelve a gris al 70 %, tope ±12 % por canal; si casi no hay gris, no se toca. Realce de cara: viñeta suave centrada en la cara + una subida pareja (la cara gana luz, los bordes bajan). |
| `filtro(correccion)` | El filtro de ffmpeg: `colorchannelmixer` (balance), `eq=gamma:contrast`, `vignette` centrada en la cara. |
| `para_toma(ruta, cfg, desde, hasta)` | Mide + propone → `(filtro, informe)`. Lo llama `grabado.py armar` por cada toma, midiendo solo el tramo usado; deja `tmp/grabado/luz.json`. |

Comandos:
- `python luz.py muestras "<salida>" "toma.mp4@12.5" "foto.jpg" [--look natural] [--realce 0.15] [--balance auto|no] [--alto 720]` → hoja `luz_<look>_NN.jpg` con ORIGINAL · SOLO LOOK · LUZ + LOOK y lo medido.
- `python luz.py medir "<toma.mp4>"` → imprime medida y corrección.
- `python color.py muestras ... --luz` → la hoja de siempre con la luz incluida.

Límites: el realce usa una posición de cara por toma (mediana); si la persona se mueve mucho, bajar `realce_cara` o ponerlo en 0. Sin cara detectada no hay realce (queda avisado). La luz no arregla una toma quemada o muy oscura: avisa «conviene mejorar la luz al grabar».

## 2 y 3. Cámara virtual en `grabado.py armar`: ángulos, punch y énfasis
Se activa si existe `grabado.enfasis` o `grabado.angulos`. Entonces cada tramo se arma en piezas, cada una con su encuadre, centrado en la cara (mediana por toma, `cara_de_toma`). El plan queda en `06_RECETA/camara.md`.

**Prioridad (de mayor a menor):**
1. **Ángulos**: definen el encuadre base. Cambian solo en un corte o en una pausa/fin de frase, nunca en medio de una palabra.
2. **Punch** (el de siempre, `punch: 1.08`): solo en un corte dentro de la misma toma donde el ángulo **no** cambió; multiplica el zoom del plano. Si en ese corte cambió el ángulo, el cambio ya tapa el salto y el punch vuelve a 1.
3. **Énfasis**: zoom suave encima del encuadre vigente. Nunca cruza un corte ni un cambio de ángulo; si no cabe (menos de 0,3 s desde el corte anterior, o menos de `dura` + 0,5 s hasta el siguiente) se omite y queda anotado.

Tope común: `zoom_max` — ningún zoom deja la cabeza (cara × 1,9 de alto) fuera del cuadro; si el plano pedido no cabe, se baja y queda anotado.

### Ángulos
`"angulos": {"modo": "alternar", "planos": ["general", "medio", "cerrado"], "cambio_cada": [4, 9]}`
- `modo`: `alternar` (en ronda, en el orden de la lista), `variar` (al azar con semilla fija, sin repetir el actual ni volver al anterior) o `fijo` (siempre el primero; sirve para dejar todo en plano medio centrado en la cara).
- `cambio_cada`: mínimo y máximo de segundos por plano. En un corte basta el mínimo; en una pausa se espera un valor al azar entre ambos. No cambia en los últimos segundos.
- Opcionales: `"zoom": {"medio": 1.3}` (por defecto general 1.0, medio 1.25, cerrado 1.5), `"cambia_en": "ambos" | "cortes" | "pausas"`, `"pausa": 0.22`.
- Sirve igual en 16:9 y 9:16: el recorte sigue a la cara en horizontal y deja la cara un poco sobre el centro.

### Énfasis
`"enfasis": {"zoom": 1.12, "dura": 0.6, "max_por_min": 6, "palabras": [...]}`
- Disparadores: `palabras` (palabras o frases dichas), `marcas` (`{"segundo": x}` o `{"frase": "..."}`, siempre entran) y, si no hay ni lista ni marcas (o con `"claves": true`), `subtitulos.palabras_clave`.
- `dura` = lo que tarda en acercarse (con ease); se queda `"sostiene"` s (1,2) y vuelve en otro `dura`. Si el corte llega antes, se queda cerca hasta el corte.
- Límites: `max_por_min` (6) y `"separacion"` (4 s entre énfasis).
- Técnica: la pieza se arma al doble de tamaño y `zoompan` hace el zoom (sin perder nitidez).

Funciones nuevas en `grabado.py`: `cara_de_toma`, `zoom_max`, `encuadre`, clase `Camara` (`_angulos`, `_enfasis`, `piezas`, `filtro`, `informe`). `stats()` ahora acepta `luz=""`.

## 4. Material de apoyo — `apoyo.py`
- **Proponer:** `python apoyo.py "<proyecto>" proponer ["<carpeta>"]` → `06_RECETA/apoyo_propuesto.json`. Compara las palabras de la transcripción editada con los nombres de archivo (y `etiquetas.json` en la carpeta: `{"playa.mp4": ["mar", "vacaciones"]}`), sin tildes ni plurales. Cada archivo se propone una vez, donde más etiquetas coinciden; mínimo 8 s entre inserciones (`"apoyo_separacion"`). No cambia el proyecto: se revisa y se copia la lista `apoyo` aprobada. Carpeta por defecto: `"apoyo_material"` o `00_APOYO`.
- **Aplicar:** `grabado.py armar` lo hace solo si hay `"apoyo"`: arma la persona en `tmp/grabado/base_sin_apoyo.mp4` y deja `tmp/solo_video.mp4` con las inserciones (`apoyo.aplicar`, un solo paso de ffmpeg). La voz no se toca. Prueba suelta: `python apoyo.py "<proyecto>" aplicar` → `tmp/solo_video_con-apoyo.mp4`.
- Campos por inserción: `en` (frase exacta, `{"frase", "despues", "desfase"}` o `{"segundo"}`), `archivo`, `dura` (3), `modo`: `completo`, `pip` (recuadro redondeado con borde de acento, en la esquina de arriba opuesta a la cara; `esquina`, `tam`) o `dividido` (16:9: mitad persona, mitad apoyo, `lado`; 9:16: apoyo arriba, persona abajo). Opcionales `desde`, `fundido` (0,15).
- Reutiliza de `capas.py`: `forma_png`, `posicion`, `color_rgb`, `info`, `es_img`.
- Solo material propio o con licencia comercial; anotar en `licencias\registro.md`.

## 5. Sonidos con subtítulos y elementos — `vivo.py` + `sonidos.py`
Apagado por defecto.
- `"subtitulos": {"sonido": "pop", "sonido_volumen": -14}`; opcionales `"sonido_en": "claves"` (por defecto: solo palabras clave y números) o `"grupos"`, `"sonido_cada": 1.5` (s mínimos entre sonidos), `"sonido_max_por_min": 12`.
- En un elemento: `"sonido": "pop"` (suena al entrar; `"sonido_volumen"` opcional).
- Nombres: `pop`, `clic`, `tic`, `suave`, `campana`, `golpe`, `cambio` (archivos del paquete Interfaz del banco CC0, tabla `vivo.SONIDOS`) o el nombre de cualquier archivo del banco o de `05_SONIDOS`.
- `sonido_volumen` = dB bajo la voz: `sonidos.py` mide el máximo del archivo (`pico_db`) y lo deja en `volumen_lufs + sonido_volumen + 9` dB. Es una aproximación: calibrar a oído.
- Hay que correr `sonidos.py` antes de `terminar.py` (como con los demás efectos). Quedan en la hoja de cues con fuente y licencia. `sonidos.py` ya no falla en proyectos sin `receta.csv` (material grabado).
- En los Shorts suenan los mismos (salen de `narracion.m4a`); en modo `grupos` los grupos del 9:16 son más cortos, así que ahí conviene `claves`.

## 6. Shorts: los elementos esquivan caras (opción B) — `vertical.py`
- Encender: `"vertical_esquivar_caras": true` en la raíz de `proyecto.json`, o `"esquivar_caras": true|false` en un corte de `"vertical"`. (No puede ser `"vertical": {...}` porque `vertical` ya es la lista de cortes.) `subtitulos.evitar_caras: false` lo apaga todo; `evitar_texto: false` ignora el texto de la imagen.
- **Proyectos existentes: no cambian** (por defecto apagado; siguen en la columna central). Proyectos nuevos: pendiente que `nuevo_proyecto.py` escriba `"vertical_esquivar_caras": true` (archivo ajeno).
- Cómo: `MapaVertical` lleva las caras/cabezas/texto de `tmp/solo_video.mp4` al cuadro 1080×1920 según el modo (`marco`, `recorte`, `seguir`). Cada elemento busca lugar dentro de la zona segura; si ninguno queda libre, **no se muestra**. Registro: `tmp/capa_viva_lugares_<short>.txt` («oculto» = no había lugar).

## 7. Arreglos pendientes del lote 0.13
- **Guante como cabeza** (`caras.detectar`): una mancha blanca redonda sin rasgos ya no es cabeza si en el cuadro hay otra con ojos claramente más grande (menos del 60 % de su área → pesa como globo). Si ninguna tiene rasgos, solo la mayor cuenta como cabeza.
- **Margen** (`caras.con_margen`, `subtitulos.margen_caras`, 0,08): al medir, caras y cabezas se agrandan 8 % por lado para que la tarjeta no quede pegada. `"margen_caras": 0` = como antes.
- **Caja girada** (`vivo.caja_girada`): la tarjeta-lista se mide con su giro real (`\frz`, −3° por defecto) sobre su esquina.
- **OCR**: si se pidió evitar texto y RapidOCR no está, sale una vez `AVISO caras: ... el lector de texto no está activo`; `caras.sin_ocr()` lo informa a otros scripts.
- Nuevo: `caras.cara_principal(im)`.

## Extra: preset `reel` (`vivo.py`)
`"subtitulos": {"estilo": "vivo", "preset": "reel"}`: Arial Black 96, 2 palabras, entrada pop, palabra clave en amarillo y más grande, posición 0,78 (16:9) / 0,66 (9:16). Todo se puede pisar.

## Pendiente para integrar (archivos ajenos)
- `VERSION` → 0.15.0 y anotar comandos en `etapas.md`, `material-grabado.md`, `capa-viva.md`, `proyecto-json.md`.
- `nuevo_proyecto.py`: `"vertical_esquivar_caras": true` en proyectos nuevos.
- `terminar.py`: si `caras.sin_ocr()`, anotarlo en `capa_viva_lugares.txt`; `terminado.py`: leer también `capa_viva_lugares_<short>.txt`.
- `prueba.py`: casos para `caja_girada`, `con_margen`, guante, `cues_sonido`, plan de `Camara`.
- `instalar.cmd`/instalar-estudio: `luz.py` y la cámara necesitan numpy y OpenCV (ya vienen con rembg).

## Pruebas sugeridas en el PC (ninguna hecha)
1. **Regresión:** proyecto de grabado existente sin campos nuevos → `armar --borrador 30`; comparar con la 0.14.3. Correr `prueba.py` (listas, contador, caras).
2. **Luz:** `luz.py muestras` con una toma oscura, una clara, una con dominante cálida y una HDR; mirar piel y fondo; probar `--realce 0` y `0.3`. Luego `armar --borrador 30` con `luz.auto` y revisar `tmp/grabado/luz.json`.
3. **Ángulos:** borrador de 60 s en 16:9 y en 9:16; ningún plano corta la cabeza; los cambios caen en cortes o pausas; leer `camara.md`.
4. **Énfasis:** 2 palabras + 1 marca; el zoom es suave, sin temblor ni salto de un cuadro al entrar/salir de la pieza; el audio sigue calzando con la boca.
5. **Punch + ángulos + énfasis juntos** y con `jl: 0.15` y dos tomas distintas (duración total = voz).
6. **Apoyo:** `proponer` con una carpeta de 5 archivos; luego `completo`, `pip` y `dividido` (16:9 y 9:16), una imagen y un clip; fundidos y que la voz no cambie.
7. **Sonidos:** `sonido: "pop"` con 3 palabras clave → `sonidos.py` → `terminar.py --borrador`; oír el nivel (¿12-14 dB bajo la voz?) y la sincronía; revisar la hoja de cues. Probar un video largo con muchos pops (largo del comando de ffmpeg).
8. **Shorts:** un corte `marco`, uno `recorte` y uno `seguir` con `esquivar_caras`; elementos fuera de caras, ocultos cuando no hay lugar; revisar el registro.
9. **caras.py:** `python caras.py "<video>" t` en un cuadro con el personaje y su guante; con y sin RapidOCR (aviso).
10. **Preset reel** con `vivo.py --prueba 0-20 --vertical --zona`.
