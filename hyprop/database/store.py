"""User database of engines / materials / injectors / tests (stage E10).

Decision D10: plain YAML files in directories - human-readable,
git-friendly, zero infrastructure. Layout::

    database/
        engines/<name>.yaml     EngineConfig + summary + timestamp
        materials/<name>.yaml   free-form material records
        injectors/<name>.yaml   characterised injectors (Cd, geometry)
        tests/<name>.yaml       fire-test data for calibration

The database root defaults to ``./database`` (project working folder),
overridable per call - it is user data, not package data.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import yaml

from hyprop.core.config import EngineConfig
from hyprop.core.exceptions import DataError
from hyprop.core.logging import get_logger

_log = get_logger(__name__)

CATEGORIES = ("engines", "materials", "injectors", "tests")
DEFAULT_ROOT = Path("database")


def _category_dir(category: str, root: str | Path | None) -> Path:
    if category not in CATEGORIES:
        raise DataError(f"Unknown category '{category}'; use {CATEGORIES}.")
    directory = Path(root or DEFAULT_ROOT) / category
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_engine(
    config: EngineConfig,
    summary: dict | None = None,
    root: str | Path | None = None,
) -> Path:
    """Persist an engine design (config + result summary)."""
    record = {
        "saved_utc": datetime.datetime.utcnow().isoformat(timespec="seconds"),
        "config": config.model_dump(mode="json"),
        "summary": dict(summary or {}),
    }
    path = _category_dir("engines", root) / f"{config.name}.yaml"
    path.write_text(yaml.safe_dump(record, sort_keys=False, allow_unicode=True), encoding="utf-8")
    _log.info("Engine saved: %s", path)
    return path


def load_engine(name: str, root: str | Path | None = None):
    """Load an engine record -> (EngineConfig, summary dict)."""
    path = _category_dir("engines", root) / f"{name}.yaml"
    if not path.exists():
        raise DataError(f"No engine '{name}' in the database.")
    record = yaml.safe_load(path.read_text(encoding="utf-8"))
    return EngineConfig.from_dict(record["config"]), record.get("summary", {})


def save_record(
    category: str,
    name: str,
    record: dict,
    root: str | Path | None = None,
) -> Path:
    """Persist a free-form record (materials / injectors / tests)."""
    record = dict(record)
    record.setdefault(
        "saved_utc",
        datetime.datetime.utcnow().isoformat(timespec="seconds"),
    )
    path = _category_dir(category, root) / f"{name}.yaml"
    path.write_text(yaml.safe_dump(record, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def load_record(category: str, name: str, root: str | Path | None = None) -> dict:
    path = _category_dir(category, root) / f"{name}.yaml"
    if not path.exists():
        raise DataError(f"No record '{category}/{name}'.")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def list_records(category: str, root: str | Path | None = None) -> list[str]:
    return sorted(p.stem for p in _category_dir(category, root).glob("*.yaml"))
