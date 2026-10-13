"""ROP analysis of the 0.5 kN PE/N2O engine (E7 demo)."""

import os

import matplotlib.pyplot as plt

import hyprop.api as api
from hyprop.oppoints import analyze

result = api.run(api.load_config("examples/pe_05kN.yaml"))
report = analyze(result)

iw, ta = report.point("impulse_weighted").values, report.time_average
print("=== Impulse-weighted vs time average ===")
for ch, unit, sc in (
    ("thrust", "N", 1),
    ("pc", "bar", 1e5),
    ("of", "-", 1),
    ("isp", "s", 1),
    ("cstar", "m/s", 1),
    ("t_c", "K", 1),
):
    print(
        f"{ch:>7}: IW={iw[ch] / sc:8.1f} {unit:4} | time-avg={ta[ch] / sc:8.1f}"
        f"  ({100 * (ta[ch] / iw[ch] - 1):+.1f}%)"
    )
print("\n=== Phases ===")
print(
    report.phases_table()[
        ["phase", "t_start_s", "t_end_s", "impulse_share", "time_share", "mean_thrust", "mean_pc"]
    ].to_string(index=False)
)
print("\n=== Time share to deliver impulse ===")
for frac, share in report.time_shares.items():
    print(f"  {frac:>4.0%} of It in {share:6.1%} of burn time")
pk = report.point("peak_performance")
print(
    f"\nPeak: Pc={pk['pc_max'] / 1e5:.1f} bar @ {pk['pc_max_time_s']:.2f}s, "
    f"F={pk['thrust_max']:.0f} N, Tc={pk['t_c_max']:.0f} K"
)
print(
    f"Recommended: nozzle -> {report.for_module('nozzle_design').name}, "
    f"thermal -> {report.for_module('thermal_analysis').name}, "
    f"structural -> {report.for_module('structural_analysis').name}"
)

# plot: thrust + cumulative impulse with ROP markers

os.makedirs("outputs", exist_ok=True)

plt.switch_backend("Agg")

h = result.history
df = h.to_dataframe()
fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
ax[0].plot(df.t, df.thrust, "b-", label="F(t)")
ax[0].axhline(iw["thrust"], c="g", ls="-", label=f"IW {iw['thrust']:.0f} N")
ax[0].axhline(ta["thrust"], c="orange", ls=":", label=f"time-avg {ta['thrust']:.0f} N")
for p in report.percentiles:
    ax[0].axvline(p.time_s, c="gray", ls="--", alpha=0.3)
mi = report.point("median_impulse")
ax[0].axvline(mi.time_s, c="r", ls="--", label=f"median It @ {mi.time_s:.1f}s")
ax[0].set_title("Thrust + ROP")
ax[0].legend(fontsize=8)
ax[0].grid(alpha=0.3)
ax[1].plot(df.t, df.impulse, "b-")
for frac in (0.5, 0.9, 0.99):
    from hyprop.oppoints import time_at_impulse_fraction

    tf = time_at_impulse_fraction(h, frac)
    ax[1].plot(tf, frac * df.impulse.iloc[-1], "ro", ms=5)
    ax[1].annotate(
        f"{frac:.0%}",
        (tf, frac * df.impulse.iloc[-1]),
        textcoords="offset points",
        xytext=(6, -4),
        fontsize=8,
    )
ax[1].set_title("Cumulative impulse [Ns]")
ax[1].grid(alpha=0.3)
for a in ax:
    a.set_xlabel("t [s]")
fig.tight_layout()
fig.savefig("outputs/rop_pe_05kN.png", dpi=110)
print("Saved outputs/rop_pe_05kN.png")
