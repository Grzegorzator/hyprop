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
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider"],
                       cwd=REPO, capture_output=True, text=True)
    lines = [l for l in p.stdout.splitlines() if l.strip()]
    tail = lines[-1] if lines else "?"
    skips = [l for l in lines if l.startswith("SKIPPED")]
    return tail + ("\n" + "\n".join(skips) if skips else "")


def _git() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return "?"


def main() -> None:
    logging.disable(logging.WARNING)
    warnings.filterwarnings("ignore")
    from validation import readme_claims

    rows = readme_claims.all_rows()
    md = [
        "# HyProp – raport walidacji\n",
        f"Wygenerowano: {_dt.datetime.now():%Y-%m-%d %H:%M}, commit `{_git()}`  ",
        f"Środowisko: {_versions()}  ",
        "Polecenie: `python -m validation.run_all` (zmienne środowiskowe: patrz `validation/README.md`).\n",
        "Zasada: wiersz może mieć PASS tylko przy sprawdzalnym źródle referencji. "
        "Brak źródła = `TODO: brak referencji`. INFO = wielkość raportowana bez kryterium.\n",
        "## 0. Zestaw testów (wszystkie opcjonalne backendy zainstalowane)\n",
        "```", _pytest_summary(), "```",
        "## 1. Odtworzenie deklaracji z README\n",
        f"Podsumowanie: {tally(rows)}\n",
        to_markdown(rows),
        (REPO / "validation" / "NOTES_stage1.md").read_text(encoding="utf-8"),
    ]
    out = REPO / "docs" / "VALIDATION.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"Written {out} ({tally(rows)})")


if __name__ == "__main__":
    main()
