"""Quasi-1D isentropic compressible flow of a calorically perfect gas.

The nozzle-flow backbone of HyProp. All relations assume steady,
adiabatic, isentropic flow of an ideal gas with constant ratio of
specific heats ``gamma`` (frozen properties between stations). Real-gas
and shifting-equilibrium effects enter through the CEA backends, which
provide effective ``gamma`` and molar mass per station.

Sources
-------
* Sutton, G. P., Biblarz, O., *Rocket Propulsion Elements*, 9th ed.,
  Wiley 2017, Ch. 3 (ideal rocket, nozzle theory).
* Anderson, J. D., *Modern Compressible Flow*, 3rd ed., Ch. 3-5.
* NASA RP-1311 (CEA), Part I - analysis equations.

Notation: ``mach`` [-], ``gamma`` [-], stagnation state ``0`` (chamber),
throat ``*``. All pressures/temperatures are static unless noted.
"""

from __future__ import annotations

import math

from scipy.optimize import brentq

from hyprop.core.exceptions import ConvergenceError

_GAMMA_MIN = 1.0001
_GAMMA_MAX = 5.0/3.0 + 0.2  # generous upper sanity bound


def _check_gamma(gamma: float) -> None:
    if not (_GAMMA_MIN <= gamma <= _GAMMA_MAX):
        raise ValueError(f"gamma={gamma} outside sane range "
                         f"[{_GAMMA_MIN}, {_GAMMA_MAX}].")


def temperature_ratio(mach: float, gamma: float) -> float:
    """Static-to-stagnation temperature ratio ``T/T0``.

    T/T0 = [1 + (gamma-1)/2 * M^2]^-1        (Anderson Eq. 3.28)
    """
    _check_gamma(gamma)
    return 1.0 / (1.0 + 0.5 * (gamma - 1.0) * mach * mach)


def pressure_ratio(mach: float, gamma: float) -> float:
    """Static-to-stagnation pressure ratio ``p/p0``.

    p/p0 = (T/T0)^(gamma/(gamma-1))          (Anderson Eq. 3.30)
    """
    return temperature_ratio(mach, gamma) ** (gamma / (gamma - 1.0))


def density_ratio(mach: float, gamma: float) -> float:
    """Static-to-stagnation density ratio ``rho/rho0``.

    rho/rho0 = (T/T0)^(1/(gamma-1))          (Anderson Eq. 3.31)
    """
    return temperature_ratio(mach, gamma) ** (1.0 / (gamma - 1.0))


def critical_pressure_ratio(gamma: float) -> float:
    """Throat (M=1) to stagnation pressure ratio ``p*/p0``.

    p*/p0 = (2/(gamma+1))^(gamma/(gamma-1))  (Sutton Eq. 3-20)
    For gamma=1.4: 0.5283.
    """
    _check_gamma(gamma)
    return (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))


def area_ratio(mach: float, gamma: float) -> float:
    """Local-to-throat area ratio ``A/A*`` for isentropic flow.

    A/A* = (1/M) * [ (2/(gamma+1)) (1 + (gamma-1)/2 M^2) ]^((gamma+1)/(2(gamma-1)))
    (Anderson Eq. 5.20; Sutton Eq. 3-14)
    """
    _check_gamma(gamma)
    if mach <= 0.0:
        raise ValueError("mach must be positive.")
    exponent = (gamma + 1.0) / (2.0 * (gamma - 1.0))
    term = (2.0 / (gamma + 1.0)) * (1.0 + 0.5 * (gamma - 1.0) * mach * mach)
    return term ** exponent / mach


def mach_from_area_ratio(
    ratio: float, gamma: float, branch: str = "supersonic"
) -> float:
    """Invert ``A/A*`` for Mach number on the chosen branch.

    Parameters
    ----------
    ratio:
        Area ratio A/A* >= 1.
    branch:
        ``"supersonic"`` (diverging part) or ``"subsonic"`` (converging).
    """
    _check_gamma(gamma)
    if ratio < 1.0:
        raise ValueError("Area ratio must be >= 1.")
    if ratio == 1.0:
        return 1.0
    if branch == "supersonic":
        lo, hi = 1.0 + 1e-12, 100.0
    elif branch == "subsonic":
        lo, hi = 1e-8, 1.0 - 1e-12
    else:
        raise ValueError("branch must be 'supersonic' or 'subsonic'.")
    try:
        return brentq(lambda m: area_ratio(m, gamma) - ratio, lo, hi,
                      xtol=1e-12, rtol=1e-12)
    except ValueError as exc:
        raise ConvergenceError(
            f"mach_from_area_ratio failed (ratio={ratio}, gamma={gamma})."
        ) from exc


def mach_from_pressure_ratio(p_over_p0: float, gamma: float) -> float:
    """Mach number from static-to-stagnation pressure ratio.

    M = sqrt( 2/(gamma-1) * [ (p/p0)^(-(gamma-1)/gamma) - 1 ] )
    (inverse of Anderson Eq. 3.30)
    """
    _check_gamma(gamma)
    if not (0.0 < p_over_p0 <= 1.0):
        raise ValueError("p/p0 must be in (0, 1].")
    return math.sqrt(
        2.0 / (gamma - 1.0) * (p_over_p0 ** (-(gamma - 1.0) / gamma) - 1.0)
    )


def vandenkerckhove(gamma: float) -> float:
    """Vandenkerckhove function Gamma(gamma).

    Gamma = sqrt(gamma) * (2/(gamma+1))^((gamma+1)/(2(gamma-1)))
    Appears in choked flow and c* (Sutton Eq. 3-24 group).
    """
    _check_gamma(gamma)
    return math.sqrt(gamma) * (2.0 / (gamma + 1.0)) ** (
        (gamma + 1.0) / (2.0 * (gamma - 1.0))
    )


def choked_mass_flux(p0: float, t0: float, gamma: float, r_specific: float) -> float:
    """Choked (sonic-throat) mass flux ``mdot/A*`` [kg/(m^2*s)].

    mdot/A* = p0 * Gamma(gamma) / sqrt(R * T0)   (Sutton Eq. 3-24)

    Parameters: stagnation pressure ``p0`` [Pa], stagnation temperature
    ``t0`` [K], specific gas constant ``r_specific`` [J/(kg*K)].
    """
    if p0 <= 0 or t0 <= 0 or r_specific <= 0:
        raise ValueError("p0, t0 and r_specific must be positive.")
    return p0 * vandenkerckhove(gamma) / math.sqrt(r_specific * t0)


def cstar_ideal(gamma: float, r_specific: float, t0: float) -> float:
    """Ideal characteristic velocity c* [m/s].

    c* = p0 * A* / mdot = sqrt(R*T0) / Gamma(gamma)   (Sutton Eq. 3-32)
    """
    return math.sqrt(r_specific * t0) / vandenkerckhove(gamma)


def exit_pressure_ratio(eps: float, gamma: float) -> float:
    """Exit static pressure ratio ``pe/p0`` for area ratio ``eps`` (supersonic).

    Solves A/A*(Me) = eps, then pe/p0 = f(Me).
    """
    mach_exit = mach_from_area_ratio(eps, gamma, "supersonic")
    return pressure_ratio(mach_exit, gamma)


def optimum_expansion_ratio(p0_over_pe: float, gamma: float) -> float:
    """Area ratio ``eps`` that expands from ``p0`` to ``pe`` (Pe = Pa optimum).

    Inverse of :func:`exit_pressure_ratio`; Sutton Eq. 3-25 combination.
    """
    if p0_over_pe <= 1.0:
        raise ValueError("p0/pe must exceed 1 for a supersonic nozzle.")
    mach_exit = mach_from_pressure_ratio(1.0 / p0_over_pe, gamma)
    return area_ratio(mach_exit, gamma)


def thrust_coefficient(
    gamma: float, eps: float, pe_over_p0: float, pa_over_p0: float
) -> float:
    """Thrust coefficient ``Cf`` of an ideal nozzle (Sutton Eq. 3-30).

    Cf = sqrt[ 2*gamma^2/(gamma-1) * (2/(gamma+1))^((gamma+1)/(gamma-1))
               * (1 - (pe/p0)^((gamma-1)/gamma)) ]
         + (pe/p0 - pa/p0) * eps

    ``F = Cf * p0 * A*`` with stagnation (chamber) pressure ``p0``.
    """
    _check_gamma(gamma)
    if not (0.0 < pe_over_p0 < 1.0):
        raise ValueError("pe/p0 must be in (0, 1).")
    momentum = math.sqrt(
        2.0 * gamma * gamma / (gamma - 1.0)
        * (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (gamma - 1.0))
        * (1.0 - pe_over_p0 ** ((gamma - 1.0) / gamma))
    )
    return momentum + (pe_over_p0 - pa_over_p0) * eps


def exhaust_velocity_ideal(
    gamma: float, r_specific: float, t0: float, pe_over_p0: float
) -> float:
    """Ideal exhaust velocity ``ve`` [m/s] for expansion to ``pe/p0``.

    ve = sqrt( 2*gamma/(gamma-1) * R * T0 * [1 - (pe/p0)^((gamma-1)/gamma)] )
    (Sutton Eq. 3-15/3-16)
    """
    _check_gamma(gamma)
    if not (0.0 < pe_over_p0 < 1.0):
        raise ValueError("pe/p0 must be in (0, 1).")
    return math.sqrt(
        2.0 * gamma / (gamma - 1.0) * r_specific * t0
        * (1.0 - pe_over_p0 ** ((gamma - 1.0) / gamma))
    )
