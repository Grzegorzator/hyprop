"""Tests for hyprop.tank (N2O properties, equilibrium blowdown) and
hyprop.injector (SPI / HEM / NHNE)."""

import math

import pytest

from hyprop.core.exceptions import ConfigError, PropertyRangeError
from hyprop.injector import SPIInjector
from hyprop.tank import ESDU91022, EquilibriumBlowdownTank, FluidState
from hyprop.tank.simple_models import ConstantMdotTank, PressureFedTank

T0 = 293.15


# --------------------------------------------------------- N2O properties
def test_esdu_sanity_at_20C():
    esdu = ESDU91022()
    # Known ballpark values at 20 C (ESDU/NIST): ~50.5 bar, ~773 kg/m^3
    assert esdu.psat(T0) == pytest.approx(50.5e5, rel=0.03)
    assert esdu.rho_liquid(T0) == pytest.approx(773.0, rel=0.03)
    assert esdu.rho_vapor(T0) < esdu.rho_liquid(T0)
    assert esdu.h_vap(T0) > 0
    assert esdu.cp_liquid(T0) > 2000.0


def test_esdu_range_guard():
    esdu = ESDU91022()
    with pytest.raises(PropertyRangeError):
        esdu.psat(320.0)  # above critical


def test_esdu_vs_coolprop_cross_validation():
    pytest.importorskip("CoolProp")
    from hyprop.tank import CoolPropN2O

    cool = CoolPropN2O()
    esdu = ESDU91022()
    for temperature in (263.15, 278.15, 293.15, 303.15):
        assert esdu.psat(temperature) == pytest.approx(cool.psat(temperature), rel=0.015)
        assert esdu.rho_liquid(temperature) == pytest.approx(
            cool.rho_liquid(temperature), rel=0.015
        )
        assert esdu.rho_vapor(temperature) == pytest.approx(cool.rho_vapor(temperature), rel=0.03)
        assert esdu.h_vap(temperature) == pytest.approx(cool.h_vap(temperature), rel=0.05)


# ------------------------------------------------------ equilibrium tank
def _make_tank(mass=5.0, volume=8e-3, temperature=T0):
    return EquilibriumBlowdownTank(
        volume_m3=volume, oxidizer_mass_kg=mass, temperature_k=temperature
    )


def test_tank_initial_state_consistency():
    tank = _make_tank()
    state = tank.state()
    esdu = ESDU91022()
    assert state.pressure_pa == pytest.approx(esdu.psat(T0), rel=1e-9)
    # volume closure: m_l/rho_l + m_v/rho_v = V
    volume = state.mass_liquid_kg / esdu.rho_liquid(T0) + state.mass_vapor_kg / esdu.rho_vapor(T0)
    assert volume == pytest.approx(8e-3, rel=1e-9)
    assert state.fluid.phase == "liquid"


def test_tank_blowdown_cools_and_depressurises():
    tank = _make_tank()
    p0 = tank.state().pressure_pa
    for _ in range(100):
        state = tank.step(dt=0.01, mdot_out=1.0)  # 1 kg drawn total
    assert state.temperature_k < T0
    assert state.pressure_pa < p0
    assert state.mass_total_kg == pytest.approx(4.0, rel=1e-9)
    assert state.mass_liquid_kg < 4.0  # some vaporised


def test_tank_overfill_rejected():
    with pytest.raises(ConfigError):
        EquilibriumBlowdownTank(volume_m3=1e-3, oxidizer_mass_kg=5.0, temperature_k=T0)


def test_tank_lro_and_vapor_phase():
    tank = _make_tank(mass=1.0, volume=2e-3)
    state = tank.state()
    steps = 0
    while not state.liquid_depleted and steps < 20000:
        state = tank.step(dt=0.01, mdot_out=0.5)
        steps += 1
    assert state.liquid_depleted
    p_lro = state.pressure_pa
    state = tank.step(dt=0.01, mdot_out=0.2)
    assert state.fluid.phase == "vapor"
    assert state.pressure_pa < p_lro  # polytropic decay
    assert state.mass_vapor_kg < 1.0


def test_simple_tanks():
    fed = PressureFedTank(
        oxidizer_mass_kg=2.0,
        pressure_pa=5e6,
        temperature_k=T0,
        density_kg_m3=1141.0,
    )
    state = fed.step(dt=1.0, mdot_out=0.5)
    assert state.mass_total_kg == pytest.approx(1.5)
    assert state.pressure_pa == 5e6  # regulated

    const = ConstantMdotTank(oxidizer_mass_kg=2.0, mdot_kg_s=0.4)
    assert const.mdot_kg_s == 0.4


# --------------------------------------------------------------- injector
def _upstream(pressure=50.5e5, density=773.0):
    return FluidState(
        pressure_pa=pressure,
        temperature_k=T0,
        density_kg_m3=density,
        vapor_pressure_pa=pressure,
        phase="liquid",
    )


def test_spi_analytic():
    injector = SPIInjector(
        discharge_coefficient=0.66,
        orifice_count=8,
        orifice_area_m2=math.pi * (0.75e-3) ** 2,
    )
    up = _upstream()
    p_chamber = 35e5
    expected = 0.66 * 8 * math.pi * (0.75e-3) ** 2 * math.sqrt(2 * 773.0 * (50.5e5 - 35e5))
    assert injector.mdot(up, p_chamber) == pytest.approx(expected, rel=1e-12)
    assert injector.mdot(up, 51e5) == 0.0  # reversed dP


def test_hem_below_spi_and_nhne_between():
    pytest.importorskip("CoolProp")
    from hyprop.injector import HEMInjector, NHNEInjector
    from hyprop.tank import CoolPropN2O

    cool = CoolPropN2O()
    args = dict(
        discharge_coefficient=0.66, orifice_count=8, orifice_area_m2=math.pi * (0.75e-3) ** 2
    )
    up = FluidState(
        pressure_pa=cool.psat(T0),
        temperature_k=T0,
        density_kg_m3=cool.rho_liquid(T0),
        vapor_pressure_pa=cool.psat(T0),
        phase="liquid",
        enthalpy_j_kg=cool.h_liquid(T0),
        entropy_j_kg_k=cool.s_liquid(T0),
    )
    p_chamber = 35e5
    spi = SPIInjector(**args).mdot(up, p_chamber)
    hem = HEMInjector(**args).mdot(up, p_chamber)
    nhne = NHNEInjector(**args).mdot(up, p_chamber)
    assert 0.0 < hem < spi  # flashing reduces flow
    assert hem < nhne < spi  # Dyer blend in between
    # saturated upstream: kappa = 1 -> arithmetic mean
    assert nhne == pytest.approx(0.5 * (spi + hem), rel=1e-6)


def test_registry_has_tank_and_injector_models():
    from hyprop.core.registry import autodiscover, list_models

    autodiscover()
    assert "equilibrium_blowdown" in list_models("tank")["tank"]
    assert "spi" in list_models("injector")["injector"]
