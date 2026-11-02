@echo off
rem Render completo de un video:  render.cmd "C:\ruta\del\video"
rem Borrador de 60 s:             render.cmd "C:\ruta\del\video" borrador
setlocal
set MOTOR=%~dp0
set PYTHONIOENCODING=utf-8
set VIDEO=%~1
if "%VIDEO%"=="" (echo Uso: render.cmd "C:\ruta\del\video" [borrador] & exit /b 1)
cd /d "%MOTOR%"
python frases.py "%VIDEO%" --validar || exit /b 1
if /i "%~2"=="borrador" (
  python armar.py "%VIDEO%" --hasta 60 || exit /b 1
  python sonidos.py "%VIDEO%" || exit /b 1
  python terminar.py "%VIDEO%" --borrador 60 || exit /b 1
  exit /b 0
)
python armar.py "%VIDEO%" || exit /b 1
python sonidos.py "%VIDEO%" || exit /b 1
python terminar.py "%VIDEO%" || exit /b 1
python vertical.py "%VIDEO%" || exit /b 1
python miniatura.py "%VIDEO%" || exit /b 1
python revisar.py "%VIDEO%"
echo FIN
