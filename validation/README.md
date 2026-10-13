# validation/

Validation suite for HyProp, kept separate from `tests/` (unit tests).
It regenerates `docs/VALIDATION.md` with one command, run from the repo root:

```bash
pip install -e .[dev,cantera,props,export,opt] rocketcea   # rocketcea needs gfortran
export HYPROP_HRAP_DIR=/path/to/HRAP/application            # contains output/ and propellant_configs/
export HYPROP_REF_07=/path/to/07_cantera_punkt0_termochemia.py
python -m validation.run_all
```

| Variable | File(s) used | Used for |
|---|---|---|
| `HYPROP_HRAP_DIR` | `output/prusakv2_HRAP_output.csv`, `propellant_configs/{HDPE,Paraffin,HTPB}.mat` | E6 benchmark, regression coefficients |
| `HYPROP_REF_07` | user's `07_cantera_punkt0_termochemia.py` (run in a temp dir) | Cantera anchor (Tc, gamma, c*, Isp) |

Every reference file is identified in the report by its SHA-256 prefix.
A missing file turns its rows into `TODO: brak referencji` (never PASS).

Files:

* `common.py` – `Row` (one report line), PASS/FAIL/TODO logic, Markdown writer.
* `readme_claims.py` – stage 1, item 1: reproduction of every number in README.md.
* `NOTES_stage1.md` – hand-written findings appended to the report.
* `run_all.py` – entry point; also runs `pytest` and records the result.
