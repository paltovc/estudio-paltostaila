---
name: instalar-estudio
description: Instala o actualiza el Estudio Paltostaila en un computador Windows vinculado (motor de scripts, ffmpeg, Python, Pillow, edge-tts, yt-dlp, banco de sonidos CC0 y, si se pide, WhisperX) y verifica que todo funcione. Usar cuando se diga "instalar el estudio", "preparar mi computador para los videos", "actualizar el motor", o cuando el arquitecto detecte que falta el motor o está desactualizado.
---

# Instalar o actualizar el estudio

Destino en el PC: `%USERPROFILE%\EstudioPaltostaila\` con `motor\`, `sonidos\`, `canales\` y opcionalmente `whisperx-venv\`.

## Pasos

1. **Computador vinculado.** Sin herramientas del computador no se puede instalar: decir que se abra esta conversación en la app de escritorio de Claude en el PC con los videos y se vincule el computador (o se inicie una tarea nueva desde la app con el computador elegido). Mientras tanto se puede trabajar guion, prompts y paquete de publicación.
2. **Copiar el motor.** Leer cada archivo de `${CLAUDE_PLUGIN_ROOT}/motor/` (todos son texto: `.py`, `.cmd`, `.html`, `.ps1`, `VERSION`; los `.cmd` con saltos de línea CRLF y `accesos_escritorio.ps1` con BOM UTF-8 para que Windows lea bien los acentos) y escribirlo igual en `%USERPROFILE%\EstudioPaltostaila\motor\` con la herramienta de archivos del computador. Si ya existe un motor, comparar `VERSION`: si es igual, no tocar nada; si es más viejo, copiar el motor actual en una carpeta `motor_<versión vieja>` antes de reemplazarlo, y avisar.
3. **Copiar la biblia de canales** de `${CLAUDE_PLUGIN_ROOT}/canales/` a `%USERPROFILE%\EstudioPaltostaila\canales\` solo si ese canal no existe todavía (nunca pisar una biblia que la persona ya editó).
4. **Herramientas.** Revisar qué falta antes de instalar: `python --version`, `where ffmpeg` (o la carpeta de WinGet `Gyan.FFmpeg`), `python -c "import PIL, edge_tts"`, `where yt-dlp`, y si existe `sonidos\RPG` y `sonidos\Interfaz`. Decir en una línea qué se va a instalar y pedir un sí (instala programas con winget y descarga ~2 MB de sonidos CC0 de opengameart.org).
5. Con el sí, ejecutar `instalar.cmd` del motor **en una ventana visible** (`Start-Process cmd -ArgumentList '/c', '"%USERPROFILE%\EstudioPaltostaila\motor\instalar.cmd"'`), porque winget puede pedir confirmación y el paso de WhisperX pregunta. Explicar que WhisperX es opcional (transcribe local, ~3 GB, 10-20 min); sin él, la transcripción se puede hacer de otra forma pero menos precisa.
6. **Accesos del escritorio.** `powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\EstudioPaltostaila\motor\accesos_escritorio.ps1"` crea "Sala de edición" y "Sala de edición (red de la casa)" en el escritorio para que la persona abra la sala sola. Si hay proyectos fuera de `EstudioPaltostaila\proyectos` (Documentos, Imágenes, Google Drive), anotar sus carpetas en `EstudioPaltostaila\proyectos_externos.txt`, una por línea.
6c. **Herramientas propias (0.11):** `python -m pip install rapidocr_onnxruntime pypdfium2`; modelos opcionales (con el sí de la persona): `python texto_imagen.py instalar-modelo` (LaMa, ~200 MB, Apache-2.0) y `python mejorar.py instalar-modelo` (Real-ESRGAN, ~130 MB, BSD-3). Comprobar que OpenCV tenga rastreador: `python -c "import cv2;print(hasattr(cv2,'TrackerCSRT_create') or hasattr(cv2,'TrackerMIL_create'))"`.
6b. **Quitar fondo (opcional):** solo con un sí de la persona, `python -m pip install "rembg[cpu]"`; el modelo `isnet-general-use` (~179 MB, uso comercial permitido) se baja solo la primera vez que se usa. Nunca usar `bria-rmbg` ni RMBG-2.0 (no comerciales).
7. **Verificación.** Desde la carpeta del motor, `python prueba.py` (arma un video de 12 s con datos inventados en una carpeta temporal y la borra si todo sale bien; tarda ~1 min, lanzarlo en segundo plano con log si la herramienta corta antes). Debe terminar con `PRUEBA SUPERADA`. Si falla, el mensaje dice en qué paso.
8. **Clave de YouTube (opcional, gratis, recomendada para tendencias).** Solo si la persona quiere el escáner con la API oficial. Lo hace ella, en su navegador (no abrir ventanas por ella):
   1. En https://console.cloud.google.com crear un proyecto (por ejemplo `estudio-tendencias`). No hace falta activar facturación.
   2. En la biblioteca de APIs activar **YouTube Data API v3**.
   3. Credenciales → Crear credenciales → Clave de API. Editar la clave y en Restricciones de API dejar **solo YouTube Data API v3**.
   4. Crear `%USERPROFILE%\EstudioPaltostaila\claves\youtube.env` con una línea `YT_API_KEY=<la clave>` (abrir el Bloc de notas: `notepad "%USERPROFILE%\EstudioPaltostaila\claves\youtube.env"`). La clave nunca se pega en el chat; si llega a aparecer en el chat o en un archivo compartido, borrarla en la consola de Google y crear otra.
   Basta con datos públicos: no conectar la cuenta del canal (OAuth) para esto. Probar con `python scanner_youtube.py "ahorrar dinero" --paginas 1`.
9. Informar: qué quedó instalado, qué versión del motor, si falta WhisperX y si hay clave de YouTube.

## Notas

- PowerShell bloquea `npm`/`npx` por política: usar `npm.cmd`/`npx.cmd` si hicieran falta.
- Python recién instalado por winget puede no estar en el PATH hasta abrir una terminal nueva: en ese caso usar `py` o la ruta completa en `%LOCALAPPDATA%\Programs\Python\`.
- Mac: el motor funciona igual (`python3`, ffmpeg con Homebrew), pero `instalar.cmd` y `render.cmd` son solo para Windows; correr los scripts uno por uno en el orden de `render.cmd`.
