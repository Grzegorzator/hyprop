"""Arbitrary port cross-section evolved by contour offsetting.

Physical basis: fuel regression is locally perpendicular to the burning
surface, so the port contour at burned web ``w`` is the *Minkowski
offset* of the initial contour by distance ``w``. Shapely's ``buffer``
performs exactly this operation (round joins = physically correct
smoothing of concave corners; convex corners self-smooth).

The offset port is clipped to the grain bore. Perimeter that has reached
the bore wall no longer burns and is excluded from ``burn_perimeter`` by
subtracting the length of the clipped boundary that lies on the bore
circle.

This one engine powers ``star``, ``wagon_wheel`` and truly custom
(user-drawn) ports - they only differ in the initial contour generator.

Source: standard level-set/offset formulation of grain regression, e.g.
Willcox et al., JPP 2007 (grain design via minimum distance function);
HRAP assumes analogous perpendicular regression for its shapes.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from hyprop.core.exceptions import ConfigError
from hyprop.core.registry import register_model
from hyprop.geometry.base import GrainGeometry

_BUFFER_RESOLUTION = 64  # segments per quarter circle in offsets
_BORE_TOLERANCE = 1e-9  # geometric tolerance [m]


def _require_shapely():
    try:
        import shapely  # noqa: F401
        from shapely.geometry import Point, Polygon

        return Point, Polygon
    except ImportError as exc:  # pragma: no cover
        raise ConfigError(
            "Contour-based geometries require shapely (pip install shapely)."
        ) from exc


@register_model("geometry", "custom")
class ContourGrain(GrainGeometry):
    """Port defined by an arbitrary simple polygon, evolved by offset."""

    def __init__(
        self,
        length_m: float,
        outer_diameter_m: float,
        contour_points_m: Sequence[tuple[float, float]],
    ) -> None:
        super().__init__(length_m, outer_diameter_m)
        Point, Polygon = _require_shapely()
        if len(contour_points_m) < 3:
            raise ConfigError("Contour needs at least 3 points.")
        self._port0 = Polygon(contour_points_m)
        if not self._port0.is_valid or self._port0.area <= 0.0:
            raise ConfigError("Contour polygon is invalid or degenerate.")
        bore_radius = 0.5 * outer_diameter_m
        self._bore = Point(0.0, 0.0).buffer(bore_radius, quad_segs=_BUFFER_RESOLUTION)
        if not self._bore.contains(self._port0):
            raise ConfigError("Initial contour must lie inside the bore.")
        self._bore_radius = bore_radius

    # ------------------------------------------------------------ engine
    def _offset_port(self, w: float):
        if w <= 0.0:
            return self._port0
        return self._port0.buffer(w, quad_segs=_BUFFER_RESOLUTION)

    def _clipped(self, w: float):
        return self._offset_port(w).intersection(self._bore)

    # ---------------------------------------------------------- interface
    def port_area(self, w: float) -> float:
        """Total port cross-section area [m^2] after web burn ``w`` [m]."""
        return self._clipped(w).area

    def burn_perimeter(self, w: float) -> float:
        """Burning perimeter [m] after web burn ``w`` [m]."""
        clipped = self._clipped(w)
        if clipped.is_empty:
            return 0.0
        boundary = clipped.boundary
        # Exclude boundary lying on the bore wall (locally burned out):
        wall_band = self._bore.boundary.buffer(_BORE_TOLERANCE * 1e3)
        on_wall = boundary.intersection(wall_band).length
        return max(boundary.length - on_wall, 0.0)

    def web_remaining(self, w: float) -> float:
        """Remaining web thickness [m] after web burn ``w`` [m]."""
        # Distance from the current port contour to the bore wall.
        port = self._offset_port(w)
        if port.contains(self._bore):
            return 0.0
        return self._bore_radius - _max_radius(port)


def _max_radius(polygon) -> float:
    """Largest distance of a polygon boundary vertex from the origin."""
    return max(math.hypot(x, y) for x, y in polygon.exterior.coords)


def star_contour(
    point_count: int,
    inner_radius_m: float,
    outer_radius_m: float,
) -> list[tuple[float, float]]:
    """Classic star port: alternating inner/outer vertices.

    ``outer_radius_m`` is the star tip radius (into the fuel),
    ``inner_radius_m`` the valley radius. Sutton Ch. 12 nomenclature.
    """
    if point_count < 3:
        raise ConfigError("Star needs at least 3 points.")
    if not (0.0 < inner_radius_m < outer_radius_m):
        raise ConfigError("Require 0 < inner_radius < outer_radius.")
    points: list[tuple[float, float]] = []
    step = math.pi / point_count
    for k in range(2 * point_count):
        radius = outer_radius_m if k % 2 == 0 else inner_radius_m
        angle = k * step
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return points


def wagon_wheel_contour(
    spoke_count: int,
    hub_radius_m: float,
    tip_radius_m: float,
    spoke_width_m: float,
) -> list[tuple[float, float]]:
    """Wagon-wheel port: central hub with radial slots (spokes of gas).

    Approximated as a polygon: circular hub of ``hub_radius_m`` with
    ``spoke_count`` rectangular slots of width ``spoke_width_m``
    extending to ``tip_radius_m``. Sutton Ch. 12 (wagon wheel family).
    """
    if spoke_count < 2:
        raise ConfigError("Wagon wheel needs at least 2 spokes.")
    if not (0.0 < hub_radius_m < tip_radius_m):
        raise ConfigError("Require 0 < hub_radius < tip_radius.")
    if spoke_width_m <= 0.0 or spoke_width_m >= 2.0 * hub_radius_m:
        raise ConfigError("Spoke width must be in (0, hub diameter).")

    half_width = 0.5 * spoke_width_m
    points: list[tuple[float, float]] = []
    sector = 2.0 * math.pi / spoke_count
    # Angular half-width of the slot where it meets the hub:
    alpha = math.asin(half_width / hub_radius_m)
    arc_steps = max(int(_BUFFER_RESOLUTION * (sector - 2 * alpha) / math.pi), 2)
    for k in range(spoke_count):
        theta = k * sector
        # slot: out along one edge, across the tip, back along the other
        for sign in (+1.0,):
            points.append(_rot(theta - alpha * sign, hub_radius_m))
        points.append(_rot_xy(theta, tip_radius_m, -half_width))
        points.append(_rot_xy(theta, tip_radius_m, +half_width))
        points.append(_rot(theta + alpha, hub_radius_m))
        # hub arc to the next slot
        start = theta + alpha
        end = theta + sector - alpha
        for j in range(1, arc_steps):
            angle = start + (end - start) * j / arc_steps
            points.append(_rot(angle, hub_radius_m))
    return points


def _rot(angle: float, radius: float) -> tuple[float, float]:
    return (radius * math.cos(angle), radius * math.sin(angle))


def _rot_xy(angle: float, x: float, y: float) -> tuple[float, float]:
    """Rotate point (x, y) by ``angle`` around origin."""
    c, s = math.cos(angle), math.sin(angle)
    return (c * x - s * y, s * x + c * y)


@register_model("geometry", "star")
class StarGrain(ContourGrain):
    """Star port built on the contour-offset engine."""

    def __init__(
        self,
        length_m: float,
        outer_diameter_m: float,
        point_count: int,
        inner_radius_m: float,
        outer_radius_m: float,
    ) -> None:
        super().__init__(
            length_m,
            outer_diameter_m,
            star_contour(point_count, inner_radius_m, outer_radius_m),
        )


@register_model("geometry", "wagon_wheel")
class WagonWheelGrain(ContourGrain):
    """Wagon-wheel port built on the contour-offset engine."""

    def __init__(
        self,
        length_m: float,
        outer_diameter_m: float,
        spoke_count: int,
        hub_radius_m: float,
        tip_radius_m: float,
        spoke_width_m: float,
    ) -> None:
        super().__init__(
            length_m,
            outer_diameter_m,
            wagon_wheel_contour(spoke_count, hub_radius_m, tip_radius_m, spoke_width_m),
        )
