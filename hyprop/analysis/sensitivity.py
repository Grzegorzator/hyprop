"""Sensitivity analysis over EngineConfig parameters (stage E9).

Methods (decision D9: OAT is the default screening; Morris and Sobol
via SALib when installed):

* **OAT** (one-at-a-time): relative sensitivity
  S = (dY/Y) / (dX/X) from central differences at +-delta (default 5%).
  Cheap (2 runs/parameter), local, ignores interactions.
* **Morris** elementary effects: global screening, ranks parameters
  with interaction indication (mu*, sigma); ~r*(k+1) runs.
* **Sobol** indices: full variance decomposition (S1, ST); expensive
  (N*(k+2) runs) - for final studies.

Outputs analysed: any numeric key of the batch row (default:
``total_impulse_ns``, ``thrust_iw``, ``peak_pc_pa``).

Sources: Saltelli et al., *Global Sensitivity Analysis: The Primer*;
Morris 1991; SALib (Herman & Usher 2017).
"""

from __future__ import annotations

from typing import Dict, Sequence, Tuple

import pandas as pd

from hyprop.batch.runner import run_case
from hyprop.core.config import EngineConfig
from hyprop.core.logging import get_logger

_log = get_logger(__name__)

OUTPUTS_DEFAULT = ("total_impulse_ns", "thrust_iw", "peak_pc_pa")


def oat_sensitivity(
    config: EngineConfig,
    parameters: Dict[str, float],
    outputs: Sequence[str] = OUTPUTS_DEFAULT,
    delta: float = 0.05,
) -> pd.DataFrame:
    """Central-difference relative sensitivities.

    Parameters
    ----------
    parameters:
        ``{config_path: nominal_value}`` - nominal must be explicit so
        that database-supplied values (e.g. regression a, n) are pinned.
    delta:
        Relative perturbation (default +-5%).

    Returns
    -------
    DataFrame indexed by parameter path, columns = outputs, values =
    relative sensitivity S (1% change of X -> S% change of Y).
    """
    base = run_case(config, dict(parameters))
    rows = {}
    for path, nominal in parameters.items():
        case_hi = dict(parameters); case_hi[path] = nominal * (1 + delta)
        case_lo = dict(parameters); case_lo[path] = nominal * (1 - delta)
        hi = run_case(config, case_hi)
        lo = run_case(config, case_lo)
        rows[path] = {
            out: ((hi[out] - lo[out]) / max(abs(base[out]), 1e-12))
                 / (2 * delta)
            for out in outputs
        }
        _log.info("OAT %s done", path)
    return pd.DataFrame(rows).T


def morris_sensitivity(
    config: EngineConfig,
    ranges: Dict[str, Tuple[float, float]],
    outputs: Sequence[str] = OUTPUTS_DEFAULT,
    trajectories: int = 8,
    seed: int = 0,
) -> Dict[str, pd.DataFrame]:
    """Morris elementary-effects screening (requires SALib)."""
    try:
        from SALib.analyze import morris as morris_analyze
        from SALib.sample import morris as morris_sample
    except ImportError as exc:                       # pragma: no cover
        raise ImportError("Morris requires SALib (pip install SALib).") from exc

    names = list(ranges)
    problem = {"num_vars": len(names), "names": names,
               "bounds": [list(ranges[n]) for n in names]}
    sample = morris_sample.sample(problem, trajectories, seed=seed)
    rows = [run_case(config, dict(zip(names, x))) for x in sample]
    frame = pd.DataFrame(rows)
    results = {}
    for out in outputs:
        analysis = morris_analyze.analyze(
            problem, sample, frame[out].to_numpy(), seed=seed,
            print_to_console=False,
        )
        results[out] = pd.DataFrame(
            {"mu_star": analysis["mu_star"], "sigma": analysis["sigma"]},
            index=names,
        )
    return results
