"""Engine configuration: the single declarative description of a case.

Design (ARCHITECTURE.md, principle 7):

* One :class:`EngineConfig` object describes a complete computation case.
* Validated with pydantic v2; serialisable to/from YAML and JSON.
* Carries a ``version`` field; :func:`_migrate` upgrades older files.
* All numeric fields are SI. Any quantity may also be given as a string
  with units (``"35 bar"``, ``"25 mm"``) — parsed via Pint at validation.

Field names carry explicit SI unit suffixes (``_pa``, ``_m``, ``_k``...)
so that units are unambiguous at every call site.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hyprop.core.exceptions import ConfigError
from hyprop.core.units import to_si

#: Current schema version of EngineConfig files.
CONFIG_VERSION = "0.1"

#: Physical quantity field. Input may be a float in SI or a unit string
#: ("40 bar"); every such field has a ``mode="before"`` validator that
#: converts to SI, so after validation the attribute is always a float.
QuantityField = float


def _unit_validator(unit: str):
    """Build a pydantic validator converting str/float input to SI float."""

    def _validate(value: Any) -> float | None:
        if value is None:
            return None
        return to_si(value, unit)

    return _validate


class _Model(BaseModel):
    """Base model: forbid unknown keys (typos fail loudly)."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class MissionRequirements(_Model):
    """Top-level mission requirements driving the sizing process."""

    thrust_n: QuantityField = Field(..., description="Required (nominal) thrust [N]")
    total_impulse_ns: QuantityField | None = Field(None, description="Required total impulse [N*s]")
    burn_time_s: QuantityField | None = Field(None, description="Required burn time [s]")
    design_altitude_m: QuantityField = Field(
        0.0,
        description="Nozzle adaptation altitude [m] (NOT the apogee; "
        "for an ascent the optimum is a fraction of the apogee)",
    )
    apogee_m: QuantityField | None = Field(
        None,
        description="Mission apogee target [m] (informational; used "
        "by sizing to pick the adaptation altitude)",
    )
    ambient_pressure_pa: QuantityField | None = Field(
        None,
        description="Ambient pressure at design point [Pa]; if omitted it "
        "will be derived from design_altitude_m (ISA) in the sizing module.",
    )
    min_isp_s: QuantityField | None = Field(
        None, description="Minimum acceptable (delivered) specific impulse [s]"
    )
    safety_factor: float = Field(1.5, ge=1.0, description="Structural safety factor [-]")

    _v_f = field_validator("thrust_n", mode="before")(_unit_validator("N"))
    _v_it = field_validator("total_impulse_ns", mode="before")(_unit_validator("N*s"))
    _v_tb = field_validator("burn_time_s", mode="before")(_unit_validator("s"))
    _v_h = field_validator("design_altitude_m", mode="before")(_unit_validator("m"))
    _v_ap = field_validator("apogee_m", mode="before")(_unit_validator("m"))
    _v_pa = field_validator("ambient_pressure_pa", mode="before")(_unit_validator("Pa"))
    _v_isp = field_validator("min_isp_s", mode="before")(_unit_validator("s"))

    @model_validator(mode="after")
    def _require_impulse_or_time(self) -> MissionRequirements:
        if self.total_impulse_ns is None and self.burn_time_s is None:
            raise ValueError("Provide total_impulse_ns or burn_time_s (or both).")
        return self


class OxidizerSpec(_Model):
    """Oxidizer selection and tank thermodynamic state."""

    name: str = Field(..., description="Database name (n2o, lox, gox, htp) or 'custom'")
    temperature_k: QuantityField = Field(293.15, description="Initial tank (fluid) temperature [K]")
    tank_pressure_pa: QuantityField | None = Field(
        None,
        description="Initial tank pressure [Pa]; for self-pressurising N2O "
        "leave empty (saturation pressure at temperature_k is used).",
    )
    overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Property overrides / definition of a custom oxidizer "
        "(same schema as data/oxidizers YAML).",
    )

    _v_t = field_validator("temperature_k", mode="before")(_unit_validator("K"))
    _v_p = field_validator("tank_pressure_pa", mode="before")(_unit_validator("Pa"))


class RegressionSpec(_Model):
    """Regression-law selection: rdot = a * G^n * L^m  (HRAP Eq. 11).

    Units convention (SI): rdot [m/s], G [kg/(m^2*s)], L [m].
    """

    model: str = Field("power_law", description="Registered regression model name")
    a: float | None = Field(None, gt=0, description="Coefficient a [m/s / (kg/m^2/s)^n / m^m]")
    n: float | None = Field(None, gt=0, description="Flux exponent n [-]")
    m: float = Field(0.0, description="Grain-length exponent m [-]")
    flux_basis: Literal["oxidizer", "total"] = Field(
        "oxidizer",
        description="Mass flux definition used by the law (decision D4): "
        "'oxidizer' = G_ox (classical literature), 'total' = G_ox + G_fuel.",
    )


class FuelSpec(_Model):
    """Fuel selection, with optional overrides of database values."""

    name: str = Field(
        ..., description="Database name (ldpe, hdpe, paraffin, htpb, abs, pmma) or 'custom'"
    )
    density_kg_m3: QuantityField | None = Field(
        None, description="Override of fuel density [kg/m^3]"
    )
    regression: RegressionSpec | None = Field(
        None,
        description="Override of regression law; default comes from database.",
    )
    overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Other property overrides / custom fuel definition "
        "(same schema as data/fuels YAML).",
    )

    _v_rho = field_validator("density_kg_m3", mode="before")(_unit_validator("kg/m^3"))


class GrainSpec(_Model):
    """Fuel grain geometry.

    ``port`` holds geometry-type-specific parameters, validated in detail by
    the selected :class:`GrainGeometry` implementation (stage E3), e.g.
    ``{"initial_diameter_m": 0.025}`` for ``cylindrical``.
    """

    geometry: str = Field(
        "cylindrical",
        description="Registered geometry name (cylindrical, multiport, wagon_wheel, star, custom)",
    )
    length_m: QuantityField = Field(..., description="Grain length [m]")
    outer_diameter_m: QuantityField = Field(..., description="Grain OD [m]")
    port: dict[str, Any] = Field(
        default_factory=dict, description="Geometry-specific port parameters"
    )

    _v_l = field_validator("length_m", mode="before")(_unit_validator("m"))
    _v_d = field_validator("outer_diameter_m", mode="before")(_unit_validator("m"))

    @field_validator("port", mode="before")
    @classmethod
    def _port_units(cls, value: Any) -> Any:
        """Convert unit strings in port parameters by key suffix.

        Keys ending in ``_m`` are lengths, ``_deg`` angles; other values pass
        through. Without this, '28 mm' reached the geometry as a string.
        """
        if not isinstance(value, dict):
            return value
        out = dict(value)
        for key, item in value.items():
            if isinstance(item, str) and key.endswith("_m"):
                out[key] = to_si(item, "m")
            elif isinstance(item, str) and key.endswith("_deg"):
                out[key] = to_si(item, "deg")
        return out

    @model_validator(mode="after")
    def _positive(self) -> GrainSpec:
        if self.length_m <= 0 or self.outer_diameter_m <= 0:
            raise ValueError("Grain dimensions must be positive.")
        return self


class TankSpec(_Model):
    """Oxidizer tank / feed-system model selection."""

    model: str = Field(
        "equilibrium_blowdown",
        description="Registered tank model (equilibrium_blowdown, pressure_fed, constant_mdot)",
    )
    volume_m3: QuantityField | None = Field(None, description="Tank volume [m^3]")
    oxidizer_mass_kg: QuantityField | None = Field(None, description="Initial oxidizer load [kg]")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Model-specific parameters"
    )

    _v_v = field_validator("volume_m3", mode="before")(_unit_validator("m^3"))
    _v_m = field_validator("oxidizer_mass_kg", mode="before")(_unit_validator("kg"))


class InjectorSpec(_Model):
    """Injector model and geometry."""

    model: str = Field("spi", description="Registered injector model (spi, nhne, hem)")
    discharge_coefficient: float = Field(
        0.66, gt=0, le=1.0, description="Discharge coefficient Cd [-]"
    )
    orifice_count: int = Field(1, ge=1, description="Number of orifices [-]")
    orifice_diameter_m: QuantityField | None = Field(
        None, description="Single orifice diameter [m]"
    )

    _v_d = field_validator("orifice_diameter_m", mode="before")(_unit_validator("m"))


class NozzleSpec(_Model):
    """Nozzle geometry; empty fields are computed by nozzle sizing (E8)."""

    throat_diameter_m: QuantityField | None = Field(None, description="Throat diameter [m]")
    expansion_ratio: float | None = Field(
        None, gt=1.0, description="Area expansion ratio eps = Ae/At [-]"
    )
    divergence_half_angle_deg: float = Field(
        15.0, gt=0, lt=45, description="Conical divergence half-angle [deg]"
    )
    efficiency: float = Field(
        1.0,
        gt=0,
        le=1.0,
        description="Additional nozzle efficiency multiplier eta_noz [-] "
        "(divergence loss is computed separately from the half-angle).",
    )
    discharge_coefficient: float = Field(
        1.0,
        gt=0,
        le=1.0,
        description="Throat discharge coefficient Cd_noz [-] (HRAP noz_Cd): "
        "effective throat area = Cd_noz * At.",
    )

    _v_dt = field_validator("throat_diameter_m", mode="before")(_unit_validator("m"))


class EfficiencySpec(_Model):
    """Empirical efficiency factors (to be confirmed by fire tests)."""

    eta_cstar: float = Field(
        0.90,
        gt=0,
        le=1.0,
        description="Combustion efficiency eta_c* [-]; default 0.90 within the "
        "0.87-0.94 measured for N2O/HDPE by Kamps et al., Aerospace 6, 45 (2019)",
    )


class SimulationSettings(_Model):
    """Numerical settings of the transient solver (E6)."""

    dt_s: QuantityField = Field(0.01, description="Time step [s]")
    t_max_s: QuantityField = Field(60.0, description="Simulation time budget [s]")
    pc_solver: Literal["fixed_point", "brent"] = Field(
        "fixed_point", description="Chamber-pressure solver (decision D5)"
    )
    pc_tolerance: float = Field(1e-4, gt=0, description="Relative Pc tolerance [-]")
    max_iterations: int = Field(200, ge=1, description="Iteration budget per step")
    cea_backend: Literal["auto", "rocketcea", "cantera"] = Field(
        "auto", description="Thermochemistry backend ('auto' = first available)"
    )

    _v_dt = field_validator("dt_s", mode="before")(_unit_validator("s"))
    _v_tm = field_validator("t_max_s", mode="before")(_unit_validator("s"))


class EngineConfig(_Model):
    """Complete, versioned description of one computation case."""

    version: str = Field(CONFIG_VERSION, description="Config schema version")
    name: str = Field("unnamed_engine", description="Case identifier")
    mission: MissionRequirements
    oxidizer: OxidizerSpec
    fuel: FuelSpec
    grain: GrainSpec
    tank: TankSpec = Field(default_factory=TankSpec)
    injector: InjectorSpec = Field(default_factory=InjectorSpec)
    nozzle: NozzleSpec = Field(default_factory=NozzleSpec)
    efficiencies: EfficiencySpec = Field(default_factory=EfficiencySpec)
    simulation: SimulationSettings = Field(default_factory=SimulationSettings)

    # ------------------------------------------------------------------ I/O
    @classmethod
    def from_yaml(cls, path: str | Path) -> EngineConfig:
        """Load and validate a configuration from a YAML file."""
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ConfigError(f"{path}: top level must be a mapping.")
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> EngineConfig:
        """Validate a raw dict (applying version migrations first)."""
        try:
            return cls.model_validate(_migrate(dict(raw)))
        except ValueError as exc:
            raise ConfigError(str(exc)) from exc

    def to_yaml(self, path: str | Path) -> None:
        """Serialise to YAML (SI floats, schema version included)."""
        Path(path).write_text(
            yaml.safe_dump(self.model_dump(mode="json"), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )


def _migrate(raw: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a raw config dict from an older schema version.

    Currently only version 0.1 exists; the function is the designated place
    for future migrations (keeps old YAML files loadable).
    """
    version = str(raw.get("version", CONFIG_VERSION))
    if version != CONFIG_VERSION:
        raise ConfigError(f"Unsupported config version '{version}' (supported: {CONFIG_VERSION}).")
    raw["version"] = version
    return raw
