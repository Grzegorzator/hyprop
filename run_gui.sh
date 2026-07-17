#!/usr/bin/env bash
# HyProp GUI - uruchomienie (po instalacji przez install_linux.sh)
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
    echo "Najpierw uruchom: ./install_linux.sh"
    exit 1
fi
exec .venv/bin/python -m hyprop.gui.app
