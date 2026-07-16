"""Public Python API of HyProp (ARCHITECTURE.md, principle 3).

GUI and CLI are thin clients of this module. Implemented incrementally:

* E1: configuration round-trip, database access, registry bootstrap.
* E6: :func:`run` — full transient simulation.
* E8: :func:`size` — inverse design from mission requirements.
* E9: :func:`run_batch` — parallel case matrices.

Example
-------
>>> import hyprop.api as api
>>> config = api.load_config("engine.yaml")
>>> result = api.run(config)          # available from stage E6
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from hyprop.core.config import EngineConfig
from hyprop.core.logging import get_logger
from hyprop.core.registry import autodiscover

_log = get_logger(__name__)
_bootstrapped = False


def _bootstrap() -> None:
    """Discover plugin models once per process."""
    global _bootstrapped
    if not _bootstrapped:
        autodiscover()
        _bootstrapped = True


def load_config(path: Union[str, Path]) -> EngineConfig:
    """Load, migrate and validate an :class:`EngineConfig` from YAML."""
    _bootstrap()
    config = EngineConfig.from_yaml(path)
    _log.info("Loaded config '%s' (schema %s)", config.name, config.version)
    return config


def save_config(config: EngineConfig, path: Union[str, Path]) -> None:
    """Serialise an :class:`EngineConfig` to YAML."""
    config.to_yaml(path)
    _log.info("Saved config '%s' -> %s", config.name, path)


def run(config: EngineConfig):
    """Run the transient simulation for one case.

    Implemented in stage E6 (simulation/solver).
    """
    raise NotImplementedError(
        "api.run() arrives with stage E6 (transient solver)."
    )


def run_batch(cases, n_jobs: int = -1):
    """Run a matrix of cases in parallel. Implemented in stage E9."""
    raise NotImplementedError(
        "api.run_batch() arrives with stage E9 (batch module)."
    )


def size(mission):
    """Inverse design: mission requirements -> initial EngineConfig.

    Implemented in stage E8 (sizing module).
    """
    raise NotImplementedError(
        "api.size() arrives with stage E8 (sizing module)."
    )
