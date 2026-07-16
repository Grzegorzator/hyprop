"""Monte Carlo uncertainty propagation (stage E9).

Input uncertainties are declared per config path as distributions:

    {"injector.discharge_coefficient": ("normal", 0.60, 0.03),
     "oxidizer.temperature_k":         ("uniform", 288.15, 298.15)}

("normal", mean, std) or ("uniform", low, high). N samples are run and
output percentiles (default 5/50/95) are reported for the selected
outputs - the publication-standard "Pc +- x, F +- y, Isp +- z" bands.
"""

from __future__ import annotations

from typing import Dict, Sequence, Tuple

import numpy as np
import pandas as pd

from hyprop.batch.runner import run_batch
from hyprop.core.config import EngineConfig
from hyprop.core.logging import get_logger

_log = get_logger(__name__)

Distribution = Tuple[str, float, float]
PERCENTILES_DEFAULT = (5.0, 50.0, 95.0)


def sample_inputs(
    distributions: Dict[str, Distribution], samples: int, seed: int = 0
) -> list:
    """Draw N cases from the declared input distributions."""
    rng = np.random.default_rng(seed)
    draws = {}
    for path, (kind, p1, p2) in distributions.items():
        if kind == "normal":
            draws[path] = rng.normal(p1, p2, samples)
        elif kind == "uniform":
            draws[path] = rng.uniform(p1, p2, samples)
        else:
            raise ValueError(f"Unknown distribution '{kind}' for {path}.")
    return [
        {path: float(draws[path][i]) for path in distributions}
        for i in range(samples)
    ]


def monte_carlo(
    config: EngineConfig,
    distributions: Dict[str, Distribution],
    samples: int = 100,
    outputs: Sequence[str] = ("total_impulse_ns", "thrust_iw",
                              "peak_pc_pa", "isp_iw"),
    percentiles: Sequence[float] = PERCENTILES_DEFAULT,
    seed: int = 0,
) -> Dict[str, pd.DataFrame]:
    """Run the MC study; returns {'samples': df, 'bands': percentile df}."""
    cases = sample_inputs(distributions, samples, seed)
    frame = run_batch(config, cases, progress=True)
    bands = pd.DataFrame({
        out: {f"p{p:g}": float(np.nanpercentile(frame[out], p))
              for p in percentiles}
        for out in outputs
    }).T
    _log.info("MC done: %d samples", samples)
    return {"samples": frame, "bands": bands}
