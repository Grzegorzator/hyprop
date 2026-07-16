"""Nozzle sizing on a Representative Operating Point (stage E8).

Inputs come exclusively from an ROP operating point (ARCHITECTURE.md
principle 8), by default the impulse-weighted point:

* throat: At = F / (Cf * Pc)  ->  mdot = Pc*At*Cd/c*   (Sutton Eq. 3-31)
* expansion: eps such that pe = pa(design altitude)     (optimum, Eq. 3-25)
* exit diameter, delivered Cf with divergence loss.

Design altitude for an ascent 0 -> apogee: a single fixed nozzle cannot
be adapted everywhere; until the trajectory module exists, the default
heuristic picks h_design = apogee/3 (approximately the altitude band
where the impulse-weighted part of the burn happens for typical
sounding-rocket TWR). Override via mission.design_altitude_m.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from hyprop.core.logging import get_logger
from hyprop.nozzle.losses import divergence_efficiency
from hyprop.oppoints.design_points import OperatingPoint
from hyprop.physics import atmosphere
from hyprop.physics.compressible import (
    exit_pressure_ratio,
    optimum_expansion_ratio,
    thrust_coefficient,
)

_log = get_logger(__name__)

#: Default design-altitude fraction of apogee (heuristic; see module doc).
DESIGN_ALTITUDE_FRACTION = 1.0 / 3.0


@dataclass(frozen=True)
class NozzleDesign:
    """Result of nozzle sizing."""

    throat_diameter_m: float
    exit_diameter_m: float
    expansion_ratio: float
    design_altitude_m: float
    design_ambient_pa: float
    exit_pressure_pa: float
    cf_design: float                 #: Cf at design point (with divergence)
    cf_sea_level: float              #: Cf at lift-off (overexpansion check)
    separation_risk: bool            #: pe < 0.4*pa at sea level (Summerfield)


def design_altitude_from_apogee(apogee_m: float) -> float:
    """Heuristic h_design = apogee/3 (to be replaced by trajectory data)."""
    return DESIGN_ALTITUDE_FRACTION * apogee_m


def size_nozzle(
    point: OperatingPoint,
    thrust_target_n: float,
    design_altitude_m: float,
    half_angle_deg: float = 15.0,
) -> NozzleDesign:
    """Size throat and expansion for a target thrust at the ROP point.

    Parameters
    ----------
    point:
        ROP operating point providing ``pc`` [Pa] and ``gamma`` [-]
        (impulse-weighted point recommended).
    thrust_target_n:
        Thrust to deliver at the design point [N].
    design_altitude_m:
        Altitude of pressure adaptation (pe = pa there) [m].
    """
    pc = point["pc"]
    gamma = point["gamma"]
    pa_design = atmosphere.pressure(design_altitude_m)

    eps = optimum_expansion_ratio(pc / pa_design, gamma)
    pe_over_pc = exit_pressure_ratio(eps, gamma)
    lam = divergence_efficiency(half_angle_deg)

    cf_design = lam * thrust_coefficient(
        gamma, eps, pe_over_pc, pa_design / pc
    )
    throat_area = thrust_target_n / (cf_design * pc)
    throat_d = 2.0 * math.sqrt(throat_area / math.pi)
    exit_d = throat_d * math.sqrt(eps)

    pa_sl = atmosphere.pressure(0.0)
    cf_sl = lam * thrust_coefficient(gamma, eps, pe_over_pc, pa_sl / pc)
    pe = pe_over_pc * pc
    separation = pe < 0.4 * pa_sl        # Summerfield criterion

    _log.info(
        "Nozzle: Dt=%.1f mm, eps=%.2f, De=%.1f mm, pe=%.0f Pa "
        "(h_d=%.0f m), Cf=%.3f (SL %.3f)%s",
        throat_d * 1e3, eps, exit_d * 1e3, pe, design_altitude_m,
        cf_design, cf_sl, " SEPARATION RISK" if separation else "",
    )
    return NozzleDesign(
        throat_diameter_m=throat_d, exit_diameter_m=exit_d,
        expansion_ratio=eps, design_altitude_m=design_altitude_m,
        design_ambient_pa=pa_design, exit_pressure_pa=pe,
        cf_design=cf_design, cf_sea_level=cf_sl,
        separation_risk=separation,
    )
