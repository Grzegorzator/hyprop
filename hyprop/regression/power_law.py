"""Power-law (Saint-Robert-type) regression: rdot = a * G^n * L^m.

The workhorse empirical law of hybrid propulsion (HRAP Theory Eq. 11).
SI convention throughout HyProp:

    rdot [m/s],  G [kg/(m^2*s)],  L [m]
    =>  a [ (m/s) / (kg/(m^2*s))^n / m^m ]

HRAP database values are published in mm/s basis (confirmed in HRAP
``propellant_template.m``); the ``data/fuels`` YAML entries already store
them converted to SI (a_SI = a_HRAP * 1e-3).

Typical exponents: n = 0.3-0.8 (turbulent boundary-layer heat transfer,
Marxman theory predicts n = 0.8); m usually 0 or slightly negative.
"""

from __future__ import annotations

from hyprop.core.exceptions import ConfigError
from hyprop.core.registry import register_model
from hyprop.regression.base import RegressionModel


@register_model("regression", "power_law")
class PowerLawRegression(RegressionModel):
    """rdot = a * G^n * L^m with configurable flux basis (D4)."""

    def __init__(
        self,
        a: float,
        n: float,
        m: float = 0.0,
        flux_basis: str = "oxidizer",
    ) -> None:
        if a <= 0.0 or n <= 0.0:
            raise ConfigError("Power law requires a > 0 and n > 0.")
        self.a = a
        self.n = n
        self.m = m
        self.flux_basis = self.validate_flux_basis(flux_basis)

    def rdot(self, g_flux: float, grain_length_m: float) -> float:
        if g_flux < 0.0:
            raise ValueError("Mass flux must be non-negative.")
        if g_flux == 0.0:
            return 0.0
        length_term = grain_length_m ** self.m if self.m != 0.0 else 1.0
        return self.a * g_flux**self.n * length_term

    # ------------------------------------------------------- constructors
    @classmethod
    def from_entry(cls, entry) -> "PowerLawRegression":
        """Build from a database :class:`~hyprop.data.RegressionEntry`."""
        return cls(a=entry.a, n=entry.n, m=entry.m,
                   flux_basis=entry.flux_basis)

    @classmethod
    def from_spec(cls, spec) -> "PowerLawRegression":
        """Build from a config :class:`~hyprop.core.config.RegressionSpec`."""
        if spec.a is None or spec.n is None:
            raise ConfigError(
                "RegressionSpec override requires both 'a' and 'n'."
            )
        return cls(a=spec.a, n=spec.n, m=spec.m, flux_basis=spec.flux_basis)

    def __repr__(self) -> str:            # pragma: no cover
        return (f"PowerLawRegression(a={self.a:.3e}, n={self.n}, "
                f"m={self.m}, flux_basis='{self.flux_basis}')")
