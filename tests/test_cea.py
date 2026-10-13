"""Tests for hyprop.cea: interface, cache, and Cantera cross-validation.

The Cantera benchmark anchors the backend to the user's validated script
``07_cantera_punkt0_termochemia.py`` (paraffin C32H66 / N2O, Pc = 35 bar,
O/F = 6.5): Tc = 3292 K, gamma = 1.245, ideal-formula c* = 1589 m/s,
Isp_ideal (expansion to 1 atm) = 247 s.
"""

import pytest

cantera = pytest.importorskip("cantera", reason="Cantera not installed")

from hyprop.cea.cache import CachedBackend  # noqa: E402
from hyprop.cea.cantera_backend import CanteraBackend  # noqa: E402

PC = 35e5
OF = 6.5
PA = 1.013e5


@pytest.fixture(scope="module")
def backend():
    return CanteraBackend(fuel="paraffin", oxidizer="n2o")


@pytest.fixture(scope="module")
def result(backend):
    return backend.query(of=OF, pc=PC, eps=6.0)


def test_chamber_matches_user_reference(result):
    assert result.chamber.temperature_k == pytest.approx(3292.0, rel=0.01)
    assert result.chamber.gamma == pytest.approx(1.245, rel=0.02)


def test_cstar_vs_user_ideal_formula(result):
    """User's script uses the ideal-c* formula on chamber (frozen) props
    -> 1589 m/s. The backend computes true shifting-equilibrium c*
    (pc / (rho_t * u_t)), which recombination raises by ~1-3% (as CEA).
    """
    from hyprop.physics.compressible import cstar_ideal

    chamber = result.chamber
    ideal = cstar_ideal(chamber.gamma, chamber.r_specific_j_kg_k, chamber.temperature_k)
    assert ideal == pytest.approx(1589.0, rel=0.01)  # user's number
    excess = result.cstar_m_s / ideal - 1.0
    assert 0.0 < excess < 0.04  # equilibrium gain


def test_throat_state_is_physical(result):
    # p*/p0 ~ (2/(g+1))^(g/(g-1)) ~ 0.555 for gamma ~ 1.25
    assert result.throat.pressure_pa == pytest.approx(0.55 * PC, rel=0.15)
    assert result.throat.temperature_k < result.chamber.temperature_k


def test_equilibrium_isp_bounds_frozen(result):
    isp_eq = result.isp_s(PA, mode="equilibrium")
    isp_fr = result.isp_s(PA, mode="frozen")
    assert isp_eq > isp_fr  # D6: frozen is lower bound
    assert (isp_eq - isp_fr) / isp_eq < 0.08  # small motor: few percent


def test_isp_close_to_user_reference(backend):
    # User's script: shifting-equilibrium expansion to exactly 1 atm
    # -> Isp_ideal = 247 s.
    result = backend.query(of=OF, pc=PC, eps=5.7)
    isp = result.isp_s(PA, mode="equilibrium")
    assert isp == pytest.approx(247.0, rel=0.02)


def test_exit_pressure_decreases_with_eps(backend):
    r4 = backend.query(of=OF, pc=PC, eps=4.0)
    r8 = backend.query(of=OF, pc=PC, eps=8.0)
    assert r8.equilibrium.exit_state.pressure_pa < r4.equilibrium.exit_state.pressure_pa


def test_major_species_present(result):
    for species in ("N2", "H2O", "CO"):
        assert species in result.mole_fractions


def test_cache_hits(backend):
    cached = CachedBackend(backend)
    a = cached.query(OF, PC, 6.0)
    b = cached.query(OF, PC, 6.0)
    assert a is b
    assert cached.hits == 1 and cached.misses == 1
    assert len(cached) == 1


def test_gamma_definitions_frozen_and_equilibrium():
    """B3: StationState.gamma is frozen cp/cv, gamma_eq is CEA's GAMMAs.

    Reference values: NASA CEA via RocketCEA for C32H66/N2O at the same
    point (gamma_fr 1.2472, gamma_s 1.1669) - see docs/VALIDATION.md.
    """
    from hyprop.cea.cantera_backend import CanteraBackend

    r = CanteraBackend(fuel="paraffin", oxidizer="n2o").query(6.5, 35e5, 5.0)
    assert r.chamber.gamma == pytest.approx(1.2472, abs=2e-3)
    assert r.chamber.gamma_eq == pytest.approx(1.1669, abs=2e-3)
    assert r.frozen.exit_state.gamma_eq is None


def test_backends_agree_on_both_gammas():
    pytest.importorskip("rocketcea")
    from hyprop.cea.cantera_backend import CanteraBackend
    from hyprop.cea.rocketcea_backend import RocketCEABackend

    a = CanteraBackend(fuel="hdpe", oxidizer="n2o").query(6.0, 30e5, 5.0)
    b = RocketCEABackend(fuel="hdpe", oxidizer="n2o").query(6.0, 30e5, 5.0)
    assert a.chamber.gamma == pytest.approx(b.chamber.gamma, rel=2e-3)
    assert a.chamber.gamma_eq == pytest.approx(b.chamber.gamma_eq, rel=2e-3)
    assert a.cstar_m_s == pytest.approx(b.cstar_m_s, rel=5e-3)


def test_pe_n2o_matches_nasa_cea():
    """PE (ldpe, dHf Splitstone & Johnson 1974) / N2O, O/F 6.5, 35 bar.

    Reference: NASA CEA Python package `cea` 3.3.4, reactant '(CH2)x(cr)'
    with the chamber enthalpy built from HyProp's dHf (same problem), see
    validation/readme_claims.py::pe_thermochemistry. Values: Tc 3276.2 K,
    c* 1615.8 m/s, gamma_s 1.1672, frozen gamma 1.2471.
    """
    from hyprop.cea.cantera_backend import CanteraBackend

    r = CanteraBackend(fuel="ldpe", oxidizer="n2o").query(6.5, 35e5, 5.0)
    assert r.chamber.temperature_k == pytest.approx(3276.2, rel=2e-3)
    assert r.cstar_m_s == pytest.approx(1615.8, rel=2e-3)
    assert r.chamber.gamma_eq == pytest.approx(1.1672, rel=2e-3)
    assert r.chamber.gamma == pytest.approx(1.2471, rel=2e-3)


def test_carbon_to_oxygen_validity_flag():
    """Cantera (gri30) has no C(gr): flag C/O >= 1. PE/N2O: C/O = 1 at
    O/F ~3.14 (NASA CEA shows C(gr) at O/F 3, not at 3.2)."""
    from hyprop.cea.cantera_backend import carbon_to_oxygen_ratio
    from hyprop.data import load_fuel, load_oxidizer

    pe, n2o = load_fuel("ldpe"), load_oxidizer("n2o")
    assert carbon_to_oxygen_ratio(pe, n2o, 3.0) > 1.0
    assert carbon_to_oxygen_ratio(pe, n2o, 3.2) < 1.0
    assert carbon_to_oxygen_ratio(pe, n2o, 3.0) == pytest.approx(
        (1 / 14.0266e-3) / (3.0 / 44.0128e-3), rel=1e-3
    )
