"""Tests for hyprop.cea: interface, cache, and Cantera cross-validation.

The Cantera benchmark anchors the backend to the user's validated script
``07_cantera_punkt0_termochemia.py`` (paraffin C32H66 / N2O, Pc = 35 bar,
O/F = 6.5): Tc = 3292 K, gamma = 1.245, ideal-formula c* = 1589 m/s,
Isp_ideal (expansion to 1 atm) = 247 s.
"""

import pytest

from hyprop.cea.backend import CEAResult, ExpansionResult, StationState

cantera = pytest.importorskip("cantera", reason="Cantera not installed")

from hyprop.cea.cache import CachedBackend                     # noqa: E402
from hyprop.cea.cantera_backend import CanteraBackend          # noqa: E402

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
    ideal = cstar_ideal(
        chamber.gamma, chamber.r_specific_j_kg_k, chamber.temperature_k
    )
    assert ideal == pytest.approx(1589.0, rel=0.01)          # user's number
    excess = result.cstar_m_s / ideal - 1.0
    assert 0.0 < excess < 0.04                               # equilibrium gain


def test_throat_state_is_physical(result):
    # p*/p0 ~ (2/(g+1))^(g/(g-1)) ~ 0.555 for gamma ~ 1.25
    assert result.throat.pressure_pa == pytest.approx(0.55 * PC, rel=0.15)
    assert result.throat.temperature_k < result.chamber.temperature_k


def test_equilibrium_isp_bounds_frozen(result):
    isp_eq = result.isp_s(PA, mode="equilibrium")
    isp_fr = result.isp_s(PA, mode="frozen")
    assert isp_eq > isp_fr                      # D6: frozen is lower bound
    assert (isp_eq - isp_fr) / isp_eq < 0.08    # small motor: few percent


def test_isp_close_to_user_reference(backend):
    # User's script: shifting-equilibrium expansion to exactly 1 atm
    # -> Isp_ideal = 247 s.
    result = backend.query(of=OF, pc=PC, eps=5.7)
    isp = result.isp_s(PA, mode="equilibrium")
    assert isp == pytest.approx(247.0, rel=0.02)


def test_exit_pressure_decreases_with_eps(backend):
    r4 = backend.query(of=OF, pc=PC, eps=4.0)
    r8 = backend.query(of=OF, pc=PC, eps=8.0)
    assert r8.equilibrium.exit_state.pressure_pa < \
        r4.equilibrium.exit_state.pressure_pa


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
