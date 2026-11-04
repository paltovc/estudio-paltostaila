@echo off
chcp 65001 >nul
title Sala de edicion - Estudio Palto Style (cierra esta ventana para apagarla)
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
python sala.py --abrir %*
if errorlevel 1 pause
