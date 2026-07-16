"""Built-in, read-only propellant reference data (YAML) with loader."""

from hyprop.data.loader import (
    FuelData,
    OxidizerData,
    RegressionEntry,
    SourcedValue,
    list_fuels,
    list_oxidizers,
    load_fuel,
    load_oxidizer,
)

__all__ = [
    "FuelData",
    "OxidizerData",
    "RegressionEntry",
    "SourcedValue",
    "load_fuel",
    "load_oxidizer",
    "list_fuels",
    "list_oxidizers",
]
