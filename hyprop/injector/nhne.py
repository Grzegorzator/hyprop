"""Non-Homogeneous Non-Equilibrium (NHNE) model of Dyer et al.

Weighted blend of the SPI (no flashing) and HEM (full equilibrium
flashing) limits:

    kappa = sqrt( (P1 - P2) / (Pv - P2) )
    mdot  = kappa/(1+kappa) * mdot_SPI + 1/(1+kappa) * mdot_HEM

For a saturated upstream state (self-pressurised N2O tank) Pv = P1 and
kappa = 1: the arithmetic mean of SPI and HEM. The blend reflects the
ratio of bubble-growth time to orifice residence time.

Sources: Dyer, Doran, Dunn, Zilliac, AIAA 2007-5702; Solomon MSc 2011;
user's 08_injector_model_NHNE.py.
"""

from __future__ import annotations

import math

from hyprop.core.registry import register_model
from hyprop.injector.base import InjectorModel
from hyprop.injector.hem import HEMInjector
from hyprop.injector.spi import SPIInjector
from hyprop.tank.base import FluidState


@register_model("injector", "nhne")
class NHNEInjector(InjectorModel):
    """Dyer blend of SPI and HEM."""

    def __init__(self, discharge_coefficient, orifice_count, orifice_area_m2):
        super().__init__(discharge_coefficient, orifice_count, orifice_area_m2)
        self._spi = SPIInjector(discharge_coefficient, orifice_count, orifice_area_m2)
        self._hem = HEMInjector(discharge_coefficient, orifice_count, orifice_area_m2)

    def mdot(self, upstream: FluidState, p_chamber_pa: float) -> float:
        dp = self._dp(upstream, p_chamber_pa)
        if dp <= 0.0:
            return 0.0
        mdot_spi = self._spi.mdot(upstream, p_chamber_pa)
        mdot_hem = self._hem.mdot(upstream, p_chamber_pa)
        dp_sat = upstream.vapor_pressure_pa - p_chamber_pa
        if dp_sat <= 0.0:
            return mdot_spi  # fully subcooled: no flashing
        kappa = math.sqrt(dp / dp_sat)
        return (kappa * mdot_spi + mdot_hem) / (1.0 + kappa)
