"""Shared physics equation library.

Dependency rule (ARCHITECTURE.md, principle 2): this package must not
import anything from other ``hyprop`` packages except ``hyprop.core``.
All general equations live here; domain modules (nozzle, tank, injector,
simulation) call into this package and never duplicate formulas.
"""
