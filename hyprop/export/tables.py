"""Tabular exports of simulation results (stage E10).

One call exports the full time history plus the ROP comparison and
phase tables to CSV / XLSX / JSON; the case config is saved as YAML
next to them (single self-documenting result folder).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from hyprop.core.config import EngineConfig
from hyprop.core.logging import get_logger
from hyprop.oppoints import ROPReport

_log = get_logger(__name__)


def export_result(
    result,
    directory: Union[str, Path],
    config: Optional[EngineConfig] = None,
    rop: Optional[ROPReport] = None,
    formats: tuple = ("csv", "xlsx", "json"),
    stem: str = "run",
) -> list:
    """Write history/ROP/phase tables; returns the list of files created."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    history = result.history.to_dataframe()
    written = []

    if "csv" in formats:
        path = directory / f"{stem}_history.csv"
        history.to_csv(path, index=False)
        written.append(path)
    if "json" in formats:
        path = directory / f"{stem}_history.json"
        history.to_json(path, orient="columns", indent=1)
        written.append(path)
    if "xlsx" in formats:
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            _log.warning("openpyxl missing - XLSX export skipped.")
        else:
            path = directory / f"{stem}.xlsx"
            import pandas as pd

            with pd.ExcelWriter(path) as writer:
                history.to_excel(writer, "history", index=False)
                if rop is not None:
                    rop.comparison_table().to_excel(writer, "rop_points")
                    rop.phases_table().to_excel(writer, "phases",
                                                index=False)
            written.append(path)
    if rop is not None and "csv" in formats:
        path = directory / f"{stem}_rop_points.csv"
        rop.comparison_table().to_csv(path)
        written.append(path)
        path = directory / f"{stem}_phases.csv"
        rop.phases_table().to_csv(path, index=False)
        written.append(path)
    if config is not None:
        path = directory / f"{stem}_config.yaml"
        config.to_yaml(path)
        written.append(path)
    _log.info("Exported %d files -> %s", len(written), directory)
    return written
