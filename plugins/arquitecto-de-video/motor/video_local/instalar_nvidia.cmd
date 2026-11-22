@echo off
rem Estudio Palto Style - instala el video local (WanGP) en un computador con tarjeta NVIDIA.
rem Se corre con doble clic desde la carpeta motor\video_local del estudio. Instala en
rem %USERPROFILE%\EstudioPaltostaila\video_local (programas, caches de pip y de modelos) y deja equipo.json
rem en la carpeta del estudio. No borra nada. Descarga varios GB (programas ahora; modelos al primer uso).
rem Si se corta a medias, se vuelve a correr y sigue donde quedo (la marca INSTALADO_OK.txt dice si termino).
setlocal
chcp 65001 >nul
set "MOTOR=%~dp0.."
set "ESTUDIO_BASE=%USERPROFILE%\EstudioPaltostaila"
set "VL=%ESTUDIO_BASE%\video_local"
set "PYTHONIOENCODING=utf-8"
set "PIP_CACHE_DIR=%VL%\pip_cache"
set "HF_HOME=%VL%\hf_cache"
set "LOG=%VL%\logs\instalar_nvidia.log"
echo.
echo === Estudio Palto Style: video local para NVIDIA ===
echo.
py -3 "%MOTOR%\equipo.py" || goto :error
set "RUTA="
for /f "usebackq delims=" %%r in (`py -3 "%MOTOR%\equipo.py" ruta`) do set "RUTA=%%r"
if not "%RUTA%"=="nvidia_wangp" goto :sin_nvidia
where git >nul 2>&1 || goto :sin_git
py -3.11 --version >nul 2>&1 || goto :sin_python
if exist "%VL%\INSTALADO_OK.txt" goto :ya_estaba
if not exist "%VL%\logs" mkdir "%VL%\logs"
if exist "%VL%\wangp\wgp.py" goto :clonado
if exist "%VL%\wangp" goto :clon_cortado
echo [%time%] Descargando WanGP (repositorio original deepbeepmeep/Wan2GP)...
git clone --depth 1 https://github.com/deepbeepmeep/Wan2GP.git "%VL%\wangp" >> "%LOG%" 2>&1 || goto :error
:clonado
git -C "%VL%\wangp" rev-parse HEAD > "%VL%\WANGP_VERSION.txt" 2>nul || goto :clon_cortado
for /f %%s in ('git -C "%VL%\wangp" status --porcelain') do goto :clon_cortado
echo [%time%] Creando su propio Python 3.11, aparte del estudio...
if not exist "%VL%\venv\Scripts\python.exe" py -3.11 -m venv "%VL%\venv" || goto :error
"%VL%\venv\Scripts\python" -m pip install --upgrade pip >> "%LOG%" 2>&1
echo [%time%] Instalando PyTorch para NVIDIA (CUDA 13; necesita el controlador NVIDIA al dia)...
"%VL%\venv\Scripts\python" -m pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu130 >> "%LOG%" 2>&1 || goto :error
echo [%time%] Instalando lo que pide WanGP...
"%VL%\venv\Scripts\python" -m pip install -r "%VL%\wangp\requirements.txt" >> "%LOG%" 2>&1 || goto :error
"%VL%\venv\Scripts\python" -c "import torch; assert torch.cuda.is_available()" >> "%LOG%" 2>&1 || goto :sin_cuda
"%VL%\venv\Scripts\python" -m pip freeze > "%VL%\requisitos_fijados.txt"
copy /y "%~dp0abrir_wangp.cmd" "%VL%\abrir_wangp.cmd" >nul
copy /y "%~dp0LEEME.md" "%VL%\LEEME.md" >nul
echo instalado %date% %time% > "%VL%\INSTALADO_OK.txt"
echo [%time%] Listo. WanGP quedo instalado en la carpeta video_local del estudio.
py -3 "%MOTOR%\equipo.py" bienvenida
echo Para abrirlo cuando quieras: doble clic en abrir_wangp.cmd (carpeta video_local del estudio).
goto :fin
:sin_nvidia
echo.
echo Este computador no tiene una NVIDIA compatible. No se instala nada:
echo la puerta queda abierta para correr este mismo archivo en un computador con NVIDIA.
goto :fin
:sin_git
echo Falta Git. Instalalo con:  winget install --id Git.Git -e   y vuelve a correr este archivo.
goto :fin
:sin_python
echo Falta Python 3.11. Instalalo con:  winget install --id Python.Python.3.11 -e   y vuelve a correr este archivo.
goto :fin
:ya_estaba
echo WanGP ya esta instalado. Para abrirlo: doble clic en abrir_wangp.cmd (carpeta video_local del estudio).
goto :fin
:clon_cortado
echo La descarga anterior de WanGP quedo cortada: la carpeta video_local\wangp existe pero esta incompleta.
echo Manda esa carpeta (solo wangp) a la Papelera y vuelve a correr este archivo. No se borro nada.
goto :fin
:sin_cuda
echo PyTorch quedo instalado pero no ve la tarjeta NVIDIA. Actualiza el controlador NVIDIA y vuelve a correr este archivo.
echo El detalle quedo en la carpeta video_local\logs. No se borro nada.
goto :fin
:error
echo.
echo Algo fallo. El detalle quedo en la carpeta video_local\logs. No se borro nada.
echo Vuelve a correr este archivo: sigue donde quedo.
:fin
echo.
pause
endlocal
