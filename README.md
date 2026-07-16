# HyProp

**Hybrid Rocket Preliminary Sizing & Analysis Environment**

Engineering tool for hybrid rocket motor design: from mission requirements,
through HRAP-like transient simulation and Representative Operating Points
(ROP), to optimization, NASA-style reports and a PySide6 GUI.

Full design & development plan: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Status: stage E7 of 12 complete

| Stage | Scope | Status |
|---|---|---|
| E0 | Architecture v0.2 (physics/ layer, API-first, plugin registry, ROP-centric) | done |
| E1 | `core/` (Pint units, versioned `EngineConfig`, registry, logging, `TimeHistory`) + `data/` (5 fuels, 4 oxidizers, sourced values) | done |
| E2 | `physics/compressible` (isentropic nozzle flow, Sutton Ch. 3) + `cea/` (RocketCEA & Cantera backends, equilibrium + frozen, cache) | done |
| E3 | `geometry/` (cylindrical, multiport, star, wagon wheel, custom via contour offset) | done |
| E4 | `regression/` (power law, G_ox/G_total) + `nozzle/losses` + `performance/` | done |
| E5 | `tank/` (equilibrium N2O blowdown, ESDU 91022 + CoolProp) + `injector/` (SPI default, NHNE, HEM) | done |
| E6 | Transient solver (`api.run`, tabulated CEA, fixed-point/Brent Pc) + HRAP benchmark | done |
| E7 | Representative Operating Points (`oppoints/`: weighted averages, design points, phases, impulse percentiles) | done |
| E8 | Inverse sizing + chamber + nozzle sizing on ROP points | next |
| E9-E12 | Batch/sensitivity/uncertainty, exports & NASA-style report, optimization, GUI | planned |

Tests: **101 passing** (`pytest`). Physical model decisions log: D1-D10 in
`docs/ARCHITECTURE.md` par. 8. Resolved: D1 (N2O props: ESDU 91022 in the
solver loop + CoolProp for injector thermodynamics and cross-validation),
D2 (tank: thermodynamic-equilibrium adiabatic blowdown, HRAP-compatible),
D3 (injector default: SPI, as HRAP; NHNE/HEM available), D6 (nozzle:
shifting equilibrium default, frozen reported as lower bound).

## Validation anchors

* Cantera backend vs user's validated `07_cantera` script (paraffin
  C32H66/N2O, Pc 35 bar, O/F 6.5): Tc 3292 K, gamma 1.245, Isp 247 s -
  agreement <1%; equilibrium c* exceeds ideal-formula c* by ~2.3%
  (documented methodological difference).
* `physics/compressible` vs Anderson isentropic tables & Sutton Cf example.
* Regression coefficients a, n extracted from HRAP `.mat` configs
  (HDPE 0.104/0.352, paraffin 0.0304/0.681, HTPB 0.198/0.325; mm/s
  convention confirmed in HRAP propellant_template.m).
* N2O saturation properties: ESDU 91022 correlations cross-validated
  against CoolProp (psat, rho_l within 1.5%, 263-303 K).
* **E6 transient benchmark vs HRAP (prusak_v2, HDPE/N2O)**: liquid-phase
  mean deviations Pc 1.7%, tank pressure 0.6%, O/F 1.0%, thrust 6.2%;
  LRO 7.19 s vs ~7.5 s. Thrust surplus is methodological (HyProp uses
  shifting-equilibrium exhaust velocity; HRAP uses RPA-table Cf, closer
  to frozen). CSV-implied regression a = 1.040e-4 SI independently
  confirms the HRAP unit conversion. See examples/benchmark_prusak_v2.py.
* Example sizing delivered: examples/hdpe_05kN.yaml - HDPE/N2O, 0.5 kN,
  It = 3942 Ns, Pc 37 bar, LRO 7.4 s (examples/sizing_hdpe_05kN.py).
* ROP demo (examples/rop_hdpe_05kN.py): plain time averages understate
  thrust by 51% and Pc by 48% vs impulse-weighted values - the liquid
  phase delivers 92.4% of impulse in 42.6% of burn time; this is why all
  design modules read the impulse-weighted point, never time averages.

## Install (development)

```bash
pip install -e .[dev]
pytest
```

Optional extras: `cea` (RocketCEA; needs a Fortran compiler), `cantera`,
`props` (CoolProp), `opt` (pymoo, SALib), `export`, `gui` (PySide6).

## Quick start

```python
import hyprop.api as api
from hyprop.cea import get_backend
from hyprop.geometry import CylindricalGrain

config = api.load_config("examples/prusak_v2.yaml")

cea = get_backend("auto", fuel="paraffin", oxidizer="n2o")
result = cea.query(of=6.5, pc=35e5, eps=6.0)
print(result.chamber.temperature_k, result.cstar_m_s,
      result.isp_s(101325.0), result.isp_s(101325.0, mode="frozen"))

grain = CylindricalGrain(length_m=0.3, outer_diameter_m=0.08,
                         initial_diameter_m=0.03)
print(grain.burn_area(w=0.005), grain.web_remaining(w=0.005))
```

## Layout

```
hyprop/core/       units (Pint), constants, EngineConfig (versioned),
                   plugin registry, logging, TimeHistory
hyprop/physics/    shared equation library (compressible flow; no deps
                   on other modules)
hyprop/cea/        thermochemistry: RocketCEA (primary), Cantera
                   (fallback), memoising cache
hyprop/geometry/   grain ports as functions of burned web w: analytic
                   (cylindrical, multiport) + contour-offset engine
                   (star, wagon wheel, custom polygons; shapely)
hyprop/tank/       N2O saturation properties (ESDU 91022 / CoolProp),
                   equilibrium blowdown, pressure-fed, constant-mdot
hyprop/injector/   SPI (default), HEM, NHNE (Dyer) orifice models
hyprop/regression/ power-law rdot = a*G^n*L^m (G_ox / G_total)
hyprop/data/       built-in propellant databases (YAML, sourced values,
                   verify flags)
hyprop/simulation/ transient solver: tank-injector-chamber-regression-
                   nozzle coupling per time step (HRAP loop), events
hyprop/oppoints/   Representative Operating Points hub: time/thrust/mdot/
                   Pc/heat-flux-proxy/custom weighted averages, peak &
                   percentile points, phase statistics, recommendations
hyprop/api.py      public API: load/save config, run (size/batch: E8/E9)
tests/             pytest suite (101 tests)
docs/              architecture & model documentation
```

## Authors

MASSLACZEK12 (design authority, physical models) & Claude (implementation).
All empirical coefficients require confirmation by fire tests before
design use - entries carry `verify` flags and sources.
