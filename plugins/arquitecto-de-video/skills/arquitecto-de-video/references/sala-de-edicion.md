# Sala de edición (sala.py)

Una página local para mirar el video como lo verá el público y pedir cambios con palabras normales, en el estilo del reel de referencia (vista en celular, línea de tiempo con marcas de colores, panel de estilos).

## Abrirla (la persona, sin Claude)
- **Doble clic en "Sala de edición"** del escritorio (o `motor\sala.cmd`): se abre una ventana minimizada que es la sala y Chrome con la página. Al cerrar esa ventana la sala se apaga. Si ya estaba abierta, solo abre Chrome.
- Arriba se elige el **proyecto**: aparecen todos los que tienen `proyecto.json` en `EstudioPaltostaila\proyectos` y en las carpetas anotadas en `EstudioPaltostaila\proyectos_externos.txt` (una carpeta por línea; sirve para videos que viven en Documentos, Imágenes o Google Drive).
- Si Claude la abre (porque la persona lo pidió): `python sala.py ["<proyecto>"]` en segundo plano; con `--abrir` abre Chrome. Sin pedido, no se abre el navegador: se da la dirección `http://127.0.0.1:8765/`.

## Dos personas (Patricio y su pareja)
- **Mismo computador:** cada una escribe su nombre en "Tu nombre" (queda recordado en ese navegador). Cada nota lleva su autor y, al guardar, las notas de las dos se juntan: nadie borra las de la otra. El estilo lo guarda quien lo cambió, con respaldo y una línea en `08_SALA/historial.txt` (quién, cuándo, qué).
- **Otro aparato en la misma red de la casa:** doble clic en "Sala de edición (red de la casa)". La ventana muestra un enlace `http://<ip>:8765/?clave=...` para abrir desde el otro notebook o el celular. La clave cambia cada vez y sin ella no entra nadie; Windows puede preguntar una vez si permite el acceso en redes privadas (aceptar solo "privadas"). Usarla solo en la casa, nunca en un wifi público.
- **Cada una en su computador:** instalar el estudio en el de ella (`instalar-estudio`, que también crea los accesos del escritorio) y tener los proyectos en una carpeta compartida de Google Drive anotada en `proyectos_externos.txt` de los dos equipos. Evitar que las dos guarden estilo del mismo proyecto al mismo tiempo (gana el último guardado; queda el respaldo).

## Primera versión automática y después la sala
Claude arma solo la primera versión completa (receta, capa viva con el preset del canal, sonidos, borrador o final) sin detenerse a pedir opinión sobre estilo. Al terminar avisa: "lista la v1 de <ID>; ábranla en la sala cuando quieran". Las dos personas miran, cambian estilos y dejan notas; después dicen "aplica las notas de la sala".

## Qué tiene
- **Qué mirar:** el armado sin subtítulos con la voz (lo mejor para probar estilos), cualquier render de `07_RENDER`, o solo la voz cuando todavía no hay imágenes.
- **Celular 9:16 / YouTube 16:9**, **zona segura** (franjas rojas de la interfaz de TikTok/Reels/Shorts) y **capa viva**: subtítulos y elementos dibujados en el navegador al instante (vista aproximada; si el video ya trae subtítulos quemados, la capa se apaga sola).
- **Línea de tiempo:** escenas, grupos de subtítulo, elementos (en rojo los que no encontraron su frase), rótulos, capítulos, cortes verticales y notas. Clic para ir a ese momento; clic en un elemento muestra su configuración.
- **Panel de estilo:** preset, fuente, tamaño, palabras a la vez, cómo entran, altura, tres colores, destellos, caja, palabras clave.
- **Notas para Claude** con el minuto exacto ("el subtítulo tapa la boca", "aquí un ícono de reloj", "esta imagen no calza").
- **Guardar cambios:** el estilo pasa a `proyecto.json` → `subtitulos` (antes se guarda un respaldo en `08_SALA/proyecto_<fecha>.json`) y las notas a `08_SALA/notas.md` y `notas.json`.
- **Prueba real de este momento:** guarda y renderiza 12 s con el motor (exactamente como saldrá el final) y los carga en la sala.

## Aplicar las notas ("aplica las notas de la sala")
1. Leer `08_SALA/notas.md` y `historial.txt`. Cada nota es un pedido con su minuto y su autor. Si dos notas se contradicen (una pide subir el subtítulo y otra bajarlo), no elegir: mostrar las dos y preguntar.
2. Traducir cada nota a un cambio concreto: estilo o posición de subtítulos, un elemento nuevo o movido en `elementos`, una escena de la receta, un rótulo, un corte de pausa. Si una nota es ambigua, preguntar solo esa.
3. Aplicar, sacar una prueba de ese tramo (`vivo.py --prueba` o `terminar.py --muestras`) y mostrarla.
4. Marcar la nota como hecha en `08_SALA/notas.json` (`"hecho": true`) para que la sala la muestre tachada; la persona recarga la página.
5. El render final sigue las puertas normales (borrador aprobado → finales → control de calidad). Cada render nuevo sube de versión; nunca se pisa uno anterior.

## Copia para el celular
`python celu.py "<proyecto>" [archivo.mp4] [--zona]` → `07_RENDER/celu/<nombre>_celu.mp4` (720p, liviano). Si existe Google Drive para escritorio, también queda en `Mi unidad\EstudioPaltostaila\celu\<ID>` para verla desde el teléfono. `--zona` marca la zona de botones en los verticales (solo para revisar; nunca se publica esa copia).
