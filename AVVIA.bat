@echo off
title SO.MI.CA. S.p.A. - Gestionale Acquisizioni
cd /d "%~dp0"

:: Prova a lanciare l'exe compilato
if exist "SoMiCa_Gestionale.exe" (
    start "" "SoMiCa_Gestionale.exe"
    exit
)

:: Fallback: launcher Python
where pythonw >nul 2>nul
if not errorlevel 1 (
    start "" pythonw launcher.py
    exit
)

where python >nul 2>nul
if errorlevel 1 (
    echo Python non trovato. Scaricalo da https://www.python.org
    pause
    exit /b 1
)

python -c "import flask" >nul 2>nul
if errorlevel 1 pip install flask >nul 2>nul

python launcher.py
