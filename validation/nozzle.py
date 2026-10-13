"""Stage 1, item 3: ideal nozzle flow vs worked examples of Sutton & Biblarz.

Source: G. P. Sutton, O. Biblarz, *Rocket Propulsion Elements*, 9th ed.,
Wiley 2017, Chapter 3 (Examples 3-1 to 3-4, 3-7). Values that Sutton
reads off a chart (Figs. 3-6/3-7) get a 2 % tolerance; values computed by
Sutton from the equations get the tolerance of the digits he prints.

The CEA-coupled nozzle (shifting equilibrium) is validated in item 2; this
item checks the constant-gamma relations in ``hyprop.physics.compressible``
used by the ideal-gas nozzle sizing path and by the tests.
"""

from __future__ import annotations

from typing import List

from hyprop.physics import compressible as cf
from validation.common import Row

S = "Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017)"
ATM = 101325.0


def all_rows() -> List[Row]:
    rows: List[Row] = []

    # Example 3-1: k=1.3, Me=2.52, p_exit=0.1013 MPa -> p0=1.84 MPa, A2/At=3.02
    k = 1.3
    p0 = 0.1013e6 / cf.pressure_ratio(2.52, k)
    rows += [
        Row("p0 dla M_e = 2.52", "k=1.3, p_e = 0.1013 MPa", 1.84, f"{S}, Ex. 3-1", p0 / 1e6,
            tol=0.3, unit="MPa"),
        Row("A_e/A_t dla M_e = 2.52", "k=1.3", 3.02, f"{S}, Ex. 3-1", cf.area_ratio(2.52, k), tol=0.3),
    ]

    # Example 3-2: k=1.3, R=345.7, T1=2222 K, p1=2.068 MPa -> p3=0.1013 MPa: v2=1827 m/s
    v2 = cf.exhaust_velocity_ideal(1.3, 345.7, 2222.0, 0.1013 / 2.068)
    rows.append(Row("v_e (rozprężanie optymalne)", "k=1.3, R=345.7, T1=2222 K, p1/p2=2.068/0.1013",
                    1827.0, f"{S}, Ex. 3-2", v2, tol=0.05, unit="m/s"))

    # Example 3-3: k=1.2, R=360, T1=2800 K, p1=2.039 MPa, p2=2.549 kPa, F=5000 N
    k, r, t1, p1, p2 = 1.2, 360.0, 2800.0, 2.039e6, 2.549e3
    eps = cf.optimum_expansion_ratio(p1 / p2, k)
    v2 = cf.exhaust_velocity_ideal(k, r, t1, p2 / p1)
    mdot = 5000.0 / v2
    at = mdot / cf.choked_mass_flux(p1, t1, k, r)
    case = "k=1.2, R=360, T1=2800 K, p1=2.039 MPa, p2=2.549 kPa, F=5000 N"
    rows += [
        Row("A_e/A_t optymalne", case, 1 / 1.67e-2, f"{S}, Ex. 3-3 (At/A2 = 1.67e-2)", eps, tol=0.6,
            comment="Sutton zaokrągla At/A2 do 3 cyfr (1.67e-2); stąd tolerancja 0.6 %."),
        Row("T gardzieli", case, 2545.0, f"{S}, Ex. 3-3", t1 * cf.temperature_ratio(1.0, k), tol=0.05, unit="K"),
        Row("v_e", case, 2851.0, f"{S}, Ex. 3-3", v2, tol=0.05, unit="m/s"),
        Row("A_t", case, 13.32, f"{S}, Ex. 3-3", at * 1e4, tol=0.1, unit="cm²"),
    ]

    # Example 3-4: k=1.3, p1=20 atm, eps=6: p2/p1=0.0198; CF(SL)=1.33, CF(10 km, p3=0.26151 atm)=1.56
    k, eps = 1.3, 6.0
    pe = cf.exit_pressure_ratio(eps, k)
    rows.append(Row("p_e/p_1 dla ε = 6", "k=1.3", 0.0198, f"{S}, Ex. 3-4 (Eq. 3-25)", pe, tol=0.3))
    for label, pa_atm, ref in (("C_F, poziom morza (praca poza p. projektowym)", 1.0, 1.33),
                               ("C_F, 10 km (p3 = 0.26151 atm)", 0.26151, 1.56)):
        got = cf.thrust_coefficient(k, eps, pe, pa_atm / 20.0)
        rows.append(Row(label, "k=1.3, p1=20 atm, ε=6", ref, f"{S}, Ex. 3-4 (odczyt z Fig. 3-7)", got, tol=2.0,
                        comment="Wartość referencyjna odczytana z wykresu – tolerancja 2 %."))
    got_vac = cf.thrust_coefficient(k, eps, pe, 0.0)
    rows.append(Row("C_F próżniowy", "k=1.3, p1=20 atm, ε=6", 1.63, f"{S}, Ex. 3-4 (Fig. 3-7)", got_vac, tol=2.0))

    # Example 3-7: k=1.23, p1/p2=20.4 optimum -> (CF)i = 1.405
    k = 1.23
    eps = cf.optimum_expansion_ratio(20.4, k)
    pe = 1 / 20.4
    rows.append(Row("(C_F)i optymalne", "k=1.23, p1/p2 = 20.4", 1.405, f"{S}, Ex. 3-7 (Eq. 3-30)",
                    cf.thrust_coefficient(k, eps, pe, pe), tol=0.05))
    return rows
