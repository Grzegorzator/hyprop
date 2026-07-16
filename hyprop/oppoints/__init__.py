"""Representative Operating Points - the mandatory design-parameter hub."""

from hyprop.oppoints.averaging import (
    WEIGHTINGS,
    averages_all_channels,
    weighted_average,
)
from hyprop.oppoints.design_points import (
    OperatingPoint,
    time_at_impulse_fraction,
    time_share_for_impulse,
)
from hyprop.oppoints.phases import PhaseStats, split_phases
from hyprop.oppoints.report_data import ROPReport, analyze

__all__ = [
    "analyze",
    "ROPReport",
    "OperatingPoint",
    "PhaseStats",
    "weighted_average",
    "averages_all_channels",
    "WEIGHTINGS",
    "split_phases",
    "time_at_impulse_fraction",
    "time_share_for_impulse",
]
