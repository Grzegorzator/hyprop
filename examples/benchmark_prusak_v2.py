"""E6 benchmark: HyProp transient vs HRAP output (prusak_v2, HDPE/N2O).

Inputs replicated 1:1 from HRAP motor config prusak_v2.mat:
tank 100 cm x 75 mm (V = 4.418 L) @ 293.15 K; injector 5 x 2.0 mm,
Cd = 0.60; throat 16 mm, eps 5.3, nozzle eff 95%; eta_c* = 95%.
Grain reconstructed from the CSV itself (the shipped .mat is a NEWER
config): ID0 = 40 mm, OD = 62.5 mm, rho*L = 609 -> L = 0.662 m at
rho = 920 kg/m^3; matches m_fuel(0) = 1.1034 kg and mdot_f(t) exactly.
CSV-implied a = 1.040e-4 SI confirms our HRAP unit conversion.
"""
import math, sys
sys.path.insert(0, '.')
import numpy as np, pandas as pd
#: NumPy 2.x renamed trapz -> trapezoid; support both.
_trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))

import hyprop.api as api
from hyprop.core.config import EngineConfig

V_TANK = math.pi * (0.075/2)**2 * 1.00           # 4.418e-3 m^3
CFG = dict(
    name="prusak_v2_benchmark",
    mission=dict(thrust_n=1000.0, burn_time_s=30.0,
                 ambient_pressure_pa=101325.0),
    oxidizer=dict(name="n2o", temperature_k=293.15),
    fuel=dict(name="hdpe", density_kg_m3=920.0),
    grain=dict(geometry="cylindrical", length_m=0.662,
               outer_diameter_m=0.0625,
               port=dict(initial_diameter_m=0.040)),
    tank=dict(model="equilibrium_blowdown", volume_m3=V_TANK,
              oxidizer_mass_kg=3.0584),
    injector=dict(model="spi", discharge_coefficient=0.60,
                  orifice_count=5, orifice_diameter_m=2.0e-3),
    nozzle=dict(throat_diameter_m=16e-3, expansion_ratio=5.3,
                divergence_half_angle_deg=15.0, efficiency=0.9673,
                discharge_coefficient=0.98),
    #   ^ HRAP noz_eff=0.95 is total; our lambda(15deg)=0.983 * 0.9673 = 0.95
    efficiencies=dict(eta_cstar=0.95),
    simulation=dict(dt_s=0.01, t_max_s=30.0, pc_solver="fixed_point",
                    cea_backend="cantera"),
)

def main():
    config = EngineConfig.from_dict(CFG)
    result = api.run(config)
    df = result.history.to_dataframe()
    import os
    hrap_dir = os.environ.get("HYPROP_HRAP_DIR")
    if not hrap_dir:
        sys.exit("Set HYPROP_HRAP_DIR to the HRAP 'application' folder "
                 "(contains output/prusakv2_HRAP_output.csv).")
    ref = pd.read_csv(os.path.join(hrap_dir, "output",
                                   "prusakv2_HRAP_output.csv"))
    ref.columns = [c.strip() for c in ref.columns]

    # --- compare on common time base (liquid phase + tail) --------------
    lro = result.event_time("liquid_runout") or df.t.iloc[-1]
    t_grid = np.arange(0.2, min(lro, 7.0), 0.05)   # liquid phase, skip ramp
    def interp(x, y): return np.interp(t_grid, x, y)
    F_h  = interp(df.t, df.thrust)
    F_r  = interp(ref["Time (s)"], ref["Thrust (N)"])
    Pc_h = interp(df.t, df.pc) / 1e3
    Pc_r = interp(ref["Time (s)"], ref["Combustion Chamber Pressure (kPa)"])
    Pt_h = interp(df.t, df.p_tank) / 1e3
    Pt_r = interp(ref["Time (s)"], ref["Oxidizer Tank Pressure (kPa)"])
    OF_h = interp(df.t, df.of)
    OF_r = interp(ref["Time (s)"], ref["Oxidizer to Fuel Ratio"])

    def dev(a, b): return float(np.mean(np.abs(a-b)) / np.mean(np.abs(b)))
    lro_h = lro
    it_r = float(_trapz(ref["Thrust (N)"], ref["Time (s)"]))
    mask_r = ref["Time (s)"] <= 7.0
    mask_h = df.t <= lro
    it_r_liq = float(_trapz(ref.loc[mask_r, "Thrust (N)"], ref.loc[mask_r, "Time (s)"]))
    it_h_liq = float(_trapz(df.loc[mask_h, "thrust"], df.loc[mask_h, "t"]))
    print(f"Liquid-phase impulse: HyProp {it_h_liq:.0f} vs HRAP {it_r_liq:.0f} Ns "
          f"({100*(it_h_liq/it_r_liq-1):+.1f}%)")

    print(f"HyProp: It={result.summary['total_impulse_ns']:.0f} Ns, "
          f"Fpeak={result.summary['peak_thrust_n']:.0f} N, "
          f"Pc_peak={result.summary['peak_pc_pa']/1e5:.1f} bar, "
          f"LRO={lro_h}, t_end={result.summary['burn_time_s']:.2f} s, "
          f"events={result.events}")
    print(f"HRAP : It={it_r:.0f} Ns, Fpeak={ref['Thrust (N)'].max():.0f} N, "
          f"Pc_peak={ref['Combustion Chamber Pressure (kPa)'].max()/1e2:.1f} bar, "
          f"t_end={ref['Time (s)'].iloc[-1]:.2f} s")
    print(f"Mean rel. dev.: F={100*dev(F_h,F_r):.1f}%  Pc={100*dev(Pc_h,Pc_r):.1f}%  "
          f"P_tank={100*dev(Pt_h,Pt_r):.1f}%  OF={100*dev(OF_h,OF_r):.1f}%")

    # --- plots ----------------------------------------------------------
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    ax[0,0].plot(ref["Time (s)"], ref["Thrust (N)"], 'k-', lw=1, label="HRAP")
    ax[0,0].plot(df.t, df.thrust, 'r--', lw=1.5, label="HyProp")
    ax[0,0].set_title("Thrust [N]"); ax[0,0].legend()
    ax[0,1].plot(ref["Time (s)"], ref["Combustion Chamber Pressure (kPa)"], 'k-', lw=1)
    ax[0,1].plot(df.t, df.pc/1e3, 'r--', lw=1.5)
    ax[0,1].plot(ref["Time (s)"], ref["Oxidizer Tank Pressure (kPa)"], 'k:', lw=1)
    ax[0,1].plot(df.t, df.p_tank/1e3, 'b--', lw=1)
    ax[0,1].set_title("Pc & P_tank [kPa]")
    ax[1,0].plot(ref["Time (s)"], ref["Oxidizer to Fuel Ratio"], 'k-', lw=1)
    ax[1,0].plot(df.t, df.of, 'r--', lw=1.5); ax[1,0].set_ylim(0, 16)
    ax[1,0].set_title("O/F [-]"); ax[1,0].set_xlabel("t [s]")
    ax[1,1].plot(ref["Time (s)"], ref["Oxidizer Mass (kg)"], 'k-', lw=1)
    ax[1,1].plot(df.t, df.m_ox, 'r--', lw=1.5)
    ax[1,1].plot(ref["Time (s)"], ref["Fuel Mass (kg)"], 'k:', lw=1)
    ax[1,1].plot(df.t, df.m_fuel, 'b--', lw=1)
    ax[1,1].set_title("Masses [kg]"); ax[1,1].set_xlabel("t [s]")
    for a in ax.flat: a.grid(alpha=0.3)
    fig.suptitle("HyProp vs HRAP - prusak_v2 (HDPE/N2O)")
    fig.tight_layout()
    os.makedirs("outputs", exist_ok=True)
    fig.savefig("outputs/benchmark_prusak_v2.png", dpi=110)
    print("Saved outputs/benchmark_prusak_v2.png")

if __name__ == "__main__":
    main()
