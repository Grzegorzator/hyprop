"""Optimization drivers (stage E11): scipy (single-objective) + NSGA-II.

* :func:`optimize_scipy` - differential evolution (global, robust to the
  noisy/discontinuous blowdown response); single objective.
* :func:`optimize_nsga2` - multi-objective Pareto front via pymoo
  (optional dependency; ImportError explains installation).
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

from hyprop.core.logging import get_logger
from hyprop.optimization.problem import OptimizationProblem

_log = get_logger(__name__)


def optimize_scipy(problem: OptimizationProblem, maxiter: int = 20,
                   popsize: int = 8, seed: int = 0) -> Dict:
    """Differential evolution on the first objective."""
    from scipy.optimize import differential_evolution

    if len(problem.objectives) != 1:
        raise ValueError("optimize_scipy handles exactly one objective; "
                         "use optimize_nsga2 for Pareto studies.")

    def cost(x):
        return problem.evaluate(x)[0][0]

    result = differential_evolution(
        cost, bounds=problem.bounds, maxiter=maxiter, popsize=popsize,
        seed=seed, polish=False, tol=1e-3,
    )
    best_case = dict(zip(problem.names, result.x))
    _, row = problem.evaluate(result.x)
    _log.info("scipy DE done: %s -> f=%.4g", best_case, result.fun)
    return {"x": best_case, "objective": result.fun, "row": row,
            "n_evaluations": result.nfev, "success": bool(result.success)}


def optimize_nsga2(problem: OptimizationProblem, generations: int = 20,
                   population: int = 24, seed: int = 0) -> Dict:
    """NSGA-II Pareto front (requires pymoo)."""
    try:
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.core.problem import ElementwiseProblem
        from pymoo.optimize import minimize
    except ImportError as exc:                          # pragma: no cover
        raise ImportError("NSGA-II requires pymoo (pip install pymoo).") \
            from exc

    lows = np.array([b[0] for b in problem.bounds])
    highs = np.array([b[1] for b in problem.bounds])

    class _Problem(ElementwiseProblem):
        def __init__(self):
            super().__init__(n_var=len(problem.names),
                             n_obj=len(problem.objectives),
                             xl=lows, xu=highs)

        def _evaluate(self, x, out, *args, **kwargs):
            out["F"] = problem.evaluate(x)[0]

    result = minimize(_Problem(), NSGA2(pop_size=population),
                      ("n_gen", generations), seed=seed, verbose=False)
    front = [dict(zip(problem.names, x)) for x in np.atleast_2d(result.X)]
    _log.info("NSGA-II done: %d Pareto points", len(front))
    return {"pareto_x": front, "pareto_f": np.atleast_2d(result.F).tolist()}
