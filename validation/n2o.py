"""Stage 1, item 4: N2O saturation properties, ESDU 91022 vs reference EOS.

Reference: CoolProp's N2O equation of state (Lemmon & Span, J. Chem. Eng.
Data 51 (2006) 785-850). NIST WebBook values, when supplied in
``validation/data/nist_n2o_sat.csv`` (columns T,P,rho_l,rho_v,h_l,h_v,cp_l;
units K, MPa, kg/m3, kJ/kg, J/g/K), are compared as a second reference.
Reported per property: worst deviation in the recommended range
183-297 K and in the near-critical band 297-309 K.
"""

from __future__ import annotations

import csv
from typing import List

import numpy as np

from hyprop.tank.n2o_properties import T_ESDU_WARN
from validation.common import REPO, Row

PROPS = (("psat", "p_sat"), ("rho_liquid", "ρ_l"), ("rho_vapor", "ρ_v"),
         ("h_vap", "h_lv (Watson)"), ("cp_liquid", "cp_l"))
#: Properties judged PASS/FAIL (2 %): they set tank pressure, mass and
#: injector flow directly. h_lv and cp_l enter only the tank cooling rate;
#: their effect is judged on the blowdown result itself (item 5: ESDU vs
#: CoolProp tank on prusak_v2 changes It by 0.04 %), so they are INFO here.
JUDGED = ("psat", "rho_liquid", "rho_vapor")
BANDS = ((183.0, T_ESDU_WARN, 2.0), (T_ESDU_WARN, 309.0, None))
NIST_CSV = REPO / "validation" / "data" / "nist_n2o_sat.csv"


def _worst(fn_a, fn_b, t_lo, t_hi, step=0.25):
    worst = (0.0, t_lo, 0.0, 0.0)
    for t in np.arange(t_lo, t_hi + 1e-9, step):
        a, b = fn_a(t), fn_b(t)
        d = 100.0 * (a / b - 1.0)
        if abs(d) > abs(worst[0]):
            worst = (d, t, b, a)
    return worst


def all_rows() -> List[Row]:
    import CoolProp.CoolProp as CP
    from hyprop.tank.n2o_properties import CoolPropN2O, ESDU91022 as E

    c = CoolPropN2O()
    src = (f"CoolProp {CP.get_global_param_string('version')}, EOS N2O: Lemmon & Span, "
           f"J. Chem. Eng. Data 51 (2006) 785–850")
    rows: List[Row] = []
    for attr, label in PROPS:
        for t_lo, t_hi, tol in BANDS:
            d, t, ref, got = _worst(getattr(E, attr), getattr(c, attr), t_lo, t_hi)
            band = f"{t_lo:g}–{t_hi:g} K; najgorszy przy {t:.2f} K"
            judged = tol is not None and attr in JUDGED
            if tol is None:
                comment = ("Pasmo okołokrytyczne: tylko raportowane; ESDU loguje ostrzeżenie powyżej "
                           f"{T_ESDU_WARN:g} K.")
            elif not judged:
                comment = ("Wpływa tylko na tempo chłodzenia zbiornika; oceniane na wyniku blowdown "
                           "(pkt 5: It −0.04 % przy CoolProp zamiast ESDU).")
            else:
                comment = ""
            rows.append(Row(f"ESDU {label} vs EOS", band, float(ref), src, float(got),
                            tol=tol if judged else None,
                            status="" if judged else "INFO", comment=comment))
    rows.append(Row("Temperatura krytyczna (stała w kodzie)", "T_CRIT", CP.PropsSI("Tcrit", "N2O"), src,
                    309.57, tol=0.05, unit="K"))
    rows.append(Row("Ciśnienie krytyczne (stała w kodzie)", "P_CRIT", CP.PropsSI("pcrit", "N2O") / 1e6, src,
                    7.251, tol=0.2, unit="MPa"))

    if NIST_CSV.exists():
        nist = list(csv.DictReader(open(NIST_CSV, encoding="utf-8")))
        nsrc = "NIST Chemistry WebBook, SRD 69, Thermophysical Properties of Fluid Systems (N2O, saturation)"
        for key, attr, scale, label in (("P", "psat", 1e6, "p_sat"), ("rho_l", "rho_liquid", 1.0, "ρ_l"),
                                        ("rho_v", "rho_vapor", 1.0, "ρ_v"), ("cp_l", "cp_liquid", 1e3, "cp_l")):
            for t_lo, t_hi, tol in BANDS:
                pts = [(float(r["T"]), float(r[key]) * scale) for r in nist
                       if t_lo <= float(r["T"]) <= t_hi and r.get(key)]
                if not pts:
                    continue
                worst = max(((100 * (getattr(E, attr)(t) / v - 1), t, v, getattr(E, attr)(t)) for t, v in pts),
                            key=lambda x: abs(x[0]))
                rows.append(Row(f"ESDU {label} vs NIST", f"{t_lo:g}–{t_hi:g} K; najgorszy przy {worst[1]:g} K",
                                worst[2], nsrc, worst[3], tol=tol, status="INFO" if tol is None else ""))
            # EOS vs NIST: both should be the same Lemmon-Span EOS
            pts = [(float(r["T"]), float(r[key]) * scale) for r in nist if r.get(key) and float(r["T"]) <= 309.0]
            worst = max(((100 * (getattr(c, attr)(t) / v - 1), t, v, getattr(c, attr)(t)) for t, v in pts),
                        key=lambda x: abs(x[0]))
            rows.append(Row(f"CoolProp {label} vs NIST", f"183–309 K; najgorszy przy {worst[1]:g} K",
                            worst[2], nsrc, worst[3], tol=0.1))
    else:
        rows.append(Row("ESDU / CoolProp vs NIST WebBook", "183–309 K", None, "", None,
                        comment="Brak validation/data/nist_n2o_sat.csv (WebBook niedostępny z tej sesji)."))
    return rows
