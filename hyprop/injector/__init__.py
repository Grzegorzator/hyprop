"""Injector models: SPI (default, D3), HEM, NHNE (Dyer)."""

from hyprop.injector.base import InjectorModel
from hyprop.injector.spi import SPIInjector

__all__ = ["InjectorModel", "SPIInjector"]

try:  # HEM/NHNE need CoolProp
    from hyprop.injector.hem import HEMInjector
    from hyprop.injector.nhne import NHNEInjector

    __all__ += ["HEMInjector", "NHNEInjector"]
except Exception:  # pragma: no cover
    pass
