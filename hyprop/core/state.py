"""Time-history container filled by the transient solver (E6).

:class:`TimeHistory` is an append-only recorder: the solver calls
:meth:`TimeHistory.record` once per time step with keyword channels, and
downstream modules (``oppoints``, ``analysis``, ``export``) read the
finalised NumPy arrays. Channel names are standardised in
:data:`CHANNELS` so that plots, ROP weighting and reports agree on
semantics and units.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

#: Standard channel names -> (description, SI unit).
CHANNELS: Dict[str, tuple] = {
    "t": ("Time", "s"),
    "thrust": ("Thrust", "N"),
    "pc": ("Chamber pressure", "Pa"),
    "p_tank": ("Tank pressure", "Pa"),
    "of": ("Oxidizer-to-fuel ratio", "-"),
    "isp": ("Specific impulse (delivered)", "s"),
    "cstar": ("Characteristic velocity", "m/s"),
    "cf": ("Thrust coefficient", "-"),
    "gamma": ("Chamber specific heat ratio cp/cv (frozen)", "-"),
    "gamma_eq": ("Chamber equilibrium isentropic exponent gamma_s", "-"),
    "t_c": ("Chamber temperature", "K"),
    "mdot_ox": ("Oxidizer mass flow", "kg/s"),
    "mdot_fuel": ("Fuel mass flow", "kg/s"),
    "mdot_total": ("Total mass flow", "kg/s"),
    "g_flux": ("Port mass flux (per flux_basis)", "kg/(m^2*s)"),
    "rdot": ("Regression rate", "m/s"),
    "web": ("Burned web thickness", "m"),
    "d_port": ("Equivalent port diameter", "m"),
    "m_fuel": ("Fuel mass remaining", "kg"),
    "m_ox": ("Oxidizer mass remaining", "kg"),
    "m_ox_liquid": ("Liquid oxidizer mass remaining", "kg"),
    "t_tank": ("Tank temperature", "K"),
    "impulse": ("Cumulative impulse", "N*s"),
}


class TimeHistory:
    """Append-only recorder of simulation channels.

    Unknown channel names are rejected to protect downstream consumers;
    extend :data:`CHANNELS` when the solver grows a new output.
    """

    def __init__(self) -> None:
        self._data: Dict[str, List[float]] = {}

    def record(self, **channels: float) -> None:
        """Append one time step. Every call must use consistent channels."""
        for key, value in channels.items():
            if key not in CHANNELS:
                raise KeyError(
                    f"Unknown channel '{key}'. Known: {sorted(CHANNELS)}"
                )
            self._data.setdefault(key, []).append(float(value))
        lengths = {len(v) for v in self._data.values()}
        if len(lengths) > 1:
            raise ValueError("Inconsistent channel set across records.")

    def __len__(self) -> int:
        return len(next(iter(self._data.values()))) if self._data else 0

    def __getitem__(self, channel: str) -> np.ndarray:
        return np.asarray(self._data[channel], dtype=float)

    @property
    def channels(self) -> List[str]:
        """Names of channels recorded so far."""
        return sorted(self._data)

    def to_dataframe(self) -> pd.DataFrame:
        """Return the full history as a pandas DataFrame (one row per step)."""
        return pd.DataFrame({k: self._data[k] for k in self.channels})
