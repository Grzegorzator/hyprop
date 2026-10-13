"""Golden (reference) cases: compute the numbers that are frozen in tests/golden/*.json.

Stage 2 of the HyProp -> YAADO plan: these results protect the physics
against unnoticed changes during the refactoring stages (Pint removal,
packaging, YAADO adapter). They are *regression* references, not
validation references - validation lives in validation/ and
docs/VALIDATION.md.

Cases (all with the Cantera backend pinned, so they reproduce on machines
without RocketCEA):

* ``pe_05kN``   - examples/pe_05kN.yaml, transient + ROP.
* ``prusak_v2`` - the HRAP benchmark configuration (examples/benchmark_prusak_v2.py).
* ``size_3km``  - api.size(500 N, 4000 Ns, 3 km), LDPE, 6 x 5 CEA table
  (as examples/size_pe_3km.py).

To accept new numbers after an intended physics change run
``python tests/golden/regenerate.py`` and commit the JSON diff together
with the change that caused it.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
GOLDEN_DIR = Path(__file__).resolve().parent
SERIES_DT = 0.25  # sampling of stored time series [s]
SERIES_CHANNELS = (
    "thrust",
    "pc",
    "p_tank",
    "of",
    "mdot_ox",
    "mdot_fuel",
    "m_ox",
    "m_fuel",
    "d_port",
)
SCALARS = (
    "total_impulse_ns",
    "peak_thrust_n",
    "peak_pc_pa",
    "burn_time_s",
    "propellant_used_kg",
    "isp_mean_s",
)
IW_CHANNELS = ("thrust", "pc", "of", "isp", "cstar", "t_c")


def _transient_record(config) -> dict[str, Any]:
    import hyprop.api as api
    from hyprop.oppoints import analyze

    res = api.run(config)
    h = res.history
    iw = analyze(res).point("impulse_weighted")
    t = np.asarray(h["t"])
    grid = np.arange(0.0, float(t[-1]) + 1e-9, SERIES_DT)
    return dict(
        scalars={k: float(res.summary[k]) for k in SCALARS},
        events={name: float(time) for time, name in res.events},
        impulse_weighted={k: float(iw[k]) for k in IW_CHANNELS},
        dt=float(config.simulation.dt_s),
        series={
            "t": grid.tolist(),
            **{ch: np.interp(grid, t, np.asarray(h[ch])).tolist() for ch in SERIES_CHANNELS},
        },
        thermo_backend=res.thermo_backend,
    )


def case_pe_05kn() -> dict[str, Any]:
    import hyprop.api as api

    return _transient_record(api.load_config(str(REPO / "examples" / "pe_05kN.yaml")))


def case_prusak_v2() -> dict[str, Any]:
    from hyprop.core.config import EngineConfig

    spec = importlib.util.spec_from_file_location(
        "bench", REPO / "examples" / "benchmark_prusak_v2.py"
    )
    assert spec is not None and spec.loader is not None
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)
    return _transient_record(EngineConfig.from_dict(bench.CFG))


def case_size_3km() -> dict[str, Any]:
    import hyprop.api as api
    import hyprop.simulation.solver as sm
    from hyprop.sizing.preliminary import SizingOptions

    old = sm._TABLE_OF, sm._TABLE_PC
    sm._TABLE_OF, sm._TABLE_PC = 6, 5
    try:
        sz = api.size(
            thrust_n=500.0,
            total_impulse_ns=4000.0,
            apogee_m=3000.0,
            fuel="ldpe",
            oxidizer="n2o",
            options=SizingOptions(cea_backend="cantera"),
        )
    finally:
        sm._TABLE_OF, sm._TABLE_PC = old
    c, nz = sz.config, sz.nozzle
    return dict(
        iterations=int(sz.iterations),
        warnings=list(sz.warnings),
        achieved={k: float(v) for k, v in sz.achieved.items()},
        design=dict(
            grain_length_m=float(c.grain.length_m),
            grain_outer_diameter_m=float(c.grain.outer_diameter_m),
            port_initial_diameter_m=float(c.grain.port["initial_diameter_m"]),
            tank_volume_m3=float(c.tank.volume_m3),
            oxidizer_mass_kg=float(c.tank.oxidizer_mass_kg),
            orifice_count=float(c.injector.orifice_count),
            orifice_diameter_m=float(c.injector.orifice_diameter_m),
            throat_diameter_m=float(nz.throat_diameter_m),
            expansion_ratio=float(nz.expansion_ratio),
            cf_design=float(nz.cf_design),
            cf_sea_level=float(nz.cf_sea_level),
        ),
    )


CASES = {"pe_05kN": case_pe_05kn, "prusak_v2": case_prusak_v2, "size_3km": case_size_3km}
