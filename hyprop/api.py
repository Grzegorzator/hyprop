"""Public Python API of HyProp (ARCHITECTURE.md, principle 3).

Thin entry points over the solver; a CLI or the YAADO adapter should call
only this module. Stages (ARCHITECTURE.md):

* E1: configuration round-trip, database access, registry bootstrap.
* E6: :func:`run` — full transient simulation.
* E8: :func:`size` — inverse design from mission requirements.
* E9: :func:`run_batch` — case matrices (sequential).

Example:
    >>> import hyprop.api as api
    >>> config = api.load_config("examples/pe_05kN.yaml")
    >>> result = api.run(config)
    >>> sized = api.size(thrust_n=500.0, total_impulse_ns=4000.0, apogee_m=3000.0)
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from hyprop.core.config import EngineConfig
from hyprop.core.logging import get_logger
from hyprop.core.registry import autodiscover

if TYPE_CHECKING:
    import pandas as pd

    from hyprop.simulation import SimulationResult
    from hyprop.sizing import SizingResult

_log = get_logger(__name__)
_bootstrapped = False


def _bootstrap() -> None:
    """Discover plugin models once per process."""
    global _bootstrapped
    if not _bootstrapped:
        autodiscover()
        _bootstrapped = True


def load_config(path: str | Path) -> EngineConfig:
    """Load, migrate and validate an engine configuration from YAML.

    Args:
        path: YAML file. Quantities may be SI floats or unit strings
            (``"35 bar"``); they are converted to SI on load.

    Returns:
        The validated configuration (all quantities in SI).

    Raises:
        ConfigError: If the file violates the schema.
        UnitError: If a unit string cannot be parsed or has wrong dimensions.
    """
    _bootstrap()
    config = EngineConfig.from_yaml(path)
    _log.info("Loaded config '%s' (schema %s)", config.name, config.version)
    return config


def save_config(config: EngineConfig, path: str | Path) -> None:
    """Serialise an engine configuration to YAML (SI values).

    Args:
        config: Configuration to write.
        path: Destination file; overwritten if it exists.
    """
    config.to_yaml(path)
    _log.info("Saved config '%s' -> %s", config.name, path)


def run(config: EngineConfig) -> SimulationResult:
    """Run the transient (blowdown) simulation for one engine.

    Args:
        config: Engine with a defined nozzle (``throat_diameter_m`` and
            ``expansion_ratio`` set).

    Returns:
        Time history, event log (liquid run-out, burnout, ...) and summary
        metrics (total impulse, peak thrust and Pc, mean Isp, ...).

    Raises:
        ConfigError: If the nozzle is not defined.
    """
    from hyprop.simulation import run_simulation

    _bootstrap()
    return run_simulation(config)


def run_batch(
    config: EngineConfig, cases: Iterable[dict[str, float]], progress: bool = True
) -> pd.DataFrame:
    """Run a set of variants of one engine (sequentially).

    Args:
        config: Baseline engine.
        cases: Overrides per case as ``{"dotted.config.path": value}``,
            e.g. from :func:`hyprop.batch.build_grid` or
            :func:`hyprop.batch.build_lhs`.
        progress: Log progress every 10 cases.

    Returns:
        One row per case: the overrides, summary metrics and the
        impulse-weighted thrust, Pc, O/F and Isp. A failed case is logged
        and leaves NaN in its metric columns.
    """
    from hyprop.batch import run_batch as _run_batch

    _bootstrap()
    return _run_batch(config, cases, progress=progress)


def size(
    thrust_n: float, total_impulse_ns: float, apogee_m: float | None = None, **kwargs: Any
) -> SizingResult:
    """Inverse design: mission requirements -> converged engine.

    Args:
        thrust_n: Required impulse-weighted thrust [N].
        total_impulse_ns: Required total impulse [N*s].
        apogee_m: Target apogee [m], optional; sets the nozzle design
            altitude to apogee/3 unless ``design_altitude_m`` is given.
            Without either, the nozzle is adapted at sea level.
        **kwargs: Passed to :func:`hyprop.sizing.size_engine` (``fuel``,
            ``oxidizer``, ``temperature_k``, ``design_altitude_m``,
            ``options``).

    Returns:
        Converged configuration, nozzle design, achieved metrics, the
        number of iterations and guard warnings (flooding, feed coupling,
        separation).
    """
    from hyprop.sizing import size_engine

    _bootstrap()
    return size_engine(thrust_n, total_impulse_ns, apogee_m, **kwargs)
