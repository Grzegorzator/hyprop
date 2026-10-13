"""Stage 1, item 6: PE/N2O regression law vs published correlations.

HyProp's PE regression (``hdpe`` and ``ldpe``) is the HRAP HDPE preset:
rdot = 0.104 mm/s * G_ox^0.352 (a_SI = 1.04e-4). HRAP does not document
its origin. Sources read in this session (user's literature folder):

* Kamps, Sakurai, Saito, Nagata, "Comprehensive Data Reduction for N2O/HDPE
  Hybrid Rocket Motor Performance Evaluation", Aerospace 2019, 6, 45,
  doi:10.3390/aerospace6040045, Sec. 3.2.1 / Fig. 9: rdot [m/s] =
  2.52e-5 G_ox^0.76 ("history", R^2 = 0.95) and 4.36e-5 G_ox^0.62
  ("endpoint"); time-averaged G_ox 50-100 kg/m^2 s; Doran et al.
  (AIAA JPC 2007) reported n = 0.331 for 50-300 kg/m^2 s (quoted by
  Kamps); steady c* efficiency 87-94 % (Conclusions).
* Moon, Han, You, Kwon, "Hybrid Rocket Underwater Propulsion: A Preliminary
  Assessment", Aerospace 2019, 6, 28, doi:10.3390/aerospace6030028,
  Eq. (1): time-space averaged r = 0.01 G_o^0.83 for multi-port (5-port)
  HDPE grains with liquid N2O, from the authors' earlier work. The unit of r
  is not legible next to Eq. (1) in the PDF text; mm/s is assumed (m/s
  would give ~0.5 m/s, physically impossible) - flagged.
* B. S. Waxman, PhD thesis, Stanford University, Table 1.1 (p. 9):
  HTPB/LOX a = 3.043e-2 mm/s, n = 0.681 (and other LOX/N2O pairs).

None of these is a PASS/FAIL reference: the law is an input. The rows show
where the preset sits relative to the literature and what that means for
the 0.5 kN example (sizing sensitivity).
"""

from __future__ import annotations

from typing import List

from validation.common import INFO, REPO, Row

KAMPS = ("Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Sec. 3.2.1, Fig. 9 "
         "(ṙ w m/s; G_ox 50–100 kg/m²s)")
MOON = ("Moon et al., Aerospace 2019, 6, 28, doi:10.3390/aerospace6030028, Eq. (1): r = 0.01·G^0.83 "
        "(5-portowe HDPE, N2O; jednostka r nieczytelna – przyjęto mm/s)")
WAXMAN_T11 = ("B. S. Waxman, PhD thesis, Stanford Univ., Table 1.1 (p. 9, za jego ref. [12]); "
              "ṙ w mm/s, G w kg/m²s")
LAWS = {
    "Kamps history (2.52e-5, 0.76)": (2.52e-5, 0.76),
    "Kamps endpoint (4.36e-5, 0.62)": (4.36e-5, 0.62),
}


def _sizing_impact(rows: List[Row], preset) -> None:
    """Run examples/pe_05kN.yaml with the literature laws instead of the preset."""
    import yaml
    import hyprop.api as api
    from hyprop.core.config import EngineConfig
    from hyprop.oppoints import analyze

    base = yaml.safe_load((REPO / "examples" / "pe_05kN.yaml").read_text(encoding="utf-8"))

    def run(a, n):
        cfg = dict(base)
        cfg["fuel"] = dict(base["fuel"], regression=dict(a=a, n=n, m=0.0, flux_basis="oxidizer"))
        res = api.run(EngineConfig.from_dict(cfg))
        iw = analyze(res).point("impulse_weighted")
        return res.summary["total_impulse_ns"], iw["of"], iw["thrust"]

    ref = run(preset.a, preset.n)
    for label, (a, n) in LAWS.items():
        it, of, f = run(a, n)
        rows.append(Row(f"pe_05kN z prawem {label}: It / O/F_iw / F_iw", "examples/pe_05kN.yaml, ta sama geometria",
                        ref[0], f"{KAMPS}; HyProp z presetem HRAP", it, unit="Ns", status=INFO,
                        comment=f"O/F_iw {ref[1]:.2f} → {of:.2f}; F_iw {ref[2]:.0f} → {f:.0f} N. "
                                "Geometria dobrana pod preset; z prawem z literatury silnik jest bogatszy w paliwo."))


def all_rows() -> List[Row]:
    from hyprop.data import load_fuel

    pe = load_fuel("ldpe").regression_for("n2o")[0]
    rows: List[Row] = []
    for g in (50.0, 100.0, 260.0):
        note = ("W zakresie danych Kampsa." if g <= 100 else
                "EKSTRAPOLACJA: G_ox na starcie prusak_v2 ≈ 260 kg/m²s, poza zakresem Kampsa (50–100).")
        for label, (a, n) in LAWS.items():
            rows.append(Row(f"ṙ preset HRAP vs {label} przy G_ox = {g:g}", "PE/N2O, pojedynczy port",
                            a * g ** n * 1e3, KAMPS, pe.a * g ** pe.n * 1e3, unit="mm/s", status=INFO,
                            comment=note))
    for g in (100.0, 300.0):
        rows.append(Row(f"ṙ preset HRAP vs Moon 2019 przy G_o = {g:g}", "PE/N2O, wieloportowe",
                        0.01 * g ** 0.83, MOON, pe.a * g ** pe.n * 1e3, unit="mm/s", status=INFO,
                        comment="Średnia czasowo-przestrzenna, ziarno 5-portowe: tylko rząd wielkości."))
    rows.append(Row("Wykładnik n: preset vs literatura N2O/HDPE", "PE/N2O", 0.331,
                    "Doran et al., AIAA JPC 2007 (n = 0.331, G 50–300 kg/m²s) – cytowane przez " + KAMPS,
                    pe.n, status=INFO,
                    comment="Preset (0.352) bliski Doranowi; Kamps: 0.62 (endpoint) / 0.76 (history). "
                            "Rozrzut n to główna niepewność sizingu – zmierzyć w kilku punktach G_ox."))
    from hyprop.sizing.preliminary import SizingOptions
    eta = SizingOptions().eta_cstar
    rows.append(Row("η_c* domyślne (sizing) w zakresie zmierzonym dla N2O/HDPE", "SizingOptions.eta_cstar",
                    0.94, KAMPS.split(", Sec.")[0] + ", Conclusions: ustalone η* 87–94 %", eta,
                    status="PASS" if 0.87 <= eta <= 0.94 else "FAIL", dev_kind="abs",
                    comment="Kryterium: wartość w przedziale 0.87–0.94 (kolumna Referencja = górna granica). "
                            "Do v0.2 domyślne było 0.95."))
    rows.append(Row("ṙ preset vs HDPE/LOX (Waxman) przy G = 100", "inny utleniacz – tylko skala",
                    2.340e-2 * 100.0 ** 0.62, WAXMAN_T11, pe.a * 100.0 ** pe.n * 1e3, unit="mm/s", status=INFO))
    par = load_fuel("paraffin").regression_for("n2o")[0]
    rows.append(Row("a „parafiny” w presecie HRAP (Paraffin.mat)", "HRAP: [0.0304, 0.681]", 3.043e-5,
                    WAXMAN_T11 + ": HTPB/LOX 3.043e-2 mm/s, n 0.681", par.a, tol=0.1,
                    comment="Preset HRAP „Paraffin” = HTPB/LOX z tabeli Waxmana. Parafina nie jest paliwem projektu."))
    rows.append(Row("Konwencja jednostek a", "HRAP propellant_template.m", 1.04e-4,
                    "HRAP propellant_template.m: ṙ mm/s, G kg/m²s, L m", pe.a, tol=0.01,
                    comment="a_SI = a_HRAP·1e-3 (sprawdzone też w pkt 1 na CSV HRAP)."))
    _sizing_impact(rows, pe)
    return rows
