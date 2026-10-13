"""Nozzle loss models (stage E4; full sizing arrives at E8).

Divergence loss of a conical nozzle (Sutton Eq. 3-34):

    lambda = (1 + cos(alpha)) / 2

where ``alpha`` is the divergence half-angle. For the standard 15 deg
cone lambda = 0.9830. Bell nozzles are treated via an equivalent
efficiency (to be extended at E8 with length-fraction correlations,
Rao / Sutton Ch. 3).

In the transient (Sutton Sec. 3.5 correction factors, Eq. 3-34 note):

    F = eta_c* * eta_nozzle * mdot * [lambda * ve + (pe - pa) * eps * c* / pc]

lambda multiplies the momentum term only; eta_nozzle (other losses) the
whole delivered C_F.
"""

from __future__ import annotations

import math

from hyprop.core.exceptions import ConfigError


def divergence_efficiency(half_angle_deg: float) -> float:
    """Conical-nozzle divergence factor lambda (Sutton Eq. 3-34)."""
    if not (0.0 < half_angle_deg < 90.0):
        raise ConfigError("Half-angle must be in (0, 90) deg.")
    return 0.5 * (1.0 + math.cos(math.radians(half_angle_deg)))


def nozzle_efficiency(
    half_angle_deg: float, extra_efficiency: float = 1.0
) -> float:
    """Combined nozzle momentum efficiency: lambda * eta_extra.

    ``extra_efficiency`` collects boundary-layer/roughness/erosion effects
    supplied by the user (EngineConfig.nozzle.efficiency).
    """
    if not (0.0 < extra_efficiency <= 1.0):
        raise ConfigError("extra_efficiency must be in (0, 1].")
    return divergence_efficiency(half_angle_deg) * extra_efficiency
