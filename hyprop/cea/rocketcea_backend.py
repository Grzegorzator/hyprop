"""RocketCEA-based thermochemistry backend (primary, decision E0).

Thin adapter around ``rocketcea.cea_obj_w_units.CEA_Obj`` (SI units),
which wraps the original NASA CEA FORTRAN code (Gordon & McBride,
RP-1311). Custom fuels are injected as CEA cards built from the fuel
database (elemental composition + standard enthalpy of formation).

Exit conditions are reconstructed from CEA's Mach number and sonic
velocity at the exit plane (ve = Me * ae) so that the ExpansionResult is
defined identically in both backends (cross-validation E2).

Requires: ``pip install rocketcea`` (needs a Fortran compiler on the
machine; on Windows see RocketCEA docs re. MinGW).
"""

from __future__ import annotations

from hyprop.cea.backend import (
    CEAResult,
    ExpansionResult,
    StationState,
    ThermochemistryBackend,
)
from hyprop.core.constants import R_UNIVERSAL
from hyprop.core.exceptions import BackendUnavailableError, DataError
from hyprop.core.logging import get_logger
from hyprop.core.registry import register_model
from hyprop.data import FuelData, OxidizerData, load_fuel, load_oxidizer

_log = get_logger(__name__)

_J_PER_CAL = 4.184

#: Map database oxidizer names to RocketCEA built-in propellant names.
_OXIDIZER_CEA = {"n2o": "N2O", "lox": "LOX", "gox": "GOX"}


def _fuel_card(fuel: FuelData) -> str:
    """Build a CEA fuel card from composition + enthalpy of formation.

    Card format per RocketCEA ``add_new_fuel`` documentation.
    """
    if fuel.enthalpy_of_formation is None:
        raise DataError(
            f"Fuel '{fuel.name}' lacks enthalpy_of_formation "
            "(J/mol per formula unit) required for a CEA card."
        )
    elements = "  ".join(f"{el} {amount:g}" for el, amount in fuel.composition.items())
    hf_cal_mol = fuel.enthalpy_of_formation.value / _J_PER_CAL
    return (
        f"fuel {fuel.name.upper()}  {elements}    wt%=100.00\n"
        f"h,cal={hf_cal_mol:.1f}    t(k)=298.15\n"
    )


@register_model("cea", "rocketcea")
class RocketCEABackend(ThermochemistryBackend):
    """NASA CEA (via RocketCEA) with SI-unit interface."""

    name = "rocketcea"

    def __init__(
        self,
        fuel: str | FuelData = "ldpe",
        oxidizer: str | OxidizerData = "n2o",
    ) -> None:
        try:
            from rocketcea.cea_obj import add_new_fuel
            from rocketcea.cea_obj_w_units import CEA_Obj
        except ImportError as exc:
            raise BackendUnavailableError(
                "RocketCEA is not installed (pip install rocketcea; requires a Fortran compiler)."
            ) from exc

        self.fuel = load_fuel(fuel) if isinstance(fuel, str) else fuel
        self.oxidizer = load_oxidizer(oxidizer) if isinstance(oxidizer, str) else oxidizer
        ox_name = _OXIDIZER_CEA.get(self.oxidizer.name)
        if ox_name is None:
            raise DataError(f"Oxidizer '{self.oxidizer.name}' has no RocketCEA mapping yet.")
        fuel_name = f"HYPROP_{self.fuel.name.upper()}"
        add_new_fuel(fuel_name, _fuel_card(self.fuel))

        self._cea = CEA_Obj(
            oxName=ox_name,
            fuelName=fuel_name,
            pressure_units="Pa",
            cstar_units="m/s",
            temperature_units="K",
            sonic_velocity_units="m/s",
            enthalpy_units="J/kg",
            density_units="kg/m^3",
            specific_heat_units="J/kg-K",
            isp_units="sec",
        )

    # ------------------------------------------------------------- query
    def query(self, of: float, pc: float, eps: float) -> CEAResult:
        """Query NASA CEA through RocketCEA (SI in and out)."""
        if of <= 0 or pc <= 0 or eps <= 1.0:
            raise ValueError("Require of > 0, pc > 0, eps > 1.")
        cea = self._cea

        t_chamber, t_throat, t_exit = cea.get_Temperatures(
            Pc=pc, MR=of, eps=eps, frozen=0, frozenAtThroat=0
        )
        # CEA's get_*_MolWt_gamma return the EQUILIBRIUM exponent GAMMAs;
        # the frozen cp/cv (HyProp's StationState.gamma) is rebuilt from
        # the frozen cp: gamma_fr = cp_fr / (cp_fr - R/M).
        mw_c, gamma_s_c = cea.get_Chamber_MolWt_gamma(Pc=pc, MR=of, eps=eps)
        mw_t, gamma_s_t = cea.get_Throat_MolWt_gamma(Pc=pc, MR=of, eps=eps)
        mw_e, gamma_s_e = cea.get_exit_MolWt_gamma(Pc=pc, MR=of, eps=eps)
        cp_fr_c, cp_fr_t, cp_fr_e = cea.get_HeatCapacities(Pc=pc, MR=of, eps=eps, frozen=1)

        def gamma_frozen(cp_fr: float, mw_g_mol: float) -> float:
            r_specific = R_UNIVERSAL / (mw_g_mol / 1000.0)
            return cp_fr / (cp_fr - r_specific)

        cstar = cea.get_Cstar(Pc=pc, MR=of)
        pc_over_pe = cea.get_PcOvPe(Pc=pc, MR=of, eps=eps)
        p_exit = pc / pc_over_pe
        p_throat = pc / cea.get_Throat_PcOvPe(Pc=pc, MR=of)

        chamber = StationState(
            t_chamber, pc, gamma_frozen(cp_fr_c, mw_c), mw_c / 1000.0, cp_fr_c, gamma_eq=gamma_s_c
        )
        # Throat/exit frozen cp: RocketCEA exposes it only for the frozen
        # expansion (same composition, slightly different T); used for the
        # informational frozen gamma at these stations only.
        throat = StationState(
            t_throat,
            p_throat,
            gamma_frozen(cp_fr_t, mw_c),
            mw_t / 1000.0,
            cp_fr_t,
            gamma_eq=gamma_s_t,
        )

        # -- equilibrium exit: ve = Me * ae ------------------------------
        mach_e = cea.get_MachNumber(Pc=pc, MR=of, eps=eps, frozen=0)
        _, _, a_exit = cea.get_SonicVelocities(Pc=pc, MR=of, eps=eps, frozen=0)
        exit_eq = StationState(
            t_exit, p_exit, gamma_frozen(cp_fr_e, mw_c), mw_e / 1000.0, cp_fr_e, gamma_eq=gamma_s_e
        )
        equilibrium = ExpansionResult(exit_eq, mach_e * a_exit)

        # -- frozen (from chamber) exit ----------------------------------
        _, _, t_exit_fr = cea.get_Temperatures(Pc=pc, MR=of, eps=eps, frozen=1, frozenAtThroat=0)
        pc_over_pe_fr = cea.get_PcOvPe(Pc=pc, MR=of, eps=eps, frozen=1)
        mach_fr = cea.get_MachNumber(Pc=pc, MR=of, eps=eps, frozen=1)
        _, _, a_exit_fr = cea.get_SonicVelocities(Pc=pc, MR=of, eps=eps, frozen=1)
        exit_fr = StationState(
            t_exit_fr,
            pc / pc_over_pe_fr,
            gamma_frozen(cp_fr_e, mw_c),
            mw_c / 1000.0,
            cp_fr_e,
        )
        frozen = ExpansionResult(exit_fr, mach_fr * a_exit_fr)

        mole_fractions = {}
        try:
            _, mole_fractions = cea.get_SpeciesMoleFractions(
                Pc=pc, MR=of, eps=eps, min_fraction=1e-6
            )
            mole_fractions = {name: values[0] for name, values in mole_fractions.items()}
        except Exception:  # pragma: no cover
            _log.debug("Species mole fractions unavailable.")

        return CEAResult(
            of=of,
            pc_pa=pc,
            eps=eps,
            chamber=chamber,
            throat=throat,
            equilibrium=equilibrium,
            frozen=frozen,
            cstar_m_s=cstar,
            mole_fractions=mole_fractions,
            backend=self.name,
        )
