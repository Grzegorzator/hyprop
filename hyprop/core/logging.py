"""Central logging configuration (ARCHITECTURE.md, principle 10).

Every HyProp module obtains its logger via :func:`get_logger`, producing a
hierarchy under the root logger ``"hyprop"``. :func:`configure` sets level
and an optional log file capturing the full solver trace (Pc iterations,
convergence, events) for debugging and report appendices.
"""

from __future__ import annotations

import logging as _logging
from pathlib import Path
from typing import Optional, Union

_ROOT_NAME = "hyprop"
_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def get_logger(name: str) -> _logging.Logger:
    """Return a logger namespaced under the ``hyprop`` root logger."""
    if name == _ROOT_NAME or name.startswith(_ROOT_NAME + "."):
        return _logging.getLogger(name)
    return _logging.getLogger(f"{_ROOT_NAME}.{name}")


def configure(
    level: Union[int, str] = "INFO",
    logfile: Optional[Union[str, Path]] = None,
    file_level: Union[int, str] = "DEBUG",
) -> _logging.Logger:
    """Configure the ``hyprop`` root logger.

    Parameters
    ----------
    level:
        Console verbosity (``"DEBUG" | "INFO" | "WARNING" | "ERROR"``).
    logfile:
        Optional path; when given, the complete run (down to ``file_level``)
        is written there.
    file_level:
        Verbosity of the file handler (default ``DEBUG`` = full trace).
    """
    root = _logging.getLogger(_ROOT_NAME)
    root.setLevel(_logging.DEBUG)
    root.handlers.clear()

    console = _logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(_logging.Formatter(_FORMAT))
    root.addHandler(console)

    if logfile is not None:
        file_handler = _logging.FileHandler(Path(logfile), encoding="utf-8")
        file_handler.setLevel(file_level)
        file_handler.setFormatter(_logging.Formatter(_FORMAT))
        root.addHandler(file_handler)

    return root
