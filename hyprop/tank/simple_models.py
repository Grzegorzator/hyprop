"""Simple feed models: constant pressure (regulated) and constant mdot.

* :class:`PressureFedTank` - regulated supply at constant pressure and
  temperature (e.g. bottle-fed GOX or pressurant-backed liquid). Mass is
  tracked; properties are constant.
* :class:`ConstantMdotTank` - degenerate model for preliminary sizing:
  the injector coupling is bypassed and the solver uses the prescribed
  mass flow directly.
"""

from __future__ import annotations

from hyprop.core.exceptions import ConfigError
from hyprop.core.registry import register_model
from hyprop.tank.base import FluidState, TankModel, TankState


@register_model("tank", "pressure_fed")
class PressureFedTank(TankModel):
    """Constant-pressure, constant-temperature liquid/gas supply."""

    def __init__(
        self,
        oxidizer_mass_kg: float,
        pressure_pa: float,
        temperature_k: float,
        density_kg_m3: float,
        vapor_pressure_pa: float = 0.0,
        phase: str = "liquid",
    ) -> None:
        if oxidizer_mass_kg <= 0 or pressure_pa <= 0 or density_kg_m3 <= 0:
            raise ConfigError("Mass, pressure and density must be positive.")
        self._mass = oxidizer_mass_kg
        self._time = 0.0
        self._fluid = FluidState(
            pressure_pa=pressure_pa,
            temperature_k=temperature_k,
            density_kg_m3=density_kg_m3,
            vapor_pressure_pa=vapor_pressure_pa,
            phase=phase,
        )

    def state(self) -> TankState:
        liquid = self._mass if self._fluid.phase == "liquid" else 0.0
        vapor = self._mass - liquid
        return TankState(
            time_s=self._time,
            pressure_pa=self._fluid.pressure_pa,
            temperature_k=self._fluid.temperature_k,
            mass_liquid_kg=liquid,
            mass_vapor_kg=vapor,
            fluid=self._fluid,
        )

    def step(self, dt: float, mdot_out: float) -> TankState:
        if dt <= 0.0 or mdot_out < 0.0:
            raise ValueError("Require dt > 0 and mdot_out >= 0.")
        self._time += dt
        self._mass = max(self._mass - mdot_out * dt, 0.0)
        return self.state()


@register_model("tank", "constant_mdot")
class ConstantMdotTank(PressureFedTank):
    """Prescribed-mdot supply for early sizing studies.

    The solver detects this model and skips the injector coupling,
    using :attr:`mdot_kg_s` directly.
    """

    def __init__(
        self,
        oxidizer_mass_kg: float,
        mdot_kg_s: float,
        pressure_pa: float = 5.0e6,
        temperature_k: float = 293.15,
        density_kg_m3: float = 786.6,
    ) -> None:
        super().__init__(
            oxidizer_mass_kg, pressure_pa, temperature_k, density_kg_m3,
            vapor_pressure_pa=pressure_pa,
        )
        if mdot_kg_s <= 0:
            raise ConfigError("mdot must be positive.")
        self.mdot_kg_s = mdot_kg_s
