@echo off
rem Estudio Palto Style - abre WanGP (video local) en el navegador de este computador (solo local).
setlocal
chcp 65001 >nul
set "ESTUDIO_BASE=%USERPROFILE%\EstudioPaltostaila"
set "VL=%ESTUDIO_BASE%\video_local"
set "MOTOR=%ESTUDIO_BASE%\motor"
set "PYTHONIOENCODING=utf-8"
set "HF_HOME=%VL%\hf_cache"
if not exist "%VL%\INSTALADO_OK.txt" goto :sin_instalar
py -3 "%MOTOR%\equipo.py" bienvenida
cd /d "%VL%\wangp"
echo Abriendo WanGP... cuando aparezca la direccion local (http://127.0.0.1:...), abrela en el navegador.
echo Usa solo modelos Wan. Guarda los clips con nombre libre (no escena_NNN) en la carpeta 04_CLIPS_FLOW del video.
echo Para cerrar: Ctrl + C en esta ventana.
"%VL%\venv\Scripts\python" wgp.py
goto :fin
:sin_instalar
echo WanGP no esta instalado (o la instalacion no termino) en este computador.
echo Corre primero motor\video_local\instalar_nvidia.cmd
pause
:fin
endlocal
