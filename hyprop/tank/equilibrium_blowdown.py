"""Thermodynamic-equilibrium adiabatic N2O blowdown (decision D2).

Model (HRAP Theory, Sec. I "Oxidizer Tank Model"; Whitmore & Chandler,
JPP 2010; user's 06_hybrid_solver energy balance is a variant):

Liquid phase (self-pressurised, saturated):
1. Remove the mass drawn by the injector from the liquid.
2. The tank returns to equilibrium: a mass ``dm_v`` of liquid vaporises,
   absorbing latent heat and cooling the contents:

       T_new = T - h_vap(T) * dm_v / (m_liq * cp_liq(T))

3. ``dm_v`` is found (Brent) so that liquid + vapour exactly fill the
   fixed tank volume at the new temperature:

       m_liq/rho_l(T_new) + m_vap/rho_v(T_new) = V_tank

4. Tank pressure = saturation pressure at the new temperature.

Vapour phase (after liquid run-out, LRO): adiabatic expansion of the
remaining vapour treated as an ideal gas along a polytrope,

    p/p_LRO = (m/m_LRO)^k,  T/T_LRO = (m/m_LRO)^(k-1),

with k = gamma_vapour (isentropic) by default. Real-gas vapour phase
(CoolProp) is decision D7 - the polytropic exponent is a parameter so
both can be compared later. The gas phase contributes little impulse
(cf. ROP module rationale) but must be simulated for phase statistics.

Sources: HRAP Theory; Whitmore & Chandler 2010; Fernandez MSc (blowdown
modelling); ESDU 91022 correlations.
"""

from __future__ import annotations

from scipy.optimize import brentq

from hyprop.core.constants import R_UNIVERSAL
from hyprop.core.exceptions import ConfigError, ConvergenceError
from hyprop.core.logging import get_logger
from hyprop.core.registry import register_model
from hyprop.tank.base import FluidState, TankModel, TankState
from hyprop.tank.n2o_properties import MOLAR_MASS, get_n2o_properties

_log = get_logger(__name__)

#: Ideal-gas isentropic exponent of N2O vapour (near-ambient; D7 default).
GAMMA_N2O_VAPOR = 1.27

#: Specific gas constant of N2O [J/(kg*K)] = R_u / M.
R_N2O = R_UNIVERSAL / MOLAR_MASS


@register_model("tank", "equilibrium_blowdown")
class EquilibriumBlowdownTank(TankModel):
    """Self-pressurising saturated N2O tank in constant equilibrium."""

    def __init__(
        self,
        volume_m3: float,
        oxidizer_mass_kg: float,
        temperature_k: float,
        properties: str = "esdu",
        polytropic_exponent: float = GAMMA_N2O_VAPOR,
    ) -> None:
        if volume_m3 <= 0 or oxidizer_mass_kg <= 0:
            raise ConfigError("Tank volume and oxidizer mass must be positive.")
        self._props = get_n2o_properties(properties)
        self._volume = volume_m3
        self._temperature = temperature_k
        self._time = 0.0
        self._poly_k = polytropic_exponent

        # Initial liquid/vapour split from mass + volume constraints:
        #   m_l/rho_l + m_v/rho_v = V,  m_l + m_v = m
        rho_l = self._props.rho_liquid(temperature_k)
        rho_v = self._props.rho_vapor(temperature_k)
        m_vap = (volume_m3 - oxidizer_mass_kg / rho_l) / (1.0 / rho_v - 1.0 / rho_l)
        if m_vap < 0.0:
            raise ConfigError("Oxidizer mass exceeds liquid-full tank (overfilled).")
        m_liq = oxidizer_mass_kg - m_vap
        if m_liq <= 0.0:
            raise ConfigError("No liquid at the initial state (tank too large / too warm).")
        self._m_liq = m_liq
        self._m_vap = m_vap
        # Vapour-phase (post-LRO) reference state, set at transition:
        self._lro_reference: tuple[float, float, float] | None = None

    # ------------------------------------------------------------ public
    def state(self) -> TankState:
        if self._m_liq > 0.0:
            pressure = self._props.psat(self._temperature)
            fluid = self._fluid_state(pressure)
        else:
            pressure, fluid = self._vapor_state()
        return TankState(
            time_s=self._time,
            pressure_pa=pressure,
            temperature_k=self._temperature,
            mass_liquid_kg=max(self._m_liq, 0.0),
            mass_vapor_kg=max(self._m_vap, 0.0),
            fluid=fluid,
        )

    def step(self, dt: float, mdot_out: float) -> TankState:
        if dt <= 0.0 or mdot_out < 0.0:
            raise ValueError("Require dt > 0 and mdot_out >= 0.")
        dm = mdot_out * dt
        self._time += dt
        if self._m_liq > 0.0:
            self._step_liquid(dm)
        else:
            self._m_vap = max(self._m_vap - dm, 0.0)
        return self.state()

    # ----------------------------------------------------------- internal
    def _step_liquid(self, dm: float) -> None:
        if dm >= self._m_liq:
            # LRO within this step: freeze reference for the gas phase and
            # draw the remainder of this step's outflow from the vapour, so
            # that tank mass decreases by exactly mdot*dt (mass conservation;
            # previously the remainder - up to one step of flow - vanished).
            _log.info("Liquid run-out at t=%.3f s", self._time)
            remainder = dm - self._m_liq
            self._m_liq = 0.0
            self._lro_reference = (
                self._props.psat(self._temperature),
                self._temperature,
                max(self._m_vap, 1e-12),
            )
            self._m_vap = max(self._m_vap - remainder, 0.0)
            return
        self._m_liq -= dm
        temperature = self._temperature
        m_liq, m_vap = self._m_liq, self._m_vap
        props = self._props
        h_vap = props.h_vap(temperature)
        cp_liq = props.cp_liquid(temperature)

        def volume_residual(dm_v: float) -> float:
            t_new = temperature - h_vap * dm_v / (max(m_liq - dm_v, 1e-9) * cp_liq)
            t_new = max(t_new, 184.0)
            rho_l = props.rho_liquid(t_new)
            rho_v = props.rho_vapor(t_new)
            return (m_liq - dm_v) / rho_l + (m_vap + dm_v) / rho_v - self._volume

        upper = 0.5 * m_liq
        try:
            dm_v = brentq(volume_residual, 0.0, upper, xtol=1e-9)
        except ValueError as exc:
            raise ConvergenceError(
                "Equilibrium vaporised-mass solve failed (tank state "
                f"T={temperature:.1f} K, m_liq={m_liq:.3f} kg)."
            ) from exc
        self._m_liq = m_liq - dm_v
        self._m_vap = m_vap + dm_v
        self._temperature = temperature - h_vap * dm_v / (max(self._m_liq, 1e-9) * cp_liq)
        if self._m_liq <= 0.0:
            self._lro_reference = (
                self._props.psat(self._temperature),
                self._temperature,
                max(self._m_vap, 1e-12),
            )

    def _fluid_state(self, pressure: float) -> FluidState:
        extras = {}
        if hasattr(self._props, "h_liquid"):  # CoolProp backend
            extras = dict(
                enthalpy_j_kg=self._props.h_liquid(self._temperature),
                entropy_j_kg_k=self._props.s_liquid(self._temperature),
            )
        return FluidState(
            pressure_pa=pressure,
            temperature_k=self._temperature,
            density_kg_m3=self._props.rho_liquid(self._temperature),
            vapor_pressure_pa=pressure,  # saturated: p = p_v
            phase="liquid",
            **extras,
        )

    def _vapor_state(self):
        if self._lro_reference is None:  # started without liquid
            self._lro_reference = (
                self._props.psat(self._temperature),
                self._temperature,
                max(self._m_vap, 1e-12),
            )
        p_ref, t_ref, m_ref = self._lro_reference
        fraction = max(self._m_vap, 0.0) / m_ref
        k = self._poly_k
        pressure = p_ref * fraction**k
        self._temperature = t_ref * fraction ** (k - 1.0)
        density = max(self._m_vap, 0.0) / self._volume
        fluid = FluidState(
            pressure_pa=pressure,
            temperature_k=self._temperature,
            density_kg_m3=density,
            vapor_pressure_pa=pressure,
            phase="vapor",
        )
        return pressure, fluid
