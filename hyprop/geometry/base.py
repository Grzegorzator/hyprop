"""Grain geometry interface (stage E3).

Every geometry answers questions *as a function of burned web thickness
``w`` [m]* - the distance the fuel surface has regressed perpendicular
to itself. This parametrisation makes the transient solver (E6)
geometry-agnostic: it integrates ``dw/dt = rdot`` and asks the geometry
for areas.

Assumptions (HRAP Theory, Sec. II; Humble Ch. 7):

* regression is uniform along the grain (no axial coupling in 0D model),
* end faces are inhibited - grain length is constant,
* burning stops locally where the surface reaches the outer wall.

Sources: HRAP Theory & Application (Eq. 10-13); Humble, Henry & Larson,
*Space Propulsion Analysis and Design*, Ch. 7; Sutton Ch. 12 (grain
geometry concepts).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from hyprop.core.exceptions import ConfigError


class GrainGeometry(ABC):
    """Port geometry of a fuel grain as a function of burned web ``w``."""

    def __init__(self, length_m: float, outer_diameter_m: float) -> None:
        if length_m <= 0 or outer_diameter_m <= 0:
            raise ConfigError("Grain length and OD must be positive.")
        self.length_m = length_m
        self.outer_diameter_m = outer_diameter_m

    # ------------------------------------------------------ abstract API
    @abstractmethod
    def port_area(self, w: float) -> float:
        """Port (flow) cross-section area [m^2] at burned web ``w``."""

    @abstractmethod
    def burn_perimeter(self, w: float) -> float:
        """Burning perimeter [m] of the port cross-section at web ``w``.

        Excludes surface that has reached the outer wall (liner).
        """

    @abstractmethod
    def web_remaining(self, w: float) -> float:
        """Minimum remaining fuel web [m]; <= 0 means local burnout."""

    # ----------------------------------------------------- derived API
    def burn_area(self, w: float) -> float:
        """Burning surface area [m^2]: perimeter x grain length."""
        return self.burn_perimeter(w) * self.length_m

    def hydraulic_diameter(self, w: float) -> float:
        """Hydraulic diameter D_h = 4 * A_port / P_wetted [m].

        The wetted perimeter equals the port perimeter (burning or not).
        For preliminary sizing the burning perimeter is used as wetted -
        the difference appears only after local burnout.
        """
        perimeter = self.burn_perimeter(w)
        if perimeter <= 0.0:
            return 0.0
        return 4.0 * self.port_area(w) / perimeter

    def equivalent_port_diameter(self, w: float) -> float:
        """Diameter of a circle with the same port area [m]."""
        import math

        return 2.0 * math.sqrt(self.port_area(w) / math.pi)

    def bore_area(self) -> float:
        """Full bore (grain OD) cross-section area [m^2]."""
        import math

        return math.pi * (0.5 * self.outer_diameter_m) ** 2

    def fuel_volume(self, w: float) -> float:
        """Remaining fuel volume [m^3] at burned web ``w``."""
        return max(self.bore_area() - self.port_area(w), 0.0) * self.length_m

    def fuel_mass(self, w: float, density_kg_m3: float) -> float:
        """Remaining fuel mass [kg] at burned web ``w``."""
        return self.fuel_volume(w) * density_kg_m3

    def is_burned_out(self, w: float) -> bool:
        """True when the minimum web is consumed."""
        return self.web_remaining(w) <= 0.0

    # ----------------------------------------------------- construction
    @classmethod
    def from_spec(
        cls, length_m: float, outer_diameter_m: float, port: dict[str, Any]
    ) -> GrainGeometry:
        """Build from ``GrainSpec`` fields; subclasses define ``port`` keys."""
        return cls(length_m, outer_diameter_m, **port)
