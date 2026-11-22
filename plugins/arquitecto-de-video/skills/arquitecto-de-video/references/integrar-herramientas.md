# Integrar algo nuevo al estudio (skill, plugin, repositorio, guía, función anunciada)

Para cuando Patricio o su pareja traen algo que vieron («mira, esto hace X») o lo que se juntó en el banco de ideas para revisar el sábado. El objetivo es que lo útil quede **dentro** del estudio, adaptado, y no como una pieza suelta que nadie usa.

## Pasos
1. **Fuente original:** leer el repositorio o la documentación oficial (no un resumen). Quién lo hace, licencia, última actualización, si sigue mantenido.
2. **Qué ejecuta y qué envía:** comandos que corre, instaladores de una línea, claves que pide, si manda audio, video, imágenes o datos fuera del PC, si usa cookies o inicios de sesión de la persona, cuánto cuesta. Si no se puede saber, se dice.
3. **Comparar con el estudio** (`menu-del-estudio.md`): ¿ya está cubierto? ¿lo hace mejor? ¿en qué etapa, línea o agente entraría?
4. **Veredicto** en una tabla: sumar / tomar solo la idea / más adelante / no sumar / descartado (choca con una regla). Con el motivo.
5. **Propuesta de adaptación** (si suma): qué archivo del estudio cambia, qué se escribe nuevo, riesgo, y si necesita instalar algo en el PC (con su licencia).
6. **Esperar el sí.** Recién ahí se programa o se escribe; las pruebas van una vez por lote aprobado.
7. **Créditos y licencias:** lo copiado o adaptado de forma sustancial se anota en `creditos-terceros.md` (aviso de la licencia) y, si se instala algo, en `licencias\registro.md`.
8. **Quitar duplicados:** si una skill suelta queda integrada, recomendar borrarla de la cuenta para que no compita con el estudio por los mismos pedidos.

## Instalar en el PC: lista segura (cuando el veredicto es «sumar» y hay un sí)
Se sigue en este orden y se para en cuanto algo no cuadra.
1. **Diagnóstico solo de lectura:** sistema, Python/Node/Git y sus versiones, espacio libre, **tarjeta gráfica** (NVIDIA, AMD o integrada) y RAM, y si el puerto que usará está libre. No revisar carpetas personales que no hagan falta.
2. **Repositorio exacto:** el que se revisó en el paso 1 de «Pasos» (fuente original), no otro fork aunque el README enlace uno distinto. Si el README manda a clonar otro repositorio, se avisa y se decide cuál.
3. **Plan antes de tocar nada:** qué se descarga (y cuánto pesa), qué comandos se corren, qué se instala fuera de la carpeta, riesgos, licencia del programa **y de cada modelo**, y si cobra o manda datos fuera. Se pide un sí con ese plan a la vista.
4. **Carpeta propia:** `%USERPROFILE%\EstudioPaltostaila\herramientas\<nombre>\` con su propio entorno (venv o `node_modules`), nunca dentro de `motor\` ni de un proyecto. Lo instalado antes del 21-11-2026 (`imagen_local`, `voz_local`, `remotion`, `remotion_skia`, en la raíz de `EstudioPaltostaila`) se queda donde está; no se mueve sin un sí. Sin `sudo`/administrador, sin instaladores de una línea sin leer, sin comandos que borren.
5. **Versiones fijas:** `requisitos_fijados.txt` o `package-lock.json` guardado, y la versión o el commit anotados. Nada que baje «la última» en cada uso.
6. **Solo en este PC:** si levanta un servidor, que escuche en `127.0.0.1`; no se expone a la red de la casa ni a internet.
7. **Claves:** en `claves\<servicio>.env`, nunca en el chat, en el repositorio ni en el almacenamiento del navegador. Si la herramienta solo acepta la clave en el navegador, se anota como riesgo en el veredicto.
8. **Nada de pago sin confirmar:** antes de la primera generación, el precio por uso con fuente; la primera prueba es gratis o con el monto que la persona apruebe.
9. **Probar y dejar instrucciones:** una prueba mínima que mida tiempo y memoria, y en `herramientas\<nombre>\LEEME.md` cómo iniciar, detener, actualizar y desinstalar (desinstalar = carpeta a la Papelera, con un sí).
10. **Registro:** `licencias\registro.md` (programa, modelos, licencias, versión) y, si suma al menú, `menu-del-estudio.md`.
Si aparece un error: explicarlo en simple y proponer el arreglo más chico **antes** de cambiar archivos.

## Lo que se descarta siempre
- Quitar marcas de agua, ocultar el uso de IA o «humanizar» para evadir detección.
- Herramientas que copian cookies o inicios de sesión de la persona.
- Mandar audio o video del estudio a servicios externos cuando hay una opción local.
- Pesos o modelos con licencia no comercial para algo que se va a monetizar.
- Prompts que publican sin aprobación.

## Revisado el 15-11-2026 (banco de ideas del sábado 14)
| Recurso | Veredicto | Qué se hizo |
|---|---|---|
| youtube-agent-skill (11 skills, MIT) | Tomar las ideas | Ganchos en español (`ganchos.md`), retención en tres problemas, un solo arreglo, prueba de las 3 búsquedas, triage de comentarios. Sus scripts no sirven en español. Borrar las 11 skills sueltas de la cuenta. |
| creative-architect (Codex, MIT) | Tomar las ideas | Luz, lente, rasgos de imagen hecha con IA y movimiento (`direccion-de-arte.md`), qué se toma y qué se deja al adaptar (`adaptar.md`), formatos UGC (receta 8). No se instala: trabaja con proveedores de pago (Higgsfield, Magnific). |
| «No es el modelo», guía del canario, Karpathy skills | Tomar las ideas | Canario, dos correcciones → chat nuevo, reglas cortas, diagnóstico (`sistema.md`). Las cuatro reglas de Karpathy ya estaban en `reglas-motor.md`. La «Guía AUDIT» no se pudo abrir (estaba solo en la Bóveda). |
| Remotion (ya instalado en el PC) | Sumar | Queda nombrado en la línea «Animado»; la conexión directa con `graficos.py` queda para un lote con pruebas. |
| HyperFrames, SupoClip, Agent-Reach, VoiceStudio, quitamarcas | No sumar / descartado | Decidido el 15-11 en el documento del Proyecto. |
| DaVinci Resolve + Claude, Recordly | Más adelante | Cuando haya un curso real que lo pida. |
| the-architect, watch | Sin revisar | No se encontraron en el PC; pedir el enlace. |

## Revisado el 21-11-2026
| Recurso | Veredicto | Qué se hizo |
|---|---|---|
| Open Higgsfield AI / Open-Generative-AI (Anil Matcha y copias; guía de @ramonibarra.k) | No sumar; tomar la idea | No se instala: la versión web genera todo en Muapi.ai (pago por crédito) y guarda la clave en el navegador; las copias son confusas. Se tomó su lista de instalación (arriba, «lista segura»). La generación local de imágenes ya existe aparte en `%USERPROFILE%\EstudioPaltostaila\imagen_local\` (Z-Image-Turbo en OpenVINO, 16-11; anterior a la lista segura: su fila de licencias y su LEEME se agregaron el 21-11, y la telemetría de OpenVINO se apagó). |
| higgsfield-ai-prompt-skill (OSideMedia, MIT) | Tomar solo la idea | Prompts por capas y cámara como capa aparte, identidad fija, registro de intentos (`direccion-de-arte.md`). Sus textos son para modelos de pago de Higgsfield: no se instala ni se copia. |
