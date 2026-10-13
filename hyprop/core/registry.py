"""Plugin registry (ARCHITECTURE.md, principle 9).

Physical models register themselves with the :func:`register_model`
decorator. The solver and the GUI query the registry instead of importing
concrete classes, so a new model dropped into the proper package becomes
available without touching solver code.

Example
-------
>>> @register_model("regression", "power_law")
... class PowerLawRegression: ...
>>> get_model("regression", "power_law")
<class 'PowerLawRegression'>

:func:`autodiscover` imports all model packages so that decorator side
effects run; call it once at API start-up.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections import defaultdict
from typing import Any

from hyprop.core.exceptions import RegistryError
from hyprop.core.logging import get_logger

_log = get_logger(__name__)

#: Model categories corresponding to plugin-capable packages.
CATEGORIES = ("regression", "geometry", "tank", "injector", "cea")

_REGISTRY: dict[str, dict[str, type]] = defaultdict(dict)


def register_model(category: str, name: str | None = None):
    """Class decorator registering a model under ``(category, name)``.

    Parameters
    ----------
    category:
        One of :data:`CATEGORIES`.
    name:
        Registry key; defaults to the lower-cased class name.
    """
    if category not in CATEGORIES:
        raise RegistryError(f"Unknown category '{category}'. Valid: {CATEGORIES}.")

    def decorator(cls: type) -> type:
        key = (name or cls.__name__).lower()
        existing = _REGISTRY[category].get(key)
        if existing is not None and existing is not cls:
            raise RegistryError(
                f"Duplicate registration '{category}/{key}' "
                f"({existing.__qualname__} vs {cls.__qualname__})."
            )
        _REGISTRY[category][key] = cls
        _log.debug("Registered model %s/%s -> %s", category, key, cls)
        return cls

    return decorator


def get_model(category: str, name: str) -> type[Any]:
    """Return the class registered under ``(category, name)``."""
    try:
        return _REGISTRY[category][name.lower()]
    except KeyError as exc:
        available = ", ".join(sorted(_REGISTRY.get(category, {}))) or "<none>"
        raise RegistryError(
            f"No model '{name}' in category '{category}'. Available: {available}."
        ) from exc


def list_models(category: str | None = None) -> dict[str, list[str]]:
    """Return registered model names, optionally for a single category."""
    if category is not None:
        return {category: sorted(_REGISTRY.get(category, {}))}
    return {cat: sorted(_REGISTRY.get(cat, {})) for cat in CATEGORIES}


def autodiscover() -> None:
    """Import every plugin-capable subpackage of ``hyprop``.

    Importing runs the ``@register_model`` decorators. Missing optional
    packages (not yet implemented stages) are skipped silently.
    """

    for pkg_name in CATEGORIES:
        full_name = f"hyprop.{pkg_name}"
        try:
            package = importlib.import_module(full_name)
        except ModuleNotFoundError:
            continue  # stage not implemented yet
        for module_info in pkgutil.iter_modules(package.__path__):
            importlib.import_module(f"{full_name}.{module_info.name}")
