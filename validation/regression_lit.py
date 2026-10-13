"""Stage 1, item 6: PE/N2O regression law vs published correlations.

HyProp's PE regression (``hdpe`` and ``ldpe``) is the HRAP HDPE preset:
rdot = 0.104 mm/s * G_ox^0.352 (a_SI = 1.04e-4). HRAP does not document
its origin. Verified in this session (local literature folder):

* B. S. Waxman, PhD thesis, Stanford University, Table 1.1 (p. 9, after
  his ref. [12]); units mm/s and kg/m^2 s: HTPB/LOX a = 3.043e-2,
  n = 0.681; HDPE/LOX 2.340e-2, 0.62; paraffin/LOX 11.70e-2, 0.62;
  paraffin/N2O 15.50e-2, 0.50. No N2O/PE entry.
* Chiaverini & Kuo (eds.), Fundamentals of Hybrid Rocket Combustion and
  Propulsion, AIAA Progress Vol. 218 (2007), Ch. 11: PE tests with
  hydrogen peroxide; LDPE "had potential for slightly higher fuel
  regression and combustion efficiency" than HDPE (qualitative).

N2O/HDPE correlations named in earlier notes (Kamps et al., Aerospace 6,
45, 2019; Moon et al., Aerospace 6, 28, 2019; Doran et al., AIAA
2007-5352) could not be opened from this session; they are listed as
TODO without numbers until checked against the papers.

None of these is a PASS/FAIL reference: the law is an input. The rows
show where the preset sits relative to the literature.
"""

from __future__ import annotations

from typing import List

from validation.common import INFO, Row

WAXMAN_T11 = ("B. S. Waxman, PhD thesis, Stanford Univ., Table 1.1 (p. 9, za jego ref. [12]); "
              "ṙ w mm/s, G w kg/m²s")


def all_rows() -> List[Row]:
    from hyprop.data import load_fuel

    pe = load_fuel("ldpe").regression_for("n2o")[0]
    rows: List[Row] = []
    for g in (100.0, 300.0):
        rows.append(Row(f"ṙ preset PE/N2O vs HDPE/LOX (Waxman) przy G = {g:g}", "inny utleniacz – tylko skala",
                        2.340e-2 * g ** 0.62, WAXMAN_T11, pe.a * g ** pe.n * 1e3, unit="mm/s", status=INFO,
                        comment="LOX, nie N2O: porównanie rzędu wielkości, nie walidacja."))
    for ref in ("Kamps et al., Aerospace 6, 45 (2019), doi:10.3390/aerospace6040045",
                "Moon et al., Aerospace 6, 28 (2019), doi:10.3390/aerospace6030028",
                "Doran et al., AIAA 2007-5352"):
        rows.append(Row("a, n dla N2O/HDPE z literatury", ref, None, "", None,
                        comment="Źródło wskazane, ale nieotwarte w tej sesji – brak liczb do porównania."))
    par = load_fuel("paraffin").regression_for("n2o")[0]
    rows.append(Row("a „parafiny” w presecie HRAP (Paraffin.mat)", "HRAP: [0.0304, 0.681]", 3.043e-5,
                    WAXMAN_T11 + ": HTPB/LOX 3.043e-2 mm/s, n 0.681", par.a, tol=0.1,
                    comment="Preset HRAP „Paraffin” = HTPB/LOX z tabeli Waxmana (a i n identyczne). "
                            "Paraffin/N2O w tej tabeli: 15.50e-2 mm/s, n 0.50. Parafina nie jest paliwem projektu."))
    rows.append(Row("Konwencja jednostek a", "HRAP propellant_template.m", 1.04e-4,
                    "HRAP propellant_template.m: ṙ mm/s, G kg/m²s, L m", pe.a, tol=0.01,
                    comment="a_SI = a_HRAP·1e-3 (sprawdzone też w pkt 1 na CSV HRAP)."))
    return rows
