"""Injector model interface (stage E5, decision D3).

An injector model maps the upstream :class:`~hyprop.tank.FluidState`
and downstream (chamber) pressure to oxidizer mass flow. Default: SPI
(decision D3, 2026-07-16) - consistent with HRAP's dLoss formulation
and the coefficients calibrated for it; NHNE and HEM are available
options for flashing-flow studies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from hyprop.core.exceptions import ConfigError
from hyprop.tank.base import FluidState


class InjectorModel(ABC):
    """Oxidizer mass-flow model of an injector plate."""

    def __init__(
        self,
        discharge_coefficient: float,
        orifice_count: int,
        orifice_area_m2: float,
    ) -> None:
        if not (0.0 < discharge_coefficient <= 1.0):
            raise ConfigError("Cd must be in (0, 1].")
        if orifice_count < 1 or orifice_area_m2 <= 0.0:
            raise ConfigError("Need >= 1 orifice with positive area.")
        self.cd = discharge_coefficient
        self.total_area_m2 = orifice_count * orifice_area_m2

    @abstractmethod
    def mdot(self, upstream: FluidState, p_chamber_pa: float) -> float:
        """Oxidizer mass flow [kg/s]; 0 when p_chamber >= upstream pressure."""

    def _dp(self, upstream: FluidState, p_chamber_pa: float) -> float:
        return max(upstream.pressure_pa - p_chamber_pa, 0.0)
