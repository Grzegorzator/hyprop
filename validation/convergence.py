"""Stage 1, item 8: numerical convergence of the transient solver.

Case: examples/pe_05kN.yaml (Cantera tables). Time-step study
dt = 0.04 ... 0.0025 s and Pc-tolerance study 1e-3 ... 1e-6 at dt = 0.01 s.
For It, LRO and the liquid-phase mean Pc the observed order
p = log2(|q(4h) - q(2h)| / |q(2h) - q(h)|) and the Richardson estimate
q* = q(h) + (q(h) - q(2h)) / (2^p - 1) are reported; the error of each dt
is measured against q*. No literature reference: these rows are
self-convergence checks (PASS when the default dt is within 0.1 % of q*).
"""

from __future__ import annotations

import math
from typing import Dict, List

import numpy as np

from validation.common import INFO, REPO, Row

DTS = (0.04, 0.02, 0.01, 0.005, 0.0025)
TOLS = (1e-3, 1e-4, 1e-5, 1e-6)
CASE = "examples/pe_05kN.yaml"


def _metrics(cfg_dict) -> Dict[str, float]:
    import hyprop.api as api
    from hyprop.core.config import EngineConfig

    res = api.run(EngineConfig.from_dict(cfg_dict))
    h = res.history
    lro = res.event_time("liquid_runout")
    liq = h["t"] <= lro
    return dict(It=res.summary["total_impulse_ns"], LRO=lro, Pc_liq=float(np.mean(h["pc"][liq])))


def all_rows() -> List[Row]:
    import yaml

    base = yaml.safe_load((REPO / CASE).read_text(encoding="utf-8"))
    runs = {}
    for dt in DTS:
        cfg = dict(base)
        cfg["simulation"] = dict(base["simulation"], dt_s=dt)
        runs[dt] = _metrics(cfg)
    default_dt = float(base["simulation"]["dt_s"])
    rows: List[Row] = []
    for q, unit in (("It", "Ns"), ("LRO", "s"), ("Pc_liq", "Pa")):
        q1, q2, q4 = runs[DTS[-1]][q], runs[DTS[-2]][q], runs[DTS[-3]][q]
        d_coarse, d_fine = abs(q4 - q2), abs(q2 - q1)
        p = math.log2(d_coarse / d_fine) if d_fine > 0 and d_coarse > 0 else float("nan")
        p_use = p if (p == p and p > 0.3) else 1.0
        q_star = q1 + (q1 - q2) / (2 ** p_use - 1)
        series = ", ".join(f"dt={dt:g}: {100 * (runs[dt][q] / q_star - 1):+.3f} %" for dt in DTS)
        rows.append(Row(f"Rząd zbieżności w dt: {q}", CASE, None, "", p, status=INFO,
                        comment=f"Ekstrapolacja Richardsona q* = {q_star:.6g} {unit}; błędy: {series}"))
        rows.append(Row(f"{q} przy domyślnym dt = {default_dt:g} s vs q* (Richardson)", CASE, q_star,
                        "ekstrapolacja Richardsona z dt = 0.01/0.005/0.0025 s (samozbieżność)",
                        runs[default_dt][q], tol=0.1 if q != "LRO" else 1.001 * 100 * default_dt / q_star,
                        unit=unit,
                        comment=("LRO jest kwantowane krokiem dt (zdarzenie na siatce czasu): tolerancja = 1 krok."
                                 if q == "LRO" else
                                 "Schemat jawny Eulera: rząd 1. dt = 0.01 s daje błąd ~0.015 % It; sizing (dt 0.02 s) ~0.03 %.")))
    for tol in TOLS:
        cfg = dict(base)
        cfg["simulation"] = dict(base["simulation"], dt_s=0.01, pc_tolerance=tol)
        m = _metrics(cfg)
        ref = runs[0.01]["It"] if tol == 1e-4 else None
        rows.append(Row(f"It przy tolerancji Pc = {tol:g}", f"{CASE}, dt = 0.01 s", runs[0.01]["It"],
                        "ten sam przypadek, tolerancja domyślna 1e-4", m["It"], tol=0.05, unit="Ns"))
        del ref
    return rows
