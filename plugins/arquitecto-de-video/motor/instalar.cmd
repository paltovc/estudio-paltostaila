@echo off
rem Instalador del Estudio Paltostaila para Windows. Se puede ejecutar varias veces: salta lo que ya esta.
rem Deja todo en %USERPROFILE%\EstudioPaltostaila (motor, sonidos y, si se elige, WhisperX).
setlocal
set ESTUDIO=%USERPROFILE%\EstudioPaltostaila
echo === Estudio Paltostaila: carpeta %ESTUDIO%
if not exist "%ESTUDIO%\motor" mkdir "%ESTUDIO%\motor"
if not exist "%ESTUDIO%\sonidos" mkdir "%ESTUDIO%\sonidos"
if not exist "%ESTUDIO%\canales" mkdir "%ESTUDIO%\canales"
if /i not "%~dp0"=="%ESTUDIO%\motor\" (
  xcopy /y /q "%~dp0*.py" "%ESTUDIO%\motor\" >nul
  xcopy /y /q "%~dp0*.cmd" "%ESTUDIO%\motor\" >nul
)

echo === 1/4 Python
where python >nul 2>nul || winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
echo === 2/4 ffmpeg
where ffmpeg >nul 2>nul || (dir /s /b "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg.exe" >nul 2>nul) || winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
echo === 3/4 Pillow (imagenes), edge-tts (voces) y yt-dlp (lectura de videos de referencia)
python -m pip install --user --quiet pillow edge-tts
where yt-dlp >nul 2>nul || winget install -e --id yt-dlp.yt-dlp --accept-source-agreements --accept-package-agreements
echo === 4/4 Sonidos CC0 de Kenney (opengameart.org, uso libre sin atribucion)
if not exist "%ESTUDIO%\sonidos\RPG" (
  powershell -NoProfile -Command "Invoke-WebRequest https://opengameart.org/sites/default/files/RPGsounds_Kenney.zip -OutFile $env:TEMP\rpg.zip; Expand-Archive -Force $env:TEMP\rpg.zip '%ESTUDIO%\sonidos\RPG'"
)
if not exist "%ESTUDIO%\sonidos\Interfaz" (
  powershell -NoProfile -Command "Invoke-WebRequest https://opengameart.org/sites/default/files/kenney_interfaceSounds.zip -OutFile $env:TEMP\ui.zip; Expand-Archive -Force $env:TEMP\ui.zip '%ESTUDIO%\sonidos\Interfaz'"
)

echo.
echo === Opcional: WhisperX para transcribir local (unos 3 GB, tarda 10-20 min)
if exist "%ESTUDIO%\whisperx-venv\Scripts\whisperx.exe" (echo ya instalado) else (
  choice /m "Instalar WhisperX ahora"
  if errorlevel 2 (echo omitido) else (
    python -m venv "%ESTUDIO%\whisperx-venv"
    "%ESTUDIO%\whisperx-venv\Scripts\python.exe" -m pip install --upgrade pip
    "%ESTUDIO%\whisperx-venv\Scripts\python.exe" -m pip install whisperx
  )
)
echo.
echo LISTO. Motor en %ESTUDIO%\motor
pause
