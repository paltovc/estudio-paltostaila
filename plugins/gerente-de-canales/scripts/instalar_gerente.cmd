@echo off
chcp 65001>nul
set PYTHONUTF8=1
rem Instala o actualiza el gerente de canales en %USERPROFILE%\EstudioPaltostaila\gerente
rem Respalda los scripts anteriores (nunca borra config, calendario, aprobaciones ni registro).
setlocal
set "G=%USERPROFILE%\EstudioPaltostaila\gerente"
set "AQUI=%~dp0"
set "PY=python"
where py >nul 2>&1 && set "PY=py -3"
if not exist "%G%" mkdir "%G%"
if exist "%G%\VERSION" call :respaldar
copy /y "%AQUI%*.py" "%G%\" >nul
copy /y "%AQUI%VERSION" "%G%\" >nul
if not exist "%G%\tmp" mkdir "%G%\tmp"
%PY% -m pip install --quiet --upgrade google-api-python-client google-auth-oauthlib tzdata
if errorlevel 1 (echo ERROR instalando paquetes de Python & exit /b 1)
cd /d "%G%"
%PY% prueba_gerente.py
exit /b %errorlevel%

:respaldar
set /p VIEJA=<"%G%\VERSION"
set "R=%G%\scripts_%VIEJA%"
if exist "%R%" set "R=%G%\scripts_%VIEJA%_%RANDOM%"
mkdir "%R%"
copy /y "%G%\*.py" "%R%\" >nul
copy /y "%G%\VERSION" "%R%\" >nul
exit /b 0
