# Plano de 6 capas (ingeniería inversa de un video, sin copiarlo)

Copiar la superficie de un video viral (sus palabras, gestos y efectos) no funciona y además es contenido reutilizado. Lo que se transfiere es la estructura. El plano la saca en seis capas, cada una con su evidencia (minuto, dato o cuadro), y termina con un esqueleto vacío que el guionista llena con un tema propio.

Fuentes de datos: `informe_base.md`, `transcripcion.txt`, `comentarios.json`, `ritmo\ritmo.md` + `ritmo.png` + `hoja_cortes_NN.jpg` (de `referente.py`, o `python ritmo.py "<video entregado>"` si la persona trajo el archivo).

## Plantilla de `plano.md`

```markdown
# Plano de <título> (<enlace>)
Números: <vistas> vistas, x<veces> su canal, <likes/1000> likes por 1.000 vistas.

## 1. Gancho (0–3 s y 3–15 s)
- Interrupción de patrón: <qué rompe lo esperado, con minuto>
- Brecha de curiosidad: <qué pregunta deja abierta>
- Señal de identidad: <a quién le habla: "si tienes 25 y no ahorras…">
- Primeros 3 s: <cortes medidos>, <texto en pantalla>, <qué se dice>

## 2. Arquitectura del guion
| parte | desde | hasta | % del video | qué pasa |
| planteamiento | 0:00 | | | |
| tensión | | | | |
| resolución / pago | | | | |
Ganchos internos: <"lo tercero es lo más importante", con minuto>

## 3. Curva emocional
Tensión de 1 a 10 cada 10–15 s (lista minuto: valor). ¿Sube y baja (bien) o es plana o una sola subida?

## 4. Ritmo visual (medido)
Cortes por minuto <n>, cambios suaves por minuto <n>, plano promedio <s>, tramos quietos de más de 6 s <lista>.
Texto en pantalla (de las hojas de cortes): cuántas palabras, dónde, cómo entra. Tipos de transición.

## 5. Público
Vocabulario (nivel), referencias, qué dolor concreto nombra, marcas visuales de identidad, formato nativo de la plataforma.

## 6. Disparadores de distribución
Qué invita a compartir, guardar o comentar (al menos dos). Qué piden o discuten los comentarios más votados.

## Lo transferible y lo que no
Transferible: <estructura, tipo de gancho, ritmo, empaque>. No transferible: <fama, tema de moda, presupuesto, rostro>.
Riesgos para nuestro canal: <promesas de ganancia, urgencia artificial, clips ajenos…>

## Esqueleto para nuestro video (vacío, sin frases del original)
| bloque | duración objetivo | función | elementos de la capa viva | ritmo objetivo |
| gancho | 0–3 s | | | 1 cambio cada <s> s |
| … | | | | |
```

Reglas:
- Ninguna frase, imagen, música ni clip del referente pasa al esqueleto. El guionista escribe desde cero con la estructura.
- El ritmo objetivo sale de los números medidos, ajustado al canal (finanzas: claridad antes que velocidad).
- Comparar después con nuestro render: `python ritmo.py "<referente.mp4>" --comparar "<nuestro.mp4>"`.
