"""Cantera-based thermochemistry backend (fallback of decision E0).

Generalises the user's validated script ``07_cantera_punkt0_termochemia.py``:

1. Build an ideal-gas solution from GRI-Mech 3.0 species plus a custom
   fuel *surrogate species* defined by elemental composition and standard
   enthalpy of formation from the fuel database.
2. Chamber: constant-(H, P) equilibrium at (T_ref = 298.15 K, Pc).
3. Throat: isentropic expansion (constant s) to the pressure where the
   flow velocity u = sqrt(2*(h_c - h)) equals the local (frozen) sound
   speed a = sqrt(gamma * R/M * T); solved with Brent's method.
4. Exit: isentropic expansion to the pressure where the local area ratio
   (rho_t * u_t)/(rho * u) matches the requested eps.

Shifting equilibrium re-equilibrates ('SP') at every station (decision
D6 default); frozen mode keeps the chamber composition fixed.

Notes
-----
* The surrogate's cp does not influence results because reactants enter
  exactly at the reference temperature (h(T_ref) = hf identically).
* Sound speed uses the frozen (cp/cv) gamma also in equilibrium mode -
  same approximation as the user's script and HRAP tables; the error on
  c* is well below 1% for these mixtures.

Sources: user's 07_cantera scripts; Gordon & McBride NASA RP-1311;
Goodwin et al., Cantera (https://cantera.org).
"""

from __future__ import annotations

import math
import warnings
from typing import Dict, Optional, Tuple, Union

from scipy.optimize import brentq

from hyprop.core.constants import R_UNIVERSAL, T_REF_THERMO
from hyprop.core.exceptions import (
    BackendUnavailableError,
    ConvergenceError,
    DataError,
)
from hyprop.core.logging import get_logger
from hyprop.core.registry import register_model
from hyprop.cea.backend import (
    CEAResult,
    ExpansionResult,
    StationState,
    ThermochemistryBackend,
)
from hyprop.data import FuelData, OxidizerData, load_fuel, load_oxidizer

_log = get_logger(__name__)

#: Map database oxidizer names to GRI-Mech species.
_OXIDIZER_SPECIES = {"n2o": "N2O", "lox": "O2", "gox": "O2", "htp": "H2O2"}

_FUEL_SPECIES_NAME = "FUEL_SURROGATE"

#: Mass-specific cp of the surrogate [J/(kg*K)]; scaled by molar mass to
#: a molar value. Nearly irrelevant for results (reactants enter at the
#: reference temperature) but a molar cp grossly oversized for a small
#: formula unit (e.g. C2H4) traps 'HP' equilibrate in a cold solution.
#: 2.2e6 J/kmol/K for C32H66 (user's script) == ~4.9e3 J/kg/K.
_SURROGATE_CP_J_KG_K = 4.9e3

_ATOMIC_MASS_KG_KMOL = {"C": 12.011, "H": 1.008, "O": 15.999, "N": 14.007,
                        "S": 32.06, "Cl": 35.45}

#: Surrogate thermo validity range [K] and reference pressure [Pa].
_SURROGATE_T_RANGE = (200.0, 3500.0)

# GRI-Mech NASA polynomials are formally valid to 3000-3500 K; hybrid
# chamber equilibria (~3300 K) extrapolate them marginally. The results
# are cross-validated (<1% vs the user's reference script), so the
# per-call "outside valid range" UserWarnings are noise - silence them.
warnings.filterwarnings(
    "ignore", message=".*outside valid range.*", category=UserWarning)


def carbon_to_oxygen_ratio(fuel: FuelData, oxidizer: OxidizerData, of: float) -> float:
    """Atomic C/O ratio of the propellant mixture at mixture ratio ``of``.

    For C/O >= 1 oxygen cannot convert all carbon to CO and NASA CEA
    predicts condensed carbon C(gr) (e.g. ~1 mol-% for PE/N2O at O/F 3).
    GRI-Mech 3.0 has no condensed phase, so the Cantera backend is only
    valid for C/O < 1 (docs/VALIDATION.md, thermochemistry grid).
    """
    def moles(data, element: str) -> float:
        comp = getattr(data, "composition", None) or data.formula
        molar_mass = sum(_ATOMIC_MASS_KG_KMOL[el] * n for el, n in comp.items())
        return comp.get(element, 0.0) / molar_mass        # kmol element per kg

    carbon = moles(fuel, "C") + of * moles(oxidizer, "C")
    oxygen = moles(fuel, "O") + of * moles(oxidizer, "O")
    return float("inf") if oxygen <= 0.0 else carbon / oxygen


@register_model("cea", "cantera")
class CanteraBackend(ThermochemistryBackend):
    """Shifting-equilibrium / frozen expansion computed with Cantera."""

    name = "cantera"

    def __init__(
        self,
        fuel: Union[str, FuelData] = "ldpe",
        oxidizer: Union[str, OxidizerData] = "n2o",
        mechanism: str = "gri30.yaml",
    ) -> None:
        try:
            import cantera as ct
        except ImportError as exc:
            raise BackendUnavailableError(
                "Cantera is not installed (pip install cantera)."
            ) from exc
        self._ct = ct
        self.fuel = load_fuel(fuel) if isinstance(fuel, str) else fuel
        self.oxidizer = (
            load_oxidizer(oxidizer) if isinstance(oxidizer, str) else oxidizer
        )
        self._ox_species = _OXIDIZER_SPECIES.get(self.oxidizer.name)
        if self._ox_species is None:
            raise DataError(
                f"Oxidizer '{self.oxidizer.name}' has no GRI-Mech mapping."
            )
        if self.fuel.enthalpy_of_formation is None:
            raise DataError(
                f"Fuel '{self.fuel.name}' lacks enthalpy_of_formation "
                "(J/mol per formula unit) required by the Cantera backend."
            )
        self._gas = self._build_solution(mechanism)
        self._warned_carbon = False

    # ------------------------------------------------------------- build
    def _build_solution(self, mechanism: str):
        """GRI-Mech species + custom fuel surrogate in one ideal-gas mix."""
        ct = self._ct
        base = ct.Solution(mechanism)
        composition = " ".join(
            f"{el}:{amount}" for el, amount in self.fuel.composition.items()
        )
        surrogate = ct.Species(_FUEL_SPECIES_NAME, composition)
        hf_j_kmol = self.fuel.enthalpy_of_formation.value * 1000.0  # J/mol -> J/kmol
        molar_mass = sum(
            _ATOMIC_MASS_KG_KMOL[el] * n
            for el, n in self.fuel.composition.items()
        )                                            # [kg/kmol]
        cp_j_kmol_k = _SURROGATE_CP_J_KG_K * molar_mass
        surrogate.thermo = ct.ConstantCp(
            _SURROGATE_T_RANGE[0],
            _SURROGATE_T_RANGE[1],
            101325.0,
            (T_REF_THERMO, hf_j_kmol, 0.0, cp_j_kmol_k),
        )
        return ct.Solution(
            thermo="ideal-gas", species=[surrogate] + list(base.species())
        )

    # ------------------------------------------------------------- query
    def query(self, of: float, pc: float, eps: float) -> CEAResult:
        if of <= 0 or pc <= 0 or eps <= 1.0:
            raise ValueError("Require of > 0, pc > 0, eps > 1.")
        if (not self._warned_carbon
                and carbon_to_oxygen_ratio(self.fuel, self.oxidizer, of) >= 1.0):
            self._warned_carbon = True
            _log.warning(
                "Cantera backend queried at O/F=%.2f with atomic C/O >= 1: "
                "condensed carbon is not modelled (gri30); Tc/Te errors of "
                "1-4 %% vs NASA CEA. Use the RocketCEA backend for fuel-rich "
                "points.", of)
        gas = self._gas

        # --- chamber: HP equilibrium at reactant reference state --------
        gas.TPY = (
            T_REF_THERMO,
            pc,
            {_FUEL_SPECIES_NAME: 1.0 / (1.0 + of),
             self._ox_species: of / (1.0 + of)},
        )
        self._check_condensed_carbon(of)
        gas.equilibrate("HP")
        chamber = self._station(gas, equilibrium=True)
        h_c = gas.enthalpy_mass
        s_c = gas.entropy_mass
        composition_c = dict(
            zip(gas.species_names, gas.X)
        )
        mole_fractions = {
            name: x for name, x in composition_c.items() if x > 1e-6
        }

        # --- shifting-equilibrium expansion (D6 default) -----------------
        throat_eq, g_throat, cstar = self._solve_throat(h_c, s_c, pc, frozen=False)
        exit_eq, ve_eq = self._solve_exit(h_c, s_c, pc, eps, g_throat, frozen=False)

        # --- frozen-from-chamber expansion (lower bound) ------------------
        self._restore_chamber(chamber, composition_c)
        _, g_throat_fr, _ = self._solve_throat(h_c, s_c, pc, frozen=True,
                                               composition=composition_c)
        exit_fr, ve_fr = self._solve_exit(h_c, s_c, pc, eps, g_throat_fr,
                                          frozen=True, composition=composition_c)

        return CEAResult(
            of=of, pc_pa=pc, eps=eps,
            chamber=chamber, throat=throat_eq,
            equilibrium=ExpansionResult(exit_eq, ve_eq),
            frozen=ExpansionResult(exit_fr, ve_fr),
            cstar_m_s=cstar,
            mole_fractions=mole_fractions,
            backend=self.name,
        )

    # ----------------------------------------------------------- helpers
    def _check_condensed_carbon(self, of: float) -> None:
        """Warn (once per backend) when elemental C/O > 1.

        GRI-Mech 3.0 has no condensed phase, while the true equilibrium of
        a C/H/O/N mixture with C/O > 1 contains solid carbon (NASA CEA
        gives C(gr)). For PE/N2O this is O/F < ~3.3; vs NASA CEA, Tc is
        then off by up to ~1.4 % and c* by ~0.6 % at O/F 3
        (docs/VALIDATION.md, item 2). Use RocketCEA for such points.
        """
        gas = self._gas
        c_to_o = gas.elemental_mole_fraction("C") / max(
            gas.elemental_mole_fraction("O"), 1e-30)
        if c_to_o > 1.0 and not getattr(self, "_warned_carbon", False):
            self._warned_carbon = True
            _log.warning(
                "Cantera backend: C/O = %.2f > 1 at O/F = %.2f - equilibrium "
                "should contain condensed carbon, which gri30 lacks; results "
                "are biased (use RocketCEA for fuel-rich points).", c_to_o, of)

    def _station(self, gas, equilibrium: bool = False) -> StationState:
        return StationState(
            temperature_k=gas.T,
            pressure_pa=gas.P,
            gamma=gas.cp / gas.cv,
            molar_mass_kg_mol=gas.mean_molecular_weight / 1000.0,
            cp_j_kg_k=gas.cp,
            gamma_eq=self._gamma_equilibrium(gas) if equilibrium else None,
        )

    @staticmethod
    def _gamma_equilibrium(gas, rel_dp: float = 1e-4) -> float:
        """gamma_s = (d ln p / d ln rho)_s at shifting equilibrium.

        Central difference along the isentrope, composition re-equilibrated
        at both points (definition of CEA's GAMMAs, NASA RP-1311 Eq. 2.71).
        The gas object is restored to its original (T, P, X) afterwards.
        """
        t0, p0, x0 = gas.T, gas.P, gas.X.copy()
        s0 = gas.entropy_mass
        rho = []
        for factor in (1.0 - rel_dp, 1.0 + rel_dp):
            gas.SP = s0, p0 * factor
            gas.equilibrate("SP")
            rho.append(gas.density)
        gas.TPX = t0, p0, x0
        return math.log((1.0 + rel_dp) / (1.0 - rel_dp)) / math.log(rho[1] / rho[0])

    def _restore_chamber(self, chamber: StationState, composition) -> None:
        self._gas.TPX = (
            chamber.temperature_k, chamber.pressure_pa, composition
        )

    def _set_sp(self, s: float, p: float, frozen: bool, composition) -> None:
        """Set (s, p); re-equilibrate unless frozen."""
        gas = self._gas
        if frozen:
            gas.TPX = gas.T, gas.P, composition  # pin composition
            gas.SP = s, p
        else:
            gas.SP = s, p
            gas.equilibrate("SP")

    def _flow_state(
        self, p: float, h_c: float, s_c: float, frozen: bool, composition
    ) -> Tuple[float, float, float]:
        """Return (u, a, rho) after isentropic expansion to pressure p."""
        gas = self._gas
        self._set_sp(s_c, p, frozen, composition)
        u_sq = 2.0 * (h_c - gas.enthalpy_mass)
        u = math.sqrt(max(u_sq, 0.0))
        gamma = gas.cp / gas.cv
        a = math.sqrt(
            gamma * (R_UNIVERSAL / (gas.mean_molecular_weight / 1000.0)) * gas.T
        )
        return u, a, gas.density

    def _solve_throat(
        self, h_c: float, s_c: float, pc: float,
        frozen: bool = False, composition: Optional[Dict] = None,
    ) -> Tuple[StationState, float, float]:
        """Find throat (u = a); return (state, mass flux G_t, c*)."""
        def residual(p: float) -> float:
            u, a, _ = self._flow_state(p, h_c, s_c, frozen, composition)
            return u - a

        try:
            p_throat = brentq(residual, 0.30 * pc, 0.80 * pc, xtol=1.0)
        except ValueError as exc:
            raise ConvergenceError("Throat condition u=a not bracketed.") from exc
        u_t, _, rho_t = self._flow_state(p_throat, h_c, s_c, frozen, composition)
        g_throat = rho_t * u_t                      # mdot / At [kg/(m^2 s)]
        cstar = pc / g_throat                       # c* = pc*At/mdot
        return self._station(self._gas, equilibrium=not frozen), g_throat, cstar

    def _solve_exit(
        self, h_c: float, s_c: float, pc: float, eps: float, g_throat: float,
        frozen: bool = False, composition: Optional[Dict] = None,
    ) -> Tuple[StationState, float]:
        """Find exit pressure matching the area ratio; return (state, ve)."""
        def residual(p: float) -> float:
            u, _, rho = self._flow_state(p, h_c, s_c, frozen, composition)
            if u <= 0.0 or rho <= 0.0:
                return 1e9
            return g_throat / (rho * u) - eps       # local A/At - eps

        # Bracket around the ideal-gas estimate of pe (avoids equilibrate
        # calls at extreme vacuum, which destabilise rich/lean mixtures).
        from hyprop.physics.compressible import exit_pressure_ratio
        gamma_c = self._gas.cp / self._gas.cv
        pe_estimate = pc * exit_pressure_ratio(eps, min(max(gamma_c, 1.05),
                                                        1.66))
        lower, upper = 0.2 * pe_estimate, min(5.0 * pe_estimate, 0.5 * pc)
        try:
            p_exit = brentq(residual, lower, upper, xtol=0.1)
        except ValueError:
            try:                                    # widen once
                p_exit = brentq(residual, 0.02 * pe_estimate, 0.5 * pc,
                                xtol=0.1)
            except ValueError as exc:
                raise ConvergenceError(
                    f"Exit area-ratio eps={eps} not bracketed."
                ) from exc
        ve, _, _ = self._flow_state(p_exit, h_c, s_c, frozen, composition)
        return self._station(self._gas, equilibrium=not frozen), ve
