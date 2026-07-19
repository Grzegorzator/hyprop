"""GUI entry point: ``hyprop-gui`` (console script) or ``python -m``."""

from __future__ import annotations

import sys
from pathlib import Path

#: Windows Application User Model ID -- required for the taskbar to show the
#: application icon instead of the generic Python icon (MSDN: SetCurrentProcess
#: ExplicitAppUserModelID).
APP_ID = "MELprop.HyProp.GUI.1"

#: Repository-root ``assets`` directory holding the application icon.
ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"


def _icon_path() -> Path | None:
    """Return the first existing application icon file, or ``None``."""
    for name in ("hyprop.ico", "melprop_logo.png"):
        candidate = ASSETS_DIR / name
        if candidate.is_file():
            return candidate
    return None


def main() -> int:
    try:
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("GUI requires PySide6: pip install hyprop[gui]")
        return 1
    from hyprop.gui.main_window import MainWindow

    if sys.platform == "win32":                          # pragma: no cover
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:                                # noqa: BLE001
            pass

    app = QApplication(sys.argv)
    icon_file = _icon_path()
    if icon_file is not None:
        app.setWindowIcon(QIcon(str(icon_file)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":                               # pragma: no cover
    raise SystemExit(main())
