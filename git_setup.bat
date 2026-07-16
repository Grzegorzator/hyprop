@echo off
REM ============================================================
REM  HyProp - inicjalizacja i wyslanie repo na GitHub
REM  Mozna uruchamiac wielokrotnie - naprawia poprzednie proby.
REM ============================================================
cd /d "%~dp0"

rmdir /s /q _DO_USUNIECIA 2>nul

REM 1. Repo (init tylko jesli brak)
if not exist .git git init -b main

REM 2. Tozsamosc autora (lokalnie dla tego repo)
git config user.name "Grzegorzator"
git config user.email "masslaczek12@gmail.com"

REM 3. Commit (jesli jeszcze go nie ma)
git add -A
git commit -m "Etap 0 + E1: architektura HyProp v0.2; core/ (units, config, registry, logging, state); data/ (5 paliw, 4 utleniacze, a,n z HRAP); szkielet api.py; 25 testow pytest"

REM 4. Remote - ustaw wlasciwy adres (nadpisuje bledny)
git remote remove origin 2>nul
git remote add origin https://github.com/Grzegorzator/hyprop.git

REM 5. Push - przy pierwszym razie otworzy sie okno logowania GitHub
git push -u origin main

echo.
echo ============================================================
echo Jesli powyzej nie ma bledow - sprawdz:
echo https://github.com/Grzegorzator/hyprop
echo ============================================================
git log --oneline
pause
