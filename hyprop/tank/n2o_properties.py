"""Saturated nitrous-oxide properties (decision D1: dual backend).

Two interchangeable sources behind one interface:

* :class:`ESDU91022` - engineering correlations (ESDU Item 91022),
  ported 1:1 from the user's validated ``06_hybrid_solver.py``. Fast,
  saturation line only, recommended range ~240-309 K.
* :class:`CoolPropN2O` - full Helmholtz EOS via CoolProp. Reference
  accuracy, adds enthalpy/entropy (needed by HEM/NHNE injector models)
  at ~100x the cost per call.

Default in the solver loop: ESDU; CoolProp for injector thermodynamics
and cross-validation (tested against each other in the test suite).

Sources: ESDU 91022 "Thermophysical properties of nitrous oxide";
Span-Wagner-type EOS in CoolProp (Lemmon & Span 2006); user's
06_hybrid_solver.py.
"""

from __future__ import annotations

import math

from hyprop.core.exceptions import BackendUnavailableError, PropertyRangeError

#: Critical parameters (ESDU 91022; NIST agrees to 4 digits).
T_CRIT = 309.57          # [K]
P_CRIT = 7.251e6         # [Pa]
RHO_CRIT = 452.0         # [kg/m^3]
T_BOIL = 184.7           # [K] normal boiling point
MOLAR_MASS = 0.044013    # [kg/mol]

_T_MIN = 183.0           # validity guard [K]


def _check_range(temperature_k: float) -> None:
    if not (_T_MIN <= temperature_k < T_CRIT):
        raise PropertyRangeError(
            f"N2O saturation properties queried at T={temperature_k} K "
            f"(valid: [{_T_MIN}, {T_CRIT}) K)."
        )


class ESDU91022:
    """ESDU 91022 saturation correlations (user's 06_hybrid_solver port)."""

    name = "esdu_91022"

    @staticmethod
    def psat(temperature_k: float) -> float:
        """Saturation pressure [Pa]."""
        _check_range(temperature_k)
        tr = temperature_k / T_CRIT
        x = 1.0 - tr
        b = (-6.71893, 1.35966, -1.3779, -4.051)
        return P_CRIT * math.exp(
            (1.0 / tr) * (b[0] * x + b[1] * x**1.5 + b[2] * x**2.5 + b[3] * x**5)
        )

    @staticmethod
    def rho_liquid(temperature_k: float) -> float:
        """Saturated liquid density [kg/m^3]."""
        _check_range(temperature_k)
        x = 1.0 - temperature_k / T_CRIT
        b = (1.72328, -0.8395, 0.5106, -0.10412)
        return RHO_CRIT * math.exp(
            b[0] * x ** (1 / 3) + b[1] * x ** (2 / 3) + b[2] * x
            + b[3] * x ** (4 / 3)
        )

    @staticmethod
    def rho_vapor(temperature_k: float) -> float:
        """Saturated vapour density [kg/m^3]."""
        _check_range(temperature_k)
        y = T_CRIT / temperature_k - 1.0
        b = (-1.009, -6.28792, 7.50332, -7.90463, 0.629427)
        return RHO_CRIT * math.exp(
            b[0] * y ** (1 / 3) + b[1] * y ** (2 / 3) + b[2] * y
            + b[3] * y ** (4 / 3) + b[4] * y ** (5 / 3)
        )

    @staticmethod
    def h_vap(temperature_k: float) -> float:
        """Latent heat of vaporisation [J/kg] (Watson-type scaling)."""
        _check_range(temperature_k)
        tr = temperature_k / T_CRIT
        trb = T_BOIL / T_CRIT
        return 376.3e3 * ((1.0 - tr) / (1.0 - trb)) ** 0.38

    @staticmethod
    def cp_liquid(temperature_k: float) -> float:
        """Saturated liquid isobaric heat capacity [J/(kg*K)]."""
        _check_range(temperature_k)
        x = 1.0 - temperature_k / T_CRIT
        return 2499.73 * (
            1.0 + 0.023454 / x - 3.80136 * x + 13.0945 * x**2 - 14.5180 * x**3
        )


class CoolPropN2O:
    """CoolProp full-EOS properties (adds h, s for injector models)."""

    name = "coolprop"
    _FLUID = "NitrousOxide"

    def __init__(self) -> None:
        try:
            import CoolProp.CoolProp as CP
        except ImportError as exc:
            raise BackendUnavailableError(
                "CoolProp is not installed (pip install CoolProp)."
            ) from exc
        self._cp = CP

    def psat(self, temperature_k: float) -> float:
        _check_range(temperature_k)
        return self._cp.PropsSI("P", "T", temperature_k, "Q", 0, self._FLUID)

    def rho_liquid(self, temperature_k: float) -> float:
        _check_range(temperature_k)
        return self._cp.PropsSI("D", "T", temperature_k, "Q", 0, self._FLUID)

    def rho_vapor(self, temperature_k: float) -> float:
        _check_range(temperature_k)
        return self._cp.PropsSI("D", "T", temperature_k, "Q", 1, self._FLUID)

    def h_vap(self, temperature_k: float) -> float:
        _check_range(temperature_k)
        h_v = self._cp.PropsSI("H", "T", temperature_k, "Q", 1, self._FLUID)
        h_l = self._cp.PropsSI("H", "T", temperature_k, "Q", 0, self._FLUID)
        return h_v - h_l

    def cp_liquid(self, temperature_k: float) -> float:
        _check_range(temperature_k)
        return self._cp.PropsSI("C", "T", temperature_k, "Q", 0, self._FLUID)

    # ---- extras used by HEM/NHNE injector models ----------------------
    def h_liquid(self, temperature_k: float) -> float:
        """Saturated liquid specific enthalpy [J/kg]."""
        return self._cp.PropsSI("H", "T", temperature_k, "Q", 0, self._FLUID)

    def s_liquid(self, temperature_k: float) -> float:
        """Saturated liquid specific entropy [J/(kg*K)]."""
        return self._cp.PropsSI("S", "T", temperature_k, "Q", 0, self._FLUID)

    def state_ps(self, pressure_pa: float, entropy_j_kg_k: float):
        """(rho, h) after isentropic expansion to ``pressure_pa``."""
        rho = self._cp.PropsSI("D", "P", pressure_pa, "S", entropy_j_kg_k,
                               self._FLUID)
        h = self._cp.PropsSI("H", "P", pressure_pa, "S", entropy_j_kg_k,
                             self._FLUID)
        return rho, h


def get_n2o_properties(backend: str = "esdu"):
    """Factory: ``'esdu'`` (fast, default) or ``'coolprop'`` (full EOS)."""
    if backend == "esdu":
        return ESDU91022()
    if backend == "coolprop":
        return CoolPropN2O()
    raise ValueError(f"Unknown N2O property backend '{backend}'.")
