# HyProp

**Hybrid Rocket Preliminary Sizing & Analysis Environment**

Engineering tool for hybrid rocket motor design: from mission requirements,
through HRAP-like transient simulation and Representative Operating Points
(ROP), to optimization, NASA-style reports and a PySide6 GUI.

Full design & development plan: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Status: ALL 12 STAGES COMPLETE (v0.1.0)

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
| E8 | Inverse sizing (`api.size`), ISA atmosphere, nozzle sizing on ROP (altitude-adapted eps), chamber L*, 1-DOF trajectory check | done |
| E9 | Batch (grid/LHS, CEA-table cache), sensitivity (OAT default, Morris/Sobol via SALib), Monte Carlo uncertainty, port Re/Ma regime flags | done |
| E10 | Exports (CSV/XLSX/JSON + config YAML), NASA-style LaTeX report (auto-PDF when pdflatex present), user database (YAML: engines/materials/injectors/tests) | done |
| E11 | Optimization: differential evolution (scipy) + NSGA-II (pymoo, optional) over config paths, objectives/constraints on ROP metrics with penalty method | done |
| E12 | GUI (PySide6, MVVM: Qt-free viewmodel + main window; `hyprop-gui` entry point) | done |

Tests: **120 passing** (`pytest`). Physical model decisions log: D1-D10 in
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
* E8 mission demo (0 m ASL -> 3000 m apogee): api.size converged in 5
  iterations to F_iw=494 N, It=4083 Ns, eps=5.02 adapted at 1000 m;
  1-DOF trajectory check (m_dry=9 kg, Cd=0.55, D=0.10 m assumed) gives
  apogee 3291 m (+10% margin). examples/size_hdpe_3km.py,
  examples/trajectory_hdpe_3km.py.
* ROP demo (examples/rop_hdpe_05kN.py): plain time averages understate
  thrust by 51% and Pc by 48% vs impulse-weighted values - the liquid
  phase delivers 92.4% of impulse in 42.6% of burn time; this is why all
  design modules read the impulse-weighted point, never time averages.

## Install on a clean Windows machine (recommended path)

Only two things must be installed manually; everything else is pulled
automatically by pip into an isolated virtual environment:

| # | Component | Where | Notes |
|---|---|---|---|
| 1 | **Python 3.11-3.14 (64-bit)** | https://python.org | During setup tick **"Add python.exe to PATH"** |
| 2 | **Git** | https://git-scm.com | Defaults are fine |

Then, in PowerShell or cmd:

```bat
git clone https://github.com/Grzegorzator/hyprop.git
cd hyprop
install_windows.bat   :: creates .venv and installs all dependencies
run_gui.bat           :: launches the GUI
```

PowerShell note: scripts in the current directory need the `.\` prefix
(`.\install_windows.bat`, `.\run_gui.bat`); plain `cmd` and
double-click in Explorer work without it.

`install_windows.bat` installs into `.venv` (does not touch the system
Python): NumPy, SciPy, pandas, matplotlib, Pint, pydantic, PyYAML,
shapely, **Cantera** (thermochemistry), **CoolProp** (N2O properties,
HEM/NHNE injector), **PySide6** (GUI), openpyxl/jinja2 (exports) and
pytest. First simulation run builds the CEA table (~20-30 s); later
runs are cached. Verify the installation with
`.venv\Scripts\python -m pytest -q` (125 tests).

Optional extras (not required to run the app):

| Component | Enables | How |
|---|---|---|
| **MiKTeX** (https://miktex.org) | automatic PDF compilation of design reports (otherwise a `.tex` file is produced - compile anywhere) | install, first run auto-fetches packages |
| **RocketCEA + MinGW gfortran** | native NASA-CEA backend (Cantera fallback is used otherwise and is validated to <1%) | see RocketCEA docs for Windows |
| `pip install -e .[opt]` | pymoo (NSGA-II) and SALib (Morris/Sobol sensitivity) | inside `.venv` |

## Install on Linux / macOS

```bash
# Ubuntu/Debian prerequisites (Fedora: dnf, Arch: pacman):
sudo apt install python3 python3-venv python3-pip git

git clone https://github.com/Grzegorzator/hyprop.git
cd hyprop
./install_linux.sh    # creates .venv and installs all dependencies
./run_gui.sh          # launches the GUI
```

If the scripts are not executable after cloning (repository committed
from Windows), run them via `bash install_linux.sh` / `bash run_gui.sh`
or restore the bit once: `chmod +x install_linux.sh run_gui.sh`.

Notes: the GUI needs Qt's xcb libraries on minimal desktops
(`sudo apt install libxcb-cursor0` if the window does not open); for
PDF reports install TeX Live (`sudo apt install texlive-latex-extra`),
otherwise a compilable `.tex` is produced. Everything else is identical
to Windows - same `.venv`, same tests (`.venv/bin/python -m pytest -q`).

### Install (development, any OS)

```bash
pip install -e .[dev,gui,cantera,props,export]
pytest
```

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
hyprop/sizing/     inverse design api.size (analytic guess + ROP loop)
hyprop/batch/      case grids/LHS over config paths
hyprop/analysis/   sensitivity (OAT/Morris/Sobol), Monte Carlo, Re/Ma flags
hyprop/export/     CSV/XLSX/JSON tables + NASA-style LaTeX/PDF report
hyprop/database/   user records (YAML): engines, materials, injectors, tests
hyprop/optimization/ DE (scipy) + NSGA-II (pymoo) on ROP objectives
hyprop/gui/        PySide6 app: hyprop-gui (pip install -e .[gui])
hyprop/api.py      public API: load/save config, run, size
tests/             pytest suite (120 tests)
docs/              architecture & model documentation
```

## Roadmap (post-v0.1)

RocketCEA backend validation on Windows (needs MinGW gfortran);
Zilliac-Karabeyoglu non-equilibrium tank; Bray sudden-freeze nozzle
chemistry; real-gas vapour blowdown (D7); nozzle erosion; trajectory
module coupled to sizing; OpenMDAO integration; CFD hooks.

## Authors

MASSLACZEK12 (design authority, physical models) & Claude (implementation).
All empirical coefficients require confirmation by fire tests before
design use - entries carry `verify` flags and sources.
