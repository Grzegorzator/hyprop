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


def _app_icon():
    """Build the application :class:`QIcon` from every asset that exists.

    PNG first: Qt's ICO reader silently fails on the PNG-compressed 256x256
    entry Pillow writes, which is why the taskbar fell back to the generic
    Python icon. The ICO is still added so Qt can pick a crisp small size.
    """
    from PySide6.QtGui import QIcon

    icon = QIcon()
    for name in ("hyprop_256.png", "hyprop.ico", "melprop_logo.png"):
        candidate = ASSETS_DIR / name
        if candidate.is_file():
            icon.addFile(str(candidate))
    return icon if not icon.isNull() else None


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
    icon = _app_icon()
    if icon is not None:
        app.setWindowIcon(icon)
    window = MainWindow()
    if icon is not None:
        # Explicit per-window icon: on Windows the taskbar button reads the
        # window icon, which does not always inherit the application default.
        window.setWindowIcon(icon)
    window.show()
    return app.exec()


if __name__ == "__main__":                               # pragma: no cover
    raise SystemExit(main())
