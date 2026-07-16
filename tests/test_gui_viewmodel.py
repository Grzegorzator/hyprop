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
