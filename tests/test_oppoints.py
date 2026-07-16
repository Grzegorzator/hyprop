"""Tests for hyprop.oppoints on an analytic synthetic burn.

Synthetic profile (dt=0.01 s):
  liquid phase 0-8 s: F = 500 N, Pc = 30 bar (constant)
  gas tail 8-12 s:    F, Pc decay linearly to 0
Total impulse = 500*8 + 0.5*500*4 = 5000 Ns; liquid share = 80%.
"""

import numpy as np
import pytest

from hyprop.core.state import TimeHistory
from hyprop.oppoints import (
    analyze,
    split_phases,
    time_at_impulse_fraction,
    weighted_average,
)
from hyprop.simulation.solver import SimulationResult


def _synthetic() -> SimulationResult:
    history = TimeHistory()
    for t in np.arange(0.0, 12.0, 0.01):
        decay = 1.0 if t < 8.0 else max(1.0 - (t - 8.0) / 4.0, 0.0)
        history.record(
            t=t, thrust=500.0 * decay, pc=30e5 * decay,
            of=7.0 * (1.0 if t < 8.0 else 0.5),
            isp=200.0 * decay, cstar=1500.0, gamma=1.25, t_c=3300.0 * decay,
            mdot_ox=0.20 * decay, mdot_fuel=0.03 * decay,
            mdot_total=0.23 * decay,
        )
    return SimulationResult(history=history,
                            events=[(8.0, "liquid_runout")])


@pytest.fixture(scope="module")
def result():
    return _synthetic()


def test_thrust_weighted_exceeds_time_average(result):
    h = result.history
    f_time = weighted_average(h, "thrust", "time")
    f_thrust = weighted_average(h, "thrust", "thrust")
    # time average diluted by the tail; impulse-weighted stays near 500
    assert f_time < f_thrust
    assert f_thrust == pytest.approx(466.7, rel=0.01)   # int(F^2)/int(F)
    assert f_time == pytest.approx(5000.0 / 12.0, rel=0.01)


def test_custom_weight_callable(result):
    h = result.history
    value = weighted_average(h, "pc", lambda t, hh: (t < 8.0).astype(float))
    assert value == pytest.approx(30e5, rel=1e-6)       # liquid-only mean


def test_unknown_weighting_raises(result):
    with pytest.raises(ValueError):
        weighted_average(result.history, "pc", "banana")


def test_median_and_percentile_times(result):
    h = result.history
    # 50% of 5000 Ns = 2500 Ns -> at t = 5 s (constant 500 N)
    assert time_at_impulse_fraction(h, 0.50) == pytest.approx(5.0, abs=0.02)
    # 80% -> 4000 Ns -> exactly at LRO (8 s)
    assert time_at_impulse_fraction(h, 0.80) == pytest.approx(8.0, abs=0.02)
    # 90% -> 4500 Ns -> in the tail
    assert time_at_impulse_fraction(h, 0.90) > 8.0


def test_phase_split_shares(result):
    phases = {p.name: p for p in split_phases(result.history, 8.0)}
    assert phases["liquid"].impulse_share == pytest.approx(0.80, abs=0.01)
    assert phases["liquid"].time_share == pytest.approx(8.0 / 12.0, abs=0.01)
    assert phases["liquid"].means["thrust"] == pytest.approx(500.0, rel=1e-6)
    # transition ends when Pc < 50% of Pc(LRO) -> at t = 10 s
    assert phases["transition"].t_end_s == pytest.approx(10.0, abs=0.05)
    total = sum(p.impulse_share for p in phases.values())
    assert total == pytest.approx(1.0, abs=0.01)


def test_full_report(result):
    report = analyze(result)
    assert set(report.points) == {
        "peak_performance", "impulse_weighted", "heat_load",
        "mass_flow", "median_impulse",
    }
    assert report.point("peak_performance")["pc_max"] == pytest.approx(30e5)
    assert report.for_module("nozzle_design").name == "impulse_weighted"
    assert report.for_module("thermal_analysis").name == "heat_load"
    # 90% of impulse delivered in less time than its share suggests
    # (synthetic tail is fat; real blowdown gives much lower values):
    assert report.time_shares[0.90] == pytest.approx(0.765, abs=0.01)
    assert report.time_shares[0.50] == pytest.approx(5.0 / 12.0, abs=0.01)
    assert len(report.percentiles) == 7
    times = [p.time_s for p in report.percentiles]
    assert times == sorted(times)                       # monotone
    table = report.comparison_table()
    assert "time_average" in table.index
    assert table.loc["impulse_weighted", "thrust"] > \
        table.loc["time_average", "thrust"]
    assert len(report.phases_table()) == 3
