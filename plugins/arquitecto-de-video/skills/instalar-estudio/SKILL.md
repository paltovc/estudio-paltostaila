---
name: instalar-estudio
description: Instala o actualiza el Estudio Paltostaila en un computador Windows vinculado (motor de scripts, ffmpeg, Python, Pillow, edge-tts, yt-dlp, banco de sonidos CC0 y, si se pide, WhisperX) y verifica que todo funcione. Usar cuando se diga "instalar el estudio", "preparar mi computador para los videos", "actualizar el motor", o cuando el arquitecto detecte que falta el motor o está desactualizado.
---

# Instalar o actualizar el estudio

Destino en el PC: `%USERPROFILE%\EstudioPaltostaila\` con `motor\`, `sonidos\`, `canales\` y opcionalmente `whisperx-venv\`.

## Pasos

1. **Computador vinculado.** Sin herramientas del computador no se puede instalar: decir que se abra esta conversación en la app de escritorio de Claude en el PC con los videos y se vincule el computador (o se inicie una tarea nueva desde la app con el computador elegido). Mientras tanto se puede trabajar guion, prompts y paquete de publicación.
2. **Copiar el motor.** Leer cada archivo de `${CLAUDE_PLUGIN_ROOT}/motor/` (todos son texto: `.py`, `.cmd`, `VERSION`) y escribirlo igual en `%USERPROFILE%\EstudioPaltostaila\motor\` con la herramienta de archivos del computador. Si ya existe un motor, comparar `VERSION`: si es igual, no tocar nada; si es más viejo, copiar el motor actual en una carpeta `motor_<versión vieja>` antes de reemplazarlo, y avisar.
3. **Copiar la biblia de canales** de `${CLAUDE_PLUGIN_ROOT}/canales/` a `%USERPROFILE%\EstudioPaltostaila\canales\` solo si ese canal no existe todavía (nunca pisar una biblia que la persona ya editó).
4. **Herramientas.** Revisar qué falta antes de instalar: `python --version`, `where ffmpeg` (o la carpeta de WinGet `Gyan.FFmpeg`), `python -c "import PIL, edge_tts"`, `where yt-dlp`, y si existe `sonidos\RPG` y `sonidos\Interfaz`. Decir en una línea qué se va a instalar y pedir un sí (instala programas con winget y descarga ~2 MB de sonidos CC0 de opengameart.org).
5. Con el sí, ejecutar `instalar.cmd` del motor **en una ventana visible** (`Start-Process cmd -ArgumentList '/c', '"%USERPROFILE%\EstudioPaltostaila\motor\instalar.cmd"'`), porque winget puede pedir confirmación y el paso de WhisperX pregunta. Explicar que WhisperX es opcional (transcribe local, ~3 GB, 10-20 min); sin él, la transcripción se puede hacer de otra forma pero menos precisa.
6. **Verificación.** Desde la carpeta del motor, `python prueba.py` (arma un video de 12 s con datos inventados en una carpeta temporal y la borra si todo sale bien; tarda ~1 min, lanzarlo en segundo plano con log si la herramienta corta antes). Debe terminar con `PRUEBA SUPERADA`. Si falla, el mensaje dice en qué paso.
7. Informar: qué quedó instalado, qué versión del motor, y si falta WhisperX.

## Notas

- PowerShell bloquea `npm`/`npx` por política: usar `npm.cmd`/`npx.cmd` si hicieran falta.
- Python recién instalado por winget puede no estar en el PATH hasta abrir una terminal nueva: en ese caso usar `py` o la ruta completa en `%LOCALAPPDATA%\Programs\Python\`.
- Mac: el motor funciona igual (`python3`, ffmpeg con Homebrew), pero `instalar.cmd` y `render.cmd` son solo para Windows; correr los scripts uno por uno en el orden de `render.cmd`.
