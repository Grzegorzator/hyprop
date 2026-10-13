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
