# validation/

Validation suite for HyProp, kept separate from `tests/` (unit tests).
It regenerates `docs/VALIDATION.md` with one command, run from the repo root:

```bash
uv sync --extra cantera --extra props --extra export --extra validation --extra cea  # cea = RocketCEA, needs gfortran
export HYPROP_HRAP_DIR=/path/to/HRAP/application            # contains output/ and propellant_configs/
uv run python -m validation.run_all
```

| Variable | File(s) used | Used for |
|---|---|---|
| `HYPROP_HRAP_DIR` | `output/prusakv2_HRAP_output.csv`, `propellant_configs/{HDPE,Paraffin,HTPB}.mat` | E6 benchmark, regression coefficients |

PE/N2O thermochemistry is checked against NASA's own CEA package (`cea`,
reactant `(CH2)x(cr)`, same dHf as HyProp); without it those rows become TODO.

Every reference file is identified in the report by its SHA-256 prefix.
A missing file turns its rows into `TODO: brak referencji` (never PASS).

Files:

* `common.py` – `Row` (one report line), PASS/FAIL/TODO logic, Markdown writer.
* `readme_claims.py` – item 1: reproduction of every number in README.md.
* `thermo_grid.py` – item 2: PE/N2O thermochemistry grid vs NASA CEA
  (full grid in `docs/validation_data/thermo_grid_pe_n2o.csv`).
* `nozzle.py` – item 3: ideal nozzle relations vs Sutton & Biblarz examples.
* `n2o.py` – item 4: ESDU 91022 vs EOS (and NIST, if `data/nist_n2o_sat.csv` exists).
* `feed.py` – item 5: injector models vs Waxman et al.; tank property sensitivity.
* `regression_lit.py` – item 6: regression law vs literature.
* `convergence.py` – item 8: dt and Pc-tolerance convergence (Richardson).
* `units_audit.py` – item 9: dimensional analysis with Pint.
* item 7 (invariants) lives in `tests/test_invariants.py` (Hypothesis).
* `SUMMARY_stage1.md`, `NOTES_stage1.md` – hand-written summary and findings.
* `run_all.py` – entry point; also runs `pytest` and records the result.
