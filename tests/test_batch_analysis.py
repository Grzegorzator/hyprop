"""Tests for hyprop.batch and hyprop.analysis (stubbed thermochemistry)."""

import numpy as np
import pytest

import hyprop.simulation.solver as solver_module
from hyprop.batch import apply_overrides, build_grid, build_lhs, run_batch
from hyprop.core.config import EngineConfig
from tests.test_solver import CFG, _StubCEA


@pytest.fixture()
def stub_cea(monkeypatch):
    monkeypatch.setattr(solver_module, "_build_cea_table", lambda config, eps: _StubCEA())


def test_apply_overrides_paths():
    config = EngineConfig.from_dict(CFG)
    out = apply_overrides(
        config,
        {
            "injector.discharge_coefficient": 0.5,
            "grain.port.initial_diameter_m": 0.030,
        },
    )
    assert out.injector.discharge_coefficient == 0.5
    assert out.grain.port["initial_diameter_m"] == 0.030
    assert config.injector.discharge_coefficient == 0.60  # base untouched


def test_build_grid_and_lhs():
    grid = build_grid({"a": [1, 2, 3], "b": [10, 20]})
    assert len(grid) == 6 and grid[0] == {"a": 1, "b": 10}
    lhs = build_lhs({"x": (0.0, 1.0), "y": (100.0, 200.0)}, samples=16)
    xs = np.array([c["x"] for c in lhs])
    assert len(lhs) == 16 and xs.min() >= 0.0 and xs.max() <= 1.0
    # LHS stratification: one sample per 1/16 stratum
    assert len(np.unique((xs * 16).astype(int))) == 16


def test_run_batch_and_failed_case(stub_cea):
    config = EngineConfig.from_dict(CFG)
    cases = [
        {"injector.discharge_coefficient": 0.55},
        {"injector.discharge_coefficient": 0.65},
        {"injector.discharge_coefficient": -1.0},  # invalid -> NaN row
    ]
    frame = run_batch(config, cases, progress=False)
    assert len(frame) == 3
    assert frame["total_impulse_ns"].notna().sum() == 2
    # more Cd -> more mdot -> more impulse (monotone sanity)
    ok = frame.dropna(subset=["total_impulse_ns"])
    assert ok["total_impulse_ns"].iloc[1] > ok["total_impulse_ns"].iloc[0]


def test_oat_sensitivity_signs(stub_cea):
    from hyprop.analysis import oat_sensitivity

    config = EngineConfig.from_dict(CFG)
    table = oat_sensitivity(
        config,
        {"injector.discharge_coefficient": 0.60, "nozzle.throat_diameter_m": 11.5e-3},
        outputs=("total_impulse_ns", "peak_pc_pa"),
        delta=0.05,
    )
    assert table.loc["injector.discharge_coefficient", "peak_pc_pa"] > 0
    assert table.loc["nozzle.throat_diameter_m", "peak_pc_pa"] < 0


def test_monte_carlo_bands(stub_cea):
    from hyprop.analysis import monte_carlo

    config = EngineConfig.from_dict(CFG)
    result = monte_carlo(
        config,
        {"injector.discharge_coefficient": ("normal", 0.60, 0.02)},
        samples=12,
        outputs=("total_impulse_ns",),
    )
    bands = result["bands"]
    assert (
        bands.loc["total_impulse_ns", "p5"]
        <= bands.loc["total_impulse_ns", "p50"]
        <= bands.loc["total_impulse_ns", "p95"]
    )


def test_regime_flags(stub_cea):
    from hyprop.analysis import port_numbers, regime_flags

    result = solver_module.run_simulation(EngineConfig.from_dict(CFG))
    numbers = port_numbers(result.history)
    assert numbers["Re"].max() > 1e5  # clearly turbulent motor
    assert isinstance(regime_flags(result.history), list)
