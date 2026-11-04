# Lo aprendido de CapCut (y cómo convive con el estudio)

Patricio tiene CapCut Pro instalado en su PC. Regla: **aprender de CapCut sí; automatizarlo o copiarlo, no.** Sus términos de servicio prohíben hacer ingeniería inversa, descompilar o crear obras derivadas del servicio (sección 5, punto 02) y "usar scripts automatizados u otras tecnologías para recopilar información o interactuar con los Servicios" (sección 5, punto 09). Por eso el estudio no edita los proyectos de CapCut por dentro: le entrega un paquete para terminar a mano.

## Funciones de CapCut y su equivalente en el estudio
| CapCut | En el estudio | Estado |
|---|---|---|
| Auto Captions + estilos de subtítulos | capa viva (`vivo.py`) con presets por canal | listo |
| Remove Filler Words, Auto-cut de silencios | `grabado.py` (muletillas, trabas, pausas, tomas repetidas) y `recortar_pausas.py` | listo |
| Auto Beat (cortes al ritmo) | `montaje_tomas.py` con los pulsos de la canción | listo |
| Scene Detection | `ritmo.py` (cortes secos y fundidos) | listo |
| Auto Reframe | `vertical.py` modo `"seguir"`: el recorte 9:16 sigue la cara (OpenCV) o lo que se mueve | nuevo 0.9 |
| Speed curves (rampas de velocidad) | `montaje_tomas.py`: `"rampa": [1.0, 0.35]` en un tramo | nuevo 0.9 |
| Stabilize | `montaje_tomas.py`: `"estabilizar": true` (filtro deshake de ffmpeg) | nuevo 0.9 |
| Color grading con LUT | `color.py`: look `"lut:C:\\ruta\\archivo.cube"` | nuevo 0.9 |
| Auto Cutout / quitar fondo | imágenes: `diseno.py` con rembg; video: no (pesado sin GPU) | imágenes listo |
| Text to Speech | `voces.py` (edge-tts, voz Lorenzo) | listo |
| Script to Video | todo el flujo del arquitecto | listo |
| Long video to Shorts | `vertical.py` + el evaluador propone los mejores momentos | listo |
| Plantillas, efectos y animaciones de texto | `diseno.py` (11 efectos) y `vivo.py` (20+ entradas) | listo |
| Voice cloning | no se hace sin pedido expreso | regla |

## Terminar a mano en CapCut
`python capcut_paquete.py "<proyecto>"` → `09_CAPCUT\`: video limpio (imagen + voz, sin subtítulos ni rótulos), imagen sola, voz a -14 LUFS, `.srt` y rótulos con su minuto, y un LEEME. CapCut de escritorio importa subtítulos `.srt` desde **Subtítulos > Agregar subtítulos** ([ayuda de CapCut](https://www.capcut.com/help/how-to-import-subtitles)). Después de exportar desde CapCut, pasar el archivo por el evaluador.

Cuidado con la nube de CapCut: sus términos piden una licencia mundial, perpetua y sublicenciable sobre el contenido que se sube; trabajar con proyectos locales y guardar copia propia.

## Repositorios revisados
| Repositorio | Qué hace | Decisión |
|---|---|---|
| [capcut-cli](https://github.com/renezander030/capcut-cli) (MIT, ~900 estrellas) | Edita los borradores `draft_content.json` de CapCut desde la terminal | No se usa: choca con el punto 09 de los términos y arriesga la cuenta Pro; además tuvo fallas de seguridad (inyección de comandos) en versiones viejas. Lo que hace ya lo hace el motor |
| [SmartCut / capcut-ai-editor](https://github.com/mrbuslov/capcut-ai-editor) (MIT) | Corta silencios y tomas repetidas dentro de un proyecto de CapCut, sin respaldo | No se usa (mismo motivo); la idea ya está en `grabado.py` |
| [ReaCut](https://github.com/Xiangyu-CAS/rea-capcut) (MIT) | Editor propio inspirado en CapCut, construido con ingeniería inversa | No: solo Mac, en etapa temprana, y su método es justo lo que prohíben los términos |
| [OpenCut](https://github.com/OpenCut-app/OpenCut) (MIT) | Alternativa abierta a CapCut | Para mirar más adelante; está en plena reescritura |
| [canvas-lms](https://github.com/instructure/canvas-lms) (AGPL) | Plataforma de cursos en línea de Instructure (**Canvas**, no Canva) | No es de diseño. Podría servir para publicar cursos con pruebas (por ejemplo, módulos de capacitación), pero exige servidor propio; para eso hay opciones más simples |
| "CapCut Pro Download", "CapCut activated", tema "cupcat" | Programas "pirateados" con archivo protegido por clave | **Peligro:** forma típica de repartir malware y robar cuentas. No descargar nunca |
