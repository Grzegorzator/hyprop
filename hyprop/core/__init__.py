"""Core foundation of HyProp: constants, units, config, registry, logging."""

from hyprop.core.config import CONFIG_VERSION, EngineConfig
from hyprop.core.exceptions import (
    BackendUnavailableError,
    ConfigError,
    ConvergenceError,
    DataError,
    HypropError,
    PropertyRangeError,
    RegistryError,
    UnitError,
)
from hyprop.core.registry import autodiscover, get_model, list_models, register_model
from hyprop.core.state import CHANNELS, TimeHistory
from hyprop.core.units import Q_, to_si, ureg

__all__ = [
    "CONFIG_VERSION",
    "EngineConfig",
    "HypropError",
    "ConfigError",
    "UnitError",
    "DataError",
    "RegistryError",
    "BackendUnavailableError",
    "ConvergenceError",
    "PropertyRangeError",
    "register_model",
    "get_model",
    "list_models",
    "autodiscover",
    "CHANNELS",
    "TimeHistory",
    "ureg",
    "Q_",
    "to_si",
]
