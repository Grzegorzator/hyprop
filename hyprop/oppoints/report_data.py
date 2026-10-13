"""Aggregated ROP analysis consumed by every design module (stage E7).

:func:`analyze` is the single entry point: it takes a
:class:`~hyprop.simulation.SimulationResult` and returns an
:class:`ROPReport` with all representative points, phase statistics,
impulse-share metrics and module recommendations. Design modules
(nozzle sizing E8, thermal, optimization E11, PDF report E10) must pull
their parameters from here, never from raw time steps
(ARCHITECTURE.md, principle 8).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import pandas as pd

from hyprop.core.logging import get_logger
from hyprop.core.state import TimeHistory
from hyprop.oppoints.averaging import averages_all_channels
from hyprop.oppoints.design_points import (
    PERCENTILES_DEFAULT,
    OperatingPoint,
    heat_load_point,
    impulse_weighted_point,
    mass_flow_point,
    median_impulse_point,
    peak_performance_point,
    percentile_points,
    time_share_for_impulse,
)
from hyprop.oppoints.phases import PhaseStats, split_phases

_log = get_logger(__name__)

#: Impulse fractions for the "how much time delivers the work" table.
IMPULSE_FRACTIONS = (0.50, 0.75, 0.90, 0.95, 0.99)

#: Module -> recommended point name (with rationale in ROPReport docs).
RECOMMENDATIONS = {
    "nozzle_design": "impulse_weighted",
    "reported_performance": "impulse_weighted",
    "thermal_analysis": "heat_load",
    "structural_analysis": "peak_performance",
    "material_selection": "peak_performance",
    "injector_and_feed": "mass_flow",
}


@dataclass
class ROPReport:
    """Complete representative-operating-point analysis."""

    points: dict[str, OperatingPoint]
    percentiles: list[OperatingPoint]
    phases: list[PhaseStats]
    #: impulse fraction -> fraction of burn time that delivered it.
    time_shares: dict[float, float]
    #: plain time averages (for the time-vs-impulse-weighted comparison).
    time_average: dict[str, float]
    recommendations: dict[str, str] = field(default_factory=lambda: dict(RECOMMENDATIONS))

    def point(self, name: str) -> OperatingPoint:
        return self.points[name]

    def for_module(self, module: str) -> OperatingPoint:
        """Operating point recommended for a design module."""
        return self.points[self.recommendations[module]]

    def comparison_table(self) -> pd.DataFrame:
        """Points x channels table (plus plain time average) for reports."""
        rows = {name: p.values for name, p in self.points.items()}
        rows["time_average"] = self.time_average
        return pd.DataFrame(rows).T

    def phases_table(self) -> pd.DataFrame:
        records = []
        for phase in self.phases:
            row = dict(
                phase=phase.name,
                t_start_s=phase.t_start_s,
                t_end_s=phase.t_end_s,
                impulse_ns=phase.impulse_ns,
                impulse_share=phase.impulse_share,
                time_share=phase.time_share,
            )
            row.update({f"mean_{k}": v for k, v in phase.means.items()})
            records.append(row)
        return pd.DataFrame.from_records(records)


def analyze(
    result,
    percentiles: Sequence[float] = PERCENTILES_DEFAULT,
) -> ROPReport:
    """Build the full ROP analysis from a SimulationResult."""
    history: TimeHistory = result.history
    lro: float | None = result.event_time("liquid_runout")

    points = {
        p.name: p
        for p in (
            peak_performance_point(history),
            impulse_weighted_point(history),
            heat_load_point(history),
            mass_flow_point(history),
            median_impulse_point(history),
        )
    }
    report = ROPReport(
        points=points,
        percentiles=percentile_points(history, percentiles),
        phases=split_phases(history, lro),
        time_shares={
            fraction: time_share_for_impulse(history, fraction) for fraction in IMPULSE_FRACTIONS
        },
        time_average=averages_all_channels(history, "time"),
    )
    iw = report.point("impulse_weighted")
    ta = report.time_average
    _log.info(
        "ROP: F_iw=%.0f N (time-avg %.0f N), Pc_iw=%.2f bar, 90%% It in %.0f%% of time",
        iw["thrust"],
        ta["thrust"],
        iw["pc"] / 1e5,
        100 * report.time_shares[0.90],
    )
    return report
