# proyecto.json

Vive en la carpeta del video. Todo campo que falte toma el valor por defecto del motor (`estudio.py`, `DEFAULTS`). Rutas relativas = relativas a la carpeta del video; también se aceptan rutas absolutas y `%USERPROFILE%`.

```json
{
  "nombre": "Video03",
  "canal": "finanzas",
  "version": "",
  "audios": "02_VOZ/*",
  "carpetas": {"imagenes": "03_IMAGENES", "receta": "06_RECETA/receta.csv", "transcripcion": "06_RECETA/transcripcion.json"},
  "video": {"fps": 30, "ancho": 1920, "alto": 1080, "crf": 20, "calidad": "1080p"},
  "volumen_lufs": -14,

  "escenas_capitulo": [10, 24, 37],
  "transiciones": {"normal": ["fade", 12], "capitulo": ["smoothleft", 18], "plano": ["fade", 6]},
  "planos": {
    "1": [[0.0, [1.00, 0.50, 0.50], [1.12, 0.50, 0.46]],
          [4.10, [1.65, 0.27, 0.44], [1.75, 0.25, 0.40]]]
  },
  "alias_clips": {"77": 23},

  "correcciones": [["¿Cuánto pararía en comisiones?", "¿Cuánto pagaría en comisiones?"]],
  "subtitulos": {"max_caracteres": 80, "fuente": "Arial", "tamano": 54},
  "rotulos": [
    {"frase": "La primera creencia", "chico": "CREENCIA 1", "grande": "Invertir es para ricos", "segundos": 5},
    {"frase": "¿Qué tres términos", "chico": "PREGUNTA PARA INVESTIGAR", "grande": "¿Qué tres términos debería aprender primero?", "segundos": 4.5},
    {"frase": "la liquidez", "chico": "DEFINICIÓN", "grande": "Liquidez: qué tan rápido\\Nconviertes algo en dinero", "segundos": 4, "estilo": "definicion"}
  ],
  "capitulos": [
    {"frase": "Imagina a dos personas", "titulo": "Dos personas, dos conclusiones"},
    {"frase": "La primera creencia", "titulo": "Creencia 1: invertir es para ricos"}
  ],

  "sonidos": {
    "activar": true,
    "vol_efectos": -19, "vol_clips": -16, "whoosh_db": -25, "limite_capa": 0.3,
    "whoosh_en_capitulos": true,
    "efectos": [
      {"frase": "cuentas con saldos enormes", "archivo": "handleCoins.ogg", "duracion": 2},
      {"escena": 12, "desfase": 0.2, "archivo": "cloth2.ogg", "ganancia": -2, "duracion": 1.5}
    ],
    "lapiz": [{"escena": 70, "desfase": 0.3}],
    "clips_con_sonido": [1, 3, 28],
    "recorte_clip": {"1": 4.1}
  },

  "vertical": [
    {"nombre": "Short_Creencia1", "desde": "Invertir es para ricos", "hasta": "La segunda creencia",
     "chico": "CREENCIA 1", "titulo": "¿Invertir es solo\\Npara ricos?", "modo": "marco"},
    {"nombre": "Short2_Video02", "desde_s": 312.4, "hasta_s": 371.0, "titulo": "¿Te pasa esto?", "modo": "recorte", "centro_x": 0.35}
  ],
  "miniaturas": [
    {"imagen": "Imagen_010.jpeg", "lineas": ["¿SOLO PARA", "RICOS?"], "lado": "derecha"}
  ],
  "whisperx": {"modelo": "large-v3", "idioma": "es", "compute_type": "int8", "ruta": ""}
}
```

`recorte` lo escribe `recortar_pausas.py` (no editar a mano): indica que la voz ya está recortada y evita recortarla dos veces.

Notas:
- `frase` se busca en la transcripción ya corregida, sin importar mayúsculas ni signos; debe ser texto que se dice de verdad. Si el motor dice "No encontre la frase", copiarla de la transcripción.
- Los momentos se pueden dar como `{"frase": ...}`, `{"escena": n}` (inicio de la escena) o `{"segundo": s}`, con `"desfase"` opcional en segundos.
- Transiciones posibles (xfade de ffmpeg): fade, smoothleft, smoothright, slideleft, wipeleft, circleopen, dissolve, fadeblack, entre otras. La duración va en cuadros (12 = 0,4 s a 30 fps).
- `planos`: el segundo es del video completo (no de la escena). El primer plano empieza siempre con la escena.
- `\\N` en un título es salto de línea.
- `video.calidad`: "720p", "1080p", "1440p" o "4k" (reemplaza ancho y alto; si el video es vertical, los da vuelta).
- `vertical`: `desde`/`hasta` por frase o `desde_s`/`hasta_s` por segundo (los escribe `cortos.py`); `modo` "marco" o "recorte" con `centro_x` de 0 a 1.
- `estilo` de un rótulo: sin estilo = caja azul arriba a la izquierda; `"pregunta"` = arriba al centro (también si el texto chico empieza con PREGUNTA); `"definicion"` = caja clara arriba a la derecha.
- Video vertical como formato principal: `"video": {"ancho": 1080, "alto": 1920}`; subtítulos y rótulos se escalan solos, pero revisar los encuadres de los planos.
