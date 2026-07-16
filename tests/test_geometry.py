"""Tests for hyprop.geometry: analytic checks + contour-engine convergence."""

import math

import pytest

from hyprop.core.exceptions import ConfigError
from hyprop.geometry import CylindricalGrain, MultiportGrain

shapely = pytest.importorskip("shapely", reason="shapely not installed")

from hyprop.geometry import ContourGrain, StarGrain, WagonWheelGrain  # noqa: E402

L = 0.30          # grain length [m]
D_OUT = 0.10      # grain OD [m]


# ------------------------------------------------------------ cylindrical
def test_cylindrical_analytic():
    grain = CylindricalGrain(L, D_OUT, initial_diameter_m=0.030)
    w = 0.010
    r = 0.015 + w
    assert grain.port_area(w) == pytest.approx(math.pi * r**2, rel=1e-12)
    assert grain.burn_perimeter(w) == pytest.approx(2 * math.pi * r, rel=1e-12)
    assert grain.burn_area(w) == pytest.approx(2 * math.pi * r * L, rel=1e-12)
    assert grain.hydraulic_diameter(w) == pytest.approx(2 * r, rel=1e-12)
    assert grain.web_remaining(w) == pytest.approx(0.05 - r, rel=1e-12)


def test_cylindrical_burnout():
    grain = CylindricalGrain(L, D_OUT, initial_diameter_m=0.030)
    w_burnout = 0.05 - 0.015
    assert grain.web_remaining(w_burnout) == pytest.approx(0.0, abs=1e-15)
    assert grain.is_burned_out(w_burnout + 1e-6)
    assert grain.burn_perimeter(w_burnout + 1e-6) == 0.0


def test_cylindrical_fuel_mass():
    grain = CylindricalGrain(L, D_OUT, initial_diameter_m=0.030)
    rho = 970.0
    v0 = (math.pi * (0.05**2 - 0.015**2)) * L
    assert grain.fuel_mass(0.0, rho) == pytest.approx(v0 * rho, rel=1e-12)


def test_cylindrical_validation():
    with pytest.raises(ConfigError):
        CylindricalGrain(L, D_OUT, initial_diameter_m=0.2)   # port > OD


# -------------------------------------------------------------- multiport
def test_multiport_analytic():
    grain = MultiportGrain(
        L, D_OUT, port_count=4, initial_diameter_m=0.015,
        bolt_circle_diameter_m=0.05,
    )
    w = 0.002
    r = 0.0075 + w
    assert grain.port_area(w) == pytest.approx(4 * math.pi * r**2, rel=1e-12)
    assert grain.burn_perimeter(w) == pytest.approx(
        4 * 2 * math.pi * r, rel=1e-12
    )
    chord = 2 * 0.025 * math.sin(math.pi / 4)
    expected_web = min(chord - 2 * r, 0.05 - 0.025 - r)
    assert grain.web_remaining(w) == pytest.approx(expected_web, rel=1e-12)


def test_multiport_with_central_port():
    grain = MultiportGrain(
        L, D_OUT, port_count=6, initial_diameter_m=0.010,
        bolt_circle_diameter_m=0.06, central_port_diameter_m=0.012,
    )
    assert grain.port_area(0.0) == pytest.approx(
        6 * math.pi * 0.005**2 + math.pi * 0.006**2, rel=1e-12
    )
    assert grain.web_remaining(0.0) > 0


def test_multiport_overlap_rejected():
    with pytest.raises(ConfigError):
        MultiportGrain(
            L, D_OUT, port_count=8, initial_diameter_m=0.02,
            bolt_circle_diameter_m=0.05,
        )


# --------------------------------------------------------- contour engine
def _circle_points(radius, n=256):
    return [
        (radius * math.cos(2 * math.pi * k / n),
         radius * math.sin(2 * math.pi * k / n))
        for k in range(n)
    ]


def test_contour_circle_matches_cylindrical():
    """Contour engine with a circular contour must reproduce the analytic
    cylindrical grain within polygonal-approximation error (<0.1%)."""
    reference = CylindricalGrain(L, D_OUT, initial_diameter_m=0.030)
    contour = ContourGrain(L, D_OUT, _circle_points(0.015))
    for w in (0.0, 0.005, 0.015):
        assert contour.port_area(w) == pytest.approx(
            reference.port_area(w), rel=1e-3
        )
        assert contour.burn_perimeter(w) == pytest.approx(
            reference.burn_perimeter(w), rel=1e-3
        )
    assert contour.web_remaining(0.010) == pytest.approx(
        reference.web_remaining(0.010), rel=1e-3
    )


def test_contour_burnout_clips_wall_perimeter():
    contour = ContourGrain(L, D_OUT, _circle_points(0.015))
    w_past_burnout = 0.05 - 0.015 + 0.005
    assert contour.port_area(w_past_burnout) == pytest.approx(
        math.pi * 0.05**2, rel=1e-3
    )
    # everything reached the wall -> nothing burns any more
    assert contour.burn_perimeter(w_past_burnout) == pytest.approx(
        0.0, abs=1e-3
    )


def test_star_grain_monotonic_and_smoothing():
    star = StarGrain(
        L, D_OUT, point_count=6, inner_radius_m=0.010, outer_radius_m=0.020
    )
    areas = [star.port_area(w) for w in (0.0, 0.002, 0.005, 0.010)]
    assert all(a2 > a1 for a1, a2 in zip(areas, areas[1:]))
    # star has larger perimeter than the circle of equal area (initially)
    equivalent_r = math.sqrt(star.port_area(0.0) / math.pi)
    assert star.burn_perimeter(0.0) > 2 * math.pi * equivalent_r


def test_wagon_wheel_basic():
    wheel = WagonWheelGrain(
        L, D_OUT, spoke_count=4, hub_radius_m=0.010,
        tip_radius_m=0.030, spoke_width_m=0.008,
    )
    assert wheel.port_area(0.0) > math.pi * 0.010**2   # hub + slots
    assert wheel.web_remaining(0.0) > 0.0
    a0, a1 = wheel.port_area(0.0), wheel.port_area(0.004)
    assert a1 > a0


def test_contour_validation():
    with pytest.raises(ConfigError):
        ContourGrain(L, D_OUT, [(0, 0), (0.01, 0)])          # 2 points
    with pytest.raises(ConfigError):
        ContourGrain(L, D_OUT, _circle_points(0.08))          # outside bore


def test_registry_exposes_all_geometries():
    from hyprop.core.registry import autodiscover, list_models

    autodiscover()
    names = list_models("geometry")["geometry"]
    for expected in ("cylindrical", "multiport", "custom", "star",
                     "wagon_wheel"):
        assert expected in names
