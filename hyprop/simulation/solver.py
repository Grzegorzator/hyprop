"""Transient hybrid-motor solver (stage E6) - the HRAP loop.

Each time step couples five models (ARCHITECTURE.md par. 4):

1. **Tank** supplies the injector-upstream fluid state.
2. **Injector** gives mdot_ox(P_tank, Pc).
3. **Chamber pressure** closes the mass balance through the choked
   throat (decision D5, both options implemented):

       Pc = (mdot_ox + mdot_fuel) * c*_delivered / (Cd_noz * At)

   where mdot_fuel follows from regression at the current Pc via
   G -> rdot -> mdot_fuel. Solved by damped fixed-point iteration
   (HRAP; user's 06_hybrid_solver, default) or Brent on the residual.
4. **Thrust** from the tabulated CEA expansion at the current O/F:

       F = eta_noz * mdot * ve + (pe - pa) * Ae

5. **Geometry update**: w += rdot * dt; tank steps by mdot_ox * dt.

Events: liquid run-out (LRO), fuel web burnout, oxidizer depletion,
chamber pressure decayed to ambient. Gas (vapour) phase continues after
LRO until a stop event - required by the ROP phase analysis (E7).

Sources: HRAP Theory & Application; user's 06_hybrid_solver.py;
Sutton Ch. 2-3; Humble Ch. 7.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from scipy.optimize import brentq

from hyprop.cea.backend import ThermochemistryBackend
from hyprop.cea.cantera_backend import CanteraBackend
from hyprop.cea.table import TabulatedBackend
from hyprop.core.config import EngineConfig
from hyprop.core.constants import G0, P_ATM_SL
from hyprop.core.exceptions import ConfigError, ConvergenceError
from hyprop.core.logging import get_logger
from hyprop.core.registry import autodiscover, get_model
from hyprop.core.state import TimeHistory
from hyprop.data import load_fuel
from hyprop.geometry.base import GrainGeometry
from hyprop.injector.base import InjectorModel
from hyprop.regression.power_law import PowerLawRegression
from hyprop.tank.base import TankModel
from hyprop.tank.simple_models import ConstantMdotTank

_log = get_logger(__name__)

#: Default CEA table resolution (O/F x Pc).
_TABLE_OF = 10
_TABLE_PC = 7
_MIN_PC_FACTOR = 1.10        # stop when Pc < factor * Pa


@dataclass
class SimulationResult:
    """Full transient output + events + derived summary."""

    history: TimeHistory
    events: List[Tuple[float, str]] = field(default_factory=list)
    summary: Dict[str, float] = field(default_factory=dict)

    def event_time(self, name: str) -> Optional[float]:
        for time_s, event in self.events:
            if event == name:
                return time_s
        return None


def _build_components(config: EngineConfig):
    """Instantiate tank, injector, geometry, regression from config."""
    autodiscover()
    fuel = load_fuel(config.fuel.name)
    fuel_density = config.fuel.density_kg_m3 or fuel.density.value

    geometry_cls = get_model("geometry", config.grain.geometry)
    geometry: GrainGeometry = geometry_cls.from_spec(
        config.grain.length_m, config.grain.outer_diameter_m,
        config.grain.port,
    )

    if config.fuel.regression is not None:
        regression = PowerLawRegression.from_spec(config.fuel.regression)
    else:
        entries = fuel.regression_for(config.oxidizer.name)
        if not entries:
            raise ConfigError(
                f"No regression data for {config.fuel.name}/"
                f"{config.oxidizer.name}; provide fuel.regression override."
            )
        regression = PowerLawRegression.from_entry(entries[0])

    tank_cls = get_model("tank", config.tank.model)
    tank_kwargs = dict(config.tank.parameters)
    if config.tank.model == "equilibrium_blowdown":
        if config.tank.volume_m3 is None or config.tank.oxidizer_mass_kg is None:
            raise ConfigError(
                "equilibrium_blowdown requires tank.volume_m3 and "
                "tank.oxidizer_mass_kg."
            )
        tank_kwargs.setdefault("volume_m3", config.tank.volume_m3)
        tank_kwargs.setdefault(
            "oxidizer_mass_kg", config.tank.oxidizer_mass_kg
        )
        tank_kwargs.setdefault(
            "temperature_k", config.oxidizer.temperature_k
        )
    tank: TankModel = tank_cls(**tank_kwargs)

    if config.injector.orifice_diameter_m is None:
        raise ConfigError("injector.orifice_diameter_m is required.")
    orifice_area = math.pi * (0.5 * config.injector.orifice_diameter_m) ** 2
    injector_cls = get_model("injector", config.injector.model)
    injector: InjectorModel = injector_cls(
        discharge_coefficient=config.injector.discharge_coefficient,
        orifice_count=config.injector.orifice_count,
        orifice_area_m2=orifice_area,
    )
    return fuel, fuel_density, geometry, regression, tank, injector


#: Process-wide table cache: (fuel, oxidizer, round(eps,2)) -> table.
#: Batch/sensitivity runs mutate injector/tank/grain parameters far more
#: often than propellants or eps; rebuilding the ~20 s Cantera sweep for
#: every case would dominate runtime.
_TABLE_CACHE: Dict[Tuple[str, str, float, int, int], TabulatedBackend] = {}


def _build_cea_table(config: EngineConfig, eps: float) -> TabulatedBackend:
    """Sweep the Cantera backend over an (O/F, Pc) grid (HRAP pattern)."""
    import numpy as np

    key = (config.fuel.name, config.oxidizer.name, round(eps, 2),
           _TABLE_OF, _TABLE_PC)
    cached = _TABLE_CACHE.get(key)
    if cached is not None:
        return cached

    backend: ThermochemistryBackend = CanteraBackend(
        fuel=config.fuel.name, oxidizer=config.oxidizer.name
    )
    # O/F below ~2 (very fuel-rich C/H) destabilises gri30 equilibrium
    # (missing condensed carbon); the transient never goes there anyway.
    of_grid = np.linspace(2.0, 14.0, _TABLE_OF)
    pc_grid = np.linspace(1.5e5, 60e5, _TABLE_PC)
    table = TabulatedBackend(backend, of_grid, pc_grid, eps)
    _TABLE_CACHE[key] = table
    return table


def run_simulation(config: EngineConfig) -> SimulationResult:
    """Run the full transient for one :class:`EngineConfig`."""
    (fuel, fuel_density, geometry, regression,
     tank, injector) = _build_components(config)

    if config.nozzle.throat_diameter_m is None:
        raise ConfigError("nozzle.throat_diameter_m is required for E6 runs.")
    if config.nozzle.expansion_ratio is None:
        raise ConfigError("nozzle.expansion_ratio is required for E6 runs.")
    throat_area = math.pi * (0.5 * config.nozzle.throat_diameter_m) ** 2
    eps = config.nozzle.expansion_ratio
    exit_area = throat_area * eps
    ambient = config.mission.ambient_pressure_pa or P_ATM_SL
    eta_cstar = config.efficiencies.eta_cstar
    from hyprop.nozzle.losses import nozzle_efficiency

    eta_noz = nozzle_efficiency(
        config.nozzle.divergence_half_angle_deg, config.nozzle.efficiency
    )
    cd_nozzle = config.nozzle.discharge_coefficient   # HRAP noz_Cd

    cea = _build_cea_table(config, eps)
    settings = config.simulation
    dt = settings.dt_s
    grain_length = config.grain.length_m

    history = TimeHistory()
    events: List[Tuple[float, str]] = []
    time_s = 0.0
    web = 0.0
    pc = 2.0 * ambient                       # ignition seed
    impulse = 0.0
    lro_logged = False

    def pc_from_mdot(mdot_total: float, of: float) -> float:
        cstar = cea.query(of, max(pc, 1.2e5), eps).cstar_m_s * eta_cstar
        return mdot_total * cstar / (cd_nozzle * throat_area)

    def chamber_balance(pc_try: float, fluid) -> Tuple[float, dict]:
        """Return (Pc implied by mass balance, flow dict) at pc_try."""
        mdot_ox = injector.mdot(fluid, pc_try)
        port_area = geometry.port_area(web)
        if port_area <= 0.0 or mdot_ox <= 0.0:
            return 0.0, dict(mdot_ox=mdot_ox, mdot_fuel=0.0, of=float("inf"),
                             g_flux=0.0, rdot=0.0)
        g_flux = mdot_ox / port_area
        if regression.flux_basis == "total":
            # inner fixed point on fuel flow (converges in 2-3 passes)
            mdot_fuel = 0.0
            for _ in range(5):
                g_flux = (mdot_ox + mdot_fuel) / port_area
                rdot = regression.rdot(g_flux, grain_length)
                mdot_fuel = fuel_density * geometry.burn_area(web) * rdot
        else:
            rdot = regression.rdot(g_flux, grain_length)
            mdot_fuel = fuel_density * geometry.burn_area(web) * rdot
        of = mdot_ox / mdot_fuel if mdot_fuel > 0 else float("inf")
        of_c = min(max(of, cea.of_range[0]), cea.of_range[1])
        pc_c = min(max(pc_try, cea.pc_range[0]), cea.pc_range[1])
        cstar = cea.query(of_c, pc_c, eps).cstar_m_s * eta_cstar
        pc_balance = (mdot_ox + mdot_fuel) * cstar / (cd_nozzle * throat_area)
        return pc_balance, dict(mdot_ox=mdot_ox, mdot_fuel=mdot_fuel, of=of,
                                g_flux=g_flux, rdot=rdot)

    def solve_pc(fluid, pc_seed: float) -> Tuple[float, dict]:
        if isinstance(tank, ConstantMdotTank):
            # prescribed mdot: Pc follows directly (no injector coupling)
            flow_mdot = tank.mdot_kg_s
            pc_direct = pc_seed
            for _ in range(10):
                _, flow = chamber_balance(pc_direct, fluid)
                flow["mdot_ox"] = flow_mdot
                pc_new = pc_from_mdot(flow_mdot + flow["mdot_fuel"],
                                      min(max(flow["of"], 1.0), 14.0))
                if abs(pc_new - pc_direct) < settings.pc_tolerance * pc_direct:
                    return pc_new, flow
                pc_direct = pc_new
            return pc_direct, flow
        if settings.pc_solver == "brent":
            upper = fluid.pressure_pa * 0.995
            lower = ambient
            try:
                pc_solution = brentq(
                    lambda p: chamber_balance(p, fluid)[0] - p,
                    lower, upper, xtol=settings.pc_tolerance * upper,
                )
            except ValueError:
                pc_solution = lower       # no burn possible (dP ~ 0)
            return pc_solution, chamber_balance(pc_solution, fluid)[1]
        # damped fixed point (HRAP / user's 06, relax=0.5)
        pc_iter = min(pc_seed, fluid.pressure_pa * 0.7)
        flow: dict = {}
        for _ in range(settings.max_iterations):
            pc_new, flow = chamber_balance(pc_iter, fluid)
            if abs(pc_new - pc_iter) < settings.pc_tolerance * max(pc_iter, 1e4):
                return pc_new, flow
            # clamp into the physical band (oscillation guard)
            pc_iter = min(max(0.5 * pc_iter + 0.5 * pc_new, 0.2 * ambient),
                          0.99 * fluid.pressure_pa)
        # Fixed point oscillates (stiff injector/throat coupling near
        # flooding); fall back to Brent - the balance residual always
        # brackets a root in [ambient, ~p_tank] since mdot -> 0 there.
        try:
            pc_root = brentq(
                lambda p: chamber_balance(p, fluid)[0] - p,
                0.5 * ambient, 0.995 * fluid.pressure_pa,
                xtol=settings.pc_tolerance * fluid.pressure_pa)
            return pc_root, chamber_balance(pc_root, fluid)[1]
        except ValueError:
            _log.warning("Pc solve failed at t=%.3f s (no equilibrium)",
                         time_s)
            return pc_iter, flow

    _log.info("Transient start: %s", config.name)
    while time_s < settings.t_max_s:
        tank_state = tank.state()
        if tank_state.empty:
            events.append((time_s, "oxidizer_depleted"))
            break
        if geometry.is_burned_out(web):
            events.append((time_s, "fuel_burnout"))
            break
        pc, flow = solve_pc(tank_state.fluid, pc)
        if pc <= _MIN_PC_FACTOR * ambient:
            events.append((time_s, "pressure_decay"))
            break
        of_c = min(max(flow["of"], cea.of_range[0]), cea.of_range[1])
        cea_point = cea.query(of_c, min(max(pc, cea.pc_range[0]),
                                        cea.pc_range[1]), eps)
        mdot_total = flow["mdot_ox"] + flow["mdot_fuel"]
        exp = cea_point.equilibrium
        thrust_n = (
            eta_noz * mdot_total * exp.exhaust_velocity_m_s
            + (exp.exit_state.pressure_pa - ambient) * exit_area
        )
        thrust_n = max(thrust_n, 0.0)
        impulse += thrust_n * dt
        isp = thrust_n / (mdot_total * G0) if mdot_total > 0 else 0.0

        history.record(
            t=time_s, thrust=thrust_n, pc=pc,
            p_tank=tank_state.pressure_pa, of=flow["of"] if
            math.isfinite(flow["of"]) else 0.0,
            isp=isp, cstar=cea_point.cstar_m_s * eta_cstar,
            gamma=cea_point.chamber.gamma,
            t_c=cea_point.chamber.temperature_k,
            mdot_ox=flow["mdot_ox"], mdot_fuel=flow["mdot_fuel"],
            mdot_total=mdot_total, g_flux=flow["g_flux"],
            rdot=flow["rdot"], web=web,
            d_port=geometry.equivalent_port_diameter(web),
            m_fuel=geometry.fuel_mass(web, fuel_density),
            m_ox=tank_state.mass_total_kg,
            m_ox_liquid=tank_state.mass_liquid_kg,
            t_tank=tank_state.temperature_k,
            impulse=impulse,
        )

        web += flow["rdot"] * dt
        tank.step(dt, flow["mdot_ox"])
        if not lro_logged and tank.state().liquid_depleted:
            events.append((time_s, "liquid_runout"))
            lro_logged = True
        time_s += dt
    else:
        events.append((time_s, "time_budget"))

    result = SimulationResult(history=history, events=events)
    if len(history):
        thrust = history["thrust"]
        mdot = history["mdot_total"]
        result.summary = dict(
            burn_time_s=float(history["t"][-1]),
            total_impulse_ns=float(impulse),
            peak_thrust_n=float(thrust.max()),
            mean_thrust_n=float(thrust.mean()),
            peak_pc_pa=float(history["pc"].max()),
            propellant_used_kg=float(
                (history["m_fuel"][0] - history["m_fuel"][-1])
                + (history["m_ox"][0] - history["m_ox"][-1])
            ),
            isp_mean_s=float(
                impulse / (G0 * max(
                    (history["m_fuel"][0] - history["m_fuel"][-1])
                    + (history["m_ox"][0] - history["m_ox"][-1]), 1e-9))
            ),
        )
    _log.info("Transient done: %s | events: %s", result.summary, events)
    return result
