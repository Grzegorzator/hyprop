"""Delivered-performance metrics (stage E4).

Definitions (Sutton & Biblarz, Ch. 2-3):

    F      = mdot * ve_eff + (pe - pa) * Ae          (thrust)
    Isp    = F / (mdot * g0)                          (specific impulse)
    c*     = pc * At / mdot                           (characteristic vel.)
    Cf     = F / (pc * At)                            (thrust coefficient)
    F      = Cf * pc * At = (c* * Cf) * mdot          (identities)

Efficiencies compare delivered with ideal values:

    eta_cstar = c*_delivered / c*_ideal   (combustion efficiency)
    eta_cf    = Cf_delivered / Cf_ideal   (nozzle efficiency)
    eta_total = eta_cstar * eta_cf        (overall)
"""

from __future__ import annotations

from hyprop.core.constants import G0


def thrust(
    mdot_kg_s: float,
    exhaust_velocity_m_s: float,
    exit_pressure_pa: float,
    ambient_pressure_pa: float,
    exit_area_m2: float,
    momentum_efficiency: float = 1.0,
) -> float:
    """Thrust [N]: momentum term (scaled by nozzle efficiency) + pressure term."""
    momentum = momentum_efficiency * mdot_kg_s * exhaust_velocity_m_s
    return momentum + (exit_pressure_pa - ambient_pressure_pa) * exit_area_m2


def specific_impulse(thrust_n: float, mdot_kg_s: float) -> float:
    """Specific impulse Isp [s] = F / (mdot * g0)."""
    if mdot_kg_s <= 0.0:
        raise ValueError("mdot must be positive.")
    return thrust_n / (mdot_kg_s * G0)


def cstar_delivered(pc_pa: float, throat_area_m2: float, mdot_kg_s: float) -> float:
    """Delivered characteristic velocity c* [m/s] = pc*At/mdot."""
    if mdot_kg_s <= 0.0:
        raise ValueError("mdot must be positive.")
    return pc_pa * throat_area_m2 / mdot_kg_s


def thrust_coefficient_delivered(
    thrust_n: float, pc_pa: float, throat_area_m2: float
) -> float:
    """Delivered thrust coefficient Cf [-] = F/(pc*At)."""
    if pc_pa <= 0.0 or throat_area_m2 <= 0.0:
        raise ValueError("pc and At must be positive.")
    return thrust_n / (pc_pa * throat_area_m2)


def efficiency(delivered: float, ideal: float) -> float:
    """Generic efficiency ratio [-] with sanity check."""
    if ideal <= 0.0:
        raise ValueError("Ideal value must be positive.")
    return delivered / ideal
