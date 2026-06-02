@echo off
title Compilazione SO.MI.CA. Gestionale
echo.
echo  Compilazione EXE in corso...
echo.

pip install pyinstaller >nul 2>nul

pyinstaller ^
  --onefile ^
  --windowed ^
  --icon=static\img\icon.ico ^
  --name=SoMiCa_Gestionale ^
  --add-data="static\img\icon.ico;static\img" ^
  --hidden-import=tkinter ^
  --hidden-import=tkinter.ttk ^
  launcher.py

echo.
echo  EXE creato in: dist\SoMiCa_Gestionale.exe
echo  Copia il file nella cartella principale e usa INSTALLA.ps1
echo.
pause
