#!/usr/bin/env bash
# ============================================================
#  HyProp - instalacja jednym poleceniem (Linux / macOS)
#  Wymaga: python3 (>=3.11) + moduly venv i pip
#    Ubuntu/Debian:  sudo apt install python3 python3-venv python3-pip git
#    Fedora:         sudo dnf install python3 git
#    Arch:           sudo pacman -S python git
#  Tworzy izolowane srodowisko .venv; mozna uruchamiac ponownie.
# ============================================================
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null; then
    echo "[BLAD] Brak python3. Zainstaluj (np. sudo apt install python3 python3-venv python3-pip)."
    exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"[BLAD] Wymagany Python >= 3.11, znaleziono {sys.version.split()[0]}.")
PY

echo "[1/3] Tworzenie srodowiska .venv ..."
[ -d .venv ] || python3 -m venv .venv || {
    echo "[BLAD] Nie mozna utworzyc venv - doinstaluj pakiet python3-venv."; exit 1; }

echo "[2/3] Instalacja HyProp + zaleznosci (moze potrwac kilka minut) ..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[gui,cantera,props,export,dev]"

echo "[3/3] Szybki test instalacji ..."
.venv/bin/python -c "import hyprop, cantera, CoolProp, PySide6; print('OK: HyProp', hyprop.__version__)"

echo
echo "============================================================"
echo "Gotowe. Uruchom aplikacje:  ./run_gui.sh"
echo "Uwaga (GUI na Linuksie): PySide6/Qt wymaga bibliotek xcb -"
echo "jesli okno nie startuje: sudo apt install libxcb-cursor0"
echo "============================================================"
