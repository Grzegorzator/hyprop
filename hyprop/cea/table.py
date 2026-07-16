"""Grid-tabulated thermochemistry (HRAP-style lookup tables).

HRAP ships RPA-generated tables T(Pc, OF), gamma(Pc, OF), M(Pc, OF) and
interpolates during the transient. This module reproduces that pattern
on top of any :class:`ThermochemistryBackend`: a one-time grid sweep at
fixed eps, then bilinear interpolation (``RegularGridInterpolator``) of
every scalar the solver needs. Speed-up vs direct Cantera queries:
~1000x per time step.

Interpolated scalars: cstar, chamber T/gamma/M/cp, exit ve/pe/T for both
equilibrium and frozen expansion.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from hyprop.cea.backend import (
    CEAResult,
    ExpansionResult,
    StationState,
    ThermochemistryBackend,
)
from hyprop.core.logging import get_logger

_log = get_logger(__name__)

_FIELDS = (
    "cstar", "t_c", "gamma_c", "m_c", "cp_c",
    "t_t", "p_t", "gamma_t", "m_t",
    "ve_eq", "pe_eq", "te_eq", "gamma_e", "m_e",
    "ve_fr", "pe_fr", "te_fr",
)


class TabulatedBackend(ThermochemistryBackend):
    """Bilinear interpolation over a precomputed (O/F, Pc) grid."""

    name = "tabulated"

    def __init__(
        self,
        backend: ThermochemistryBackend,
        of_grid: Sequence[float],
        pc_grid: Sequence[float],
        eps: float,
    ) -> None:
        self._eps = eps
        of_grid = np.asarray(of_grid, dtype=float)
        pc_grid = np.asarray(pc_grid, dtype=float)
        tables = {name: np.empty((of_grid.size, pc_grid.size))
                  for name in _FIELDS}
        _log.info(
            "Building CEA table: %d x %d points (eps=%.2f)",
            of_grid.size, pc_grid.size, eps,
        )
        for i, of in enumerate(of_grid):
            for j, pc in enumerate(pc_grid):
                r = backend.query(float(of), float(pc), eps)
                tables["cstar"][i, j] = r.cstar_m_s
                tables["t_c"][i, j] = r.chamber.temperature_k
                tables["gamma_c"][i, j] = r.chamber.gamma
                tables["m_c"][i, j] = r.chamber.molar_mass_kg_mol
                tables["cp_c"][i, j] = r.chamber.cp_j_kg_k or 0.0
                tables["t_t"][i, j] = r.throat.temperature_k
                tables["p_t"][i, j] = r.throat.pressure_pa
                tables["gamma_t"][i, j] = r.throat.gamma
                tables["m_t"][i, j] = r.throat.molar_mass_kg_mol
                eq, fr = r.equilibrium, r.frozen
                tables["ve_eq"][i, j] = eq.exhaust_velocity_m_s
                tables["pe_eq"][i, j] = eq.exit_state.pressure_pa
                tables["te_eq"][i, j] = eq.exit_state.temperature_k
                tables["gamma_e"][i, j] = eq.exit_state.gamma
                tables["m_e"][i, j] = eq.exit_state.molar_mass_kg_mol
                tables["ve_fr"][i, j] = fr.exhaust_velocity_m_s
                tables["pe_fr"][i, j] = fr.exit_state.pressure_pa
                tables["te_fr"][i, j] = fr.exit_state.temperature_k
        self._interp = {
            name: RegularGridInterpolator(
                (of_grid, pc_grid), tables[name],
                bounds_error=False, fill_value=None,   # linear extrapolation
            )
            for name in _FIELDS
        }
        self.of_range = (float(of_grid[0]), float(of_grid[-1]))
        self.pc_range = (float(pc_grid[0]), float(pc_grid[-1]))

    def query(self, of: float, pc: float, eps: float) -> CEAResult:
        if abs(eps - self._eps) > 1e-9:
            raise ValueError(
                f"Table built for eps={self._eps}, queried eps={eps}."
            )
        point = np.array([[of, pc]])
        value = {name: float(self._interp[name](point)[0])
                 for name in _FIELDS}
        chamber = StationState(value["t_c"], pc, value["gamma_c"],
                               value["m_c"], value["cp_c"] or None)
        throat = StationState(value["t_t"], value["p_t"],
                              value["gamma_t"], value["m_t"])
        exit_eq = StationState(value["te_eq"], value["pe_eq"],
                               value["gamma_e"], value["m_e"])
        exit_fr = StationState(value["te_fr"], value["pe_fr"],
                               value["gamma_c"], value["m_c"])
        return CEAResult(
            of=of, pc_pa=pc, eps=eps, chamber=chamber, throat=throat,
            equilibrium=ExpansionResult(exit_eq, value["ve_eq"]),
            frozen=ExpansionResult(exit_fr, value["ve_fr"]),
            cstar_m_s=value["cstar"], backend=self.name,
        )
