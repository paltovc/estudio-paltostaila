@echo off
chcp 65001 >nul
title Sala de edicion EN RED - Estudio Palto Style (cierra esta ventana para apagarla)
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo Copia el enlace "desde otro aparato" que aparece abajo y abrelo en el otro notebook o celular (mismo wifi).
python sala.py --abrir --red %*
if errorlevel 1 pause
