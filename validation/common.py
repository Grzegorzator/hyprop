"""Shared helpers for the validation suite (kept separate from tests/).

Every row of docs/VALIDATION.md is a :class:`Row`. Hard rule: a row may only
be PASS when its reference value has a verifiable source (full citation, URL
or a hashed local file). Rows without a verifiable reference are TODO and are
never counted as PASS.
"""

from __future__ import annotations

import hashlib
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

REPO = Path(__file__).resolve().parents[1]

PASS, FAIL, TODO, INFO = "PASS", "FAIL", "TODO: brak referencji", "INFO"


@dataclass
class Row:
    quantity: str
    case: str
    reference: Optional[float]
    source: str
    hyprop: Optional[float]
    tol: Optional[float] = None          # tolerance in the units of `dev`
    dev_kind: str = "rel"                # "rel" [%] | "abs" [units of value]
    comment: str = ""
    unit: str = ""
    status: str = field(default="")

    @property
    def dev(self) -> Optional[float]:
        if self.reference is None or self.hyprop is None:
            return None
        if self.dev_kind == "rel":
            return 100.0 * (self.hyprop / self.reference - 1.0)
        return self.hyprop - self.reference

    def evaluate(self) -> "Row":
        if self.status:                      # explicitly set (INFO / forced)
            return self
        if self.reference is None or not self.source:
            self.status = TODO
        elif self.hyprop is None or (isinstance(self.hyprop, float)
                                     and math.isnan(self.hyprop)):
            self.status = FAIL
        elif self.tol is None:
            self.status = INFO
        else:
            self.status = PASS if abs(self.dev) <= self.tol else FAIL
        return self


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def external(env: str, *candidates: str) -> Optional[Path]:
    """Locate an external reference file: env var first, then candidates."""
    paths = [os.environ.get(env, "")] + list(candidates)
    for p in paths:
        if p and Path(p).exists():
            return Path(p)
    return None


def _fmt(x: Optional[float]) -> str:
    if x is None:
        return "—"
    if isinstance(x, str):
        return x
    ax = abs(x)
    if ax == 0:
        return "0"
    if ax >= 1e4 or ax < 1e-3:
        return f"{x:.4g}"
    if ax >= 100:
        return f"{x:.1f}"
    return f"{x:.4g}"


def to_markdown(rows: List[Row]) -> str:
    head = ("| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp "
            "| Odchyłka | Tolerancja | Status | Komentarz |\n"
            "|---|---|---|---|---|---|---|---|---|---|\n")
    out = []
    for i, r in enumerate(rows, 1):
        r.evaluate()
        dev = r.dev
        if dev is None:
            dev_s = "—"
        elif r.dev_kind == "rel":
            dev_s = f"{dev:+.2f} %"
        else:
            dev_s = f"{dev:+.4g} {r.unit}".strip()
        tol_s = "—" if r.tol is None else (
            f"±{r.tol:g} %" if r.dev_kind == "rel" else f"±{r.tol:g} {r.unit}".strip())
        unit = f" {r.unit}" if r.unit else ""
        esc = lambda x: str(x).replace("|", "\\|")
        r.quantity, r.case, r.source, r.comment = map(esc, (r.quantity, r.case, r.source, r.comment))
        out.append(
            f"| {i} | {r.quantity} | {r.case} | {_fmt(r.reference)}{unit if r.reference is not None else ''} "
            f"| {r.source} | {_fmt(r.hyprop)}{unit if r.hyprop is not None else ''} | {dev_s} | {tol_s} "
            f"| **{r.status}** | {r.comment} |")
    return head + "\n".join(out) + "\n"


def tally(rows: List[Row]) -> str:
    counts = {}
    for r in rows:
        r.evaluate()
        counts[r.status] = counts.get(r.status, 0) + 1
    return ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
