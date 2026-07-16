"""Domain exception hierarchy for HyProp.

Catching :class:`HypropError` catches every error raised by the package.
"""


class HypropError(Exception):
    """Base class for all HyProp errors."""


class ConfigError(HypropError):
    """Invalid, inconsistent or unparseable engine configuration."""


class UnitError(ConfigError):
    """A quantity has wrong dimensionality or an unparseable unit string."""


class DataError(HypropError):
    """Propellant/material database entry is missing or malformed."""


class RegistryError(HypropError):
    """Requested model is not registered or registration is invalid."""


class BackendUnavailableError(HypropError):
    """An optional backend (RocketCEA, Cantera, CoolProp) is not installed."""


class ConvergenceError(HypropError):
    """An iterative solver failed to converge within its budget."""


class PropertyRangeError(HypropError):
    """A property/correlation was queried outside its validity range."""
