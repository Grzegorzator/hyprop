"""Multiple circular ports arranged on a bolt circle.

N identical circular ports of initial diameter d0, centres on a circle
of radius R_c around the grain axis (optionally plus a central port).
Valid until neighbouring burn fronts merge; the geometry reports
``web_remaining`` as the minimum of (a) fuel between adjacent ports,
(b) fuel between port and outer wall, (c) fuel between outer and
central port (if present) - the solver stops or switches model there.

    d_centres = 2 * R_c * sin(pi / N)                (chord between centres)
    web_pp(w) = d_centres - 2*r(w)                   (port-port)
    web_pw(w) = (D_out/2 - R_c) - r(w)               (port-wall)

Source: Humble Ch. 7 (multiport hybrids); geometric relations.
"""

from __future__ import annotations

import math

from hyprop.core.exceptions import ConfigError
from hyprop.core.registry import register_model
from hyprop.geometry.base import GrainGeometry


@register_model("geometry", "multiport")
class MultiportGrain(GrainGeometry):
    """N circular ports on a bolt circle, optional central port."""

    def __init__(
        self,
        length_m: float,
        outer_diameter_m: float,
        port_count: int,
        initial_diameter_m: float,
        bolt_circle_diameter_m: float,
        central_port_diameter_m: float = 0.0,
    ) -> None:
        super().__init__(length_m, outer_diameter_m)
        if port_count < 2:
            raise ConfigError("multiport requires port_count >= 2.")
        if initial_diameter_m <= 0:
            raise ConfigError("Port diameter must be positive.")
        if not (0.0 < bolt_circle_diameter_m < outer_diameter_m):
            raise ConfigError("Bolt circle must fit inside the grain.")
        self.port_count = port_count
        self.initial_diameter_m = initial_diameter_m
        self.bolt_circle_radius_m = 0.5 * bolt_circle_diameter_m
        self.central_port_diameter_m = central_port_diameter_m
        if self._initial_min_web() <= 0.0:
            raise ConfigError(
                "Initial multiport layout has overlapping ports/walls."
            )

    # ------------------------------------------------------------ helpers
    def _radius(self, w: float) -> float:
        return 0.5 * self.initial_diameter_m + max(w, 0.0)

    def _central_radius(self, w: float) -> float:
        if self.central_port_diameter_m <= 0.0:
            return 0.0
        return 0.5 * self.central_port_diameter_m + max(w, 0.0)

    def _has_central(self) -> bool:
        return self.central_port_diameter_m > 0.0

    def _initial_min_web(self) -> float:
        return self.web_remaining(0.0)

    # ---------------------------------------------------------- interface
    def port_area(self, w: float) -> float:
        area = self.port_count * math.pi * self._radius(w) ** 2
        if self._has_central():
            area += math.pi * self._central_radius(w) ** 2
        return area

    def burn_perimeter(self, w: float) -> float:
        if self.is_burned_out(w):
            return 0.0
        perimeter = self.port_count * 2.0 * math.pi * self._radius(w)
        if self._has_central():
            perimeter += 2.0 * math.pi * self._central_radius(w)
        return perimeter

    def web_remaining(self, w: float) -> float:
        radius = self._radius(w)
        chord = 2.0 * self.bolt_circle_radius_m * math.sin(
            math.pi / self.port_count
        )
        web_port_port = chord - 2.0 * radius
        web_port_wall = (
            0.5 * self.outer_diameter_m - self.bolt_circle_radius_m - radius
        )
        webs = [web_port_port, web_port_wall]
        if self._has_central():
            webs.append(
                self.bolt_circle_radius_m - radius - self._central_radius(w)
            )
        return min(webs)
