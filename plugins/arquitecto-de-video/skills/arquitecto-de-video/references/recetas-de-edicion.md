# Recetas de edición por formato

Una receta es el punto de partida del estilo de un video: ritmo de cortes, encuadres, subtítulos, elementos, sonido y duración. La biblia del canal elige una o dos recetas y anota sus ajustes; el `editor-de-escenas` (o el montajista en material grabado) parte de ahí, y la sala de edición la afina. Lo marcado **(0.15)** es nuevo en el motor 0.15 y está pendiente de prueba en el PC.

Regla común: una o dos entradas de texto y 3-4 transiciones fijas por canal, siempre las mismas, para que el canal tenga identidad. Animar las palabras clave, no todo.

## 1. Reel de persona hablando (TikTok, Reels, Shorts)
- **Duración:** 25-60 s. **Formato:** 9:16, zona segura.
- **Ritmo:** algo cambia cada 1,5-3 s: corte, ángulo virtual **(0.15)**, zoom de énfasis **(0.15)**, texto o apoyo.
- **Cortes:** sin muletillas ni silencios (`grabado.py cortar`, `pausa_max` 0,30-0,35 s); punch en cortes del mismo plano.
- **Luz y color:** `grabado.luz.auto` + realce de cara suave **(0.15)**; look `natural` o `calido`.
- **Subtítulos:** preset `rosa` o `reel` **(0.15)**: 1-2 palabras, grandes, centro-bajo, palabra clave en color de acento; sonido «pop» suave solo en palabras clave **(0.15)**.
- **Elementos:** número gigante en cifras, ícono en la idea clave; material de apoyo cuando nombra algo **(0.15)**.
- **Gancho:** primera frase con fórmula de `ganchos.md` y texto en pantalla distinto de lo que se dice en los primeros 2 s.
- **Cierre:** termina en una frase que conecta con la primera (loop) o en un pedido único.

## 2. Clip de podcast o conversación
- **Duración:** 30-90 s del mejor momento. **Formato:** 9:16 o 1:1.
- **Encuadre:** pantalla dividida (`capas.py dividir --modo arriba`) o ángulo que sigue a quien habla.
- **Subtítulos:** 2-3 palabras, con color por persona si son dos.
- **Ritmo:** se respetan las pausas naturales de la conversación; solo se cortan silencios largos.
- **Elementos:** casi ninguno; a lo más el nombre del invitado con `seguimiento.py`.

## 3. Tutorial o «cómo se hace»
- **Duración:** 3-10 min (largo) o 45-60 s (corto). **Formato:** 16:9 o 9:16.
- **Estructura:** resultado al inicio, luego pasos con `progreso` («PASO 2 DE 5») en la capa viva.
- **Encuadre:** persona en círculo (`capas.py pip`) sobre la pantalla o el objeto; acercamientos a lo que se hace.
- **Subtítulos:** preset `curso` (caja, sobrio).
- **Texto:** «Paso N» siempre en edición, nunca dentro de la imagen generada.

## 4. Storytime o historia personal
- **Duración:** 45-90 s (corto) o 6-12 min (largo).
- **Gancho:** historia empezada a la mitad (fórmula 4 de adaptar.md o 8/9 de ganchos.md).
- **Ritmo:** más lento que el reel; ángulos virtuales en cambios de emoción **(0.15)**; zoom de énfasis en la frase clave.
- **Sonido:** efectos mínimos, nada de pops; transición suave.

## 5. Explicador narrado (finanzas, curiosidades)
- **Duración:** 6-12 min. **Formato:** 16:9 + 3 Shorts.
- **Ritmo:** algo cambia cada 3-5 s (imagen, plano dentro de la imagen, rótulo o tarjeta).
- **Subtítulos:** preset del canal (por ejemplo `finanzas`), palabras clave y cifras resaltadas.
- **Elementos:** gráficos cuando hay cifras con fuente, tarjetas escritas a mano, `progreso` en listas.
- **Personaje:** siempre el de la ficha maestra.

## 6. Documental retro o histórico
- **Duración:** 8-15 min.
- **Imagen:** archivo real de dominio público con licencia anotada; la IA solo para mapas, ilustraciones claramente dibujadas o recreaciones marcadas como tales. Imágenes realistas hechas con IA de hechos reales llevan **etiqueta de contenido alterado o sintético** (`monetizacion.md`).
- **Efectos:** `antiguo` o `vhs` según la época, con medida.
- **Subtítulos:** preset `documental` (serif, 4 palabras, fundido).
- **Ritmo:** más pausado; acercamientos lentos tipo Ken Burns; capítulos claros.

## 7. Video musical
- **Formato:** 9:16 o 16:9 según el canal. **Ritmo:** cada tramo termina en un golpe (`montaje_tomas.py`).
- **Imagen:** tomas propias; rampas de velocidad en golpes fuertes; congelar con destello en el coro.
- **Texto:** letra con la capa viva (preset `bachata` u otro propio), solo en los tramos que lo pidan.
- **Derechos:** la canción es del canal o tiene licencia; si fue hecha con IA y es el foco, etiqueta obligatoria.

## 8. Producto o servicio con voz en off (UGC sin rostro)
- Tomado de los formatos UGC de creative-architect (MIT, ver `creditos-terceros.md`).
- 4-6 tomas del producto en uso, con manos, cámara tipo teléfono; voz en off; texto en pantalla con el beneficio.
- Variantes: **review** (alguien hablando a cámara del producto: va por la receta 1), **unboxing** (la revelación es la toma más cuidada), **tutorial** (receta 3).

## Cómo se anota en la biblia
```markdown
## Receta de edición
- Principal: 1 Reel de persona hablando · Secundaria: 3 Tutorial
- Ajustes: subtítulos preset reel con acento #FFD23F · ángulos cada 3-6 s · sin pops · transiciones: golpe, barrido, fundido
```
