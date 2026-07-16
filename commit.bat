@echo off
REM ============================================================
REM  HyProp - szybki commit + push po kazdym etapie
REM  Uzycie: dwuklik, wpisz opis zmian, Enter.
REM ============================================================
cd /d "%~dp0"

git add -A
git status -s
echo.
set /p MSG="Opis zmian (np. E2: physics/ + cea/): "
if "%MSG%"=="" set MSG=Aktualizacja robocza
git commit -m "%MSG%"
git push
echo.
git log --oneline -5
pause
