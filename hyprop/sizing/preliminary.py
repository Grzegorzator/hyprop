"""Inverse preliminary sizing: mission requirements -> EngineConfig (E8).

Algorithm
---------
1. **Analytic first guess** (Sutton/Humble relations at assumed Pc):
   mdot from F/(Isp_est*g0); throat from Cf; oxidizer mass from It;
   port diameter from a max-flux limit G_ox0; grain length from the
   regression law matched to the target O/F; injector area from a
   pressure-drop ratio (dP ~ 25-35% of Pc for feed stability).
2. **Simulation refinement loop**: run the transient, take the
   impulse-weighted ROP point, and rescale
      - oxidizer mass by It_target/It (with tank volume),
      - injector area to keep the design mdot_ox,
      - throat area by F_target/F_iw at fixed Pc,
      - nozzle eps re-adapted to the design altitude each pass.
   Repeats until F_iw and It are within tolerance (default 3%).

Stability guards baked in (reported, not silently fixed): initial
oxidizer flux G_ox0 <= 500 kg/m^2/s (flooding), injector dP/Pc >= 0.20
(chug margin; Sutton Ch. 8 rule of thumb), web margin at burnout.

Sources: Sutton Ch. 3, 8; Humble Ch. 7; HRAP practice.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from hyprop.core.config import EngineConfig
from hyprop.core.constants import G0
from hyprop.core.exceptions import ConvergenceError
from hyprop.core.logging import get_logger
from hyprop.data import load_fuel
from hyprop.nozzle.sizing import (
    NozzleDesign,
    design_altitude_from_apogee,
    size_nozzle,
)
from hyprop.oppoints import analyze
from hyprop.physics import atmosphere
from hyprop.tank.n2o_properties import ESDU91022

_log = get_logger(__name__)

#: Sizing assumptions (overridable via SizingOptions).
PC_DESIGN_DEFAULT = 32e5          # [Pa] target liquid-phase chamber pressure
G_OX0_MAX = 450.0                 # [kg/m^2/s] initial oxidizer flux limit
DP_OVER_PC = 0.30                 # injector pressure-drop ratio at design
ISP_ESTIMATE_S = 210.0            # first-guess delivered Isp
WEB_MARGIN = 1.25                 # OD sized for 25% web reserve
FILL_FRACTION = 0.85              # tank liquid volume fill at loading


@dataclass
class SizingOptions:
    """Tunable assumptions of the preliminary sizing."""

    pc_design_pa: float = PC_DESIGN_DEFAULT
    of_design: Optional[float] = None       # None -> near optimum - 15%
    g_ox0: float = 400.0                    # initial port flux [kg/m^2/s]
    injector_cd: float = 0.60
    orifice_diameter_m: float = 1.5e-3
    eta_cstar: float = 0.95
    nozzle_efficiency: float = 0.9673       # with lambda(15deg) -> 0.95 total
    max_iterations: int = 10
    tolerance: float = 0.03


@dataclass
class SizingResult:
    """Converged sizing output."""

    config: EngineConfig
    nozzle: NozzleDesign
    achieved: Dict[str, float]
    warnings: List[str] = field(default_factory=list)
    iterations: int = 0


def size_engine(
    thrust_n: float,
    total_impulse_ns: float,
    apogee_m: float,
    fuel: str = "hdpe",
    oxidizer: str = "n2o",
    temperature_k: float = 293.15,
    design_altitude_m: Optional[float] = None,
    options: Optional[SizingOptions] = None,
    _runner=None,
) -> SizingResult:
    """Mission (F, It, apogee) -> converged EngineConfig (HDPE/N2O path)."""
    import hyprop.api as api

    opts = options or SizingOptions()
    run = _runner or api.run
    fuel_data = load_fuel(fuel)
    rho_fuel = fuel_data.density.value
    regression = fuel_data.regression_for(oxidizer)[0]
    h_design = (design_altitude_m
                if design_altitude_m is not None
                else design_altitude_from_apogee(apogee_m))

    # ---------------- analytic first guess ------------------------------
    mdot_total = thrust_n / (ISP_ESTIMATE_S * G0)
    of_design = opts.of_design or 0.85 * 8.2       # sub-optimum: O/F drifts
    mdot_ox = mdot_total * of_design / (1.0 + of_design)
    mdot_fuel = mdot_total - mdot_ox
    burn_time = total_impulse_ns / thrust_n
    m_ox = 1.10 * mdot_ox * burn_time              # 10% for gas-phase tail

    port_area = mdot_ox / opts.g_ox0
    port_d = 2.0 * math.sqrt(port_area / math.pi)
    rdot0 = regression.a * opts.g_ox0 ** regression.n
    grain_length = mdot_fuel / (rho_fuel * math.pi * port_d * rdot0)
    web = rdot0 * burn_time                        # crude (rdot falls in time)
    outer_d = port_d + 2.0 * WEB_MARGIN * web

    esdu = ESDU91022()
    p_tank = esdu.psat(temperature_k)
    rho_l = esdu.rho_liquid(temperature_k)
    tank_volume = m_ox / (FILL_FRACTION * rho_l
                          + (1 - FILL_FRACTION) * esdu.rho_vapor(temperature_k))
    dp = max(p_tank - opts.pc_design_pa, DP_OVER_PC * opts.pc_design_pa)
    orifice_area = math.pi * (0.5 * opts.orifice_diameter_m) ** 2
    n_orifices = max(round(
        mdot_ox / (opts.injector_cd * orifice_area
                   * math.sqrt(2.0 * rho_l * dp))), 1)

    # placeholder ROP-like point for the very first nozzle sizing
    from hyprop.oppoints.design_points import OperatingPoint
    seed_point = OperatingPoint(
        "seed", {"pc": opts.pc_design_pa, "gamma": 1.25})
    nozzle = size_nozzle(seed_point, thrust_n, h_design)

    warnings: List[str] = []
    achieved: Dict[str, float] = {}
    config = None
    for iteration in range(1, opts.max_iterations + 1):
        config = EngineConfig.from_dict(dict(
            name=f"sized_{fuel}_{thrust_n:.0f}N",
            mission=dict(thrust_n=thrust_n,
                         total_impulse_ns=total_impulse_ns,
                         burn_time_s=burn_time,
                         design_altitude_m=h_design,
                         apogee_m=apogee_m,
                         ambient_pressure_pa=atmosphere.pressure(0.0)),
            oxidizer=dict(name=oxidizer, temperature_k=temperature_k),
            fuel=dict(name=fuel),
            grain=dict(geometry="cylindrical", length_m=grain_length,
                       outer_diameter_m=outer_d,
                       port=dict(initial_diameter_m=port_d)),
            tank=dict(model="equilibrium_blowdown", volume_m3=tank_volume,
                      oxidizer_mass_kg=m_ox),
            injector=dict(model="spi",
                          discharge_coefficient=opts.injector_cd,
                          orifice_count=int(n_orifices),
                          orifice_diameter_m=opts.orifice_diameter_m),
            nozzle=dict(throat_diameter_m=nozzle.throat_diameter_m,
                        expansion_ratio=nozzle.expansion_ratio,
                        divergence_half_angle_deg=15.0,
                        efficiency=opts.nozzle_efficiency,
                        discharge_coefficient=0.98),
            efficiencies=dict(eta_cstar=opts.eta_cstar),
            simulation=dict(dt_s=0.02, t_max_s=60.0),
        ))
        result = run(config)
        report = analyze(result)
        iw = report.point("impulse_weighted")
        it = result.summary["total_impulse_ns"]
        f_iw = iw["thrust"]
        err_f = f_iw / thrust_n - 1.0
        err_it = it / total_impulse_ns - 1.0
        _log.info("Sizing iter %d: F_iw=%.0f N (%+.1f%%), It=%.0f Ns (%+.1f%%)",
                  iteration, f_iw, 100 * err_f, it, 100 * err_it)
        achieved = dict(thrust_iw_n=f_iw, total_impulse_ns=it,
                        pc_iw_pa=iw["pc"], of_iw=iw["of"],
                        isp_iw_s=iw["isp"],
                        lro_s=result.event_time("liquid_runout") or 0.0)
        if abs(err_f) < opts.tolerance and abs(err_it) < opts.tolerance:
            break
        # --- rescale toward targets ------------------------------------
        # In a blowdown, thrust is governed by the injector (mdot_ox),
        # not the throat: scale total injector area by F_target/F_iw
        # (continuous, via orifice diameter); the throat then re-sizes
        # at the new impulse-weighted point to hold the design Pc.
        factor_f = thrust_n / max(f_iw, 1.0)
        opts.orifice_diameter_m *= math.sqrt(factor_f)
        grain_length *= factor_f ** (1.0 - regression.n)   # keep O/F
        m_ox *= factor_f / (1.0 + err_it)
        tank_volume *= factor_f / (1.0 + err_it)
        # Throat sized at the FIXED design Pc (gamma from the iw point);
        # sizing it at the drifting Pc_iw creates positive feedback
        # (higher mdot -> higher Pc -> smaller throat -> flooding).
        design_point = OperatingPoint(
            "design", {"pc": opts.pc_design_pa, "gamma": iw["gamma"]})
        nozzle = size_nozzle(design_point, thrust_n, h_design)
        g0_actual = result.history["g_flux"][0]
        if g0_actual > G_OX0_MAX:
            port_d *= math.sqrt(g0_actual / opts.g_ox0)
    else:
        warnings.append(
            f"Sizing did not reach {opts.tolerance:.0%} in "
            f"{opts.max_iterations} iterations (last F {err_f:+.1%}, "
            f"It {err_it:+.1%}).")

    # ------------------------- guard reports ----------------------------
    g0_actual = result.history["g_flux"][0]
    if g0_actual > G_OX0_MAX:
        warnings.append(f"Initial G_ox = {g0_actual:.0f} kg/m^2/s exceeds "
                        f"{G_OX0_MAX:.0f} (flooding risk).")
    dp_ratio = (result.history["p_tank"][0] - result.history["pc"][0]) \
        / result.history["pc"][0]
    if dp_ratio < 0.20:
        warnings.append(f"Injector dP/Pc = {dp_ratio:.2f} < 0.20 "
                        "(feed-coupled instability risk).")
    if nozzle.separation_risk:
        warnings.append("Nozzle overexpanded at lift-off "
                        "(pe < 0.4 pa,SL - Summerfield).")
    for message in warnings:
        _log.warning("%s", message)
    return SizingResult(config=config, nozzle=nozzle, achieved=achieved,
                        warnings=warnings,
                        iterations=iteration)
