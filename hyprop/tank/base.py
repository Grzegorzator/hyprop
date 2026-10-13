"""Tank / feed-system model interface (stage E5).

A tank model advances the oxidizer supply state by one time step given
the mass drawn through the injector, and exposes the upstream
:class:`FluidState` the injector model needs.

Decision D2 (2026-07-16): default model is the thermodynamic-equilibrium
adiabatic blowdown (HRAP/Whitmore); non-equilibrium Zilliac-Karabeyoglu
is a planned extension behind this same interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class FluidState:
    """Injector-upstream fluid state."""

    pressure_pa: float
    temperature_k: float
    density_kg_m3: float
    vapor_pressure_pa: float
    #: 'liquid' | 'vapor' - what currently leaves the tank.
    phase: str = "liquid"
    enthalpy_j_kg: float | None = None
    entropy_j_kg_k: float | None = None


@dataclass(frozen=True)
class TankState:
    """Tank contents state reported after each step."""

    time_s: float
    pressure_pa: float
    temperature_k: float
    mass_liquid_kg: float
    mass_vapor_kg: float
    fluid: FluidState

    @property
    def mass_total_kg(self) -> float:
        return self.mass_liquid_kg + self.mass_vapor_kg

    @property
    def liquid_depleted(self) -> bool:
        """Liquid run-out (LRO) - transition to the gas phase."""
        return self.mass_liquid_kg <= 0.0

    @property
    def empty(self) -> bool:
        return self.mass_total_kg <= 0.0


class TankModel(ABC):
    """Advances tank thermodynamics under outflow."""

    @abstractmethod
    def state(self) -> TankState:
        """Current tank state (without advancing time)."""

    @abstractmethod
    def step(self, dt: float, mdot_out: float) -> TankState:
        """Advance by ``dt`` [s] with outflow ``mdot_out`` [kg/s]."""
