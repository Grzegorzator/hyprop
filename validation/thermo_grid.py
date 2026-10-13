"""Stage 1, item 2: thermochemistry grid PE/N2O vs NASA CEA.

Grid: O/F x Pc, eps = 5 (prusak_v2 class nozzle). Both chemistry models:
shifting equilibrium and frozen-from-chamber (CEA n_frz = 1).

Reference: NASA CEA, official Python package ``cea`` (NASA Glenn, algorithm
of Gordon & McBride RP-1311), reactant ``(CH2)x(cr)``; its library dHf for
PE is replaced by HyProp's (Splitstone & Johnson 1974) through the chamber
enthalpy hc, so all codes solve the same problem.

Tolerance 0.5 %: Cantera uses GRI-Mech 3.0 thermo fits (valid to 3000 K,
extrapolated to ~3300 K) and a reduced C/H/N/O species set; RocketCEA is
the 1990s CEA Fortran with its own thermo.inp. Differences of a few 0.1 %
between equilibrium codes with different databases are expected.
"""

from __future__ import annotations

import csv
from typing import Dict, List

import numpy as np

from validation.common import INFO, REPO, Row

OF_GRID = (3.0, 4.0, 5.0, 6.0, 6.5, 7.0, 8.0, 9.0, 10.0)
PC_GRID_BAR = (10.0, 20.0, 35.0, 50.0)
EPS = 5.0
PA = 101325.0
G0 = 9.80665
TOL = 0.5
OUT_CSV = REPO / "docs" / "validation_data" / "thermo_grid_pe_n2o.csv"


def _nasa_cea_solver():
    import cea
    from hyprop.data import load_fuel

    reac = cea.Mixture(["(CH2)x(cr)", "N2O"])
    prod = cea.Mixture(["(CH2)x(cr)", "N2O"], products_from_reactants=True)
    t298 = np.array([298.15, 298.15])
    h_ox = reac.calc_property(cea.ENTHALPY, np.array([0.0, 1.0]), t298)
    h_fu = load_fuel("ldpe").enthalpy_of_formation.value / (2 * 14.02658e-3)
    return cea, reac, prod, h_ox, h_fu


def _reference(cea, reac, prod, h_ox, h_fu, of: float, pc_bar: float, frozen: bool) -> Dict[str, float]:
    solver = cea.RocketSolver(prod, reactants=reac)
    sol = cea.RocketSolution(solver)
    w = reac.of_ratio_to_weights(np.array([0.0, 1.0]), np.array([1.0, 0.0]), of)
    hc = (h_fu / (1 + of) + h_ox * of / (1 + of)) / cea.R
    kw = dict(supar=[EPS], hc=hc, iac=True)
    if frozen:
        kw["n_frz"] = 1
    solver.solve(sol, w, pc_bar, [pc_bar * 1e5 / PA], **kw)
    # points: 0 chamber, 1 throat, 2 pe = pa, 3 eps = EPS
    mw = sol.MW[0]
    return dict(
        Tc=sol.T[0], M=mw, gamma_s=sol.gamma_s[0],
        gamma_fr=sol.cp_fr[0] / (sol.cp_fr[0] - 8.314462618 / mw),
        cstar=sol.c_star[0], eps_opt=sol.ae_at[2],
        isp_opt=sol.Isp[2] / G0, isp_vac=sol.Isp_vacuum[3] / G0, Te=sol.T[3],
    )


def _hyprop(backend, of: float, pc_bar: float, eps_opt: float, frozen: bool) -> Dict[str, float]:
    pc = pc_bar * 1e5
    r = backend.query(of, pc, EPS)
    ro = backend.query(of, pc, float(eps_opt))
    exp = r.frozen if frozen else r.equilibrium
    exp_o = ro.frozen if frozen else ro.equilibrium
    c = r.chamber
    isp_vac = (exp.exhaust_velocity_m_s + exp.exit_state.pressure_pa * EPS * r.cstar_m_s / pc) / G0
    return dict(
        Tc=c.temperature_k, M=c.molar_mass_kg_mol * 1e3, gamma_s=c.gamma_eq, gamma_fr=c.gamma,
        cstar=r.cstar_m_s, isp_opt=exp_o.exhaust_velocity_m_s / G0, isp_vac=isp_vac,
        Te=exp.exit_state.temperature_k,
    )


QUANTITIES = {
    "Tc": "Tc", "M": "M komory", "gamma_fr": "γ zamrożone", "gamma_s": "γ_s",
    "cstar": "c*", "isp_vac": "Isp próżniowy (ε=5)", "isp_opt": "Isp optymalny (p_e = 1 atm)",
    "Te": "T wylotu (ε=5)",
}
CHAMBER_ONLY = ("Tc", "M", "gamma_fr", "gamma_s", "cstar")


def grid_rows() -> List[Row]:
    from hyprop.cea import get_backend

    try:
        cea, reac, prod, h_ox, h_fu = _nasa_cea_solver()
    except ImportError:
        return [Row("Siatka termochemii PE/N2O", "—", None, "", None,
                    comment="Brak pakietu NASA `cea` (pip install cea).")]
    ver = getattr(cea, "__version__", "?")
    src = (f"NASA CEA, pakiet `cea` {ver} (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; "
           f"pełna siatka: `docs/validation_data/{OUT_CSV.name}`")
    backends = {}
    for name in ("cantera", "rocketcea"):
        try:
            backends[name] = get_backend(name, fuel="ldpe", oxidizer="n2o")
        except Exception:
            pass

    from hyprop.data import load_fuel, load_oxidizer
    from hyprop.cea.cantera_backend import carbon_to_oxygen_ratio
    fuel, ox = load_fuel("ldpe"), load_oxidizer("n2o")

    records = []
    worst: Dict[tuple, tuple] = {}
    for mode in ("eq", "fr"):
        frozen = mode == "fr"
        for pc in PC_GRID_BAR:
            for of in OF_GRID:
                ref = _reference(cea, reac, prod, h_ox, h_fu, of, pc, frozen)
                sooting = carbon_to_oxygen_ratio(fuel, ox, of) >= 1.0
                for name, b in backends.items():
                    got = _hyprop(b, of, pc, ref["eps_opt"], frozen)
                    for q in QUANTITIES:
                        if frozen and q in CHAMBER_ONLY:
                            continue            # identical to the equilibrium chamber
                        dev = 100 * (got[q] / ref[q] - 1)
                        records.append(dict(mode=mode, pc_bar=pc, of=of, backend=name, quantity=q,
                                            reference=ref[q], hyprop=got[q], dev_pct=dev,
                                            c_over_o_ge_1=sooting))
                        key = (mode, name, q, sooting)
                        if key not in worst or abs(dev) > abs(worst[key][0]):
                            worst[key] = (dev, of, pc, ref[q], got[q])

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(records[0]))
        wr.writeheader()
        for rec in records:
            wr.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in rec.items()})

    rows: List[Row] = []
    for (mode, name, q, sooting), (dev, of, pc, ref, got) in sorted(worst.items()):
        label = "równowaga" if mode == "eq" else "zamrożony od komory"
        region = "C/O ≥ 1 (sadza)" if sooting else "C/O < 1"
        sooting_cantera = sooting and name == "cantera"
        rows.append(Row(f"max odchyłka {QUANTITIES[q]} – {name} ({label})",
                        f"{region}; siatka O/F {OF_GRID[0]:g}–{OF_GRID[-1]:g} × Pc "
                        f"{PC_GRID_BAR[0]:g}–{PC_GRID_BAR[-1]:g} bar; najgorszy punkt O/F {of:g}, {pc:g} bar",
                        float(ref), src, float(got), tol=None if sooting_cantera else TOL,
                        status=INFO if sooting_cantera else "",
                        comment=("Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol "
                                 "węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1."
                                 if sooting_cantera else "")))
    n = len(OF_GRID) * len(PC_GRID_BAR)
    rows.append(Row("Liczba punktów siatki", "PE/N2O", None, "", float(n), status=INFO,
                    comment=f"{n} punktów × 2 modele chemii × {len(backends)} backendy."))
    return rows


def all_rows():
    return grid_rows()
