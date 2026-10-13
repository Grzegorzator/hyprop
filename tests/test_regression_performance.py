"""Tests for hyprop.regression, hyprop.nozzle.losses, hyprop.performance."""

import pytest

from hyprop.core.constants import G0
from hyprop.core.exceptions import ConfigError
from hyprop.data import load_fuel
from hyprop.nozzle import divergence_efficiency, nozzle_efficiency
from hyprop.performance import (
    cstar_delivered,
    efficiency,
    specific_impulse,
    thrust,
    thrust_coefficient_delivered,
)
from hyprop.regression import PowerLawRegression


# ------------------------------------------------------------- regression
def test_power_law_hdpe_hrap_value():
    """HDPE/N2O (HRAP): a=0.104 mm/s basis -> at G=100 kg/m^2/s
    rdot = 0.104 * 100^0.352 = 0.526 mm/s."""
    law = PowerLawRegression(a=1.04e-4, n=0.352)
    assert law.rdot(100.0, 0.3) * 1e3 == pytest.approx(0.526, abs=0.002)


def test_power_law_from_database_entry():
    entry = load_fuel("hdpe").regression_for("n2o")[0]
    law = PowerLawRegression.from_entry(entry)
    assert law.flux_basis == "oxidizer"
    assert law.rdot(200.0, 0.3) == pytest.approx(1.04e-4 * 200.0**0.352, rel=1e-12)


def test_power_law_length_exponent():
    law = PowerLawRegression(a=1e-4, n=0.5, m=-0.2)
    ratio = law.rdot(100.0, 0.6) / law.rdot(100.0, 0.3)
    assert ratio == pytest.approx(2.0 ** (-0.2), rel=1e-12)


def test_power_law_zero_flux_and_validation():
    law = PowerLawRegression(a=1e-4, n=0.5)
    assert law.rdot(0.0, 0.3) == 0.0
    with pytest.raises(ValueError):
        law.rdot(-1.0, 0.3)
    with pytest.raises(ConfigError):
        PowerLawRegression(a=-1.0, n=0.5)
    with pytest.raises(ConfigError):
        PowerLawRegression(a=1e-4, n=0.5, flux_basis="banana")


def test_total_flux_basis_flag():
    law = PowerLawRegression(a=1e-4, n=0.62, flux_basis="total")
    assert law.flux_basis == "total"


# ----------------------------------------------------------------- nozzle
def test_divergence_efficiency_15_deg():
    # Sutton Eq. 3-34: lambda(15 deg) = 0.9830
    assert divergence_efficiency(15.0) == pytest.approx(0.9830, abs=1e-4)


def test_nozzle_efficiency_combines():
    assert nozzle_efficiency(15.0, 0.98) == pytest.approx(0.9830 * 0.98, abs=1e-4)
    with pytest.raises(ConfigError):
        nozzle_efficiency(15.0, 1.5)


# ------------------------------------------------------------ performance
def test_thrust_and_identities():
    mdot, ve, pe, pa, ae = 0.5, 2200.0, 60e3, 101325.0, 0.002
    f = thrust(mdot, ve, pe, pa, ae)
    assert f == pytest.approx(0.5 * 2200 + (60e3 - 101325) * 0.002, rel=1e-12)

    pc, at = 3.0e6, 3.0e-4
    cstar = cstar_delivered(pc, at, mdot)
    cf = thrust_coefficient_delivered(f, pc, at)
    # identity: F = cstar * Cf * mdot
    assert cstar * cf * mdot == pytest.approx(f, rel=1e-12)


def test_specific_impulse():
    assert specific_impulse(1000.0, 0.5) == pytest.approx(1000.0 / (0.5 * G0), rel=1e-12)


def test_efficiency_ratio():
    assert efficiency(1550.0, 1626.0) == pytest.approx(0.9533, abs=1e-3)
    with pytest.raises(ValueError):
        efficiency(1.0, 0.0)


def test_registry_has_power_law():
    from hyprop.core.registry import autodiscover, list_models

    autodiscover()
    assert "power_law" in list_models("regression")["regression"]
