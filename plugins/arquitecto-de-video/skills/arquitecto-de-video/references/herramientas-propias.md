# Herramientas propias aprendidas de CapCut y Canva (0.11)

Son diez scripts del motor que hacen lo mismo que funciones de CapCut o Canva, hechos de cero con herramientas gratuitas y de licencia comercial.
- **Se aprende la función; no se copian** plantillas, stickers, efectos ni música de esas apps.
- **Todo corre en el PC.**
- **Nada reemplaza un original:** cada resultado sale con nombre nuevo.

| Script | Equivale a | Para qué |
|---|---|---|
| `texto_imagen.py` | Grab Text + Magic Eraser + traducir (Canva) | traducir o borrar el texto escrito dentro de una imagen |
| `graficos.py` | gráficos animados (Canva) | barras, línea, torta/dona y contador con la marca del canal |
| `audio.py` | Reducir ruido, Realzar voz, ecualizador, Ducking (CapCut) | voz limpia y música que baja sola bajo la voz |
| `efectos.py` | Effects (CapCut) | grano, viñeta, antiguo, VHS, brillo, sueño, congelar, cámara lenta fluida |
| `capas.py` | Chroma key, Overlay/PiP, Split screen, Mask | pantalla verde, persona en una esquina, dos tomas, toma dentro de una forma |
| `presentacion.py` | Magic Design for Video (Canva) | PDF o PowerPoint → curso en video |
| `seguimiento.py` | Tracking (CapCut) | texto, círculo o flecha que sigue a alguien |
| `formatos.py` | Magic Switch/Resize, Magic Animate (Canva) | el video en 1:1, 4:5 y 9:16; portada con capas animadas |
| `mejorar.py` | Upscale / Mejorar calidad | agrandar imágenes con IA (Real-ESRGAN) o clásico |
| `doblaje.py` | subtítulos traducidos + voz (CapCut) | pasar un video de inglés a español |

## 1. Texto dentro de imágenes — `texto_imagen.py`
1. `python texto_imagen.py detectar "<imagen o carpeta>"`. Deja `_textos\<nombre>.json` con cada línea, su caja y `"nuevo": ""`, más una vista con las cajas numeradas.
2. Claude llena `"nuevo"` con la traducción. `""` deja la línea igual y `"-"` solo la borra. Opcionales por línea: `"color"`, `"fuente"` y `"borde": false`.
3. `python texto_imagen.py reemplazar "<imagen o carpeta>" [--canal finanzas]` deja `<nombre>_es.png`. Primero borra el texto rellenando el fondo y después escribe el nuevo:
   - el borrado usa LaMa, o el relleno simple de OpenCV si LaMa no está;
   - el texto nuevo va con la letra del canal, el color de las letras originales y su contorno.

Detalles:
- Modelo LaMa: `python texto_imagen.py instalar-modelo` (unos 200 MB, Apache-2.0).
- Lector de texto: RapidOCR (Apache-2.0).
- Revisar siempre el resultado. En fondos con mucho detalle el relleno puede notarse; ahí conviene rehacer la imagen con el prompt en español.
- Solo para imágenes propias o con derechos. Nunca para quitar marcas de agua o firmas de otros.

## 2. Gráficos animados — `graficos.py`
En `proyecto.json`, `"graficos"` es una lista. Cada gráfico se pega a una escena:
```json
{"escena": 12, "tipo": "barras", "titulo": "Lo que cobra cada AFP", "etiquetas": ["A", "B"], "valores": [0.46, 1.45],
 "sufijo": "%", "decimales": 2, "destacar": 0, "empieza_en": "y la más cara"}
```
Los tipos:
- **barras:** etiquetas, valores y destacar (la barra que va en el color de acento).
- **linea:** x y series, cada una con nombre y valores (sirve para el interés compuesto).
- **torta** (dona por defecto): partes con nombre y valor, más centro.
- **contador:** desde, hasta y texto.

Comunes a todos: `prefijo`, `sufijo`, `decimales` (formato chileno 1.234,5), `color` por serie o parte, y `empieza_en`, que es la frase de la voz donde arranca la animación.

Para generarlos: `python graficos.py "<proyecto>"` crea `04_CLIPS_FLOW\escena_NNN.mp4` y `armar.py` lo inserta como cualquier clip.
- No pisa un clip que ya exista. Con `--rehacer` reemplaza uno hecho por él.
- Suelto, sin proyecto: `python graficos.py --spec g.json --salida g.mp4 --dur 6 [--vertical]`.

Regla: las cifras van con fuente en la investigación. El gráfico se ve como un dato y tiene que ser verdad.

## 3. Audio — `audio.py`
- **Medir:** `python audio.py medir "<archivo>"` da el volumen, el ruido de fondo y qué limpieza conviene.
- **Limpiar:** `python audio.py limpiar in.wav out.wav --nivel suave|media|fuerte [--radio]`. "fuerte" además baja la cola del eco entre palabras. `--radio` le da cuerpo y presencia a la voz.
- **Mezclar con música:** `python audio.py mezclar voz.wav musica.mp3 out.wav --musica -20`. El ducking viene activado: la música baja unos 10 dB cuando hay voz y sube en las pausas.
- **Efectos de voz:** `python audio.py efecto in out --tipo eco|sala|telefono|radio_antigua|grave|aguda`. Son para efectos puntuales, nunca para cambiar de quién es la voz.
- **En un video narrado** (`proyecto.json`, lo aplica `terminar.py`):
  - `"audio_voz": {"limpiar": "media", "radio": true}`;
  - `"musica": {"archivo": "02_MUSICA/tema.mp3", "volumen": -20, "ducking": true}`. Solo música con licencia para monetizar.
  - `tmp/voz.wav` queda siempre solo con la voz.
- **En material grabado** (`grabado.py`): `"limpiar_voz": "suave" | "media" | "fuerte" | "radio"`.

## 4. Efectos de imagen — `efectos.py`
- **Ver todos en una hoja:** `python efectos.py muestra "<imagen o video>"`.
- **Lista:** grano, vineta, blanco_negro, contraste, nitidez, desenfoque, antiguo (sepia + parpadeo + grano), vhs, brillo (resplandor suave) y sueno.
- **Video narrado:** `"efectos_video": ["antiguo"]` en `proyecto.json`. Va debajo de los subtítulos y rótulos. Para el documental retro sirve `["antiguo"]`, o `["vhs"]` en tramos ochenteros.
- **Video sobre música** (`montaje.json`, por tramo):
  - `"efectos": ["brillo"]`;
  - `"congelar": {"en": 1.2, "dura": 0.8}`: cuadro congelado con destello en el golpe;
  - `"fluido": true`: cámara lenta que inventa los cuadros intermedios. Es lenta de calcular, usarla en tramos cortos.
  - En la raíz: `"efectos"` para todos los tramos.
- **Archivo suelto:** `python efectos.py aplicar in.mp4 out.mp4 --efectos vhs,grano [--desde 3 --hasta 8] [--congelar 2.5:0.8] [--fluido 0.5]`.
- **Con medida:** un efecto marca el estilo de todo el video o de un momento. Varios a la vez se ven a filtro de app.

## 5. Capas — `capas.py`
- **Pantalla verde:** `verde fondo persona_verde.mp4 out.mp4 [--escala 0.8 --x der]`. Quita el verde y el reflejo verde de los bordes.
- **Imagen dentro de imagen:** `pip fondo encima out.mp4 --esquina abajo_der --tam 0.3 --forma circulo [--desde 5 --hasta 60] [--audio encima]`. Lleva un borde del color de acento del canal. Es lo típico de un curso: la presentación de fondo y la persona en un círculo.
- **Pantalla dividida:** `dividir a b out.mp4 --modo lado|arriba`. Para 9:16 usar `--modo arriba --ancho 1080 --alto 1920`.
- **Máscara:** `mascara in out.mp4 --forma circulo|corazon|estrella|redondeado [--fondo desenfocado|negro|fondo]`.
- El fondo y la capa de encima pueden ser video o imagen.

## 6. Presentación a curso — `presentacion.py`
`python presentacion.py charla.pdf|charla.pptx "<proyecto>"` hace tres cosas:
- deja las diapositivas en `03_IMAGENES` a 1920×1080, completando con el fondo del canal sin cortar;
- deja el texto de cada una en `06_RECETA\diapositivas.txt`;
- si ya hay transcripción, arma `receta_diapos.csv`: cada diapositiva entra cuando la voz empieza a hablar de lo que dice.

Después se revisa la receta (las filas marcadas "tiempo repartido"), se copia como `receta.csv`, se valida y se arma como siempre.
- Un .pptx se convierte con PowerPoint del PC; si no hay, Guardar como PDF a mano.
- Lector de PDF: pypdfium2 (Apache/BSD).
- Para la persona en la esquina, `capas.py pip` al final.
- Para la charla EAP: una diapositiva por estándar, y capítulos y test por módulo.

## 7. Seguimiento — `seguimiento.py`
1. `python seguimiento.py video.mp4 --cuadro 3.0` saca ese cuadro con una cuadrícula para leer la caja.
2. `python seguimiento.py video.mp4 out.mp4 --desde 3 --hasta 9.5 --caja x,y,ancho,alto --texto "Ava" [--lado arriba]` o `--marca circulo|flecha`.

Revisar `<out>_control.jpg`, que muestra dónde lo vio cada 0,5 s. Si lo pierde (alguien se cruza), queda quieto donde lo vio por última vez y lo avisa. Usa OpenCV (CSRT o KCF, o MIL si no hay otro).

## 8. Formatos y portada animada — `formatos.py`
- `python formatos.py video final.mp4 --formatos 1x1,4x5,9x16 --modo relleno|recorte`:
  - relleno no pierde nada: sirve para textos y gráficos;
  - recorte llena la pantalla;
  - para 9:16 que siga a la persona, `vertical.py` con `"modo": "seguir"`.
- `python formatos.py animar miniatura-lado --campo imagen=foto.png --campo "titulo=AHORRA\nDINERO" --estilo subir|aparecer|golpe [--formato 9x16]` entrega la portada de `diseno.py` con cada capa entrando por separado. Sirve para el primer segundo de un Short o como tarjeta de presentación.

## 9. Mejorar resolución — `mejorar.py`
- `python mejorar.py instalar-modelo` baja Real-ESRGAN x2 y x4 en ONNX (BSD-3, pesos oficiales de xinntao).
- `python mejorar.py imagen "<imagen o carpeta>" --escala 2|4` usa IA si el modelo está; si no, el método clásico. Revisar caras y letras chicas.
- `python mejorar.py video in.mp4 --alto 2160` es solo clásico (escalado fino + limpieza + nitidez), porque con IA un video tomaría horas.

## 10. Doblaje — `doblaje.py`
1. `preparar video.mp4 --idioma en` transcribe localmente y deja `segmentos.json` + `original.srt`.
2. Claude llena `"traduccion"`, con frases que se puedan decir en el mismo tiempo (unos 15 caracteres por segundo).
3. `voz <carpeta> --voz es-CL-LorenzoNeural`:
   - calza cada frase en su segundo; si no cabe, acelera hasta 25 % y avisa en `avisos.txt`;
   - para videos que se publican, las voces van mejor generadas en la página de voz con licencia: `textos_para_voz.txt` tiene las frases; se guardan como `voces\001.mp3…` y se corre `voz --desde-archivos`;
   - edge-tts no da licencia comercial explícita (ver `voces.py`).
4. `mezclar <carpeta> [--original -16|sin] [--quemar]`:
   - deja `<video>_ES.mp4` con el audio original debajo, bajando solo cuando habla la voz nueva (como en un documental), o sin él;
   - con `--quemar`, también una versión con los subtítulos en español.

Solo subtítulos: `subtitulos <carpeta>` → `traduccion.srt`, para subirlo a YouTube como pista.

Nunca se clona la voz de la pareja (ni de nadie) sin un pedido expreso. El video doblado se publica en su canal o con su permiso.

## Dependencias (instalar-estudio)
- `python -m pip install rapidocr_onnxruntime pypdfium2`. onnxruntime y OpenCV ya vienen con rembg.
- Modelos opcionales en `%USERPROFILE%\EstudioPaltostaila\modelos`: LaMa con `texto_imagen.py instalar-modelo` y Real-ESRGAN con `mejorar.py instalar-modelo`.
- Licencias verificadas: RapidOCR Apache-2.0 · LaMa Apache-2.0 · Real-ESRGAN BSD-3 · pypdfium2 Apache-2.0/BSD-3 · OpenCV Apache-2.0.


## Videos terminados fuera del estudio (0.12)

| Script | Para qué |
|---|---|
| `revisar_idioma.py "<video>"` | Lee el video cada segundo (RapidOCR, local) y lista los minutos con texto que parece en inglés dentro de la imagen (`<video>_idioma.txt` + hoja `<video>_idioma.jpg`). Confirmar a ojo: hay falsos positivos. |
| `reemplazar_imagen.py plan.json [--analizar \| --muestras]` | Cambia imágenes dentro de un video ya terminado sin tocar el original: busca el tramo de cada imagen vieja, pone la nueva con el mismo movimiento y vuelve a poner encima los subtítulos quemados y los rótulos de la edición (`"conservar": ["titulo", "numero"]`). En tramos animados (`"letreros"`) cambia solo los carteles siguiendo el movimiento. Renderiza a `*.parcial.mp4`, revisa códigos de ffmpeg y cantidad de cuadros, y recién ahí deja la versión con nombre nuevo + `*.cambios.json`. |

Flujo (FIN-001, 7 nov 2026): `revisar_idioma.py` → imágenes nuevas (con `texto_imagen.py`, o con Codex/ChatGPT si la persona lo aprueba: gasta su plan) en una carpeta aparte → `reemplazar_imagen.py plan.json --analizar` → `--muestras` → render → revisar cuadros de cada tramo antes de entregar. En los cruces entre escenas (~0,3 s) puede verse la imagen vieja.
