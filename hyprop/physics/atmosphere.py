"""International Standard Atmosphere (ISA), troposphere + low stratosphere.

    T(h) = T0 - L*h                        (h <= 11 km, L = 6.5 K/km)
    p(h) = p0 * (T/T0)^(g0*M_air/(R*L))    (ISO 2533:1975)
    h in geopotential metres; valid here to 20 km.

Sources: ISO 2533:1975; U.S. Standard Atmosphere 1976.
"""

from __future__ import annotations

import math

from hyprop.core.constants import G0, P_ATM_SL, R_UNIVERSAL, T_ATM_SL

M_AIR = 0.0289644  # [kg/mol] mean molar mass of dry air (ISO 2533)
LAPSE_RATE = 0.0065  # [K/m] tropospheric lapse rate
H_TROPOPAUSE = 11_000.0  # [m]
T_TROPOPAUSE = T_ATM_SL - LAPSE_RATE * H_TROPOPAUSE  # 216.65 K
_EXPONENT = G0 * M_AIR / (R_UNIVERSAL * LAPSE_RATE)  # ~5.2559
P_TROPOPAUSE = P_ATM_SL * (T_TROPOPAUSE / T_ATM_SL) ** _EXPONENT


def temperature(altitude_m: float) -> float:
    """ISA temperature [K] (0-20 km)."""
    _check(altitude_m)
    if altitude_m <= H_TROPOPAUSE:
        return T_ATM_SL - LAPSE_RATE * altitude_m
    return T_TROPOPAUSE


def pressure(altitude_m: float) -> float:
    """ISA static pressure [Pa] (0-20 km)."""
    _check(altitude_m)
    if altitude_m <= H_TROPOPAUSE:
        return P_ATM_SL * (temperature(altitude_m) / T_ATM_SL) ** _EXPONENT
    return P_TROPOPAUSE * math.exp(
        -G0 * M_AIR * (altitude_m - H_TROPOPAUSE) / (R_UNIVERSAL * T_TROPOPAUSE)
    )


def density(altitude_m: float) -> float:
    """ISA density [kg/m^3] from the ideal-gas law."""
    return pressure(altitude_m) * M_AIR / (R_UNIVERSAL * temperature(altitude_m))


def _check(altitude_m: float) -> None:
    if not (-500.0 <= altitude_m <= 20_000.0):
        raise ValueError(f"ISA model valid 0-20 km, got {altitude_m} m.")
