"""Regenerate tests/golden/*.json - run ONLY after an intended physics change:

    python tests/golden/regenerate.py            # all cases
    python tests/golden/regenerate.py pe_05kN    # one case

Commit the JSON diff together with the change that caused it, and say in
the commit message why the numbers moved.
"""

from __future__ import annotations

import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cases import CASES, GOLDEN_DIR, REPO  # noqa: E402


def _meta() -> dict:
    import cantera
    import numpy
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                            capture_output=True, text=True).stdout.strip()
    return dict(generated=_dt.datetime.now().isoformat(timespec="seconds"), commit=commit,
                python=sys.version.split()[0], numpy=numpy.__version__, cantera=cantera.__version__)


def main(names) -> None:
    import logging
    import warnings
    logging.disable(logging.WARNING)
    warnings.filterwarnings("ignore")
    for name in names or CASES:
        data = dict(meta=_meta(), result=CASES[name]())
        path = GOLDEN_DIR / f"{name}.json"
        path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"written {path}")


main(sys.argv[1:])
