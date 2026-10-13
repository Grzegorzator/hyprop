"""Stage 1, item 1: reproduce every quantitative claim of README.md.

Reference values are either (a) the README claim itself, checked against a
fresh HyProp run, or (b) the primary data the claim was derived from (HRAP
output CSV, HRAP .mat configs, the user's 07_cantera script, CoolProp).
External files are located through environment variables (see
validation/README.md); rows whose reference file is missing become TODO.
"""

from __future__ import annotations

import dataclasses
import math
from unittest import mock

import numpy as np

from validation.common import FAIL, INFO, REPO, Row, external, load_module, sha256

_trapz = next(getattr(np, n) for n in ("trapezoid", "trapz") if hasattr(np, n))
README = "README.md (v0.2, sekcje Validation/Examples)"


def _load_example(name: str):
    # examples guard main() -> importing them has no side effects
    return load_module(name, REPO / "examples" / f"{name}.py")


# ----------------------------------------------------------------- HRAP E6
def hrap_benchmark() -> list[Row]:
    import pandas as pd

    import hyprop.api as api
    from hyprop.core.config import EngineConfig

    hrap_dir = external("HYPROP_HRAP_DIR")
    csv = hrap_dir / "output" / "prusakv2_HRAP_output.csv" if hrap_dir else None
    rows: list[Row] = []
    if hrap_dir is None or csv is None or not csv.exists():
        return [
            Row(
                "HRAP benchmark",
                "prusak_v2",
                None,
                "",
                None,
                comment="Brak pliku HRAP CSV (ustaw HYPROP_HRAP_DIR).",
            )
        ]
    src = (
        f"HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 {sha256(csv)[:12]}…"
    )

    bench = _load_example("benchmark_prusak_v2")
    cfg = EngineConfig.from_dict(bench.CFG)
    res = api.run(cfg)
    df = res.history.to_dataframe()
    ref = pd.read_csv(csv)
    ref.columns = [c.strip() for c in ref.columns]
    lro = res.event_time("liquid_runout")
    assert lro is not None, "prusak_v2 must reach liquid run-out"
    tg = np.arange(0.2, min(lro, 7.0), 0.05)  # identical window to benchmark script

    def dev(col_h, col_r, scale=1.0):
        a = np.interp(tg, df.t, df[col_h]) / scale
        b = np.interp(tg, ref["Time (s)"], ref[col_r])
        return float(100 * np.mean(np.abs(a - b)) / np.mean(np.abs(b)))

    claims = [
        ("Pc", "pc", "Combustion Chamber Pressure (kPa)", 1e3, 1.4),
        ("p_tank", "p_tank", "Oxidizer Tank Pressure (kPa)", 1e3, 0.5),
        ("O/F", "of", "Oxidizer to Fuel Ratio", 1.0, 0.8),
        ("Ciąg F", "thrust", "Thrust (N)", 1.0, 0.6),
    ]
    for label, ch, cr, sc, claim in claims:
        rows.append(
            Row(
                f"Średnia odchyłka {label} HyProp–HRAP [%]",
                "prusak_v2, faza ciekła 0.2–7.0 s",
                claim,
                f"{README}; {src}",
                dev(ch, cr, sc),
                tol=0.05,
                dev_kind="abs",
                unit="pp",
                comment="Odtworzenie deklaracji README (tolerancja = zaokrąglenie).",
            )
        )
    rows.append(
        Row(
            "LRO HyProp",
            "prusak_v2",
            7.16,
            README,
            round(lro, 4),
            tol=0.005,
            dev_kind="abs",
            unit="s",
        )
    )
    # HRAP run-out from its own data: the step where mdot_ox collapses
    t = ref["Time (s)"].to_numpy()
    m = ref["Oxidizer Mass Flow Rate (kg/s)"].to_numpy()
    i = int(np.argmin(np.diff(m)))
    lro_hrap = float(t[i + 1])
    rows.append(
        Row(
            "LRO HRAP (z danych HRAP)",
            "prusak_v2",
            6.955,
            README,
            lro_hrap,
            tol=0.0005,
            dev_kind="abs",
            unit="s",
            comment=(
                f"Skok ṁ_ox {m[i]:.3f}→{m[i + 1]:.3f} kg/s w CSV. (v0.1 README podawało "
                "błędnie ~7.5 s.)"
            ),
        )
    )
    rows.append(
        Row(
            "LRO HyProp vs HRAP",
            "prusak_v2",
            lro_hrap,
            src,
            round(lro, 4),
            comment="Odchyłka faktyczna, bez kryterium (do oceny w pkt 5).",
            status=INFO,
        )
    )

    # Thrust-gap decomposition: same run, frozen instead of shifting exit.
    import hyprop.cea.table as tb

    q0 = tb.TabulatedBackend.query

    def frozen_exit(s, of, pc, eps):
        r = q0(s, of, pc, eps)
        return dataclasses.replace(r, equilibrium=r.frozen)

    with mock.patch.object(tb.TabulatedBackend, "query", frozen_exit):
        dff = api.run(cfg).history.to_dataframe()
    a = np.interp(tg, dff.t, dff.thrust)
    b = np.interp(tg, ref["Time (s)"], ref["Thrust (N)"])
    rows.append(
        Row(
            "Średnia odchyłka F, wylot zamrożony [%]",
            "prusak_v2 (diagnostyka)",
            None,
            "",
            float(100 * np.mean(np.abs(a - b)) / np.mean(b)),
            status=INFO,
            comment="Ta sama symulacja z v_e zamrożonym zamiast równowagowego (diagnostyka). "
            "HRAP nie stosuje η_c* do ciągu, a liczy v_e ze stałym γ; zgodność F jest "
            "częściowo przypadkowa (efekty o przeciwnych znakach).",
        )
    )

    # regression coefficients: HRAP .mat vs HyProp database
    from scipy.io import loadmat

    from hyprop.data import load_fuel

    for fuel, mat in (("hdpe", "HDPE"), ("paraffin", "Paraffin"), ("htpb", "HTPB")):
        p = hrap_dir / "propellant_configs" / f"{mat}.mat"
        if not p.exists():
            continue
        s = [
            v
            for k, v in loadmat(p, squeeze_me=True, struct_as_record=False).items()
            if not k.startswith("__")
        ][0]
        a_mm, n_ref = float(s.prop_Reg[0]), float(s.prop_Reg[1])
        e = load_fuel(fuel).regression_for("n2o")[0]
        msrc = (
            f"HRAP `{mat}.mat` prop_Reg=[{a_mm:g}, {n_ref:g}] "
            f"(mm/s; propellant_template.m) sha256 {sha256(p)[:12]}…"
        )
        rows.append(
            Row(
                f"a regresji {fuel} [m/s·(kg/m²s)^-n]",
                "N2O, baza HyProp[0]",
                a_mm * 1e-3,
                msrc,
                float(e.a),
                tol=0.01,
            )
        )
        rows.append(
            Row(f"n regresji {fuel}", "N2O, baza HyProp[0]", n_ref, msrc, float(e.n), tol=0.01)
        )
    r = ref[(ref["Time (s)"] > 0.3) & (ref["Time (s)"] < 6.5)]
    g = r["Oxidizer Mass Flow Rate (kg/s)"] / (math.pi * (r["Grain ID (cm)"] / 200) ** 2)
    n_fit, ln_a = np.polyfit(np.log(g), np.log(r["Regression Rate (mm/s)"]), 1)
    rows.append(
        Row(
            "a z CSV HRAP (fit ṙ=aG^n)",
            "prusak_v2",
            1.04e-4,
            f"HRAP `HDPE.mat` 0.104 mm/s; {src}",
            float(np.exp(ln_a)),
            tol=0.1,
            comment=(
                f"n_fit={n_fit:.4f}. Kolumna CSV „Regression Rate (mm/s)” zawiera faktycznie "
                "m/s (potwierdzone przez d(ID)/dt) – stąd deklaracja „a=1.040e-4 SI”."
            ),
        )
    )
    return rows


# ------------------------------------------------------- sizing examples
def sizing_examples() -> list[Row]:
    import hyprop.api as api
    from hyprop.oppoints import analyze

    rows: list[Row] = []
    res = api.run(api.load_config(str(REPO / "examples" / "pe_05kN.yaml")))
    s = res.summary
    lro = res.event_time("liquid_runout")
    case = "examples/pe_05kN.yaml"
    rows += [
        Row("It", case, 3501, README, s["total_impulse_ns"], tol=0.5, dev_kind="abs", unit="Ns"),
        Row(
            "Pc (szczyt)",
            case,
            36.0,
            README,
            s["peak_pc_pa"] / 1e5,
            tol=0.05,
            dev_kind="abs",
            unit="bar",
        ),
        Row("LRO", case, 7.11, README, lro, tol=0.005, dev_kind="abs", unit="s"),
        Row("Isp średni", case, 184, README, s["isp_mean_s"], tol=0.5, dev_kind="abs", unit="s"),
    ]
    rep = analyze(res)
    iw, ta = rep.point("impulse_weighted").values, rep.time_average
    ph = rep.phases_table().set_index("phase")
    rows += [
        Row(
            "Średnia czasowa F vs IW [%]",
            "ROP " + case,
            -51,
            README,
            100 * (ta["thrust"] / iw["thrust"] - 1),
            tol=1.0,
            dev_kind="abs",
            unit="pp",
            comment="README podaje liczby całkowite. Tolerancja ±1 pp.",
        ),
        Row(
            "Średnia czasowa Pc vs IW [%]",
            "ROP " + case,
            -47,
            README,
            100 * (ta["pc"] / iw["pc"] - 1),
            tol=1.0,
            dev_kind="abs",
            unit="pp",
        ),
        Row(
            "Udział fazy ciekłej w It [%]",
            "ROP " + case,
            92.8,
            README,
            100 * ph.loc["liquid", "impulse_share"],
            tol=0.05,
            dev_kind="abs",
            unit="pp",
        ),
        Row(
            "Udział fazy ciekłej w czasie [%]",
            "ROP " + case,
            43.1,
            README,
            100 * ph.loc["liquid", "time_share"],
            tol=0.05,
            dev_kind="abs",
            unit="pp",
        ),
    ]
    return rows


def size_3km() -> list[Row]:
    import hyprop.api as api
    import hyprop.simulation.solver as sm
    from hyprop.sizing.preliminary import SizingOptions

    case = "examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera)"
    old = sm._TABLE_OF, sm._TABLE_PC
    sm._TABLE_OF, sm._TABLE_PC = 6, 5  # as in the example
    sm._TABLE_CACHE.clear()
    try:
        sz = api.size(
            thrust_n=500.0,
            total_impulse_ns=4000.0,
            apogee_m=3000.0,
            fuel="hdpe",
            oxidizer="n2o",
            options=SizingOptions(cea_backend="cantera"),
        )
    finally:
        sm._TABLE_OF, sm._TABLE_PC = old
        sm._TABLE_CACHE.clear()
    a = sz.achieved
    return [
        Row(
            "Liczba iteracji",
            case,
            8,
            README,
            sz.iterations,
            tol=0,
            dev_kind="abs",
            comment="Tolerancja sizingu 1 % (v0.1: 3 %); v0.1 padało na błędzie B1.",
        ),
        Row("F_iw", case, 498, README, a["thrust_iw_n"], tol=0.5, dev_kind="abs", unit="N"),
        Row("It", case, 4030, README, a["total_impulse_ns"], tol=0.5, dev_kind="abs", unit="Ns"),
        Row(
            "Dt",
            case,
            12.0,
            README,
            sz.nozzle.throat_diameter_m * 1e3,
            tol=0.05,
            dev_kind="abs",
            unit="mm",
        ),
        Row("eps", case, 5.00, README, sz.nozzle.expansion_ratio, tol=0.005, dev_kind="abs"),
    ]


def trajectory() -> list[Row]:
    src_text = (REPO / "examples" / "trajectory_pe_3km.py").read_text(encoding="utf-8")
    code = src_text.replace("print(", "(lambda *a, **k: None)(")
    ns: dict = {"__name__": "traj"}
    exec(compile(code, "trajectory_pe_3km.py", "exec"), ns)
    import hyprop.simulation.solver as sm

    sm._TABLE_OF, sm._TABLE_PC = 10, 7  # the example mutates module globals
    sm._TABLE_CACHE.clear()
    return [
        Row(
            "Apogeum (m_dry = 7 kg)",
            "examples/trajectory_pe_3km.py",
            3736,
            README,
            ns["apogee"],
            tol=0.5,
            dev_kind="abs",
            unit="m",
            comment="m_dry, Cd, D to założenia (skrypt); bez referencji lotnej.",
        )
    ]


# ------------------------------------------------------- thermochemistry
#: Project operating points (PE/N2O): README point + prusak_v2 liquid phase.
PE_POINTS = ((6.5, 35.0), (6.3, 32.0), (8.0, 32.0))  # (O/F, Pc [bar])
SPLITSTONE = "Splitstone & Johnson, J. Res. NBS 78A(5) 611-616 (1974), doi:10.6028/jres.078A.038"


def pe_thermochemistry() -> list[Row]:
    """PE/N2O: Cantera and RocketCEA backends vs NASA's own CEA package.

    Reference: NASA CEA (Python package ``cea``, NASA Glenn, RP-1311
    algorithm) with reactant '(CH2)x(cr)'. Its library enthalpy for PE
    (-25.6 kJ/mol CH2, McBride 1996) is replaced by HyProp's value through
    the chamber enthalpy hc, so all three codes solve the same problem.
    """
    import numpy as np

    from hyprop.cea import get_backend
    from hyprop.data import load_fuel

    rows: list[Row] = []
    fuel = load_fuel("ldpe")
    assert fuel.enthalpy_of_formation is not None
    hf = fuel.enthalpy_of_formation.value
    rows.append(
        Row(
            "ΔHf PE [kJ/mol C2H4]",
            "baza HyProp `ldpe`/`hdpe`",
            2 * -28.182,
            SPLITSTONE,
            hf / 1e3,
            tol=0.01,
            comment=(
                "72 % krystaliczności. NASA CEA thermo.inp '(CH2)x(cr)' ma -51.2 (McBride 1996)."
            ),
        )
    )
    try:
        import cea
    except ImportError:
        rows.append(
            Row(
                "NASA CEA (pakiet cea)",
                "PE/N2O",
                None,
                "",
                None,
                comment="Brak pakietu `cea` (pip install cea, Python >= 3.11).",
            )
        )
        return rows
    ver = getattr(cea, "__version__", "?")
    src = (
        f"NASA CEA, pakiet `cea` {ver} (NASA Glenn; Gordon & McBride RP-1311), "
        "reagent (CH2)x(cr) z ΔHf HyProp"
    )
    reac = cea.Mixture(["(CH2)x(cr)", "N2O"])
    t298 = np.array([298.15, 298.15])
    h_ox = reac.calc_property(cea.ENTHALPY, np.array([0.0, 1.0]), t298)  # J/kg
    m_c2h4 = 2 * 14.02658e-3
    h_fu = hf / m_c2h4  # J/kg
    prod = cea.Mixture(["(CH2)x(cr)", "N2O"], products_from_reactants=True)
    solver = cea.RocketSolver(prod, reactants=reac)
    sol = cea.RocketSolution(solver)
    backends = {}
    for name in ("cantera", "rocketcea"):
        try:
            backends[name] = get_backend(name, fuel="ldpe", oxidizer="n2o")
        except Exception:
            pass
    g0 = 9.80665
    for of, pc in PE_POINTS:
        w = reac.of_ratio_to_weights(np.array([0.0, 1.0]), np.array([1.0, 0.0]), of)
        hc = (h_fu / (1 + of) + h_ox * of / (1 + of)) / cea.R
        solver.solve(sol, w, pc, [pc / 1.01325], supar=[5.0], hc=hc, iac=True)
        mw = sol.MW[0]
        ref = dict(
            Tc=sol.T[0],
            cstar=sol.c_star[0],
            gamma_s=sol.gamma_s[0],
            gamma_fr=sol.cp_fr[0] / (sol.cp_fr[0] - 8.314462618 / mw),
            eps_opt=sol.ae_at[2],
            isp_opt=sol.Isp[2] / g0,
            isp5=sol.Isp[3] / g0,
        )
        case = f"PE/N2O O/F {of}, Pc {pc:g} bar"
        for name, b in backends.items():
            r5 = b.query(of, pc * 1e5, 5.0)
            ro = b.query(of, pc * 1e5, float(ref["eps_opt"]))
            c = r5.chamber
            got = dict(
                Tc=c.temperature_k,
                cstar=r5.cstar_m_s,
                gamma_s=c.gamma_eq,
                gamma_fr=c.gamma,
                isp_opt=ro.equilibrium.exhaust_velocity_m_s / g0,
                isp5=r5.equilibrium.exhaust_velocity_m_s / g0,
            )
            labels = dict(
                Tc="Tc",
                cstar="c*",
                gamma_s="γ_s (równowagowe)",
                gamma_fr="γ zamrożone cp/cv",
                isp_opt=f"Isp, p_e = 1 atm (ε={ref['eps_opt']:.3f})",
                isp5="Isp próżn.-wylot v_e/g0, ε=5",
            )
            keys = labels if name == "cantera" else ("Tc", "cstar", "isp_opt")
            for k in keys:
                rows.append(
                    Row(
                        f"{labels[k]} – {name}",
                        case,
                        float(ref[k]),
                        src,
                        None if (v := got[k]) is None else float(v),
                        tol=0.5,
                    )
                )
        if "cantera" in backends:
            cb = backends["cantera"].query(of, pc * 1e5, 5.0).chamber
            assert cb.gamma_eq is not None  # Cantera always fills γ_s
            for gname, g in (("zamrożone", cb.gamma), ("γ_s", cb.gamma_eq)):
                cs = math.sqrt(
                    8314.462618 / (cb.molar_mass_kg_mol * 1e3) * cb.temperature_k / g
                ) * ((g + 1) / 2) ** ((g + 1) / (2 * (g - 1)))
                rows.append(
                    Row(
                        f"c* ze wzoru idealnego z γ {gname} vs c* CEA [%]",
                        case,
                        float(ref["cstar"]),
                        src,
                        cs,
                        tol=None if gname == "zamrożone" else 0.5,
                        status=INFO if gname == "zamrożone" else "",
                        comment=(
                            "Wzór idealny z γ zamrożonym zaniża c* (dawne „~2.3 %” ze skryptu 07)."
                            if gname == "zamrożone"
                            else "Z γ_s wzór odtwarza c* równowagowe."
                        ),
                    )
                )
    return rows


def n2o_esdu_vs_coolprop() -> list[Row]:
    import CoolProp.CoolProp as CP

    from hyprop.tank.n2o_properties import ESDU91022 as E
    from hyprop.tank.n2o_properties import CoolPropN2O

    c = CoolPropN2O()
    T = np.arange(263.0, 303.01, 0.5)
    src = (
        f"CoolProp {CP.get_global_param_string('version')}, EOS N2O: Lemmon & Span, J. Chem. Eng. "
        "Data "
        f"51 (2006) 785–850 (klucz {CP.get_BibTeXKey('N2O', 'EOS')})"
    )
    rows = []
    for f, label in (("psat", "p_sat"), ("rho_liquid", "ρ_l")):
        d = max(abs(getattr(E, f)(t) / getattr(c, f)(t) - 1) for t in T) * 100
        rows.append(
            Row(
                f"max |ESDU/CoolProp−1| {label} [%]",
                "263–303 K, krok 0.5 K",
                1.5,
                f"{README}; {src}",
                d,
                dev_kind="abs",
                unit="pp",
                comment=(
                    "Deklaracja „within 1.5 %”. Kolumna HyProp = max odchyłka; odchyłka = "
                    "zapas do 1.5 %."
                ),
                status="PASS" if d <= 1.5 else FAIL,
            )
        )
    return rows


def all_rows() -> list[Row]:
    rows: list[Row] = []
    for fn in (
        hrap_benchmark,
        sizing_examples,
        size_3km,
        trajectory,
        pe_thermochemistry,
        n2o_esdu_vs_coolprop,
    ):
        rows += fn()
    return rows
