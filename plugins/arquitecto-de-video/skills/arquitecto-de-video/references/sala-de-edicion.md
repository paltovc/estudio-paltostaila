# Sala de edición (sala.py)

Una página local para mirar el video como lo verá el público y pedir cambios con palabras normales, en el estilo del reel de referencia (vista en celular, línea de tiempo con marcas de colores, panel de estilos).

## Abrirla
1. Lanzar en segundo plano (queda corriendo): `python sala.py "<proyecto>"` con log, por ejemplo con `Start-Process`. Escucha solo en el propio computador: `http://127.0.0.1:8765/` (`--puerto` para otro).
2. Decirle a la persona que la abra en Chrome cuando quiera. Abrir Chrome por ella solo si lo pide (`--abrir`), porque no se abren ventanas sin avisar.
3. Al terminar, cerrar el proceso.

## Qué tiene
- **Qué mirar:** el armado sin subtítulos con la voz (lo mejor para probar estilos), cualquier render de `07_RENDER`, o solo la voz cuando todavía no hay imágenes.
- **Celular 9:16 / YouTube 16:9**, **zona segura** (franjas rojas de la interfaz de TikTok/Reels/Shorts) y **capa viva**: subtítulos y elementos dibujados en el navegador al instante (vista aproximada; si el video ya trae subtítulos quemados, la capa se apaga sola).
- **Línea de tiempo:** escenas, grupos de subtítulo, elementos (en rojo los que no encontraron su frase), rótulos, capítulos, cortes verticales y notas. Clic para ir a ese momento; clic en un elemento muestra su configuración.
- **Panel de estilo:** preset, fuente, tamaño, palabras a la vez, cómo entran, altura, tres colores, destellos, caja, palabras clave.
- **Notas para Claude** con el minuto exacto ("el subtítulo tapa la boca", "aquí un ícono de reloj", "esta imagen no calza").
- **Guardar cambios:** el estilo pasa a `proyecto.json` → `subtitulos` (antes se guarda un respaldo en `08_SALA/proyecto_<fecha>.json`) y las notas a `08_SALA/notas.md` y `notas.json`.
- **Prueba real de este momento:** guarda y renderiza 12 s con el motor (exactamente como saldrá el final) y los carga en la sala.

## Aplicar las notas ("aplica las notas de la sala")
1. Leer `08_SALA/notas.md`. Cada nota es un pedido con su minuto.
2. Traducir cada nota a un cambio concreto: estilo o posición de subtítulos, un elemento nuevo o movido en `elementos`, una escena de la receta, un rótulo, un corte de pausa. Si una nota es ambigua, preguntar solo esa.
3. Aplicar, sacar una prueba de ese tramo (`vivo.py --prueba` o `terminar.py --muestras`) y mostrarla.
4. Marcar la nota como hecha en `08_SALA/notas.json` (`"hecho": true`) para que la sala la muestre tachada; la persona recarga la página.
5. El render final sigue las puertas normales (borrador aprobado → finales → control de calidad). Cada render nuevo sube de versión; nunca se pisa uno anterior.

## Copia para el celular
`python celu.py "<proyecto>" [archivo.mp4] [--zona]` → `07_RENDER/celu/<nombre>_celu.mp4` (720p, liviano). Si existe Google Drive para escritorio, también queda en `Mi unidad\EstudioPaltostaila\celu\<ID>` para verla desde el teléfono. `--zona` marca la zona de botones en los verticales (solo para revisar; nunca se publica esa copia).
