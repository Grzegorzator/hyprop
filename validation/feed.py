"""Stage 1, item 5: tank blowdown and injector models vs literature.

Readable literature data available to this project:

* Waxman, Zimmerman, Cantwell, Zilliac, "Mass Flow Rate and Isolation
  Characteristics of Injectors for Use with Self-Pressurizing Oxidizers
  in Hybrid Rockets" (NASA NTRS 20190001326; Stanford / NASA Ames):
  Table 1 injector 3 (straight, D 1.50 mm, L 18.4 mm, rounded inlet);
  N2O test at T1 = 280 K; SPI fit Cd ~ 0.77 for 0.207 < dP < 1.38 MPa;
  effective Cd "approximately 0.6" at dP = 330 psi (2.28 MPa). Only text
  values are used (no plot digitising). P1 is given twice: text
  "704 psig (4.96 MPa)" with supercharge 1.26 MPa, Fig. 11/12 captions
  "704 psia (4.85 MPa)" with 1.17 MPa - each pair is consistent with
  psat(280 K) = 3.7 MPa, so both are evaluated.
* Whitmore & Chandler (2010) and Zimmerman et al. (2013) tank blowdown
  data are not in the literature folder -> TODO.

Plus code-to-code: equilibrium blowdown with ESDU vs CoolProp properties
on the HRAP prusak_v2 case (sensitivity to the property backend).
"""

from __future__ import annotations

import math

from validation.common import INFO, Row, external

WAXMAN = (
    "Waxman, Zimmerman, Cantwell, Zilliac, „Mass Flow Rate and Isolation Characteristics of "
    "Injectors…” (NASA NTRS 20190001326), wtryskiwacz nr 3, N2O, T1 = 280 K: "
    "Cd_eff ≈ 0.6 przy ΔP = 2.28 MPa (tekst)"
)


def injector_rows() -> list[Row]:
    import CoolProp.CoolProp as CP

    from hyprop.injector.hem import HEMInjector
    from hyprop.injector.nhne import NHNEInjector
    from hyprop.injector.spi import SPIInjector
    from hyprop.tank.base import FluidState

    area = math.pi * (1.5e-3 / 2) ** 2
    t1, dp, cd_spi = 280.0, 2.28e6, 0.77
    ps = CP.PropsSI("P", "T", t1, "Q", 0, "NitrousOxide")
    rows: list[Row] = []
    for p1, label in (
        (4.85e6, "P1 = 4.85 MPa (podpisy rys. 11–12)"),
        (4.96e6, "P1 = 4.96 MPa (tekst)"),
    ):
        rho = CP.PropsSI("D", "T", t1, "P", p1, "NitrousOxide")
        h = CP.PropsSI("H", "T", t1, "P", p1, "NitrousOxide")
        s = CP.PropsSI("S", "T", t1, "P", p1, "NitrousOxide")
        fluid = FluidState(p1, t1, rho, ps, "liquid", h, s)
        for cls, name in (
            (SPIInjector, "SPI"),
            (HEMInjector, "HEM"),
            (NHNEInjector, "NHNE (Dyer)"),
        ):
            mdot = cls(cd_spi, 1, area).mdot(fluid, p1 - dp)
            cd_eff = mdot / (area * math.sqrt(2.0 * rho * dp))
            rows.append(
                Row(
                    f"Cd_eff {name}, Cd_SPI = 0.77",
                    f"{label}; p_sat(EOS) = {ps / 1e6:.2f} MPa",
                    0.6,
                    WAXMAN,
                    cd_eff,
                    status=INFO,
                    comment=(
                        "Referencja „approximately 0.6” (przybliżona, dwa warianty P1 w źródle) – "
                        "tylko porównanie, bez PASS/FAIL."
                    )
                    if name == "SPI"
                    else "",
                )
            )
    return rows


def tank_rows() -> list[Row]:
    rows: list[Row] = [
        Row(
            "Blowdown zbiornika vs pomiar",
            "Whitmore & Chandler 2010; Zimmerman et al. 2013",
            None,
            "",
            None,
            comment="Źródeł nie ma w folderze literatury; dane z wykresów nie są używane.",
        ),
    ]
    hrap_dir = external("HYPROP_HRAP_DIR")
    if hrap_dir is None:
        return rows

    import hyprop.api as api
    from hyprop.core.config import EngineConfig
    from validation.common import REPO, load_module

    bench = load_module("b", REPO / "examples" / "benchmark_prusak_v2.py")
    out = {}
    for props in ("esdu", "coolprop"):
        cfg = dict(bench.CFG)
        cfg["tank"] = dict(bench.CFG["tank"], parameters=dict(properties=props))
        res = api.run(EngineConfig.from_dict(cfg))
        out[props] = (
            res.event_time("liquid_runout"),
            res.summary["total_impulse_ns"],
            float(res.history["p_tank"][0]),
        )
    src = "HyProp z właściwościami N2O z CoolProp (EOS Lemmon & Span 2006) – kod-kod"
    for i, (label, unit) in enumerate((("LRO", "s"), ("It", "Ns"), ("p_tank(0)", "Pa"))):
        rows.append(
            Row(
                f"Blowdown ESDU vs CoolProp: {label}",
                "prusak_v2, 293.15 K",
                out["coolprop"][i],
                src,
                out["esdu"][i],
                unit=unit,
                status=INFO,
            )
        )
    return rows


def all_rows() -> list[Row]:
    return injector_rows() + tank_rows()
