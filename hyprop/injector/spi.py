"""Single-Phase Incompressible (SPI) injector model - default (D3).

    mdot = Cd * A * sqrt(2 * rho * (P1 - P2))        (orifice equation)

Equivalent to HRAP's dLoss formulation: HRAP defines
``dLoss = 1/(Cd*N*A)^2 * K/2`` with K = 2, i.e. mdot = sqrt(dP*rho/dLoss)
== Cd*N*A*sqrt(2*rho*dP). Valid for subcooled liquid; overpredicts flow
for saturated N2O at low dP (no flashing) - cf. NHNE.

Sources: HRAP Theory (injector section); Sutton Ch. 8; Waxman et al.,
JPP 2013 (N2O injector review).
"""

from __future__ import annotations

import math

from hyprop.core.registry import register_model
from hyprop.injector.base import InjectorModel
from hyprop.tank.base import FluidState


@register_model("injector", "spi")
class SPIInjector(InjectorModel):
    """Incompressible orifice flow."""

    def mdot(self, upstream: FluidState, p_chamber_pa: float) -> float:
        dp = self._dp(upstream, p_chamber_pa)
        if dp <= 0.0:
            return 0.0
        return self.cd * self.total_area_m2 * math.sqrt(
            2.0 * upstream.density_kg_m3 * dp
        )
