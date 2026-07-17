"""GUI view-model (stage E12) - Qt-free, fully testable.

MVVM separation (ARCHITECTURE.md): the view (main_window) binds widgets
to this view-model; the view-model talks only to hyprop.api. All state
lives in a plain dict mirror of EngineConfig, edited via dotted paths
(same convention as batch overrides).
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, List, Optional

import hyprop.api as api
from hyprop.core.config import EngineConfig
from hyprop.core.logging import get_logger
from hyprop.oppoints import ROPReport, analyze

_log = get_logger(__name__)

#: (dotted path, label, unit) rows shown in the input form, per tab.
FORM_LAYOUT: Dict[str, List[tuple]] = {
    "Mission": [
        ("mission.thrust_n", "Required thrust", "N"),
        ("mission.total_impulse_ns", "Total impulse", "N s"),
        ("mission.burn_time_s", "Burn time", "s"),
        ("mission.design_altitude_m", "Design altitude", "m"),
        ("mission.safety_factor", "Safety factor", "-"),
    ],
    "Propellants": [
        ("oxidizer.name", "Oxidizer", "-"),
        ("oxidizer.temperature_k", "Tank temperature", "K"),
        ("fuel.name", "Fuel", "-"),
        ("fuel.density_kg_m3", "Fuel density", "kg/m3"),
    ],
    "Grain": [
        ("grain.geometry", "Geometry", "-"),
        ("grain.length_m", "Length", "m"),
        ("grain.outer_diameter_m", "Outer diameter", "m"),
        ("grain.port.initial_diameter_m", "Port diameter", "m"),
    ],
    "Feed system": [
        ("tank.model", "Tank model", "-"),
        ("tank.volume_m3", "Tank volume", "m3"),
        ("tank.oxidizer_mass_kg", "Oxidizer mass", "kg"),
        ("injector.model", "Injector model", "-"),
        ("injector.discharge_coefficient", "Cd", "-"),
        ("injector.orifice_count", "Orifice count", "-"),
        ("injector.orifice_diameter_m", "Orifice diameter", "m"),
    ],
    "Nozzle": [
        ("nozzle.throat_diameter_m", "Throat diameter", "m"),
        ("nozzle.expansion_ratio", "Expansion ratio", "-"),
        ("nozzle.divergence_half_angle_deg", "Half-angle", "deg"),
        ("efficiencies.eta_cstar", "eta c*", "-"),
    ],
    "Simulation": [
        ("simulation.dt_s", "Time step", "s"),
        ("simulation.t_max_s", "Time budget", "s"),
        ("simulation.pc_solver", "Pc solver", "-"),
    ],
}


#: Display units per unit system; config stays SI internally.
UNIT_SYSTEMS = ("si", "metric", "imperial")

DISPLAY_UNITS: Dict[str, Dict[str, str]] = {
    "mission.thrust_n":          {"si": "N",     "metric": "N",     "imperial": "lbf"},
    "mission.total_impulse_ns":  {"si": "N*s",   "metric": "N*s",   "imperial": "lbf*s"},
    "mission.design_altitude_m": {"si": "m",     "metric": "m",     "imperial": "ft"},
    "oxidizer.temperature_k":    {"si": "K",     "metric": "degC",  "imperial": "degF"},
    "fuel.density_kg_m3":        {"si": "kg/m^3","metric": "kg/m^3","imperial": "lb/ft^3"},
    "grain.length_m":            {"si": "m",     "metric": "mm",    "imperial": "in"},
    "grain.outer_diameter_m":    {"si": "m",     "metric": "mm",    "imperial": "in"},
    "grain.port.initial_diameter_m":
                                 {"si": "m",     "metric": "mm",    "imperial": "in"},
    "tank.volume_m3":            {"si": "m^3",   "metric": "L",     "imperial": "in^3"},
    "tank.oxidizer_mass_kg":     {"si": "kg",    "metric": "kg",    "imperial": "lb"},
    "injector.orifice_diameter_m":
                                 {"si": "m",     "metric": "mm",    "imperial": "in"},
    "nozzle.throat_diameter_m":  {"si": "m",     "metric": "mm",    "imperial": "in"},
}


def field_choices() -> Dict[str, List[str]]:
    """Dropdown options for choice-type fields (database + registry)."""
    from hyprop.core.registry import autodiscover, list_models
    from hyprop.data import list_fuels, list_oxidizers

    autodiscover()
    models = list_models()
    return {
        "oxidizer.name": list_oxidizers(),
        "fuel.name": list_fuels(),
        "grain.geometry": models["geometry"],
        "injector.model": models["injector"],
        "tank.model": models["tank"],
        "simulation.pc_solver": ["fixed_point", "brent"],
    }


class SessionViewModel:
    """Holds the edited config and the last run results."""

    def __init__(self) -> None:
        self.unit_system: str = "si"
        self.raw: Dict[str, Any] = {}
        self.result = None
        self.rop: Optional[ROPReport] = None
        self.source_path: Optional[Path] = None

    # ------------------------------------------------------------ config
    def load(self, path) -> None:
        self.raw = api.load_config(path).model_dump(mode="python")
        self.source_path = Path(path)

    def save(self, path) -> None:
        api.save_config(self.config(), path)

    def config(self) -> EngineConfig:
        return EngineConfig.from_dict(copy.deepcopy(self.raw))

    def get(self, path: str) -> Any:
        node: Any = self.raw
        for key in path.split("."):
            node = node[key]
        return node

    def set(self, path: str, text: str) -> None:
        """Set a value from widget text (numbers parsed, else string).

        Missing intermediate branches are created - combo boxes emit
        change signals before any YAML is loaded.
        """
        keys = path.split(".")
        node = self.raw
        for key in keys[:-1]:
            node = node.setdefault(key, {})
        try:
            value: Any = float(text)
        except ValueError:
            value = text
        node[keys[-1]] = value

    def validate(self) -> Optional[str]:
        """Return an error message or None when the config is valid."""
        try:
            self.config()
            return None
        except Exception as exc:                        # noqa: BLE001
            return str(exc)

    # ------------------------------------------------------- display units
    def set_unit_system(self, system: str) -> None:
        if system not in UNIT_SYSTEMS:
            raise ValueError(f"Unknown unit system '{system}'.")
        self.unit_system = system

    def display_unit(self, path: str, si_unit: str) -> str:
        """Unit shown next to the field in the current system."""
        return DISPLAY_UNITS.get(path, {}).get(self.unit_system, si_unit)

    def get_display(self, path: str):
        """Field value converted from SI to the display unit."""
        value = self.get(path)
        units = DISPLAY_UNITS.get(path)
        if value is None or units is None or self.unit_system == "si"                 or not isinstance(value, (int, float)):
            return value
        from hyprop.core.units import Q_
        si_unit = units["si"]
        quantity = Q_(float(value), si_unit).to(units[self.unit_system])
        return float(quantity.magnitude)

    def set_display(self, path: str, text: str) -> None:
        """Set a field from display-unit text (converted back to SI)."""
        units = DISPLAY_UNITS.get(path)
        if units is None or self.unit_system == "si":
            self.set(path, text)
            return
        try:
            value = float(text)
        except ValueError:
            self.set(path, text)
            return
        from hyprop.core.units import Q_
        si_value = Q_(value, units[self.unit_system]).to(units["si"]).magnitude
        self.set(path, str(float(si_value)))

    # -------------------------------------------------------------- run
    def run(self) -> None:
        """Blocking transient run (the view wraps this in a thread)."""
        config = self.config()
        self.result = api.run(config)
        self.rop = analyze(self.result)
        _log.info("GUI run finished: %s", self.result.summary)

    def summary_rows(self) -> List[tuple]:
        if self.result is None:
            return []
        rows = [(k, f"{v:.4g}") for k, v in self.result.summary.items()]
        if self.rop is not None:
            iw = self.rop.point("impulse_weighted")
            rows += [(f"IW {ch}", f"{iw[ch]:.4g}")
                     for ch in ("thrust", "pc", "of", "isp")]
        return rows

    def export(self, directory) -> list:
        from hyprop.export import export_result

        return export_result(self.result, directory, config=self.config(),
                             rop=self.rop)

    def report(self, path):
        from hyprop.export import generate_report

        return generate_report(self.config(), self.result, self.rop, path)
