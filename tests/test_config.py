"""Tests for hyprop.core.config (EngineConfig)."""

import pytest

from hyprop.core.config import CONFIG_VERSION, EngineConfig
from hyprop.core.exceptions import ConfigError

MINIMAL = {
    "name": "test_engine",
    "mission": {"thrust_n": 1000.0, "burn_time_s": 7.0},
    "oxidizer": {"name": "n2o", "temperature_k": 293.15},
    "fuel": {"name": "hdpe"},
    "grain": {
        "geometry": "cylindrical",
        "length_m": 0.30,
        "outer_diameter_m": 0.08,
        "port": {"initial_diameter_m": 0.03},
    },
}


def test_minimal_config_validates():
    config = EngineConfig.from_dict(MINIMAL)
    assert config.version == CONFIG_VERSION
    assert config.mission.thrust_n == pytest.approx(1000.0)
    assert config.injector.model == "spi"  # defaults applied


def test_unit_strings_are_parsed():
    raw = dict(MINIMAL)
    raw["mission"] = {"thrust_n": "1 kN", "burn_time_s": "7 s"}
    raw["oxidizer"] = {"name": "n2o", "tank_pressure_pa": "50 bar"}
    config = EngineConfig.from_dict(raw)
    assert config.mission.thrust_n == pytest.approx(1000.0)
    assert config.oxidizer.tank_pressure_pa == pytest.approx(5.0e6)


def test_missing_impulse_and_time_rejected():
    raw = dict(MINIMAL)
    raw["mission"] = {"thrust_n": 1000.0}
    with pytest.raises(ConfigError):
        EngineConfig.from_dict(raw)


def test_unknown_key_rejected():
    raw = dict(MINIMAL)
    raw["grain"] = dict(MINIMAL["grain"], lenght_m=0.3)  # typo
    with pytest.raises(ConfigError):
        EngineConfig.from_dict(raw)


def test_unsupported_version_rejected():
    raw = dict(MINIMAL, version="9.9")
    with pytest.raises(ConfigError):
        EngineConfig.from_dict(raw)


def test_yaml_roundtrip(tmp_path):
    config = EngineConfig.from_dict(MINIMAL)
    path = tmp_path / "engine.yaml"
    config.to_yaml(path)
    reloaded = EngineConfig.from_yaml(path)
    assert reloaded == config


def test_port_parameters_accept_unit_strings():
    """Regression: '28 mm' in grain.port reached the geometry as a string."""
    from hyprop.core.config import GrainSpec

    g = GrainSpec(length_m="450 mm", outer_diameter_m="5 cm",
                  port={"initial_diameter_m": "28 mm"})
    assert g.port["initial_diameter_m"] == pytest.approx(0.028)
