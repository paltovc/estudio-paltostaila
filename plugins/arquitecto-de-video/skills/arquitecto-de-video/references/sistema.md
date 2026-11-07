# El sistema que deja al estudio igual cada vez

Basado en "No es el modelo" (tododeia). Cada chat parte en blanco: lo que hace que el estudio trabaje igual de bien cada vez es lo que queda escrito y lo que se comprueba solo.

| capa | dónde vive en el estudio |
|---|---|
| Reglas escritas | instrucciones del Proyecto "Estudio Palto Style" + este plugin (SKILL.md y references) |
| Lo que no puede depender de la memoria | el motor: nunca sobrescribe versiones; `caras.py` evita tapar caras; `revisar.py` |
| Verificación | `terminado.py`: lista de sí o no, se entrega tal cual antes de decir "listo"; además `evaluar.py` |
| Examen | `examen` en el documento del Proyecto: 5 tareas fijas para comparar al cambiar de modelo |

## Correcciones que se convierten en reglas
Cuando la persona corrige lo mismo dos veces:
1. escribir en una línea qué se hizo y qué quería;
2. proponer una regla corta que lo evite;
3. compararla con las instrucciones del Proyecto: nueva, repetida o contradictoria;
4. no agregar nada sin su sí.

## Si algo sale mal
1. ¿Hay un incidente abierto? Revisar status.claude.com.
2. ¿Cambió el modelo o el esfuerzo?
3. ¿El chat ya era muy largo? Abrir uno nuevo dentro del Proyecto: el documento vivo guarda el estado.
4. ¿Se dieron las reglas esta vez?
5. ¿Había cómo saber que terminó bien? Correr `terminado.py`.
