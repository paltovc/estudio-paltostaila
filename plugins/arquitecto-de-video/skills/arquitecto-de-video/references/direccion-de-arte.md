# Dirección de arte: luz, lente, cámara, lo que delata a la IA y el movimiento

Para director-de-arte, director-de-movimiento y control-de-calidad. Ideas tomadas de creative-architect y de higgsfield-ai-prompt-skill (ambos MIT, ver `creditos-terceros.md`), adaptadas al estudio. Complementa `prompts.md`; la biblia del canal manda sobre esto (un canal 2D plano no necesita lente, sí luz y composición).

## La luz en tres decisiones
1. **De dónde viene:** frontal (aplana; catálogo), lateral (textura y volumen; la más útil), contraluz (borde brillante; vidrio, humo, drama), cenital (sombra corta; objetos sobre mesa), rasante (relieve).
2. **Qué tan dura:** dura = fuente chica, sombras nítidas, se siente gráfica y moderna. Suave = fuente grande y difusa, sombras graduales, se siente cara y limpia.
3. **De qué color:** cálida (cercana), neutra (honesta, comercial), fría (técnica, distante). Mezclar cálida de un lado y fría del otro da profundidad.

Esquemas con nombre para copiar al prompt: **ventana grande** (suave y lateral, relleno tenue; el que nunca falla), **estudio con contraste** (dura arriba a un lado, sin relleno), **contraluz con borde**, **hora dorada** (cálida, baja, sombras largas), **neón** (dos colores opuestos; solo si la marca lo pide).

## El lente (imágenes realistas o «foto»)
24 mm ambiente · 35 mm lifestyle · 50 mm como el ojo · **85 mm retrato y producto (la opción segura)** · 100 mm macro. Apertura: f/1.8 fondo muy borroso · **f/2.8 punto medio** · f/8 casi todo enfocado. Se escribe así: «Lente de 85 mm a f/2.8. Enfoque nítido en <sujeto>, fondo suave».

## Lo que hace que una imagen «se vea a IA» (revisar antes y después de generar)
1. Todo perfecto, sin desgaste → pedir imperfección concreta (arrugas de uso, polvo, huella).
2. Simetría de más → sujeto al tercio, algo saliéndose del cuadro.
3. **Luz de ninguna parte** (el delator número uno) → escribir el bloque de luz.
4. Todo enfocado → elegir un plano de enfoque.
5. Saturación de más → «colores algo desaturados, contraste medio».
6. Texto que no es texto → las imágenes se piden **sin texto**; el texto lo pone el motor.
7. Manos y dedos → contarlos; si algo está raro, se descarta.
8. La cara de nadie (piel de plástico, ojos vidriosos) → piel real con textura, sin retoque.

Exclusiones base para el bloque «qué evitar»: sin texto, letras, logotipos ajenos, marcas de agua ni firmas; sin manos deformes ni extremidades de más; sin luz plana ni sombras contradictorias; sin colores sobresaturados ni aspecto de render pulido; sin fondo desordenado; sin marcos ni collages.

No sirven: apilar «8k, ultra HD, obra maestra», nombrar a un artista vivo (además del problema con su obra), párrafos larguísimos, sinónimos repetidos.

**Revisión de 20 segundos del prompt:** ¿va en el orden de capas? ¿dice el plano y el ángulo? ¿dice de dónde viene la luz y qué tan dura? ¿dónde está el sujeto en el cuadro? ¿qué está enfocado? ¿está la ficha del personaje? ¿pide «sin texto» y deja aire donde va el rótulo? ¿los colores salen de `marca.json`? ¿hay exclusiones? ¿cada renglón tiene una razón?

**Al recibir:** se descarta (no se entrega «porque casi») si la luz no viene de ningún lado, el personaje o el producto cambió, hay letras inventadas, manos raras o se ve más limpio que la realidad. Decir qué falló y qué renglón del prompt cambia antes de pedir otra.

## La cámara: un bloque fijo en cada prompt
Buena parte del aspecto «de cine» de las herramientas tipo Higgsfield viene de fijar estas decisiones de cámara en cada imagen. Sirven igual en Nano Banana, ChatGPT y Veo.
- **Plano:** general (lugar completo, el personaje chico), conjunto (cuerpo entero), medio (de la cintura arriba; el de casi todo el video), primer plano (cara y hombros; emoción), detalle (un objeto o una mano: billetes, una boleta, el celular).
- **Ángulo y altura:** a la altura de los ojos (neutro; por defecto), picado (desde arriba: el sujeto se ve chico o agobiado), contrapicado (desde abajo: poder, logro), cenital (vista de pájaro: mesa, planos, mapas), holandés (inclinado: algo anda mal; muy de vez en cuando).
- **Lente y foco:** lo de la sección «El lente»; en un canal 2D plano se cambia por «sin perspectiva exagerada» o «leve profundidad».
- **Dónde está el sujeto:** tercio izquierdo o derecho, mirando hacia el espacio libre; ese espacio libre coincide con el del rótulo.
- Variar el plano de una idea a otra (general → medio → detalle) da ritmo sin cambiar el estilo. Dos imágenes seguidas con el mismo plano y ángulo se sienten repetidas.

## El prompt por capas (siempre en el mismo orden)
1. **Herramienta y formato** (Nano Banana Pro, 16:9, 2K).
2. **Cámara** (plano, ángulo, lente o «2D plano», posición del sujeto).
3. **Sujeto:** el personaje con las palabras exactas de su ficha y la ficha adjunta. **Esta capa no cambia nunca entre imágenes**; lo que cambia es la cámara y la acción.
4. **Look:** luz (tres decisiones), paleta de `marca.json`, textura.
5. **Acción y fondo:** qué hace, dónde, un solo gesto.
6. **Qué evitar** y criterio de aceptación.
Las prohibiciones se escriben también en positivo cuando se puede («fondo despejado» además de «sin fondo desordenado»): varios modelos siguen mejor lo que sí deben hacer.

## Registro de intentos
Opcional (las imágenes las genera la persona, así que depende de lo que ella informe). En `03_IMAGENES/registro_intentos.md`, una línea por imagen generada: archivo, herramienta, n.º de intento, aceptada o descartada y por qué (con el renglón del prompt que se cambió). Sirve para ver qué prompts fallan seguido y cuánto cuesta cada imagen que sirve (costo por resultado útil, I-09). Se anota a mano, o lo anota el director de arte al revisar según lo que le cuente quien generó. Ningún script lo crea todavía.

## Movimiento (clips de Flow/Veo)
- La escena ya está en la imagen de partida: el prompt describe **solo el movimiento**, en este orden: **cámara** (acercamiento lento —casi siempre el mejor—, alejamiento que revela, paneo, órbita —vistosa pero deforma—, fija), **sujeto** (un gesto, uno solo) y **ambiente** (vapor, polvo, tela, hojas).
- **Menos es más:** una cosa de la cámara y una del sujeto. Tres cosas moviéndose a la vez se ve generado.
- Duración según para qué: 3-5 s un plano suelto, 5 s el gancho de un reel, 8-10 s solo si la escena cuenta algo.
- Generar directo en la proporción final (9:16 si va a Reels).
- Tres fallos: el personaje o el objeto se deforma (bajar el movimiento y anclar «no cambia de forma ni de ropa»), manos y caras raras (se descarta), movimiento de péndulo que vuelve al inicio (decir hacia dónde y «sin regresar»).
- Tras **dos intentos fallidos** de la misma toma: parar, explicar qué falla y proponer otro enfoque (otra imagen de partida, otro movimiento o sin clip).
