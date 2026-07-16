"""Memoising wrapper for thermochemistry backends.

A transient simulation queries thermochemistry thousands of times with
slowly varying (O/F, Pc). Exact-repeat queries are served from a dict
keyed on rounded inputs; the rounding tolerances are far below the
uncertainty of any combustion model. Grid-interpolation tables (HRAP
style, cf. ``prop_T/prop_k/prop_M`` in ``*.mat`` configs) will be added
at stage E6 when the solver's access pattern is known.
"""

from __future__ import annotations

from typing import Dict, Tuple

from hyprop.cea.backend import CEAResult, ThermochemistryBackend
from hyprop.core.logging import get_logger

_log = get_logger(__name__)


class CachedBackend(ThermochemistryBackend):
    """Decorator-pattern cache around any :class:`ThermochemistryBackend`.

    Keys are rounded to: O/F 1e-3, Pc 100 Pa, eps 1e-2 - i.e. below any
    physically meaningful resolution of the underlying models.
    """

    name = "cached"

    def __init__(self, backend: ThermochemistryBackend) -> None:
        self._backend = backend
        self._cache: Dict[Tuple[float, float, float], CEAResult] = {}
        self.hits = 0
        self.misses = 0

    def query(self, of: float, pc: float, eps: float) -> CEAResult:
        key = (round(of, 3), round(pc, -2), round(eps, 2))
        result = self._cache.get(key)
        if result is not None:
            self.hits += 1
            return result
        self.misses += 1
        result = self._backend.query(of, pc, eps)
        self._cache[key] = result
        return result

    def __len__(self) -> int:
        return len(self._cache)
