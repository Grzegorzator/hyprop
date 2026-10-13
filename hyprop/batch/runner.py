"""Batch execution of case matrices (stage E9).

A *case* is a dict of config-path overrides applied to a base
:class:`EngineConfig`, e.g. ``{"injector.discharge_coefficient": 0.55,
"oxidizer.temperature_k": 288.15}``. Paths use dots; list indices are
not needed at this stage.

:func:`build_grid` produces the full factorial of parameter lists;
:func:`build_lhs` a Latin Hypercube sample of parameter ranges
(scipy.stats.qmc). :func:`run_batch` executes cases (sequentially by
default - the CEA-table cache in the solver makes each case cheap) and
returns one pandas row per case: overrides + solver summary + selected
impulse-weighted ROP values.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Sequence

import pandas as pd

from hyprop.core.config import EngineConfig
from hyprop.core.logging import get_logger
from hyprop.oppoints import analyze

_log = get_logger(__name__)

Case = dict[str, float]

#: Impulse-weighted channels copied into batch results.
_ROP_CHANNELS = ("thrust", "pc", "of", "isp")


def apply_overrides(config: EngineConfig, case: Case) -> EngineConfig:
    """Return a new config with dotted-path overrides applied."""
    raw = config.model_dump(mode="python")
    for path, value in case.items():
        node = raw
        keys = path.split(".")
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value
    return EngineConfig.from_dict(raw)


def build_grid(parameters: dict[str, Sequence[float]]) -> list[Case]:
    """Full factorial grid of ``{path: [values...]}``."""
    names = list(parameters)
    return [
        dict(zip(names, combo, strict=False))
        for combo in itertools.product(*(parameters[n] for n in names))
    ]


def build_lhs(ranges: dict[str, tuple[float, float]], samples: int, seed: int = 0) -> list[Case]:
    """Latin Hypercube sample of ``{path: (low, high)}``."""
    from scipy.stats import qmc

    names = list(ranges)
    sampler = qmc.LatinHypercube(d=len(names), seed=seed)
    unit = sampler.random(samples)
    lows = [ranges[n][0] for n in names]
    highs = [ranges[n][1] for n in names]
    scaled = qmc.scale(unit, lows, highs)
    return [dict(zip(names, row, strict=False)) for row in scaled]


def run_case(config: EngineConfig, case: Case) -> dict[str, float]:
    """Run one case; returns overrides + summary + ROP values."""
    from hyprop.simulation import run_simulation

    result = run_simulation(apply_overrides(config, case))
    row: dict[str, float] = dict(case)
    row.update(result.summary)
    iw = analyze(result).point("impulse_weighted")
    row.update({f"{ch}_iw": iw[ch] for ch in _ROP_CHANNELS})
    lro = result.event_time("liquid_runout")
    row["lro_s"] = lro if lro is not None else float("nan")
    return row


def run_batch(config: EngineConfig, cases: Iterable[Case], progress: bool = True) -> pd.DataFrame:
    """Execute all cases; failed cases yield NaN rows (logged)."""
    rows = []
    cases = list(cases)
    for index, case in enumerate(cases):
        try:
            rows.append(run_case(config, case))
        except Exception as exc:  # noqa: BLE001
            _log.warning("Case %d failed: %s (%s)", index, case, exc)
            rows.append(dict(case))
        if progress and (index + 1) % 10 == 0:
            _log.info("Batch progress: %d/%d", index + 1, len(cases))
    return pd.DataFrame(rows)
