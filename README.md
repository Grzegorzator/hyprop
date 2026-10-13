# HyProp

**Hybrid Rocket Preliminary Sizing & Analysis Environment** - a Python
library for preliminary sizing of N2O hybrid rocket motors: mission
requirements -> inverse sizing -> HRAP-like transient simulation ->
Representative Operating Points (ROP). Target: the hybrid-propulsion
solver of the KNN MELprop MDO framework YAADO.

Design document: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (v0.2
changes listed at its top). Validation report:
[`docs/VALIDATION.md`](docs/VALIDATION.md).

## Status

v0.2-dev. Library only (the PySide6 GUI of v0.1 was removed). No fire
test has been performed yet: every empirical coefficient (regression a,
n; eta_c*; injector Cd) carries a `verify` flag and must be confirmed
experimentally before design use.

## Install

```bash
git clone https://github.com/Grzegorzator/hyprop.git
cd hyprop
pip install -e .[dev,cantera,props,export]
pytest
```

Optional: `pip install rocketcea` (NASA CEA; needs a Fortran compiler)
and `pip install -e .[opt]` (pymoo NSGA-II, SALib Morris/Sobol).

## Physical conventions (v0.2)

* **Thrust** (Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed.,
  Sec. 3.5, Eqs. 3-40/3-41):
  `c_i = v_e + (p_e - p_a)*eps*c*_i/p_c`, `F = eta_c* * eta_noz * mdot * c_i`,
  with `eta_noz = lambda(alpha) * nozzle.efficiency`. Chamber pressure
  from `p_c = mdot * eta_c* * c*_i / (Cd * A_t)`.
* **Thermochemistry**: shifting equilibrium by default, frozen expansion
  reported alongside. `simulation.cea_backend`: `auto` (RocketCEA if
  installed, else Cantera), `rocketcea`, `cantera`. The examples pin
  `cantera` so they reproduce on any machine.
* **gamma**: `StationState.gamma` is the frozen cp/cv in every backend;
  `gamma_eq` is the equilibrium exponent gamma_s (CEA "GAMMAs").
* **Nozzle sizing**: eps from the CEA expansion (p_e = p_a at the design
  altitude), throat from the delivered Cf = lambda*eta*Cd*Cf_i at the
  design p_c.
* **Regression**: `rdot = a G^n L^m` in SI (m/s, kg/m^2/s). HRAP stores
  `a` in mm/s; HyProp's database holds `a_SI = a_HRAP * 1e-3`.

## Validation (summary; full table in docs/VALIDATION.md)

Reproduced with `python -m validation.run_all`.

* **HRAP v1.06 benchmark** (prusak_v2, HDPE/N2O, liquid phase): mean
  deviations Pc 1.7 %, tank pressure 0.6 %, O/F 1.0 %, thrust 0.9 %
  (0.2-7.0 s). Liquid run-out 7.19 s vs 6.955 s in HRAP (+3.4 %). This is a
  code-to-code check (same tank, injector and regression models), not a
  physical validation. HRAP omits eta_c* from thrust, so part of the
  thrust agreement is coincidental (docs/VALIDATION.md, Sec. 2).
* **Thermochemistry**: Cantera backend vs NASA CEA (RocketCEA) for
  C32H66/N2O, 35 bar, O/F 6.5: Tc, c*, Isp within 0.15 %; frozen and
  equilibrium gamma within 1e-3. The user's 07_cantera script is
  reproduced exactly (Tc 3292 K, gamma 1.247, Isp_opt 247.2 s). Its
  c* is 2.3 % below CEA because the ideal formula uses frozen gamma;
  with gamma_s the formula reproduces CEA c* to 0.13 %.
* **N2O**: ESDU 91022 vs CoolProp (Lemmon & Span 2006 EOS), 263-303 K:
  p_sat 0.16 %, rho_l 0.19 %.
* **Regression coefficients** match HRAP `.mat` files (HDPE 0.104/0.352,
  paraffin 0.0304/0.681, HTPB 0.198/0.325, mm/s convention).

## Examples (Cantera backend)

| Script | Result |
|---|---|
| `examples/sizing_hdpe_05kN.py` | HDPE/N2O: It = 3749 Ns, Pc_peak 36.9 bar, LRO 7.38 s, Isp 196 s |
| `examples/rop_hdpe_05kN.py` | time averages understate thrust by 51 % and Pc by 48 % vs impulse-weighted; liquid phase delivers 92.3 % of It in 42.6 % of burn time |
| `examples/size_hdpe_3km.py` | `api.size(500 N, 4000 Ns, 3 km)`: 7 iterations, F_iw 497 N, It 4040 Ns, Dt 12.0 mm, eps 5.03 adapted at 1000 m |
| `examples/trajectory_hdpe_3km.py` | 1-DOF, m_dry 7 kg (assumed), Cd 0.55, D 0.10 m: apogee 3775 m |
| `examples/benchmark_prusak_v2.py` | HRAP comparison (needs `HYPROP_HRAP_DIR`) |
| `examples/sensitivity_hdpe.py`, `examples/report_hdpe_3km.py` | OAT sensitivity; CSV/XLSX/JSON export + LaTeX report |

Figures and exports go to `outputs/` (git-ignored).

## Quick start

```python
import hyprop.api as api
from hyprop.cea import get_backend

result = api.run(api.load_config("examples/hdpe_05kN.yaml"))
print(result.summary["total_impulse_ns"], result.thermo_backend)

cea = get_backend("cantera", fuel="paraffin", oxidizer="n2o")
r = cea.query(of=6.5, pc=35e5, eps=5.0)
print(r.chamber.temperature_k, r.chamber.gamma, r.chamber.gamma_eq,
      r.cstar_m_s, r.isp_s(101325.0), r.isp_s(101325.0, mode="frozen"))
```

## Layout

```
hyprop/core/        units (Pint, I/O boundary), constants, EngineConfig, registry, TimeHistory
hyprop/physics/     compressible flow, ISA atmosphere
hyprop/cea/         thermochemistry: RocketCEA, Cantera, tabulated backend
hyprop/geometry/    grain ports (cylindrical, multiport, star, wagon wheel, custom)
hyprop/tank/        N2O properties (ESDU 91022 / CoolProp), equilibrium blowdown
hyprop/injector/    SPI (default), HEM, NHNE
hyprop/regression/  power law rdot = a G^n L^m
hyprop/data/        propellant databases (YAML, sourced values, verify flags)
hyprop/simulation/  transient solver (HRAP loop)
hyprop/oppoints/    Representative Operating Points
hyprop/sizing/      inverse sizing api.size
hyprop/nozzle/      nozzle sizing and losses
hyprop/batch/, analysis/, optimization/, export/, database/
validation/         validation suite -> docs/VALIDATION.md
tests/              pytest
```

## Authors

MASSLACZEK12 (design authority, physical models) & Claude (implementation).
