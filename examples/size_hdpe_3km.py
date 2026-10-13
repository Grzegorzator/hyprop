"""Inverse sizing demo (E8): HDPE/N2O, F=0.5 kN, It=4000 Ns, apogee 3 km.

Launch at 0 m ASL; nozzle adapted at the h=apogee/3 heuristic (1000 m)
until the trajectory module provides the impulse-weighted altitude.
"""
import sys; sys.path.insert(0, '.')
import hyprop.simulation.solver as sm
sm._TABLE_OF, sm._TABLE_PC = 6, 5      # coarser CEA table: sizing speed knob
import hyprop.api as api
from hyprop.sizing.preliminary import SizingOptions

# Cantera pinned for reproducibility across machines (RocketCEA needs a
# Fortran compiler; the two agree to 0.15 %, docs/VALIDATION.md).
sized = api.size(thrust_n=500.0, total_impulse_ns=4000.0, apogee_m=3000.0,
                 fuel="hdpe", oxidizer="n2o",
                 options=SizingOptions(cea_backend="cantera"))
cfg, nz, ach = sized.config, sized.nozzle, sized.achieved
print(f"Converged in {sized.iterations} iterations; warnings: {sized.warnings or 'none'}")
print(f"Achieved: F_iw={ach['thrust_iw_n']:.0f} N, It={ach['total_impulse_ns']:.0f} Ns, "
      f"Pc_iw={ach['pc_iw_pa']/1e5:.1f} bar, O/F_iw={ach['of_iw']:.2f}, "
      f"Isp_iw={ach['isp_iw_s']:.0f} s, LRO={ach['lro_s']:.2f} s")
print(f"Grain : port {cfg.grain.port['initial_diameter_m']*1e3:.1f} -> OD "
      f"{cfg.grain.outer_diameter_m*1e3:.1f} mm x {cfg.grain.length_m*1e3:.0f} mm")
print(f"Tank  : {cfg.tank.volume_m3*1e3:.2f} L, {cfg.tank.oxidizer_mass_kg:.2f} kg N2O")
print(f"Inj   : {cfg.injector.orifice_count} x {cfg.injector.orifice_diameter_m*1e3:.2f} mm, Cd {cfg.injector.discharge_coefficient}")
print(f"Nozzle: Dt={nz.throat_diameter_m*1e3:.1f} mm, eps={nz.expansion_ratio:.2f}, "
      f"De={nz.exit_diameter_m*1e3:.1f} mm, adapted @ {nz.design_altitude_m:.0f} m "
      f"(pe={nz.exit_pressure_pa/1e3:.1f} kPa), Cf_design={nz.cf_design:.3f}, "
      f"Cf_SL={nz.cf_sea_level:.3f}, separation_risk={nz.separation_risk}")
api.save_config(cfg, "examples/hdpe_05kN_3km_sized.yaml")
print("Saved examples/hdpe_05kN_3km_sized.yaml")
