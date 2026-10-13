"""Stage 1, item 1: reproduce every quantitative claim of README.md.

Reference values are either (a) the README claim itself, checked against a
fresh HyProp run, or (b) the primary data the claim was derived from (HRAP
output CSV, HRAP .mat configs, the user's 07_cantera script, CoolProp).
External files are located through environment variables (see
validation/README.md); rows whose reference file is missing become TODO.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

import numpy as np

from validation.common import FAIL, INFO, REPO, Row, external, sha256

_trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))
README = "README.md §Validation anchors"


def _load_example(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "examples" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)            # examples guard main() -> no side effects
    return mod


# ----------------------------------------------------------------- HRAP E6
def hrap_benchmark() -> List[Row]:
    import pandas as pd
    import hyprop.api as api
    from hyprop.core.config import EngineConfig

    hrap_dir = external("HYPROP_HRAP_DIR")
    csv = hrap_dir / "output" / "prusakv2_HRAP_output.csv" if hrap_dir else None
    rows: List[Row] = []
    if csv is None or not csv.exists():
        return [Row("HRAP benchmark", "prusak_v2", None, "", None,
                    comment="Brak pliku HRAP CSV (ustaw HYPROP_HRAP_DIR).")]
    src = f"HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 {sha256(csv)[:12]}…"

    bench = _load_example("benchmark_prusak_v2")
    cfg = EngineConfig.from_dict(bench.CFG)
    res = api.run(cfg)
    df = res.history.to_dataframe()
    ref = pd.read_csv(csv)
    ref.columns = [c.strip() for c in ref.columns]
    lro = res.event_time("liquid_runout")
    tg = np.arange(0.2, min(lro, 7.0), 0.05)    # identical window to benchmark script

    def dev(col_h, col_r, scale=1.0):
        a = np.interp(tg, df.t, df[col_h]) / scale
        b = np.interp(tg, ref["Time (s)"], ref[col_r])
        return float(100 * np.mean(np.abs(a - b)) / np.mean(np.abs(b)))

    claims = [("Pc", "pc", "Combustion Chamber Pressure (kPa)", 1e3, 1.7),
              ("p_tank", "p_tank", "Oxidizer Tank Pressure (kPa)", 1e3, 0.6),
              ("O/F", "of", "Oxidizer to Fuel Ratio", 1.0, 1.0),
              ("Ciąg F", "thrust", "Thrust (N)", 1.0, 6.2)]
    for label, ch, cr, sc, claim in claims:
        rows.append(Row(f"Średnia odchyłka {label} HyProp–HRAP [%]", "prusak_v2, faza ciekła 0.2–7.0 s",
                        claim, f"{README}; {src}", dev(ch, cr, sc), tol=0.05, dev_kind="abs",
                        unit="pp", comment="Odtworzenie deklaracji README (tolerancja = zaokrąglenie)."))
    rows.append(Row("LRO HyProp", "prusak_v2", 7.19, README, round(lro, 4), tol=0.005,
                    dev_kind="abs", unit="s"))
    # HRAP run-out from its own data: the step where mdot_ox collapses
    t = ref["Time (s)"].to_numpy(); m = ref["Oxidizer Mass Flow Rate (kg/s)"].to_numpy()
    i = int(np.argmin(np.diff(m)))
    lro_hrap = float(t[i + 1])
    rows.append(Row("LRO HRAP: deklaracja README „~7.5 s”", "prusak_v2", lro_hrap,
                    f"{src}: skok ṁ_ox {m[i]:.3f}→{m[i+1]:.3f} kg/s", 7.5, tol=1.0,
                    comment="Kolumna HyProp = wartość z README. README zawyża LRO HRAP; z CSV wynika 6.955 s."))
    rows.append(Row("LRO HyProp vs HRAP", "prusak_v2", lro_hrap, src, round(lro, 4),
                    comment="Odchyłka faktyczna (bez tolerancji – do oceny w pkt 5).", status=INFO))

    # Thrust-gap decomposition: same run, frozen instead of shifting exit.
    import hyprop.cea.table as tb
    q0 = tb.TabulatedBackend.query
    tb.TabulatedBackend.query = lambda s, of, pc, eps: dataclasses.replace(
        q0(s, of, pc, eps), equilibrium=q0(s, of, pc, eps).frozen)
    try:
        dff = api.run(cfg).history.to_dataframe()
    finally:
        tb.TabulatedBackend.query = q0
    a = np.interp(tg, dff.t, dff.thrust); b = np.interp(tg, ref["Time (s)"], ref["Thrust (N)"])
    rows.append(Row("Średnia odchyłka F, wylot zamrożony [%]", "prusak_v2 (diagnostyka)", None, "",
                    float(100 * np.mean(np.abs(a - b)) / np.mean(b)), status=INFO,
                    comment="Ta sama symulacja z v_e zamrożonym zamiast równowagowego: luka F 6.2 → "
                            "~3.3 %. Równowaga/zamrożenie tłumaczy ok. połowę; reszta niewyjaśniona (pkt 5)."))

    # regression coefficients: HRAP .mat vs HyProp database
    from scipy.io import loadmat
    from hyprop.data import load_fuel
    for fuel, mat in (("hdpe", "HDPE"), ("paraffin", "Paraffin"), ("htpb", "HTPB")):
        p = hrap_dir / "propellant_configs" / f"{mat}.mat"
        if not p.exists():
            continue
        s = [v for k, v in loadmat(p, squeeze_me=True, struct_as_record=False).items()
             if not k.startswith("__")][0]
        a_mm, n_ref = float(s.prop_Reg[0]), float(s.prop_Reg[1])
        e = load_fuel(fuel).regression_for("n2o")[0]
        msrc = f"HRAP `{mat}.mat` prop_Reg=[{a_mm:g}, {n_ref:g}] (mm/s; propellant_template.m) sha256 {sha256(p)[:12]}…"
        rows.append(Row(f"a regresji {fuel} [m/s·(kg/m²s)^-n]", "N2O, baza HyProp[0]",
                        a_mm * 1e-3, msrc, float(e.a), tol=0.01))
        rows.append(Row(f"n regresji {fuel}", "N2O, baza HyProp[0]", n_ref, msrc, float(e.n), tol=0.01))
    r = ref[(ref["Time (s)"] > 0.3) & (ref["Time (s)"] < 6.5)]
    g = r["Oxidizer Mass Flow Rate (kg/s)"] / (math.pi * (r["Grain ID (cm)"] / 200) ** 2)
    n_fit, ln_a = np.polyfit(np.log(g), np.log(r["Regression Rate (mm/s)"]), 1)
    rows.append(Row("a z CSV HRAP (fit ṙ=aG^n)", "prusak_v2", 1.04e-4, f"HRAP `HDPE.mat` 0.104 mm/s; {src}",
                    float(np.exp(ln_a)), tol=0.1,
                    comment=f"n_fit={n_fit:.4f}. Kolumna CSV „Regression Rate (mm/s)” zawiera faktycznie m/s "
                            "(potwierdzone przez d(ID)/dt) – stąd deklaracja „a=1.040e-4 SI”."))
    return rows


# ------------------------------------------------------- sizing examples
def sizing_examples() -> List[Row]:
    import hyprop.api as api
    from hyprop.oppoints import analyze

    rows: List[Row] = []
    res = api.run(api.load_config(str(REPO / "examples" / "hdpe_05kN.yaml")))
    s = res.summary
    lro = res.event_time("liquid_runout")
    case = "examples/hdpe_05kN.yaml"
    rows += [
        Row("It", case, 3942, README, s["total_impulse_ns"], tol=0.5, dev_kind="abs", unit="Ns"),
        Row("Pc (szczyt)", case, 37, README, s["peak_pc_pa"] / 1e5, tol=0.5, dev_kind="abs", unit="bar",
            comment="README podaje „Pc 37 bar” bez rodzaju; zgadza się z wartością szczytową."),
        Row("LRO", case, 7.4, README, lro, tol=0.05, dev_kind="abs", unit="s"),
    ]
    rep = analyze(res)
    iw, ta = rep.point("impulse_weighted").values, rep.time_average
    ph = rep.phases_table().set_index("phase")
    rows += [
        Row("Średnia czasowa F vs IW [%]", "ROP " + case, -51, README, 100 * (ta["thrust"] / iw["thrust"] - 1),
            tol=1.0, dev_kind="abs", unit="pp",
            comment="README podaje liczby całkowite (51 %, 48 %); przykład drukuje −51.5 % i −47.5 %. Tolerancja ±1 pp."),
        Row("Średnia czasowa Pc vs IW [%]", "ROP " + case, -48, README, 100 * (ta["pc"] / iw["pc"] - 1),
            tol=1.0, dev_kind="abs", unit="pp"),
        Row("Udział fazy ciekłej w It [%]", "ROP " + case, 92.4, README, 100 * ph.loc["liquid", "impulse_share"],
            tol=0.05, dev_kind="abs", unit="pp"),
        Row("Udział fazy ciekłej w czasie [%]", "ROP " + case, 42.6, README, 100 * ph.loc["liquid", "time_share"],
            tol=0.05, dev_kind="abs", unit="pp"),
    ]
    return rows


def size_3km() -> List[Row]:
    import hyprop.simulation.solver as sm
    import hyprop.api as api

    case = "examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km)"
    rows: List[Row] = []
    old = sm._TABLE_OF, sm._TABLE_PC
    sm._TABLE_OF, sm._TABLE_PC = 6, 5           # as in the example
    sm._TABLE_CACHE.clear()
    try:
        try:
            api.size(thrust_n=500.0, total_impulse_ns=4000.0, apogee_m=3000.0, fuel="hdpe", oxidizer="n2o")
            rows.append(Row("api.size bez wyjątku", case, None, "", None, status=INFO, comment="OK"))
        except ValueError as exc:
            rows.append(Row("api.size bez wyjątku", case, None, README, None, status=FAIL,
                            comment=f"BŁĄD: `{exc}`. Klucz cache tablicy CEA to round(eps, 2), a "
                                    "TabulatedBackend.query wymaga |Δeps|<1e-9 → kolizja kluczy dla "
                                    "eps 5.0209 i 5.0167."))
        # Diagnostic: exact-eps cache key (this is the proposed fix, not applied in hyprop/)
        orig = sm._build_cea_table
        cache = {}

        def exact(config, eps):
            k = (config.fuel.name, config.oxidizer.name, float(eps))
            if k not in cache:
                sm._TABLE_CACHE.clear()
                cache[k] = orig(config, eps)
            return cache[k]
        sm._build_cea_table = exact
        try:
            sz = api.size(thrust_n=500.0, total_impulse_ns=4000.0, apogee_m=3000.0, fuel="hdpe", oxidizer="n2o")
        finally:
            sm._build_cea_table = orig
        a = sz.achieved
        note = "Z poprawionym kluczem cache (diagnostyka, bez zmian w hyprop/)."
        rows += [
            Row("Liczba iteracji", case, 5, README, sz.iterations, tol=0, dev_kind="abs", comment=note),
            Row("F_iw", case, 494, README, a["thrust_iw_n"], tol=0.5, dev_kind="abs", unit="N", comment=note),
            Row("It", case, 4083, README, a["total_impulse_ns"], tol=0.5, dev_kind="abs", unit="Ns", comment=note),
            Row("eps", case, 5.02, README, sz.nozzle.expansion_ratio, tol=0.005, dev_kind="abs", comment=note),
        ]
    finally:
        sm._TABLE_OF, sm._TABLE_PC = old
        sm._TABLE_CACHE.clear()
    return rows


def trajectory() -> List[Row]:
    src_text = (REPO / "examples" / "trajectory_hdpe_3km.py").read_text(encoding="utf-8")
    pat = r"^M_DRY, D_REF, CD = ([0-9.]+), 0\.10, 0\.55"
    m_now = float(re.search(pat, src_text, re.M).group(1))
    out = {}
    for m_dry in (9.0, m_now):
        code = re.sub(pat, f"M_DRY, D_REF, CD = {m_dry}, 0.10, 0.55", src_text, flags=re.M)
        code = code.replace("print(", "(lambda *a, **k: None)(")
        ns: dict = {"__name__": "traj"}
        exec(compile(code, "trajectory_hdpe_3km.py", "exec"), ns)
        out[m_dry] = ns["apogee"]
        import hyprop.simulation.solver as sm
        sm._TABLE_OF, sm._TABLE_PC = 10, 7          # the example mutates module globals
        sm._TABLE_CACHE.clear()
    case = "examples/trajectory_hdpe_3km.py"
    return [
        Row("Apogeum (m_dry = 9 kg, jak w README)", case, 3291, README, out[9.0], tol=0.5, dev_kind="abs", unit="m"),
        Row(f"Apogeum (m_dry = {m_now:g} kg, obecny skrypt)", case, None, "", out[m_now], status=INFO, unit="m",
            comment="README nieaktualne: commit d22b828 zmienił m_dry 9→7 kg, README dalej podaje 3291 m dla 9 kg."),
    ]


# ------------------------------------------------------- thermochemistry
def cantera_anchor() -> List[Row]:
    from scipy.optimize import brentq
    from hyprop.cea import get_backend

    rows: List[Row] = []
    script = external("HYPROP_REF_07", str(REPO.parent / "07_cantera_punkt0_termochemia.py"))
    ref = None
    if script is not None:
        with tempfile.TemporaryDirectory() as td:
            subprocess.run([sys.executable, str(script)], cwd=td, check=True,
                           capture_output=True, text=True, timeout=600)
            for line in (Path(td) / "cantera_sweep.csv").read_text().splitlines()[1:]:
                f = line.split(",")
                if abs(float(f[0]) - 6.5) < 1e-9:
                    ref = dict(Tc=float(f[1]), cstar=float(f[2]), gamma=float(f[3]), M=float(f[4]),
                               isp=float(f[5]))
        s07 = f"Skrypt użytkownika `07_cantera_punkt0_termochemia.py` (sha256 {sha256(script)[:12]}…), " \
              f"cantera_sweep.csv, O/F=6.5"
    case = "parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar"
    res = {}
    for name in ("cantera", "rocketcea"):
        try:
            b = get_backend(name, fuel="paraffin", oxidizer="n2o")
        except Exception:
            continue
        eps = brentq(lambda e: b.query(6.5, 35e5, e).equilibrium.exit_state.pressure_pa - 1.013e5,
                     2.0, 15.0, xtol=1e-8)
        r = b.query(6.5, 35e5, eps)
        c = r.chamber
        g, mm = c.gamma, c.molar_mass_kg_mol
        cs_formula = math.sqrt(8314.46 / (mm * 1e3) * c.temperature_k / g) * \
            ((g + 1) / 2) ** ((g + 1) / (2 * (g - 1)))
        res[name] = dict(Tc=c.temperature_k, gamma=g, cstar=r.cstar_m_s, cs_formula=cs_formula,
                         isp=r.equilibrium.exhaust_velocity_m_s / 9.80665,
                         isp_fr=r.frozen.exhaust_velocity_m_s / 9.80665, eps=eps)
    ca = res.get("cantera")
    if ca and ref:
        rows += [
            Row("Tc", case + " [Cantera]", ref["Tc"], s07, ca["Tc"], tol=0.5, dev_kind="abs", unit="K",
                comment="Cantera vs Cantera (ta sama baza gri30 i to samo Hf) – spójność, nie walidacja niezależna."),
            Row("γ (cp/cv, zamrożone)", case + " [Cantera]", ref["gamma"], s07, ca["gamma"], tol=0.0005,
                dev_kind="abs"),
            Row("Isp_opt (równowaga)", case + " [Cantera]", ref["isp"], s07, ca["isp"], tol=0.05, dev_kind="abs",
                unit="s"),
            Row("c* ze wzoru idealnego (γ zamrożone)", case + " [Cantera]", ref["cstar"], s07, ca["cs_formula"],
                tol=0.5, dev_kind="abs", unit="m/s"),
        ]
    if ca:
        rows += [
            Row("Tc – deklaracja README", case, 3292, README, ca["Tc"], tol=0.5, dev_kind="abs", unit="K"),
            Row("γ – deklaracja README", case, 1.245, README, ca["gamma"], tol=0.0005, dev_kind="abs",
                comment="README: 1.245; skrypt 07 i HyProp: 1.247. Literówka w README (różnica 0.2 %)."),
            Row("Isp – deklaracja README", case, 247, README, ca["isp"], tol=0.5, dev_kind="abs", unit="s"),
            Row("c* równowagowe / c* ze wzoru – deklaracja README „~2.3 %”", case, 2.3, README,
                100 * (ca["cstar"] / ca["cs_formula"] - 1), tol=0.1, dev_kind="abs", unit="pp"),
        ]
    rc = res.get("rocketcea")
    if ca and rc:
        src_rc = "NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; " \
                 "paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol)"
        rows += [
            Row("Tc Cantera vs NASA CEA", case, rc["Tc"], src_rc, ca["Tc"], tol=1.0),
            Row("c* Cantera vs NASA CEA", case, rc["cstar"], src_rc, ca["cstar"], tol=1.0),
            Row("Isp_opt eq Cantera vs NASA CEA", case, rc["isp"], src_rc, ca["isp"], tol=1.0),
            Row("Isp_opt frozen Cantera vs NASA CEA", case, rc["isp_fr"], src_rc, ca["isp_fr"], tol=1.0),
            Row("γ komory Cantera vs NASA CEA", case, rc["gamma"], src_rc, ca["gamma"], tol=1.0,
                comment="RÓŻNE DEFINICJE: Cantera backend zwraca cp/cv (zamrożone), RocketCEA γ_s "
                        "(równowagowe). Ten sam atrybut `chamber.gamma` znaczy co innego zależnie od backendu."),
            Row("c* ze wzoru idealnego z γ_s (CEA) vs c* CEA", case, rc["cstar"], src_rc, rc["cs_formula"],
                tol=0.5, comment="Wyjaśnienie „2.3 %”: wzór idealny z γ_s odtwarza c* równowagowe (0.1 %); "
                                 "2.3 % to wyłącznie efekt wstawienia γ zamrożonego do wzoru."),
        ]
    return rows


def n2o_esdu_vs_coolprop() -> List[Row]:
    from hyprop.tank.n2o_properties import ESDU91022 as E, CoolPropN2O
    import CoolProp.CoolProp as CP
    c = CoolPropN2O()
    T = np.arange(263.0, 303.01, 0.5)
    src = f"CoolProp {CP.get_global_param_string('version')}, EOS N2O: Lemmon & Span, J. Chem. Eng. Data " \
          f"51 (2006) 785–850 (klucz {CP.get_BibTeXKey('N2O', 'EOS')})"
    rows = []
    for f, label in (("psat", "p_sat"), ("rho_liquid", "ρ_l")):
        d = max(abs(getattr(E, f)(t) / getattr(c, f)(t) - 1) for t in T) * 100
        rows.append(Row(f"max |ESDU/CoolProp−1| {label} [%]", "263–303 K, krok 0.5 K", 1.5, f"{README}; {src}", d,
                        dev_kind="abs", unit="pp",
                        comment="Deklaracja „within 1.5 %”. Kolumna HyProp = max odchyłka; odchyłka = zapas do 1.5 %.",
                        status="PASS" if d <= 1.5 else FAIL))
    return rows


def all_rows() -> List[Row]:
    rows: List[Row] = []
    for fn in (hrap_benchmark, sizing_examples, size_3km, trajectory, cantera_anchor, n2o_esdu_vs_coolprop):
        rows += fn()
    return rows
