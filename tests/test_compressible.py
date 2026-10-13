"""Tests for hyprop.physics.compressible.

Reference values: standard isentropic-flow tables (gamma = 1.4),
Anderson 'Modern Compressible Flow' App. A; Sutton & Biblarz Ch. 3.
"""

import pytest

from hyprop.physics import compressible as cf


def test_critical_pressure_ratio_gamma_14():
    # Sutton: p*/p0 = 0.5283 for gamma = 1.4
    assert cf.critical_pressure_ratio(1.4) == pytest.approx(0.5283, abs=1e-4)


def test_isentropic_tables_mach_2():
    # Anderson App. A, gamma=1.4, M=2: p0/p=7.824, T0/T=1.8, A/A*=1.6875
    assert 1.0 / cf.pressure_ratio(2.0, 1.4) == pytest.approx(7.824, rel=1e-3)
    assert 1.0 / cf.temperature_ratio(2.0, 1.4) == pytest.approx(1.8, rel=1e-6)
    assert cf.area_ratio(2.0, 1.4) == pytest.approx(1.6875, rel=1e-3)


def test_area_ratio_at_sonic_is_unity():
    assert cf.area_ratio(1.0, 1.25) == pytest.approx(1.0, rel=1e-12)


@pytest.mark.parametrize("mach", [0.3, 0.8, 1.5, 3.0, 5.0])
@pytest.mark.parametrize("gamma", [1.15, 1.25, 1.4])
def test_mach_area_roundtrip(mach, gamma):
    branch = "supersonic" if mach > 1.0 else "subsonic"
    ratio = cf.area_ratio(mach, gamma)
    assert cf.mach_from_area_ratio(ratio, gamma, branch) == pytest.approx(mach, rel=1e-9)


def test_mach_pressure_roundtrip():
    gamma = 1.22
    mach = 2.7
    p_ratio = cf.pressure_ratio(mach, gamma)
    assert cf.mach_from_pressure_ratio(p_ratio, gamma) == pytest.approx(mach, rel=1e-12)


def test_cstar_and_choked_flux_are_consistent():
    # c* = p0 / (mdot/A*) by definition (Sutton Eq. 3-32)
    gamma, r_spec, t0, p0 = 1.24, 320.0, 3300.0, 3.0e6
    cstar = cf.cstar_ideal(gamma, r_spec, t0)
    flux = cf.choked_mass_flux(p0, t0, gamma, r_spec)
    assert cstar == pytest.approx(p0 / flux, rel=1e-12)


def test_optimum_expansion_roundtrip():
    gamma = 1.25
    eps = cf.optimum_expansion_ratio(p0_over_pe=35.0, gamma=gamma)
    assert 1.0 / cf.exit_pressure_ratio(eps, gamma) == pytest.approx(35.0, rel=1e-9)


def test_thrust_coefficient_matched_sutton():
    # Sutton classic example: gamma=1.30, p0/pa=68.05 (1000 psia -> 1 atm),
    # matched optimum expansion -> Cf ~ 1.55 (Fig. 3-6 / Ch. 3 example).
    gamma = 1.30
    pe_over_p0 = 1.0 / 68.05
    eps = cf.optimum_expansion_ratio(68.05, gamma)
    cf_value = cf.thrust_coefficient(gamma, eps, pe_over_p0, pe_over_p0)
    assert cf_value == pytest.approx(1.55, abs=0.02)


def test_vacuum_cf_exceeds_matched():
    gamma, p0_over_pe = 1.25, 50.0
    eps = cf.optimum_expansion_ratio(p0_over_pe, gamma)
    pe = 1.0 / p0_over_pe
    matched = cf.thrust_coefficient(gamma, eps, pe, pe)
    vacuum = cf.thrust_coefficient(gamma, eps, pe, 0.0)
    assert vacuum > matched


def test_exhaust_velocity_matches_cf_route():
    # F/mdot = ve (matched) must equal Cf*p0*A*/mdot = Cf*cstar
    gamma, r_spec, t0 = 1.24, 320.0, 3300.0
    p0_over_pe = 40.0
    pe_over_p0 = 1.0 / p0_over_pe
    eps = cf.optimum_expansion_ratio(p0_over_pe, gamma)
    ve = cf.exhaust_velocity_ideal(gamma, r_spec, t0, pe_over_p0)
    cf_matched = cf.thrust_coefficient(gamma, eps, pe_over_p0, pe_over_p0)
    cstar = cf.cstar_ideal(gamma, r_spec, t0)
    assert ve == pytest.approx(cf_matched * cstar, rel=1e-9)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        cf.area_ratio(-1.0, 1.4)
    with pytest.raises(ValueError):
        cf.temperature_ratio(2.0, 0.99)
    with pytest.raises(ValueError):
        cf.mach_from_area_ratio(0.5, 1.4)
    with pytest.raises(ValueError):
        cf.thrust_coefficient(1.2, 5.0, 1.5, 0.0)
