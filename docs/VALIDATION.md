# HyProp – raport walidacji

Wygenerowano: 2026-10-13 14:56, commit `f745e95`  
Środowisko: Python 3.11.17 (Linux), numpy 2.4.6, scipy 1.17.1, cantera 3.2.0, CoolProp 8.0.0, rocketcea 1.2.3, pymoo 0.6.2, shapely 2.2.0, pint 0.25.3  
Polecenie: `python -m validation.run_all` (zmienne środowiskowe: patrz `validation/README.md`).

Zasada: wiersz może mieć PASS tylko przy sprawdzalnym źródle referencji. Brak źródła = `TODO: brak referencji`. INFO = wielkość raportowana bez kryterium.

## 0. Zestaw testów (wszystkie opcjonalne backendy zainstalowane)

```
124 passed in 39.88s
```
## 1. Odtworzenie deklaracji z README

Podsumowanie: INFO: 2, PASS: 44

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Średnia odchyłka Pc HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 1.7 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 1.686 pp | -0.01418 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 2 | Średnia odchyłka p_tank HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 0.6 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.561 pp | -0.03896 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 3 | Średnia odchyłka O/F HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 1 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 1.046 pp | +0.04553 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 4 | Średnia odchyłka Ciąg F HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 0.9 pp | README.md (v0.2, sekcje Validation/Examples); HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.9484 pp | +0.04843 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 5 | LRO HyProp | prusak_v2 | 7.19 s | README.md (v0.2, sekcje Validation/Examples) | 7.19 s | +0 s | ±0.005 s | **PASS** |  |
| 6 | LRO HRAP (z danych HRAP) | prusak_v2 | 6.955 s | README.md (v0.2, sekcje Validation/Examples) | 6.955 s | +0 s | ±0.0005 s | **PASS** | Skok ṁ_ox 0.317→0.114 kg/s w CSV. (v0.1 README podawało błędnie ~7.5 s.) |
| 7 | LRO HyProp vs HRAP | prusak_v2 | 6.955 | HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 7.19 | +3.38 % | — | **INFO** | Odchyłka faktyczna, bez kryterium (do oceny w pkt 5). |
| 8 | Średnia odchyłka F, wylot zamrożony [%] | prusak_v2 (diagnostyka) | — |  | 1.848 | — | — | **INFO** | Ta sama symulacja z v_e zamrożonym zamiast równowagowego (diagnostyka). HRAP nie stosuje η_c* do ciągu, a liczy v_e ze stałym γ; zgodność F jest częściowo przypadkowa (efekty o przeciwnych znakach). |
| 9 | a regresji hdpe [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 0.000104 | HRAP `HDPE.mat` prop_Reg=[0.104, 0.352] (mm/s; propellant_template.m) sha256 efb88e5a7ea1… | 0.000104 | +0.00 % | ±0.01 % | **PASS** |  |
| 10 | n regresji hdpe | N2O, baza HyProp[0] | 0.352 | HRAP `HDPE.mat` prop_Reg=[0.104, 0.352] (mm/s; propellant_template.m) sha256 efb88e5a7ea1… | 0.352 | +0.00 % | ±0.01 % | **PASS** |  |
| 11 | a regresji paraffin [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 3.04e-05 | HRAP `Paraffin.mat` prop_Reg=[0.0304, 0.681] (mm/s; propellant_template.m) sha256 5cd27ae16fe4… | 3.04e-05 | +0.00 % | ±0.01 % | **PASS** |  |
| 12 | n regresji paraffin | N2O, baza HyProp[0] | 0.681 | HRAP `Paraffin.mat` prop_Reg=[0.0304, 0.681] (mm/s; propellant_template.m) sha256 5cd27ae16fe4… | 0.681 | +0.00 % | ±0.01 % | **PASS** |  |
| 13 | a regresji htpb [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 0.000198 | HRAP `HTPB.mat` prop_Reg=[0.198, 0.325] (mm/s; propellant_template.m) sha256 acda3a38a891… | 0.000198 | -0.00 % | ±0.01 % | **PASS** |  |
| 14 | n regresji htpb | N2O, baza HyProp[0] | 0.325 | HRAP `HTPB.mat` prop_Reg=[0.198, 0.325] (mm/s; propellant_template.m) sha256 acda3a38a891… | 0.325 | +0.00 % | ±0.01 % | **PASS** |  |
| 15 | a z CSV HRAP (fit ṙ=aG^n) | prusak_v2 | 0.000104 | HRAP `HDPE.mat` 0.104 mm/s; HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.000104 | -0.01 % | ±0.1 % | **PASS** | n_fit=0.3520. Kolumna CSV „Regression Rate (mm/s)” zawiera faktycznie m/s (potwierdzone przez d(ID)/dt) – stąd deklaracja „a=1.040e-4 SI”. |
| 16 | It | examples/hdpe_05kN.yaml | 3749.0 Ns | README.md (v0.2, sekcje Validation/Examples) | 3748.9 Ns | -0.07622 Ns | ±0.5 Ns | **PASS** |  |
| 17 | Pc (szczyt) | examples/hdpe_05kN.yaml | 36.9 bar | README.md (v0.2, sekcje Validation/Examples) | 36.94 bar | +0.0379 bar | ±0.05 bar | **PASS** |  |
| 18 | LRO | examples/hdpe_05kN.yaml | 7.38 s | README.md (v0.2, sekcje Validation/Examples) | 7.38 s | -1.128e-13 s | ±0.005 s | **PASS** |  |
| 19 | Isp średni | examples/hdpe_05kN.yaml | 196.0 s | README.md (v0.2, sekcje Validation/Examples) | 195.6 s | -0.4091 s | ±0.5 s | **PASS** |  |
| 20 | Średnia czasowa F vs IW [%] | ROP examples/hdpe_05kN.yaml | -51 pp | README.md (v0.2, sekcje Validation/Examples) | -51.43 pp | -0.4268 pp | ±1 pp | **PASS** | README podaje liczby całkowite (51 %, 48 %); przykład drukuje −51.5 % i −47.5 %. Tolerancja ±1 pp. |
| 21 | Średnia czasowa Pc vs IW [%] | ROP examples/hdpe_05kN.yaml | -48 pp | README.md (v0.2, sekcje Validation/Examples) | -47.46 pp | +0.5432 pp | ±1 pp | **PASS** |  |
| 22 | Udział fazy ciekłej w It [%] | ROP examples/hdpe_05kN.yaml | 92.3 pp | README.md (v0.2, sekcje Validation/Examples) | 92.3 pp | +0.00209 pp | ±0.05 pp | **PASS** |  |
| 23 | Udział fazy ciekłej w czasie [%] | ROP examples/hdpe_05kN.yaml | 42.6 pp | README.md (v0.2, sekcje Validation/Examples) | 42.55 pp | -0.04804 pp | ±0.05 pp | **PASS** |  |
| 24 | Liczba iteracji | examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km, Cantera) | 7 | README.md (v0.2, sekcje Validation/Examples) | 7 | +0 | ±0 | **PASS** | Tolerancja sizingu 1 % (v0.1: 3 %); v0.1 padało na błędzie B1. |
| 25 | F_iw | examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km, Cantera) | 497.0 N | README.md (v0.2, sekcje Validation/Examples) | 496.9 N | -0.1399 N | ±0.5 N | **PASS** |  |
| 26 | It | examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km, Cantera) | 4040.0 Ns | README.md (v0.2, sekcje Validation/Examples) | 4040.0 Ns | -0.04899 Ns | ±0.5 Ns | **PASS** |  |
| 27 | Dt | examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km, Cantera) | 12 mm | README.md (v0.2, sekcje Validation/Examples) | 12 mm | -0.003986 mm | ±0.05 mm | **PASS** |  |
| 28 | eps | examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km, Cantera) | 5.03 | README.md (v0.2, sekcje Validation/Examples) | 5.025 | -0.004762 | ±0.005 | **PASS** |  |
| 29 | Apogeum (m_dry = 7 kg) | examples/trajectory_hdpe_3km.py | 3775.0 m | README.md (v0.2, sekcje Validation/Examples) | 3774.5 m | -0.4563 m | ±0.5 m | **PASS** | m_dry, Cd, D to założenia (skrypt); bez referencji lotnej. |
| 30 | Tc | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar [Cantera] | 3292.0 K | Skrypt użytkownika `07_cantera_punkt0_termochemia.py` (sha256 55e88fed0749…), cantera_sweep.csv, O/F=6.5 | 3291.8 K | -0.1781 K | ±0.5 K | **PASS** | Cantera vs Cantera (ta sama baza gri30 i to samo Hf) – spójność, nie walidacja niezależna. |
| 31 | γ (cp/cv, zamrożone) | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar [Cantera] | 1.247 | Skrypt użytkownika `07_cantera_punkt0_termochemia.py` (sha256 55e88fed0749…), cantera_sweep.csv, O/F=6.5 | 1.247 | +0.0003927 | ±0.0005 | **PASS** |  |
| 32 | Isp_opt (równowaga) | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar [Cantera] | 247.2 s | Skrypt użytkownika `07_cantera_punkt0_termochemia.py` (sha256 55e88fed0749…), cantera_sweep.csv, O/F=6.5 | 247.2 s | +0.02129 s | ±0.05 s | **PASS** |  |
| 33 | c* ze wzoru idealnego (γ zamrożone) | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar [Cantera] | 1588.0 m/s | Skrypt użytkownika `07_cantera_punkt0_termochemia.py` (sha256 55e88fed0749…), cantera_sweep.csv, O/F=6.5 | 1588.3 m/s | +0.3104 m/s | ±0.5 m/s | **PASS** |  |
| 34 | Tc – deklaracja README | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 3292.0 K | README.md (v0.2, sekcje Validation/Examples) | 3291.8 K | -0.1781 K | ±0.5 K | **PASS** |  |
| 35 | γ (zamrożone) – deklaracja README | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 1.247 | README.md (v0.2, sekcje Validation/Examples) | 1.247 | +0.0003927 | ±0.0005 | **PASS** |  |
| 36 | Isp – deklaracja README | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 247.0 s | README.md (v0.2, sekcje Validation/Examples) | 247.2 s | +0.2213 s | ±0.5 s | **PASS** |  |
| 37 | c* równowagowe / c* ze wzoru – deklaracja README „~2.3 %” | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 2.3 pp | README.md (v0.2, sekcje Validation/Examples) | 2.375 pp | +0.07474 pp | ±0.1 pp | **PASS** |  |
| 38 | Tc Cantera vs NASA CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 3288.8 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 3291.8 | +0.09 % | ±1 % | **PASS** |  |
| 39 | c* Cantera vs NASA CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 1624.1 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 1626.0 | +0.12 % | ±1 % | **PASS** |  |
| 40 | Isp_opt eq Cantera vs NASA CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 247.1 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 247.2 | +0.03 % | ±1 % | **PASS** |  |
| 41 | Isp_opt frozen Cantera vs NASA CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 241.1 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 241.2 | +0.03 % | ±1 % | **PASS** |  |
| 42 | γ zamrożone (cp/cv) Cantera vs NASA CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 1.247 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 1.247 | +0.02 % | ±0.1 % | **PASS** | README: „within 1e-3”. W v0.1 backendy zwracały w `gamma` różne wielkości (B3). |
| 43 | γ_s równowagowe Cantera vs NASA CEA (GAMMAs) | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 1.167 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 1.167 | -0.01 % | ±0.1 % | **PASS** | Cantera: różnica centralna (d ln p/d ln ρ)_s, RP-1311 Eq. 2.71. |
| 44 | c* ze wzoru idealnego z γ_s vs c* CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 1624.1 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 1626.1 | +0.13 % | ±0.5 % | **PASS** | Wyjaśnienie „2.3 %”: wzór idealny z γ_s odtwarza c* równowagowe; 2.3 % to wyłącznie efekt wstawienia γ zamrożonego do wzoru. |
| 45 | max \|ESDU/CoolProp−1\| p_sat [%] | 263–303 K, krok 0.5 K | 1.5 pp | README.md (v0.2, sekcje Validation/Examples); CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 (klucz Lemmon-JCED-2006) | 0.1617 pp | -1.338 pp | — | **PASS** | Deklaracja „within 1.5 %”. Kolumna HyProp = max odchyłka; odchyłka = zapas do 1.5 %. |
| 46 | max \|ESDU/CoolProp−1\| ρ_l [%] | 263–303 K, krok 0.5 K | 1.5 pp | README.md (v0.2, sekcje Validation/Examples); CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 (klucz Lemmon-JCED-2006) | 0.191 pp | -1.309 pp | — | **PASS** | Deklaracja „within 1.5 %”. Kolumna HyProp = max odchyłka; odchyłka = zapas do 1.5 %. |

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
| B5 | Dysza w sizingu: ε ze wzoru gazu idealnego (frozen γ: −3 % vs CEA), Cf bez η i Cd → pętla sizingu stała na −5 % ciągu po B4 | ε z rozprężania CEA (p_e = p_a), Cf dostarczony = λ·η·Cd·Cf_i; tolerancja sizingu 3 % → 1 % | sizing 3 km: 7 iteracji, F_iw 497 N, It 4040 Ns |

Drobne: shapely `resolution` → `quad_segs`; `importorskip("openpyxl")`; ścieżka HRAP przez `HYPROP_HRAP_DIR`; przykłady piszą do `outputs/` zamiast nadpisywać śledzone pliki.

### 2.3 Poprawione w dokumentacji

* LRO HRAP: v0.1 README podawało ~7.5 s, a z CSV wynika **6.955 s**.
* γ = 1.245 → 1.247 (frozen).
* Apogeum: skrypt od commitu `d22b828` używa m_dry = 7 kg; README podawało wynik dla 9 kg.
* Liczba testów: README nie podaje już liczby.

### 2.4 Wyjaśnienie różnicy ~2.3 % c*

Skrypt 07 liczy c* wzorem gazu idealnego z γ = cp/cv mieszaniny **zamrożonej**. CEA/HyProp podaje c* **równowagowe**. Ten sam wzór z γ_s odtwarza c* CEA do 0.13 %. Różnica wynika wyłącznie z definicji γ.

### 2.5 Ograniczenia: co te zgodności dowodzą, a co nie

* Benchmark HRAP to porównanie **kod–kod** (ten sam model zbiornika i wtryskiwacza, te same współczynniki). Po B4 zgodność ciągu (0.9 %) jest częściowo przypadkowa. HRAP nie stosuje η_c* do ciągu, ale liczy v_e ze stałym γ komory, co daje niższe v_e niż rozprężanie równowagowe. Oba efekty mają przeciwne znaki.
* Kotwica „07” to Cantera vs Cantera (test spójności). Naprawdę niezależne są NASA CEA (przez RocketCEA) i CoolProp (EOS Lemmon & Span). Obie dostają jednak dane wejściowe z HyProp, np. Hf paliwa.
* Hf parafiny C32H66 = −703 kJ/mol to oszacowanie **fazy gazowej** (addytywność grupowa). Paliwo w silniku jest stałe. Do weryfikacji z NIST w pkt 2; nie podaję liczby bez źródła.
* HTPB nie ma Hf w bazie: żaden backend nie policzy HTPB/N2O.
* Żadnych prób ogniowych: η_c*, Cd wtryskiwacza, a i n są założeniami lub danymi literaturowymi (flagi `verify`).
