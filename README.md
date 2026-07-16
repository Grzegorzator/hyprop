# HyProp

**Hybrid Rocket Preliminary Sizing & Analysis Environment**

Engineering tool for hybrid rocket motor design: from mission requirements,
through HRAP-like transient simulation and Representative Operating Points
(ROP), to optimization, NASA-style reports and a PySide6 GUI.

Status: **stage E1 of 12** (core foundation). See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design and
development plan.

## Install (development)

```bash
pip install -e .[dev]
pytest
```

Optional extras: `cea` (RocketCEA), `cantera`, `props` (CoolProp),
`opt` (pymoo, SALib), `export`, `gui` (PySide6).

## Quick start (E1 scope)

```python
import hyprop.api as api
from hyprop.data import load_fuel, load_oxidizer

config = api.load_config("examples/prusak_v2.yaml")
fuel = load_fuel(config.fuel.name)          # validated database entry
print(fuel.regression_for("n2o"))           # rdot = a*G^n*L^m datasets
```

## Layout

```
hyprop/core/     units (Pint), constants, EngineConfig (versioned), plugin
                 registry, logging, TimeHistory
hyprop/data/     built-in propellant databases (YAML, sourced values)
hyprop/api.py    public API: load_config/save_config (run/size/batch: E6/E8/E9)
tests/           pytest suite
docs/            architecture & model documentation
```

## Authors

MASSLACZEK12 (design authority, physical models) & Claude (implementation).
All empirical coefficients require confirmation by fire tests before
design use — entries carry `verify` flags and sources.
