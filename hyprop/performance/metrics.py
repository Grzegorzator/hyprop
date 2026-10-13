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


def ideal_effective_exhaust_velocity(
    exhaust_velocity_m_s: float,
    exit_pressure_pa: float,
    ambient_pressure_pa: float,
    expansion_ratio: float,
    cstar_ideal_m_s: float,
    pc_pa: float,
    divergence: float = 1.0,
) -> float:
    """Ideal effective exhaust velocity c_i [m/s] at the operating ambient.

    c_i = lambda * v_e + (p_e - p_a) * A_e / mdot_i,
    A_e/mdot_i = eps*c*_i/p_c (ideal mass flow mdot_i = p_c*A_t/c*_i;
    Sutton & Biblarz 9th ed., Eqs. 2-16, 3-24, 3-32: c = c* C_F).
    The conical divergence factor ``lambda`` multiplies the momentum term
    only, not the pressure term (Sutton Eq. 3-34 and the note below it).

    Args:
        exhaust_velocity_m_s: Ideal exit velocity v_e from the
            thermochemistry backend [m/s].
        exit_pressure_pa: Exit static pressure p_e [Pa].
        ambient_pressure_pa: Ambient pressure p_a [Pa].
        expansion_ratio: Nozzle area ratio eps = A_e/A_t [-].
        cstar_ideal_m_s: Ideal characteristic velocity c*_i [m/s].
        pc_pa: Chamber pressure p_c [Pa].
        divergence: Conical divergence factor lambda [-] (1 = no loss).

    Returns:
        Ideal effective exhaust velocity c_i [m/s].
    """
    return (
        divergence * exhaust_velocity_m_s
        + (exit_pressure_pa - ambient_pressure_pa) * expansion_ratio * cstar_ideal_m_s / pc_pa
    )


def delivered_thrust(
    mdot_kg_s: float,
    c_ideal_m_s: float,
    zeta_cstar: float,
    zeta_cf: float,
) -> float:
    """Delivered thrust [N] from correction factors (Sutton convention).

    F_a = mdot_a * c_a,  c_a = zeta_v * c_i,  zeta_v = zeta_c* * zeta_CF
    (Sutton & Biblarz, Rocket Propulsion Elements, 9th ed., Sec. 3.5
    "Performance Correction Factors", Eqs. 3-40 and 3-41; worked in
    Example 3-7). zeta_c* is the combustion (c*) efficiency, zeta_CF the
    nozzle (thrust-coefficient) efficiency including divergence.

    Args:
        mdot_kg_s: Actual propellant mass flow [kg/s].
        c_ideal_m_s: Ideal effective exhaust velocity c_i [m/s], see
            :func:`ideal_effective_exhaust_velocity`.
        zeta_cstar: Combustion (c*) efficiency [-].
        zeta_cf: Nozzle (thrust-coefficient) efficiency [-] other than the
            divergence already contained in ``c_ideal_m_s``.

    Returns:
        Delivered thrust [N].
    """
    return zeta_cstar * zeta_cf * mdot_kg_s * c_ideal_m_s


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


def thrust_coefficient_delivered(thrust_n: float, pc_pa: float, throat_area_m2: float) -> float:
    """Delivered thrust coefficient Cf [-] = F/(pc*At)."""
    if pc_pa <= 0.0 or throat_area_m2 <= 0.0:
        raise ValueError("pc and At must be positive.")
    return thrust_n / (pc_pa * throat_area_m2)


def efficiency(delivered: float, ideal: float) -> float:
    """Generic efficiency ratio [-] with sanity check."""
    if ideal <= 0.0:
        raise ValueError("Ideal value must be positive.")
    return delivered / ideal
