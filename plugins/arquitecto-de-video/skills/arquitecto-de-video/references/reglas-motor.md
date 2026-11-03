# Reglas para cambiar el motor (scripts de `motor/`)

Para quien corrija o agregue scripts (montajista, director o Claude al mejorar el estudio). Inspiradas en las pautas que circulan como "Karpathy skills" (MIT), escritas para este estudio.

1. **Pensar antes de tocar.** Decir qué se entiende del problema y qué se supone. Si hay dos formas razonables de entender el pedido, preguntar antes de escribir código. Si hay una solución más simple que la pedida, proponerla.
2. **Lo mínimo que resuelve.** Sin opciones, capas ni configuraciones que nadie pidió. Un script nuevo hace una cosa, lee `proyecto.json` o su propio `.json` y deja su salida con los nombres de `nombres.md`.
3. **Cambios quirúrgicos.** Tocar solo lo necesario para el pedido; respetar el estilo de los scripts vecinos. Lo que se vea mal al lado se anota, no se arregla de pasada.
4. **Demostrar que funciona.** Antes de decir "listo": compilar (`python -m py_compile`), correr en un proyecto de prueba o con `prueba.py`, y mirar el resultado (fotograma, hoja, informe). Si se corrigió un error, reproducirlo primero y confirmar que ya no aparece.
5. Al terminar: subir `VERSION`, anotar en `etapas.md` el comando nuevo o el error conocido, y no dejar claves, rutas personales ni datos de la persona dentro de los scripts.
