# HyProp – raport walidacji

Wygenerowano: 2026-10-13 15:26, commit `7d39940`  
Środowisko: Python 3.11.17 (Linux), numpy 2.4.6, scipy 1.17.1, cantera 3.2.0, CoolProp 8.0.0, rocketcea 1.2.3, pymoo 0.6.2, shapely 2.2.0, pint 0.25.3  
Polecenie: `python -m validation.run_all` (zmienne środowiskowe: patrz `validation/README.md`).

Zasada: wiersz może mieć PASS tylko przy sprawdzalnym źródle referencji. Brak źródła = `TODO: brak referencji`. INFO = wielkość raportowana bez kryterium.

## 0. Zestaw testów (wszystkie opcjonalne backendy zainstalowane)

```
126 passed in 46.47s
```
## 1. Odtworzenie deklaracji z README

Podsumowanie: INFO: 5, PASS: 60

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Średnia odchyłka Pc HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 1.4 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 1.421 pp | +0.02064 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 2 | Średnia odchyłka p_tank HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 0.5 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.4949 pp | -0.0051 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 3 | Średnia odchyłka O/F HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 0.8 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.8356 pp | +0.03559 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 4 | Średnia odchyłka Ciąg F HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 0.6 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.6087 pp | +0.008691 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 5 | LRO HyProp | prusak_v2 | 7.16 s | README.md (v0.2, sekcje Validation/Examples) | 7.16 s | +0 s | ±0.005 s | **PASS** |  |
| 6 | LRO HRAP (z danych HRAP) | prusak_v2 | 6.955 s | README.md (v0.2, sekcje Validation/Examples) | 6.955 s | +0 s | ±0.0005 s | **PASS** | Skok ṁ_ox 0.317→0.114 kg/s w CSV. (v0.1 README podawało błędnie ~7.5 s.) |
| 7 | LRO HyProp vs HRAP | prusak_v2 | 6.955 | HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 7.16 | +2.95 % | — | **INFO** | Odchyłka faktyczna, bez kryterium (do oceny w pkt 5). |
| 8 | Średnia odchyłka F, wylot zamrożony [%] | prusak_v2 (diagnostyka) | — |  | 2.052 | — | — | **INFO** | Ta sama symulacja z v_e zamrożonym zamiast równowagowego (diagnostyka). HRAP nie stosuje η_c* do ciągu, a liczy v_e ze stałym γ; zgodność F jest częściowo przypadkowa (efekty o przeciwnych znakach). |
| 9 | a regresji hdpe [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 0.000104 | HRAP `HDPE.mat` prop_Reg=[0.104, 0.352] (mm/s; propellant_template.m) sha256 efb88e5a7ea1… | 0.000104 | +0.00 % | ±0.01 % | **PASS** |  |
| 10 | n regresji hdpe | N2O, baza HyProp[0] | 0.352 | HRAP `HDPE.mat` prop_Reg=[0.104, 0.352] (mm/s; propellant_template.m) sha256 efb88e5a7ea1… | 0.352 | +0.00 % | ±0.01 % | **PASS** |  |
| 11 | a regresji paraffin [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 3.04e-05 | HRAP `Paraffin.mat` prop_Reg=[0.0304, 0.681] (mm/s; propellant_template.m) sha256 5cd27ae16fe4… | 3.04e-05 | +0.00 % | ±0.01 % | **PASS** |  |
| 12 | n regresji paraffin | N2O, baza HyProp[0] | 0.681 | HRAP `Paraffin.mat` prop_Reg=[0.0304, 0.681] (mm/s; propellant_template.m) sha256 5cd27ae16fe4… | 0.681 | +0.00 % | ±0.01 % | **PASS** |  |
| 13 | a regresji htpb [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 0.000198 | HRAP `HTPB.mat` prop_Reg=[0.198, 0.325] (mm/s; propellant_template.m) sha256 acda3a38a891… | 0.000198 | -0.00 % | ±0.01 % | **PASS** |  |
| 14 | n regresji htpb | N2O, baza HyProp[0] | 0.325 | HRAP `HTPB.mat` prop_Reg=[0.198, 0.325] (mm/s; propellant_template.m) sha256 acda3a38a891… | 0.325 | +0.00 % | ±0.01 % | **PASS** |  |
| 15 | a z CSV HRAP (fit ṙ=aG^n) | prusak_v2 | 0.000104 | HRAP `HDPE.mat` 0.104 mm/s; HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.000104 | -0.01 % | ±0.1 % | **PASS** | n_fit=0.3520. Kolumna CSV „Regression Rate (mm/s)” zawiera faktycznie m/s (potwierdzone przez d(ID)/dt) – stąd deklaracja „a=1.040e-4 SI”. |
| 16 | It | examples/pe_05kN.yaml | 3719.0 Ns | README.md (v0.2, sekcje Validation/Examples) | 3718.6 Ns | -0.3652 Ns | ±0.5 Ns | **PASS** |  |
| 17 | Pc (szczyt) | examples/pe_05kN.yaml | 36.9 bar | README.md (v0.2, sekcje Validation/Examples) | 36.88 bar | -0.02461 bar | ±0.05 bar | **PASS** |  |
| 18 | LRO | examples/pe_05kN.yaml | 7.35 s | README.md (v0.2, sekcje Validation/Examples) | 7.35 s | -1.119e-13 s | ±0.005 s | **PASS** |  |
| 19 | Isp średni | examples/pe_05kN.yaml | 194.0 s | README.md (v0.2, sekcje Validation/Examples) | 194.2 s | +0.1853 s | ±0.5 s | **PASS** |  |
| 20 | Średnia czasowa F vs IW [%] | ROP examples/pe_05kN.yaml | -51 pp | README.md (v0.2, sekcje Validation/Examples) | -51.29 pp | -0.2877 pp | ±1 pp | **PASS** | README podaje liczby całkowite. Tolerancja ±1 pp. |
| 21 | Średnia czasowa Pc vs IW [%] | ROP examples/pe_05kN.yaml | -47 pp | README.md (v0.2, sekcje Validation/Examples) | -47.32 pp | -0.3194 pp | ±1 pp | **PASS** |  |
| 22 | Udział fazy ciekłej w It [%] | ROP examples/pe_05kN.yaml | 92.4 pp | README.md (v0.2, sekcje Validation/Examples) | 92.43 pp | +0.03294 pp | ±0.05 pp | **PASS** |  |
| 23 | Udział fazy ciekłej w czasie [%] | ROP examples/pe_05kN.yaml | 42.8 pp | README.md (v0.2, sekcje Validation/Examples) | 42.77 pp | -0.02611 pp | ±0.05 pp | **PASS** |  |
| 24 | Liczba iteracji | examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera) | 8 | README.md (v0.2, sekcje Validation/Examples) | 8 | +0 | ±0 | **PASS** | Tolerancja sizingu 1 % (v0.1: 3 %); v0.1 padało na błędzie B1. |
| 25 | F_iw | examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera) | 498.0 N | README.md (v0.2, sekcje Validation/Examples) | 498.1 N | +0.05183 N | ±0.5 N | **PASS** |  |
| 26 | It | examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera) | 4023.0 Ns | README.md (v0.2, sekcje Validation/Examples) | 4023.0 Ns | -0.03548 Ns | ±0.5 Ns | **PASS** |  |
| 27 | Dt | examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera) | 12 mm | README.md (v0.2, sekcje Validation/Examples) | 12 mm | +0.0007295 mm | ±0.05 mm | **PASS** |  |
| 28 | eps | examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera) | 5 | README.md (v0.2, sekcje Validation/Examples) | 5 | -0.0004639 | ±0.005 | **PASS** |  |
| 29 | Apogeum (m_dry = 7 kg) | examples/trajectory_pe_3km.py | 3753.0 m | README.md (v0.2, sekcje Validation/Examples) | 3752.8 m | -0.2372 m | ±0.5 m | **PASS** | m_dry, Cd, D to założenia (skrypt); bez referencji lotnej. |
| 30 | ΔHf PE [kJ/mol C2H4] | baza HyProp `ldpe`/`hdpe` | -56.36 | Splitstone & Johnson, J. Res. NBS 78A(5) 611-616 (1974), doi:10.6028/jres.078A.038 | -56.36 | +0.00 % | ±0.01 % | **PASS** | 72 % krystaliczności. NASA CEA thermo.inp '(CH2)x(cr)' ma -51.2 (McBride 1996). |
| 31 | Tc – cantera | PE/N2O O/F 6.5, Pc 35 bar | 3276.2 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 3278.3 | +0.06 % | ±0.5 % | **PASS** |  |
| 32 | c* – cantera | PE/N2O O/F 6.5, Pc 35 bar | 1615.8 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1617.4 | +0.10 % | ±0.5 % | **PASS** |  |
| 33 | γ_s (równowagowe) – cantera | PE/N2O O/F 6.5, Pc 35 bar | 1.167 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1.167 | -0.00 % | ±0.5 % | **PASS** |  |
| 34 | γ zamrożone cp/cv – cantera | PE/N2O O/F 6.5, Pc 35 bar | 1.247 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1.247 | -0.00 % | ±0.5 % | **PASS** |  |
| 35 | Isp, p_e = 1 atm (ε=5.141) – cantera | PE/N2O O/F 6.5, Pc 35 bar | 245.8 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 245.9 | +0.02 % | ±0.5 % | **PASS** |  |
| 36 | Isp próżn.-wylot v_e/g0, ε=5 – cantera | PE/N2O O/F 6.5, Pc 35 bar | 244.8 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 244.9 | +0.03 % | ±0.5 % | **PASS** |  |
| 37 | Tc – rocketcea | PE/N2O O/F 6.5, Pc 35 bar | 3276.2 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 3275.3 | -0.03 % | ±0.5 % | **PASS** |  |
| 38 | c* – rocketcea | PE/N2O O/F 6.5, Pc 35 bar | 1615.8 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1615.5 | -0.02 % | ±0.5 % | **PASS** |  |
| 39 | Isp, p_e = 1 atm (ε=5.141) – rocketcea | PE/N2O O/F 6.5, Pc 35 bar | 245.8 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 245.7 | -0.02 % | ±0.5 % | **PASS** |  |
| 40 | c* ze wzoru idealnego z γ zamrożone vs c* CEA [%] | PE/N2O O/F 6.5, Pc 35 bar | 1615.8 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1580.2 | -2.20 % | — | **INFO** | Wzór idealny z γ zamrożonym zaniża c* (dawne „~2.3 %” ze skryptu 07). |
| 41 | c* ze wzoru idealnego z γ γ_s vs c* CEA [%] | PE/N2O O/F 6.5, Pc 35 bar | 1615.8 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1618.3 | +0.15 % | ±0.5 % | **PASS** | Z γ_s wzór odtwarza c* równowagowe. |
| 42 | Tc – cantera | PE/N2O O/F 6.3, Pc 32 bar | 3246.5 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 3248.6 | +0.06 % | ±0.5 % | **PASS** |  |
| 43 | c* – cantera | PE/N2O O/F 6.3, Pc 32 bar | 1613.0 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1614.3 | +0.08 % | ±0.5 % | **PASS** |  |
| 44 | γ_s (równowagowe) – cantera | PE/N2O O/F 6.3, Pc 32 bar | 1.171 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1.171 | -0.00 % | ±0.5 % | **PASS** |  |
| 45 | γ zamrożone cp/cv – cantera | PE/N2O O/F 6.3, Pc 32 bar | 1.248 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1.248 | -0.00 % | ±0.5 % | **PASS** |  |
| 46 | Isp, p_e = 1 atm (ε=4.792) – cantera | PE/N2O O/F 6.3, Pc 32 bar | 242.7 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 242.8 | +0.02 % | ±0.5 % | **PASS** |  |
| 47 | Isp próżn.-wylot v_e/g0, ε=5 – cantera | PE/N2O O/F 6.3, Pc 32 bar | 244.3 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 244.3 | +0.02 % | ±0.5 % | **PASS** |  |
| 48 | Tc – rocketcea | PE/N2O O/F 6.3, Pc 32 bar | 3246.5 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 3245.5 | -0.03 % | ±0.5 % | **PASS** |  |
| 49 | c* – rocketcea | PE/N2O O/F 6.3, Pc 32 bar | 1613.0 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1612.6 | -0.02 % | ±0.5 % | **PASS** |  |
| 50 | Isp, p_e = 1 atm (ε=4.792) – rocketcea | PE/N2O O/F 6.3, Pc 32 bar | 242.7 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 242.7 | -0.02 % | ±0.5 % | **PASS** |  |
| 51 | c* ze wzoru idealnego z γ zamrożone vs c* CEA [%] | PE/N2O O/F 6.3, Pc 32 bar | 1613.0 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1579.4 | -2.08 % | — | **INFO** | Wzór idealny z γ zamrożonym zaniża c* (dawne „~2.3 %” ze skryptu 07). |
| 52 | c* ze wzoru idealnego z γ γ_s vs c* CEA [%] | PE/N2O O/F 6.3, Pc 32 bar | 1613.0 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1616.0 | +0.19 % | ±0.5 % | **PASS** | Z γ_s wzór odtwarza c* równowagowe. |
| 53 | Tc – cantera | PE/N2O O/F 8.0, Pc 32 bar | 3330.9 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 3332.5 | +0.05 % | ±0.5 % | **PASS** |  |
| 54 | c* – cantera | PE/N2O O/F 8.0, Pc 32 bar | 1605.7 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1608.4 | +0.17 % | ±0.5 % | **PASS** |  |
| 55 | γ_s (równowagowe) – cantera | PE/N2O O/F 8.0, Pc 32 bar | 1.148 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1.148 | -0.01 % | ±0.5 % | **PASS** |  |
| 56 | γ zamrożone cp/cv – cantera | PE/N2O O/F 8.0, Pc 32 bar | 1.243 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1.243 | +0.00 % | ±0.5 % | **PASS** |  |
| 57 | Isp, p_e = 1 atm (ε=5.253) – cantera | PE/N2O O/F 8.0, Pc 32 bar | 246.0 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 246.1 | +0.04 % | ±0.5 % | **PASS** |  |
| 58 | Isp próżn.-wylot v_e/g0, ε=5 – cantera | PE/N2O O/F 8.0, Pc 32 bar | 244.1 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 244.2 | +0.04 % | ±0.5 % | **PASS** |  |
| 59 | Tc – rocketcea | PE/N2O O/F 8.0, Pc 32 bar | 3330.9 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 3330.2 | -0.02 % | ±0.5 % | **PASS** |  |
| 60 | c* – rocketcea | PE/N2O O/F 8.0, Pc 32 bar | 1605.7 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1605.4 | -0.02 % | ±0.5 % | **PASS** |  |
| 61 | Isp, p_e = 1 atm (ε=5.253) – rocketcea | PE/N2O O/F 8.0, Pc 32 bar | 246.0 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 246.0 | -0.02 % | ±0.5 % | **PASS** |  |
| 62 | c* ze wzoru idealnego z γ zamrożone vs c* CEA [%] | PE/N2O O/F 8.0, Pc 32 bar | 1605.7 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1559.8 | -2.86 % | — | **INFO** | Wzór idealny z γ zamrożonym zaniża c* (dawne „~2.3 %” ze skryptu 07). |
| 63 | c* ze wzoru idealnego z γ γ_s vs c* CEA [%] | PE/N2O O/F 8.0, Pc 32 bar | 1605.7 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; Gordon & McBride RP-1311), reagent (CH2)x(cr) z ΔHf HyProp | 1605.3 | -0.03 % | ±0.5 % | **PASS** | Z γ_s wzór odtwarza c* równowagowe. |
| 64 | max \|ESDU/CoolProp−1\| p_sat [%] | 263–303 K, krok 0.5 K | 1.5 pp | README.md (v0.2, sekcje Validation/Examples); CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 (klucz Lemmon-JCED-2006) | 0.1617 pp | -1.338 pp | — | **PASS** | Deklaracja „within 1.5 %”. Kolumna HyProp = max odchyłka; odchyłka = zapas do 1.5 %. |
| 65 | max \|ESDU/CoolProp−1\| ρ_l [%] | 263–303 K, krok 0.5 K | 1.5 pp | README.md (v0.2, sekcje Validation/Examples); CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 (klucz Lemmon-JCED-2006) | 0.191 pp | -1.309 pp | — | **PASS** | Deklaracja „within 1.5 %”. Kolumna HyProp = max odchyłka; odchyłka = zapas do 1.5 %. |

## 2. Ustalenia etapu 1 (pkt 0–1) i ich los

### 2.1 Stan wyjściowy v0.1 (commit `143f8b8`)

* Testy (Python 3.11, wszystkie backendy): 126 passed. 3 skipy z czystej instalacji to 2× `importorskip("CoolProp")` oraz cały moduł `test_cea.py` (Cantera, 8 testów liczonych jako 1 skip), a nie RocketCEA ani pymoo. RocketCEA, NSGA-II i Morris/Sobol nie miały żadnego testu.
* Liczby z README v0.1 odtwarzały się (benchmark HRAP: Pc 1.7 %, p_tank 0.6 %, O/F 1.0 %, F 6.2 %; sizing 0.5 kN; ROP; apogeum 3291 m dla m_dry = 9 kg) z wyjątkami opisanymi niżej.

### 2.2 Błędy znalezione i poprawione (osobne commity `fix(...)`)

| ID | Problem w v0.1 | Poprawka v0.2 | Wpływ na liczby |
|---|---|---|---|
| B1 | Klucz cache tablicy CEA `round(eps, 2)` przy ścisłej kontroli eps → `api.size` (3 km) padało z `ValueError` | klucz na pełnym `float(eps)` + test regresyjny | brak (naprawia awarię) |
| B2 | `simulation.cea_backend` ignorowany, solver zawsze na Canterze | `get_backend(cea_backend)`, backend zapisany w `SimulationResult.thermo_backend` | przy `auto` + RocketCEA: ≤ 0.15 % |
| B3 | `StationState.gamma` = cp/cv (Cantera), ale γ_s (RocketCEA); RocketCEA zwracał też cp równowagowe | `gamma` = zamrożone cp/cv wszędzie, nowe pole `gamma_eq` = γ_s | transient bez zmian (Cantera) |
| B4 | η_c* nie wchodziło do ciągu (∂F/∂η_c* = −0.61) – jak w HRAP (Nickel, równ. 20–24) | `F = η_c*·η_noz·ṁ·c_i` wg Sutton & Biblarz, 9th ed., r. 3.5, równ. 3-40/3-41 | F, Isp −(1−η_c*) ≈ −5 % |
| B5 | Dysza w sizingu: ε ze wzoru gazu idealnego (frozen γ: −3 % vs CEA), Cf bez η i Cd → pętla sizingu stała na −5 % ciągu po B4 | ε z rozprężania CEA (p_e = p_a), Cf dostarczony = λ·η·Cd·Cf_i; tolerancja sizingu 3 % → 1 % | sizing 3 km (jeszcze HDPE): 7 iteracji, F_iw 497 N, It 4040 Ns |
| B6 | Paliwo: domyślna parafina, a ΔHf PE = −41.2 kJ/mol C2H4 to oszacowanie fazy **gazowej** | PE jako paliwo projektu: ΔHf fazy stałej −28.182 kJ/mol CH2 (Splitstone & Johnson, J. Res. NBS 78A, 611, 1974); nowy wpis `ldpe` (granulat MELprop, ρ 920); domyślne paliwo `ldpe` | O/F 6.3, 32 bar: Tc −23 K (3272 → 3249), c* −0.5 %, Isp −0.5 %; z ρ 920: sizing 3 km 8 iteracji, F_iw 498 N, It 4023 Ns |

Drobne: shapely `resolution` → `quad_segs`; `importorskip("openpyxl")`; ścieżka HRAP przez `HYPROP_HRAP_DIR`; przykłady piszą do `outputs/` zamiast nadpisywać śledzone pliki.

### 2.3 Poprawione w dokumentacji

* LRO HRAP: v0.1 README podawało ~7.5 s, a z CSV wynika **6.955 s**.
* γ = 1.245 → 1.247 (frozen).
* Apogeum: skrypt od commitu `d22b828` używa m_dry = 7 kg; README podawało wynik dla 9 kg.
* Liczba testów: README nie podaje już liczby.

### 2.4 Wyjaśnienie różnicy ~2.3 % c* (v0.1, parafina)

Skrypt 07 liczył c* wzorem gazu idealnego z γ = cp/cv mieszaniny **zamrożonej**. CEA/HyProp podaje c* **równowagowe**. Ten sam wzór z γ_s odtwarza c* NASA CEA (dla PE wiersze „c* ze wzoru idealnego z γ_s”). Różnica wynika wyłącznie z definicji γ. Dla PE/N2O wynosi ok. 2.5 %.

### 2.5 Ograniczenia: co te zgodności dowodzą, a co nie

* Benchmark HRAP to porównanie **kod–kod** (ten sam model zbiornika i wtryskiwacza, te same współczynniki). Po B4 i B6 zgodność ciągu (0.6 %) jest częściowo przypadkowa. HRAP nie stosuje η_c* do ciągu, ale liczy v_e ze stałym γ komory, co daje niższe v_e niż rozprężanie równowagowe. Oba efekty mają przeciwne znaki.
* Termochemia PE: referencją jest oficjalny pakiet NASA `cea` (reagent `(CH2)x(cr)`), niezależny od RocketCEA i Cantery, przy tym samym ΔHf. Sprawdza to obliczenia, nie samo ΔHf. To pochodzi z kalorymetrii NBS dla liniowego PE (72 % krystaliczności). Dla LDPE (~40–50 %) ekstrapolacja daje ok. 1 kJ/mol CH2 mniej ujemne (ok. 3 K w Tc). NASA CEA ma w bibliotece −25.6 kJ/mol CH2 (McBride 1996), co daje ok. 7 K niżej.
* N2O: CoolProp (EOS Lemmon & Span 2006).
* Parafina i HTPB zostają w bazie tylko do porównań. Hf parafiny (−703 kJ/mol) to nadal oszacowanie fazy gazowej, a HTPB nie ma Hf.
* Żadnych prób ogniowych: η_c*, Cd wtryskiwacza, a i n są założeniami lub danymi literaturowymi (flagi `verify`).
