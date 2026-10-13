"""Tests for hyprop.optimization (stubbed thermochemistry)."""

import pytest

import hyprop.simulation.solver as solver_module
from hyprop.core.config import EngineConfig
from hyprop.optimization import Objective, OptimizationProblem, optimize_scipy
from tests.test_solver import CFG, _StubCEA


@pytest.fixture()
def stub_cea(monkeypatch):
    monkeypatch.setattr(solver_module, "_build_cea_table", lambda config, eps: _StubCEA())


def _problem():
    return OptimizationProblem(
        base_config=EngineConfig.from_dict(CFG),
        variables={"nozzle.throat_diameter_m": (9e-3, 14e-3)},
        objectives=[Objective("thrust_iw", "max")],
        constraints=[lambda row: row["peak_pc_pa"] - 45e5],  # Pc <= 45 bar
    )


def test_evaluate_and_penalty(stub_cea):
    problem = _problem()
    values, row = problem.evaluate([11.5e-3])
    assert row["thrust_iw"] > 0 and values[0] < 0  # max -> negated
    # infeasible variable (tiny throat -> huge Pc) triggers the constraint
    values_bad, _ = problem.evaluate([9e-3])
    assert values_bad[0] > values[0]


def test_scipy_de_finds_larger_throat(stub_cea):
    problem = _problem()
    best = optimize_scipy(problem, maxiter=4, popsize=4)
    # thrust grows with throat until the Pc constraint bites; optimum
    # must sit above the mid-range and stay feasible
    assert best["x"]["nozzle.throat_diameter_m"] > 10.5e-3
    assert best["row"]["peak_pc_pa"] <= 45e5 * 1.001
    assert best["n_evaluations"] > 10


def test_single_objective_guard(stub_cea):
    problem = _problem()
    problem.objectives.append(Objective("total_impulse_ns", "max"))
    with pytest.raises(ValueError):
        optimize_scipy(problem)
