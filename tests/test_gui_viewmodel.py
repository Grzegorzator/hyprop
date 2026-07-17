"""Tests for the Qt-free GUI view-model (no display needed)."""

import pytest

import hyprop.simulation.solver as solver_module
from hyprop.gui.viewmodel import FORM_LAYOUT, SessionViewModel
from tests.test_solver import CFG, _StubCEA


@pytest.fixture()
def vm(tmp_path):
    from hyprop.core.config import EngineConfig

    path = tmp_path / "case.yaml"
    EngineConfig.from_dict(CFG).to_yaml(path)
    viewmodel = SessionViewModel()
    viewmodel.load(path)
    return viewmodel


def test_form_layout_paths_resolve(vm):
    for rows in FORM_LAYOUT.values():
        for path, _, _ in rows:
            vm.get(path)                       # must not raise


def test_set_get_and_validate(vm):
    vm.set("injector.discharge_coefficient", "0.55")
    assert vm.get("injector.discharge_coefficient") == 0.55
    assert vm.validate() is None
    vm.set("injector.discharge_coefficient", "2.0")   # out of (0, 1]
    assert vm.validate() is not None


def test_run_and_summary(vm, monkeypatch):
    monkeypatch.setattr(
        solver_module, "_build_cea_table", lambda config, eps: _StubCEA())
    vm.set("injector.discharge_coefficient", "0.6")
    vm.run()
    rows = dict(vm.summary_rows())
    assert "total_impulse_ns" in rows and "IW thrust" in rows


def test_field_choices_cover_registry_and_database():
    from hyprop.gui.viewmodel import field_choices

    choices = field_choices()
    assert "hdpe" in choices["fuel.name"]
    assert "n2o" in choices["oxidizer.name"]
    assert "cylindrical" in choices["grain.geometry"]
    assert "spi" in choices["injector.model"]
    assert "equilibrium_blowdown" in choices["tank.model"]
    assert choices["simulation.pc_solver"] == ["fixed_point", "brent"]


def test_set_creates_missing_branches():
    vm2 = SessionViewModel()                 # empty raw (no YAML loaded)
    vm2.set("grain.geometry", "cylindrical")
    assert vm2.raw["grain"]["geometry"] == "cylindrical"


def test_custom_fuel_card_roundtrip(tmp_path, monkeypatch):
    import hyprop.data.loader as loader
    from hyprop.data import load_fuel
    from hyprop.data.custom import save_custom_fuel

    monkeypatch.setattr(loader, "_USER_DIR", tmp_path)
    save_custom_fuel("mojewosk", 930.0, {"C": 20, "H": 42}, -450e3,
                     regression_a_si=1.2e-4, regression_n=0.5,
                     root=tmp_path)
    fuel = load_fuel("mojewosk")
    assert fuel.density.value == 930.0
    assert fuel.enthalpy_of_formation.verify is True
    assert fuel.regression_for("n2o")[0].a == 1.2e-4
    assert "mojewosk" in loader.list_fuels()


def test_custom_oxidizer_card(tmp_path, monkeypatch):
    import hyprop.data.loader as loader
    from hyprop.data.custom import save_custom_oxidizer
    from hyprop.core.exceptions import DataError
    import pytest as _pytest

    monkeypatch.setattr(loader, "_USER_DIR", tmp_path)
    save_custom_oxidizer("mixox", "gox", 0.032, 1100.0, root=tmp_path)
    from hyprop.data import load_oxidizer
    ox = load_oxidizer("mixox")
    assert ox.parameters["chemistry_base"] == "gox"
    with _pytest.raises(DataError):
        save_custom_oxidizer("zly", "chlorek", 0.05, root=tmp_path)


def test_unit_system_display_roundtrip(vm):
    vm.set_unit_system("metric")
    vm.set("grain.length_m", "0.45")               # SI setter
    assert vm.get_display("grain.length_m") == pytest.approx(450.0)  # mm
    vm.set_display("grain.length_m", "500")        # user types 500 mm
    assert vm.get("grain.length_m") == pytest.approx(0.5)            # SI
    vm.set_display("oxidizer.temperature_k", "20") # 20 degC
    assert vm.get("oxidizer.temperature_k") == pytest.approx(293.15)
    vm.set_unit_system("imperial")
    assert vm.display_unit("mission.thrust_n", "N") == "lbf"
    vm.set_display("mission.thrust_n", "112.4")    # ~500 N
    assert vm.get("mission.thrust_n") == pytest.approx(500.0, rel=0.001)
    vm.set_unit_system("si")
    with pytest.raises(ValueError):
        vm.set_unit_system("banany")


def test_empty_field_means_none_not_empty_string(vm):
    """Regression: blank QLineEdit used to inject '' and break pydantic
    unit parsing ("Cannot parse quantity ''")."""
    vm.set("fuel.density_kg_m3", "")
    assert vm.get("fuel.density_kg_m3") is None
    assert vm.validate() is None                    # config still valid
    vm.set_unit_system("metric")
    vm.set_display("fuel.density_kg_m3", "  ")      # whitespace only
    assert vm.get("fuel.density_kg_m3") is None
    vm.set_unit_system("si")
