# Tworzy skroty do HyProp GUI (Pulpit + Menu Start) z ikona MELprop.
#
# Skrot wskazuje bezposrednio na pythonw.exe z .venv, wiec aplikacja startuje
# bez okna konsoli. Do diagnostyki bledow nadal sluzy run_gui.bat.
#
# Uruchomienie:
#   powershell -ExecutionPolicy Bypass -File .\create_shortcut.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$pythonw = Join-Path $root ".venv\Scripts\pythonw.exe"
$icon    = Join-Path $root "assets\hyprop.ico"

if (-not (Test-Path $pythonw)) {
    Write-Host "Brak .venv - uruchom najpierw install_windows.bat" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $icon)) {
    Write-Host "Brak assets\hyprop.ico - uruchom: .venv\Scripts\python tools\make_icon.py" -ForegroundColor Red
    exit 1
}

$shell = New-Object -ComObject WScript.Shell

$targets = @(
    [Environment]::GetFolderPath("Desktop"),
    (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs")
)

foreach ($dir in $targets) {
    $lnk = Join-Path $dir "HyProp.lnk"
    $sc  = $shell.CreateShortcut($lnk)
    $sc.TargetPath       = $pythonw
    $sc.Arguments        = "-m hyprop.gui.app"
    $sc.WorkingDirectory = $root
    $sc.IconLocation     = "$icon,0"
    $sc.Description      = "HyProp - preliminary sizing hybrydowych silnikow rakietowych (MELprop)"
    $sc.Save()
    Write-Host "Utworzono: $lnk" -ForegroundColor Green
}

Write-Host ""
Write-Host "Gotowe. Ikona na Pulpicie i w Menu Start." -ForegroundColor Cyan
