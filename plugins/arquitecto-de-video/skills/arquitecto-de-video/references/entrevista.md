# Entrevista inicial y carpetas

El objetivo es entender qué quiere construir la persona y cómo quiere hacerlo, antes de escribir o generar nada. Preguntar con la herramienta de preguntas con opciones (máximo 4 preguntas por vez, siempre con opción de escribir otra respuesta), en 2 rondas como máximo. Saltar lo que ya se sabe (su mensaje, la biblia del canal, un `00_BRIEF.md` anterior). Si la persona no está o dice "decide tú", tomar los valores por defecto y anotarlos como supuestos en el brief.

## Ronda 1: qué y para dónde
0. **Canal, línea e idioma** (si no está claro en el pedido): para qué canal es, qué línea de producción sigue (narrado, animado, persona a cámara, musical, curso; `lineas-de-produccion.md`) y en qué idioma sale (y si lleva pistas o subtítulos en otros, `idiomas.md`). Si el canal no tiene biblia completa, pasar antes por **nuevo-canal**.
1. **Qué quiere lograr con este video** — enseñar algo, contar una historia, mostrar un producto o servicio, entretener, crecer el canal. (Por defecto: lo que diga la biblia del canal.)
2. **Plataforma principal** — YouTube video largo / YouTube Shorts / TikTok / Instagram Reels / varias. Define el formato: largo horizontal 16:9 o vertical 9:16. (Por defecto: YouTube largo + 3 cortes verticales.)
3. **Duración aproximada** — menos de 1 min / 1-3 min / 5-10 min / más de 10 min.
   Si es YouTube largo, preguntar también la **calidad**: 1080p (recomendada: es la resolución real de las imágenes de ChatGPT) / 1440p (YouTube la procesa con mejor compresión, se ve más nítida en pantallas grandes; render ~2 veces más lento) / 4K (solo si las imágenes y clips son 4K; render muy lento) / 720p (borradores). Va en `proyecto.json` → `"video": {"calidad": "1440p"}`. Y cuántos **cortos verticales** sacar del video largo (por defecto 3, para Shorts, TikTok y Reels).
4. **Qué material ya tiene** (selección múltiple) — guion escrito / audio de voz / imágenes / imágenes del personaje / clips de video / nada todavía.

## Ronda 2: según lo que respondió
- **Si trae guion:** pedirlo (pegado en el chat o la ruta del archivo) y preguntar si se puede ajustar el inicio y el ritmo o si va tal cual.
- **Si no trae guion:** tema concreto; público (edad, país, nivel); tono (cercano, serio, humor, inspirador); la única idea que quien mira debe llevarse; llamado a la acción.
- **Personaje:** "¿Hay un personaje o figura que aparezca siempre?" → si sí, pedir 2-3 imágenes o la carpeta (skill ficha-personaje). Si no hay, ofrecer crear uno o trabajar sin personaje.
- **Voz:** la genera la persona (qué herramienta y voz) / la graba con su voz / necesita propuesta.
- **Imágenes y clips:** las genera la persona con ChatGPT y Flow (el estudio prepara los textos) / ya están hechas.
- **Carpeta:** dónde trabajar (ver abajo).
- **Referentes:** "¿Hay algún video que te guste como modelo?" (enlace) → analista de referentes.

## 00_BRIEF.md (plantilla)
```markdown
# Brief — <nombre del video>
Fecha: <fecha> · Quién pidió: <nombre> · Canal: <canal>

- Objetivo: 
- Plataforma principal y formato: 
- Calidad: 
- Cortos verticales a sacar del largo (cuántos, para qué redes): 
- Otras plataformas (cortes): 
- Duración objetivo: 
- Público: 
- Tono: 
- Idea que debe llevarse quien mira: 
- Llamado a la acción: 
- Guion: trae el suyo (ruta) / escribir desde cero / adaptar
- Voz: 
- Personaje: sí/no — referencias en: 
- Imágenes y clips: quién los genera
- Referentes: 
- Carpeta de trabajo: 
- Supuestos tomados (si no hubo respuesta): 
```

## Carpetas
1. **La persona nombra una carpeta** → trabajar ahí. Listar lo que contiene antes de tocar nada.
   - Si ya tiene subcarpetas con material (por ejemplo `imagenes`, `audios`, `guion`), respetarlas: `nuevo_proyecto.py ... --imagenes "<esa carpeta>" --voz "<esa carpeta>"` hace que `proyecto.json` apunte ahí, sin mover ni renombrar nada.
   - Si la carpeta está vacía o solo tiene sueltos, crear la estructura numerada dentro (`01_GUION` … `08_PUBLICAR`) y pedir permiso antes de mover algo; por defecto se copia.
2. **No nombra carpeta** → proponer `%USERPROFILE%\EstudioPaltostaila\proyectos\<canal>\<VideoNN_tema>` y crearla solo con su sí.
3. **Video que continúa** → buscar `00_ESTADO.md` en la carpeta indicada o en `EstudioPaltostaila\proyectos\`; si hay varios candidatos, preguntar cuál.
4. Nunca borrar ni sobrescribir archivos de la persona. Todo lo generado va con nombre nuevo.

## Estructura que crea nuevo_proyecto.py
```
<VideoNN_tema>\
  00_BRIEF.md · 00_ESTADO.md · proyecto.json
  01_GUION\        guion, investigación, empaque, referentes
  02_VOZ\          audios de voz (parte1, parte2...)
  03_IMAGENES\     imágenes + prompts_imagenes.md
  04_CLIPS_FLOW\   clips descargados + SUBIR_A_FLOW\
  05_SONIDOS\      sonidos propios (opcional)
  06_RECETA\       transcripción y receta de escenas
  07_RENDER\       borradores, finales, revisión
  08_PUBLICAR\     paquete por plataforma
```
