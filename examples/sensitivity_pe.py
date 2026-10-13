"""OAT sensitivity of the sized 0.5 kN PE engine (E9 demo).

Regression coefficients pinned explicitly (database values) so they can
be perturbed via config paths.
"""

import hyprop.api as api
import hyprop.simulation.solver as sm
from hyprop.analysis import oat_sensitivity, regime_flags
from hyprop.batch import apply_overrides
from hyprop.core.config import EngineConfig

sm._TABLE_OF, sm._TABLE_PC = 5, 4

base = api.load_config("examples/pe_05kN_3km_sized.yaml")
base = apply_overrides(base, {"simulation.dt_s": 0.04})
raw = base.model_dump(mode="python")
raw["fuel"]["regression"] = dict(
    model="power_law", a=1.04e-4, n=0.352, m=0.0, flux_basis="oxidizer"
)

base = EngineConfig.from_dict(raw)
assert base.nozzle.throat_diameter_m is not None  # sized config

table = oat_sensitivity(
    base,
    {
        "fuel.regression.a": 1.04e-4,
        "fuel.regression.n": 0.352,
        "injector.discharge_coefficient": 0.60,
        "efficiencies.eta_cstar": 0.90,
        "nozzle.throat_diameter_m": base.nozzle.throat_diameter_m,
    },
    delta=0.05,
)
# NOTE: tank temperature needs an ABSOLUTE perturbation (+-5 K), not
# relative (+-14.7 K reaches the N2O critical point) - handled in the
# uncertainty module via a uniform distribution instead.
print("Relative sensitivities (1% param change -> S% output change):")
print(table.round(2).to_string())


flags = regime_flags(sm.run_simulation(base).history)
print("\nRegime flags:", flags or "none (turbulent, incompressible port)")
