# HyProp – raport walidacji (etap 1)

Wygenerowano: 2026-10-13 20:50, commit `e0c624d`  
Środowisko: Python 3.11.17 (Linux), numpy 2.4.6, scipy 1.17.1, cantera 3.2.0, CoolProp 8.0.0, rocketcea 1.2.3, pymoo 0.6.2, shapely 2.2.0, pint 0.25.3  
Polecenie: `python -m validation.run_all` (zmienne środowiskowe: patrz `validation/README.md`).

Zasada: wiersz może mieć PASS tylko przy sprawdzalnym źródle referencji. Brak źródła = `TODO: brak referencji`. INFO = wielkość raportowana bez kryterium.

**Razem: INFO: 49, PASS: 129, TODO: brak referencji: 2**

## Podsumowanie etapu 1

### Zwalidowane (niezależna referencja, PASS)

* **Termochemia PE/N2O** (pkt 2): siatka O/F 3–10 × Pc 10–50 bar, równowaga i zamrożenie, wobec oficjalnego pakietu NASA `cea` przy tym samym ΔHf. Wielkości: Tc, M, γ_s, γ, c*, Isp i T wylotu.
  * RocketCEA: ≤ 0.28 % w całej siatce.
  * Cantera: ≤ 0.33 % dla C/O < 1 (O/F > ~3.2). Przy O/F 3 brakuje jej węgla stałego, błąd do 1.4 % w Tc i 3.9 % w T wylotu; backend ostrzega.
* **Przepływ w dyszy** (pkt 3): relacje izentropowe, C_F i praca poza punktem projektowym. Przykłady 3-1 do 3-4 i 3-7 z Suttona: 12/12.
* **Własności N2O** (pkt 4): p_sat, ρ_l i ρ_v z ESDU 91022 w granicach 2 % od EOS Lemmon & Span w zakresie 183–297 K. Stałe krytyczne zgodne.
* **Analiza wymiarowa** (pkt 9): 10/10 relacji rdzenia zgodnych z Pintem do 1e-14. Pint występuje tylko na granicy konfiguracji (`to_si`).
* **Niezmienniki** (pkt 7, Hypothesis):
  * bilans masy utleniacza i paliwa;
  * impuls = ∫F dt;
  * port rośnie monotonicznie;
  * Pc mieści się między ciśnieniem otoczenia a ciśnieniem w zbiorniku;
  * wynik nie zależy od jednostek wejścia.
* **Zbieżność** (pkt 8): rząd 1 w dt (jawny Euler, zgodnie z oczekiwaniem). Przy dt = 0.01 s błąd It wynosi 0.015 %, Pc fazy ciekłej 0.009 %, LRO 1 krok. Tolerancja solvera Pc 1e-4 wpływa na It poniżej 0.002 %.

### Częściowo zwalidowane

* **Wtryskiwacz** (pkt 5): jedyny punkt literaturowy możliwy do odczytania ze źródła to Waxman i in. (NTRS 20190001326): Cd_eff ≈ 0.6 przy ΔP = 2.28 MPa i T1 = 280 K.
  * HEM daje 0.57–0.59, NHNE 0.69–0.70.
  * SPI (domyślny, jak w HRAP) z Cd dopasowanym w zakresie jednofazowym daje 0.77. Przeszacowuje więc ṁ w zakresie dwufazowym o ~28 %.
  * prusak_v2 pracuje przy ΔP ≈ 1.7 MPa, blisko przejścia. Cd i model wtryskiwacza wymagają próby na zimno (cold flow).
* **Zbiornik**: tylko porównanie kod–kod (HRAP; ESDU vs CoolProp zmienia It o 0.04 %). Danych pomiarowych blowdown (Whitmore & Chandler, Zimmerman) nie ma w folderze literatury.
* **ESDU h_lv i cp_l**: h_lv (skalowanie Watsona) odbiega o +1.6 do +2.8 % w zakresie 280–305 K, cp_l o 3.3 % przy 198 K i silnie powyżej 297 K. Wpływ na It wynosi 0.04 %. Powyżej 297 K kod loguje ostrzeżenie.
* **Benchmark HRAP**: porównanie kod–kod, zgodność ciągu częściowo przypadkowa (opis w sekcji 2.5).

### Niemożliwe do zwalidowania bez nowych danych

* **Regresja PE/N2O (a, n)**: preset HRAP (0.104 mm/s, n 0.352) o nieudokumentowanym pochodzeniu. Teraz porównany z literaturą (pkt 6):
  * Kamps i in. 2019 (N2O/HDPE, G_ox 50–100 kg/m²s): ṙ = 2.52e-5·G^0.76 (history) lub 4.36e-5·G^0.62 (endpoint), w m/s. Preset jest wolniejszy o 16–37 % w tym zakresie. Przy G_ox ≈ 260 kg/m²s (start prusak_v2, ekstrapolacja) jest wolniejszy 1.9–2.3 raza.
  * Doran 2007 podaje n = 0.331 (za Kampsem), blisko presetu.
  * Wpływ na przykład 0.5 kN: z prawem Kampsa O/F_iw spada z 6.1 do 3.1–3.6 (silnik bogaty w paliwo, blisko obszaru C/O ≈ 1, gdzie trzeba użyć RocketCEA), a It o 2.5–3 %.
  * **Wniosek**: n między 0.33 a 0.76 to największa niepewność sizingu. Bez pomiaru a i n dla Waszego PE w kilku punktach G_ox wynik sizingu jest tylko orientacyjny.
* **η_c***: domyślne 0.95 jest powyżej zakresu zmierzonego przez Kampsa dla N2O/HDPE (87–94 %).
* **Cd wtryskiwacza, gęstość LDPE i jego krystaliczność** (wpływa na ΔHf, ok. 3 K w Tc): wymagają prób lub pomiarów.
* **NIST WebBook**: tabeli nie udało się pobrać. Plik CSV wrzucony do `validation/data/nist_n2o_sat.csv` zostanie użyty automatycznie.

### Błędy znalezione i poprawione w pkt 2–9 (osobne commity `fix(...)`)

* `fix(cea)`: Cantera poza zakresem ważności (C/O ≥ 1), dodane ostrzeżenie i funkcja `carbon_to_oxygen_ratio`.
* `fix(tank)`: w kroku wyczerpania cieczy (LRO) znikała masa utleniacza (do jednego kroku przepływu).
* `fix(config)`: wartości z jednostkami w `grain.port` (np. "28 mm") wywracały geometrię.
* `fix(performance)`: współczynnik dywergencji λ tylko na członie pędowym (Sutton, równ. 3-34).
* N2O: ostrzeżenie dla ESDU powyżej 297 K.
* Obserwacja: preset HRAP „Paraffin” [0.0304, 0.681] to współczynniki HTPB/LOX z tabeli 1.1 u Waxmana.


## 0. Zestaw testów (wszystkie opcjonalne backendy zainstalowane)

```
131 passed in 61.63s (0:01:01)
```
## 1. Odtworzenie deklaracji z README

Podsumowanie: INFO: 5, PASS: 60

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Średnia odchyłka Pc HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 1.4 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 1.421 pp | +0.02064 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 2 | Średnia odchyłka p_tank HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 0.5 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.4949 pp | -0.0051 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 3 | Średnia odchyłka O/F HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 0.8 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.8356 pp | +0.03559 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 4 | Średnia odchyłka Ciąg F HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 0.6 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.5873 pp | -0.01272 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 5 | LRO HyProp | prusak_v2 | 7.16 s | README.md (v0.2, sekcje Validation/Examples) | 7.16 s | +0 s | ±0.005 s | **PASS** |  |
| 6 | LRO HRAP (z danych HRAP) | prusak_v2 | 6.955 s | README.md (v0.2, sekcje Validation/Examples) | 6.955 s | +0 s | ±0.0005 s | **PASS** | Skok ṁ_ox 0.317→0.114 kg/s w CSV. (v0.1 README podawało błędnie ~7.5 s.) |
| 7 | LRO HyProp vs HRAP | prusak_v2 | 6.955 | HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 7.16 | +2.95 % | — | **INFO** | Odchyłka faktyczna, bez kryterium (do oceny w pkt 5). |
| 8 | Średnia odchyłka F, wylot zamrożony [%] | prusak_v2 (diagnostyka) | — |  | 2.084 | — | — | **INFO** | Ta sama symulacja z v_e zamrożonym zamiast równowagowego (diagnostyka). HRAP nie stosuje η_c* do ciągu, a liczy v_e ze stałym γ; zgodność F jest częściowo przypadkowa (efekty o przeciwnych znakach). |
| 9 | a regresji hdpe [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 0.000104 | HRAP `HDPE.mat` prop_Reg=[0.104, 0.352] (mm/s; propellant_template.m) sha256 efb88e5a7ea1… | 0.000104 | +0.00 % | ±0.01 % | **PASS** |  |
| 10 | n regresji hdpe | N2O, baza HyProp[0] | 0.352 | HRAP `HDPE.mat` prop_Reg=[0.104, 0.352] (mm/s; propellant_template.m) sha256 efb88e5a7ea1… | 0.352 | +0.00 % | ±0.01 % | **PASS** |  |
| 11 | a regresji paraffin [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 3.04e-05 | HRAP `Paraffin.mat` prop_Reg=[0.0304, 0.681] (mm/s; propellant_template.m) sha256 5cd27ae16fe4… | 3.04e-05 | +0.00 % | ±0.01 % | **PASS** |  |
| 12 | n regresji paraffin | N2O, baza HyProp[0] | 0.681 | HRAP `Paraffin.mat` prop_Reg=[0.0304, 0.681] (mm/s; propellant_template.m) sha256 5cd27ae16fe4… | 0.681 | +0.00 % | ±0.01 % | **PASS** |  |
| 13 | a regresji htpb [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 0.000198 | HRAP `HTPB.mat` prop_Reg=[0.198, 0.325] (mm/s; propellant_template.m) sha256 acda3a38a891… | 0.000198 | -0.00 % | ±0.01 % | **PASS** |  |
| 14 | n regresji htpb | N2O, baza HyProp[0] | 0.325 | HRAP `HTPB.mat` prop_Reg=[0.198, 0.325] (mm/s; propellant_template.m) sha256 acda3a38a891… | 0.325 | +0.00 % | ±0.01 % | **PASS** |  |
| 15 | a z CSV HRAP (fit ṙ=aG^n) | prusak_v2 | 0.000104 | HRAP `HDPE.mat` 0.104 mm/s; HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.000104 | -0.01 % | ±0.1 % | **PASS** | n_fit=0.3520. Kolumna CSV „Regression Rate (mm/s)” zawiera faktycznie m/s (potwierdzone przez d(ID)/dt) – stąd deklaracja „a=1.040e-4 SI”. |
| 16 | It | examples/pe_05kN.yaml | 3714.0 Ns | README.md (v0.2, sekcje Validation/Examples) | 3714.5 Ns | +0.4791 Ns | ±0.5 Ns | **PASS** |  |
| 17 | Pc (szczyt) | examples/pe_05kN.yaml | 36.9 bar | README.md (v0.2, sekcje Validation/Examples) | 36.88 bar | -0.02461 bar | ±0.05 bar | **PASS** |  |
| 18 | LRO | examples/pe_05kN.yaml | 7.35 s | README.md (v0.2, sekcje Validation/Examples) | 7.35 s | -1.119e-13 s | ±0.005 s | **PASS** |  |
| 19 | Isp średni | examples/pe_05kN.yaml | 194.0 s | README.md (v0.2, sekcje Validation/Examples) | 194.0 s | -0.02938 s | ±0.5 s | **PASS** |  |
| 20 | Średnia czasowa F vs IW [%] | ROP examples/pe_05kN.yaml | -51 pp | README.md (v0.2, sekcje Validation/Examples) | -51.37 pp | -0.3656 pp | ±1 pp | **PASS** | README podaje liczby całkowite. Tolerancja ±1 pp. |
| 21 | Średnia czasowa Pc vs IW [%] | ROP examples/pe_05kN.yaml | -47 pp | README.md (v0.2, sekcje Validation/Examples) | -47.36 pp | -0.3605 pp | ±1 pp | **PASS** |  |
| 22 | Udział fazy ciekłej w It [%] | ROP examples/pe_05kN.yaml | 92.5 pp | README.md (v0.2, sekcje Validation/Examples) | 92.52 pp | +0.01671 pp | ±0.05 pp | **PASS** |  |
| 23 | Udział fazy ciekłej w czasie [%] | ROP examples/pe_05kN.yaml | 42.8 pp | README.md (v0.2, sekcje Validation/Examples) | 42.77 pp | -0.02611 pp | ±0.05 pp | **PASS** |  |
| 24 | Liczba iteracji | examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera) | 8 | README.md (v0.2, sekcje Validation/Examples) | 8 | +0 | ±0 | **PASS** | Tolerancja sizingu 1 % (v0.1: 3 %); v0.1 padało na błędzie B1. |
| 25 | F_iw | examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera) | 498.0 N | README.md (v0.2, sekcje Validation/Examples) | 497.8 N | -0.1643 N | ±0.5 N | **PASS** |  |
| 26 | It | examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera) | 4026.0 Ns | README.md (v0.2, sekcje Validation/Examples) | 4025.8 Ns | -0.2229 Ns | ±0.5 Ns | **PASS** |  |
| 27 | Dt | examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera) | 12 mm | README.md (v0.2, sekcje Validation/Examples) | 12 mm | +0.0003731 mm | ±0.05 mm | **PASS** |  |
| 28 | eps | examples/size_pe_3km.py (api.size LDPE 0.5 kN / 4000 Ns / 3 km, Cantera) | 5 | README.md (v0.2, sekcje Validation/Examples) | 5.002 | +0.001587 | ±0.005 | **PASS** |  |
| 29 | Apogeum (m_dry = 7 kg) | examples/trajectory_pe_3km.py | 3755.0 m | README.md (v0.2, sekcje Validation/Examples) | 3754.7 m | -0.3035 m | ±0.5 m | **PASS** | m_dry, Cd, D to założenia (skrypt); bez referencji lotnej. |
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

## 2. Termochemia PE/N2O – siatka vs NASA CEA

Podsumowanie: INFO: 12, PASS: 33

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | max odchyłka M komory – cantera (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 7, 50 bar | 25.77 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 25.77 | +0.02 % | ±0.5 % | **PASS** |  |
| 2 | max odchyłka M komory – cantera (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 20 bar | 19.11 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 19.33 | +1.15 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 3 | max odchyłka Tc – cantera (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 6.5, 35 bar | 3276.2 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 3278.3 | +0.06 % | ±0.5 % | **PASS** |  |
| 4 | max odchyłka Tc – cantera (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 1918.8 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1891.3 | -1.43 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 5 | max odchyłka T wylotu (ε=5) – cantera (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 7, 10 bar | 1965.4 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1964.0 | -0.07 % | ±0.5 % | **PASS** |  |
| 6 | max odchyłka T wylotu (ε=5) – cantera (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 973.9 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 935.5 | -3.94 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 7 | max odchyłka c* – cantera (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 9, 10 bar | 1570.9 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1574.3 | +0.21 % | ±0.5 % | **PASS** |  |
| 8 | max odchyłka c* – cantera (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 1367.5 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1359.0 | -0.62 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 9 | max odchyłka γ zamrożone – cantera (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 4, 10 bar | 1.279 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1.279 | -0.01 % | ±0.5 % | **PASS** |  |
| 10 | max odchyłka γ zamrożone – cantera (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 35 bar | 1.306 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1.302 | -0.30 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 11 | max odchyłka γ_s – cantera (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 5, 20 bar | 1.214 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1.214 | +0.03 % | ±0.5 % | **PASS** |  |
| 12 | max odchyłka γ_s – cantera (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 1.275 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1.29 | +1.21 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 13 | max odchyłka Isp optymalny (p_e = 1 atm) – cantera (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 7, 10 bar | 207.0 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 207.2 | +0.07 % | ±0.5 % | **PASS** |  |
| 14 | max odchyłka Isp optymalny (p_e = 1 atm) – cantera (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 175.2 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 174.3 | -0.53 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 15 | max odchyłka Isp próżniowy (ε=5) – cantera (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 8, 10 bar | 269.8 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 269.9 | +0.04 % | ±0.5 % | **PASS** |  |
| 16 | max odchyłka Isp próżniowy (ε=5) – cantera (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 225.7 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 224.6 | -0.49 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 17 | max odchyłka M komory – rocketcea (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 10, 10 bar | 27.06 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 27.06 | +0.01 % | ±0.5 % | **PASS** |  |
| 18 | max odchyłka M komory – rocketcea (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 19.09 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 19.09 | -0.00 % | ±0.5 % | **PASS** |  |
| 19 | max odchyłka Tc – rocketcea (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 4, 50 bar | 2532.1 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 2530.7 | -0.06 % | ±0.5 % | **PASS** |  |
| 20 | max odchyłka Tc – rocketcea (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 1918.8 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1917.5 | -0.07 % | ±0.5 % | **PASS** |  |
| 21 | max odchyłka T wylotu (ε=5) – rocketcea (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 4, 10 bar | 1121.3 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1120.5 | -0.07 % | ±0.5 % | **PASS** |  |
| 22 | max odchyłka T wylotu (ε=5) – rocketcea (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 973.9 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 973.7 | -0.02 % | ±0.5 % | **PASS** |  |
| 23 | max odchyłka c* – rocketcea (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 4, 50 bar | 1498.1 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1497.6 | -0.03 % | ±0.5 % | **PASS** |  |
| 24 | max odchyłka c* – rocketcea (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 1367.5 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1367.0 | -0.04 % | ±0.5 % | **PASS** |  |
| 25 | max odchyłka γ zamrożone – rocketcea (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 10, 10 bar | 1.247 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1.247 | -0.02 % | ±0.5 % | **PASS** |  |
| 26 | max odchyłka γ zamrożone – rocketcea (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 50 bar | 1.305 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1.305 | -0.02 % | ±0.5 % | **PASS** |  |
| 27 | max odchyłka γ_s – rocketcea (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 5, 10 bar | 1.204 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1.204 | +0.01 % | ±0.5 % | **PASS** |  |
| 28 | max odchyłka γ_s – rocketcea (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 1.275 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1.275 | +0.01 % | ±0.5 % | **PASS** |  |
| 29 | max odchyłka Isp optymalny (p_e = 1 atm) – rocketcea (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 4, 50 bar | 231.4 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 231.3 | -0.03 % | ±0.5 % | **PASS** |  |
| 30 | max odchyłka Isp optymalny (p_e = 1 atm) – rocketcea (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 175.2 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 175.2 | -0.04 % | ±0.5 % | **PASS** |  |
| 31 | max odchyłka Isp próżniowy (ε=5) – rocketcea (równowaga) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 4, 35 bar | 246.4 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 246.4 | -0.03 % | ±0.5 % | **PASS** |  |
| 32 | max odchyłka Isp próżniowy (ε=5) – rocketcea (równowaga) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 225.7 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 225.6 | -0.03 % | ±0.5 % | **PASS** |  |
| 33 | max odchyłka T wylotu (ε=5) – cantera (zamrożony od komory) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 6.5, 35 bar | 1566.1 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1567.8 | +0.11 % | ±0.5 % | **PASS** |  |
| 34 | max odchyłka T wylotu (ε=5) – cantera (zamrożony od komory) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 754.1 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 741.4 | -1.69 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 35 | max odchyłka Isp optymalny (p_e = 1 atm) – cantera (zamrożony od komory) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 6.5, 50 bar | 246.7 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 246.8 | +0.03 % | ±0.5 % | **PASS** |  |
| 36 | max odchyłka Isp optymalny (p_e = 1 atm) – cantera (zamrożony od komory) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 174.2 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 172.9 | -0.78 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 37 | max odchyłka Isp próżniowy (ε=5) – cantera (zamrożony od komory) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 9, 10 bar | 251.5 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 252.3 | +0.33 % | ±0.5 % | **PASS** |  |
| 38 | max odchyłka Isp próżniowy (ε=5) – cantera (zamrożony od komory) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 222.1 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 220.5 | -0.76 % | — | **INFO** | Poza zakresem ważności Cantery: gri30 nie ma C(gr); NASA CEA daje ~1 % mol węgla stałego przy O/F 3. Backend ostrzega przy C/O ≥ 1. |
| 39 | max odchyłka T wylotu (ε=5) – rocketcea (zamrożony od komory) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 4, 50 bar | 1084.9 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 1084.2 | -0.07 % | ±0.5 % | **PASS** |  |
| 40 | max odchyłka T wylotu (ε=5) – rocketcea (zamrożony od komory) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 10 bar | 754.1 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 753.6 | -0.08 % | ±0.5 % | **PASS** |  |
| 41 | max odchyłka Isp optymalny (p_e = 1 atm) – rocketcea (zamrożony od komory) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 4, 50 bar | 230.3 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 230.3 | -0.03 % | ±0.5 % | **PASS** |  |
| 42 | max odchyłka Isp optymalny (p_e = 1 atm) – rocketcea (zamrożony od komory) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 35 bar | 202.5 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 202.4 | -0.03 % | ±0.5 % | **PASS** |  |
| 43 | max odchyłka Isp próżniowy (ε=5) – rocketcea (zamrożony od komory) | C/O < 1; siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 9, 10 bar | 251.5 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 252.2 | +0.28 % | ±0.5 % | **PASS** |  |
| 44 | max odchyłka Isp próżniowy (ε=5) – rocketcea (zamrożony od komory) | C/O ≥ 1 (sadza); siatka O/F 3–10 × Pc 10–50 bar; najgorszy punkt O/F 3, 50 bar | 222.5 | NASA CEA, pakiet `cea` 3.3.4 (NASA Glenn; RP-1311), (CH2)x(cr) z ΔHf HyProp; pełna siatka: `docs/validation_data/thermo_grid_pe_n2o.csv` | 222.5 | +0.01 % | ±0.5 % | **PASS** |  |
| 45 | Liczba punktów siatki | PE/N2O | — |  | 36 | — | — | **INFO** | 36 punktów × 2 modele chemii × 2 backendy. |

## 3. Przepływ w dyszy – przykłady Suttona

Podsumowanie: PASS: 12

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | p0 dla M_e = 2.52 | k=1.3, p_e = 0.1013 MPa | 1.84 MPa | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-1 | 1.84 MPa | +0.02 % | ±0.3 % | **PASS** |  |
| 2 | A_e/A_t dla M_e = 2.52 | k=1.3 | 3.02 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-1 | 3.019 | -0.02 % | ±0.3 % | **PASS** |  |
| 3 | v_e (rozprężanie optymalne) | k=1.3, R=345.7, T1=2222 K, p1/p2=2.068/0.1013 | 1827.0 m/s | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-2 | 1827.1 m/s | +0.01 % | ±0.05 % | **PASS** |  |
| 4 | A_e/A_t optymalne | k=1.2, R=360, T1=2800 K, p1=2.039 MPa, p2=2.549 kPa, F=5000 N | 59.88 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-3 (At/A2 = 1.67e-2) | 59.97 | +0.15 % | ±0.6 % | **PASS** | Sutton zaokrągla At/A2 do 3 cyfr (1.67e-2); stąd tolerancja 0.6 %. |
| 5 | T gardzieli | k=1.2, R=360, T1=2800 K, p1=2.039 MPa, p2=2.549 kPa, F=5000 N | 2545.0 K | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-3 | 2545.5 K | +0.02 % | ±0.05 % | **PASS** |  |
| 6 | v_e | k=1.2, R=360, T1=2800 K, p1=2.039 MPa, p2=2.549 kPa, F=5000 N | 2851.0 m/s | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-3 | 2850.6 m/s | -0.01 % | ±0.05 % | **PASS** |  |
| 7 | A_t | k=1.2, R=360, T1=2800 K, p1=2.039 MPa, p2=2.549 kPa, F=5000 N | 13.32 cm² | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-3 | 13.32 cm² | -0.02 % | ±0.1 % | **PASS** |  |
| 8 | p_e/p_1 dla ε = 6 | k=1.3 | 0.0198 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-4 (Eq. 3-25) | 0.0198 | +0.01 % | ±0.3 % | **PASS** |  |
| 9 | C_F, poziom morza (praca poza p. projektowym) | k=1.3, p1=20 atm, ε=6 | 1.33 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-4 (odczyt z Fig. 3-7) | 1.335 | +0.35 % | ±2 % | **PASS** | Wartość referencyjna odczytana z wykresu – tolerancja 2 %. |
| 10 | C_F, 10 km (p3 = 0.26151 atm) | k=1.3, p1=20 atm, ε=6 | 1.56 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-4 (odczyt z Fig. 3-7) | 1.556 | -0.24 % | ±2 % | **PASS** | Wartość referencyjna odczytana z wykresu – tolerancja 2 %. |
| 11 | C_F próżniowy | k=1.3, p1=20 atm, ε=6 | 1.63 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-4 (Fig. 3-7) | 1.635 | +0.29 % | ±2 % | **PASS** |  |
| 12 | (C_F)i optymalne | k=1.23, p1/p2 = 20.4 | 1.405 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), Ex. 3-7 (Eq. 3-30) | 1.405 | -0.01 % | ±0.05 % | **PASS** |  |

## 4. Własności N2O – ESDU 91022 vs EOS (CoolProp/NIST)

Podsumowanie: INFO: 7, PASS: 5, TODO: brak referencji: 1

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ESDU p_sat vs EOS | 183–297 K; najgorszy przy 212.25 K | 4.133e+05 | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 4.15e+05 | +0.40 % | ±2 % | **PASS** |  |
| 2 | ESDU p_sat vs EOS | 297–309 K; najgorszy przy 297.00 K | 5.509e+06 | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 5.517e+06 | +0.15 % | — | **INFO** | Pasmo okołokrytyczne: tylko raportowane; ESDU loguje ostrzeżenie powyżej 297 K. |
| 3 | ESDU ρ_l vs EOS | 183–297 K; najgorszy przy 183.00 K | 1235.4 | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 1221.0 | -1.17 % | ±2 % | **PASS** |  |
| 4 | ESDU ρ_l vs EOS | 297–309 K; najgorszy przy 309.00 K | 548.6 | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 551.8 | +0.59 % | — | **INFO** | Pasmo okołokrytyczne: tylko raportowane; ESDU loguje ostrzeżenie powyżej 297 K. |
| 5 | ESDU ρ_v vs EOS | 183–297 K; najgorszy przy 220.25 K | 15.24 | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 15.36 | +0.78 % | ±2 % | **PASS** |  |
| 6 | ESDU ρ_v vs EOS | 297–309 K; najgorszy przy 308.00 K | 315.8 | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 325.4 | +3.04 % | — | **INFO** | Pasmo okołokrytyczne: tylko raportowane; ESDU loguje ostrzeżenie powyżej 297 K. |
| 7 | ESDU h_lv (Watson) vs EOS | 183–297 K; najgorszy przy 297.00 K | 1.532e+05 | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 1.573e+05 | +2.68 % | — | **INFO** | Wpływa tylko na tempo chłodzenia zbiornika; oceniane na wyniku blowdown (pkt 5: It −0.04 % przy CoolProp zamiast ESDU). |
| 8 | ESDU h_lv (Watson) vs EOS | 297–309 K; najgorszy przy 309.00 K | 4.646e+04 | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 4.854e+04 | +4.48 % | — | **INFO** | Pasmo okołokrytyczne: tylko raportowane; ESDU loguje ostrzeżenie powyżej 297 K. |
| 9 | ESDU cp_l vs EOS | 183–297 K; najgorszy przy 198.00 K | 1733.7 | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 1790.5 | +3.28 % | — | **INFO** | Wpływa tylko na tempo chłodzenia zbiornika; oceniane na wyniku blowdown (pkt 5: It −0.04 % przy CoolProp zamiast ESDU). |
| 10 | ESDU cp_l vs EOS | 297–309 K; najgorszy przy 309.00 K | 6.275e+04 | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 3.432e+04 | -45.30 % | — | **INFO** | Pasmo okołokrytyczne: tylko raportowane; ESDU loguje ostrzeżenie powyżej 297 K. |
| 11 | Temperatura krytyczna (stała w kodzie) | T_CRIT | 309.5 K | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 309.6 K | +0.02 % | ±0.05 % | **PASS** |  |
| 12 | Ciśnienie krytyczne (stała w kodzie) | P_CRIT | 7.245 MPa | CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 | 7.251 MPa | +0.09 % | ±0.2 % | **PASS** |  |
| 13 | ESDU / CoolProp vs NIST WebBook | 183–309 K | — |  | — | — | — | **TODO: brak referencji** | Brak validation/data/nist_n2o_sat.csv (WebBook niedostępny z tej sesji). |

## 5. Zbiornik i wtryskiwacz – literatura

Podsumowanie: INFO: 9, TODO: brak referencji: 1

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Cd_eff SPI, Cd_SPI = 0.77 | P1 = 4.85 MPa (podpisy rys. 11–12); p_sat(EOS) = 3.71 MPa | 0.6 | Waxman, Zimmerman, Cantwell, Zilliac, „Mass Flow Rate and Isolation Characteristics of Injectors…” (NASA NTRS 20190001326), wtryskiwacz nr 3, N2O, T1 = 280 K: Cd_eff ≈ 0.6 przy ΔP = 2.28 MPa (tekst) | 0.77 | +28.33 % | — | **INFO** | Referencja „approximately 0.6” (przybliżona, dwa warianty P1 w źródle) – tylko porównanie, bez PASS/FAIL. |
| 2 | Cd_eff HEM, Cd_SPI = 0.77 | P1 = 4.85 MPa (podpisy rys. 11–12); p_sat(EOS) = 3.71 MPa | 0.6 | Waxman, Zimmerman, Cantwell, Zilliac, „Mass Flow Rate and Isolation Characteristics of Injectors…” (NASA NTRS 20190001326), wtryskiwacz nr 3, N2O, T1 = 280 K: Cd_eff ≈ 0.6 przy ΔP = 2.28 MPa (tekst) | 0.5654 | -5.77 % | — | **INFO** |  |
| 3 | Cd_eff NHNE (Dyer), Cd_SPI = 0.77 | P1 = 4.85 MPa (podpisy rys. 11–12); p_sat(EOS) = 3.71 MPa | 0.6 | Waxman, Zimmerman, Cantwell, Zilliac, „Mass Flow Rate and Isolation Characteristics of Injectors…” (NASA NTRS 20190001326), wtryskiwacz nr 3, N2O, T1 = 280 K: Cd_eff ≈ 0.6 przy ΔP = 2.28 MPa (tekst) | 0.6853 | +14.22 % | — | **INFO** |  |
| 4 | Cd_eff SPI, Cd_SPI = 0.77 | P1 = 4.96 MPa (tekst); p_sat(EOS) = 3.71 MPa | 0.6 | Waxman, Zimmerman, Cantwell, Zilliac, „Mass Flow Rate and Isolation Characteristics of Injectors…” (NASA NTRS 20190001326), wtryskiwacz nr 3, N2O, T1 = 280 K: Cd_eff ≈ 0.6 przy ΔP = 2.28 MPa (tekst) | 0.77 | +28.33 % | — | **INFO** | Referencja „approximately 0.6” (przybliżona, dwa warianty P1 w źródle) – tylko porównanie, bez PASS/FAIL. |
| 5 | Cd_eff HEM, Cd_SPI = 0.77 | P1 = 4.96 MPa (tekst); p_sat(EOS) = 3.71 MPa | 0.6 | Waxman, Zimmerman, Cantwell, Zilliac, „Mass Flow Rate and Isolation Characteristics of Injectors…” (NASA NTRS 20190001326), wtryskiwacz nr 3, N2O, T1 = 280 K: Cd_eff ≈ 0.6 przy ΔP = 2.28 MPa (tekst) | 0.591 | -1.50 % | — | **INFO** |  |
| 6 | Cd_eff NHNE (Dyer), Cd_SPI = 0.77 | P1 = 4.96 MPa (tekst); p_sat(EOS) = 3.71 MPa | 0.6 | Waxman, Zimmerman, Cantwell, Zilliac, „Mass Flow Rate and Isolation Characteristics of Injectors…” (NASA NTRS 20190001326), wtryskiwacz nr 3, N2O, T1 = 280 K: Cd_eff ≈ 0.6 przy ΔP = 2.28 MPa (tekst) | 0.6981 | +16.35 % | — | **INFO** |  |
| 7 | Blowdown zbiornika vs pomiar | Whitmore & Chandler 2010; Zimmerman et al. 2013 | — |  | — | — | — | **TODO: brak referencji** | Źródeł nie ma w folderze literatury; dane z wykresów nie są używane. |
| 8 | Blowdown ESDU vs CoolProp: LRO | prusak_v2, 293.15 K | 7.16 s | HyProp z właściwościami N2O z CoolProp (EOS Lemmon & Span 2006) – kod-kod | 7.16 s | +0.00 % | — | **INFO** |  |
| 9 | Blowdown ESDU vs CoolProp: It | prusak_v2, 293.15 K | 7073.8 Ns | HyProp z właściwościami N2O z CoolProp (EOS Lemmon & Span 2006) – kod-kod | 7076.8 Ns | +0.04 % | — | **INFO** |  |
| 10 | Blowdown ESDU vs CoolProp: p_tank(0) | prusak_v2, 293.15 K | 5.053e+06 Pa | HyProp z właściwościami N2O z CoolProp (EOS Lemmon & Span 2006) – kod-kod | 5.06e+06 Pa | +0.15 % | — | **INFO** |  |

## 6. Regresja paliwa – literatura

Podsumowanie: INFO: 13, PASS: 2

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ṙ preset HRAP vs Kamps history (2.52e-5, 0.76) przy G_ox = 50 | PE/N2O, pojedynczy port | 0.4927 mm/s | Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Sec. 3.2.1, Fig. 9 (ṙ w m/s; G_ox 50–100 kg/m²s) | 0.4122 mm/s | -16.35 % | — | **INFO** | W zakresie danych Kampsa. |
| 2 | ṙ preset HRAP vs Kamps endpoint (4.36e-5, 0.62) przy G_ox = 50 | PE/N2O, pojedynczy port | 0.493 mm/s | Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Sec. 3.2.1, Fig. 9 (ṙ w m/s; G_ox 50–100 kg/m²s) | 0.4122 mm/s | -16.40 % | — | **INFO** | W zakresie danych Kampsa. |
| 3 | ṙ preset HRAP vs Kamps history (2.52e-5, 0.76) przy G_ox = 100 | PE/N2O, pojedynczy port | 0.8345 mm/s | Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Sec. 3.2.1, Fig. 9 (ṙ w m/s; G_ox 50–100 kg/m²s) | 0.5261 mm/s | -36.96 % | — | **INFO** | W zakresie danych Kampsa. |
| 4 | ṙ preset HRAP vs Kamps endpoint (4.36e-5, 0.62) przy G_ox = 100 | PE/N2O, pojedynczy port | 0.7577 mm/s | Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Sec. 3.2.1, Fig. 9 (ṙ w m/s; G_ox 50–100 kg/m²s) | 0.5261 mm/s | -30.57 % | — | **INFO** | W zakresie danych Kampsa. |
| 5 | ṙ preset HRAP vs Kamps history (2.52e-5, 0.76) przy G_ox = 260 | PE/N2O, pojedynczy port | 1.725 mm/s | Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Sec. 3.2.1, Fig. 9 (ṙ w m/s; G_ox 50–100 kg/m²s) | 0.7364 mm/s | -57.31 % | — | **INFO** | EKSTRAPOLACJA: G_ox na starcie prusak_v2 ≈ 260 kg/m²s, poza zakresem Kampsa (50–100). |
| 6 | ṙ preset HRAP vs Kamps endpoint (4.36e-5, 0.62) przy G_ox = 260 | PE/N2O, pojedynczy port | 1.37 mm/s | Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Sec. 3.2.1, Fig. 9 (ṙ w m/s; G_ox 50–100 kg/m²s) | 0.7364 mm/s | -46.26 % | — | **INFO** | EKSTRAPOLACJA: G_ox na starcie prusak_v2 ≈ 260 kg/m²s, poza zakresem Kampsa (50–100). |
| 7 | ṙ preset HRAP vs Moon 2019 przy G_o = 100 | PE/N2O, wieloportowe | 0.4571 mm/s | Moon et al., Aerospace 2019, 6, 28, doi:10.3390/aerospace6030028, Eq. (1): r = 0.01·G^0.83 (5-portowe HDPE, N2O; jednostka r nieczytelna – przyjęto mm/s) | 0.5261 mm/s | +15.09 % | — | **INFO** | Średnia czasowo-przestrzenna, ziarno 5-portowe: tylko rząd wielkości. |
| 8 | ṙ preset HRAP vs Moon 2019 przy G_o = 300 | PE/N2O, wieloportowe | 1.138 mm/s | Moon et al., Aerospace 2019, 6, 28, doi:10.3390/aerospace6030028, Eq. (1): r = 0.01·G^0.83 (5-portowe HDPE, N2O; jednostka r nieczytelna – przyjęto mm/s) | 0.7744 mm/s | -31.93 % | — | **INFO** | Średnia czasowo-przestrzenna, ziarno 5-portowe: tylko rząd wielkości. |
| 9 | Wykładnik n: preset vs literatura N2O/HDPE | PE/N2O | 0.331 | Doran et al., AIAA JPC 2007 (n = 0.331, G 50–300 kg/m²s) – cytowane przez Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Sec. 3.2.1, Fig. 9 (ṙ w m/s; G_ox 50–100 kg/m²s) | 0.352 | +6.34 % | — | **INFO** | Preset (0.352) bliski Doranowi; Kamps: 0.62 (endpoint) / 0.76 (history). Rozrzut n to główna niepewność sizingu – zmierzyć w kilku punktach G_ox. |
| 10 | η_c* domyślne vs zmierzone dla N2O/HDPE | SizingOptions.eta_cstar = 0.95 | 0.94 | Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Conclusions: ustalone η* 87–94 % | 0.95 | +1.06 % | — | **INFO** | Domyślne 0.95 jest powyżej górnej granicy zmierzonej przez Kampsa (87–94 %). |
| 11 | ṙ preset vs HDPE/LOX (Waxman) przy G = 100 | inny utleniacz – tylko skala | 0.4066 mm/s | B. S. Waxman, PhD thesis, Stanford Univ., Table 1.1 (p. 9, za jego ref. [12]); ṙ w mm/s, G w kg/m²s | 0.5261 mm/s | +29.37 % | — | **INFO** |  |
| 12 | a „parafiny” w presecie HRAP (Paraffin.mat) | HRAP: [0.0304, 0.681] | 3.043e-05 | B. S. Waxman, PhD thesis, Stanford Univ., Table 1.1 (p. 9, za jego ref. [12]); ṙ w mm/s, G w kg/m²s: HTPB/LOX 3.043e-2 mm/s, n 0.681 | 3.04e-05 | -0.10 % | ±0.1 % | **PASS** | Preset HRAP „Paraffin” = HTPB/LOX z tabeli Waxmana. Parafina nie jest paliwem projektu. |
| 13 | Konwencja jednostek a | HRAP propellant_template.m | 0.000104 | HRAP propellant_template.m: ṙ mm/s, G kg/m²s, L m | 0.000104 | +0.00 % | ±0.01 % | **PASS** | a_SI = a_HRAP·1e-3 (sprawdzone też w pkt 1 na CSV HRAP). |
| 14 | pe_05kN z prawem Kamps history (2.52e-5, 0.76): It / O/F_iw / F_iw | examples/pe_05kN.yaml, ta sama geometria | 3714.5 Ns | Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Sec. 3.2.1, Fig. 9 (ṙ w m/s; G_ox 50–100 kg/m²s); HyProp z presetem HRAP | 3610.6 Ns | -2.80 % | — | **INFO** | O/F_iw 6.09 → 3.08; F_iw 445 → 438 N. Geometria dobrana pod preset; z prawem z literatury silnik jest bogatszy w paliwo. |
| 15 | pe_05kN z prawem Kamps endpoint (4.36e-5, 0.62): It / O/F_iw / F_iw | examples/pe_05kN.yaml, ta sama geometria | 3714.5 Ns | Kamps et al., Aerospace 2019, 6, 45, doi:10.3390/aerospace6040045, Sec. 3.2.1, Fig. 9 (ṙ w m/s; G_ox 50–100 kg/m²s); HyProp z presetem HRAP | 3622.9 Ns | -2.47 % | — | **INFO** | O/F_iw 6.09 → 3.56; F_iw 445 → 436 N. Geometria dobrana pod preset; z prawem z literatury silnik jest bogatszy w paliwo. |

## 8. Zbieżność numeryczna

Podsumowanie: INFO: 3, PASS: 7

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Rząd zbieżności w dt: It | examples/pe_05kN.yaml | — |  | 1.016 | — | — | **INFO** | Ekstrapolacja Richardsona q* = 3713.93 Ns; błędy: dt=0.04: +0.059 %, dt=0.02: +0.030 %, dt=0.01: +0.015 %, dt=0.005: +0.007 %, dt=0.0025: +0.004 % |
| 2 | It przy domyślnym dt = 0.01 s vs q* (Richardson) | examples/pe_05kN.yaml | 3713.9 Ns | ekstrapolacja Richardsona z dt = 0.01/0.005/0.0025 s (samozbieżność) | 3714.5 Ns | +0.01 % | ±0.1 % | **PASS** | Schemat jawny Eulera: rząd 1. dt = 0.01 s daje błąd ~0.015 % It; sizing (dt 0.02 s) ~0.03 %. |
| 3 | Rząd zbieżności w dt: LRO | examples/pe_05kN.yaml | — |  | 1 | — | — | **INFO** | Ekstrapolacja Richardsona q* = 7.36 s; błędy: dt=0.04: -0.543 %, dt=0.02: -0.272 %, dt=0.01: -0.136 %, dt=0.005: -0.068 %, dt=0.0025: -0.034 % |
| 4 | LRO przy domyślnym dt = 0.01 s vs q* (Richardson) | examples/pe_05kN.yaml | 7.36 s | ekstrapolacja Richardsona z dt = 0.01/0.005/0.0025 s (samozbieżność) | 7.35 s | -0.14 % | ±0.136005 % | **PASS** | LRO jest kwantowane krokiem dt (zdarzenie na siatce czasu): tolerancja = 1 krok. |
| 5 | Rząd zbieżności w dt: Pc_liq | examples/pe_05kN.yaml | — |  | 0.998 | — | — | **INFO** | Ekstrapolacja Richardsona q* = 3.26806e+06 Pa; błędy: dt=0.04: +0.036 %, dt=0.02: +0.018 %, dt=0.01: +0.009 %, dt=0.005: +0.004 %, dt=0.0025: +0.002 % |
| 6 | Pc_liq przy domyślnym dt = 0.01 s vs q* (Richardson) | examples/pe_05kN.yaml | 3.268e+06 Pa | ekstrapolacja Richardsona z dt = 0.01/0.005/0.0025 s (samozbieżność) | 3.268e+06 Pa | +0.01 % | ±0.1 % | **PASS** | Schemat jawny Eulera: rząd 1. dt = 0.01 s daje błąd ~0.015 % It; sizing (dt 0.02 s) ~0.03 %. |
| 7 | It przy tolerancji Pc = 0.001 | examples/pe_05kN.yaml, dt = 0.01 s | 3714.5 Ns | ten sam przypadek, tolerancja domyślna 1e-4 | 3714.4 Ns | -0.00 % | ±0.05 % | **PASS** |  |
| 8 | It przy tolerancji Pc = 0.0001 | examples/pe_05kN.yaml, dt = 0.01 s | 3714.5 Ns | ten sam przypadek, tolerancja domyślna 1e-4 | 3714.5 Ns | +0.00 % | ±0.05 % | **PASS** |  |
| 9 | It przy tolerancji Pc = 1e-05 | examples/pe_05kN.yaml, dt = 0.01 s | 3714.5 Ns | ten sam przypadek, tolerancja domyślna 1e-4 | 3714.5 Ns | +0.00 % | ±0.05 % | **PASS** |  |
| 10 | It przy tolerancji Pc = 1e-06 | examples/pe_05kN.yaml, dt = 0.01 s | 3714.5 Ns | ten sam przypadek, tolerancja domyślna 1e-4 | 3714.5 Ns | +0.00 % | ±0.05 % | **PASS** |  |

## 9. Analiza wymiarowa

Podsumowanie: PASS: 10

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [m/s] c* = sqrt(R T0)/Γ | analiza wymiarowa (Pint) | 1566.0 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed., Eq. 3-32 | 1566.0 | +0.00 % | ±1e-06 % | **PASS** |  |
| 2 | [kg/(m^2*s)] ṁ/A* = p0 Γ / sqrt(R T0) | analiza wymiarowa (Pint) | 2043.4 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed., Eq. 3-24 | 2043.4 | +0.00 % | ±1e-06 % | **PASS** |  |
| 3 | [m/s] v_e (izentropowe) | analiza wymiarowa (Pint) | 2318.7 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed., Eq. 3-16 | 2318.7 | +0.00 % | ±1e-06 % | **PASS** |  |
| 4 | [m/s] c_i = λ v_e + (p_e − p_a) ε c*/p_c | analiza wymiarowa (Pint) | 2330.9 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed., Eqs. 2-16, 3-32, 3-34 | 2330.9 | +0.00 % | ±1e-06 % | **PASS** |  |
| 5 | [N] F = η_c* η_noz ṁ c_i | analiza wymiarowa (Pint) | 5369.8 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed., Eqs. 3-40, 3-41 | 5369.8 | +0.00 % | ±1e-06 % | **PASS** |  |
| 6 | [Pa] p_c = ṁ η_c* c* / (Cd A_t) (bilans w solverze) | analiza wymiarowa (Pint) | 1.929e+07 | Sutton & Biblarz, Rocket Propulsion Elements, 9th ed., Eq. 2-17 / 3-32 | 1.929e+07 | +0.00 % | ±1e-06 % | **PASS** | Wyrażenie przepisane z simulation/solver.py (chamber_balance). |
| 7 | [kg/s] ṁ_SPI = Cd N A sqrt(2 ρ ΔP) | analiza wymiarowa (Pint) | 0.4854 | Waxman et al., NASA NTRS 20190001326, Eqs. (2), (9) (Eq. 2) | 0.4854 | -0.00 % | ±1e-06 % | **PASS** |  |
| 8 | [m/s] ṙ = a G^n (a z mm/s → SI) | analiza wymiarowa (Pint) | 0.0007263 | HRAP propellant_template.m (ṙ mm/s, G kg/m²s) | 0.0007263 | +0.00 % | ±1e-06 % | **PASS** | Wymiar a zależy od n: [a] = m^(1+2n) kg^(−n) s^(n−1); baza przechowuje a w tej konwencji SI. |
| 9 | [kg/s] ṁ_f = ρ_f A_b ṙ | analiza wymiarowa (Pint) | 0.02834 | bilans masy paliwa (HRAP Eq. 12) | 0.02834 | +0.00 % | ±1e-06 % | **PASS** |  |
| 10 | [K] ΔT = h_lv Δm_v / (m_l c_p) | analiza wymiarowa (Pint) | 0.06 | bilans energii zbiornika (HRAP r. II; tank/equilibrium_blowdown.py) | 0.06 | +0.00 % | ±1e-06 % | **PASS** |  |

## 7. Niezmienniki fizyczne (Hypothesis, `tests/test_invariants.py`)

Bilans masy utleniacza i paliwa, impuls = ∫F dt, port tylko rośnie, Pc między otoczeniem a zbiornikiem, brak NaN/ujemnych mas, niezależność od jednostek wejścia.

```
3 passed in 23.51s
```
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
| B6 | Paliwo: domyślna parafina, a ΔHf PE = −41.2 kJ/mol C2H4 to oszacowanie fazy **gazowej** | PE jako paliwo projektu: ΔHf fazy stałej −28.182 kJ/mol CH2 (Splitstone & Johnson, J. Res. NBS 78A, 611, 1974); nowy wpis `ldpe` (granulat MELprop, ρ 920); domyślne paliwo `ldpe` | O/F 6.3, 32 bar: Tc −23 K (3272 → 3249), c* −0.5 %, Isp −0.5 %; z ρ 920: sizing 3 km 8 iteracji, F_iw 498 N, It 4026 Ns |

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
