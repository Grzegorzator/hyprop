# HyProp – raport walidacji

Wygenerowano: 2026-10-13 13:55, commit `143f8b8`  
Środowisko: Python 3.11.17 (Linux), numpy 2.4.6, scipy 1.17.1, cantera 3.2.0, CoolProp 8.0.0, rocketcea 1.2.3, pymoo 0.6.2, shapely 2.2.0, pint 0.25.3  
Polecenie: `python -m validation.run_all` (zmienne środowiskowe: patrz `validation/README.md`).

Zasada: wiersz może mieć PASS tylko przy sprawdzalnym źródle referencji. Brak źródła = `TODO: brak referencji`. INFO = wielkość raportowana bez kryterium.

## 0. Zestaw testów (wszystkie opcjonalne backendy zainstalowane)

```
126 passed, 16 warnings in 23.80s
```
README deklaruje liczbę testów: 120, 125 (różne miejsca README).

## 1. Odtworzenie deklaracji z README

Podsumowanie: FAIL: 4, INFO: 3, PASS: 38

| # | Wielkość | Przypadek | Referencja | Źródło referencji | HyProp | Odchyłka | Tolerancja | Status | Komentarz |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Średnia odchyłka Pc HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 1.7 pp | README.md §Validation anchors; HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 1.686 pp | -0.01418 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 2 | Średnia odchyłka p_tank HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 0.6 pp | README.md §Validation anchors; HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.561 pp | -0.03896 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 3 | Średnia odchyłka O/F HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 1 pp | README.md §Validation anchors; HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 1.046 pp | +0.04553 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 4 | Średnia odchyłka Ciąg F HyProp–HRAP [%] | prusak_v2, faza ciekła 0.2–7.0 s | 6.2 pp | README.md §Validation anchors; HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 6.237 pp | +0.0373 pp | ±0.05 pp | **PASS** | Odtworzenie deklaracji README (tolerancja = zaokrąglenie). |
| 5 | LRO HyProp | prusak_v2 | 7.19 s | README.md §Validation anchors | 7.19 s | +0 s | ±0.005 s | **PASS** |  |
| 6 | LRO HRAP: deklaracja README „~7.5 s” | prusak_v2 | 6.955 | HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5…: skok ṁ_ox 0.317→0.114 kg/s | 7.5 | +7.84 % | ±1 % | **FAIL** | Kolumna HyProp = wartość z README. README zawyża LRO HRAP; z CSV wynika 6.955 s. |
| 7 | LRO HyProp vs HRAP | prusak_v2 | 6.955 | HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 7.19 | +3.38 % | — | **INFO** | Odchyłka faktyczna (bez tolerancji – do oceny w pkt 5). |
| 8 | Średnia odchyłka F, wylot zamrożony [%] | prusak_v2 (diagnostyka) | — |  | 3.316 | — | — | **INFO** | Ta sama symulacja z v_e zamrożonym zamiast równowagowego: luka F 6.2 → ~3.3 %. Równowaga/zamrożenie tłumaczy ok. połowę; reszta niewyjaśniona (pkt 5). |
| 9 | a regresji hdpe [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 0.000104 | HRAP `HDPE.mat` prop_Reg=[0.104, 0.352] (mm/s; propellant_template.m) sha256 efb88e5a7ea1… | 0.000104 | +0.00 % | ±0.01 % | **PASS** |  |
| 10 | n regresji hdpe | N2O, baza HyProp[0] | 0.352 | HRAP `HDPE.mat` prop_Reg=[0.104, 0.352] (mm/s; propellant_template.m) sha256 efb88e5a7ea1… | 0.352 | +0.00 % | ±0.01 % | **PASS** |  |
| 11 | a regresji paraffin [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 3.04e-05 | HRAP `Paraffin.mat` prop_Reg=[0.0304, 0.681] (mm/s; propellant_template.m) sha256 5cd27ae16fe4… | 3.04e-05 | +0.00 % | ±0.01 % | **PASS** |  |
| 12 | n regresji paraffin | N2O, baza HyProp[0] | 0.681 | HRAP `Paraffin.mat` prop_Reg=[0.0304, 0.681] (mm/s; propellant_template.m) sha256 5cd27ae16fe4… | 0.681 | +0.00 % | ±0.01 % | **PASS** |  |
| 13 | a regresji htpb [m/s·(kg/m²s)^-n] | N2O, baza HyProp[0] | 0.000198 | HRAP `HTPB.mat` prop_Reg=[0.198, 0.325] (mm/s; propellant_template.m) sha256 acda3a38a891… | 0.000198 | -0.00 % | ±0.01 % | **PASS** |  |
| 14 | n regresji htpb | N2O, baza HyProp[0] | 0.325 | HRAP `HTPB.mat` prop_Reg=[0.198, 0.325] (mm/s; propellant_template.m) sha256 acda3a38a891… | 0.325 | +0.00 % | ±0.01 % | **PASS** |  |
| 15 | a z CSV HRAP (fit ṙ=aG^n) | prusak_v2 | 0.000104 | HRAP `HDPE.mat` 0.104 mm/s; HRAP v1.06 (R. Nickel, UTK), wynik `prusakv2_HRAP_output.csv` sha256 4eeaffee43d5… | 0.000104 | -0.01 % | ±0.1 % | **PASS** | n_fit=0.3520. Kolumna CSV „Regression Rate (mm/s)” zawiera faktycznie m/s (potwierdzone przez d(ID)/dt) – stąd deklaracja „a=1.040e-4 SI”. |
| 16 | It | examples/hdpe_05kN.yaml | 3942.0 Ns | README.md §Validation anchors | 3941.7 Ns | -0.339 Ns | ±0.5 Ns | **PASS** |  |
| 17 | Pc (szczyt) | examples/hdpe_05kN.yaml | 37 bar | README.md §Validation anchors | 36.94 bar | -0.0621 bar | ±0.5 bar | **PASS** | README podaje „Pc 37 bar” bez rodzaju; zgadza się z wartością szczytową. |
| 18 | LRO | examples/hdpe_05kN.yaml | 7.4 s | README.md §Validation anchors | 7.38 s | -0.02 s | ±0.05 s | **PASS** |  |
| 19 | Średnia czasowa F vs IW [%] | ROP examples/hdpe_05kN.yaml | -51 pp | README.md §Validation anchors | -51.51 pp | -0.5074 pp | ±1 pp | **PASS** | README podaje liczby całkowite (51 %, 48 %); przykład drukuje −51.5 % i −47.5 %. Tolerancja ±1 pp. |
| 20 | Średnia czasowa Pc vs IW [%] | ROP examples/hdpe_05kN.yaml | -48 pp | README.md §Validation anchors | -47.5 pp | +0.5042 pp | ±1 pp | **PASS** |  |
| 21 | Udział fazy ciekłej w It [%] | ROP examples/hdpe_05kN.yaml | 92.4 pp | README.md §Validation anchors | 92.39 pp | -0.01186 pp | ±0.05 pp | **PASS** |  |
| 22 | Udział fazy ciekłej w czasie [%] | ROP examples/hdpe_05kN.yaml | 42.6 pp | README.md §Validation anchors | 42.55 pp | -0.04804 pp | ±0.05 pp | **PASS** |  |
| 23 | api.size bez wyjątku | examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km) | — | README.md §Validation anchors | — | — | — | **FAIL** | BŁĄD: `Table built for eps=5.02091697319613, queried eps=5.016723777516034.`. Klucz cache tablicy CEA to round(eps, 2), a TabulatedBackend.query wymaga \|Δeps\|<1e-9 → kolizja kluczy dla eps 5.0209 i 5.0167. |
| 24 | Liczba iteracji | examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km) | 5 | README.md §Validation anchors | 5 | +0 | ±0 | **PASS** | Z poprawionym kluczem cache (diagnostyka, bez zmian w hyprop/). |
| 25 | F_iw | examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km) | 494.0 N | README.md §Validation anchors | 493.7 N | -0.2523 N | ±0.5 N | **PASS** | Z poprawionym kluczem cache (diagnostyka, bez zmian w hyprop/). |
| 26 | It | examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km) | 4083.0 Ns | README.md §Validation anchors | 4082.8 Ns | -0.2184 Ns | ±0.5 Ns | **PASS** | Z poprawionym kluczem cache (diagnostyka, bez zmian w hyprop/). |
| 27 | eps | examples/size_hdpe_3km.py (api.size 0.5 kN / 4000 Ns / 3 km) | 5.02 | README.md §Validation anchors | 5.017 | -0.003276 | ±0.005 | **PASS** | Z poprawionym kluczem cache (diagnostyka, bez zmian w hyprop/). |
| 28 | Apogeum (m_dry = 9 kg, jak w README) | examples/trajectory_hdpe_3km.py | 3291.0 m | README.md §Validation anchors | 3291.4 m | +0.4408 m | ±0.5 m | **PASS** |  |
| 29 | Apogeum (m_dry = 7 kg, obecny skrypt) | examples/trajectory_hdpe_3km.py | — |  | 3832.4 m | — | — | **INFO** | README nieaktualne: commit d22b828 zmienił m_dry 9→7 kg, README dalej podaje 3291 m dla 9 kg. |
| 30 | Tc | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar [Cantera] | 3292.0 K | Skrypt użytkownika `07_cantera_punkt0_termochemia.py` (sha256 55e88fed0749…), cantera_sweep.csv, O/F=6.5 | 3291.8 K | -0.1781 K | ±0.5 K | **PASS** | Cantera vs Cantera (ta sama baza gri30 i to samo Hf) – spójność, nie walidacja niezależna. |
| 31 | γ (cp/cv, zamrożone) | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar [Cantera] | 1.247 | Skrypt użytkownika `07_cantera_punkt0_termochemia.py` (sha256 55e88fed0749…), cantera_sweep.csv, O/F=6.5 | 1.247 | +0.0003927 | ±0.0005 | **PASS** |  |
| 32 | Isp_opt (równowaga) | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar [Cantera] | 247.2 s | Skrypt użytkownika `07_cantera_punkt0_termochemia.py` (sha256 55e88fed0749…), cantera_sweep.csv, O/F=6.5 | 247.2 s | +0.02129 s | ±0.05 s | **PASS** |  |
| 33 | c* ze wzoru idealnego (γ zamrożone) | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar [Cantera] | 1588.0 m/s | Skrypt użytkownika `07_cantera_punkt0_termochemia.py` (sha256 55e88fed0749…), cantera_sweep.csv, O/F=6.5 | 1588.3 m/s | +0.3104 m/s | ±0.5 m/s | **PASS** |  |
| 34 | Tc – deklaracja README | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 3292.0 K | README.md §Validation anchors | 3291.8 K | -0.1781 K | ±0.5 K | **PASS** |  |
| 35 | γ – deklaracja README | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 1.245 | README.md §Validation anchors | 1.247 | +0.002393 | ±0.0005 | **FAIL** | README: 1.245; skrypt 07 i HyProp: 1.247. Literówka w README (różnica 0.2 %). |
| 36 | Isp – deklaracja README | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 247.0 s | README.md §Validation anchors | 247.2 s | +0.2213 s | ±0.5 s | **PASS** |  |
| 37 | c* równowagowe / c* ze wzoru – deklaracja README „~2.3 %” | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 2.3 pp | README.md §Validation anchors | 2.375 pp | +0.07474 pp | ±0.1 pp | **PASS** |  |
| 38 | Tc Cantera vs NASA CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 3288.8 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 3291.8 | +0.09 % | ±1 % | **PASS** |  |
| 39 | c* Cantera vs NASA CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 1624.1 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 1626.0 | +0.12 % | ±1 % | **PASS** |  |
| 40 | Isp_opt eq Cantera vs NASA CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 247.1 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 247.2 | +0.03 % | ±1 % | **PASS** |  |
| 41 | Isp_opt frozen Cantera vs NASA CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 241.1 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 241.2 | +0.03 % | ±1 % | **PASS** |  |
| 42 | γ komory Cantera vs NASA CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 1.167 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 1.247 | +6.90 % | ±1 % | **FAIL** | RÓŻNE DEFINICJE: Cantera backend zwraca cp/cv (zamrożone), RocketCEA γ_s (równowagowe). Ten sam atrybut `chamber.gamma` znaczy co innego zależnie od backendu. |
| 43 | c* ze wzoru idealnego z γ_s (CEA) vs c* CEA | parafina C32H66/N2O, Pc 35 bar, O/F 6.5, rozprężanie do 1.013 bar | 1624.1 | NASA CEA (Gordon & McBride, NASA RP-1311, 1994/1996) przez RocketCEA 1.2.3; paliwo: karta z bazy HyProp (C32H66, Hf=-703 kJ/mol) | 1626.1 | +0.13 % | ±0.5 % | **PASS** | Wyjaśnienie „2.3 %”: wzór idealny z γ_s odtwarza c* równowagowe (0.1 %); 2.3 % to wyłącznie efekt wstawienia γ zamrożonego do wzoru. |
| 44 | max \|ESDU/CoolProp−1\| p_sat [%] | 263–303 K, krok 0.5 K | 1.5 pp | README.md §Validation anchors; CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 (klucz Lemmon-JCED-2006) | 0.1617 pp | -1.338 pp | — | **PASS** | Deklaracja „within 1.5 %”. Kolumna HyProp = max odchyłka; odchyłka = zapas do 1.5 %. |
| 45 | max \|ESDU/CoolProp−1\| ρ_l [%] | 263–303 K, krok 0.5 K | 1.5 pp | README.md §Validation anchors; CoolProp 8.0.0, EOS N2O: Lemmon & Span, J. Chem. Eng. Data 51 (2006) 785–850 (klucz Lemmon-JCED-2006) | 0.191 pp | -1.309 pp | — | **PASS** | Deklaracja „within 1.5 %”. Kolumna HyProp = max odchyłka; odchyłka = zapas do 1.5 %. |

## 2. Ustalenia (etap 1, pkt 0–1)

### 2.1 Testy

* Python 3.11, wszystkie backendy (Cantera 3.2, CoolProp 8.0, RocketCEA 1.2.3 zbudowany z gfortran, pymoo 0.6, openpyxl): **126 passed, 0 skipped, 0 failed**.
* 3 skipy z czystej instalacji to **nie** RocketCEA/Cantera/pymoo, tylko: 2× `importorskip("CoolProp")` w `test_tank_injector.py` oraz cały moduł `test_cea.py` (`importorskip("cantera")` na poziomie modułu – 8 testów liczonych jako 1 skip). Stąd 119 vs 126.
* **RocketCEA, NSGA-II (pymoo) i Morris/Sobol (SALib) nie mają żadnego testu.** Ich instalacja nie zmienia wyniku pytest – nigdy nie są wywoływane.
* Ostrzeżenie shapely `resolution` → `quad_segs`: potwierdzone (16×), do etapu 3.

### 2.2 Błędy w kodzie (do osobnych commitów `fix(...)`, po akceptacji)

| ID | Problem | Skutek | Proponowana poprawka |
|---|---|---|---|
| B1 | `_build_cea_table`: klucz cache `round(eps, 2)`, a `TabulatedBackend.query` wymaga \|Δeps\| < 1e-9 | `examples/size_hdpe_3km.py` (= `api.size`) pada z `ValueError`. Z poprawionym kluczem wyniki z README odtwarzają się co do cyfry (wiersze 24–27). | Klucz na pełnej wartości `float(eps)`. Bez zmiany fizyki. |
| B2 | `simulation.cea_backend` jest ignorowany; solver ma na sztywno `CanteraBackend` | Symulacja i sizing **zawsze** liczą Cantera, wbrew README („RocketCEA primary”) i wbrew konfiguracji. Wszystkie liczby transient w README są z Cantery. | Honorować `cea_backend` przez `get_backend()`. Uwaga: zmieni liczby przy `auto` + RocketCEA, patrz B3 – wymaga decyzji. |
| B3 | `StationState.gamma` znaczy co innego w backendach: Cantera = cp/cv zamrożone (1.247), RocketCEA = γ_s równowagowe (1.167) | `chamber.gamma` trafia do historii i do doboru dyszy (`nozzle/sizing.py`: eps_opt, Cf). Po naprawie B2 wynik sizingu zależałby od backendu o ~7 % w γ. | Dwa jawne pola: `gamma_frozen` i `gamma_eq`; sizing dyszy świadomie wybiera jedno. Wpływ na eps/Cf policzę w pkt 2–3. |
| B4 | η_c* nie wchodzi do ciągu: `F = η_noz·ṁ·v_e,ideal + (p_e − p_a)·A_e`, gdzie v_e i p_e są idealne (CEA) | η_c* obniża tylko Pc. Isp dostarczony = η_noz·Isp_ideal niezależnie od η_c*. `sensitivity_hdpe.py` pokazuje ∂F_iw/∂η_c* = −0.61 (lepsze spalanie → mniejszy ciąg). Przy η_c* = 0.95 ciąg i Isp zawyżone o ~5 % względem konwencji Isp_del = η_c*·η_F·Isp_ideal. | **Decyzja fizyczna – do omówienia.** HRAP ma tę samą konstrukcję (Nickel, „Theory and Application of HRAP”, r. V, równ. 20–22: v_e z idealnego T_c), więc benchmark z HRAP tego nie wykrywa. Źródło konwencji η_c*·η_F podam z numerem równania w pkt 3 – nie cytuję z pamięci. |

### 2.3 Niezgodności dokumentacji

* **D1** README: „LRO 7.19 s vs ~7.5 s” (HRAP). Z CSV HRAP: ṁ_ox spada 0.317 → 0.114 kg/s przy **t = 6.955 s**. HyProp jest więc o 3.4 % *później*, a nie wcześniej.
* **D2** Apogeum 3291 m dotyczy m_dry = 9 kg. Commit `d22b828` zmienił skrypt na 7 kg → obecnie 3832 m. README nieaktualne.
* **D3** γ = 1.245 w README; skrypt 07 i HyProp dają 1.247.
* **D4** Liczba testów: README podaje 120 i 125, faktycznie 126.
* **D5** „Cantera fallback validated to <1 %”: prawda dla Tc, c*, Isp (≤ 0.15 % vs NASA CEA), nieprawda dla γ (B3), a w transient RocketCEA nigdy nie jest używany (B2).
* **D6** Higiena przykładów (do etapu 3): `benchmark_prusak_v2.py` ma na sztywno ścieżkę `/sessions/festive-nice-darwin/...`; `report_hdpe_3km.py` nie znajduje figury (`../../examples/...`); przykłady nadpisują śledzone pliki (`database/engines/sized_hdpe_500N.yaml`, PNG w `examples/`).
* **D7** (HRAP, informacyjnie) kolumna CSV „Regression Rate (mm/s)” zawiera wartości w m/s. Potwierdza to przyrost średnicy portu.

### 2.4 Wyjaśnienie różnicy ~2.3 % c*

Skrypt 07 liczy c* wzorem gazu idealnego z γ = cp/cv mieszaniny **zamrożonej** w komorze. HyProp/CEA podaje c* **równowagowe** (zmiana składu w zbieżnej części dyszy). Ten sam wzór z równowagowym γ_s z NASA CEA odtwarza c* CEA z dokładnością 0.13 % (wiersz 43). Całe 2.3 % wynika więc z definicji γ, a nie z różnicy w termochemii.

### 2.5 Co te zgodności faktycznie dowodzą

* Benchmark HRAP to porównanie **kod–kod**: ten sam model zbiornika, ten sam SPI i te same współczynniki. Zgodność dowodzi wierności implementacji HRAP, a nie poprawności fizycznej (patrz B4).
* Kotwica „07” to Cantera vs Cantera (gri30, to samo Hf), czyli test spójności.
* Na razie naprawdę niezależne są dwie referencje: NASA CEA (przez RocketCEA) i CoolProp (EOS Lemmon & Span 2006). Obie dostają jednak te same dane wejściowe HyProp, np. Hf paliwa.
* Hf parafiny C32H66 = −703 kJ/mol to oszacowanie **fazy gazowej** z addytywności grupowej. W silniku paliwo jest stałe, więc entalpia przemiany fazowej jest pominięta. Wpływ na Tc/c* wymaga referencji NIST w pkt 2; nie podaję liczby bez źródła.
* HTPB nie ma Hf w bazie, więc żaden backend nie policzy HTPB/N2O. Siatka z pkt 2 wymaga składu i Hf HTPB ze źródłem.
* Luka ciągu 6.2 % vs HRAP: ok. 2.9 pp wyjaśnia wylot równowagowy vs zamrożony (wiersz 8). Pozostałe ~3.3 pp są na razie niewyjaśnione (kandydaci: η_noz stosowane tylko do członu pędowego w HyProp vs całego ciągu w HRAP, γ_e = const w HRAP, dynamika napełniania komory w HRAP). Do pkt 5.
