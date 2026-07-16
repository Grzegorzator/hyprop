"""Weighted time-averaging of simulation channels (stage E7).

A blowdown hybrid has no single operating point; design parameters are
representative averages. For any channel X(t) and weight w(t):

    X_bar = integral(X * w dt) / integral(w dt)

Weightings (user specification):

* ``time``       - w = 1 (plain time average; misleading for blowdown:
                   the long, weak gas phase drags values down).
* ``thrust``     - w = F(t)  (DEFAULT). Since It = integral(F dt), each
                   instant is weighted by its contribution to total
                   impulse - the natural design weighting.
* ``mdot``       - w = mdot_total(t) (injector/feed design).
* ``heat_flux``  - w = Pc^0.8 (Bartz proxy: h_g ~ Pc^0.8; replaced by a
                   real q_dot channel when the thermal module arrives).
* ``pc``         - w = Pc(t).
* callable       - user-defined w(t, history) -> array.
"""

from __future__ import annotations

from typing import Callable, Dict, Union

import numpy as np

from hyprop.core.state import TimeHistory

WeightSpec = Union[str, Callable[[np.ndarray, TimeHistory], np.ndarray]]

#: Named weight functions: name -> callable(t, history) -> w array.
WEIGHTINGS: Dict[str, Callable] = {
    "time": lambda t, h: np.ones_like(t),
    "thrust": lambda t, h: h["thrust"],
    "mdot": lambda t, h: h["mdot_total"],
    "heat_flux": lambda t, h: np.maximum(h["pc"], 0.0) ** 0.8,
    "pc": lambda t, h: h["pc"],
}


def weight_array(history: TimeHistory, weighting: WeightSpec) -> np.ndarray:
    """Evaluate the weight w(t) for the whole history."""
    t = history["t"]
    if callable(weighting):
        w = np.asarray(weighting(t, history), dtype=float)
    else:
        try:
            w = np.asarray(WEIGHTINGS[weighting](t, history), dtype=float)
        except KeyError:
            raise ValueError(
                f"Unknown weighting '{weighting}'. "
                f"Known: {sorted(WEIGHTINGS)} or a callable."
            ) from None
    if w.shape != t.shape:
        raise ValueError("Weight array must match the time base.")
    if np.all(w <= 0.0):
        raise ValueError("Weight function is non-positive everywhere.")
    return np.maximum(w, 0.0)


def weighted_average(
    history: TimeHistory, channel: str, weighting: WeightSpec = "thrust"
) -> float:
    """X_bar = int(X*w dt) / int(w dt) using trapezoidal integration."""
    t = history["t"]
    x = history[channel]
    w = weight_array(history, weighting)
    denominator = np.trapz(w, t)
    return float(np.trapz(x * w, t) / denominator)


def averages_all_channels(
    history: TimeHistory, weighting: WeightSpec = "thrust"
) -> Dict[str, float]:
    """Weighted average of every recorded channel (except time itself)."""
    return {
        channel: weighted_average(history, channel, weighting)
        for channel in history.channels if channel != "t"
    }
