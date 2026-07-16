"""Preliminary sizing run: HDPE/N2O, 0.5 kN, Itot ~ 4000 Ns (E6 demo)."""
import sys; sys.path.insert(0, '.')
import numpy as np
import hyprop.api as api

result = api.run(api.load_config("examples/hdpe_05kN.yaml"))
h, s = result.history, result.summary
lro = result.event_time("liquid_runout"); liq = h["t"] <= lro
print(f"It={s['total_impulse_ns']:.0f} Ns (liquid {np.trapz(h['thrust'][liq], h['t'][liq]):.0f})")
print(f"F_peak={s['peak_thrust_n']:.0f} N, F_mean_liq={h['thrust'][liq].mean():.0f} N")
print(f"Pc_peak={s['peak_pc_pa']/1e5:.1f} bar, LRO={lro:.2f} s, Isp={s['isp_mean_s']:.0f} s")

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
df = h.to_dataframe()
fig, ax = plt.subplots(2, 3, figsize=(15, 7))
panels = [("thrust", "Thrust [N]", 1), ("pc", "Pc [bar]", 1e5),
          ("of", "O/F [-]", 1), ("d_port", "Port dia [mm]", 1e-3),
          ("m_ox", "Ox mass [kg]", 1), ("impulse", "Cumulative It [Ns]", 1)]
for a, (col, title, scale) in zip(ax.flat, panels):
    a.plot(df.t, df[col] / scale, 'b-')
    a.axvline(lro, ls='--', c='r', alpha=0.6)
    a.set_title(title); a.grid(alpha=0.3); a.set_xlabel("t [s]")
fig.suptitle("HDPE/N2O 0.5 kN preliminary sizing (red: LRO)")
fig.tight_layout(); fig.savefig("examples/sizing_hdpe_05kN.png", dpi=110)
print("Saved examples/sizing_hdpe_05kN.png")
