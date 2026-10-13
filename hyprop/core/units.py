"""Unit handling for HyProp, built on Pint.

Design (ARCHITECTURE.md, principle 4):

* One shared :class:`pint.UnitRegistry` for the whole application.
* The numerical core works on plain ``float`` values in SI base units.
* Conversion happens only at module boundaries (config parsing, I/O, GUI),
  using :func:`to_si`.

Example
-------
>>> to_si("35 bar", "Pa")
3500000.0
>>> to_si(0.025, "m")
0.025
"""

from __future__ import annotations

from typing import Any

import pint

from hyprop.core.exceptions import UnitError

#: Shared unit registry (singleton for the whole application).
ureg: pint.UnitRegistry = pint.UnitRegistry()

#: Shorthand quantity constructor bound to the shared registry.
Q_ = ureg.Quantity

Numeric = int | float
QuantityLike = Numeric | str | pint.Quantity


def to_si(value: QuantityLike, target_unit: str) -> float:
    """Convert ``value`` to a plain float expressed in ``target_unit``.

    Parameters
    ----------
    value:
        Either a bare number (assumed to already be in ``target_unit``),
        a string with units (e.g. ``"35 bar"``), or a ``pint.Quantity``.
    target_unit:
        SI unit the caller expects, e.g. ``"Pa"``, ``"m"``, ``"kg/m^3"``.

    Returns
    -------
    float
        Magnitude of ``value`` expressed in ``target_unit``.

    Raises
    ------
    UnitError
        If the string cannot be parsed or dimensions are incompatible.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    try:
        quantity: Any = Q_(value) if isinstance(value, str) else value
        return float(quantity.to(target_unit).magnitude)
    except pint.errors.DimensionalityError as exc:
        raise UnitError(
            f"Incompatible units: cannot convert {value!r} to '{target_unit}'."
        ) from exc
    except Exception as exc:  # pint parsing errors are heterogeneous
        raise UnitError(f"Cannot parse quantity {value!r}.") from exc
