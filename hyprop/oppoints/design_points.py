"""Representative design points of a blowdown burn (stage E7).

Points produced (user specification):

* **peak_performance** - envelope of maxima (Pc, F, Tc, heat-flux proxy)
  with their times; for structural/thermal/material sizing.
* **impulse_weighted** - thrust-weighted averages of all channels; THE
  primary design point (nozzle, expansion, reported performance).
* **heat_load** - instantaneous state at maximum heat-flux proxy
  (Bartz: q ~ Pc^0.8); graphite/erosion/cooling analysis.
* **mass_flow** - mdot-weighted averages; injector/valve/line sizing.
* **median_impulse** - instantaneous state at the moment 50% of total
  impulse has been delivered.
* **percentile p** - instantaneous states at 10/25/50/75/90/95/99% of
  cumulative impulse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np

from hyprop.core.state import TimeHistory
from hyprop.oppoints.averaging import averages_all_channels

PERCENTILES_DEFAULT = (10.0, 25.0, 50.0, 75.0, 90.0, 95.0, 99.0)


@dataclass(frozen=True)
class OperatingPoint:
    """One representative operating point."""

    name: str
    values: Dict[str, float]
    #: Time [s] the point corresponds to (None for weighted averages).
    time_s: Optional[float] = None
    description: str = ""
    recommended_for: Sequence[str] = field(default_factory=tuple)

    def __getitem__(self, channel: str) -> float:
        return self.values[channel]


def _state_at_time(history: TimeHistory, time_s: float) -> Dict[str, float]:
    """All channels linearly interpolated at ``time_s``."""
    t = history["t"]
    return {
        channel: float(np.interp(time_s, t, history[channel]))
        for channel in history.channels if channel != "t"
    }


def _cumulative_impulse(history: TimeHistory):
    t = history["t"]
    thrust = history["thrust"]
    cumulative = np.concatenate(
        ([0.0], np.cumsum(0.5 * (thrust[1:] + thrust[:-1]) * np.diff(t)))
    )
    return t, cumulative


def time_at_impulse_fraction(history: TimeHistory, fraction: float) -> float:
    """Time [s] at which ``fraction`` of total impulse was delivered."""
    if not (0.0 < fraction < 1.0):
        raise ValueError("fraction must be in (0, 1).")
    t, cumulative = _cumulative_impulse(history)
    return float(np.interp(fraction * cumulative[-1], cumulative, t))


def time_share_for_impulse(history: TimeHistory, fraction: float) -> float:
    """Fraction of burn time needed to deliver ``fraction`` of impulse."""
    t = history["t"]
    return time_at_impulse_fraction(history, fraction) / float(t[-1])


def peak_performance_point(history: TimeHistory) -> OperatingPoint:
    """Envelope of channel maxima (each with its own instant)."""
    values: Dict[str, float] = {}
    t = history["t"]
    for channel in ("pc", "thrust", "t_c"):
        idx = int(np.argmax(history[channel]))
        values[f"{channel}_max"] = float(history[channel][idx])
        values[f"{channel}_max_time_s"] = float(t[idx])
    # convenience: full state at the Pc maximum (structural design case)
    values.update(_state_at_time(history, values["pc_max_time_s"]))
    return OperatingPoint(
        name="peak_performance", values=values,
        time_s=values["pc_max_time_s"],
        description="Envelope of maxima; state at max Pc.",
        recommended_for=("structural analysis", "material selection",
                         "safety factors"),
    )


def impulse_weighted_point(history: TimeHistory) -> OperatingPoint:
    """Thrust-weighted averages - the primary design point."""
    return OperatingPoint(
        name="impulse_weighted",
        values=averages_all_channels(history, "thrust"),
        description="Thrust-weighted averages (impulse-representative).",
        recommended_for=("nozzle design", "expansion ratio",
                         "reported performance"),
    )


def heat_load_point(history: TimeHistory) -> OperatingPoint:
    """State at the maximum of the Bartz heat-flux proxy (Pc^0.8)."""
    proxy = np.maximum(history["pc"], 0.0) ** 0.8
    idx = int(np.argmax(proxy))
    time_s = float(history["t"][idx])
    return OperatingPoint(
        name="heat_load", values=_state_at_time(history, time_s),
        time_s=time_s,
        description="State at max heat-flux proxy (Bartz ~ Pc^0.8).",
        recommended_for=("thermal analysis", "graphite/erosion", "cooling"),
    )


def mass_flow_point(history: TimeHistory) -> OperatingPoint:
    """mdot-weighted averages - feed system design point."""
    return OperatingPoint(
        name="mass_flow", values=averages_all_channels(history, "mdot"),
        description="Mass-flow-weighted averages.",
        recommended_for=("injector design", "valves", "feed lines"),
    )


def median_impulse_point(history: TimeHistory) -> OperatingPoint:
    """Instantaneous state at 50% of delivered impulse."""
    time_s = time_at_impulse_fraction(history, 0.5)
    return OperatingPoint(
        name="median_impulse", values=_state_at_time(history, time_s),
        time_s=time_s,
        description="State at the median-impulse instant.",
        recommended_for=("sanity checks", "mid-burn reference"),
    )


def percentile_points(
    history: TimeHistory,
    percentiles: Sequence[float] = PERCENTILES_DEFAULT,
) -> List[OperatingPoint]:
    """Instantaneous states at given cumulative-impulse percentiles."""
    points = []
    for percentile in percentiles:
        time_s = time_at_impulse_fraction(history, percentile / 100.0)
        points.append(OperatingPoint(
            name=f"impulse_p{percentile:g}",
            values=_state_at_time(history, time_s), time_s=time_s,
            description=f"State at {percentile:g}% of total impulse.",
        ))
    return points
