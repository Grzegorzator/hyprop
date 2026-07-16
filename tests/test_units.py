"""Tests for hyprop.core.units."""

import pytest

from hyprop.core.exceptions import UnitError
from hyprop.core.units import Q_, to_si


def test_float_passthrough():
    assert to_si(0.025, "m") == pytest.approx(0.025)


def test_string_conversion_pressure():
    assert to_si("35 bar", "Pa") == pytest.approx(3.5e6)


def test_string_conversion_length():
    assert to_si("25 mm", "m") == pytest.approx(0.025)


def test_quantity_conversion():
    assert to_si(Q_(1.0, "MPa"), "Pa") == pytest.approx(1.0e6)


def test_dimension_mismatch_raises():
    with pytest.raises(UnitError):
        to_si("35 bar", "m")


def test_unparseable_raises():
    with pytest.raises(UnitError):
        to_si("thirty five bars", "Pa")
