"""Single cylindrical port - the workhorse of hybrid motors.

Analytic relations for a centred circular port of initial diameter D0
in a grain of outer diameter D_out:

    r(w)      = D0/2 + w
    A_port(w) = pi * r(w)^2
    P_burn(w) = 2 * pi * r(w)
    web(w)    = D_out/2 - r(w)

Source: HRAP Theory Eq. 10-12; any propulsion text.
"""

from __future__ import annotations

import math

from hyprop.core.exceptions import ConfigError
from hyprop.core.registry import register_model
from hyprop.geometry.base import GrainGeometry


@register_model("geometry", "cylindrical")
class CylindricalGrain(GrainGeometry):
    """Centred single circular port."""

    def __init__(
        self,
        length_m: float,
        outer_diameter_m: float,
        initial_diameter_m: float,
    ) -> None:
        super().__init__(length_m, outer_diameter_m)
        if not (0.0 < initial_diameter_m < outer_diameter_m):
            raise ConfigError(
                "Port initial diameter must be in (0, outer diameter)."
            )
        self.initial_diameter_m = initial_diameter_m

    def _radius(self, w: float) -> float:
        return 0.5 * self.initial_diameter_m + max(w, 0.0)

    def port_area(self, w: float) -> float:
        radius = min(self._radius(w), 0.5 * self.outer_diameter_m)
        return math.pi * radius * radius

    def burn_perimeter(self, w: float) -> float:
        if self.is_burned_out(w):
            return 0.0
        return 2.0 * math.pi * self._radius(w)

    def web_remaining(self, w: float) -> float:
        return 0.5 * self.outer_diameter_m - self._radius(w)
