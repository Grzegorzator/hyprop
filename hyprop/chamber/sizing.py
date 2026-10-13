"""Combustion chamber sizing on an ROP point (stage E8).

Definitions (Sutton Ch. 8; Humble Ch. 7 for hybrid pre/post chambers):

    L* = V_c / At                        (characteristic length)
    tau = V_c * rho_c / mdot             (residence time; rho_c from ROP)

For hybrids the "chamber volume" includes the port free volume plus pre-
and post-combustion chambers. Typical hybrid L* = 1.5-4 m (mixing-limited,
higher than liquids); post-chamber usually 0.5-1.0 x grain diameter long.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from hyprop.core.constants import R_UNIVERSAL
from hyprop.oppoints.design_points import OperatingPoint


@dataclass(frozen=True)
class ChamberDesign:
    """Chamber-level derived quantities at the chosen ROP point."""

    volume_m3: float
    characteristic_length_m: float  #: L* = V_c/At
    residence_time_s: float
    length_over_diameter: float


def characteristic_length(volume_m3: float, throat_area_m2: float) -> float:
    """L* = V_c / At [m] (Sutton Eq. 8-9)."""
    return volume_m3 / throat_area_m2


def residence_time(volume_m3: float, point: OperatingPoint, mdot_kg_s: float) -> float:
    """Tau = V_c * rho_c / mdot [s], rho_c from the ROP chamber state."""
    rho_c = (
        point["pc"] / (R_UNIVERSAL / 0.0265 * point["t_c"]) if "m_c" not in point.values else None
    )
    # molar mass channel is not recorded; use ideal gas with M from gamma?
    # Recorded channels give pc, t_c; effective M via c* would double-count.
    # Use M = 26.5 g/mol typical for HDPE/N2O products (table range 25-28).
    m_eff = 0.0265
    rho_c = point["pc"] * m_eff / (R_UNIVERSAL * point["t_c"])
    return volume_m3 * rho_c / mdot_kg_s


def size_chamber(
    point: OperatingPoint,
    port_volume_m3: float,
    grain_outer_diameter_m: float,
    grain_length_m: float,
    throat_area_m2: float,
    pre_chamber_length_m: float = 0.0,
    post_chamber_length_m: float = 0.0,
) -> ChamberDesign:
    """Aggregate chamber quantities: L*, residence time, L/D.

    ``port_volume_m3`` is the free port volume at the ROP instant
    (impulse-weighted web), from the geometry model.
    """
    section = math.pi * (0.5 * grain_outer_diameter_m) ** 2
    volume = port_volume_m3 + section * (pre_chamber_length_m + post_chamber_length_m)
    total_length = grain_length_m + pre_chamber_length_m + post_chamber_length_m
    return ChamberDesign(
        volume_m3=volume,
        characteristic_length_m=characteristic_length(volume, throat_area_m2),
        residence_time_s=residence_time(volume, point, point["mdot_total"]),
        length_over_diameter=total_length / grain_outer_diameter_m,
    )
