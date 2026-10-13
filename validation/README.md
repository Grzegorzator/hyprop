# validation/

Validation suite for HyProp, kept separate from `tests/` (unit tests).
It regenerates `docs/VALIDATION.md` with one command, run from the repo root:

```bash
pip install -e .[dev,cantera,props,export,validation] rocketcea   # rocketcea needs gfortran
export HYPROP_HRAP_DIR=/path/to/HRAP/application            # contains output/ and propellant_configs/
python -m validation.run_all
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
* `readme_claims.py` – stage 1, item 1: reproduction of every number in README.md.
* `NOTES_stage1.md` – hand-written findings appended to the report.
* `run_all.py` – entry point; also runs `pytest` and records the result.
