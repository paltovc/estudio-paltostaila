# Transiciones (68, al estilo de CapCut)

`motor/transiciones.py` tiene 68 transiciones propias con nombre en español y su equivalente en CapCut.
**No se copian las de CapCut**: se hicieron de nuevo con ffmpeg (xfade y efectos propios). Por eso se pueden usar en videos monetizados sin la licencia de CapCut.

## Ver todas
`python transiciones.py --catalogo` deja en `%USERPROFILE%\EstudioPaltostaila\recursos\transiciones`:
- `catalogo_transiciones.mp4`: las 68 seguidas, cada una con su número y nombre;
- `catalogo_transiciones.txt`: la lista.

`python transiciones.py --lista` imprime la lista. La persona mira el catálogo y dice cuáles le gustan, por número o por nombre.

## Familias
- **Fundidos:** mezcla, disolver, negro, destello, grises, rapido, lento.
- **Cortinas y deslizamientos** (en 4 direcciones: _izq, _der, _arriba, _abajo): cortina, deslizar, suave, cubrir, revelar.
- **Formas:**
  - circulo_abrir, circulo_cerrar, circulo, rectangulo;
  - abrir/cerrar vertical u horizontal;
  - reloj, pixelar;
  - diagonal_*, esquina_*, persiana_*, viento_*;
  - apretar_horizontal/vertical, distancia, zoom, desenfoque_horizontal.
- **Con movimiento** (efectos propios, las más "CapCut"):
  - empujar (Pull in), alejar (Zoom out), golpe (Zoom punch), giro (Spin);
  - barrido_izq/der (Whip), desenfoque (Blur);
  - sacudida (Shake), glitch, fuga_de_luz (Light leak).

Se acepta el nombre del estudio, el de CapCut en inglés (`spin`, `whip`, `pull in`, `glitch`…) o el de ffmpeg (`fade`, `smoothleft`…). Un nombre desconocido se cambia por `mezcla` y queda un aviso en el log.

## Videos narrados (`armar.py`, en `proyecto.json`)
```json
"transiciones": {
  "normal":   ["mezcla", 12],
  "capitulo": ["empujar", 18],
  "plano":    ["rapido", 6],
  "variar":   ["golpe", "barrido_izq", "mezcla", "desenfoque"],
  "por_escena": {"7": ["giro", 14], "15": ["fuga_de_luz", 12]}
}
```
Las claves:
- **normal:** entre escenas.
- **capitulo:** al abrir un bloque o capítulo.
- **plano:** entre planos de una misma imagen.
- **variar** (opcional): reemplaza a normal. Rota entre esas transiciones, en orden, en las escenas normales, con la duración de normal.
- **por_escena** (opcional): fija la transición al ENTRAR a esa escena. Le gana a todo lo demás.

La duración va en cuadros (12 = 0,4 s a 30 fps). **La sincronía con la voz se mantiene**: la transición se reparte mitad antes y mitad después del cambio, como siempre.

## Videos con tomas sobre música (`montaje_tomas.py`, en `montaje.json`)
- En la raíz:
  - `"transicion": ["mezcla", 8]` aplica una transición en todos los cambios;
  - o `"variar_transiciones": ["golpe", "giro", "barrido_der"]` las rota;
  - `"cuadros_transicion": 8` fija la duración que usan los nombres sueltos y "variar".
- En un tramo:
  - `"transicion": ["glitch", 8]` es la transición al entrar a ese tramo;
  - `"transicion": "corte"` deja ese cambio seco.
- Sin nada de esto: cortes secos en el golpe, como antes.
- El tramo nuevo empieza exactamente en su golpe y la transición se monta desde ahí, así que el ritmo no se corre. La duración total no cambia.

## Cuál usar (guía rápida)
Pocas y con intención: la transición tiene que acompañar lo que pasa, no decorar.
- **Finanzas / explicativo:** mezcla o rapido entre escenas; empujar, suave_* o deslizar_* al abrir capítulo; golpe solo en una cifra o revelación.
- **Bachata / música:** cortes secos en la mayoría de los golpes. golpe, giro o barrido en los acentos fuertes; fuga_de_luz o desenfoque en momentos románticos; sacudida o glitch casi nunca.
- **Shorts:** rápidas (6-10 cuadros): golpe, barrido, empujar.
- **No abusar:** variar con 2-4 transiciones parecidas se ve profesional. Variar con 10 distintas se ve a plantilla. El evaluador baja la nota de ritmo si las transiciones tapan la narración.

Si igual se quiere una transición exclusiva de CapCut (una con efecto 3D o de partículas), se termina en CapCut con los clips por escena del paquete (`capcut.md`).
