"""Tests for the built-in propellant database (hyprop.data)."""

import pytest

from hyprop.core.exceptions import DataError
from hyprop.data import list_fuels, list_oxidizers, load_fuel, load_oxidizer


def test_all_fuels_load_and_validate():
    fuels = list_fuels()
    assert {"ldpe", "hdpe", "paraffin", "htpb", "abs", "pmma"} <= set(fuels)
    for name in fuels:
        fuel = load_fuel(name)
        assert 800.0 <= fuel.density.value <= 2000.0  # sanity [kg/m^3]
        assert fuel.composition  # non-empty elemental composition


def test_all_oxidizers_load_and_validate():
    oxidizers = list_oxidizers()
    assert {"n2o", "lox", "gox", "htp"} <= set(oxidizers)
    for name in oxidizers:
        ox = load_oxidizer(name)
        assert 0.01 <= ox.molar_mass_kg_mol <= 0.2  # sanity [kg/mol]


def test_hdpe_regression_from_hrap():
    fuel = load_fuel("hdpe")
    entries = fuel.regression_for("n2o")
    assert len(entries) == 1
    assert entries[0].a == pytest.approx(1.04e-4)
    assert entries[0].n == pytest.approx(0.352)
    assert entries[0].flux_basis == "oxidizer"


def test_paraffin_has_hrap_and_user_datasets():
    fuel = load_fuel("paraffin")
    assert len(fuel.regression_for("n2o")) == 2


def test_missing_entry_raises():
    with pytest.raises(DataError):
        load_fuel("unobtainium")


def test_polyethylene_enthalpy_is_solid_phase_nbs_value():
    """dHf of solid linear PE: -28.182 kJ/mol CH2 (Splitstone & Johnson,
    J. Res. NBS 78A, 611, 1974). v0.1 used a gas-phase estimate (-41.2/C2H4)."""
    for name in ("hdpe", "ldpe"):
        fuel = load_fuel(name)
        assert fuel.composition == {"C": 2, "H": 4}
        assert fuel.enthalpy_of_formation.value == pytest.approx(2 * -28.182e3)
    assert load_fuel("ldpe").density.value == pytest.approx(920.0)
