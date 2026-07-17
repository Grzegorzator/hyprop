"""Loader and validation of built-in propellant databases (YAML).

The ``data/`` package is read-only reference data shipped with HyProp
(user-editable records live in ``database/``, stage E10). Each YAML file
is validated against a pydantic schema on load; values carry their source
and an optional ``verify`` flag marking numbers that still require
confirmation against primary literature or fire tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

from hyprop.core.exceptions import DataError

_DATA_DIR = Path(__file__).parent

#: User-database fallback (custom cards from the GUI); cwd-relative.
_USER_DIR = Path("database")


def _find(kind: str, name: str) -> Path:
    """Package data first, then the user database directory."""
    for base in (_DATA_DIR, _USER_DIR):
        path = base / kind / f"{name.lower()}.yaml"
        if path.exists():
            return path
    return _DATA_DIR / kind / f"{name.lower()}.yaml"   # -> DataError


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourcedValue(_Model):
    """A numeric value carrying its bibliographic source."""

    value: float
    source: str
    verify: bool = Field(
        False, description="True if the value still awaits confirmation"
    )


class RegressionEntry(_Model):
    """One regression-law dataset: rdot = a * G^n * L^m (SI units)."""

    oxidizer: str
    model: str = "power_law"
    a: float = Field(..., gt=0, description="[m/s / (kg/m^2/s)^n / m^m]")
    n: float = Field(..., gt=0)
    m: float = 0.0
    flux_basis: str = "oxidizer"
    source: str
    verify: bool = False


class FuelData(_Model):
    """Validated content of a ``data/fuels/*.yaml`` file."""

    schema_id: str = Field(..., alias="schema")
    name: str
    display_name: str
    density: SourcedValue
    composition: Dict[str, float]
    composition_source: str
    enthalpy_of_formation: Optional[SourcedValue] = None
    regression: List[RegressionEntry] = Field(default_factory=list)
    notes: str = ""

    def regression_for(self, oxidizer: str) -> List[RegressionEntry]:
        """Return regression datasets available for ``oxidizer``."""
        return [r for r in self.regression if r.oxidizer == oxidizer.lower()]


class OxidizerData(_Model):
    """Validated content of a ``data/oxidizers/*.yaml`` file."""

    schema_id: str = Field(..., alias="schema")
    name: str
    display_name: str
    formula: Dict[str, float]
    molar_mass_kg_mol: float = Field(..., gt=0)
    critical_temperature_k: Optional[float] = None
    critical_pressure_pa: Optional[float] = None
    phase_at_storage: str
    property_backends: List[str] = Field(default_factory=list)
    reference_density: Optional[SourcedValue] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


def _load_yaml(path: Path) -> dict:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DataError(f"Database entry not found: {path.name}") from exc
    if not isinstance(raw, dict):
        raise DataError(f"{path.name}: top level must be a mapping.")
    return raw


def load_fuel(name: str) -> FuelData:
    """Load and validate a fuel by database name (e.g. ``'hdpe'``)."""
    path = _find("fuels", name)
    try:
        return FuelData.model_validate(_load_yaml(path))
    except ValueError as exc:
        raise DataError(f"Invalid fuel entry '{name}': {exc}") from exc


def load_oxidizer(name: str) -> OxidizerData:
    """Load and validate an oxidizer by database name (e.g. ``'n2o'``)."""
    path = _find("oxidizers", name)
    try:
        return OxidizerData.model_validate(_load_yaml(path))
    except ValueError as exc:
        raise DataError(f"Invalid oxidizer entry '{name}': {exc}") from exc


def _list(kind: str) -> List[str]:
    names = {p.stem for p in (_DATA_DIR / kind).glob("*.yaml")}
    if (_USER_DIR / kind).is_dir():
        names |= {p.stem for p in (_USER_DIR / kind).glob("*.yaml")}
    return sorted(names)


def list_fuels() -> List[str]:
    """Names of all fuels (built-in + user database)."""
    return _list("fuels")


def list_oxidizers() -> List[str]:
    """Names of all oxidizers (built-in + user database)."""
    return _list("oxidizers")
