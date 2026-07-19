@echo off
REM HyProp - ikona + skroty (Pulpit i Menu Start).
REM Wymaga: assets\melprop_logo.png oraz .venv (install_windows.bat).
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
    echo Najpierw uruchom install_windows.bat
    pause & exit /b 1
)
if not exist assets\melprop_logo.png (
    echo Zapisz logo MELprop jako assets\melprop_logo.png i uruchom ponownie.
    pause & exit /b 1
)

.venv\Scripts\python -c "import PIL" 2>nul || .venv\Scripts\python -m pip install pillow
.venv\Scripts\python tools\make_icon.py || (pause & exit /b 1)
powershell -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1" || (pause & exit /b 1)

echo.
echo Gotowe - skrot HyProp jest na Pulpicie.
pause
