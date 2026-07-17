"""Writing user-defined propellant cards (GUI 'custom...' option).

Custom cards are plain YAML with the same schema as the built-in
database, stored under the user database root (default ``./database``)
in ``fuels/`` and ``oxidizers/``; the loader searches there after the
package data (see loader._search_paths). Qt-free: the GUI dialog only
collects values and calls these writers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Union

import yaml

from hyprop.core.exceptions import DataError

DEFAULT_ROOT = Path("database")


def _write(kind: str, name: str, record: Dict,
           root: Union[str, Path, None]) -> Path:
    if not name.isidentifier():
        raise DataError(
            "Name must be a valid identifier (letters/digits/underscore).")
    directory = Path(root or DEFAULT_ROOT) / kind
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name.lower()}.yaml"
    path.write_text(yaml.safe_dump(record, sort_keys=False,
                                   allow_unicode=True), encoding="utf-8")
    return path


def save_custom_fuel(
    name: str,
    density_kg_m3: float,
    composition: Dict[str, float],
    hf_j_mol: float,
    regression_a_si: Optional[float] = None,
    regression_n: Optional[float] = None,
    oxidizer: str = "n2o",
    notes: str = "",
    root: Union[str, Path, None] = None,
) -> Path:
    """Write a fully solver-compatible custom fuel card."""
    if density_kg_m3 <= 0:
        raise DataError("Density must be positive.")
    composition = {el: n for el, n in composition.items() if n > 0}
    if not composition:
        raise DataError("Composition needs at least one element.")
    regression = []
    if regression_a_si and regression_n:
        regression.append(dict(
            oxidizer=oxidizer, model="power_law",
            a=float(regression_a_si), n=float(regression_n), m=0.0,
            flux_basis="oxidizer",
            source="User-entered (GUI material card); confirm by fire test",
            verify=True,
        ))
    record = {
        "schema": "fuel/1", "name": name.lower(),
        "display_name": f"{name} (custom)",
        "density": dict(value=float(density_kg_m3),
                        source="User material card", verify=True),
        "composition": composition,
        "composition_source": "User material card",
        "enthalpy_of_formation": dict(
            value=float(hf_j_mol),
            source="User material card [J/mol per formula unit]",
            verify=True),
        "regression": regression,
        "notes": notes or "User-defined fuel (GUI).",
    }
    return _write("fuels", name, record, root)


#: Chemistry base species available in the GRI-Mech mechanism.
OXIDIZER_BASE_SPECIES = ("n2o", "gox", "htp")


def save_custom_oxidizer(
    name: str,
    base: str,
    molar_mass_kg_mol: float,
    reference_density: Optional[float] = None,
    notes: str = "",
    root: Union[str, Path, None] = None,
) -> Path:
    """Write a custom oxidizer card.

    ``base`` selects the combustion chemistry species (n2o / gox / htp -
    the species available in GRI-Mech). NOTE: the equilibrium blowdown
    tank model remains N2O-only; use pressure_fed for other oxidizers.
    """
    if base not in OXIDIZER_BASE_SPECIES:
        raise DataError(f"base must be one of {OXIDIZER_BASE_SPECIES}.")
    record = {
        "schema": "oxidizer/1", "name": name.lower(),
        "display_name": f"{name} (custom, chemistry as {base.upper()})",
        "formula": {"X": 1},
        "molar_mass_kg_mol": float(molar_mass_kg_mol),
        "critical_temperature_k": None, "critical_pressure_pa": None,
        "phase_at_storage": "user-defined",
        "property_backends": [],
        "reference_density": (
            None if reference_density is None else
            dict(value=float(reference_density),
                 source="User material card", verify=True)),
        "parameters": {"chemistry_base": base},
        "notes": notes or "User-defined oxidizer (GUI); tank model: "
                          "pressure_fed recommended.",
    }
    return _write("oxidizers", name, record, root)
