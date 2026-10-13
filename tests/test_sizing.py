"""Tests for atmosphere, nozzle sizing and inverse sizing (stubbed CEA)."""

import math

import pytest

import hyprop.simulation.solver as solver_module
from hyprop.oppoints.design_points import OperatingPoint
from hyprop.physics import atmosphere
from hyprop.nozzle.sizing import design_altitude_from_apogee, size_nozzle


def test_isa_reference_values():
    # ISO 2533 tables: p(0)=101325, p(1000)=89876, p(3000)=70121, p(11000)=22632
    assert atmosphere.pressure(0.0) == pytest.approx(101325.0)
    assert atmosphere.pressure(1000.0) == pytest.approx(89876.0, rel=1e-3)
    assert atmosphere.pressure(3000.0) == pytest.approx(70121.0, rel=1e-3)
    assert atmosphere.pressure(11000.0) == pytest.approx(22632.0, rel=1e-3)
    assert atmosphere.temperature(3000.0) == pytest.approx(268.65, abs=0.01)
    assert atmosphere.density(0.0) == pytest.approx(1.225, rel=1e-3)


def test_nozzle_sizing_roundtrip():
    point = OperatingPoint("iw", {"pc": 31.3e5, "gamma": 1.25})
    design = size_nozzle(point, thrust_target_n=500.0,
                         design_altitude_m=1000.0)
    # exit pressure adapted to 1000 m ISA:
    assert design.exit_pressure_pa == pytest.approx(89876.0, rel=1e-3)
    # thrust recovered: F = Cf * pc * At
    at = math.pi * (design.throat_diameter_m / 2) ** 2
    assert design.cf_design * 31.3e5 * at == pytest.approx(500.0, rel=1e-9)
    assert design.expansion_ratio > 4.0
    assert not design.separation_risk


def test_design_altitude_heuristic():
    assert design_altitude_from_apogee(3000.0) == pytest.approx(1000.0)


class _StubCEA:
    of_range = (2.0, 14.0)
    pc_range = (1.5e5, 60e5)

    def query(self, of, pc, eps):
        from hyprop.cea.backend import CEAResult, ExpansionResult, StationState
        chamber = StationState(3300.0, pc, 1.25, 0.0265, 1900.0)
        throat = StationState(3100.0, 0.55 * pc, 1.25, 0.0265)
        exit_s = StationState(1800.0, 0.5e5, 1.28, 0.0265)
        return CEAResult(of=of, pc_pa=pc, eps=eps, chamber=chamber,
                         throat=throat,
                         equilibrium=ExpansionResult(exit_s, 2150.0),
                         frozen=ExpansionResult(exit_s, 2100.0),
                         cstar_m_s=1550.0, backend="stub")


def test_inverse_sizing_converges(monkeypatch):
    monkeypatch.setattr(solver_module, "_build_cea_table",
                        lambda config, eps: _StubCEA())
    from hyprop.sizing import size_engine
    from hyprop.sizing.preliminary import SizingOptions

    sized = size_engine(thrust_n=500.0, total_impulse_ns=4000.0,
                        apogee_m=3000.0,
                        options=SizingOptions(nozzle_from_cea=False))
    achieved = sized.achieved
    assert achieved["thrust_iw_n"] == pytest.approx(500.0, rel=0.05)
    assert achieved["total_impulse_ns"] == pytest.approx(4000.0, rel=0.05)
    # nozzle adapted at ~1000 m for the 3 km mission:
    assert sized.nozzle.design_altitude_m == pytest.approx(1000.0)
    assert sized.config.grain.length_m > 0.1
    assert sized.config.tank.oxidizer_mass_kg > 0.5


def test_nozzle_eps_from_cea_matches_equilibrium_expansion():
    """eps from the CEA expansion: pe(eps) = pa at the design altitude.
    Reference: CEA/Cantera eps_opt = 5.14 for C32H66/N2O, 35 bar, O/F 6.5,
    pa = 1.013 bar (docs/VALIDATION.md); ideal frozen-gamma formula: 4.99."""
    pytest.importorskip("cantera")
    from hyprop.cea.cantera_backend import CanteraBackend
    from hyprop.oppoints.design_points import OperatingPoint

    cea = CanteraBackend(fuel="paraffin", oxidizer="n2o")
    point = OperatingPoint("d", {"pc": 35e5, "of": 6.5, "gamma": 1.247})
    nz = size_nozzle(point, 500.0, design_altitude_m=0.0, cea=cea)
    r = cea.query(6.5, 35e5, nz.expansion_ratio)
    assert r.equilibrium.exit_state.pressure_pa == pytest.approx(101325.0, rel=1e-3)
    assert nz.expansion_ratio == pytest.approx(5.14, abs=0.02)
