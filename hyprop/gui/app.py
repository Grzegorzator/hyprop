"""GUI entry point: ``hyprop-gui`` (console script) or ``python -m``."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("GUI requires PySide6: pip install hyprop[gui]")
        return 1
    from hyprop.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":                               # pragma: no cover
    raise SystemExit(main())
