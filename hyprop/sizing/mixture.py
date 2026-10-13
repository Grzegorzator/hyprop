"""Optimum mixture ratio from the thermochemistry backend.

The design O/F of the sizing is the O/F that maximises the ideal
(shifting-equilibrium) specific impulse at the design chamber pressure,
nozzle expansion and ambient pressure, computed for the actual propellant
pair rather than taken from a constant.

For PE/N2O the Isp curve is flat around the optimum (within 1 % for
O/F ~ 6.5-9.3 at 25-35 bar, eps 5; NASA CEA via RocketCEA) and steeper on
the fuel-rich side, so a few percent error in the optimum costs little,
while running fuel-rich costs a lot.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar

from hyprop.cea.backend import ThermochemistryBackend

#: Default O/F search interval. The lower bound stays above atomic C/O = 1
#: for CH2-type fuels with N2O (O/F = 44/14 = 3.14), where gas-phase-only
#: backends (Cantera/GRI-Mech) lose accuracy.
OF_BOUNDS = (3.5, 14.0)


def optimal_of(
    cea: ThermochemistryBackend,
    pc_pa: float,
    expansion_ratio: float,
    ambient_pa: float,
    bounds: tuple[float, float] = OF_BOUNDS,
    grid_step: float = 0.25,
) -> float:
    """O/F maximising the ideal equilibrium Isp.

    A coarse grid locates the maximum (robust against the flat top), then
    a bounded scalar search refines it inside the neighbouring grid cells.

    Args:
        cea: Thermochemistry backend for the propellant pair.
        pc_pa: Chamber pressure [Pa].
        expansion_ratio: Nozzle area ratio A_e/A_t [-].
        ambient_pa: Ambient pressure for the Isp pressure term [Pa].
        bounds: O/F search interval [-].
        grid_step: Coarse grid spacing in O/F [-].

    Returns:
        The Isp-optimal O/F [-] (to ~0.01).
    """

    def isp(of: float) -> float:
        return cea.query(float(of), pc_pa, expansion_ratio).isp_s(ambient_pa)

    grid = np.arange(bounds[0], bounds[1] + 0.5 * grid_step, grid_step)
    values = np.array([isp(of) for of in grid])
    i = int(np.argmax(values))
    lo = grid[max(i - 1, 0)]
    hi = grid[min(i + 1, len(grid) - 1)]
    if hi <= lo:
        return float(grid[i])
    res = minimize_scalar(
        lambda of: -isp(of), bounds=(lo, hi), method="bounded", options={"xatol": 0.01}
    )
    return float(res.x) if -res.fun >= values[i] else float(grid[i])
