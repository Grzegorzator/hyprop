@echo off
REM ============================================================
REM  HyProp - wyslanie na GitHub commitow przygotowanych w Cowork.
REM  Claude robi git add + git commit z opisem; tutaj tylko push,
REM  bo poswiadczenia GitHub sa wylacznie na tym komputerze.
REM  Uzycie: dwuklik.
REM ============================================================
cd /d "%~dp0"

echo Commity oczekujace na wyslanie:
git log --oneline origin/main..HEAD
echo.
git push
echo.
git log --oneline -5
pause
