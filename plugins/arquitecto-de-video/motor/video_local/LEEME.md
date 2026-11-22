# Video local (Estudio Palto Style)

> Hola, amor 💛
> Este motor de video no corre en el computador de Patricio: le falta una tarjeta gráfica NVIDIA. Pero él dejó la puerta abierta para que funcionara en el tuyo, porque este estudio lo está construyendo para los dos.
> Todo lo que se genere aquí queda en tu computador, sin gastar créditos.
> — Patricio (y el Estudio Palto Style)

## Qué es
Anima las imágenes de los videos (por ejemplo, el personaje del canal de finanzas) en el propio computador, sin internet ni créditos, con **WanGP** (repositorio original `github.com/deepbeepmeep/Wan2GP`). Solo funciona con una tarjeta **NVIDIA de 6 GB o más**. El estudio lo detecta solo con `motor\equipo.py`.

| Equipo | Qué pasa |
|---|---|
| NVIDIA de 8 GB o más | Imagen a video hasta 720p |
| NVIDIA de 6 a 8 GB | Imagen a video hasta 480p |
| Sin NVIDIA (por ejemplo, el PC de Patricio con Intel) | No se instala nada; la puerta queda abierta. Ahí se usa Flow o Higgsfield |

## Instalar (una vez, en el computador con NVIDIA)
1. Actualizar el controlador de la tarjeta NVIDIA (WanGP usa CUDA 13).
2. Doble clic en `motor\video_local\instalar_nvidia.cmd`. Si falta Git o Python 3.11, la ventana dice cómo instalarlos con `winget`.
3. Todo queda en `%USERPROFILE%\EstudioPaltostaila\video_local\` (WanGP, su propio Python, las cachés y los modelos, que se descargan la primera vez que se usan; pueden ser decenas de GB). Si la instalación se corta, se vuelve a correr el mismo archivo y sigue donde quedó; `INSTALADO_OK.txt` aparece solo cuando terminó bien.
4. Las tarjetas GTX 10xx o más antiguas no las cubre este instalador (WanGP pide otra versión de PyTorch para ellas): el archivo lo avisa y no instala.

## Usar
- Doble clic en `video_local\abrir_wangp.cmd`. La primera vez aparece el mensaje de arriba.
- En la página que abre (solo local), elegir un modelo de **imagen a video** de Wan, cargar la imagen de la escena y escribir la indicación de la receta del canal.
- Guardar el clip en la carpeta de clips del proyecto (`04_CLIPS_FLOW` o la que diga `proyecto.json`) con un nombre libre, por ejemplo `local_2026-11-22_01.mp4`, **nunca** `escena_NNN.mp4` (ese nombre lo pone el estudio y podría pisar un clip ya asignado). Después el estudio lo asigna con `asignar_clips.py`, igual que un clip de Flow.
- Usar solo modelos **Wan** (los de nombre «Wan»). WanGP trae también otros (Hunyuan, LTX, Flux, Qwen) con licencias propias y a veces con límites: no se usan en videos publicados sin revisar antes su licencia.
- Para muchas escenas: en WanGP, «Save Queue» y luego `venv\Scripts\python wangp\wgp.py --process cola.zip`.

## Reglas del estudio
- Un video no mezcla resoluciones: si un clip local sale en 720p, todo el video va en 720p.
- Material privado (caras reales, voces) se puede animar aquí porque no sale del computador.

## Licencia
WanGP Community License 2.0: gratis para uso personal e interno; lo que genera se puede publicar en los videos. No se puede revender WanGP como servicio. Si alguna vez se **vende o licencia un clip suelto** hecho con WanGP, hay que poner «Made with WanGP». Rige también su sección 10 (uso aceptable). Los modelos Wan tienen su propia licencia (Apache 2.0); eso vale solo para los Wan. Registrado en `licencias\registro.md`.

## Desinstalar
Mover la carpeta `video_local` a la Papelera, solo con un sí, y marcar su fila en `licencias\registro.md` como «retirado».
