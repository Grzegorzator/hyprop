"""Optimization problems over EngineConfig (stage E11).

An :class:`OptimizationProblem` maps decision variables (dotted config
paths + bounds) to objectives/constraints evaluated on the transient
result and its ROP analysis (ARCHITECTURE.md: objectives always read
representative points, never raw steps).

Built-in objective/constraint metrics (per batch-row keys):
``total_impulse_ns``, ``thrust_iw``, ``pc_iw``, ``isp_iw``,
``peak_pc_pa``, ``propellant_used_kg``, ``burn_time_s``, ``lro_s``.
Custom metrics: pass a callable(row_dict) -> float.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Sequence, Tuple, Union

import numpy as np

from hyprop.batch.runner import run_case
from hyprop.core.config import EngineConfig
from hyprop.core.logging import get_logger

_log = get_logger(__name__)

Metric = Union[str, Callable[[Dict[str, float]], float]]


@dataclass
class Objective:
    """One objective: metric + direction ('min' | 'max')."""

    metric: Metric
    direction: str = "max"

    def value(self, row: Dict[str, float]) -> float:
        raw = self.metric(row) if callable(self.metric) else row[self.metric]
        return -raw if self.direction == "max" else raw   # minimise always


@dataclass
class OptimizationProblem:
    """Decision variables, objectives and inequality constraints g<=0."""

    base_config: EngineConfig
    variables: Dict[str, Tuple[float, float]]           # path -> (lo, hi)
    objectives: List[Objective]
    constraints: List[Callable[[Dict[str, float]], float]] = field(
        default_factory=list)
    penalty: float = 1e9

    @property
    def names(self) -> List[str]:
        return list(self.variables)

    @property
    def bounds(self) -> List[Tuple[float, float]]:
        return [self.variables[n] for n in self.names]

    def evaluate(self, x: Sequence[float]) -> Tuple[List[float], Dict]:
        """Return (objective values [min-form], result row)."""
        case = dict(zip(self.names, (float(v) for v in x)))
        try:
            row = run_case(self.base_config, case)
        except Exception as exc:                        # infeasible design
            _log.debug("Infeasible x=%s (%s)", case, exc)
            return [self.penalty] * len(self.objectives), {}
        values = [obj.value(row) for obj in self.objectives]
        violation = sum(max(g(row), 0.0) for g in self.constraints)
        if violation > 0.0:
            values = [v + self.penalty * (1.0 + violation) for v in values]
        return values, row
