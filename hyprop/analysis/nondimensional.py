"""Dimensionless numbers of the port flow (stage E9, model validation).

Computed from the TimeHistory to flag regime-validity issues
(ARCHITECTURE.md par. 9 item 5):

* Port Reynolds  Re = G * D_h / mu   (G = mass flux = rho*u)
* Port Mach      Ma = u / a with u = G / rho, a = sqrt(gamma*R/M*T)

The combustion-gas viscosity uses a fixed representative value
mu = 8.5e-5 Pa*s (CO2/H2O/N2 mixtures at ~3000-3300 K; Svehla NASA
TR R-132 tables) - adequate for regime flags (Re enters correlations
at ~0.2 power). A full transport model arrives with physics/transport.

Flags raised: laminar port flow (Re < 1e4 - regression correlations
assume turbulent boundary layer) and compressible port flow (Ma > 0.3).
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

from hyprop.core.constants import R_UNIVERSAL
from hyprop.core.state import TimeHistory

#: Representative combustion-gas viscosity [Pa*s] (Svehla, ~3200 K).
MU_COMBUSTION_GAS = 8.5e-5

#: Mean molar mass fallback [kg/mol] when composition channel absent.
M_GAS_DEFAULT = 0.026

RE_TURBULENT_MIN = 1.0e4
MA_INCOMPRESSIBLE_MAX = 0.30


def port_numbers(history: TimeHistory) -> Dict[str, np.ndarray]:
    """Time series of port Re and Ma (at the port exit station)."""
    g_flux = history["g_flux"]
    d_h = history["d_port"]                     # cylindrical: D_h = D_port
    t_c = history["t_c"]
    gamma = history["gamma"]
    reynolds = g_flux * d_h / MU_COMBUSTION_GAS
    r_specific = R_UNIVERSAL / M_GAS_DEFAULT
    rho = history["pc"] / (r_specific * np.maximum(t_c, 300.0))
    velocity = g_flux / np.maximum(rho, 1e-9)
    sound = np.sqrt(gamma * r_specific * np.maximum(t_c, 300.0))
    return {"Re": reynolds, "Ma": velocity / sound}


def regime_flags(history: TimeHistory) -> List[str]:
    """Human-readable warnings about model-validity violations."""
    numbers = port_numbers(history)
    flags: List[str] = []
    # evaluate only while thrust is significant (liquid phase mostly)
    active = history["thrust"] > 0.1 * history["thrust"].max()
    if np.any(numbers["Re"][active] < RE_TURBULENT_MIN):
        flags.append(
            f"Port Re dropped below {RE_TURBULENT_MIN:.0e} during burn - "
            "turbulent regression correlations questionable."
        )
    if np.any(numbers["Ma"][active] > MA_INCOMPRESSIBLE_MAX):
        flags.append(
            f"Port Mach exceeded {MA_INCOMPRESSIBLE_MAX} - incompressible "
            "port-flow assumption strained (consider larger port)."
        )
    return flags
