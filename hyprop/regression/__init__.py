"""Fuel regression models (rdot as a function of port mass flux)."""

from hyprop.regression.base import RegressionModel
from hyprop.regression.power_law import PowerLawRegression

__all__ = ["RegressionModel", "PowerLawRegression"]
