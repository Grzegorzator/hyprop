# Golden tests (stage 2)

Frozen reference results that protect HyProp's numbers during refactoring
(Pint removal, packaging, YAADO adapter). They are regression references,
not validation; validation is in `validation/` and `docs/VALIDATION.md`.

| File | Case | Content |
|---|---|---|
| `pe_05kN.json` | `examples/pe_05kN.yaml` (LDPE/N2O, eta_c* 0.90) | summary scalars, events, impulse-weighted point, 9 channels every 0.25 s |
| `prusak_v2.json` | HRAP benchmark config (`examples/benchmark_prusak_v2.py`) | same |
| `size_3km.json` | `api.size(500 N, 4000 Ns, 3 km)`, LDPE, 6 x 5 CEA table | iterations, achieved values, grain/tank/injector/nozzle design |

All cases pin the Cantera backend (reproducible without a Fortran compiler).
Each JSON stores the generating commit and library versions under `meta`.

## Tolerances and why

Noise study on `pe_05kN` (2026-10-13): Pc solver tolerance 1e-4 -> 1e-5, or
tabulated c* perturbed by 1e-6 (stand-in for platform/library round-off):

* scalars and impulse-weighted values move by <= 1e-6 relative;
* sampled series by <= 5.5e-5 of the channel maximum;
* events (liquid run-out, pressure decay) do not move.

Hence `rtol = 2e-4` for scalars and sizing outputs (~200x noise, 5x below a
0.1 % change), series `atol = 1e-3 x channel max` (samples within 0.1 s of an
event are skipped: a one-step event shift is legitimately large point-wise),
events +-1.5 dt, sizing iteration count exact. Mutation check: +0.1 % on
delivered thrust is detected.

## Accepting new numbers

Only after an intended physics change:

```bash
python tests/golden/regenerate.py            # or: ... regenerate.py pe_05kN
```

Commit the JSON diff together with the change and explain in the message why
the numbers moved. Quick test run without golden tests: `pytest -m "not slow"`.
