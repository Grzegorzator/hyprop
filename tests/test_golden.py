"""Golden tests: frozen reference results (stage 2), see tests/golden/cases.py.

Tolerances, justified by a noise study on pe_05kN (tests/golden/README.md):
tightening the Pc solver tolerance 1e-4 -> 1e-5 or
perturbing the tabulated c* by 1e-6 (a stand-in for library/platform
round-off) moves scalars by <= 1e-6 relative and sampled series by
<= 5.5e-5 of the channel maximum, and does not move any event.

* scalars, impulse-weighted point, sizing outputs: rtol = 2e-4
  (~200x the observed noise, 5x below the smallest change we want to see,
  0.1 %);
* time series: atol = 1e-3 x channel maximum (~20x noise), skipping samples
  within 0.1 s of an event, where a one-step event shift is legitimately
  large point-wise;
* events (liquid run-out, pressure decay): +-1.5 dt (events are quantised
  to the time step);
* sizing iteration count: exact.

Accepting new numbers after an intended change: python tests/golden/regenerate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("cantera")
sys.path.insert(0, str(Path(__file__).resolve().parent / "golden"))
import cases  # noqa: E402

RTOL = 2e-4
SERIES_ATOL_FRAC = 1e-3
EVENT_GUARD_S = 0.1
pytestmark = pytest.mark.slow


def _golden(name):
    return json.loads((cases.GOLDEN_DIR / f"{name}.json").read_text(encoding="utf-8"))["result"]


@pytest.fixture(autouse=True)
def _quiet_and_fresh_cache():
    import hyprop.simulation.solver as sm

    sm._TABLE_CACHE.clear()
    yield
    sm._TABLE_CACHE.clear()


def _check_transient(new, ref):
    for k, v in ref["scalars"].items():
        assert new["scalars"][k] == pytest.approx(v, rel=RTOL), k
    for k, v in ref["impulse_weighted"].items():
        assert new["impulse_weighted"][k] == pytest.approx(v, rel=RTOL), f"iw.{k}"
    assert set(new["events"]) == set(ref["events"])
    for k, v in ref["events"].items():
        assert new["events"][k] == pytest.approx(v, abs=1.5 * ref["dt"]), f"event {k}"
    t = np.asarray(ref["series"]["t"])
    n = min(len(t), len(new["series"]["t"]))
    mask = np.ones(n, dtype=bool)
    for te in ref["events"].values():
        mask &= np.abs(t[:n] - te) > EVENT_GUARD_S
    for ch in cases.SERIES_CHANNELS:
        a = np.asarray(new["series"][ch])[:n][mask]
        b = np.asarray(ref["series"][ch])[:n][mask]
        atol = SERIES_ATOL_FRAC * float(np.max(np.abs(ref["series"][ch])))
        np.testing.assert_allclose(a, b, rtol=0.0, atol=atol, err_msg=ch)
    assert new["thermo_backend"] == ref["thermo_backend"]


@pytest.mark.parametrize("name", ["pe_05kN", "prusak_v2"])
def test_golden_transient(name):
    _check_transient(cases.CASES[name](), _golden(name))


def test_golden_sizing_3km():
    new, ref = cases.case_size_3km(), _golden("size_3km")
    assert new["iterations"] == ref["iterations"]
    assert new["warnings"] == ref["warnings"]
    for group in ("achieved", "design"):
        for k, v in ref[group].items():
            assert new[group][k] == pytest.approx(v, rel=RTOL), f"{group}.{k}"
