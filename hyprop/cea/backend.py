"""Thermochemistry backend interface (stage E2).

Every backend answers one question: *given O/F, chamber pressure and
nozzle area ratio, what are the combustion-product properties at the
chamber, throat and exit?* Backends return a :class:`CEAResult`; the rest
of HyProp never talks to RocketCEA/Cantera directly.

Nozzle chemistry (decision D6, 2026-07-16): **shifting equilibrium is the
default**; frozen-from-chamber values are always computed alongside and
reported as the conservative lower bound.

Sources: NASA RP-1311 (Gordon & McBride, CEA analysis); Sutton &
Biblarz 9th ed., Ch. 3, 5.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from hyprop.core.constants import G0
from hyprop.core.exceptions import BackendUnavailableError
from hyprop.core.logging import get_logger

_log = get_logger(__name__)


@dataclass(frozen=True)
class StationState:
    """Gas state at one nozzle station (chamber / throat / exit).

    Two isentropic exponents are distinguished explicitly (they differ by
    ~7 % in a hybrid chamber at ~3300 K, so mixing them is not harmless):

    * ``gamma``    - **frozen** cp/cv of the local mixture (composition held
      fixed). Same in every backend. This is what ideal-gas nozzle
      relations with a "chamber gamma" (HRAP tables, user's 07 script) use.
    * ``gamma_eq`` - **equilibrium** isentropic exponent
      gamma_s = (d ln p / d ln rho)_s with composition re-equilibrated
      (NASA CEA "GAMMAs", RP-1311 Eq. 2.71). ``None`` for frozen stations.

    ``cp_j_kg_k`` is the frozen cp, consistent with ``gamma``.
    """

    temperature_k: float
    pressure_pa: float
    gamma: float  #: frozen cp/cv at the station [-]
    molar_mass_kg_mol: float
    cp_j_kg_k: float | None = None  #: frozen cp [J/(kg*K)]
    gamma_eq: float | None = None  #: equilibrium gamma_s [-]

    @property
    def r_specific_j_kg_k(self) -> float:
        """Specific gas constant R = R_u / M [J/(kg*K)]."""
        from hyprop.core.constants import R_UNIVERSAL

        return R_UNIVERSAL / self.molar_mass_kg_mol

    @property
    def cv_j_kg_k(self) -> float | None:
        """Specific heat at constant volume [J/(kg*K)] (if cp known)."""
        return None if self.cp_j_kg_k is None else self.cp_j_kg_k / self.gamma


@dataclass(frozen=True)
class ExpansionResult:
    """Result of expanding to the nozzle exit under one chemistry model."""

    exit_state: StationState
    exhaust_velocity_m_s: float  #: ve at the exit plane [m/s]

    def isp_s(
        self, ambient_pressure_pa: float, eps: float, cstar_m_s: float, pc_pa: float
    ) -> float:
        """Delivered-ideal Isp [s] at given ambient pressure.

        Isp = [ve + (pe - pa) * Ae / mdot] / g0, with
        Ae/mdot = eps * cstar / pc  (from mdot = pc*At/cstar).
        """
        area_per_mdot = eps * cstar_m_s / pc_pa
        thrust_per_mdot = (
            self.exhaust_velocity_m_s
            + (self.exit_state.pressure_pa - ambient_pressure_pa) * area_per_mdot
        )
        return thrust_per_mdot / G0


@dataclass(frozen=True)
class CEAResult:
    """Complete thermochemistry answer for one (O/F, Pc, eps) point."""

    of: float
    pc_pa: float
    eps: float
    chamber: StationState
    throat: StationState
    equilibrium: ExpansionResult  #: shifting-equilibrium expansion (default)
    frozen: ExpansionResult  #: frozen-from-chamber expansion (lower bound)
    cstar_m_s: float
    mole_fractions: dict[str, float] = field(default_factory=dict)
    backend: str = ""

    def isp_s(self, ambient_pressure_pa: float, mode: str = "equilibrium") -> float:
        """Ideal Isp [s] at ambient pressure, per D6 default mode."""
        expansion = self.equilibrium if mode == "equilibrium" else self.frozen
        return expansion.isp_s(ambient_pressure_pa, self.eps, self.cstar_m_s, self.pc_pa)


class ThermochemistryBackend(ABC):
    """Common interface of RocketCEA / Cantera / native-CEA backends."""

    name: str = "abstract"

    @abstractmethod
    def query(self, of: float, pc: float, eps: float) -> CEAResult:
        """Compute combustion and expansion properties.

        Args:
            of: Oxidizer-to-fuel mass ratio [-].
            pc: Chamber (stagnation) pressure [Pa].
            eps: Nozzle expansion area ratio Ae/At [-].

        Returns:
            Chamber state, ideal c*, and the exit expansion under shifting
            equilibrium and frozen-at-chamber chemistry.
        """


def get_backend(name: str = "auto", **kwargs) -> ThermochemistryBackend:
    """Instantiate a thermochemistry backend.

    ``"auto"`` tries RocketCEA first (native NASA CEA results), then
    Cantera. The Cantera backend (GRI-Mech 3.0) has no condensed carbon and
    is accurate only for atomic C/O < 1 (docs/VALIDATION.md).

    Args:
        name: ``"auto"``, ``"rocketcea"`` or ``"cantera"``.
        **kwargs: Backend arguments, typically ``fuel`` and ``oxidizer``
            database keys.

    Returns:
        A backend whose :meth:`ThermochemistryBackend.query` answers
        (O/F, Pc, eps) points.
    """
    from hyprop.core.registry import autodiscover, get_model

    autodiscover()
    if name != "auto":
        return get_model("cea", name)(**kwargs)
    errors = []
    for candidate in ("rocketcea", "cantera"):
        try:
            backend = get_model("cea", candidate)(**kwargs)
            _log.info("Thermochemistry backend: %s", candidate)
            return backend
        except BackendUnavailableError as exc:
            errors.append(f"{candidate}: {exc}")
    raise BackendUnavailableError("No thermochemistry backend available. " + " | ".join(errors))
