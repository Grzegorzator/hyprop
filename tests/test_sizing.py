"""Tests for atmosphere, nozzle sizing and inverse sizing (stubbed CEA)."""

import math

import pytest

import hyprop.simulation.solver as solver_module
from hyprop.nozzle.sizing import design_altitude_from_apogee, size_nozzle
from hyprop.oppoints.design_points import OperatingPoint
from hyprop.physics import atmosphere


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
    design = size_nozzle(point, thrust_target_n=500.0, design_altitude_m=1000.0)
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
        return CEAResult(
            of=of,
            pc_pa=pc,
            eps=eps,
            chamber=chamber,
            throat=throat,
            equilibrium=ExpansionResult(exit_s, 2150.0),
            frozen=ExpansionResult(exit_s, 2100.0),
            cstar_m_s=1550.0,
            backend="stub",
        )


def test_inverse_sizing_converges(monkeypatch):
    monkeypatch.setattr(solver_module, "_build_cea_table", lambda config, eps: _StubCEA())
    from hyprop.sizing import size_engine
    from hyprop.sizing.preliminary import SizingOptions

    sized = size_engine(
        thrust_n=500.0,
        total_impulse_ns=4000.0,
        apogee_m=3000.0,
        # the stub thermochemistry is O/F-independent: no optimum to find
        options=SizingOptions(nozzle_from_cea=False, of_design=6.97),
    )
    achieved = sized.achieved
    assert achieved["thrust_iw_n"] == pytest.approx(500.0, rel=0.05)
    assert achieved["total_impulse_ns"] == pytest.approx(4000.0, rel=0.05)
    # the loop holds the impulse-weighted O/F at the requested target:
    assert achieved["of_target"] == 6.97
    assert achieved["of_iw"] == pytest.approx(6.97, rel=0.02)
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


def test_inverse_sizing_does_not_mutate_options(monkeypatch):
    """The refinement loop used to rescale opts.orifice_diameter_m in place,
    so re-using one SizingOptions object gave a different second design."""
    monkeypatch.setattr(solver_module, "_build_cea_table", lambda config, eps: _StubCEA())
    from hyprop.sizing import size_engine
    from hyprop.sizing.preliminary import SizingOptions

    opts = SizingOptions(nozzle_from_cea=False, of_design=6.97)
    before = dict(vars(opts))
    size_engine(thrust_n=500.0, total_impulse_ns=4000.0, apogee_m=3000.0, options=opts)
    assert vars(opts) == before


class _ParabolaCEA:
    """Isp(O/F) = 250 - (O/F - 7.3)^2: optimum known exactly."""

    def query(self, of, pc, eps):
        class R:
            def isp_s(self, pa):
                return 250.0 - (of - 7.3) ** 2

        return R()


def test_optimal_of_finds_known_maximum():
    from hyprop.sizing.mixture import optimal_of

    assert optimal_of(_ParabolaCEA(), 32e5, 5.0, 101325.0) == pytest.approx(7.3, abs=0.01)


def test_optimal_of_pe_n2o_matches_nasa_cea():
    """Reference: NASA CEA (RocketCEA 1.2.3, this repo's LDPE/N2O data) gives
    the Isp-optimal O/F 7.93 at Pc 32 bar, eps 5.31, pa = ISA 1000 m; at
    25-35 bar, eps 5 the optimum is 7.75-8.0 (session check, 2026-10-14)."""
    pytest.importorskip("cantera")
    from hyprop.cea.cantera_backend import CanteraBackend
    from hyprop.sizing.mixture import optimal_of

    cea = CanteraBackend(fuel="ldpe", oxidizer="n2o")
    of = optimal_of(cea, 32e5, 5.31, atmosphere.pressure(1000.0), grid_step=0.5)
    assert of == pytest.approx(7.93, abs=0.1)
