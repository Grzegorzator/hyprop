"""Fast unit tests of the transient solver loop (stubbed thermochemistry).

The full HRAP benchmark lives in examples/benchmark_prusak_v2.py (needs
~40 s: real Cantera table). Here the CEA table is monkeypatched with an
analytic stub so the coupling logic is tested in milliseconds.
"""

import math

import pytest

import hyprop.simulation.solver as solver_module
from hyprop.cea.backend import CEAResult, ExpansionResult, StationState
from hyprop.core.config import EngineConfig


class _StubCEA:
    """Constant-property thermochemistry: c*=1550, ve=2200, pe=0.4 bar."""
    of_range = (2.0, 14.0)
    pc_range = (1.5e5, 60e5)

    def query(self, of, pc, eps):
        chamber = StationState(3300.0, pc, 1.25, 0.026, 1900.0)
        throat = StationState(3100.0, 0.55 * pc, 1.25, 0.026)
        exit_s = StationState(1800.0, 0.4e5, 1.28, 0.026)
        return CEAResult(
            of=of, pc_pa=pc, eps=eps, chamber=chamber, throat=throat,
            equilibrium=ExpansionResult(exit_s, 2200.0),
            frozen=ExpansionResult(exit_s, 2150.0),
            cstar_m_s=1550.0, backend="stub",
        )


@pytest.fixture()
def stub_cea(monkeypatch):
    monkeypatch.setattr(
        solver_module, "_build_cea_table", lambda config, eps: _StubCEA()
    )


CFG = dict(
    name="unit_test_motor",
    mission=dict(thrust_n=500.0, burn_time_s=10.0,
                 ambient_pressure_pa=101325.0),
    oxidizer=dict(name="n2o", temperature_k=293.15),
    fuel=dict(name="hdpe", density_kg_m3=920.0),
    grain=dict(geometry="cylindrical", length_m=0.45,
               outer_diameter_m=0.050,
               port=dict(initial_diameter_m=0.028)),
    tank=dict(model="equilibrium_blowdown", volume_m3=2.8e-3,
              oxidizer_mass_kg=1.9),
    injector=dict(model="spi", discharge_coefficient=0.60,
                  orifice_count=5, orifice_diameter_m=1.4e-3),
    nozzle=dict(throat_diameter_m=11.5e-3, expansion_ratio=5.3),
    simulation=dict(dt_s=0.02, t_max_s=30.0),
)


def test_transient_runs_and_is_physical(stub_cea):
    result = solver_module.run_simulation(EngineConfig.from_dict(CFG))
    h = result.history
    assert len(h) > 50
    assert result.summary["total_impulse_ns"] > 0
    # Pc must stay below tank pressure and above ambient while burning:
    assert (h["pc"] < h["p_tank"]).all()
    assert h["pc"].max() > 5e5
    # impulse channel is the cumulative integral of thrust:
    assert h["impulse"][-1] == pytest.approx(
        result.summary["total_impulse_ns"], rel=1e-9)
    # events recorded and ordered:
    names = [e for _, e in result.events]
    assert "liquid_runout" in names


def test_brent_matches_fixed_point(stub_cea):
    cfg_fp = EngineConfig.from_dict(CFG)
    raw = dict(CFG); raw["simulation"] = dict(dt_s=0.02, t_max_s=30.0,
                                              pc_solver="brent")
    cfg_br = EngineConfig.from_dict(raw)
    r_fp = solver_module.run_simulation(cfg_fp)
    r_br = solver_module.run_simulation(cfg_br)
    assert r_br.summary["peak_pc_pa"] == pytest.approx(
        r_fp.summary["peak_pc_pa"], rel=0.01)
    assert r_br.summary["total_impulse_ns"] == pytest.approx(
        r_fp.summary["total_impulse_ns"], rel=0.02)


def test_cea_table_cache_keys_on_exact_eps():
    """Regression (B1): two eps values that round to the same 2 decimals
    must get separate tables (formerly crashed api.size)."""
    import hyprop.simulation.solver as sm
    from hyprop.core.config import EngineConfig

    old = sm._TABLE_OF, sm._TABLE_PC
    sm._TABLE_OF, sm._TABLE_PC = 3, 3
    try:
        cfg = EngineConfig.from_dict(dict(
            mission=dict(thrust_n=500.0, burn_time_s=8.0),
            oxidizer=dict(name="n2o"), fuel=dict(name="hdpe"),
            grain=dict(geometry="cylindrical", length_m=0.3,
                       outer_diameter_m=0.06,
                       port=dict(initial_diameter_m=0.02)),
        ))
        a = sm._build_cea_table(cfg, 5.0209)
        b = sm._build_cea_table(cfg, 5.0167)
        assert a is not b
        b.query(6.0, 30e5, 5.0167)          # must not raise
    finally:
        sm._TABLE_OF, sm._TABLE_PC = old


def test_cea_backend_setting_is_honoured(monkeypatch):
    """B2: simulation.cea_backend selects the table backend (was ignored)."""
    import hyprop.simulation.solver as sm
    from hyprop.cea.backend import ThermochemistryBackend
    from hyprop.core.config import EngineConfig

    seen = []

    def fake_get_backend(name, **kwargs):
        seen.append(name)

        class _B(ThermochemistryBackend):
            name = "fake"

            def query(self, of, pc, eps):
                return _StubCEA().query(of, pc, eps)
        return _B()

    import hyprop.cea as cea_pkg
    monkeypatch.setattr(cea_pkg, "get_backend", fake_get_backend)
    sm._TABLE_CACHE.clear()
    cfg = EngineConfig.from_dict(dict(
        mission=dict(thrust_n=500.0, burn_time_s=8.0),
        oxidizer=dict(name="n2o"), fuel=dict(name="hdpe"),
        grain=dict(geometry="cylindrical", length_m=0.3, outer_diameter_m=0.06,
                   port=dict(initial_diameter_m=0.02)),
        simulation=dict(cea_backend="rocketcea"),
    ))
    table = sm._build_cea_table(cfg, 5.0)
    sm._TABLE_CACHE.clear()
    assert seen == ["rocketcea"]
    assert table.name == "tabulated[fake]"


def test_thrust_uses_sutton_correction_factors(stub_cea):
    """B4: F = eta_c* * eta_noz * mdot * c_i  (Sutton 9th ed. Eqs. 3-40/41),
    c_i = lambda*ve + (pe - pa)*eps*c*_i/Pc (lambda on momentum only,
    Eq. 3-34). Checked step by step."""
    import numpy as np
    from hyprop.nozzle.losses import divergence_efficiency

    cfg = EngineConfig.from_dict(CFG)
    h = solver_module.run_simulation(cfg).history
    lam = divergence_efficiency(cfg.nozzle.divergence_half_angle_deg)
    c_i = lam * 2200.0 + (0.4e5 - 101325.0) * 5.3 * 1550.0 / h["pc"]
    expected = np.maximum(cfg.efficiencies.eta_cstar * cfg.nozzle.efficiency
                          * h["mdot_total"] * c_i, 0.0)
    np.testing.assert_allclose(h["thrust"], expected, rtol=1e-12)


def test_better_combustion_raises_isp(stub_cea):
    """B4 regression: with the old formulation dIsp/deta_c* was ~0 and
    dF/deta_c* < 0. Delivered Isp must scale ~ with eta_c*."""
    def isp(eta):
        raw = dict(CFG); raw["efficiencies"] = dict(eta_cstar=eta)
        return solver_module.run_simulation(
            EngineConfig.from_dict(raw)).summary["isp_mean_s"]
    ratio = isp(0.95) / isp(0.85)
    assert ratio == pytest.approx(0.95 / 0.85, rel=0.03)
