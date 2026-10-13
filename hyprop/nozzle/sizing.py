"""Nozzle sizing on a Representative Operating Point (stage E8).

Inputs come exclusively from an ROP operating point (ARCHITECTURE.md
principle 8), by default the impulse-weighted point:

* throat: At = F / (eta*Cd*Cf_i,lambda * Pc), lambda on the momentum
  term of Cf only                                      (Sutton Eqs. 3-31, 3-34)
* expansion: eps such that pe = pa(design altitude)     (optimum, Eq. 3-25),
  from the CEA shifting-equilibrium expansion when a backend is given
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
from typing import TYPE_CHECKING

from scipy.optimize import brentq

from hyprop.core.logging import get_logger
from hyprop.nozzle.losses import divergence_efficiency
from hyprop.oppoints.design_points import OperatingPoint
from hyprop.performance.metrics import ideal_effective_exhaust_velocity
from hyprop.physics import atmosphere
from hyprop.physics.compressible import (
    exit_pressure_ratio,
    optimum_expansion_ratio,
    thrust_coefficient,
)

if TYPE_CHECKING:
    from hyprop.cea.backend import ThermochemistryBackend

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
    cf_design: float  #: Cf at design point (with divergence)
    cf_sea_level: float  #: Cf at lift-off (overexpansion check)
    separation_risk: bool  #: pe < 0.4*pa at sea level (Summerfield)


def design_altitude_from_apogee(apogee_m: float) -> float:
    """Heuristic h_design = apogee/3 (to be replaced by trajectory data)."""
    return DESIGN_ALTITUDE_FRACTION * apogee_m


def size_nozzle(
    point: OperatingPoint,
    thrust_target_n: float,
    design_altitude_m: float,
    half_angle_deg: float = 15.0,
    efficiency: float = 1.0,
    discharge_coefficient: float = 1.0,
    cea: ThermochemistryBackend | None = None,
) -> NozzleDesign:
    """Size throat and expansion for a target thrust at the ROP point.

    Parameters
    ----------
    point:
        ROP operating point providing ``pc`` [Pa], ``of`` [-] and
        ``gamma`` [-] (frozen cp/cv; impulse-weighted point recommended).
    thrust_target_n:
        Thrust to deliver at the design point [N].
    design_altitude_m:
        Altitude of pressure adaptation (pe = pa there) [m].
    efficiency, discharge_coefficient:
        Same meaning as ``nozzle.efficiency`` / ``nozzle.discharge_coefficient``
        in the transient, so that the sized throat delivers the target
        thrust at the design Pc: F = eta*Cd*Cf_i,lambda*Pc*At (the c*
        efficiency cancels at fixed Pc, Sutton 9th ed. Eqs. 3-31, 3-40).
    cea:
        Thermochemistry backend. When given (and ``point`` has ``of``),
        eps and Cf_i come from the shifting-equilibrium expansion itself
        (eps such that CEA p_e = p_a). Otherwise the ideal-gas relations
        with constant frozen gamma are used, which misplace eps_opt by
        ~3 % (frozen gamma) to ~10 % (equilibrium gamma) for hybrid
        exhaust at 35 bar (docs/VALIDATION.md).
    """
    pc = point["pc"]
    pa_design = atmosphere.pressure(design_altitude_m)
    pa_sl = atmosphere.pressure(0.0)
    lam = divergence_efficiency(half_angle_deg)
    use_cea = cea is not None and "of" in point.values

    if use_cea and cea is not None:
        of = point["of"]

        def pe_of(eps_try: float) -> float:
            return cea.query(of, pc, eps_try).equilibrium.exit_state.pressure_pa

        eps = brentq(lambda e: pe_of(e) - pa_design, 1.2, 80.0, xtol=1e-5)
        r = cea.query(of, pc, eps)
        pe = r.equilibrium.exit_state.pressure_pa

        def cf_ideal(pa: float) -> float:
            c_i = ideal_effective_exhaust_velocity(
                r.equilibrium.exhaust_velocity_m_s, pe, pa, eps, r.cstar_m_s, pc, lam
            )
            return c_i / r.cstar_m_s

        cf_i_design, cf_i_sl = cf_ideal(pa_design), cf_ideal(pa_sl)
    else:
        gamma = point["gamma"]
        eps = optimum_expansion_ratio(pc / pa_design, gamma)
        pe_over_pc = exit_pressure_ratio(eps, gamma)
        pe = pe_over_pc * pc
        cf_momentum = thrust_coefficient(gamma, eps, pe_over_pc, pe_over_pc)

        def cf_ideal(pa: float) -> float:
            return lam * cf_momentum + (pe_over_pc - pa / pc) * eps

        cf_i_design, cf_i_sl = cf_ideal(pa_design), cf_ideal(pa_sl)

    # lambda is already inside cf_i (momentum term only, Sutton Eq. 3-34)
    cf_design = efficiency * cf_i_design
    cf_sl = efficiency * cf_i_sl
    throat_area = thrust_target_n / (cf_design * discharge_coefficient * pc)
    throat_d = 2.0 * math.sqrt(throat_area / math.pi)
    exit_d = throat_d * math.sqrt(eps)
    separation = pe < 0.4 * pa_sl  # Summerfield criterion

    _log.info(
        "Nozzle (%s): Dt=%.2f mm, eps=%.3f, De=%.1f mm, pe=%.0f Pa "
        "(h_d=%.0f m), Cf=%.3f (SL %.3f)%s",
        "CEA" if use_cea else "ideal gas",
        throat_d * 1e3,
        eps,
        exit_d * 1e3,
        pe,
        design_altitude_m,
        cf_design,
        cf_sl,
        " SEPARATION RISK" if separation else "",
    )
    return NozzleDesign(
        throat_diameter_m=throat_d,
        exit_diameter_m=exit_d,
        expansion_ratio=eps,
        design_altitude_m=design_altitude_m,
        design_ambient_pa=pa_design,
        exit_pressure_pa=pe,
        cf_design=cf_design,
        cf_sea_level=cf_sl,
        separation_risk=separation,
    )
