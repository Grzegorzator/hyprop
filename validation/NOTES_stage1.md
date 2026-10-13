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
