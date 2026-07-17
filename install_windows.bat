@echo off
REM ============================================================
REM  HyProp - instalacja jednym klikiem (Windows)
REM  Wymaga: Python 3.11+ (python.org, z opcja "Add to PATH")
REM  Tworzy izolowane srodowisko .venv i instaluje zaleznosci.
REM  Mozna uruchamiac ponownie - naprawia/aktualizuje instalacje.
REM ============================================================
cd /d "%~dp0"

where py >nul 2>nul || where python >nul 2>nul || (
    echo [BLAD] Nie znaleziono Pythona. Zainstaluj z https://python.org
    echo        i zaznacz "Add python.exe to PATH", potem uruchom ponownie.
    pause & exit /b 1
)

echo [1/3] Tworzenie srodowiska .venv ...
if not exist .venv (py -3 -m venv .venv 2>nul || python -m venv .venv)

echo [2/3] Instalacja HyProp + zaleznosci (moze potrwac kilka minut) ...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e .[gui,cantera,props,export,dev]
if errorlevel 1 (
    echo [BLAD] Instalacja nie powiodla sie - zobacz komunikaty wyzej.
    pause & exit /b 1
)

echo [3/3] Szybki test instalacji ...
.venv\Scripts\python -c "import hyprop, cantera, CoolProp, PySide6; print('OK: HyProp', hyprop.__version__)"

echo.
echo ============================================================
echo Gotowe. Uruchom aplikacje przez run_gui.bat
echo ============================================================
pause
