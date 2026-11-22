# Líneas de producción

El estudio no es de un solo tipo de video. Cada canal dice en su biblia qué líneas usa (puede combinar varias), y cada video dice en `00_BRIEF.md` cuál sigue. El director elige el camino de etapas según la línea; las reglas que no se negocian, las puertas de créditos, escuchar y publicar, y el juez valen para todas.

| Línea | Cuándo | Material de entrada | Etapas que cambian | Herramientas clave |
|---|---|---|---|---|
| **1. Narrado con imágenes** | Explicadores, finanzas, curiosidades, historia | Guion → voz (página de voz, Kokoro o voz propia) + imágenes generadas | La de siempre (0-11 de `SKILL.md`) | `frases.py`, `armar.py`, capa viva, `graficos.py` |
| **2. Animado** | Personaje que se mueve, escenas de acción, cuentos | Igual que la 1, con más clips | La etapa 7 (movimiento) pasa a ser central: se planifican clips por escena, no solo el gancho | Flow/Veo (con el sí de la persona por los créditos), `graficos.py`, Remotion en `EstudioPaltostaila\remotion` para gráficos animados más complejos, capa viva |
| **3. Persona a cámara** | Reels, cursos, testimonios, vlogs, tutoriales, podcast | Tomas grabadas (celular o cámara) | Sin imágenes, Flow ni voz: transcribir tomas → elegir tomas (puerta: la persona aprueba la lista) → cortar → luz y color → armar con ángulos, énfasis y material de apoyo → terminar | `grabado.py`, `luz.py`, `apoyo.py`, `color.py`, `capas.py`, `seguimiento.py` (`material-grabado.md`, `motor-0150-camara.md`) |
| **4. Musical y montaje** | Videos musicales, viajes, baile, recuerdos | Canción + tomas y fotos | Sin guion ni voz: inventario → canción y ritmo → color → montaje al golpe | `inventario_tomas.py`, `montaje_tomas.py`, `efectos.py`, transiciones sobre música |
| **5. Presentación o curso** | Clases, charlas, inducciones | PDF o PowerPoint + voz o grabación | Las diapositivas reemplazan a las imágenes | `presentacion.py`, `capas.py pip` (persona en la esquina) |

## Combinaciones frecuentes
- **Persona a cámara + material de apoyo + gráficos:** un reel de tu pareja explicando algo, con imágenes generadas o tomas de apoyo cuando nombra algo y un gráfico cuando da una cifra.
- **Narrado + persona a cámara al inicio y al cierre:** el gancho y el cierre con la cara, el cuerpo narrado.
- **Musical + letra en pantalla:** montaje al ritmo con la capa viva en modo letra (preset `bachata` o uno propio).
- **Video de otro idioma adaptado:** cualquier línea, con `idiomas.md` (pistas o canal aparte) y `adaptar.md` si el original es de otro canal.

## Qué decide la línea
- Qué agentes trabajan (en la 3 y la 4 no hay director de arte ni de movimiento salvo para el material de apoyo).
- Qué receta de edición se usa por defecto (`recetas-de-edicion.md`).
- Qué mide el evaluador (con el motor 0.15, `evaluar.py` lee el tipo de video si está en `proyecto.json`).
- Qué entra en el paquete de publicación (en la 3 y la 4 casi siempre el vertical es el formato principal).

## Lo que el estudio no hace
- No anima personajes cuadro a cuadro ni hace 3D completo: para eso se usan clips de Flow/Veo (la persona genera) o una herramienta aparte. El estudio arma, sincroniza y termina.
- No clona voces sin un pedido expreso de la persona dueña de la voz.
