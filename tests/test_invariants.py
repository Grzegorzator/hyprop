"""Physical invariants of the transient solver (property-based, Hypothesis).

Stage 1, item 7. Thermochemistry is stubbed (constant c*, ve, pe; see
test_solver._StubCEA) so that hundreds of motors can be simulated; the
invariants concern the coupling and bookkeeping, not the chemistry.

Invariants:
* oxidizer mass leaving the tank equals the integral of mdot_ox
  (exact for the explicit-Euler bookkeeping used by the solver);
* consumed fuel mass equals rho * (V_port(end) - V_port(0)) and matches
  the integral of mdot_fuel to first order in dt;
* exported total impulse equals the integral of thrust;
* the port only grows; no NaN or negative masses; Pc stays between
  ambient and tank pressure while the motor burns;
* results do not depend on the units used in the input file.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

import hyprop.simulation.solver as solver_module  # noqa: E402
from hyprop.cea.backend import CEAResult, ExpansionResult, StationState  # noqa: E402
from hyprop.core.config import EngineConfig  # noqa: E402

DT = 0.01


class _StubCEA:
    """Constant-property thermochemistry (same as tests/test_solver.py)."""

    of_range = (2.0, 14.0)
    pc_range = (1.5e5, 60e5)

    def query(self, of, pc, eps):
        chamber = StationState(3300.0, pc, 1.25, 0.026, 1900.0)
        throat = StationState(3100.0, 0.55 * pc, 1.25, 0.026)
        exit_s = StationState(1800.0, 0.4e5, 1.28, 0.026)
        return CEAResult(
            of=of,
            pc_pa=pc,
            eps=eps,
            chamber=chamber,
            throat=throat,
            equilibrium=ExpansionResult(exit_s, 2200.0),
            frozen=ExpansionResult(exit_s, 2150.0),
            cstar_m_s=1550.0,
            backend="stub",
        )


def _config(port_d, outer_d, length, orifice_d, n_orifice, cd, m_ox, temp, dt=DT, units=False):
    grain = dict(
        geometry="cylindrical",
        length_m=length,
        outer_diameter_m=outer_d,
        port=dict(initial_diameter_m=port_d),
    )
    if units:  # same values, other units
        grain = dict(
            geometry="cylindrical",
            length_m=f"{length * 1e3} mm",
            outer_diameter_m=f"{outer_d * 100} cm",
            port=dict(initial_diameter_m=f"{port_d * 1e3} mm"),
        )
    return EngineConfig.from_dict(
        dict(
            name="invariant",
            mission=dict(thrust_n=500.0, burn_time_s=8.0, ambient_pressure_pa=101325.0),
            oxidizer=dict(name="n2o", temperature_k=temp),
            fuel=dict(name="ldpe"),
            grain=grain,
            tank=dict(model="equilibrium_blowdown", volume_m3=m_ox / 650.0, oxidizer_mass_kg=m_ox),
            injector=dict(
                model="spi",
                discharge_coefficient=cd,
                orifice_count=n_orifice,
                orifice_diameter_m=orifice_d,
            ),
            nozzle=dict(throat_diameter_m=12e-3, expansion_ratio=5.0),
            simulation=dict(dt_s=dt, t_max_s=40.0),
        )
    )


motors = st.fixed_dictionaries(
    dict(
        port_d=st.floats(0.020, 0.035),
        web=st.floats(0.006, 0.015),
        length=st.floats(0.25, 0.60),
        orifice_d=st.floats(1.2e-3, 2.0e-3),
        n_orifice=st.integers(3, 6),
        cd=st.floats(0.55, 0.75),
        m_ox=st.floats(1.0, 3.0),
        temp=st.floats(275.0, 296.0),
    )
)


def _run(m, **kw):
    cfg = _config(
        m["port_d"],
        m["port_d"] + 2 * m["web"],
        m["length"],
        m["orifice_d"],
        m["n_orifice"],
        m["cd"],
        m["m_ox"],
        m["temp"],
        **kw,
    )
    return solver_module.run_simulation(cfg), cfg


@pytest.fixture(autouse=True)
def _stub(monkeypatch):
    monkeypatch.setattr(solver_module, "_build_cea_table", lambda config, eps: _StubCEA())


@settings(
    max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(motors)
def test_mass_and_impulse_bookkeeping(m):
    res, cfg = _run(m)
    h = res.history
    assert len(h) > 10
    for ch in ("thrust", "pc", "m_ox", "m_fuel", "mdot_ox", "mdot_fuel", "d_port"):
        assert np.all(np.isfinite(h[ch])), ch
    assert np.all(h["m_ox"] >= -1e-12) and np.all(h["m_fuel"] >= -1e-12)
    assert np.all(h["mdot_ox"] >= 0) and np.all(h["mdot_fuel"] >= 0)

    # oxidizer: tank decrement == sum(mdot_ox * dt) over the steps taken
    dm_ox = h["m_ox"][0] - h["m_ox"][-1]
    assert dm_ox == pytest.approx(float(np.sum(h["mdot_ox"][:-1]) * DT), rel=1e-9, abs=1e-12)

    # fuel: geometric consumption vs integral of mdot_fuel (first order in dt)
    rho = 920.0
    dv = math.pi / 4 * (h["d_port"][-1] ** 2 - h["d_port"][0] ** 2) * cfg.grain.length_m
    assert h["m_fuel"][0] - h["m_fuel"][-1] == pytest.approx(rho * dv, rel=1e-9)
    assert float(np.sum(h["mdot_fuel"][:-1]) * DT) == pytest.approx(rho * dv, rel=0.02)

    # impulse: exported value is the integral of thrust
    assert res.summary["total_impulse_ns"] == pytest.approx(
        float(np.sum(h["thrust"]) * DT), rel=1e-9
    )
    trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))
    assert res.summary["total_impulse_ns"] == pytest.approx(
        float(trapz(h["thrust"], h["t"])), rel=0.01
    )


@settings(
    max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(motors)
def test_monotonic_port_and_bounded_pressures(m):
    res, _ = _run(m)
    h = res.history
    assert np.all(np.diff(h["d_port"]) >= 0.0)  # port only grows
    assert np.all(np.diff(h["web"]) >= 0.0)
    burning = h["mdot_ox"] > 0
    assert np.all(h["pc"][burning] < h["p_tank"][burning])  # injector flows forward
    assert np.all(h["pc"][burning] > 101325.0)
    of = h["of"][burning & (h["mdot_fuel"] > 0)]
    assert np.all((of > 0.0) & (of < 50.0))  # sane O/F


@settings(
    max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(motors)
def test_input_units_do_not_change_results(m):
    a, _ = _run(m)
    b, _ = _run(m, units=True)
    # mm->m and cm->m conversions differ from the float literal in the last
    # bit; that noise (~1e-16 relative) is amplified only where F -> 0.
    np.testing.assert_allclose(a.history["thrust"], b.history["thrust"], rtol=1e-9, atol=1e-9)
    assert a.summary["total_impulse_ns"] == pytest.approx(b.summary["total_impulse_ns"], rel=1e-10)
