"""Homogeneous Equilibrium Model (HEM) injector - flashing lower bound.

Two-phase mixture in thermodynamic equilibrium expands isentropically
from the upstream state; mass flux at downstream pressure P:

    G(P) = rho(P, s1) * sqrt(2 * (h1 - h(P, s1)))

The flow chokes where G(P) is maximum; the delivered flux is

    mdot = Cd * A * max_{P in [P2, P1]} G(P)   (evaluated as G at the
    choking pressure if P2 is below it, else at P2).

Requires CoolProp (full h, s data) - decision D1 dual-backend.

Sources: Dyer et al., AIAA 2007; Waxman/Cantwell, JPP 2013; user's
08_injector_model_NHNE.py prototype.
"""

from __future__ import annotations

import math

import numpy as np

from hyprop.core.exceptions import ConfigError
from hyprop.core.registry import register_model
from hyprop.injector.base import InjectorModel
from hyprop.tank.base import FluidState
from hyprop.tank.n2o_properties import CoolPropN2O

_SCAN_POINTS = 60


@register_model("injector", "hem")
class HEMInjector(InjectorModel):
    """Isentropic homogeneous-equilibrium flashing flow (choked-aware)."""

    def __init__(self, discharge_coefficient, orifice_count, orifice_area_m2):
        super().__init__(discharge_coefficient, orifice_count, orifice_area_m2)
        self._props = CoolPropN2O()  # raises if CoolProp missing

    def mdot(self, upstream: FluidState, p_chamber_pa: float) -> float:
        if self._dp(upstream, p_chamber_pa) <= 0.0:
            return 0.0
        h1, s1 = self._upstream_hs(upstream)
        p_grid = np.linspace(max(p_chamber_pa, 1e4), upstream.pressure_pa * 0.999, _SCAN_POINTS)
        g_max = 0.0
        for pressure in p_grid:
            rho, h = self._props.state_ps(float(pressure), s1)
            if h1 <= h:
                continue
            g_flux = rho * math.sqrt(2.0 * (h1 - h))
            g_max = max(g_max, g_flux)
        return self.cd * self.total_area_m2 * g_max

    def _upstream_hs(self, upstream: FluidState):
        if upstream.enthalpy_j_kg is not None and upstream.entropy_j_kg_k is not None:
            return upstream.enthalpy_j_kg, upstream.entropy_j_kg_k
        if upstream.phase != "liquid":
            raise ConfigError("HEM requires upstream h, s (vapor phase not supported yet).")
        temperature = upstream.temperature_k
        return (
            self._props.h_liquid(temperature),
            self._props.s_liquid(temperature),
        )
