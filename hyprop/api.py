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
    """Run the transient simulation for one case (stage E6).

    Returns
    -------
    hyprop.simulation.SimulationResult
        Full time history, event log and summary metrics.
    """
    from hyprop.simulation import run_simulation

    _bootstrap()
    return run_simulation(config)


def run_batch(cases, n_jobs: int = -1):
    """Run a matrix of cases in parallel. Implemented in stage E9."""
    raise NotImplementedError(
        "api.run_batch() arrives with stage E9 (batch module)."
    )


def size(thrust_n: float, total_impulse_ns: float, apogee_m: float,
         **kwargs):
    """Inverse design: mission -> converged EngineConfig (stage E8).

    Returns
    -------
    hyprop.sizing.SizingResult
        Converged config + nozzle design + achieved metrics + warnings.
    """
    from hyprop.sizing import size_engine

    _bootstrap()
    return size_engine(thrust_n, total_impulse_ns, apogee_m, **kwargs)
