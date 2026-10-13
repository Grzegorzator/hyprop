"""Stage 1, item 9: dimensional analysis of the numerical core.

HyProp's core works on plain SI floats; Pint is used only at the
configuration boundary (``hyprop.core.units.to_si``: ``.to(unit).magnitude``
- the single place a magnitude leaves Pint). The audit below re-evaluates
every central relation of physics/, tank/, injector/, regression/ and the
solver with Pint quantities carrying units, converts the result to the
SI unit the code assumes, and compares it with the plain-float function.
A unit slip in the code (bar vs Pa, mm vs m, kJ vs J, g vs kg) would show
up as a factor of 10^n. Reference = the textbook equation evaluated by
Pint (sources per row); tolerance 1e-6 %.
"""

from __future__ import annotations

import math
from typing import List

from validation.common import Row

S = "Sutton & Biblarz, Rocket Propulsion Elements, 9th ed."
WAX = "Waxman et al., NASA NTRS 20190001326, Eqs. (2), (9)"
TOL = 1e-6


def all_rows() -> List[Row]:
    from hyprop.core.units import Q_
    from hyprop.physics import compressible as cf
    from hyprop.injector.spi import SPIInjector
    from hyprop.regression.power_law import PowerLawRegression
    from hyprop.performance.metrics import ideal_effective_exhaust_velocity, delivered_thrust
    from hyprop.tank.base import FluidState

    rows: List[Row] = []

    def add(name, formula_src, pint_value, unit, code_value, comment=""):
        ref = float(pint_value.to(unit).magnitude)
        rows.append(Row(f"[{unit}] {name}", "analiza wymiarowa (Pint)", ref, formula_src,
                        float(code_value), tol=TOL, comment=comment))

    # --- compressible flow -----------------------------------------------
    g, r, t0, p0 = 1.24, Q_(320.0, "J/(kg*K)"), Q_(3300.0, "K"), Q_(32.0, "bar")
    gam = math.sqrt(g) * (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))
    add("c* = sqrt(R T0)/Γ", f"{S}, Eq. 3-32", (r * t0) ** 0.5 / gam, "m/s",
        cf.cstar_ideal(g, 320.0, 3300.0))
    add("ṁ/A* = p0 Γ / sqrt(R T0)", f"{S}, Eq. 3-24", p0 * gam / (r * t0) ** 0.5, "kg/(m^2*s)",
        cf.choked_mass_flux(32e5, 3300.0, g, 320.0))
    pr = 0.03
    ve = (2 * g / (g - 1) * r * t0 * (1 - pr ** ((g - 1) / g))) ** 0.5
    add("v_e (izentropowe)", f"{S}, Eq. 3-16", ve, "m/s", cf.exhaust_velocity_ideal(g, 320.0, 3300.0, pr))

    # --- thrust (Sutton correction factors) --------------------------------
    v, pe, pa, eps, cstar, pc = Q_(2400.0, "m/s"), Q_(0.9, "bar"), Q_(1.01325, "bar"), 5.0, \
        Q_(1600.0, "m/s"), Q_(32.0, "bar")
    lam = 0.983
    c_i = lam * v + (pe - pa) * eps * cstar / pc
    add("c_i = λ v_e + (p_e − p_a) ε c*/p_c", f"{S}, Eqs. 2-16, 3-32, 3-34", c_i, "m/s",
        ideal_effective_exhaust_velocity(2400.0, 0.9e5, 101325.0, eps, 1600.0, 32e5, lam))
    mdot = Q_(2.5, "kg/s")
    add("F = η_c* η_noz ṁ c_i", f"{S}, Eqs. 3-40, 3-41", 0.95 * 0.97 * mdot * c_i, "N",
        delivered_thrust(2.5, float(c_i.to("m/s").magnitude), 0.95, 0.97))
    cd_noz, at = 0.98, Q_(math.pi / 4 * 16.0 ** 2, "mm^2")
    pc_bal = mdot * 0.95 * cstar / (cd_noz * at)
    add("p_c = ṁ η_c* c* / (Cd A_t) (bilans w solverze)", f"{S}, Eq. 2-17 / 3-32", pc_bal, "Pa",
        2.5 * 0.95 * 1600.0 / (cd_noz * math.pi / 4 * 0.016 ** 2),
        comment="Wyrażenie przepisane z simulation/solver.py (chamber_balance).")

    # --- injector SPI --------------------------------------------------------
    rho, dp, a_or = Q_(780.0, "kg/m^3"), Q_(17.0, "bar"), Q_(math.pi / 4 * 2.0 ** 2, "mm^2")
    fluid = FluidState(50e5, 293.15, 780.0, 50e5, "liquid")
    spi = SPIInjector(0.6, 5, math.pi / 4 * 0.002 ** 2)
    add("ṁ_SPI = Cd N A sqrt(2 ρ ΔP)", f"{WAX} (Eq. 2)", 0.6 * 5 * a_or * (2 * rho * dp) ** 0.5, "kg/s",
        spi.mdot(fluid, 33e5))

    # --- regression power law -----------------------------------------------
    # HRAP/literature: rdot[mm/s] = a_mm * G[kg/m^2 s]^n  ->  a_SI = a_mm * 1e-3
    a_mm, n, g_flux = 0.104, 0.352, 250.0
    rdot_ref = Q_(a_mm * g_flux ** n, "mm/s")
    law = PowerLawRegression(a=1.04e-4, n=n, m=0.0, flux_basis="oxidizer")
    add("ṙ = a G^n (a z mm/s → SI)", "HRAP propellant_template.m (ṙ mm/s, G kg/m²s)", rdot_ref, "m/s",
        law.rdot(g_flux, 0.5),
        comment="Wymiar a zależy od n: [a] = m^(1+2n) kg^(−n) s^(n−1); baza przechowuje a w tej konwencji SI.")
    rho_f, ab = Q_(920.0, "kg/m^3"), Q_(math.pi * 30.0 * 450.0, "mm^2")
    add("ṁ_f = ρ_f A_b ṙ", "bilans masy paliwa (HRAP Eq. 12)", rho_f * ab * rdot_ref, "kg/s",
        920.0 * math.pi * 0.030 * 0.450 * law.rdot(g_flux, 0.5))

    # --- tank energy balance ---------------------------------------------------
    hv, dmv, m_l, cp = Q_(180.0, "kJ/kg"), Q_(2.0, "g"), Q_(2.5, "kg"), Q_(2.4, "kJ/(kg*K)")
    add("ΔT = h_lv Δm_v / (m_l c_p)", "bilans energii zbiornika (HRAP r. II; tank/equilibrium_blowdown.py)",
        hv * dmv / (m_l * cp), "K", 180e3 * 0.002 / (2.5 * 2400.0))
    return rows
