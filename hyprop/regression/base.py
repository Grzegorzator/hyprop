"""Fuel regression model interface (stage E4).

A regression model converts the port mass flux ``G`` [kg/(m^2*s)] into a
surface regression rate ``rdot`` [m/s]. The flux definition is part of
the model (decision D4):

* ``flux_basis = "oxidizer"``: G = mdot_ox / A_port. The classical
  convention - almost all published (a, n) pairs, including the HRAP
  database, use G_ox. Default.
* ``flux_basis = "total"``: G = (mdot_ox + mdot_fuel) / A_port.
  Physically more complete (boundary layer sees total flux; Marxman's
  original theory), but requires coefficients fitted to G_total and an
  extra iteration in the solver (mdot_fuel depends on rdot).

The solver (E6) reads ``flux_basis`` and supplies the matching flux.

Sources: Marxman & Gilbert 1963; Karabeyoglu et al., JPP 2001-2004;
Chiaverini & Kuo (eds.), *Fundamentals of Hybrid Rocket Combustion and
Propulsion*, AIAA 2007; HRAP Theory Eq. 11.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from hyprop.core.exceptions import ConfigError


class RegressionModel(ABC):
    """Maps port mass flux (and grain length) to regression rate."""

    #: Flux definition expected by this model instance ("oxidizer"|"total").
    flux_basis: str = "oxidizer"

    @abstractmethod
    def rdot(self, g_flux: float, grain_length_m: float) -> float:
        """Regression rate [m/s].

        Parameters
        ----------
        g_flux:
            Port mass flux [kg/(m^2*s)] consistent with :attr:`flux_basis`.
        grain_length_m:
            Grain length [m] (used by laws with an L^m term).
        """

    @staticmethod
    def validate_flux_basis(flux_basis: str) -> str:
        if flux_basis not in ("oxidizer", "total"):
            raise ConfigError(f"flux_basis must be 'oxidizer' or 'total', got {flux_basis!r}.")
        return flux_basis
