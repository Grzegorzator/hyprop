"""Burn-phase segmentation and per-phase statistics (stage E7).

Phases of a self-pressurised blowdown burn:

* **liquid**     - start .. liquid run-out (LRO event from the solver);
* **transition** - LRO .. chamber pressure fallen to a fraction
  (default 50%) of its value at LRO (two-phase/vapour transient);
* **gas**        - remainder (weak vapour blowdown tail).

For each phase: mean F, Pc, O/F, Isp, c*, gamma, Tc; delivered impulse,
share of total impulse [%], share of burn time [%].
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from hyprop.core.state import TimeHistory

#: NumPy 2.x renamed trapz -> trapezoid; support both.
_trapz: Callable[..., Any] = next(
    getattr(np, name) for name in ("trapezoid", "trapz") if hasattr(np, name)
)

_MEAN_CHANNELS = ("thrust", "pc", "of", "isp", "cstar", "gamma", "t_c")

#: Pc fraction (vs Pc at LRO) closing the transition phase.
TRANSITION_PC_FRACTION = 0.5


@dataclass(frozen=True)
class PhaseStats:
    """Statistics of one burn phase."""

    name: str
    t_start_s: float
    t_end_s: float
    means: dict[str, float]
    impulse_ns: float
    impulse_share: float  #: fraction of total impulse [-]
    time_share: float  #: fraction of burn time [-]


def _phase_stats(
    history: TimeHistory, mask: np.ndarray, name: str, impulse_total: float, burn_time: float
) -> PhaseStats:
    t = history["t"]
    if mask.sum() < 2:
        return PhaseStats(
            name,
            float("nan"),
            float("nan"),
            {c: float("nan") for c in _MEAN_CHANNELS},
            0.0,
            0.0,
            0.0,
        )
    thrust = history["thrust"][mask]
    t_phase = t[mask]
    impulse = float(_trapz(thrust, t_phase))
    means = {
        channel: float(history[channel][mask].mean())
        for channel in _MEAN_CHANNELS
        if channel in history.channels
    }
    return PhaseStats(
        name=name,
        t_start_s=float(t_phase[0]),
        t_end_s=float(t_phase[-1]),
        means=means,
        impulse_ns=impulse,
        impulse_share=impulse / impulse_total if impulse_total else 0.0,
        time_share=(t_phase[-1] - t_phase[0]) / burn_time if burn_time else 0.0,
    )


def split_phases(
    history: TimeHistory,
    lro_time_s: float | None,
    transition_pc_fraction: float = TRANSITION_PC_FRACTION,
) -> list[PhaseStats]:
    """Segment the burn into liquid / transition / gas phases."""
    t = history["t"]
    impulse_total = float(_trapz(history["thrust"], t))
    burn_time = float(t[-1] - t[0])

    if lro_time_s is None:  # never left liquid phase
        return [_phase_stats(history, np.ones_like(t, bool), "liquid", impulse_total, burn_time)]

    pc_at_lro = float(np.interp(lro_time_s, t, history["pc"]))
    after = t >= lro_time_s
    below = history["pc"] <= transition_pc_fraction * pc_at_lro
    gas_start_candidates = t[after & below]
    gas_start = float(gas_start_candidates[0]) if gas_start_candidates.size else float(t[-1])

    masks = {
        "liquid": t < lro_time_s,
        "transition": (t >= lro_time_s) & (t < gas_start),
        "gas": t >= gas_start,
    }
    return [
        _phase_stats(history, mask, name, impulse_total, burn_time) for name, mask in masks.items()
    ]
