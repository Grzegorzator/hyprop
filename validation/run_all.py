"""Regenerate docs/VALIDATION.md with one command (run from the repo root):

    python -m validation.run_all

External reference files are read from environment variables, see
validation/README.md. Missing references turn rows into TODO, never PASS.
"""

from __future__ import annotations

import datetime as _dt
import importlib
import logging
import platform
import subprocess
import sys
import warnings

from validation.common import REPO, tally, to_markdown


def _versions() -> str:
    out = [f"Python {platform.python_version()} ({platform.system()})"]
    for mod in ("numpy", "scipy", "cantera", "CoolProp", "rocketcea", "pymoo", "shapely", "pint"):
        try:
            m = importlib.import_module(mod)
            out.append(f"{mod} {getattr(m, '__version__', '?')}")
        except Exception:
            out.append(f"{mod} —")
    return ", ".join(out)


def _pytest_summary() -> str:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
    tail = lines[-1] if lines else "?"
    skips = [ln for ln in lines if ln.startswith("SKIPPED")]
    return tail + ("\n" + "\n".join(skips) if skips else "")


def _git() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True
        ).stdout.strip()
    except Exception:
        return "?"


SECTIONS = (
    ("1. Odtworzenie deklaracji z README", "readme_claims"),
    ("2. Termochemia PE/N2O – siatka vs NASA CEA", "thermo_grid"),
    ("3. Przepływ w dyszy – przykłady Suttona", "nozzle"),
    ("4. Własności N2O – ESDU 91022 vs EOS (CoolProp/NIST)", "n2o"),
    ("5. Zbiornik i wtryskiwacz – literatura", "feed"),
    ("6. Regresja paliwa – literatura", "regression_lit"),
    ("8. Zbieżność numeryczna", "convergence"),
    ("9. Analiza wymiarowa", "units_audit"),
)


def _invariants_summary() -> str:
    p = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_invariants.py",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
    return lines[-1] if lines else "?"


def main() -> None:
    import importlib

    logging.disable(logging.WARNING)
    warnings.filterwarnings("ignore")
    all_rows = []
    body = []
    for title, mod in SECTIONS:
        rows = importlib.import_module(f"validation.{mod}").all_rows()
        all_rows += rows
        body += [f"## {title}\n", f"Podsumowanie: {tally(rows)}\n", to_markdown(rows)]
    inv = _invariants_summary()
    md = [
        "# HyProp – raport walidacji (etap 1)\n",
        f"Wygenerowano: {_dt.datetime.now():%Y-%m-%d %H:%M}, commit `{_git()}`  ",
        f"Środowisko: {_versions()}  ",
        "Polecenie: `python -m validation.run_all` (zmienne środowiskowe: patrz "
        "`validation/README.md`).\n",
        "Zasada: wiersz może mieć PASS tylko przy sprawdzalnym źródle referencji. "
        "Brak źródła = `TODO: brak referencji`. INFO = wielkość raportowana bez kryterium.\n",
        f"**Razem: {tally(all_rows)}**\n",
        (REPO / "validation" / "SUMMARY_stage1.md").read_text(encoding="utf-8"),
        "## 0. Zestaw testów (wszystkie opcjonalne backendy zainstalowane)\n",
        "```",
        _pytest_summary(),
        "```",
        *body,
        "## 7. Niezmienniki fizyczne (Hypothesis, `tests/test_invariants.py`)\n",
        "Bilans masy utleniacza i paliwa, impuls = ∫F dt, port tylko rośnie, Pc między otoczeniem "
        "a zbiornikiem, "
        "brak NaN/ujemnych mas, niezależność od jednostek wejścia.\n",
        "```",
        inv,
        "```",
        (REPO / "validation" / "NOTES_stage1.md").read_text(encoding="utf-8"),
    ]
    out = REPO / "docs" / "VALIDATION.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"Written {out} ({tally(all_rows)})")


if __name__ == "__main__":
    main()
