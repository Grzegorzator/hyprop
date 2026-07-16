@echo off
REM Jednorazowa naprawa: nadpisuje auto-wygenerowany commit GitHuba
REM (README utworzone przy zakladaniu repo na stronie) naszym repo.
cd /d "%~dp0"

git push -u origin main --force

echo.
echo Sprawdz: https://github.com/Grzegorzator/hyprop
git log --oneline
pause
