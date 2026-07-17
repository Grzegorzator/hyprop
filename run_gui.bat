@echo off
REM HyProp GUI - uruchomienie (po instalacji przez install_windows.bat)
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Najpierw uruchom install_windows.bat
    pause & exit /b 1
)
.venv\Scripts\python -m hyprop.gui.app
if errorlevel 1 pause
